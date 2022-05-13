import components
from components.SimBroker import SimBroker

'''Need to be updated to new control scheme'''

class ControlWrapperLimCon():
    # A Wrapper for the Limit Controller

    def __init__(self, parkingZoneId, info_plugs, result_directory, simName, t_start, path_vehicleDatabase) -> None:
        ChargingStationId = parkingZoneId # TODO: how do we wanna name the charging station?
        ''' init SimBroker Dummy , VehicleGenerator and ResultWriter'''
        self.SimBroker          = components.GeminiWrapper.SimBrokerDummy(t_start) # central timekeeper
        self.VehicleGenerator   = components.GeminiWrapper.VehicleGeneratorBeam(path_vehicleDatabase)
        self.ResultWriter       = components.ResultWriter(result_directory, simName, saveInGemini=True, chargingStationId=str(ChargingStationId))

        '''create charging station object'''
        #ChargingStationId  assigned above to use its name to create chargingStationDirectory
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
        vehicle = self.VehicleGenerator.generateVehicle(VehicleId = vehicleId, VehicleType = vehicleType, VehicleArrival = arrivalTime, VehicleDesEnd = desiredDepartureTime, primaryFuelLevelInJoules = primaryFuelLevelinJoules, desiredFuelLevelInJoules = desiredFuelLevelInJoules)
        self.ChargingStation.arrival(vehicle, self.SimBroker.t_act)

    def step (self, timestep):
        self.ChargingStation.step(timestep)

        vehicles, power, release = self.ChargingStation.getControlOutput()

        control_command_list = []
        for i in range(0, len(vehicles)):
            control_command_list.append({
                'vehicleId': str(vehicles[i]),
                'power': str(power[i]),
                'release': str(release[i])
            })
        return control_command_list

    def saveResults(self):
        self.ResultWriter.save()

    #####################################
    # MAKE SURE TO SAVE RESULTS IN THE END WHEN SHUTTING DOWN FEDERATE
    #####################################

    