import components
import pandas as pd
import logging

# create mapping from parkingZoneId to chargingStation and from taz to chargingStation
def createMaps(path_infrastructure, mode = 'numberPlugs'):
    pass

# create the actual charging station objects
def createChargingStations(path_infrastructure, chargingStationClass: components.ChaDepParent, ResultWriter, SimBroker, btms_effiency = 0.85):

    logging.info("creating charging stations of type " + str(chargingStationClass))
    usecols_infrastructure = ["taz", "parkingType",
                            "chargingPointType", "parkingZoneId", "numStalls"]
    dtype_infrastructure = {"taz": "string", "parkingType": "category",
                            "chargingPointType": "category", "parkingZoneId": "string", "numStalls": "int64"}
    df_infrastructure = pd.read_csv(
        path_infrastructure, dtype=dtype_infrastructure, usecols=usecols_infrastructure)
    df_infrastructure = df_infrastructure.set_index("parkingZoneId")
    df_infrastructure.sort_index()

    chargingStations = []  # list of charging stations
    for i in range(df_infrastructure.shape[0]):
        infrastructure = df_infrastructure.iloc[i]
        ChargingStationId = infrastructure["taz"]
        # make a list with the power of each charging bay:
        ChBaMaxPower = []
        maxPower = components.chargingCapFromString(infrastructure["chargingPointType"])
        for j in range(0, infrastructure["numStalls"]):
            ChBaMaxPower.append(maxPower)
        ChBaParkingZoneId = [infrastructure.name]
        ChBaNum = len(ChBaMaxPower)

        # create charging station
        container = chargingStationClass(ChargingStationId=ChargingStationId, ResultWriter=ResultWriter, SimBroker=SimBroker,ChBaMaxPower=ChBaMaxPower, ChBaParkingZoneId=ChBaParkingZoneId, ChBaNum=ChBaNum, calcBtmsGridProp=True, BtmsEfficiency = btms_effiency)

        chargingStations.append(container)
        logging.info(str(ChargingStationId) + " was created with " + str(container.ChBaNum) +
            " charging bays and " + str(container.BtmsSize) + "kWh BTM-Storage")

    return chargingStations