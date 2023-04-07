'''
This script shall run the MPC simulation for the advanced scenario.
First, we set up the simulation environment and load results and parameters from prediction generation and sizing.
We only used the charging depots which determined at the end of step 4.
Then, we run the simulation and save the results.
'''

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

def main(SOC_start):
    # required filepaths
    streamHandler = components.loggerConfig()
    os.chdir('simulationScripts\\advancedScenario')

    path = result_parent_directory + os.sep + 'step6_MPC_simulation_own_charging_events'
    
    result_directory = path + os.sep + 'simulation_results'
    os.makedirs(result_directory, exist_ok=True)
    figure_directory = path + os.sep + 'figures'
    os.makedirs(figure_directory, exist_ok=True)

    sizing_results_stats_and_selected_stations_path = os.path.join(result_parent_directory, 'step4_btms_sizing_sensitivity', 'analysis', 'step4_used_charging_depots_for_control_with_stats_a_5.0.csv')
    a_value_selected = 5.0
    sizing_results_parent_directory = os.path.join(result_parent_directory, 'step4_btms_sizing_sensitivity', 'sizing_results')
    # find out in which folder the results for the selected a value are stored
    for folder in os.listdir(sizing_results_parent_directory):
        _path = os.path.join(sizing_results_parent_directory, folder)
        _path = os.listdir(_path)[0]
        _path = os.path.join(sizing_results_parent_directory, folder, _path)
        df = pd.read_csv(_path, index_col=0)
        if df['param: btms size, a,b_sys,b_cap,b_loan,c'].iloc[1] *365/12 == a_value_selected:
            sizing_results_directory = os.path.join(sizing_results_parent_directory, folder)
            break
    
    #intialize helper objects to create charging stations, but this are dummy objects and we will overwrite them later, because of multiprocessing
    # simulation broker
    _SimBroker = components.SimBroker(path_Sim, dtype_Sim)
    # result writer
    _ResultWriter = components.ResultWriter(result_directory)

    # create charging stations with create charging stations script
    path_infrastructure = os.path.join(result_parent_directory, 'step2_k_means_clustering', 'infrastructure_removed_zeros.csv')
    chargingStations = createChargingStations.createChargingStations(path_infrastructure, chargingStationClass, _ResultWriter, _SimBroker, btms_effiency=btms_efficiency)

    # delete charging stations which we want to exclude
    sizing_results_stats_and_selected_stations = pd.read_csv(sizing_results_stats_and_selected_stations_path, index_col=0)
    sizing_results_stats_and_selected_stations.index.name = 'taz'
    sizing_results_stats_and_selected_stations.index.astype(str)
    chargingStations_to_include = sizing_results_stats_and_selected_stations.index.values.astype(str)
    idx_station_to_include = []
    for i in range(len(chargingStations)):
        if chargingStations[i].ChargingStationId in chargingStations_to_include:
            idx_station_to_include.append(i)
            logging.info('Charging station ' + str(chargingStations[i].ChargingStationId) + ' included in simulation')
    chargingStations = [chargingStations[i] for i in idx_station_to_include]

    # load predictions 
    # load sizing results
    if chargingStationClass == components.ChaDepMpcBase:
        for x in chargingStations:
            taz_name = str(x.ChargingStationId)
            x.load_prediction(os.path.join(prediction_directory, taz_name + '.csv'))
            logging.info('Prediction for charging station ' + taz_name + ' loaded')
            x.load_determine_btms_size_results(os.path.join(sizing_results_directory, 'btms_sizing_' + taz_name + '.csv'))
            logging.info('Sizing results for charging station ' + taz_name + ' loaded')

    def simulation_for_one_charging_station(chargingStation: chargingStationClass, result_directory: str, use_events_of_charging_station: str):
        logging.info('Simulation for charging station ' + str(chargingStation.ChargingStationId) + ' started')
        # make own result directory
        result_directory = os.path.join(result_directory, str(chargingStation.ChargingStationId))
        os.makedirs(result_directory, exist_ok=True)

        #intialize helper objects
        '''Initialize helper classes'''
        # TODO for every Charging Station
        # simulation broker
        SimBroker = components.SimBroker(path_Sim, dtype_Sim)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": SimBroker initialized")
        # vehicle generator
        VehicleGenerator = components.VehicleGenerator(path_Sim, dtype_Sim, path_DataBase)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": VehicleGenerator initialized")
        # result writer
        ResultWriter = components.ResultWriter(result_directory)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": ResultWriter initialized")

        # overwrite SimBroker and ResultWriter of charging station for multiprocessing
        chargingStation.SimBroker = SimBroker
        chargingStation.ResultWriter = ResultWriter

        # initialize PhySimDummy and DermsDummy
        PhySimDummy = components.PhySimDummy(chargingStations)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": PhySimDummy initialized")
        DermsDummy  = components.DermsDummy(chargingStations)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": DermsDummy initialized")

        # initialize BTMS SOC
        chargingStation.BtmsEn = chargingStation.BtmsEn * SOC_start

        # start simulation
        max_iter = np.ceil((SimBroker.SimRes.index[-1] - SimBroker.SimRes.index[0])/timestep)
        progress_bar = tqdm(desc = 'MPC Sim @ Charging station ' + str(chargingStation.ChargingStationId), total = max_iter)
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": Simulation started")

        while not SimBroker.eol():
            # Sim Broker Step
            slice = SimBroker.step(timestep)
            # PhySimDummy and DermsDummy Step
            # GridPowerLower, GridPowerUpper = DermsDummy.output(chargingStation.ChargingStationId)
            # chargingStation.update_from_derms(GridPowerLower, GridPowerUpper)
            # chargingStation.update_from_grid_simulation(PhySimDummy.output(chargingStation.ChargingStationId))
            for i in range(len(slice)):
                # TODO test here dataypes
                rows_of_interest = slice.loc[slice["parkingTaz"] == int(use_events_of_charging_station)]
                rows_of_interest = rows_of_interest.loc[rows_of_interest["type"] == "ChargingPlugInEvent"]
                for row in rows_of_interest.iterrows():
                        vehicle = VehicleGenerator.generate_vechicle_from_df_slice(row)
                        chargingStation.arrival(vehicle, SimBroker.t_act)
            # charging station step
            chargingStation.step(timestep)
            progress_bar.update(1)
            # provide input to PhySimDummy and DermsDummy
            # PhySimDummy.input(chargingStation.ChargingStationId, sum(chargingStation.ChBaPower), chargingStation.P_BTMS, timestep)
            # DermsDummy.input(chargingStation.ChargingStationId, chargingStation.PowerDesire)
        progress_bar.close()
        logging.info("Charging station " + str(chargingStation.ChargingStationId) + ": Simulation finished")
        # write results
        ResultWriter.save()


    # launch multiprocessing

    for x in chargingStations:
        simulation_for_one_charging_station(x, result_directory, use_events_of_charging_station = x.ChargingStationId)

    # pool = mp.Pool(processes=6)
    # result_list_tqdm = []
    # for result in tqdm(pool.imap(func=do_sizing, iterable=chargingStations), total=len(chargingStations)):
    #     result_list_tqdm.append(result)
    # chargingStations = result_list_tqdm
    # pool.close()


if __name__ == '__main__':

    SOC_start = 0.8

    main(SOC_start=SOC_start)