# do sizing for all chargining depots with nominal values from thesis
# save btms sizes ad trajectories for every station in a csv file
# pick 2,3 examples for thesis later to show working principle of BTMS
# show with them the effect of flexible energy price (and flexible demand charge))
import os
#os.chdir('/workspaces/xfc_btms_saev_controller/')
import sys
sys.path.append(os.getcwd())
from config import *
sys.path.append('../')
sys.path.append('../../')
#sys.path.append('c:\\Users\\akaju\\Documents\\GitHub\\xfc_btms_saev_controller')
import components
import components.ChaDepMpcBase as chargingStationClass
from simulationScripts import createChargingStations
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
import logging
import multiprocessing as mp
import uuid

def main(result_directory, a, b_sys, b_cap, b_loan, c):
    #%% import packages
    #streamHandler = components.loggerConfig()
    old_directory = os.getcwd()
    os.chdir('simulationScripts'+os.sep+ 'advancedScenario')

    os.makedirs(result_directory, exist_ok=True)

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

    #%% perform btms sizing
    # for x in tqdm(chargingStations):
    #     a = 20/(365/12)
    #     x.determine_btms_size(SimBroker.t_act, SimBroker.t_max, timestep, a, b_sys, b_cap, b_loan, c, include_max_c_rate = True, max_c_rate = max_c_rate)
    
    #define function to be used in multiprocessing with a, b, c as parameters inherited from main function call
    
    pool = mp.Pool(processes=mp.cpu_count())
    result_list_tqdm = []
    # make iterable
    iterables = [[x, a, b_sys, b_cap, b_loan, c] for x in chargingStations]
    for result in tqdm(pool.imap(func=do_sizing, iterable=iterables), total=len(chargingStations), leave = False):
        result_list_tqdm.append(result)
    chargingStations = result_list_tqdm
    pool.close()

    os.chdir(old_directory)

def do_sizing(iterable):
    iterable[0].determine_btms_size(iterable[0].SimBroker.t_act, iterable[0].SimBroker.t_max, timestep, iterable[1], iterable[2], iterable[3], iterable[4], iterable[5], include_max_c_rate = True, max_c_rate = max_c_rate)
    return iterable[0]

#%% main

if __name__ == '__main__':
    
    #a_cost_sizing = np.concatenate([np.arange(0, 8, 1), np.arange(8,21,2)]) / (365/12)
    #a_cost_sizing = np.array([5]) / (365/12)
    a_cost_sizing = np.array([0,1,2,3,4,6,8,10,12,14,16,20]) / (365/12)
    path = result_parent_directory + os.sep + 'step4b_btms_sizing_sensitivity_c_rate_high_interest' + os.sep + 'sizing_results'
    os.makedirs(path, exist_ok=True) 
    print('Did you delete old files?')
    for x in tqdm(a_cost_sizing):
        result_directory = os.path.join(path, str(uuid.uuid4()))
        print(result_directory)
        b_loan_cost_sizing_mid = calculate_interest_cost(investion=b_cap_cost_sizing_mid*5400, payback_time=10*12, interest_rate=0.15/12)/(10*365)
        main(result_directory, x, b_sys_cost_sizing_mid, b_cap_cost_sizing_mid, b_loan_cost_sizing_mid, c_cost_sizing)