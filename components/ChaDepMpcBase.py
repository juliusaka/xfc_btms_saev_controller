from components import ChaDepParent
from components import SimBroker
import numpy as np

class ChaDepMpcBase(ChaDepParent):

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

    def initializePlanning(self, BeamPredictionFile, dtype, addNoise = True):
        # generate a prediction for the charging station
        # neglection of charging desire, make this not too good
        ChBaVehicles = []
        Queue = []
        time = []
        power = []
        #open a SimBroker object for this
        PredBroker = SimBroker(BeamPredictionFile, dtype)
            # find out if current element belongs to this chargingStation
        time.append(PredBroker.t_act)
        
        while not PredBroker.eol(): 
            
            np.isin(element = self.ChBaParkingZoneId, test_elements= ['X-PEV-9-1']).any()
        del SimBroker
        pass
    
    def planning(self, t_act):
        pass