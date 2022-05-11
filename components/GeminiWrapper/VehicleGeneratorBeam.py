import pandas as pd
import components

class VehicleGeneratorBeam:

    def __init__(self, path_DataBase) -> None:

        # load now the vehicletype database. Here is specified, what data shall be loaded.
        useCols = ["vehicleTypeId", "primaryFuelConsumptionInJoulePerMeter", "primaryFuelCapacityInJoule", "chargingCapability"]
        dtype_DataBase = {"vehicleTypeId": "category", "primaryFuelConsumptionInJoulePerMeter": "float64", "primaryFuelCapacityInJoule": "float64", "chargingCapability": "category"}
        self.DataBase = pd.read_csv(path_DataBase, usecols=useCols, dtype=dtype_DataBase, index_col="vehicleTypeId")

    def generateVehicle(self, VehicleId, VehicleType, VehicleArrival, VehicleDesEnd, primaryFuelLevelInJoules, desiredFuelLevelInJoules) -> components.Vehicle:
        # conversions
        VehicleEngy         = primaryFuelLevelInJoules / 3.6e6 # conversion Joule to kWh
        VehicleDesEngy      = desiredFuelLevelInJoules / 3.6e6 # conversion Joule to kWh
        # TODO: make sure this is the desired fuel level, not the energy to be added
        
        # values from the database
        chargingCap         = self.DataBase.loc[VehicleType, "chargingCapability"]
        VehicleMaxPower     = components.chargingCapFromString(chargingCap)
        VehicleMaxEngy      = self.DataBase.loc[VehicleType, "primaryFuelCapacityInJoule"] / 3.6e6 # conversion to kWh

        Vehicle = components.Vehicle(VehicleId, VehicleType, VehicleArrival, VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleMaxEngy, VehicleMaxPower, ParkingZoneId=False)
        # TODO might add PlugId here

        return Vehicle