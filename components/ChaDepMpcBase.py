import components
from components import ChaDepParent
import numpy as np
import cvxpy as cp
import cvxpy.atoms.max as cpmax

class ChaDepMpcBase(ChaDepParent):
    '''see mpcBase.md for explanations'''

    def __init__(self, ChargingStationId, ResultWriter: components.ResultWriter, SimBroker: components.SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize=100, BtmsC=1, BtmsMaxSoc=0.8, BtmsMinSOC=0.2, BtmsSoc0=0.5, calcBtmsGridProp=False, GridPowerMax_Nom=1, GridPowerLower=-1, GridPowerUpper=1):

        super().__init__(ChargingStationId, ResultWriter, SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize, BtmsC, BtmsMaxSoc, BtmsMinSOC, BtmsSoc0, calcBtmsGridProp, GridPowerMax_Nom, GridPowerLower, GridPowerUpper)

        '''additional variables for btms size optimization'''
        self.determinedBtmsSize = None
        self.determinedMaxPower = None

        '''additional variables for MPC:'''
        self.PredictionTime = []
        self.PredictionPower = []
        self.power_sum_original = []
        self.PredictionGridUpper = []
        self.PreidctionGridLower = []


    def generatePredictions(self, path_BeamPredictionFile, dtype, path_DataBase, timestep=5*60, addNoise = True):
        # generate a prediction for the charging station
        # neglection of charging desire, make this not too good
        ChBaVehicles = []
        Queue = []
        time = []
        power_sum = []
        #open a SimBroker object for this
        PredBroker = components.SimBroker(path_BeamPredictionFile, dtype)
        # open a VehicleGenerator for this:
        VehicleGenerator = components.VehicleGenerator(path_BeamPredictionFile, dtype, path_DataBase)
        #print("check 1")

        #add all vehicle to queue which arrive at this charging station
        while not PredBroker.eol():
            #print("check 1.5")
            slice = PredBroker.step(timestep)
            for i in range(0, len(slice)):
                #print("check 1.9")
                if slice.iloc[i]["type"] == "ChargingPlugInEvent":
                    vehicle = VehicleGenerator.generateVehicleSO(slice.iloc[i], AddParkingZoneId=True)
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
        if addNoise:
            param = 0.10
            avg = np.average(power_sum)
            self.power_sum_original = power_sum.copy()
            for i in range(0,len(power_sum)):
                 power_sum[i] = power_sum[i] + avg * (np.random.randn() * param)
                 if power_sum[i] < 0:
                     power_sum[i] = 0
        # save to Prediction Variables
        self.PredictionTime = time
        self.PredictionPower = power_sum

        # generate a prediction for power limits
        for i in time:
            self.PredictionGridUpper.append(self.GridPowerMax_Nom)
            self.PreidctionGridLower.append(- self.GridPowerMax_Nom)

    def determineBtmsSize(self, t_act, t_max, timestep, a, b, c, P_free):
        '''see mpcBase.md for explanations'''
        # vector lengthes
        T = int(np.floor((t_max - t_act) / timestep))

        # define variables 
        x = cp.Variable((1, T+1))
        u = cp.Variable((4, T))
        p_gridSlack = cp.Variable((1,1)) # slack variable to determine demand charge with free demand charge level, e.g. if p_max > 20kW, demand charge applied
        
        # define disturbance d, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_max)
        i_power = power[idx]
        if len(i_power) != T:
            print("length d", len(i_power))
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
        E_BTMS = x[0,:-1].value
        P_Charge = i_power
        P_BTMS_Ch = u[2,:].value
        P_BTMS_DCh = u[3,:].value
        cost = prob.value

        self.determinedBtmsSize = btms_size
        self.determinedMaxPower = max(abs(P_BTMS))

        return time, btms_size, P_Grid, P_BTMS, P_BTMS_Ch, P_BTMS_DCh, E_BTMS, P_Charge, cost

    def planning(self, t_act, t_max, timestep, a, b, c, d_param, P_free, P_ChargeAvg):
        '''see mpcBase.md for explanations'''
        # vector lengthes
        T = int(np.floor((t_max - t_act) / timestep))

        # define variables 
        x = cp.Variable((2, T+1))
        u = cp.Variable((5, T))
        t_lag = cp.Variable((1,T)) # slack variable for time lag
        p_gridSlack = cp.Variable((1,1)) # slack variable to determine demand charge with free demand charge level, e.g. if p_max > 20kW, demand charge applied
        
        # define disturbance i_power, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_max)
        i_power = power[idx]
        if len(i_power) != T:
            print("length d", len(i_power))
            print("length T", T)
            raise ValueError("length T and length of vector d are unequal")

        #create array for cost-function parameter d
        d = []
        for i in range(len(i_power)):
            d.append(d_param)

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # tuning parameters
        constr = []
        # define constraints
        for k in range(T):
            constr += [x[0,k+1] == x[0,k] + ts * eta * u[2,k] + ts * 1/eta * u[3,k], # BTMS equation
                        x[1,k+1] == x[1,k] + ts * u[4,k], # shifted energy equation
                        i_power[k] - u[4,k] == u[0,k] - u[1,k], # energy flow equation
                        u[1,k] == u[2,k] + u[3,k], # P_BTMS is sum of charge and discharge
                        u[2,k] >= 0, # charging power always positive
                        u[3,k] <= 0, # discharge power always negative^
                        x[0,k] >= 0, # lower limit of BTMS size
                        x[0,k] <= self.BtmsSize, # upper limit of BTMS size
                        t_lag[0,k] >= (x[1,k+1]-x[1,k])/P_ChargeAvg, #time lag is the increase in energy lag
                        t_lag[0,k] >= 0 # lower bound of time lag.
                        ]
        # insert initial constraint, bound BTMS size and define free power level
        constr +=  [x[0,0] == x[0,T], # ensure not to discharge BTMS to minimize cost function
                    p_gridSlack >= cpmax(u[0,:]),
                    p_gridSlack >= P_free,
                    ]
        
        # define cost-funciton
        cost = a * (p_gridSlack - P_free) # demand charg
        for k in range(T):       # cost of btms degradation and cost of energy loss
            cost += (b+c) * u[2,k] * ts + c * u[3,k] * ts + d[k] * t_lag[0,k] # u[3,k] is always negative

        # solve the problem
        prob = cp.Problem(cp.Minimize(cost), constr)
        prob.solve()

        # determine BTMS size and unpack over values
        btms_size = np.max(x.value) - np.min(x.value)
        P_Grid = u[0,:].value
        P_BTMS = u[1,:].value
        E_BTMS = x[0,:-1].value
        P_Charge = i_power
        P_BTMS_Ch = u[2,:].value
        P_BTMS_DCh = u[3,:].value
        cost = prob.value
        pass

    def step(self, timestep):

        '''repark vehicles based on tehir charging desire with the parent method'''
        self.repark()

        '''insert here the control action'''

        '''assign values to:
        self.ChBaPower
        self.BtmsPower
        DONE: self.PowerDesire # for DERMS
        DONE: self.BtmsPowerDesire # for DERMS
        '''

        '''update SOC and Result Writer for Vehicles'''
        # BTMS
        self.BtmsAddPower(self.BtmsPower, timestep)
        # Vehicles
        self.updateVehicleStatesAndWriteResults(self.ChBaPower, timestep)

        '''determine power desire for next time step
                this must be done after Vehicle and BTMS states are updated, so that charging curves can be taken into account'''
        PowerDesire = 0
        for i in range(0,len(self.ChBaVehicles)):
            if self.ChBaVehicles[i] != False:
                PowerDesire += min([self.ChBaVehicles[i].getMaxChargingPower(timestep), self.ChBaMaxPower[i]])

        self.PowerDesire = PowerDesire
        self.BtmsPowerDesire = self.getBtmsMaxPower(timestep)

        '''Write chargingStation states in ResultWriter'''
        self.ResultWriter.updateChargingStationState(self.SimBroker.t_act, self)

        '''release vehicles when full'''
        r1 = self.chBaReleaseThreshold()
        r2 = self.queueReleaseThreshold()
        released_Vehicles = r1 + r2
        # add release events
        for x in released_Vehicles:
            self.ResultWriter.releaseEvent(self.SimBroker.t_act, x, self.ChargingStationId)

        '''checks'''
        if len(self.ChBaVehicles)!=self.ChBaNum:
            raise ValueError("Size of ChargingBay List shouldn't change")