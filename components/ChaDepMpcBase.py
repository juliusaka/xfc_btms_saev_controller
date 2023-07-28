from multiprocessing.sharedctypes import Value
import pandas as pd
import os
from typing import List
import components
from components import ChaDepParent
import numpy as np
import cvxpy as cp
import cvxpy.atoms.max as cpmax
import time as time_module
import logging
import matplotlib.pyplot as plt

class ChaDepMpcBase(ChaDepParent):
    '''see mpcBase.md for explanations'''

    def __init__(self, ChargingStationId, ResultWriter: components.ResultWriter, SimBroker: components.SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize=100, BtmsC=1, BtmsMaxSoc=1.0, BtmsMinSOC=0.0, BtmsSoc0=0.8, calcBtmsGridProp=False, GridPowerMax_Nom=1, GridPowerLower=-1, GridPowerUpper=1, BtmsEfficiency = 0.85):

        super().__init__(ChargingStationId, ResultWriter, SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize, BtmsC, BtmsMaxSoc, BtmsMinSOC, BtmsSoc0, calcBtmsGridProp, GridPowerMax_Nom, GridPowerLower, GridPowerUpper, BtmsEfficiency)

        '''additional parameters for results of btms size optimization'''
        self.determinedBtmsSize     = None
        self.determinedMaxPower     = None

        '''additional variables for MPC:'''
        #variables for storing data
        self.PredictionTime         = []    # time vector
        self.PredictionPower        = []    # predicted, unconstrained power
        self.PredictionTimeLag      = []    # associated time lag vector
        self.PredictionEnergyLag    = []    # associated energy lag vector
        self.power_sum_original     = []    # predicted, unconstrained power, with no noise applied
        self.PredictionGridUpper    = []    # TODO used so far?
        self.PredictionGridLower    = []    # TODO used so far?

        self.E_BtmsLower            = []    # btms energy from planning
        self.E_BtmsUpper            = []    # btms energy from planning
        self.E_BtmsPlanned          = []    # btms energy from planning
        self.E_BtmsReference        = []    # btms reference energy

        self.E_V_Upper_lastArrivals = []    # energy trajectories of last arrivals   
        self.E_V_Lower_lastArrivals = []    # energy trajectories of last arrivals 

        self.OptimalValues          = None  # optimal values of MPC solver
        self.VectorT1               = None  # vector t1, which is the feasibility guaranteeing variable for the vehicle charge trajectory
        self.VectorT2               = None  # vector t2, which is the feasibility guaranteeing variable for the energy conservation, in case the BTMS is fully empty.

        # variables
        self.P_GridLast             = None      # last Grid Power, used to flatten the MPC power curve
        self.P_GridMaxPlanning      = None      # maximal P_Grid from planning, used to keep demand charge low
        self.P_ChargeGranted        = 0         # power granted by MPC to vehicles
        self.P_ChargeDelivered      = 0         # power delivered to vehicles
        self.P_BTMSGranted          = 0         # power granted by MPC to BTMS
        self.P_BTMSDeliverable      = 0         # power deliverable by BTMS
        self.avgHorizon             = 2         # average horizon of charging demand in horizon in steps


    def generate_prediction(self, path_BeamPredictionFile, dtype, path_DataBase, timestep=5*60, addNoise = True, noise_param = 0.2, prediction_directory = None):
        # generate a prediction for the charging station
        # neglection of charging desire, make this not too good
        ChBaVehicles = []
        Queue = []
        #open a SimBroker object for this
        PredBroker = components.SimBroker(path_BeamPredictionFile, dtype)
        # open a VehicleGenerator for this:
        VehicleGenerator = components.VehicleGenerator(path_BeamPredictionFile, dtype, path_DataBase)
        
        # open lists for power and time
        time = []
        power_sum = []
        # calculate also time lag and energy lag as reference values
        time_lag = []
        energy_lag = []

        #add all vehicle to queue which arrive at this charging station
        while not PredBroker.eol():
            slice = PredBroker.step(timestep)
            for i in range(0, len(slice)):
                if slice.iloc[i]["type"] == "RefuelSessionEvent":
                    vehicle = VehicleGenerator.generate_vechicle_from_df_slice(slice.iloc[i])
                    if np.isin(element=self.ChargingStationId, test_elements=[slice.iloc[i].parkingTaz]).any():
                        Queue.append(vehicle)
            # add vehicle to charging bays if possible
            while len(ChBaVehicles) < self.ChBaNum and len(Queue) > 0:
                ChBaVehicles.append(Queue.pop(0))
            # charge vehicles with maximum possible power
            power_i = []
            for x in ChBaVehicles:
                p = min([x.get_max_charging_power(timestep), self.ChBaMaxPower_abs])
                x.add_power(p, timestep)
                power_i.append(p)
            #save result in vectors
            time.append(PredBroker.t_act)
            power_sum.append(sum(power_i))
            # calculate time lag and energy lag
            time_lag.append(sum([x.update_time_lag(PredBroker.t_act) for x in ChBaVehicles]))
            energy_lag.append(sum([x.update_energy_lag(PredBroker.t_act) for x in ChBaVehicles]))
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
            param = noise_param
            avg = np.average(power_sum)
            # seed random variable
            np.random.seed(1)
            for i in range(0,len(power_sum)):
                 power_sum[i] = power_sum[i] + avg * (np.random.randn() * param)
                 if power_sum[i] < 0:
                     power_sum[i] = 0
        # save to Prediction Variables
        self.PredictionTime = time
        self.PredictionPower = power_sum
        self.PredictionTimeLag = time_lag
        self.PredictionEnergyLag = energy_lag

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
            'TimeLag': self.PredictionTimeLag,
            'EnergyLag': self.PredictionEnergyLag,
            'PredictionGridUpper': self.PredictionGridUpper,
            'PredictionGridLower': self.PredictionGridLower,
        }
        df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
        if prediction_directory is None:
            dir         = os.path.join(self.ResultWriter.directory, 'generatePredictions')
        else:
            dir         = prediction_directory
        os.makedirs(dir, exist_ok=True) 
        filename    = str(self.ChargingStationId) + ".csv"
        df.to_csv(os.path.join(dir, filename))
    
    def load_prediction(self, path):
        df = pd.read_csv(path)
        self.PredictionTime = df['time'].to_numpy()
        self.PredictionPower = df['Power_noise'].to_numpy()
        self.PredictionTimeLag = df['TimeLag'].to_numpy()
        self.PredictionEnergyLag = df['EnergyLag'].to_numpy()
        self.PredictionGridUpper = df['PredictionGridUpper'].to_numpy()
        self.PredictionGridLower = df['PredictionGridLower'].to_numpy()
        self.power_sum_original = df['Power_original'].to_numpy()
        # turn off noise
        self.PredictionPower = self.power_sum_original.copy()


    def plot_prediction(self, directory):
        time = self.PredictionTime
        power = self.PredictionPower

        ax = plt.subplot()
        ax.plot(time,power, label = 'with noise')
        ax.plot(time,self.power_sum_original, label = 'without noise')
        ax.legend()
        plt.savefig(os.path.join(directory, self.ChargingStationId + '_prediction.png'))
        # return fig
        return ax
        
    def determine_btms_size(self, t_act, t_max, timestep, a, b_sys, b_cap, b_loan, c, include_max_c_rate = False, max_c_rate = 2, d_wait_cost = None):
        P_Charge_avg = 300 # average charging power in kW for wait time calculation
        '''see mpcBase.md for explanations'''
        # vector lengthes
        T = int(np.ceil((t_max - t_act) / timestep))

        # define time-varying d_wait_cost
        if d_wait_cost == 1e6:
            d_wait_cost = None
            flag_d_wait_cost_active = True
        elif d_wait_cost != None:
            flag_d_wait_cost_active = True
        else:
            flag_d_wait_cost_active = False
        if d_wait_cost != None:
            if d_wait_cost == 'varying':
                d_wait_cost = []
                for i in range(T+1):
                    if i * timestep >= 6*3600 and  10*3600 >= i * timestep:
                        d_wait_cost.append(20)
                    elif i * timestep >= 15*3600 and  19*3600 >= i * timestep:
                        d_wait_cost.append(20)
                    else:
                        d_wait_cost.append(0)
            else:
                d = d_wait_cost
                d_wait_cost = []
                for i in range(T+1):
                    d_wait_cost.append(d)

        # define variables 
        E_BTMS = cp.Variable((1, T+1))
        P_Grid = cp.Variable((1, T))
        P_BTMS = cp.Variable((1, T))
        P_BTMS_Charge = cp.Variable((1, T))
        P_BTMS_Discharge = cp.Variable((1, T)) # is defined positive and negative values are taken into account in the constraints
        E_Btms_max = cp.Variable((1, 1))
        P_Btms_max = cp.Variable((1, 1))
        P_Grid_max = cp.Variable((1, 1))
        if d_wait_cost != None:
            E_Shift = cp.Variable((1, T+1))
            P_Shift = cp.Variable((1, T))
            n_a = cp.Variable((1, T+1))
            n_b = cp.Variable((1, T+1)) # is defined till T+1, but only used till T. This is for easier implementation of the wait time at T+1. But T+1 must still be >=0.
            t_wait = cp.Variable((1, T+1))
        
        
        # define disturbance P_Charge, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_act + T*timestep)
        time = time[idx]
        P_Charge = power[idx]
        if len(P_Charge) != T:
            logging.warning("length of i_power does not match T, length of i_power: " + str(len(P_Charge)) + ", T: " + str(T))
            raise ValueError("length T and length of vector i_power are unequal, i_power: " + str(len(P_Charge)) + ", T: " + str(T))
        
        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency
        
        # define constraints
        constr = []
        for k in range(T):
            constr += [
                E_BTMS[0,k+1] == E_BTMS[0,k] + ts * eta * P_BTMS_Charge[0,k] - ts * P_BTMS_Discharge[0,k], # btms charging equation
                P_Grid[0,k] == P_Charge[k] + P_BTMS[0,k] if d_wait_cost == None else P_Grid[0,k] == P_Charge[k] - P_Shift[0,k] + P_BTMS[0,k], # grid power equation
                P_BTMS[0,k] == P_BTMS_Charge[0,k] - P_BTMS_Discharge[0,k], # P_BTMS is sum of charge and discharge
                P_BTMS_Charge[0,k] >= 0, # charge power always positive
                P_BTMS_Discharge[0,k] >= 0, # discharge power always negative
                P_Grid[0,k] >= 0, # grid power always positive
            ]
        for k in range(T+1):
            constr += [
                E_BTMS[0,k] >= 0, # btms energy always positive
            ]
        # cyclic behaviour
        constr +=  [
            E_BTMS[0,0] == E_BTMS[0,T], # ensure cyclic behaviour
            E_Btms_max[0,0] >= cp.max(E_BTMS[0,:]), # get max btms energy
            P_Btms_max[0,0] >= cp.max(P_BTMS_Charge[0,:]), # get max btms power
            P_Btms_max[0,0] >= cp.max(P_BTMS_Discharge[0,:]), # get max btms power
            P_Grid_max[0,0] >= cp.max(P_Grid[0,:]), # get max grid power
                    ]
        if include_max_c_rate:
            constr += [
                P_Btms_max[0,0] <= max_c_rate * E_Btms_max[0,0], # c_rate enforcement
                ]
        # wait time integration
        if d_wait_cost != None:
            for k in range(T):
                constr += [
                    E_Shift[0,k+1] == E_Shift[0,k] + ts * P_Shift[0,k],
                    n_b[0,k] >= P_Shift[0,k] / P_Charge_avg, # wait time due to newly shifted energy
                ]
            for k in range(T+1):
                constr += [
                    E_Shift[0,k] >= 0, # shifted energy always positive
                    t_wait[0,k] >= ts * (n_a[0,k] + n_b[0,k]), # wait time
                    n_a[0,k] >= E_Shift[0,k]/(P_Charge_avg * ts), # wait time due to already shifted energy
                    n_b[0,k] >= 0, # wait time due to newly shifted energy is always positive
                ]
            constr += [
                E_Shift[0,0] == 0, # initial condition
                E_Shift[0,T] == 0, # final condition
                ]
        
        # define cost-funciton
        cost = a * P_Grid_max[0,0]                                  # demand charge
        cost += b_sys * P_Btms_max[0,0]                      # power cost of btms
        cost += b_loan * E_Btms_max[0,0]                           # cost of btms loan
        for k in range(T):
            cost += (b_cap + (1-eta) * c) * P_BTMS_Charge[0,k] * ts # cost of btms capacity and cost of charging losses
        # wait time integration
        if d_wait_cost != None:
            for k in range(T+1):
                cost += d_wait_cost[k] * t_wait[0,k]
        
        # solve the problem
        logging.info("\n----- \n btms size optimization for charging station %s \n-----" % self.ChargingStationId)
        prob = cp.Problem(cp.Minimize(cost), constr)
        components.solver_algorithm(prob)
        
        # determine BTMS size and unpack over values
        btms_size = E_Btms_max.value[0,0] #np.max(E_BTMS.value) - np.min(E_BTMS.value)
        P_Grid = P_Grid.value.reshape(-1)
        P_BTMS = P_BTMS.value.reshape(-1)
        E_BTMS = E_BTMS.value.reshape(-1)
        P_Charge = P_Charge
        if d_wait_cost != None:
            E_Shift = E_Shift.value.reshape(-1)
            P_Shift = P_Shift.value.reshape(-1)
        P_BTMS_Ch = P_BTMS_Charge.value.reshape(-1)
        P_BTMS_DCh = P_BTMS_Discharge.value.reshape(-1)
        cost = prob.value
        time_x = time.tolist()
        time_x.append(time[-1]+timestep)
        time_x = np.array(time_x) # time_x is the time vector for states, time the time vector for control inputs

        self.determinedBtmsSize = btms_size
        self.BtmsSize = btms_size
        self.determinedMaxPowerBTMS = max(abs(P_BTMS))
        self.determinedMaxPowerGrid = max(abs(P_Grid))
        self.sizing_cost = cost

        #save results to csv-file
        param_vec = np.zeros_like(time)
        param_vec = param_vec.tolist()
        param_vec[0] = self.determinedBtmsSize
        param_vec[1] = a
        param_vec[2] = b_sys
        param_vec[3] = b_cap
        param_vec[4] = b_loan
        param_vec[5] = c
        if d_wait_cost != None:
            param_vec[6] = d_wait_cost if type(d_wait_cost) != list else 0
        dict = {
            'time': time,
            'time_x': time_x,
            'P_Grid': P_Grid,
            'P_BTMS': P_BTMS,
            'E_BTMS': E_BTMS[:-1],
            'P_Charge': P_Charge,
            'P_BTMS_Ch': P_BTMS_Ch,
            'P_BTMS_DCh': P_BTMS_DCh,
        }
        if flag_d_wait_cost_active:
            dict['param: btms size, a,b_sys,b_cap,b_loan,c,d_wait_cost'] = param_vec
        else:
            dict['param: btms size, a,b_sys,b_cap,b_loan,c'] = param_vec
        if d_wait_cost != None:
            dict['E_Shift'] = E_Shift[:-1]
            dict['P_Shift'] = P_Shift
        df = pd.DataFrame({ key:pd.Series(value) for key, value in dict.items() })
        dir         = self.ResultWriter.directory
        os.makedirs(dir, exist_ok=True) 
        filename    = 'btms_sizing_' + self.ChargingStationId + ".csv"
        df.to_csv(os.path.join(dir, filename))

        return time, time_x, btms_size, P_Grid, P_BTMS, P_BTMS_Ch, P_BTMS_DCh, E_BTMS, P_Charge, cost
    
    def load_determine_btms_size_results(self, filename):
        df = pd.read_csv(filename)
        self.determinedBtmsSize = df['param: btms size, a,b_sys,b_cap,b_loan,c'][0]
        self.BtmsSize = df['param: btms size, a,b_sys,b_cap,b_loan,c'][0]
        self.determinedMaxPowerBTMS = max(abs(df['P_BTMS']))
        self.determinedMaxPowerGrid = max(abs(df['P_Grid']))
        self.sizing_cost = df['param: btms size, a,b_sys,b_cap,b_loan,c'][6]
        return df

    def day_planning(self, t_act, t_max, timestep, a, b, c, d_param, P_free, P_ChargeAvg, beta, cRating=None, verbose=True):
        time_start = time_module.time() # timing
        '''see mpcBase.md for explanations'''
        # vector length T
        T = int(np.ceil((t_max - t_act) / timestep))

        # define variables 
        x = cp.Variable((2, T+1))
        u = cp.Variable((5, T))
        p_gridSlack = cp.Variable((1,1))    # slack variable to determine demand charge with free demand charge level, e.g. if p_max > 20kW, demand charge applied
        t_wait = cp.Variable((1,T))
        n = cp.Variable((2,T))
        
        # define disturbance i_power for the needed time period, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_act + T*timestep)
        time = time[idx]
        i_power = power[idx]
        if len(i_power) != T:
            logging.warning("length of i_power is not equal to T, i_power: %s, T: %s" % (len(i_power), T))
            raise ValueError("length T and length of vector i_power are unequal, T: %s, i_power: %s" % (T, len(i_power)))

        #create array for cost-function parameter d, if wait time cost is not flexible (given as an array)
        if type(d_param) != list:
            d = []
            for i in range(len(i_power)+1):
                d.append(d_param)
        else:
            d = d_param
            if len(d) != T:
                logging.warning("length of d is not equal to T, d: %s, T: %s" % (len(d), T))
                raise ValueError("length T and length of vector d are unequal, d: %s, T: %s" % (len(d), T))

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # define constraints (including system dynamics)
        constr = []
        for k in range(T):
            constr += [
                        x[0, k+1] == x[0, k] + ts * eta * u[2, k] + ts * u[3, k],    # BTMS equation
                       # shifted energy equation
                       x[1, k+1] == x[1, k] + ts * u[4, k],
                       # energy flow equation
                       u[0, k] - u[1, k] == i_power[k] - u[4, k],
                       # P_BTMS is sum of charge and discharge
                       u[1, k] == u[2, k] + u[3, k],
                       # charging power always positive
                       u[2, k] >= 0,
                       # discharge power always negative
                       u[3, k] <= 0,
                       # wait time
                       t_wait[0, k] >= ts * (n[0, k] + n[1, k]),
                       # wait time due to already shifted energy
                       n[0, k] >= x[1, k]/(P_ChargeAvg * ts),
                       # wait time due to newly shifted energy
                       n[1, k] >= u[4, k] / P_ChargeAvg,
                       # wait time due to newly shifted energy is always positive
                       n[1, k] >= 0,
                       ]

        # btms power limits
        if cRating != None:
            for k in range(T):
                constr += [u[2,k] <= cRating*self.BtmsSize,     # upper power limit,
                            u[3,k] >= -cRating*self.BtmsSize,   # discharge power always negative
                            ]

        # btms size limits
        for k in range(T+1):
            constr += [x[0,k] >= 0,                 # lower limit of BTMS size
                        x[0,k] <= self.BtmsSize,    # upper limit of BTMS size
                        x[1,k] >= 0,                # shifted energy is only a positive bin
                        ]

        # insert initial constraint, bound BTMS charge/discharge and define free power level
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
        logging.info("\n----- \n day planning for charging station %s \n-----" % self.ChargingStationId)
        prob = cp.Problem(cp.Minimize(cost), constr)
        components.solver_algorithm(prob)

        time_end2=time_module.time()    # timewatch

        # logging additional solver stats
        logging.info("self tracked times: setup time: %s, solve time: %s, total action time: %s" % (time_end1-time_start, time_end2-time_end1, time_end2-time_start))

        # unpack results
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
        self.E_BtmsPlanned     = []
        for repeat in range(2): # double the E_BTMSLower and Upper vector length to have sufficient long prediction vectors for the last time steps.
            for i in range(T+1):
                self.E_BtmsLower.append(max([0            , E_BTMS[i] - beta * self.BtmsSize]))
                self.E_BtmsUpper.append(min([self.BtmsSize, E_BTMS[i] + beta * self.BtmsSize]))
                self.E_BtmsPlanned.append(E_BTMS[i])

        # initialize charging station with planning results
        self.P_Grid = P_Grid[0]   # grid power last with first planning value
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
        logging.info("planning results saved to %s" % os.path.join(dir, filename))

        return time, time_x, P_Grid, P_BTMS, P_BTMS_Ch, P_BTMS_DCh, E_BTMS, E_Shift, P_Charge, P_Shift, t_wait_val, cost_t_wait, cost

    def init_mpc_problem(self, timestep, N, rho=5000, M1 = 200, E_btms_reference=0.8):
        self.warm_start = False
        self.N_mpc = N
        # cvxpy parameters         
        self.P_GridLast_param    = cp.Parameter(1)
        self.E_Btms0_param       = cp.Parameter(1)
        self.E_Vehicles_lower_param = cp.Parameter(N+1)
        self.E_Vehicles_upper_param = cp.Parameter(N+1)

        # constants
        P_Grid_max_constant   = cp.Constant(self.determinedMaxPowerGrid)
        P_Btms_max_constant   = cp.Constant(self.determinedMaxPowerBTMS)
        btms_size_constant           = cp.Constant(self.BtmsSize)
        E_Btms_reference_constant    = cp.Constant(E_btms_reference)
        ts_constant = cp.Constant(timestep / 3.6e3)

        # variables 
        self.E_BTMS_opti = cp.Variable((1, N+1))
        self.E_Vehicles_opti = cp.Variable((1, N+1))

        self.P_Grid_opti = cp.Variable((1, N))
        self.P_BTMS_opti = cp.Variable((1, N))
        self.P_Charge_opti = cp.Variable((1, N))
        self.t_opti = cp.Variable((1,N)) # this goes from [0, N]: for control output variable

        constr = []
        
        # system dynamics and control variable constraints
        for k in range(N):
            constr += [self.E_BTMS_opti[0, k+1] == self.E_BTMS_opti[0, k] + ts_constant * self.P_BTMS_opti[0,k],   # system dynamic btms 
                self.E_Vehicles_opti[0, k+1] == self.E_Vehicles_opti[0, k] + ts_constant * self.P_Charge_opti[0, k],    # system dynamic charged energy to vehicles
                self.P_Grid_opti[0,k] == self.P_Charge_opti[0,k]  + self.P_BTMS_opti[0,k], # grid power is sum of btms and vehicle power
                self.P_Grid_opti[0,k] <= P_Grid_max_constant,
                self.P_Grid_opti[0,k] >= 0,
                self.P_BTMS_opti[0,k] <= P_Btms_max_constant,
                self.P_BTMS_opti[0,k] >= -1 * P_Btms_max_constant,
                self.P_Charge_opti[0,k] >= 0,
                self.t_opti[0, k] >= 0,
            ]
        # state constraints
        for k in range(N+1):
            constr += [
                        self.E_BTMS_opti[0, k] >= 0,
                        self.E_BTMS_opti[0, k] <= btms_size_constant,
            ]
        # define these constraints from 1 on to reduce the number of redundant constraints
        for k in range(1, N+1):
            constr += [
                        self.E_Vehicles_opti[0, k] >= self.E_Vehicles_lower_param[k] - self.t_opti[0, k-1], # we defined t1 as a vector of length N+1-1, so we need to subtract 1 to get the correct index
                        self.E_Vehicles_opti[0, k] <= self.E_Vehicles_upper_param[k] ,#- t[0, k-1],            
            ]
        # initial constraints
        constr += [
            self.E_BTMS_opti[0, 0] == self.E_Btms0_param,
            self.E_Vehicles_opti[0, 0] == 0,
        ]

        # objective function
        # last grid power gradient cost
        self.cost_mpc =  cp.square((self.P_Grid_opti[0,0]- self.P_GridLast_param)/(ts_constant*P_Grid_max_constant))
        # grid power gradient cost
        for k in range(1, N-1):
            self.cost_mpc += cp.square((self.P_Grid_opti[0, k+1] - self.P_Grid_opti[0, k])/(ts_constant*P_Grid_max_constant))
        # reference btms energy tracking cost
        for k in range(N): 
            self.cost_mpc += rho * cp.square((self.E_BTMS_opti[0,k] - E_Btms_reference_constant)/btms_size_constant) 
        # penalty variable cost
        self.cost_mpc += M1 * cp.sum(cp.square(self.t_opti[0, :] ))

        # set up problem
        self.mpc_problem = cp.Problem(cp.Minimize(self.cost_mpc), constr)

    def run_mpc(self, timestep, SimBroker: components.SimBroker, verbose = False):
        
        # initialize problem parameters
        self.P_GridLast_param.value=np.array([self.P_GridLast])
        self.E_Btms0_param.value = np.array([self.BtmsEn])
        # charging trajectories from cars
        E_V_lower = np.zeros(self.N_mpc+1)
        E_V_upper = np.zeros(self.N_mpc+1)
        for i in range(len(self.ChBaVehicles)):
            if self.ChBaVehicles[i] != False:
                lower, upper = self.ChBaVehicles[i].get_charging_trajectories(SimBroker.t_act, timestep, self.N_mpc, maxPowerPlug = self.ChBaMaxPower[i])
                E_V_upper = np.add(E_V_upper, upper)
                E_V_lower = np.add(E_V_lower, lower)
        self.E_Vehicles_lower_param.value = E_V_lower
        self.E_Vehicles_upper_param.value = E_V_upper

        # solve problem
        try:
            self.mpc_problem.solve(solver=cp.ECOS, verbose=verbose, warm_start=self.warm_start)
            self.warm_start = True
        except:
            logging.warning("MPC Solver failed at iteration %s. Using fallback solver." % SimBroker.iteration)
            components.solver_algorithm(self.mpc_problem)

        # note optimal value and slack variables
        self.OptimalValues          = self.mpc_problem.value
        self.VectorT1               = self.t_opti.value
        self.VectorT2               = 0
        self.ResultWriter.update_mpc_stats(SimBroker.t_act, self, self.mpc_problem, self.t_opti, self.t_opti)
        
        # return control action
        P_BTMS = self.P_BTMS_opti[0,0].value
        P_ChargeGranted = self.P_Charge_opti[0,0].value
        P_Grid = self.P_Grid_opti[0,0].value

        # deal with numerical issues
        eps = 0.2
        eps_E_Vehicles = self.E_Vehicles_opti[0,1].value - self.E_Vehicles_lower_param[1].value # E_Vehicles should be greate than E_Vehicles_lower
        if eps_E_Vehicles < 0 and eps_E_Vehicles > - eps: # if E_Vehicles is eps close to E_Vehicles_lower, recalculate P_Charge
            _P_ChargeGranted = (self.E_Vehicles_lower_param[1].value - self.E_Vehicles_lower_param[0].value)/(timestep/3600)
            P_BTMS = P_BTMS + P_ChargeGranted - _P_ChargeGranted
            P_ChargeGranted = _P_ChargeGranted
        return P_BTMS, P_ChargeGranted

    def step(self, timestep, verbose = False):
        
        '''repark vehicles based on their charging desire with the parent method'''
        self.repark()
        logging.info("Vehicles reparked in %s" % self.ChargingStationId)
        
        ''' get control action'''
        # run MPC to obtain max power for charging vehicles and charging power for BTMS
        self.P_GridLast = self.P_Grid
        self.P_BTMSGranted, P_Charge_Granted = self.run_mpc(timestep, self.SimBroker, verbose = verbose)

        # distribute MPC powers to vehicles (by charging desire)
        self.P_ChargeDelivered = self.distribute_charging_power_to_vehicles(timestep, P_Charge_Granted)
        logging.info('P_ChargeGranted: {:.2f}, P_ChargeDelivered: {:.2f}'.format(P_Charge_Granted, self.P_ChargeDelivered))

        # calculate dispatachable BTMS power (checking that bounds aren't exceeded)
        self.P_BTMSDeliverable = self.get_btms_max_deliverable_power(self.P_BTMSGranted, timestep)
        self.P_BTMS = self.P_BTMSDeliverable
        logging.info('P_BTMS granted: {:.2f}, P_BTMS deliverable: {:.2f}'.format(self.P_BTMSGranted, self.P_BTMSDeliverable))

        # calculate grid power from delivered charge and BTMS power
        self.P_Grid = self.P_ChargeDelivered + self.P_BTMS
        logging.info('P_Grid: {:.2f}'.format(self.P_Grid))

        '''Write chargingStation states for k in ResultWriter'''
        self.ResultWriter.update_charging_station_state(
            self.SimBroker.t_act, self)
        logging.debug("results written for charging station {}".format(self.ChargingStationId))

        '''# update BTMS state for k+1'''
        # BTMS
        self.btms_add_power(self.P_BTMS, timestep)
        logging.debug("BTMS state updated for charging station {}".format(self.ChargingStationId))

        '''write vehicle states for k in ResultWriter and update vehicle states for k+1'''
        # Vehicles
        self.update_vehicle_states_and_write_states(self.ChBaPower, timestep)
        logging.debug("vehicle states updated for charging station {}".format(self.ChargingStationId))

        '''determine power desire for next time step'''
        PowerDesire = 0
        for i in range(0, len(self.ChBaVehicles)):
            if isinstance(self.ChBaVehicles[i], components.Vehicle):
                PowerDesire += min(
                    [self.ChBaVehicles[i].get_max_charging_power(timestep), self.ChBaMaxPower[i]])
        self.PowerDesire = PowerDesire
        self.BtmsPowerDesire = self.get_btms_max_power(timestep) # TODO this should be changed for DERMS to MPC output
        logging.debug("power desires updated for charging station {}".format(self.ChargingStationId))

        '''release vehicles when fully charged, this is already at the next timestep k+1'''
        self.reset_output() # here we reset the control output
        r1 = self.charging_bays_release_vehicles_and_add_to_output()
        r2 = self.queue_release_vehicles_and_add_to_output()
        logging.debug("vehicles released for charging station {}".format(self.ChargingStationId))
        released_Vehicles = r1 + r2
        
        # write vehicle states before releasing them (to have final SOC)
        for x in r1:
            possiblePower = x.get_max_charging_power(timestep)
            self.ResultWriter.update_vehicle_states(
                    t_act=self.SimBroker.t_act + timestep, vehicle=x, ChargingStationId=self.ChargingStationId, QueueOrBay=False, ChargingPower=0, possiblePower=possiblePower)
        for x in r2:
            possiblePower = x.get_max_charging_power(timestep)
            self.ResultWriter.update_vehicle_states(
                    t_act=self.SimBroker.t_act + timestep, vehicle=x, ChargingStationId=self.ChargingStationId, QueueOrBay=True, ChargingPower=0, possiblePower=possiblePower)

        # add release events
        for x in released_Vehicles:
            self.ResultWriter.release_event(
                self.SimBroker.t_act + timestep, x, self.ChargingStationId)
        logging.debug("vehicle release events written for charging station {}".format(self.ChargingStationId))

        '''checks'''
        if len(self.ChBaVehicles) != self.ChBaNum:
            raise ValueError("Size of ChargingBay List shouldn't change")
