class Vehicle:
    def __init__(self, VehicleId, VehicleType, VehicleArrival, VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleMaxEngy): # the first inputs are from Beam, the last from the vehicle file
        self.VehicleId      = VehicleId                     # vehicle id
        self.VehicleType    = VehicleType                   # vehicle type
        self.VehicleArrival = VehicleArrival                # arrival time of vehicles
        self.VehicleDesEnd  = VehicleDesEnd                 # desired end times of charging
        self.VehicleEngy    = VehicleEngy                   # Energy State of vehicles [kWh]
        self.VehicleDesEngy = VehicleDesEngy                # desired Energy State of vehicles [kWh]
        self.VehicleSoc     = VehicleEngy / VehicleMaxEngy  # SOC of vehicles [-]
        self.VehicleMaxEngy = VehicleMaxEngy                # maximal energy state of vehicles [kWh]
        
    def addEngy(self, addedEngy):
        #addedEngy in kWh
        self.VehicleEngy    = self.VehicleEngy + addedEngy  # add energy 
        self.VehicleSoc     = self.VehicleEngy / self. VehicleMaxEngy # update SOC

    def addPower(self, power, ts):
        # power in kW, ts in hours
        self.VehicleEngy    = self.VehicleEngy + ts * power # add energy 
        self.VehicleSoc     = self.VehicleEngy / self. VehicleMaxEngy # update SOC
