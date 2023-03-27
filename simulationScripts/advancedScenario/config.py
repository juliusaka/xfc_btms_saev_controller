import os
'''Simulation Name'''
sim_name = "advancedScenario7"
result_parent_directory = "results" + os.sep + sim_name
os.makedirs(result_parent_directory, exist_ok=True)

'''Infrastructure Creation Mode'''
infrastructure_creation_mode = "taz" # or numberplugs

'''Simulation'''
timestep = 60  # in seconds
simulation_end_time = 24*60*60 # in seconds


'''Predictions'''
prediction_add_noise = True
noise_param = 0.2

'''Sizing of Charging Stations'''
# demand charge in $/kWh amortized per day
a_cost_sizing = 20 / (365/12)
# free power demand as ratio to max charging power
P_free_Ratio_sizing = 0.0
# btms cost per cycle in $/kWh
b_cost_sizing = 220/5400
c_cost_sizing = 0.12
btms_efficiency = 0.85

'''Creating optimal day ahead plan'''

###########################################
## Plots ##
###########################################
showPlots = False
plotPrediction = False
plotSizing = True
plotSizeX = 3.61
plotSizeY = 1.2
plotSizeX2col = 6.6
plotSizeY2col = 2.7
pltFontSize = 7
def pltSettings():
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.size': 7})
        plt.rcParams['mathtext.fontset'] = 'cm'
        # does this work?
###########################################
## FILEPATHS Files ##
###########################################
#'''Simulation Broker'''
test_data_path = 'test_data'
path_Sim_original_data = test_data_path + os.sep + "rhev-siting.6.events.7Advanced.csv"
path_Sim = test_data_path + os.sep + "rhev-siting.6.events.7Advanced_filtered.csv"
dtype_Sim = {
       'time': 'int64', 'type': 'category', 'vehicle': 'string', 'parkingTaz': 'category','chargingPointType': 'category', 
       'primaryFuelLevel': 'float64', 'mode': 'category', 'currentTourMode': 'category', 'vehicleType': 'category', 
       'arrivalTime': 'float64', 'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category', 
       'parkingZoneId': 'category','duration': 'float64' , 'shiftStatus': 'category',
        }
#'''Vehicle Generator'''
path_DataBase = test_data_path + os.sep + "vehicletypes-HighEV2040_2021620.csv"
#'''Infrastructure File'''
path_infrastructure = test_data_path + os.sep + "taz-parking_S80_P300_R250_F35k_Scenario7.csv"
# '''generated predictions''':
prediction_directory = result_parent_directory + os.sep + 'step1_predictions'
os.makedirs(prediction_directory, exist_ok=True)