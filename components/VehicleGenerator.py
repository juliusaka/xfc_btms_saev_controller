import pandas as pd
import numpy as np
import components

class VehicleGenerator:

    '''This is the vehicle generator for the stand-alone version.'''

    def __init__(self, path_Sim, dtype_Sim, path_DataBase):
        # vehicle generator for the stand-alone version
        # for advanced scenario 7

        # load now the vehicletype database. Here is specified, what data shall be loaded.
        useCols = ["vehicleTypeId", "primaryFuelConsumptionInJoulePerMeter", "primaryFuelCapacityInJoule", "chargingCapability"]
        dtype_DataBase = {"vehicleTypeId": "category", "primaryFuelConsumptionInJoulePerMeter": "float64", "primaryFuelCapacityInJoule": "float64", "chargingCapability": "category"}
        self.DataBase = pd.read_csv(path_DataBase, usecols=useCols, dtype=dtype_DataBase, index_col="vehicleTypeId")

        pass

    def generate_vechicle_from_df_slice(self, df_slice: pd.DataFrame):
        # for the Stand-Alone (SO) version
        # generate here the vehicle, based on the df_slice with "RefuelSessionEvent"
        # (the slice of the event) which is given by the SimBroker.
        # as we don't know the energy level at arrival, we can't include SOC behavior. 
        # but it might be possible to scratch this from the last path traversal event.

        if df_slice.type != "RefuelSessionEvent":
            raise ValueError("You didn't pass a refuelSessionEvent to generateVehicle")
        
        VehicleId           = df_slice["vehicle"]
        VehicleType         = df_slice["vehicleType"] # use map to find out the vehicleType
        VehicleArrival      = df_slice.name
        VehicleEngy         = 0 # we don't know the energy level at arrival, see above.
        VehicleMaxEngy      = self.DataBase.loc[VehicleType, "primaryFuelCapacityInJoule"] / 3.6e6 # conversion to kWh
        # generate here the maximum power of the vehicle:
        chargingCap = self.DataBase.loc[VehicleType, "chargingCapability"]
        VehicleMaxPower = components.chargingCapFromString(chargingCap)
        
        #for desired end and desired energy, we need to find the corresponding RefuelSessionEvent
        # this is after ChargingPlugInEvent.
        # therfore: time must be greater equals than VehicleArrival Time, type must be RefuelSessionEvent, VehicleId must be the same. Furthermore, this must be the first entry. 
        try:
            VehicleDesEnd       = df_slice.name + df_slice["duration"]# this is the time at which refuel session event is finished
            VehicleDesEngy      = df_slice["fuel"] / 3.6e6 + VehicleEngy # this is the desired state of energy at the end of the charging event
            BeamDesignatedParkingZoneId = df_slice["parkingZoneId"]
        except: # if we are at the end of the file, we don't want errors from events which aren't finished.
            VehicleDesEnd               = 0
            VehicleDesEngy              = 0 
            BeamDesignatedParkingZoneId    = False
            print("VehicleGenerator: did not find associated RefuelSession Event. Set Energy to 0")
        
        Vehicle = components.Vehicle(VehicleId, VehicleType, VehicleArrival, VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleMaxEngy, VehicleMaxPower, ParkingZoneId=BeamDesignatedParkingZoneId)

        return Vehicle