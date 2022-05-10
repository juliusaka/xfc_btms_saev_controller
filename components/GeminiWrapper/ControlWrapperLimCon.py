import components
from components.SimBroker import SimBroker

class ControlWrapperLimCon():
    # A Wrapper for the Limit Controller

    def __init__(self, parkingZoneId, info_plugs, result_directory, simName, t_start, path_vehicleDatabase) -> None:
        ''' init SimBroker Dummy , VehicleGenerator and ResultWriter'''
        self.SimBroker = components.GeminiWrapper.SimBrokerDummy(t_start) # central timekeeper
        # TODO a VehicleGenerator for Gemini
        self.ResultWriter = components.ResultWriter(result_directory, simName)

        '''create charging station object'''
        ChargingStationId = parkingZoneId # TODO: how do we wanna name the charging station?
        ChBaMaxPower            = []      # TODO: how to get this from info_plugs; list of maximal power per plug
        ChBaParkingZoneId       = []      # TODO: how to get this from info_plugs; list of plug ids
        ChBaNum                 = len(ChBaNum)
        self.ChargingStation = components.ChaDepLimCon(ChargingStationId=ChargingStationId, ResultWriter=self.ResultWriter, SimBroker = self.SimBroker, ChBaMaxPower=ChBaMaxPower, ChBaParkingZoneId=ChBaParkingZoneId, ChBaNum = ChBaNum ,calcBtmsGridProp = True)

        '''write chargingStationProperties to ResultWriter'''
        self.ResultWriter.saveChargingStationProperties([self.ChargingStation]) # this function takes a list of charging station as input argument

        # probably not necessary: PhySim and DERMS Dummy


    def departure(self, vehicleId) -> None:
        # TODO for future implementation, should throw an error message to the results
        pass

    def arrival(self, vehicleId, vehicleType, arrivalTime, desiredDepartureTime, primaryFuelLevelinJoules, desiredFuelLevelInJoules) -> None:
        #vehicle = self.VehicleGenerator() TODO integration vehicle generator
        #self.ChargingStation.arrival(vehicle, self.SimBroker.t_act)
        pass

    def step (self, timestep):
        self.ChargingStation.step(timestep)
        
        # TODO: provide control outputs to BEAM
        control_command_list = []
        for i in range(0, len(self.Vehicles)):
            control_command_list.append({
                'vehicleId': str(self.Vehicles[i]),
                'power': str(power),
                'release': str(release[i])
            })
        return control_command_list

    def saveResults(self):
        self.ResultWriter.save()

    #####################################
    # MAKE SURE TO SAVE RESULTS IN THE END WHEN SHUTTING DOWN FEDERATE
    #####################################

    