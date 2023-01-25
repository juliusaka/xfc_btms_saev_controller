import os
'''Simulation Name'''
sim_name = "advancedScenario7"
result_directory = "results" + os.sep + sim_name
os.makedirs(result_directory, exist_ok=True)

'''Infrastructure Creation Mode'''
infrastructure_creation_mode = "taz" # or numberplugs

'''Simulation'''
timestep = 60  # in seconds


'''Predictions'''
prediction_add_noise = True
noise_param = 0.2

'''Sizing of Charging Stations'''
# demand charge in $/kWh
a_cost_sizing = 20
# free power demand as ratio to max charging power
P_free_Ratio_sizing = 0.0
# btms cost per cycle in $/kWh
b_cost_sizing = 300/5000
c_cost_sizing = 0.15

'''Creating optimal day ahead plan'''

###########################################
## Plots ##
###########################################
showPlots = False
plotPrediction = False
plotSizing = True
plotSizeX = 3.61
plotSizeY = 1.2
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
directory_figures = result_directory + os.sep + "figures"
os.makedirs(directory_figures, exist_ok=True)
path_Sim_original_data = '..' + os.sep + '..' + os.sep + "test_data" + os.sep + "advancedScenario7" + os.sep + "rhev-siting.6.events.7Advanced.csv"
path_Sim = '..' + os.sep + '..' + os.sep + "test_data" + os.sep + "advancedScenario7" + os.sep + "rhev-siting.6.events.7Advanced_filtered.csv"
dtype_Sim = {
       'time': 'int64', 'type': 'category', 'vehicle': 'string', 'parkingTaz': 'category','chargingPointType': 'category', 
       'primaryFuelLevel': 'float64', 'mode': 'category', 'currentTourMode': 'category', 'vehicleType': 'category', 
       'arrivalTime': 'float64', 'departureTime': 'float64', 'linkTravelTime': 'string', 'primaryFuelType': 'category', 
       'parkingZoneId': 'category','duration': 'float64' , 'shiftStatus': 'category',
        }
#'''Vehicle Generator'''
path_DataBase = '..' + os.sep + '..' + os.sep + "test_data" + os.sep + "advancedScenario7" + os.sep + "vehicletypes-HighEV2040_2021620.csv"
#'''Infrastructure File'''
path_infrastructure = '..' + os.sep + '..' + os.sep + "test_data" + os.sep + "advancedScenario7" + os.sep + "taz-parking_S80_P300_R250_F35k_Scenario7.csv"