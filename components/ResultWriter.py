
import string
import pandas as pd
from components import ChaDepParent
from components import Vehicle
import components

class ResultWriter:

    def __init__(self, filename: string, iterations_save: int = 12, format: string = ".csv") -> None:
        self.iterations_save                = iterations_save # number of iterations, after which results are saved (backup for crashs). Not used so far
        self.ChargingStationState_Filename  = filename + "-ChargingStationState" + format
        self.Events_Filename         = filename +"-Events" + format
        self.VehicleStates_Filename          = filename + "-VehicleStates" + format

        '''initialize pandas dataframes'''
        self.ChargingStationStates          = pd.DataFrame(columns= [
            "time", "ChargingStationID", "BaysVehicleIds", "BaysChargingPower", "TotalChargingPower", "BaysChargingDesire","BaysNumberOfVehicles", "QueueVehicleIds", "QueueChargingDesire", "QueueNumberOfVehicles", "BtmsPower","BtmsSoc","BtmsEnergy", "TotalChargingPowerDesire", "GridPowerUpper", "GridPowerLower"
        ])
        self.Events                         = pd.DataFrame(columns=[
            "time", "Event", "ChargingStationId", "VehicleId", "QueueOrBay", "ChargingDesire", "VehicleType", "VehicleArrival", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", "VehicleMaxEnergy", "VehicleMaxPower", "ChargingBayMaxPower"
        ])
        self.VehicleStates                   = pd.DataFrame(columns=[
            "time", "VehicleId", "ChargingStationId", "QueueOrBay", "ChargingPower", "ChargingDesire", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", 
        ])
    def reset(self):
        list1 = self.ChargingStationStates.columns
        list2 = self.Events.columns
        list3 = self.VehicleStates.columns

        self.ChargingStationStates = pd.DataFrame(columns=list1)
        self.Events = pd.DataFrame(columns=list2)
        self.VehicleStates = pd.DataFrame(columns=list3)


    def save(self):
        # save the three DataFrames
        saveDataFrames = [self.ChargingStationStates, self.Events, self.VehicleStates]
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
    
    def updateChargingStationState(self, t_act, ChargingStation: ChaDepParent):
        CD_Bays = []
        VehicleIds = []
        numVehiclesBays = 0
        for x in ChargingStation.ChBaVehicles:
            if x != False:
                CD_Bays.append(x.ChargingDesire)
                VehicleIds.append(x.VehicleId)
                numVehiclesBays += 1
            else:
                CD_Bays.append(float('nan'))
        CD_Queue = []
        VehicleIdsQueue = []
        for x in ChargingStation.Queue:
            CD_Queue.append(x.ChargingDesire)
            VehicleIdsQueue.append(x.VehicleId)

        self.ChargingStationStates = self.ChargingStationStates.append({
            "time": t_act, "ChargingStationID": ChargingStation.ChargingStationId, "BaysVehicleIds":VehicleIds, "BaysChargingPower": ChargingStation.ChBaPower, "TotalChargingPower": sum(ChargingStation.ChBaPower), "BaysChargingDesire": CD_Bays,"BaysNumberOfVehicles": numVehiclesBays, "QueueVehicleIds": VehicleIdsQueue, "QueueChargingDesire": CD_Queue, "QueueNumberOfVehicles": len(CD_Queue), "BtmsPower": ChargingStation.BtmsPower,"BtmsSoc": ChargingStation.BtmsSoc(), "BtmsEnergy": ChargingStation.BtmsEn, "TotalChargingPowerDesire": ChargingStation.PowerDesire, "GridPowerUpper": ChargingStation.GridPowerUpper, "GridPowerLower": ChargingStation.GridPowerLower
        }, ignore_index=True)