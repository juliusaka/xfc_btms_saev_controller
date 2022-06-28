import pandas as pd
import os
from typing import List
import components
from components import ChaDepParent
import numpy as np
import cvxpy as cp
import cvxpy.atoms.max as cpmax
import time as time_module

class ChaDepMpcBase(ChaDepParent):
    '''see mpcBase.md for explanations'''

    def __init__(self, ChargingStationId, ResultWriter: components.ResultWriter, SimBroker: components.SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize=100, BtmsC=1, BtmsMaxSoc=0.8, BtmsMinSOC=0.2, BtmsSoc0=0.5, calcBtmsGridProp=False, GridPowerMax_Nom=1, GridPowerLower=-1, GridPowerUpper=1):

        super().__init__(ChargingStationId, ResultWriter, SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize, BtmsC, BtmsMaxSoc, BtmsMinSOC, BtmsSoc0, calcBtmsGridProp, GridPowerMax_Nom, GridPowerLower, GridPowerUpper)

        '''additional variables for btms size optimization'''
        self.determinedBtmsSize = None
        self.determinedMaxPower = None

        '''additional variables for MPC:'''
        self.PredictionTime         = []    # time vector
        self.PredictionPower        = []    
        self.power_sum_original     = []    
        self.PredictionGridUpper    = []   # TODO used so far?
        self.PredictionGridLower    = []   # TODO used so far?

        self.P_GridLast             = None      # last Grid Power, used to flatten the MPC power curve
        self.P_GridMaxPlanning      = None      # maximal P_Grid from planning, used to keep demand charge low

        self.E_BtmsLower            = []        # btms energy from planning
        self.E_BtmsUpper            = []        # btms energy from planning

        self.N                      = 10      # number of short horizoned steps in MPC



    def generatePredictions(self, path_BeamPredictionFile, dtype, path_DataBase, timestep=5*60, addNoise = True):
        # generate a prediction for the charging station
        # neglection of charging desire, make this not too good
        ChBaVehicles = []
        Queue = []
        #open a SimBroker object for this
        PredBroker = components.SimBroker(path_BeamPredictionFile, dtype)
        # open a VehicleGenerator for this:
        VehicleGenerator = components.VehicleGenerator(path_BeamPredictionFile, dtype, path_DataBase)
        
        # open lists for power and time, initialize with a value to synchronize with iteration counter of prediction broker (at iteration 0, the power is 0, because no vehicles have arrived. all the vehicles of the last timestep seconds start charging at the start of the iteration)
        time = [PredBroker.t_act]
        power_sum = [0]

        #add all vehicle to queue which arrive at this charging station
        while not PredBroker.eol():
            #print("check 1.5")
            slice = PredBroker.step(timestep)
            for i in range(0, len(slice)):
                #print("check 1.9")
                if slice.iloc[i]["type"] == "ChargingPlugInEvent":
                    vehicle = VehicleGenerator.generateVehicleSO(slice.iloc[i])
                    if np.isin(element=self.ChBaParkingZoneId, test_elements=vehicle.BeamDesignatedParkingZoneId).any():
                        Queue.append(vehicle)
            # add vehicle to charging bays if possible
            while len(ChBaVehicles) < self.ChBaNum and len(Queue) > 0:
                ChBaVehicles.append(Queue.pop(0))
            # charge vehicles with maximum possible power
            power_i = []
            for x in ChBaVehicles:
                p = min([x.getMaxChargingPower(timestep), self.ChBaMaxPower_abs])
                x.addPower(p, timestep)
                power_i.append(p)
            #save result in vectors
            time.append(PredBroker.t_act)
            power_sum.append(sum(power_i))
            #release vehicles which are full
            pop_out = []
            for i in range(0,len(ChBaVehicles)):
                if ChBaVehicles[i].VehicleEngy >= ChBaVehicles[i].VehicleDesEngy:
                    pop_out.append(i)
            for i in range(0, len(pop_out)):
                x = ChBaVehicles.pop(pop_out[i]-i) # -i makes up for the loss of list-length after pop 
                # print(x.VehicleSoc)
                # print(x.VehicleDesEngy/x.VehicleMaxEngy)
        
        # add noise to produce prediction:
        self.power_sum_original = power_sum.copy()
        if addNoise:
            param = 0.10
            avg = np.average(power_sum)
            for i in range(0,len(power_sum)):
                 power_sum[i] = power_sum[i] + avg * (np.random.randn() * param)
                 if power_sum[i] < 0:
                     power_sum[i] = 0
        # save to Prediction Variables
        self.PredictionTime = time
        self.PredictionPower = power_sum

        # generate a prediction for power limits
        # TODO: so far no implemented deviations
        for i in time:
            self.PredictionGridUpper.append(self.GridPowerMax_Nom)
            self.PredictionGridLower.append(- self.GridPowerMax_Nom)
        
        #save results to csv-file
        dict = {
            'time': time,
            'Power_original': self.power_sum_original,
            'Power_noise': self.PredictionPower,
            'PredictionGridUpper': self.PredictionGridUpper,
            'PredictionGridLower': self.PredictionGridLower,
        }
        df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
        dir         = os.path.join(self.ResultWriter.directory,'generatePredictions')
        os.makedirs(dir, exist_ok=True) 
        filename    = self.ChargingStationId + ".csv"
        df.to_csv(os.path.join(dir, filename))

    def determineBtmsSize(self, t_act, t_max, timestep, a, b, c, P_free):
        '''see mpcBase.md for explanations'''
        # vector lengthes
        T = int(np.ceil((t_max - t_act) / timestep))

        # define variables 
        x = cp.Variable((1, T+1))
        u = cp.Variable((4, T))
        p_gridSlack = cp.Variable((1,1)) # slack variable to determine demand charge with free demand charge level, e.g. if p_max > 20kW, demand charge applied
        
        # define disturbance i_power, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_max)
        time = time[idx]
        i_power = power[idx]
        if len(i_power) != T:
            print("length input power", len(i_power))
            print("length T", T)
            raise ValueError("length T and length of vector d are unequal")

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # tuning parameters
        constr = []
        # define constraints
        for k in range(T):
            constr += [x[:,k+1] == x[:,k] + ts * eta * u[2,k] + ts * 1/eta * u[3,k],
                        u[0,k] - u[1,k] == i_power[k], # energy flow equation
                        u[1,k] == u[2,k] + u[3,k], # P_BTMS is sum of charge and discharge
                        u[2,k] >= 0, # charging power always positive
                        u[3,k] <= 0, # discharge power always negative
                        ]
        # insert initial constraint, bound BTMS size and define free power level
        constr +=  [x[:,0]== 0,
                    x[:,0] == x[:,T],
                    p_gridSlack >= cpmax(u[0,:]),
                    p_gridSlack >= P_free,]
        
        # define cost-funciton
        cost = a * (p_gridSlack - P_free) # demand charg
        for k in range(T):       # cost of btms degradation and cost of energy loss
            cost += (b+c) * u[2,k] * ts + c * u[3,k] * ts # u[3,k] is always negative

        # solve the problem
        prob = cp.Problem(cp.Minimize(cost), constr)
        prob.solve()

        # determine BTMS size and unpack over values
        btms_size = np.max(x.value) - np.min(x.value)
        P_Grid = u[0,:].value
        P_BTMS = u[1,:].value
        E_BTMS = x[0,:].value
        P_Charge = i_power
        P_BTMS_Ch = u[2,:].value
        P_BTMS_DCh = u[3,:].value
        cost = prob.value
        time_x = time.tolist()
        time_x.append(time[-1]+timestep)
        time_x = np.array(time_x) # time_x is the time vector for states, time the time vector for control inputs

        self.determinedBtmsSize = btms_size
        self.determinedMaxPower = max(abs(P_BTMS))

        #save results to csv-file
        param_vec = np.zeros_like(time)
        param_vec[0] = self.determinedBtmsSize
        param_vec[1] = a
        param_vec[2] = b
        param_vec[3] = c
        dict = {
            'time': time,
            'time_x': time_x,
            'P_Grid': P_Grid,
            'P_BTMS': P_BTMS,
            'E_BTMS': E_BTMS[:-1],
            'P_Charge': P_Charge,
            'P_BTMS_Ch': P_BTMS_Ch,
            'P_BTMS_DCh': P_BTMS_DCh,
            'param: btms size, a,b,c': param_vec,
        }
        df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
        dir         = os.path.join(self.ResultWriter.directory,'determineBtmsSize')
        os.makedirs(dir, exist_ok=True) 
        filename    = self.ChargingStationId + ".csv"
        df.to_csv(os.path.join(dir, filename))

        return time, time_x, btms_size, P_Grid, P_BTMS, P_BTMS_Ch, P_BTMS_DCh, E_BTMS, P_Charge, cost

    def planning(self, t_act, t_max, timestep, a, b, c, d_param, P_free, P_ChargeAvg, beta, cRating=None):
        time_start = time_module.time() # timewatch
        '''see mpcBase.md for explanations'''
        # vector lengthes
        T = int(np.ceil((t_max - t_act) / timestep))

        # define variables 
        x = cp.Variable((2, T+1))
        u = cp.Variable((5, T))
        p_gridSlack = cp.Variable((1,1))    # slack variable to determine demand charge with free demand charge level, e.g. if p_max > 20kW, demand charge applied
        t_wait = cp.Variable((1,T))
        n = cp.Variable((2,T))
        
        # define disturbance i_power, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_max)
        time = time[idx]
        i_power = power[idx]
        if len(i_power) != T:
            print("length i_power", len(i_power))
            print("length T", T)
            raise ValueError("length T and length of vector i_power are unequal")

        #create array for cost-function parameter d
        if type(d_param) != list:
            d = []
            for i in range(len(i_power)+1):
                d.append(d_param)
        else:
            d = d_param
            if len(d) != T:
                print("length d", len(d))
                print("length T", T)
                raise ValueError("length T and length of vector d are unequal")

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # define constraints (including system dynamics)
        constr = []
        for k in range(T):
            constr += [x[0,k+1] == x[0,k] + ts * eta * u[2,k] + ts * 1/eta * u[3,k],    # BTMS equation
                        x[1,k+1] == x[1,k] + ts * u[4,k],                               # shifted energy equation
                        u[0,k] - u[1,k] == i_power[k] - u[4,k],                         # energy flow equation
                        u[1,k] == u[2,k] + u[3,k],                                      # P_BTMS is sum of charge and discharge
                        u[2,k] >= 0,                                                    # charging power always positive
                        u[3,k] <= 0,                                                    # discharge power always negative
                        t_wait[0,k] >= ts *( n[0,k] +n[1,k]),                           # wait time 
                        n[0,k] >= x[1,k]/(P_ChargeAvg * ts),                            # wait time due to already shifted energy
                        n[1,k] >= u[4,k] / P_ChargeAvg,                                 # wait time due to newly shifted energy
                        n[1,k] >= 0,                                                    # wait time due to newly shifted energy is always positive
                        ]

        # btms power limits
        if cRating != None:
            for k in range(T):
                constr += [u[2,k] <= cRating*self.BtmsSize,     # upper power limit,
                            u[3,k] >= -cRating*self.BtmsSize,   # discharge power always negative
                            ]

        for k in range(T+1):
            constr += [x[0,k] >= 0,                 # lower limit of BTMS size
                        x[0,k] <= self.BtmsSize,    # upper limit of BTMS size
                        x[1,k] >= 0,                # shifted energy is only a positive bin
                        ]
        # insert initial constraint, bound BTMS size and define free power level
        constr +=  [x[0,0] == x[0,T],               # ensure not to discharge BTMS to minimize cost function
                    x[1,0] == 0,                    # set shifted Energy at beginning to zero
                    x[1,T] == 0,                    # shifted energy should be zero at end
                    p_gridSlack >= cpmax(u[0,:]),
                    p_gridSlack >= P_free,
                    ]
        
        # define cost-funciton
        cost = a * (p_gridSlack - P_free)           # demand charge
        for k in range(T):                          # cost of btms degradation, cost of energy loss, cost of waiting time
            cost += (b+c) * u[2,k] * ts + c * u[3,k] * ts + d[k] * t_wait[0,k]

        time_end1 = time_module.time() # timewatch

        # solve the problem
        prob = cp.Problem(cp.Minimize(cost), constr)
        prob.solve()

        time_end2=time_module.time()    # timewatch

        # determine BTMS size and unpack over values
        P_Grid = u[0,:].value
        P_BTMS = u[1,:].value
        E_BTMS = x[0,:].value
        E_Shift = x[1,:].value
        P_Charge = i_power
        P_Shift = u[4,:].value
        P_BTMS_Ch = u[2,:].value
        P_BTMS_DCh = u[3,:].value
        t_wait_val = t_wait[0,:].value
        cost_t_wait = 0
        for k in range(len(t_wait_val)):
            cost_t_wait += d[k] * t_wait_val[k]
        cost = prob.value
        time_x = time.tolist()
        time_x.append(time[-1]+timestep)
        time_x = np.array(time_x)       # time_x is the time vector for states, time the time vector for control inputs, time_x is one entry longer

        # save important values to object
        self.P_GridMaxPlanning = max(P_Grid)
        self.E_BtmsLower        = []
        self.E_BtmsUpper        = []
        for i in range(T+1):
            self.E_BtmsLower.append(max([0, (1-beta) * E_BTMS[i]]))
            self.E_BtmsUpper.append(min([self.BtmsSize, (1+beta) * E_BTMS[i]]))
        
        # initialize charging station with planning results
        self.P_GridLast = P_Grid[0]   # grid power last with first planning value
        self.BtmsEn = E_BTMS[0]       # BTMS energy with first planning value
        
        #save results to csv-file
        param_vec = np.zeros_like(time)
        param_vec[0] = self.BtmsSize
        param_vec[1] = a
        param_vec[2] = b
        param_vec[3] = c
        dict = {
            'time': time,
            'time_x': time_x,
            'P_Grid': P_Grid,
            'P_BTMS': P_BTMS,
            'E_BTMS': E_BTMS,
            'E_BTMS_lower': self.E_BtmsLower,
            'E_BTMS_upper': self.E_BtmsUpper,
            'E_Shift': E_Shift,
            'P_Charge': P_Charge,
            'P_Shift': P_Shift,
            'P_BTMS_Ch': P_BTMS_Ch,
            'P_BTMS_DCh': P_BTMS_DCh,
            't_wait': t_wait_val,
            'param: btms size, a,b,c': param_vec,
            'd': d
        }
        df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
        dir         = os.path.join(self.ResultWriter.directory,'planning')
        os.makedirs(dir, exist_ok=True) 
        filename    = self.ChargingStationId + ".csv"
        df.to_csv(os.path.join(dir, filename))

        # print solver stats
        print(self.ChargingStationId)
        print('solver name: ',prob.solver_stats.solver_name)
        print('setup time: ',time_end1-time_start)
        print('solve time: ',time_end2-time_end1)
        print('total control action time: ', time_end2-time_start)
        print(prob.status)
        print('')

        return time, time_x, P_Grid, P_BTMS, P_BTMS_Ch, P_BTMS_DCh, E_BTMS, E_Shift, P_Charge, P_Shift, t_wait_val, cost_t_wait, cost

    def runMpc(self, timestep, N, SimBroker: components.SimBroker, M1 = 1e6, M2 = 1e7):
        # N is the MPC optimization horizon

        # define variables 
        x = cp.Variable((2, N+1))
        u = cp.Variable((5, N))
        t1 = cp.Variable((1,N)) # this goes from [0, N]: for control output variable
        t2 = cp.Variable((1,N)) # this goes from [1, N+1]: for state variable, first (0) is already bound
        P_avg = cp.Variable((1,1))

        # obtain inputs
        P_GridLast          = self.P_GridLast             # grid power from last control step
        i_act               = SimBroker.iteration         # actual iteration to read out from planning results
        P_GridMaxPlanning   = self.P_GridMaxPlanning     
        P_GridUpper         = self.GridPowerUpper 
        btms_size           = self.BtmsSize
        E_BtmsLower         = self.E_BtmsLower
        E_BtmsUpper         = self.E_BtmsUpper
        E_Btms              = self.BtmsEn
        # charging trajectories from cars
        E_V_lower = np.zeros(N+1)
        E_V_upper = np.zeros(N+1)
        for x in self.ChBaVehicles:
            if x != False:
                upper, lower = x.getChargingTrajectory(SimBroker.t_act, timestep, N)
                E_V_upper = np.add(E_V_upper, upper)
                E_V_lower = np.add(E_V_lower, lower)

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # set up control problem
        constr = []

        for k in range(N):
            # system dynamics and control variable constraints
            constr += [
                        x[0, k+1] == x[0, k] + ts * (eta * u[2,k] + 1/eta * u[3, k]),   # system dynamic btms
                        x[1, k+1] == x[1, k] + ts * u[4, k],    # system dynamic charged energy to vehicles
                        u[4, k] == u[0, k] - u[1, k],   # energy flow at station
                        u[1, k] == u[2, k] + u[3, k],   # energy equation charge/discharge
                        u[0, k] <= P_GridMaxPlanning + t2[0, k],  # grid power smaller than value from planning
                        u[0, k] <= P_GridUpper, # upper bound from derms
                        u[2, k] >= 0, 
                        u[3, k] <= 0,
                        u[4, k] >= 0,
                        t1[0, k] >= 0,
                        t2[0, k] >= 0,
            ]
        for k in range(N+1):
            # state constraints
            constr += [
                        x[0, k] >= 0,
                        x[0, k] <= btms_size,
            ]
        # define these constraints from 1 on to reduce the number of redundant constraints
        for k in range(1, N+1):
            constr += [
                        x[0, k] >= E_BtmsLower[i_act + k], # correct position in planning results is i_act + k
                        x[0, k] <= E_BtmsUpper[i_act + k],
                        x[1, k] >= E_V_lower[k] - t1[0, k], 
                        x[1, k] <= E_V_upper[k],            
            ]
        # initial constraints
        constr += [
            x[0, 0] == E_Btms,
            x[1, 0] == 0,
        ]
        # average power constraint
        constr += [
            P_avg == (cp.sum(u[0, :]) + P_GridLast)/ (N+1),
        ]
        # objective function
        cost = cp.square(P_GridLast - P_avg)
        cost += cp.sum(cp.square(u[0, :] - P_avg))
        cost += M1 * cp.sum(cp.square(t1[0, :] ))
        cost += M2 * cp.sum(cp.square(t2[0, :] ))

        # solve control problem
        prob = cp.Problem(cp.Minimize(cost), constr)
        prob.solve()

        # add routine to deal with infeasibilty (even control problem should always be feasible)
        if prob.status == 'infeasible':
            print('The problem is infeasible!')
            # TODO: add additional code to deal with this
            
        # return control action
        '''our control outputs are P_BTMS  and P_Charge, P_Grid is the sum of both'''
        P_BTMS = u[1, 0].value
        P_Charge = u[4, 0].value

        return P_BTMS, P_Charge


    def step(self, timestep):

        '''repark vehicles based on their charging desire with the parent method'''
        self.repark()

        '''insert here the control action'''
        
        '''assign values to:
        self.ChBaPower
        self.BtmsPower
        '''
        # run MPC to obtain max power for charging vehicles and charging power for BTMS
        P_BTMS, P_Charge = self.runMpc(timestep, self.N, self.SimBroker)
        P_max = P_Charge
        # distribute MPC powers to vehicles (by charging desire)
        self.distributeChargingPowerToVehicles(timestep, P_max)
        # assign MPC btms power to btms
        self.BtmsPower = P_BTMS

        '''# update BTMS and vehicles states and update the result writer with their states'''
        # BTMS
        self.BtmsAddPower(self.BtmsPower, timestep)
        # Vehicles
        self.updateVehicleStatesAndWriteResults(self.ChBaPower, timestep)

        '''determine power desire for next time step'''
        PowerDesire = 0
        for i in range(0,len(self.ChBaVehicles)):
            if self.ChBaVehicles[i] != False:
                PowerDesire += min([self.ChBaVehicles[i].getMaxChargingPower(timestep), self.ChBaMaxPower[i]])

        self.PowerDesire = PowerDesire
        self.BtmsPowerDesire = self.getBtmsMaxPower(timestep)

        '''Write chargingStation states in ResultWriter'''
        self.ResultWriter.updateChargingStationState(self.SimBroker.t_act, self)

        '''release vehicles when full and create control outputs'''
        self.resetOutput()
        r1 = self.chBaReleaseThresholdAndOutput()
        r2 = self.queueReleaseThresholdAndOutput()
        released_Vehicles = r1 + r2
        # add release events
        for x in released_Vehicles:
            self.ResultWriter.releaseEvent(self.SimBroker.t_act, x, self.ChargingStationId)
        # TODO: create control outputs

        '''checks'''
        if len(self.ChBaVehicles)!=self.ChBaNum:
            raise ValueError("Size of ChargingBay List shouldn't change")