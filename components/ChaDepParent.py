from components import Vehicle
from components import ResultWriter
from components import SimBroker
import numpy as np

class ChaDepParent:
    
    def __init__(self, ChargingStationId, ResultWriter: ResultWriter, SimBroker: SimBroker, ChBaMaxPower, ChBaParkingZoneId, BtmsSize = 100, BtmsC = 1, BtmsMaxSoc = 0.8, BtmsMinSOC = 0.2, BtmsSoc0 = 0.50, calcBtmsGridProp = False, GridPowerMax_Nom = 1 , GridPowerLower = -1, GridPowerUpper = 1):

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
        self.BtmsC              = BtmsC             # C-Rating of BTMS (1C is a complete charge an hour) C= [1/h]
        self.BtmsMaxPower       = BtmsC * self.BtmsSize
        self.BtmsMaxSoc         = BtmsMaxSoc        # maximal allowed SOC of BTMS
        self.BtmsMinSoc         = BtmsMinSOC        # minimal allowed SOC of BTMS
        #variables:
        self.BtmsEn             = BtmsSoc0 * self.BtmsSize # start BTMS energy content at initialization [kWh]

        '''Charging Bays'''
        #properties
        self.ChBaNum            = len(ChBaParkingZoneId)# number of charging bays
        self.ChBaMaxPower       = ChBaMaxPower      # list of maximum power for each charging bay in kW
        self.ChBaMaxPower_abs   = max(ChBaMaxPower) # maximum value from list above
        self.ChBaParkingZoneId  = ChBaParkingZoneId # list of parking zone ids associated with max power list
        #variables
        self.ChBaVehicles       = []                # list for Vehicles objects, which are in charging bays.

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

        '''Simulation Data'''
        self.SimBroker              = SimBroker

    def BtmsSoc(self):
        return self.BtmsEn/self.BtmsSize

    def dayPlanning(self):
        # class method to perform day planning
        pass

    def arrival(self, vehicle: Vehicle):
        # class method to let vehicles arrive
        # calculate charging desire
        vehicle.ChargingDesire = self.chargingDesire(vehicle)
        self.Queue.append(vehicle)
        self.ResultWriter.arrivalEvent(self.SimBroker.t_act, vehicle, self.ChargingStationId)

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
        # add vehicles to charging bays if possible
        '''please add this!'''
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
            self.ResultWriter.reparkEvent(self.SimBroker.t_act, Queue_out, self.ChargingStationId, "Bay", self.ChBaMaxPower[i_Bay])
            self.ResultWriter.reparkEvent(self.SimBroker.t_act, Bay_out, self.ChargingStationId, "Queue", 0)
        pass

    def chargingDesire(self, v: Vehicle):
        if not self.SimBroker.t_act >= v.VehicleDesEnd:
            P_max = min([self.ChBaMaxPower_abs, v.VehicleMaxPower])
            f1 = v.VehicleDesEngy - v.VehicleEngy # fraction part 1
            f2 = (v.VehicleDesEnd - self.SimBroker.t_act) * P_max / 3.6e3
            CD = f1/f2
        else:
            CD = float("inf")
        v.ChargingDesire = CD
        return CD

    def release(self,):
        # class method to release vehicles
        # TODO will this be done by the chargingStation itself?
        #self.ResultWriter.releaseEvent(self.SimBroker.t_act, )
        pass
    
    def initialize(self, GridPowerLower, GridPowerUpper):
        self.GridPowerLower = GridPowerLower
        self.GridPowerUpper = GridPowerUpper
    
    def updateFromDerms(self, GridPowerLower: float, GridPowerUpper: float) -> None:
        self.GridPowerLower = GridPowerLower
        self.GridPowerUpper = GridPowerUpper

    def updateFromPhySim(self, CesSoc: float):
        pass
        #self.BtmsEn = self.BtmsSize * CesSoc

    def step(self, timestep): # call with t_act = SimBroker.t_act
        # class method to perform control action for the next simulation step.
        '''Requirements:'''
            # release vehicles when full from charging bays
            # repark vehicles from queue to charging bays if possible
        self.repark()
            # update control action from last step with new results for SOC, P_total, P_Btms
            # perform controller action
            # function INPUTS: Grid Limits, Revised SOC of Storage, 
            # function OUTPUTS: Power from Grid, from BTMS
        pass

        