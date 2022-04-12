from time import time
from components import ChaDepParent
import numpy as np

from components.SimBroker import SimBroker
from components.Vehicle import Vehicle

class ChaDepLimCon(ChaDepParent):

    def step(self, timestep):
        # class method to perform control action for the next simulation step.
        '''repark vehicles based on their charging desire with the parent method'''
        self.repark()

        ''' control action'''
        '''# calculate maximum summed charging power, for 3 different cases'''
        if self.BtmsSoc() <= self.BtmsMinSoc:
            P_max = self.GridPowerUpper
        # if Btms energy content is large enough to power for the next timestep full discharge rating
        elif self.BtmsEn - timestep/3.6e3 * self.BtmsMaxPower >= self.BtmsSize * self.BtmsMinSoc:
            P_max = self.GridPowerUpper + self.BtmsMaxPower
        # this is the intermediate case and the chargingPower to reach the minimum SOC
        else:
            P_max = self.GridPowerUpper + (self.BtmsEn - self.BtmsSize * self.BtmsMinSoc) / (timestep/3.6e3)
        
        '''# now assign the charging powers to each vehicle, prioritized by their charging desire'''
        self.ChBaPower = [] # delete charging power of previous timestep
        CD_Bays = [] # list of charging desire of the vehicles in bays
        for x in self.ChBaVehicles:
            self.ChBaPower.append(0) # make list of charging power with corresponding size
            if type(x) == Vehicle:
                CD_Bays.append(-1* x.ChargingDesire) # multiply with -1 to have an sorted descending list
            else:
                CD_Bays.append(float('nan')) # add nan if no vehicle is in Bay
        idx_Bays = np.argsort(CD_Bays)
        for i in range(0, len(self.ChBaVehicles)): # go through charging bays sorted by their charging desire
            j = idx_Bays[i] # save index of current charging bay in j
            if type(self.ChBaVehicles[j]) == Vehicle: # only assign charging power, if a vehicle is in the bay
                maxPower = min([self.ChBaMaxPower[j], self.ChBaVehicles[j].getMaxChargingPower(timestep)]) # the maximum power of the current bay is the minimum of the chargingbay max power and the vehicle max power
                sumPowers = sum(self.ChBaPower)
                if  sumPowers + maxPower <= P_max: # test if maxPower of current bay can be fully added
                    self.ChBaPower[j] = maxPower
                elif sumPowers < P_max: # test if intermediate value can be added
                    self.ChBaPower[j] = P_max - sumPowers
                else: # if no power adding is possible, we can leave this loop.
                    break

        '''# now find out how to charge or discharge BTMS''' 
        sumPowers = sum(self.ChBaPower)
        # if sum of charging power is greater than grid power limit, the btms must be discharged
        if sumPowers >= self.GridPowerUpper:
            self.BtmsPower = self.GridPowerUpper - sumPowers # result is negative
        # if that is not the case, we might be able to charge with full power for one timestep, if we don't exceed BtmsMaxSOC with this
        elif self.BtmsEn <= self.BtmsSize * self.BtmsMaxSoc - self.BtmsMaxPower * timestep/3.6e3:
            self.BtmsPower = min([self.BtmsMaxPower, self.GridPowerUpper - sumPowers])
        # if that doesn't work, we can charge with an intermediate value:
        elif self.BtmsEn < self.BtmsSize * self.BtmsMaxSoc:
            self.BtmsPower = min([self.BtmsMaxPower, (self.BtmsSize * self.BtmsMaxSoc - self.BtmsEn) / (timestep/3.6e3), self.GridPowerUpper - sumPowers])
        # if that doesn't work, it seems like Btms is full, then charging power is 0.
        else:
            self.BtmsPower = 0
        
        '''# update SOC values'''
        # BTMS
        self.BtmsAddPower(self.BtmsPower, timestep)
        # Vehicles
        for i in range(0, len(self.ChBaVehicles)):
            if type(self.ChBaVehicles[i]) == Vehicle:
                #print('updateSOC')
                self.ChBaVehicles[i].addPower(self.ChBaPower[i], timestep)
        
        # result Writer for chargingStation states and vehicle states
        for i in range(0, len(self.ChBaVehicles)):
            if type(self.ChBaVehicles[i]) == Vehicle:
                self.ResultWriter.updateVehicleStates(t_act = self.SimBroker.t_act + timestep, vehicle=self.ChBaVehicles[i], ChargingStationId=self.ChargingStationId, QueueOrBay=False, ChargingPower=self.ChBaPower[i])
        for i in range(0, len(self.Queue)):
            self.ResultWriter.updateVehicleStates(t_act = self.SimBroker.t_act + timestep, vehicle=self.Queue[i], ChargingStationId=self.ChargingStationId, QueueOrBay=True, ChargingPower=0)

        '''determine power desire for next time step'''
        PowerDesire = 0
        for i in range(0,len(self.ChBaVehicles)):
            if type(self.ChBaVehicles[i]) == Vehicle:
                PowerDesire += min([self.ChBaVehicles[i].getMaxChargingPower(timestep), self.ChBaMaxPower[i]])

        self.PowerDesire = PowerDesire

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
        