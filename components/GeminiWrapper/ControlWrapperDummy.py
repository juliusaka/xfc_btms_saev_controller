import components
class ControlWrapperDummy():

    def __init__(self) -> None:
        self.Vehicles = [] # list for vehicle ids
        self.stay_length = []
    
    def departure(self, vehicleId) -> None:
        # for future implementation, should throw an error message
        pass

    def arrival(self, vehicleId, vehicleType, arrivalTime, desiredDepartureTime, primaryFuelLevelinJoules, desiredFuelLevelInJoules) -> None:
        self.Vehicles.append(vehicleId)
        self.stay_length.append(0)

    def step (self, timestep):
        power = 500
        delete = []
        release = []
        for i in range(0, len(self.Vehicles)):
            self.stay_length[i] += 1
            if self.stay_length[i] > 2: # release vehicles after 3 charging iterations
                delete.append(i)
                release.append(True)
            else:
                release.append(False)

        control_command_list = []
        for i in range(0, len(self.Vehicles)):
            control_command_list.append({
                'vehicleId': str(self.Vehicles[i]),
                'power': str(power),
                'release': str(release[i])
            })
        
        # delete release vehicles from charging station
        for i in range(0, len(delete)):
            self.stay_length.pop(delete[i] - i)
            self.Vehicles.pop(delete[i] - i)

        return control_command_list

    