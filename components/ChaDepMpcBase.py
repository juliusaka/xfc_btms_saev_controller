import components
from components import ChaDepParent
import numpy as np
import cvxpy as cp
import cvxpy.atoms.max as cpmax
import cvxpy.atoms.min as cpmin

class ChaDepMpcBase(ChaDepParent):

    def __init__(self, ChargingStationId, ResultWriter: components.ResultWriter, SimBroker: components.SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize=100, BtmsC=1, BtmsMaxSoc=0.8, BtmsMinSOC=0.2, BtmsSoc0=0.5, calcBtmsGridProp=False, GridPowerMax_Nom=1, GridPowerLower=-1, GridPowerUpper=1):

        super().__init__(ChargingStationId, ResultWriter, SimBroker, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, BtmsSize, BtmsC, BtmsMaxSoc, BtmsMinSOC, BtmsSoc0, calcBtmsGridProp, GridPowerMax_Nom, GridPowerLower, GridPowerUpper)

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

    def planning(self, t_act, t_max, timestep):
        # vector lengthes
        T = np.floor((t_max - t_act) / timestep)

        # define variables 
        x = cp.Variable((1, T+1))
        u = cp.Variable((2, T))
        
        # define disturbance d, which is the charging power demand
        time = np.array(self.PredictionTime)
        power = np.array(self.PredictionPower)
        idx = np.logical_and(time >=t_act, time <= t_max)
        d = power[idx]
        if len(d) != T:
            print("length d", len(d))
            print("length T", T)
            raise ValueError("length T and length of vector d are unequal")

        #parameters
        ts = timestep / 3.6e3
        eta = self.BtmsEfficiency

        # tuning parameters
        a = 1
        b = 1
        constr = []
        # define constraints
        for k in range(T):
            constr += [x[:,k+1] == x[:,k] + ts * eta * u[1,k],
                        u[0,k] - u[1,k] >= d[k]]
        # insert initial constraint and bound BTMS size
        constr += [x[:,0]== 0,
                    x[:,0] == x[:,T]]
        
        # define cost-funciton
        cost = a * cpmax(u[0,:]) + b*(cpmax(x) - cpmin(x))

        # solve the problem
        prob = cp.Problem(cp.Minimize(cost), constr)

        # determine BTMS size
        btms_size = max(x.value) - min(x.value)
        P_Grid = u[0,:].value
        P_BTMS = u[1,:].value
        E_BTMS = x.value
        P_Charge = d
        
        return btms_size, P_Grid, P_BTMS, E_BTMS, P_Charge

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