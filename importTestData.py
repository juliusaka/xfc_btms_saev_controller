# %%
# the line above is used to start the interactive mode. with ctrl + T you will open the interactive window on the right
#%pylab inline # this should help with plotting inline, but it isnt recommended.

# import required modules
from datetime import date
print("\n new Run\n - - - - - \n ")
import pandas as pd
import numpy as np
import time
import dask
from dask import dataframe as df1

# change this to the location of where you stored the output file:
path = "C:/Users/akaju/Documents/project thesis/Beam Output Data/archive/0.events.csv/0.events.csv"
columns_inFile = {
       'person', 'link', 'facility', 'actType', 'time', 'type', 'departTime',
       'startX', 'startY', 'endX', 'endY', 'driver', 'vehicle', 'parkingTaz', 
       'chargingPointType', 'pricingModel', 'parkingType', 'locationY',       
       'locationX', 'cost', 'legMode', 'primaryFuelLevel',
       'secondaryFuelLevel', 'price', 'score', 'mode', 'currentTourMode',     
       'expectedMaximumUtility', 'availableAlternatives', 'location',
       'personalVehicleAvailable', 'length', 'tourIndex', 'vehicleType',      
       'links', 'numPassengers', 'primaryFuel', 'riders', 'toStopIndex',      
       'fromStopIndex', 'seatingCapacity', 'tollPaid', 'capacity',
       'arrivalTime', 'departureTime', 'linkTravelTime', 'secondaryFuel',     
       'secondaryFuelType', 'primaryFuelType', 'shiftStatus', 'parkingZoneId',       'fuel', 'duration', 'incentive', 'tollCost', 'netCost', 'reason'
}
# specify columns we want to load
usecols = [
       'person','actType', 'time', 'type', 'departTime',
       'startX', 'startY', 'endX', 'endY', 'driver', 'vehicle', 'parkingTaz', 
       'chargingPointType', 'pricingModel', 'parkingType', 'locationY',       
       'locationX', 'cost', 'legMode', 'primaryFuelLevel',
       'secondaryFuelLevel', 'price', 'score', 'mode', 'currentTourMode',     
       'expectedMaximumUtility', 'availableAlternatives', 'location',
       'personalVehicleAvailable', 'length', 'tourIndex', 'vehicleType',      
       'links', 'numPassengers', 'primaryFuel', 'riders', 'toStopIndex',      
       'fromStopIndex', 'seatingCapacity', 'tollPaid', 'capacity',
       'arrivalTime', 'departureTime', 'linkTravelTime', 'secondaryFuel',     
       'secondaryFuelType', 'primaryFuelType', 'shiftStatus', 'parkingZoneId',       'fuel', 'duration', 'incentive', 'tollCost', 'netCost', 'reason'
]
# state without selecting cols
dtype={'actType': 'string',
       'availableAlternatives': 'string',
       'chargingPointType': 'string',
       'currentTourMode': 'string',
       'driver': 'string',
       'linkTravelTime': 'string',
       'links': 'string',
       'mode': 'string',
       'person' : 'string',
       'personalVehicleAvailable' : 'string',
       'parkingTaz': 'string',
       'parkingType': 'string',
       'parkingZoneId': 'string',
       'pricingModel': 'string',
       'primaryFuelType': 'string',
       'reason': 'string',
       'riders': 'string',
       'secondaryFuelType': 'string',
       'vehicleType': 'string'}

print("\n loading BEAM-output-File from "+ path + "\n")

s_time_dask = time.time()
dask_df = df1.read_csv(path, dtype = dtype)
e_time_dask = time.time()
  
print("Read with dask: ", (e_time_dask-s_time_dask), "seconds")
  
# data
print(dask_df.columns)
dask_df.info()
# print(dask_df.columns[30])
dask_df.head(500)

#dask_df.loc[:3, :].to_csv("beam_output.csv")

df = dask_df.loc[:5, :]
df2 = df["person"]
df2[0]

usecols = ['time', 'type', 'vehicle', 'parkingTaz',
       'chargingPointType', 'primaryFuelLevel', 'mode', 'currentTourMode', 'vehicleType', 'primaryFuel', 'arrivalTime',
       'departureTime', 'linkTravelTime', 'primaryFuelType', 
       'parkingZoneId', ]
       # vehicle seems like it is the vehicle identifier

       # departTime doesnt seem used, discarded
