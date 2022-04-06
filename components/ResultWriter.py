
import string
import pandas as pd
from components.Vehicle import Vehicle

class ResultWriter:

    def __init__(self, filename: string, iterations_save: int = 12, format: string = ".csv") -> None:
        self.iterations_save                = iterations_save # number of iterations, after which results are saved (backup for crashs). Not used so far
        self.ChargingStationState_Filename  = filename + "-ChargingStationState" + format
        self.Events_Filename         = filename +"-Events" + format
        self.VehicleStates_Filename          = filename + "-VehicleStates" + format

        '''initialize pandas dataframes'''
        self.ChargingStationStates          = pd.DataFrame(columns= [
            "time", "ChargingStationID", "BaysVehicleIds", "BaysChargingPower", "BaysChargingDesire","BaysNumberOfVehicles", "QueueVehicleIds", "QueueChargingDesire", "QueueNumberOfVehicles", "TotalChargingPowerDesire", "BtmsChargingPowerDesire", "BtmsPower"
        ])
        self.Events                         = pd.DataFrame(columns=[
            "time", "Event", "ChargingStationId", "VehicleId", "QueueOrBay", "ChargingDesire", "VehicleType", "VehicleArrival", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", "VehicleMaxEnergy", "VehicleMaxPower", "ChargingBayMaxPower"
        ])
        self.VehicleStates                   = pd.DataFrame(columns=[
            "time", "VehicleId", "ChargingStationId", "QueueOrBay", "ChargingPower", "ChargingDesire", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", 
        ])

    def save(self):
        # save the three DataFrames
        saveDataFrames = [self.ChargingStationStates, self.Events, self.VehicleState]
        saveFileNames  = [self.ChargingStationState_Filename, self.Events_Filename, self.VehicleStates_Filename] 
        for i in range(0,3):
            pd.DataFrame.to_csv( saveDataFrames[i].set_index("time") , saveFileNames[i]) # the index is just set to time before saving.

    # add now all the events which could happen and assign the entries to the differnt dataframes

    def reparkEvent(self, t_act, Vehicle: Vehicle, ChargingStationId, QueueOrBay, ChargingBayMaxPower):
        if QueueOrBay == True:
            QueueOrBay = 'Queue'
        else:
            QueueOrBay = 'Bay'
        self.Events = self.Events.append(
            {"time": t_act, "Event": "ReparkEvent", "ChargingStationId": ChargingStationId, "VehicleId": Vehicle.VehicleId, "QueueOrBay": QueueOrBay, "ChargingDesire": Vehicle.ChargingDesire, "VehicleType": Vehicle.VehicleType, "VehicleArrival": Vehicle.VehicleArrival, "VehicleDesiredEnd": Vehicle.VehicleDesEnd, "VehicleEnergy": Vehicle.VehicleEngy, "VehicleDesiredEnergy": Vehicle.VehicleDesEngy, "VehicleSoc": Vehicle.VehicleSoc, "VehicleMaxEnergy": Vehicle.VehicleMaxEngy, "VehicleMaxPower": Vehicle.VehicleMaxPower, "ChargingBayMaxPower": ChargingBayMaxPower
        }, ignore_index=True)

    def arrivalEvent(self, t_act, Vehicle: Vehicle, ChargingStationId):
        self.Events = self.Events.append(
            {"time": t_act, "Event": "ArrivalEvent", "ChargingStationId": ChargingStationId, "VehicleId": Vehicle.VehicleId, "QueueOrBay": "", "ChargingDesire": Vehicle.ChargingDesire, "VehicleType": Vehicle.VehicleType, "VehicleArrival": Vehicle.VehicleArrival, "VehicleDesiredEnd": Vehicle.VehicleDesEnd, "VehicleEnergy": Vehicle.VehicleEngy, "VehicleDesiredEnergy": Vehicle.VehicleDesEngy, "VehicleSoc": Vehicle.VehicleSoc, "VehicleMaxEnergy": Vehicle.VehicleMaxEngy, "VehicleMaxPower": Vehicle.VehicleMaxPower, "ChargingBayMaxPower": float("nan")
        }, ignore_index=True)

    def releaseEvent(self, t_act, Vehicle: Vehicle, ChargingStationId):
        self.Events = self.Events.append(
            {"time": t_act, "Event": "ReleaseEvent", "ChargingStationId": ChargingStationId, "VehicleId": Vehicle.VehicleId, "QueueOrBay": "", "ChargingDesire": float("NaN"), "VehicleType": Vehicle.VehicleType, "VehicleArrival": Vehicle.VehicleArrival, "VehicleDesiredEnd": Vehicle.VehicleDesEnd, "VehicleEnergy": Vehicle.VehicleEngy, "VehicleDesiredEnergy": Vehicle.VehicleDesEngy, "VehicleSoc": Vehicle.VehicleSoc, "VehicleMaxEnergy": Vehicle.VehicleMaxEngy, "VehicleMaxPower": Vehicle.VehicleMaxPower, "ChargingBayMaxPower": float("nan")
        }, ignore_index=True)

    def updateVehicleStates(self, t_act, vehicle: Vehicle, ChargingStationId, QueueOrBay, ChargingPower):
        if QueueOrBay == True:
            QueueOrBay = 'Queue'
        else:
            QueueOrBay = 'Bay'
        self.VehicleStates = self.VehicleStates.append(
            {"time": t_act, "VehicleId": vehicle.VehicleId, "ChargingStationId": ChargingStationId, "QueueOrBay": QueueOrBay , "ChargingPower": ChargingPower, "ChargingDesire": vehicle.ChargingDesire, "VehicleDesiredEnd": vehicle.VehicleDesEnd, "VehicleEnergy": vehicle.VehicleEngy, "VehicleDesiredEnergy": vehicle.VehicleDesEngy, "VehicleSoc": vehicle.VehicleSoc
            }, ignore_index=True)