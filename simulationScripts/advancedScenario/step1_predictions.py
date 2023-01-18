#%% import packages
import sys
import os
from config import *
sys.path.append('../')
sys.path.append('../../')
import components
from simulationScripts import createChargingStations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import logging
streamHandler = components.loggerConfig()

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