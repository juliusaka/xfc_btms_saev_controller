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

def calculate_interest_cost(investion, payback_time, interest_rate):
    # payback time in months, interest rate per month
    # url https://en.wikipedia.org/wiki/Mortgage_calculator
    monthly_payment = investion * interest_rate * (1 + interest_rate) ** payback_time / ((1 + interest_rate) ** payback_time - 1)
    interest_paid = monthly_payment * payback_time - investion
    return interest_paid

'''Sizing of Charging Stations'''
# demand charge in $/kWh amortized per day
a_cost_sizing = 20 / (365/12)
# btms cost per cycle in $/kWh
b_cap_cost_sizing_mid = 125/5400 # amortized per cycle
b_sys_cost_sizing_mid = (186  + calculate_interest_cost(186, 10*12, 0.05/12)) /(15*365) # amortized to one day, lifetime 15 years
b_loan_cost_sizing_mid = calculate_interest_cost(investion=b_cap_cost_sizing_mid*5400, payback_time=10*12, interest_rate=0.05/12)/(10*365) # capital cost per kWh amortized to one day
c_cost_sizing = 0.12 # electricity price in $/kWh
btms_efficiency = 0.85  # efficiency of btms

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