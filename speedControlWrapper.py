# %%
import components
import time
import os
from threading import Thread
stations = []

class AnotherWrapper():
    def __init__(self, taz, var1, var2, var3, initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max):
        self.taz = taz
        self.var1 = var1
        self.var2 = var2
        self.var3 = var3
        self.SPM = components.GeminiWrapper.ControlWrapper(initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max)

class AnotherWrapperWithThread():
    thread = Thread()

    def __init__(self, taz, var1, var2, var3, initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max):
        self.taz = taz
        self.var1 = var1
        self.var2 = var2
        self.var3 = var3
        self.SPM = components.GeminiWrapper.ControlWrapper(initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max)

class HaitamsWrapper():
    thread = Thread()
    ControlCommands = []

    def __init__(self, taz_id, site_id, name, time_step, output_directory, simulation_duration):
        self.taz_id = taz_id
        self.site_id = site_id
        self.site_prefix_logging = name + "[" + str(taz_id) + ":" + str(site_id) + "]. "
        self.time_step = time_step
        # JULIUS: @HL I initialized my SPM Controller here
        # @ HL can you provide the missing information
        # TODO uncomment
        initMpc = False
        t_start = int(0)
        timestep_intervall = int(self.time_step)
        result_directory = output_directory
        RideHailDepotId = site_id
        ChBaMaxPower = [250] * 10 # list of floats in kW for each plug, for first it should be the same maximum power
        # for all -> could set 10 000 kW if message contains data --> list with length of number
        # of plugs from infrastructure file?
        ChBaParkingZoneId = ['test'] * 10# list of strings, could just be a list of empty strings as not further used so far
        ChBaNum = len(ChBaMaxPower)  # number of plugs in one depot --> infrastructure file?
        # only needed for MPC
        path_BeamPredictionFile = ''  # path to a former run of the same simulation to obtain predicitions.
        # the beam result file should be reduced before to only contain the relevant data
        dtype_Predictions = {
            'time': 'int64', 'type': 'category', 'vehicle': 'int64', 'parkingTaz': 'category',
            'chargingPointType': 'category', 'primaryFuelLevel': 'float64', 'mode': 'category',
            'currentTourMode': 'category', 'vehicle_type': 'category', 'arrival_time': 'float64',
            'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category',
            'parkingZoneId': 'category', 'duration': 'float64'
        }  # dictionary containing the data types in the beam prediction file
        # maximum time up to which we simulate (for predicting in MPC)
        t_max = int(simulation_duration - self.time_step)
        self.depotController = components.GeminiWrapper.ControlWrapper(
            initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower,
            ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max)


# %%
# first with control wrapper
t1 = time.time()
stations = []
for i in range(0,400):
    initMpc = False
    t_start = 0
    timestep_intervall = 300
    result_directory = 'results/speedTest'
    RideHailDepotId = 'station_' + str(i)
    ChBaMaxPower = [100] *10
    ChBaParkingZoneId = ['zone_' + str(i)] *10
    ChBaNum = 10
    path_BeamPredictionFile = "test_data" + os.sep + "beam1" + os.sep + "beam1-0.csv"
    dtype_Predictions = {
            'time': 'int64', 'type': 'category', 'vehicle': 'int64', 'parkingTaz': 'category',
            'chargingPointType': 'category', 'primaryFuelLevel': 'float64', 'mode': 'category',
            'currentTourMode': 'category', 'vehicle_type': 'category', 'arrival_time': 'float64',
            'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category',
            'parkingZoneId': 'category', 'duration': 'float64'
        }
    t_max = 86400
    stations.append(components.GeminiWrapper.ControlWrapper(initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max))

t2 = time.time()

print("it took " + str(t2-t1))
# %%
# second with a wrapper around the control wrapper without a thread
t1 = time.time()
stations = []
for i in range(0,400):
    taz = i
    var1 = 1
    var2 = 2
    var3 = 3
    initMpc = False
    t_start = 0
    timestep_intervall = 300
    result_directory = 'results/speedTest'
    RideHailDepotId = 'station_' + str(i)
    ChBaMaxPower = [100] *10
    ChBaParkingZoneId = ['zone_' + str(i)] *10
    ChBaNum = 10
    path_BeamPredictionFile = "test_data" + os.sep + "beam1" + os.sep + "beam1-0.csv"
    dtype_Predictions = {
            'time': 'int64', 'type': 'category', 'vehicle': 'int64', 'parkingTaz': 'category',
            'chargingPointType': 'category', 'primaryFuelLevel': 'float64', 'mode': 'category',
            'currentTourMode': 'category', 'vehicle_type': 'category', 'arrival_time': 'float64',
            'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category',
            'parkingZoneId': 'category', 'duration': 'float64'
        }
    t_max = 86400
    stations.append(AnotherWrapper(taz, var1, var2, var3, initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max))

t2 = time.time()

print("it took " + str(t2-t1))

# %%
# third with a wrapper around the control wrapper with a thread
t1 = time.time()
stations = []
for i in range(0,400):
    taz = i
    var1 = 1
    var2 = 2
    var3 = 3
    initMpc = False
    t_start = 0
    timestep_intervall = 300
    result_directory = 'results/speedTest'
    RideHailDepotId = 'station_' + str(i)
    ChBaMaxPower = [100] *10
    ChBaParkingZoneId = ['zone_' + str(i)] *10
    ChBaNum = 10
    path_BeamPredictionFile = "test_data" + os.sep + "beam1" + os.sep + "beam1-0.csv"
    dtype_Predictions = {
            'time': 'int64', 'type': 'category', 'vehicle': 'int64', 'parkingTaz': 'category',
            'chargingPointType': 'category', 'primaryFuelLevel': 'float64', 'mode': 'category',
            'currentTourMode': 'category', 'vehicle_type': 'category', 'arrival_time': 'float64',
            'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category',
            'parkingZoneId': 'category', 'duration': 'float64'
        }
    t_max = 86400
    stations.append(AnotherWrapperWithThread(taz, var1, var2, var3, initMpc, t_start, timestep_intervall, result_directory, RideHailDepotId, ChBaMaxPower, ChBaParkingZoneId, ChBaNum, path_BeamPredictionFile, dtype_Predictions, t_max))

t2 = time.time()

print("it took " + str(t2-t1))

# %%
# fourth with Haitams wrapper
t1 = time.time()
stations = []
for i in range(0,400):
    taz = i
    var1 = 1
    var2 = 2
    var3 = 3
    initMpc = False
    t_start = 0
    timestep_intervall = 300
    result_directory = 'results/speedTest'
    RideHailDepotId = 'station_' + str(i)
    ChBaMaxPower = [100] *10
    ChBaParkingZoneId = ['zone_' + str(i)] *10
    ChBaNum = 10
    path_BeamPredictionFile = "test_data" + os.sep + "beam1" + os.sep + "beam1-0.csv"
    dtype_Predictions = {
            'time': 'int64', 'type': 'category', 'vehicle': 'int64', 'parkingTaz': 'category',
            'chargingPointType': 'category', 'primaryFuelLevel': 'float64', 'mode': 'category',
            'currentTourMode': 'category', 'vehicle_type': 'category', 'arrival_time': 'float64',
            'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category',
            'parkingZoneId': 'category', 'duration': 'float64'
        }
    t_max = 86400
    stations.append(HaitamsWrapper(taz, taz, RideHailDepotId, 60, result_directory, 10000))

t2 = time.time()

print("it took " + str(t2-t1))
# %%
