# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc. Within the GEMINI-XFC project, we talk about Site Power Management Controllers (SPMC). Their task is to control charging power of a BTMS and the charging power of vehicles with low grid impact and high speed, constrained by grid power limits. The major difference of a SPMC for a SAEV-fleet compared to a SPMC for normal EVs is that its control strategy can influence the availability of ride-hailing services and should therefore work differently than a normal SPMC for private EVs.

This code is set up so that it can be tested in a stand-alone version (without connection to other parts of the GEMINI-XFC framework), and also implemented in the GEMINI-XFC framework. The reason for this is, that the stand-alone version shall allow the user to quickly test changes of the control scheme, without waiting for results of the long-lasting BEAM simulation.

## python environment

this framework was developed using python 3.7.11. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

*first, I couldn't run python with anaconda on my PC. I then added path variables like described in this [video](https://www.youtube.com/watch?v=3Wt00qGlh3s). I also had to change the execution policy of Windows Powershell to RemoteSigned (Open PowerShell, Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework
- **numpy**

## components

the components folder contains all objects which are necessary for the object oriented approach. All this objects are generated and used together in a main skript file.

### ChaDepParent

This is the parent class for Charging Depots. You can inherit subclasses from this, in which you implement the different controllers.

#### Properties / parts:
please look in the source code for a complete lis of this.
- BTMS properties
- Charging Bays properties; also a list for Vehicle Objects which are in charging Bays
- Grid Constraints; nomial variables for grid power limits
- Queue: for vehicles, if charging station is full.

#### subclasses:

- ChaDepLimCon: Charging Depot with Limit Controller
- ChaDepMPC: 

#### methods:

- *repark()*: reparks the vehicles based on their need to charge. The charging desire of a vehicle can be calculated as

     $ \text{CD} = \frac{E_\text{necessary}}{E_\text{possible}} = \frac{E_{\text{desired,Vehicle}(t_\text{end})} - E_{\text{Vehicle}(t)}} { (t_\text{end} - t) \quad P_\text{max}}$
     
     with 

     $P_\text{max} = \text{min}(P_\text{Charging Depot, max} , P_\text{Vehicle, max})$

     with an excemption: if $t_\text{end} <= t$, then $\text{CD} = \text{inf}$

     the repark process assumes that all charging bays have the same charging capability.

### Vehicle

an object as a datastructure for all the vehicle information. Has also methods to addEngy and addPower (give Power and duration). can be used in lists to represent the queue and charging bays.

### VehicleGenerator

generates vehicles objects based on the outputs (a pandas dataframe slice) of the SimBroker. Links vehicleType with their maximum energy. Implemented as an object, so that vehicle-properties-file isn't loaded repeatedly. three major dataframes:

- Simulation Results SimRes: used to determine the following RefuelSessionEvent of ChargingPlugInEvent (loaded from csv)
- Vehicle Data Base: Contains the Vehicle Data Base (loaded from csv)
- Vehicle Dataframe: Connects VehicleIds with the Vehicle Type

The VehicleGenerator automatically determines in the method generateVehicles the maximum charging power based on strings like "FC(150.0|DC)", "XFC(400.0|DC)" the maximum charging power, it therefore searches for the symbols "(" and "|)". If you change this format, the function must also be changed.

### Sim Broker

Object, which provides the BEAM-simulation results to charging station simulation.

- with the initialization, the SimBroker looks for the first line after the start time
- for every call of *.step()*, the index of the rows from the last simulation time to the next simulation time is determined and a dataframe-slice with all the events happening in between given back. 

### Result Writer

opens 3 pandas data frames and writes charging station states, vehicle states and events regularily in it. 

#### ChargingStationStates:

    "time", "ChargingStationID", "BaysVehicleIds", "BaysChargingPower", "BaysChargingDesire","BaysNumberOfVehicles", "QueueVehicleIds", "QueueChargingDesire", "QueueNumberOfVehicles", "TotalChargingPowerDesire", "BtmsChargingPowerDesire", "BtmsPower"

    BaysChargingPower: Actual Charging Power of each vehicle in the charging bays.
    TotalChargingDesire: Desire of power delivery from grid to charge vehicles (+/-)
    BtmsChargingPowerDesire: Desire of charging power to charge BTMS
    BtmsPower: Actual charging power of BTMS (+/-)

#### Events: 

    "time", "Event", "ChargingStationId", "VehicleId", "QueueOrBay", "ChargingDesire", "VehicleType", "VehicleArrival", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", "VehicleMaxEnergy", "VehicleMaxPower", "ChargingStationMaxPower"

#### VehicleState:
    "time", "VehicleId", "ChargingStationId", "QueueOrBay", "ChargingPower", "ChargingDesire", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", 

            
Finally, the data frames are saved as .csv files.

- *arrivalEvent*: writes states at vehicle arrival into events dataframe
- *reparkEvent*: writes states when vehicle change from queue to charging bay (bay to queue) into events dataframe
- *releaseEvent*: writes states when vehicle is released from station into events dataframe

*not finished*

## Adaption to use within GEMINI-XFC

- change VehicleGenerator, such that the vehicle population with their properites is directly passed, with no need to reconstruct them. Need for implementation for interaction with Beam.