# %%
import pandas as pd
import numpy as np
import time
from dask import dataframe as df1
import dask
path = "C:/Users/akaju/Documents/project thesis/Beam Output Data/vehicletypes-Base_2035_20210204_updated.csv"

# %%
print("\n loading vehicletypes file from "+ path + "\n")

dtype={'automationLevel': 'float64',
       'primaryFuelCapacityInJoule': 'float64',
       'primaryFuelConsumptionInJoulePerMeter': 'float64',
       'secondaryFuelType': 'string',
       'secondaryVehicleEnergyFile': 'string'}
usecols = ['vehicleTypeId', 'primaryFuelType',
       'primaryFuelConsumptionInJoulePerMeter', 'primaryFuelCapacityInJoule',
       'secondaryFuelType','secondaryFuelConsumptionInJoulePerMeter',
       'rechargeLevel2RateLimitInWatts','rechargeLevel3RateLimitInWatts',
       'vehicleCategory','sampleProbabilityWithinCategory', 
       'sampleProbabilityString', 'chargingCapability', 'RH_prob']
#all columns : ['vehicleTypeId', 'seatingCapacity', 'standingRoomCapacity', 'lengthInMeter', 'primaryFuelType',
    #    'primaryFuelConsumptionInJoulePerMeter', 'primaryFuelCapacityInJoule',
    #    'primaryVehicleEnergyFile', 'secondaryFuelType',
    #    'secondaryFuelConsumptionInJoulePerMeter', 'secondaryVehicleEnergyFile',
    #    'secondaryFuelCapacityInJoule', 'automationLevel', 'maxVelocity',
    #    'passengerCarUnit', 'rechargeLevel2RateLimitInWatts',
    #    'rechargeLevel3RateLimitInWatts', 'vehicleCategory',
    #    'sampleProbabilityWithinCategory', 'sampleProbabilityString',
    #    'chargingCapability', 'RH_prob']
df_vehicles = df1.read_csv(path, dtype = dtype, usecols = usecols)

df_vehicles.head(10)

# %%
path = "C:/Users/akaju/Documents/project thesis/Beam Output Data/archive/0.events.csv/0.events.csv"
# for testing
#path = 'test_data/beam1/beam_output20-006.csv'
print("\n loading simulation results file from "+ path + "\n")
all_cols = ['person', 'link', 'facility', 'actType', 'time', 'type', 'departTime',
       'startX', 'startY', 'endX', 'endY', 'driver', 'vehicle', 'parkingTaz',
       'chargingPointType', 'pricingModel', 'parkingType', 'locationY',
       'locationX', 'cost', 'legMode', 'primaryFuelLevel',
       'secondaryFuelLevel', 'price', 'score', 'mode', 'currentTourMode',
       'expectedMaximumUtility', 'availableAlternatives', 'location',
       'personalVehicleAvailable', 'length', 'tourIndex', 'vehicleType',
       'links', 'numPassengers', 'primaryFuel', 'riders', 'toStopIndex',
       'fromStopIndex', 'seatingCapacity', 'tollPaid', 'capacity',
       'arrivalTime', 'departureTime', 'linkTravelTime', 'secondaryFuel',
       'secondaryFuelType', 'primaryFuelType', 'shiftStatus', 'parkingZoneId',
       'fuel', 'duration', 'incentive', 'tollCost', 'netCost', 'reason']
usecols = ['time', 'type', 'vehicle', 'parkingTaz',
       'chargingPointType', 'primaryFuelLevel', 'mode', 'currentTourMode', 'vehicleType', 'arrivalTime',
       'departureTime', 'linkTravelTime', 'primaryFuelType', 
       'parkingZoneId', 'fuel', 'duration' ]
       # vehicle seems like it is the vehicle identifier
       # , 'primaryFuel' doesnt seem needed
       # departTime doesnt seem used, discarded
dtype = {
       'time': 'float64', 
       'type': 'category', 
       'vehicle': 'string', 
       'parkingTaz': 'category', #
       'chargingPointType': 'category', 
       'primaryFuelLevel': 'float64', #
       'mode': 'category', 
       'currentTourMode': 'category', 
       'vehicleType': 'category', 
       'arrivalTime': 'float64', #
       'departureTime': 'float64', # 
       'linkTravelTime': 'string', 
       'primaryFuelType': 'category', 
       'parkingZoneId': 'category',
       'duration': 'float64' #
}
df_sim = df1.read_csv(path, dtype = dtype, usecols = usecols) #, blocksize = 12e6)

#set index, not necessary.
#df_sim.set_index('time', sorted = True)

#df_sim.head(20)

# %%
# choose new rows with events which are interesting and delte df_sim
df_sim_new = df_sim.loc[
    df_sim['type'].isin(['RefuelSessionEvent', 'ChargingPlugOutEvent', 'ChargingPlugInEvent']) &
    df_sim['chargingPointType'].str.contains('DC', na=False)
    , : ]
#del df_sim

# %%
#repartion to save storage. partion_size might be expensive
print("old number of partitions: " + str(df_sim_new.npartitions))
df_sim_new = df_sim_new.repartition(partition_size="100MB").persist() # might be expensive, can put also npartitions # added persist to let this stay in memory
#df_sim_new.compute()
print("new number of partitions: " + str(df_sim_new.npartitions))
df_sim_new.info()
#df_sim_new.head(16)

# %%
# print out number of rows
df_sim_new.shape[0].compute()

# %%
#save data to csv. parquet might be better, but need to downgrade python for that.
df_sim_new.to_csv('test_data/beam1/beam1-*.csv')