import components
import pandas as pd
import logging

# create mapping from parkingZoneId to chargingStation and from taz to chargingStation
def createMaps(path_infrastructure, mode = 'numberPlugs'):
    # load infrastructure file into dataframe
    usecols_infrastructure = ["taz", "parkingType",
                            "chargingPointType", "parkingZoneId"]
    dtype_infrastructure = {"taz": "int64", "parkingType": "category",
                            "chargingPointType": "category", "parkingZoneId": "string"}
    infrastructure = pd.read_csv(
        path_infrastructure, dtype=dtype_infrastructure, usecols=usecols_infrastructure)
    # filter infrastructure for only public fast and extreme fast charging
    infrastructure = infrastructure.loc[infrastructure["parkingType"] == "Public"]
    infrastructure = infrastructure.loc[infrastructure["chargingPointType"].str.contains(
        "publicfc|publicxfc")]
    # allocate dicts
    chargingStationMappedToParkingZoneId = {}
    chargingStationMappedToTaz = {}
    if mode == 'numberPlugs':
        
        infrastructure = infrastructure.set_index("parkingZoneId")

        # sort infrastructure by taz and parkingZoneId
        infrastructure = infrastructure.sort_values(by=["taz", "parkingZoneId"])

        # now, make a dict of every parkingZoneId that belongs to a charging station
        stepsize = 200 # approximate number of plugs per charging station
        i = 0
        j = 1
        stop = False
        while i < len(infrastructure) - 1: # loop over infrastructure file in chunks
            name = "chargingStation-" + str(j)
            # we want to make sure, that all the chargingBays of one TAZ are in one chargingStation
            if i + stepsize < len(infrastructure): # didnt reach end of infrastructure file
                i_end = i+stepsize # read until this index
                while infrastructure.iloc[i_end]["taz"] == infrastructure.iloc[i_end+1]["taz"]:
                    i_end += 1  # if the taz is the same, we should increase reading to the next row
                    if i_end + 1 == len(infrastructure): # make sure, that we don't try to read in the next step something that doesnt exist
                        stop = True
                        break
            else:
                i_end = len(infrastructure) - 1
            slice = infrastructure.iloc[i:i_end+1]
            chargingStationMappedToParkingZoneId[name] = slice.index.to_list()
            chargingStationMappedToTaz[name] = list(
                set(slice["taz"].to_list()))  # this removes duplicates
            i = i_end+1 # start reading next cycle at i
            j += 1

    elif mode == 'taz':
        #here, we will make chargingStation depending on TAZ
        taz = infrastructure.taz.drop_duplicates().to_list()
        taz = sorted(taz)
        for i in range(0, len(taz)):
            name = "chargingStation-" + str(i)
            idx = infrastructure["taz"].isin([taz[i]])
            slice = infrastructure.loc[idx]
            chargingStationMappedToParkingZoneId[name] = slice.index.to_list()
            chargingStationMappedToTaz[name] = [taz[i]]
            
    # we convert chargingStationMappedToTaz to a dataframe to use search methods
    chargingStationMappedToTaz = pd.DataFrame.from_dict(
        chargingStationMappedToTaz, orient='index')
    chargingStationMappedToTaz = chargingStationMappedToTaz.transpose()

    logging.info("charging stations mapped to parkingZoneId")

    return chargingStationMappedToParkingZoneId, chargingStationMappedToTaz

# create the actual charging station objects
def createChargingStations(chargingStationMappedToParkingZoneId, path_infrastructure, chargingStationClass, ResultWriter, SimBroker):

    logging.info("creating charging stations of type " + str(chargingStationClass))
    usecols_infrastructure = ["taz", "parkingType",
                            "chargingPointType", "parkingZoneId"]
    dtype_infrastructure = {"taz": "int64", "parkingType": "category",
                            "chargingPointType": "category", "parkingZoneId": "string"}
    infrastructure = pd.read_csv(
        path_infrastructure, dtype=dtype_infrastructure, usecols=usecols_infrastructure)
    infrastructure = infrastructure.set_index("parkingZoneId")

    chargingStations = []  # list of charging stations
    for i in chargingStationMappedToParkingZoneId:
        ChargingStationId = i
        # make a list with the power of each charging bay:
        ChBaMaxPower = []
        for j in chargingStationMappedToParkingZoneId[i]:
            power_string = infrastructure.loc[j, "chargingPointType"]
            ChBaMaxPower.append(components.chargingCapFromString(power_string))

        # for now, we assume that all charging bays have the same charging power
        PowerMax = max(ChBaMaxPower)
        len_power = len(ChBaMaxPower)
        ChBaMaxPower = []
        # make charging limit for each bay the same (for testing and simplicity)
        for j in range(0, len_power):
            ChBaMaxPower.append(PowerMax)
        del PowerMax, len_power

        ChBaParkingZoneId = chargingStationMappedToParkingZoneId[i]

        '''reduce number of charging bays to test controller'''
        # numStations = 30
        # ChBaMaxPower = ChBaMaxPower[0:numStations]
        ChBaNum = len(ChBaMaxPower)

        # create charging station
        container = chargingStationClass(ChargingStationId=ChargingStationId, ResultWriter=ResultWriter, SimBroker=SimBroker,
                                        ChBaMaxPower=ChBaMaxPower, ChBaParkingZoneId=ChBaParkingZoneId, ChBaNum=ChBaNum, calcBtmsGridProp=True)
        chargingStations.append(container)
        logging.info(ChargingStationId + " was created with " + str(container.ChBaNum) +
            " charging bays and " + str(container.BtmsSize) + "kWh BTM-Storage")

    return chargingStations


def main():
    pass

if __name__ == "__main__":
    main()