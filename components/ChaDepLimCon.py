from time import time
from components import ChaDepParent
import numpy as np

from components.SimBroker import SimBroker
from components.Vehicle import Vehicle
import components

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
        self.distributeChargingPowerToVehicles(timestep, P_max)

        '''# now find out how to charge or discharge BTMS''' 
        sumPowers = sum(self.ChBaPower)
        # if sum of charging power is greater than grid power limit, the btms must be discharged
        if sumPowers >= self.GridPowerUpper:
            self.BtmsPower = self.GridPowerUpper - sumPowers # result is negative
        # if that is not the case, we might be able to charge for one timestep, if SOC < Max SOC
        elif self.BtmsEn < self.BtmsSize * self.BtmsMaxSoc:
            self.BtmsPower = min([self.getBtmsMaxPower(timestep), self.GridPowerUpper - sumPowers])
        # if that doesn't work, it seems like Btms is full, then charging power is 0.
        else:
            self.BtmsPower = 0

        '''Write chargingStation states for k in ResultWriter'''
        self.ResultWriter.updateChargingStationState(self.SimBroker.t_act, self)

        '''# update BTMS state for k+1'''
        # BTMS
        self.BtmsAddPower(self.BtmsPower, timestep)

        '''write vehicle states for k in ResultWriter and update vehicle states for k+1'''
        # Vehicles
        self.updateVehicleStatesAndWriteStates(self.ChBaPower, timestep)

        '''determine power desire for next time step'''
        PowerDesire = 0
        for i in range(0,len(self.ChBaVehicles)):
            if isinstance(self.ChBaVehicles[i], components.Vehicle):
                PowerDesire += min([self.ChBaVehicles[i].getMaxChargingPower(timestep), self.ChBaMaxPower[i]])

        self.PowerDesire = PowerDesire
        self.BtmsPowerDesire = self.getBtmsMaxPower(timestep)

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
        