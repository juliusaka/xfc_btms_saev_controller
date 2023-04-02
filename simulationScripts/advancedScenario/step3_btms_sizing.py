# do sizing for all chargining depots with nominal values from thesis
# save btms sizes ad trajectories for every station in a csv file
# pick 2,3 examples for thesis later to show working principle of BTMS
# show with them the effect of flexible energy price (and flexible demand charge))
import sys
import os
from config import *
sys.path.append('../')
sys.path.append('../../')
sys.path.append('c:\\Users\\akaju\\Documents\\GitHub\\xfc_btms_saev_controller')
import components
import components.ChaDepMpcBase as chargingStationClass
from simulationScripts import createChargingStations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import logging
import multiprocessing as mp

def main():
    #%% import packages
    streamHandler = components.loggerConfig()
    os.chdir('simulationScripts\\advancedScenario')

    result_directory = result_parent_directory + os.sep + 'step3_btms_sizing'
    figure_directory = prediction_directory + os.sep + 'figures'
    os.makedirs(result_directory, exist_ok=True)
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
    path_infrastructure = os.path.join(result_parent_directory, 'step2_k_means_clustering', 'infrastructure_removed_zeros.csv')
    chargingStations = createChargingStations.createChargingStations(path_infrastructure, chargingStationClass, ResultWriter, SimBroker, btms_effiency=btms_efficiency)


    #%% initialize simulation

    '''Simulation settings:'''
    logging.info("timestep is set to " + str(timestep) + " seconds")

    PhySimDummy = components.PhySimDummy(chargingStations)
    logging.info("PhySimDummy initialized")
    DermsDummy  = components.DermsDummy(chargingStations)
    logging.info("DermsDummy initialized")

    # %%  load predictions of power usage at charging stations
    if chargingStationClass == components.ChaDepMpcBase:
        for x in chargingStations:
            taz_name = str(x.ChargingStationId)
            x.load_prediction(os.path.join(prediction_directory, taz_name + '.csv'))
    # %% perform btms sizing
    if True: # for testing
        for x in tqdm(chargingStations):
                do_sizing(x)

    
    pool = mp.Pool(4)
    result_list_tqdm = []
    for result in tqdm(pool.imap(func=do_sizing, iterable=chargingStations), total=len(chargingStations)):
        result_list_tqdm.append(result)
    chargingStations = result_list_tqdm
    pool.close()


#%% do this with multiprocessing

def do_sizing(x):
    x.determine_btms_size(x.SimBroker.t_act, x.SimBroker.t_max, timestep, a_cost_sizing, b_sys_cost_sizing_mid, b_cap_cost_sizing_mid, c_cost_sizing)
    return x

if __name__ == '__main__':
    main()