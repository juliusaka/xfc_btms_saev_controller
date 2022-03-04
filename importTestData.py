# import required modules
from datetime import date
print("\n new Run\n - - - - - \n ")
import pandas as pd
import numpy as np
import time
from dask import dataframe as df1

# change this to the location of where you stored the output file:
path = "C:/Users/akaju/Documents/project thesis/Beam Output Data/archive/0.events.csv/0.events.csv"

print("\n loading BEAM-output-File from "+ path + "\n")
# like dask suggested, i add this:
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
s_time_dask = time.time()
dask_df = df1.read_csv(path, dtype = dtype)
e_time_dask = time.time()
  
print("Read with dask: ", (e_time_dask-s_time_dask), "seconds")
  
# data
print(dask_df.columns)
# print(dask_df.columns[30])
print(dask_df.head())

