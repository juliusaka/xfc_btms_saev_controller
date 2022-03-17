'''
Datatypes template for Input File:
dtype = {
       'time': 'int64', 
       'type': 'category', 
       'vehicle': 'int64', 
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

'''
import pandas as pd

class SimBroker:

    def __init__(self, path, dtype):

        self.SimRes     = pd.read_csv(path, dtype = dtype, index_col= "time") # save length of pd dataframe, time is set as index!
        self.SimRes     = self.SimRes.sort_index()  # make sure that inputs are ascending
        self.length     = len(self.SimRes)     # save length of pd dataframe
        self.i          = 0
        self.t_act      = self.SimRes.index[self.i]
        '''
        self.t_act      = t_Start              # start time of simulation in seconds
        while self.SimRes.index[self.i] < self.t_act:
            self.i      +=1
        '''

    def step(self, timestep):
        self.t_act      += timestep             # update actual time
        self.i          += 1
        i_old = self.i                          # first index row of slice, is the last index +1 row from 
        while self.SimRes.index[self.i] <= self.t_act: # include elements up to equals t_act
            self.i      +=1
        df_slice = self.SimRes.iloc[i_old:self.i , :]
        return df_slice