from msilib.schema import Error
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
        self.BtmsPower       = 0                    # actual charging power of the btms

        '''Charging Bays'''
        #properties
        self.ChBaNum            = len(ChBaParkingZoneId)# number of charging bays
        self.ChBaMaxPower       = ChBaMaxPower      # list of maximum power for each charging bay in kW
        self.ChBaMaxPower_abs   = max(ChBaMaxPower) # maximum value from list above
        self.ChBaParkingZoneId  = ChBaParkingZoneId # list of parking zone ids associated with max power list
        #variables
        self.ChBaVehicles       = self.chBaInit(self.ChBaNum) # list for Vehicles objects, which are in charging bays.
        if (len(ChBaMaxPower) != len(ChBaParkingZoneId)):
            raise ValueError(' size of list with maximal plug power doesnt equals size of list with parking zone ids')
        # variables
        self.ChBaPower          = []                # this is the variable to which charging power for each bay is assigned.
        
        

        '''Grid Constraints'''
        if calcBtmsGridProp:
            self.GridPowerMax_Nom   = sum(ChBaMaxPower)/2 # empirical formula (check with literature)
        else:
            self.GridPowerMax_Nom   = GridPowerMax_Nom  # maximum power withdrawal from grid, nominal value (can be time-varying)
        self.GridPowerLower         = GridPowerLower  # will be assigned in step function
        self.GridPowerUpper         = GridPowerUpper  # will be assigned in step function

        '''Power Desire'''
        self.PowerDesire            = 0               # Power Desire to DERMS

        '''Queue of Vehicles'''
        #variables
        self.Queue                  = []                # list for Vehicles objects, which are in the queue.

        '''Simulation Data'''
        self.SimBroker              = SimBroker

    def BtmsSoc(self):
        return self.BtmsEn/self.BtmsSize

    def BtmsAddPower(self, power, timestep):
        # power in kW and timestep in s
        self.BtmsEn += power * timestep/3.6e3
    
    def chBaInit(self, ChBaNum):
        # initialize the list of ChargingBay Vehicles with False for no vehicles parked
        ChBaVehicles = []
        for i in range(0, ChBaNum):
            ChBaVehicles.append(False)
        return ChBaVehicles

    def chBaActiveCharges(self):
        num_Charges = 0
        for x in self.ChBaVehicles:
            if not x == False:
                num_Charges +=1
        return num_Charges
    
    def chBaAdd(self, vehicle):
        # add a vehicle to the charging Bay
        did_add = False
        for i in range(0, len(self.ChBaVehicles)):
            if self.ChBaVehicles[i] == False:
                self.ChBaVehicles.insert(i, vehicle)
                did_add = True
                j = i
                break # can leave after adding
        if did_add == False:
            print(vehicle)
            print(self.ChargingStationId)
            pass #raise ValueError('The Vehicle couldnt be added')
        #returns the positions  where vehicle was added.
        return j

    def sortVehicleOut(self, threshold, list):
        # threshold gives a threshold of desired energy, after which vehicle can be released.
        pop = []
        out = []
        for i in range(0, len(list)):
            # find out which indices need to be popped out
            if type(list[i]) == Vehicle:
                if list[i].VehicleEngy > threshold * list[i].VehicleDesEngy:
                    pop.append(i)
        # pop this indices out
        for i in range(0, len(pop)):
            out.append(list.pop(pop[i]-i)) # to make up the loss of popped out elements before
        return out, list

    def chBaReleaseThreshold(self, threshold = 0.9999):
        (out, self.ChBaVehicles) = self.sortVehicleOut(threshold, self.ChBaVehicles)
        return out
    
    def queueReleaseThreshold(self, threshold = 0.9999):
        (out, self.Queue) = self.sortVehicleOut(threshold, self.Queue)
        return out
 
    def dayPlanning(self):
        # class method to perform day planning
        pass

    def arrival(self, vehicle: Vehicle):
        # class method to let vehicles arrive
        # calculate charging desire
        vehicle.ChargingDesire = self.chargingDesire(vehicle)
        self.Queue.append(vehicle)
        self.ResultWriter.arrivalEvent(self.SimBroker.t_act, vehicle, self.ChargingStationId)
        self.ResultWriter.updateVehicleStates(t_act = self.SimBroker.t_act, vehicle=vehicle, ChargingStationId=self.ChargingStationId, QueueOrBay=True, ChargingPower=0)
        

    def repark(self):
        # class method to repark the vehicles, based on their charging desire

        # add vehicles to charging bays if possible
        while self.chBaActiveCharges() < self.ChBaNum and len(self.Queue) > 0:
            add = self.Queue.pop(0)
            pos = self.chBaAdd(add)
            self.ResultWriter.reparkEvent(self.SimBroker.t_act, add, self.ChargingStationId, True, self.ChBaMaxPower[pos])

        # update charging desire for every vehicle in the bays and the queue
        CD_Queue = []
        CD_Bays  = []
        for vehicle in self.Queue:
            CD_Queue.append(self.chargingDesire(vehicle))
        for vehicle in self.ChBaVehicles:
            if type(vehicle) == Vehicle:
                CD_Bays.append(self.chargingDesire(vehicle))
            else:
                CD_Bays.append(-float('inf')) # shouldn't be used at all later

        ''' sorting approach 2'''
        # sort vehicles based on their charging desire and add them to charging bays or queue. Make sure, that you don't shuffle vehicles within the charging bays.
        if len(self.Queue) > 0: # we only need to sort, if we have cars which are not plugged in. If that is the case, every entry in the self.ChBaVehicles list should be of type Vehicle
            CD_merged = CD_Bays + CD_Queue 
            allVehicles = self.ChBaVehicles + self.Queue

            for i in range(0,len(CD_merged)):# change sign to make list descending
                CD_merged[i] = -1* CD_merged[i]
            idx_sorted = np.argsort(CD_merged, kind= 'stable') [::-1] # [::-1] reverses the list to have it descending
            n = self.ChBaNum
            idx_Bay_new = idx_sorted[:n]    #this are the vehicles, which should be plugged in
            idx_Bay_newStable = []          #this is a stable indice list of vehicles which are plugged in
            idx_Bay_old = range(0,n)        #this is a indice list of vehicles which have been charging before
            idx = np.isin(element = idx_Bay_old, test_elements=idx_Bay_new) # if true, the vehicle in the old list of vehicles in charging bays is also in the new
            idx_inv = np.isin(element = idx_Bay_new, test_elements=idx_Bay_old) # if false, the vehicle of the new list of vehicles in the charging bays have not been in the old (and should be added)
            j = 0   # variable, read index in idx_inv
            for i in range(0, n):
                if idx[i]:
                    idx_Bay_newStable.append(i)
                else:
                    while idx_inv[j] == True:
                        j+=1
                    idx_inv[j] = True
                    idx_Bay_newStable.append(idx_Bay_new[j])
                    num = idx_Bay_new[j]
                    self.ResultWriter.reparkEvent(SimBroker.t_act, allVehicles[num], self.ChargingStationId, False, self.ChBaMaxPower[num])
            idx_Queue_new_bool = np.isin(element = range(0,len(CD_merged)), test_elements = idx_Bay_newStable, invert=True) # these are the vehicles which are now in the queue
            idx_Queue_new = [] # this is a list to save their indices
            for i in range(0, len(idx_Queue_new_bool)):
                if idx_Queue_new_bool[i]:
                    idx_Queue_new.append(i)

            idx_from_Bay_to_Queue = np.isin(element = idx_Queue_new, test_elements = range(0, len(self.ChBaVehicles))) # this is to determine if a vehicle was reparked from Bay to Queue
            self.ChBaVehicles = []
            self.Queue = []
            for i in idx_Bay_newStable:
                self.ChBaVehicles.append(allVehicles[i])
            for i in range(0,idx_Queue_new):
                self.Queue.append(allVehicles[i])
                if idx_from_Bay_to_Queue[i]:
                    self.ResultWriter.reparkEvent(SimBroker.t_act, allVehicles[num], self.ChargingStationId, True, self.ChBaMaxPower[num])

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

        