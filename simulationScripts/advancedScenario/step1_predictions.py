#%% import packages
import sys
import os
from config import *
sys.path.append('../')
sys.path.append('../../')
import components
import components.ChaDepMpcBase as chargingStationClass
from simulationScripts import createChargingStations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import logging
streamHandler = components.loggerConfig()
result_directory = prediction_directory
figure_directory = prediction_directory + os.sep + 'figures'
os.makedirs(figure_directory, exist_ok=True)

#%% intialize helper objects
'''Initialize helper classes'''
# simulation broker
SimBroker = components.SimBroker(path_Sim, dtype_Sim)
logging.info("SimBroker initialized")
# vehicle generator
VehicleGenerator = components.VehicleGenerator(path_Sim, dtype_Sim, path_DataBase)
logging.info("VehicleGenerator initialized")
# result writer
ResultWriter = components.ResultWriter(result_directory)
logging.info("ResultWriter initialized")

#%% create charging stations
chargingStations = createChargingStations.createChargingStations(path_infrastructure, chargingStationClass, ResultWriter, SimBroker)


#%% initialize simulation

'''Simulation settings:'''
logging.info("timestep is set to " + str(timestep) + " seconds")

PhySimDummy = components.PhySimDummy(chargingStations)
logging.info("PhySimDummy initialized")
DermsDummy  = components.DermsDummy(chargingStations)
logging.info("DermsDummy initialized")

# %% generate predictions

# generate predictions of power usage at charging stations
if chargingStationClass == components.ChaDepMpcBase:
    for x in chargingStations:
        x.generate_prediction(path_BeamPredictionFile = path_Sim, dtype = dtype_Sim, path_DataBase = path_DataBase, timestep = timestep, addNoise = prediction_add_noise, noise_param = noise_param, prediction_directory = prediction_directory)
        logging.info("generated predictions for " + str(x.ChargingStationId))
# plot predictions
if plotPrediction:
    for x in chargingStations:
        ax = x.plot_prediction(figure_directory)
        logging.info("plotted predictions for " + str(x.ChargingStationId))
if showPlots:
    plt.show()
# %%
