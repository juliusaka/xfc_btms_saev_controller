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

def main(result_directory, a, b_sys, b_cap, b_loan, c, d_wait_cost):
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
    # %% perform btms sizing
    # make iterable which contains all parameters for do_sizing function
    iterables = [[x, a, b_sys, b_cap, b_loan, c, d_wait_cost] for x in chargingStations]
    
    # # test without multiprocessing
    # for iterable in tqdm(iterables):
    #     do_sizing(iterable)
    # count only half of the cores if on windows
    if os.name == 'nt':
        pool = mp.Pool(processes=int(mp.cpu_count()/2))
        print(' pool initiliazed with ' + str(int(mp.cpu_count()/2)) + ' cores')
    else:
        pool = mp.Pool(processes=mp.cpu_count())
        print(' pool initiliazed with ' + str(mp.cpu_count()) + ' cores')
    result_list_tqdm = []
    for result in tqdm(pool.imap(func=do_sizing, iterable=iterables), total=len(chargingStations), leave = False):
        result_list_tqdm.append(result)
    chargingStations = result_list_tqdm
    pool.close()

    os.chdir(old_directory)

def do_sizing(iterable):
    iterable[0].determine_btms_size(iterable[0].SimBroker.t_act, iterable[0].SimBroker.t_max, timestep, iterable[1], iterable[2], iterable[3], iterable[4], iterable[5], d_wait_cost = iterable[6])
    return iterable[0]

#%% main

if __name__ == '__main__':
    
    a_cost_sizing = np.array([2,5,8, 10]) / (365/12)
    #d_wait_cost = np.array([1, 5, 10, 15, 20])
    d_wait_cost = np.array(['varying'])
    
    path = result_parent_directory + os.sep + 'step4c_btms_sizing_sensitivity_wait_time' + os.sep + 'sizing_results' 
    print(path)
    print('Did you delete old files?')
    for a_x in tqdm(a_cost_sizing):
        for d_x in tqdm(d_wait_cost):
            result_directory = os.path.join(path, str(uuid.uuid4()))
            main(result_directory, a_x, b_sys_cost_sizing_mid, b_cap_cost_sizing_mid, b_loan_cost_sizing_mid, c_cost_sizing, d_x)