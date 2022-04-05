# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc. Within the GEMINI-XFC project, we talk about Site Power Management Controllers (SPMC). Their task is to control charging power of a BTMS and the charging power of vehicles with low grid impact and high speed, constrained by grid power limits. The major difference of a SPMC for a SAEV-fleet compared to a SPMC for normal EVs is that its control strategy can influence the availability of ride-hailing services and should therefore work differently than a normal SPMC for private EVs.

This code is set up so that it can be tested in a stand-alone version (without connection to other parts of the GEMINI-XFC framework), and also implemented in the GEMINI-XFC framework. The reason for this is, that the stand-alone version shall allow the user to quickly test changes of the control scheme, without waiting for results of the long-lasting BEAM simulation.

## python environment

this framework was developed using python 3.7.11. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

*first, I couldn't run python with anaconda on my PC. I then added path variables like described in this [video](https://www.youtube.com/watch?v=3Wt00qGlh3s). I also had to change the execution policy of Windows Powershell to RemoteSigned (Open PowerShell, Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework
- **numpy**

## Units

- time is in seconds [s]
- energy is in kilowatthours [kWh] - Beam is in J, must be convert with 3.6e6 J/kWh
- power is in kilowatt [kW]

## components

the components folder contains all objects which are necessary for the object oriented approach. All this objects are generated and used together in a main skript file.

### ChaDepParent

This is the parent class for Charging Depots. You can inherit subclasses from this, in which you implement the different controllers.

#### Properties / parts:

- ChargingStationId
- ResultWriter: Reference to ResultWriter Object
- BTMS properties:
    -parameters:
        - BtmsSize
        - BtmsC: BTMS-C rating (e.g. 2C = max. charging speed is two full charges in one hour)
        - BtmsMaxPower = BtmsC*BtmsSize
        - BtmsMaxSoc, BtmsMinSoc
    -Variables:
        - BtmsEn: BTMS Energy Content, initialized with Btms0*BtmsSize
        - (BTMS SOC can be obtained by calling .BtmsSoc())
- Charging Bays properties:
    - parameters:
        - ChBaNum: Number of Charging Bays
        - ChBaMaxPower: list of maximum power for each charging bay
        - ChBaMaxPower_abs: maximum value from list above
        - ChBaParkingZoneId: ParkingZoneId associated with charging bays and maximum power withdrawal
    -Variables:
        -a list for Vehicle Objects which are in charging Bays
- Grid Constraints
    - Parameters: 
        - GridPowerMax_Nom: nominal maximum grid power withdrawel of the whole charging station
    - Variables: 
        - GridPowerLower
        - GridPowerUpper
- Queue: for vehicles, if charging station is full.
    - Variables:
        - Queue: list for vehicles
-Simulation Data:
    - SimBroker: Reference to SimBroker object to obtain actual time.

if calcBtmsGridProp = True when you create the chargingStationObject, BtmsSize and GridPowerMax_Nom are determined on heuristics. If you don't specify all variables and parameters, standard values are used.

before the first step, an initilization function can be called:
    def initialize(self, t_start, GridPowerLower, GridPowerUpper):

### subclasses of ChaDepParent:

### ChaDepLimCon
Charging Depot with Limit Controller



### ChaDepMPC: 

#### methods:

- *repark()*: reparks the vehicles based on their need to charge. The charging desire of a vehicle can be calculated as

     $ \text{CD} = \frac{E_\text{necessary}}{E_\text{possible}} = \frac{E_{\text{desired,Vehicle}(t_\text{end})} - E_{\text{Vehicle}(t)}} { (t_\text{end} - t) \quad P_\text{max}}$
     
     with 

     $P_\text{max} = \text{min}(P_\text{Charging Depot, max} , P_\text{Vehicle, max})$

     with an excemption: if $t >= t_\text{end} $, then $\text{CD} = \text{inf}$

     the repark process assumes that all charging bays have the same charging capability.

- updateFromDerms: updates the Grid Power Limit based on DERMS output

- updateFromPhySim: updates the CES Soc based on the output of the physical Simulation. *not used so far to prevent mistakes for debugging*

### Vehicle

an object as a datastructure for all the vehicle information. Has also methods to addEngy and addPower (give Power and duration). can be used in lists to represent the queue and charging bays.

- Vehicle Energy: the energy level of the vehicle
- desired Energy: the desired energy level of the vehicle (not the energy to be refilled)

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
- the Sim Broker also performs the time handling, the reference should therefore be passed to every object of the simulation which needs it.

### Result Writer

opens 3 pandas data frames and writes charging station states, vehicle states and events regularily in it. 

#### ChargingStationStates:

    "time", "ChargingStationID", "BaysVehicleIds", "BaysChargingPower", "BaysChargingDesire","BaysNumberOfVehicles", "QueueVehicleIds", "QueueChargingDesire", "QueueNumberOfVehicles", "TotalChargingPowerDesire", "BtmsChargingPowerDesire", "BtmsPower"

    BaysChargingPower: Actual Charging Power of each vehicle in the charging bays.
    TotalChargingDesire: Desire of power delivery from grid to charge vehicles (+/-)
    BtmsChargingPowerDesire: Desire of charging power to charge BTMS
    BtmsPower: Actual charging power of BTMS (+/-)

#### Events: 

    "time", "Event", "ChargingStationId", "VehicleId", "QueueOrBay", "ChargingDesire", "VehicleType", "VehicleArrival", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", "VehicleMaxEnergy", "VehicleMaxPower", "ChargingBayMaxPower"

#### VehicleState:
    "time", "VehicleId", "ChargingStationId", "QueueOrBay", "ChargingPower", "ChargingDesire", "VehicleDesiredEnd", "VehicleEnergy", "VehicleDesiredEnergy", "VehicleSoc", 

            
Finally, the data frames are saved as .csv files.

- *arrivalEvent*: writes states at vehicle arrival into events dataframe
- *reparkEvent*: writes states when vehicle change from queue to charging bay (bay to queue) into events dataframe
- *releaseEvent*: writes states when vehicle is released from station into events dataframe

*not finished*

### Physiscs Simulation Dummy (PhySimDummy)

likewise to the Signal-Flow chart we produced, this is a dummy for the grid simulation and the Colocated Energy Storage (CES) Simulation.

- INPUTS from SPMC:
    - Net Load = observed charging load + CES charge power
    - CES charging power command
- OUTPUTS to SPMC:
    - SOC of CES

This dummy must take from each charging station inputs and provide outputs as well.

must be created after all charging stations are created, because it builds up based on them

adds normal distributed noise on the storage charging command

### DERMS Dummy (DermsDummy)

likewise to the signal flow chart we produced, this is a dummy for the Distributed Energy Resources Manager.

- INPUTS from SPMC: 
    - Desired Charging Power
- OUTPUTS to SPMC:
    - Site net power limits (upper and lower bound)

This dummy must take from each charging station inputs and provide outputs as well.

adds normal distributed noise on grid power limits

### BEAM Dummy

this is the Simulation Broker. The simulation broker has the other task to distribute the time to each element.

## Adaption to use within GEMINI-XFC

- change VehicleGenerator, such that the vehicle population with their properites is directly passed, with no need to reconstruct them. Need for implementation for interaction with Beam.