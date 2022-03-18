from components import Vehicle
import numpy as np

from components.ResultWriter import ResultWriter

class ChaDepParent:
    
    def __init__(self, ChargingStationId, ResultWriter: ResultWriter, BtmsSize = 100, BtmsC = 1, BtmsMaxSoc = 0.8, BtmsMinSOC = 0.2, BtmsSoc0 = 0.50, ChBaNum = 2, ChBaMaxPower = [200, 200], ChBaParkingZoneId = ["xxx1", "xxx2"], calcBtmsGridProp = False, GridPowerMax_Nom = 200, GridPowerLower = -1, GridPowerUpper = 1):

        '''ChargingStationIdentity'''
        self.ChargingStationId  = ChargingStationId

        '''Result Writer'''
        self.ResultWriter       = ResultWriter

        '''BTMS'''
        # properties
        if calcBtmsGridProp:
            self.BtmsSize       = sum(ChBaMaxPower)/2 #empirical formula (check with literature)
        else:
            self.BtmsSize       = BtmsSize          # size of the BTMS in kWh
        self.BtmsC              = BtmsC             # C-Rating of BTMS (1C is a complete charge an hour)
        self.BtmsMaxSoc         = BtmsMaxSoc        # maximal allowed SOC of BTMS
        self.BtmsMinSoc         = BtmsMinSOC        # minimal allowed SOC of BTMS
        #variables:
        self.BtmsEn             = BtmsSoc0 * BtmsSize # start BTMS energy content at initialization [kWh]
        self.BtmsSOC            = BtmsSoc0          # start SOC at initialization [-]


        '''Charging Bays'''
        #properties
        self.ChBaNum            = ChBaNum           # number of charging bays
        self.ChBaMaxPower       = ChBaMaxPower      # list of maximum power for each charging bay in kW
        self.ChBaMaxPower_abs   = max(ChBaMaxPower) # maximum value from list above
        self.ChBaParkingZoneId  = ChBaParkingZoneId # list of parking zone ids associated with max power list
        #variables
        self.ChBaVehicles       = []                # list for Vehicles objects, which are in charging bays.

        if (ChBaNum != len(ChBaMaxPower)):
            raise ValueError(' number of charging bays doesnt equals size of list with maximal plug power')
        if (ChBaNum != len(ChBaParkingZoneId)):
            raise ValueError(' number of charging bays doesnt equals size of list with parking zone ids')
        if (len(ChBaMaxPower) != len(ChBaParkingZoneId)):
            raise ValueError(' size of list with maximal plug power doesnt equals size of list with parking zone ids')
        

        '''Grid Constraints'''
        if calcBtmsGridProp:
            self.GridPowerMax_Nom   = sum(ChBaMaxPower)/2 # empirical formula (check with literature)
        else:
            self.GridPowerMax_Nom   = GridPowerMax_Nom  # maximum power withdrawal from grid, nominal value (can be time-varying)
        self.GridPowerLower         = GridPowerLower  # will be assigned in step function
        self.GridPowerUpper         = GridPowerUpper  # will be assigned in step function


        '''Queue of Vehicles'''
        #variables
        self.Queue                  = []                # list for Vehicles objects, which are in the queue.
        self.QueuePower             = []                # list for the associated power of queue vehicles, should be later set to 0 when returning data.

        '''Simulation Data'''
        self.t_act                  = float("NaN")


    def dayPlanning(self):
        # class method to perform day planning
        pass

    def arrival(self, vehicle: Vehicle):
        # class method to let vehicles arrive
        self.Queue.append(vehicle)
        self.ResultWriter.arrivalEvent(self.t_act, vehicle, self.ChargingStationId)

    def repark(self):
        # class method to repark the vehicles, based on their charging desire
        # calculate charging desire for every vehicle in the bays and the queue
        CD_Queue = []
        CD_Bays  = []
        for vehicle in self.Queue:
            CD_Queue.append(self.chargingDesire(vehicle))
        for vehicle in self.ChBaVehicles:
            CD_Bays.append(self.chargingDesire(vehicle))
        # change only, when vehicles in Bay have higher charging demand
        if len(CD_Queue) == 0:
            CD_Queue = [0]
        if len(CD_Bays) == 0:
            CD_Bays = [0]
        # sorting, so that the vehicles with highest charging desire are in Bays.
            # doesnt take charging speed capabilites into account
        while max(CD_Queue) > min(CD_Bays):
            i_Queue = np.argmax(CD_Queue)
            i_Bay   = np.argmin(CD_Bays)
            Queue_out = self.Queue.pop(i_Queue)
            Bay_out   = self.ChBaVehicles.pop(i_Bay)
            self.Queue.insert(i_Queue, Bay_out)
            self.ChBaVehicles.insert(i_Bay, Queue_out)
            # add repark events to ResultWriter
            self.ResultWriter.reparkEvent(self.t_act, Queue_out, self.ChargingStationId, "Bay", self.ChBaMaxPower[i_Bay])
            self.ResultWriter.reparkEvent(self.t_act, Bay_out, self.ChargingStationId, "Queue", 0)
        pass

    def chargingDesire(self, v: Vehicle):
        if v.VehicleDesEnd <= self.t_act:
            P_max = min([self.ChBaMaxPower, v.VehicleMaxPower])
            f1 = v.VehicleDesEngy - v.VehicleEngy # fraction part 1
            f2 = (v.VehicleDesEnd - self.t_act) * P_max
            CD = float("inf")
        else:
            CD = f1/f2
        v.CharginDesire = CD
        return CD

    def release(self,):
        # class method to release vehicles
        # TODO will this be done by the chargingStation itself?
        #self.ResultWriter.releaseEvent(self.t_act, )
        pass
    
    def step(self, timestep, t_act): # call with t_act = SimBroker.t_act
        self.t_act = t_act
        # class method to perform control action for the next simulation step.
        '''Requirements:'''
            # release vehicles when full from charging bays
            # repark vehicles from queue to charging bays if possible
            # update control action from last step with new results for SOC, P_total, P_Btms
            # perform controller action
            # function INPUTS: Grid Limits, Revised SOC of Storage, 
            #                  Revised power withdrawals from last step
            # function OUTPUTS: Power from Grid, from BTMS
        pass

        