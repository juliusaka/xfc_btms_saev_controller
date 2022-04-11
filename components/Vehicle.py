class Vehicle:
    def __init__(self, VehicleId, VehicleType, VehicleArrival, VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleMaxEngy, VehicleMaxPower): # the first inputs are from Beam, the last from the vehicle file
        self.VehicleId      = VehicleId                     # vehicle id
        self.VehicleType    = VehicleType                   # vehicle type
        self.VehicleArrival = VehicleArrival                # arrival time of vehicles
        self.VehicleDesEnd  = VehicleDesEnd                 # desired end times of charging
        self.VehicleEngy    = VehicleEngy                   # Energy State of vehicles [kWh]
        self.VehicleDesEngy = VehicleDesEngy                # desired Energy State of vehicles: level + fuel [kWh]
        self.VehicleSoc     = VehicleEngy / VehicleMaxEngy  # SOC of vehicles [-]
        self.VehicleMaxEngy = VehicleMaxEngy                # maximal energy state of vehicles [kWh]
        self.VehicleMaxPower= VehicleMaxPower               # maximal charging power of vehicles
        self.ChargingDesire = 0                             # charging desire of vehicle, assigned during control steps
    
    def __str__(self):
        # print method
        return ("Vehicle with the following properties: \nVehicleId: " + str(self.VehicleId) + " VehicleType: " + str(self.VehicleType) + " Arrival: " + str(self.VehicleArrival) + " Desired End Time: " + str(self.VehicleDesEnd) + " Vehicle Energy: " + str(self.VehicleEngy) + " Desired Energy: " + str(self.VehicleDesEngy) + " SOC: " + str(self.VehicleSoc) + " Maximal Energy: " + str(self.VehicleMaxEngy) + " Max Charging Power: "  + str(self.VehicleMaxPower))
        
    def addEngy(self, addedEngy):
        #addedEngy in kWh
        self.VehicleEngy    = self.VehicleEngy + addedEngy  # add energy 
        self.VehicleSoc     = self.VehicleEngy / self. VehicleMaxEngy # update SOC
        self.SOC_warning()

    def addPower(self, power, ts):
        # power in kW, ts in hours
        self.VehicleEngy    = self.VehicleEngy + ts * power/3.6e3 # add energy 
        self.VehicleSoc     = self.VehicleEngy / self. VehicleMaxEngy # update SOC
        self.SOC_warning()
        self.power_warning(power)

    def SOC_warning(self):
        if self.VehicleEngy > self.VehicleMaxEngy:
            print("Warning: Vehicle " + str(self.VehicleId) + " exceeds Vehicle Max SOC. Vehicle Energy " + str(self.VehicleEngy) + ", Vehicle Max Energy " + str(self.VehicleMaxEngy))
    
    def power_warning(self, power):
        if power > self.VehicleMaxPower:
            print("Warning: Vehicle " + self.VehicleId + " exceeds maximal charging power. Charging power " + str(power))