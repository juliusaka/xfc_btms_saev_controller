# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc. Within the GEMINI-XFC project, we talk about Site Power Management Controllers (SPMC). Their task is to control charging power of a BTMS and the charging power of vehicles with low grid impact and high charging speed, constrained by grid power limits. The major difference of a SPMC for a SAEV-fleet compared to a SPMC for normal EVs is that its control strategy can influence the availability of ride-hailing services and should therefore work differently than a normal SPMC for private EVs. 

This code is set up so that it can be tested in a stand-alone version (without connection to other parts of the GEMINI-XFC framework), and also implemented in the GEMINI-XFC framework. The reason for this is, that the stand-alone version shall allow the user to quickly test changes of the control scheme, without waiting for results of the long-lasting BEAM simulation.

## python environment

this framework was developed using python 3.7.11. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

*first, I couldn't run python with anaconda on my PC. I then added path variables like described in this [video](https://www.youtube.com/watch?v=3Wt00qGlh3s). I also had to change the execution policy of Windows Powershell to RemoteSigned (Open PowerShell, Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework
- **numpy**
- **cvxopt**:


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
    - parameters:
        - BtmsSize
        - BtmsC: BTMS-C rating (e.g. 2C = max. charging speed is two full charges in one hour)
        - BtmsMaxPower = BtmsC*BtmsSize
        - BtmsMaxSoc, BtmsMinSoc
    - Variables:
        - BtmsEn: BTMS Energy Content, initialized with Btms0*BtmsSize
        - (BTMS SOC can be obtained by calling .BtmsSoc())
- Charging Bays properties:
    - parameters:
        - ChBaNum: Number of Charging Bays
        - ChBaMaxPower: list of maximum power for each charging bay
        - ChBaMaxPower_abs: maximum value from list above
        - ChBaParkingZoneId: ParkingZoneId associated with charging bays and maximum power withdrawal
    - Variables:
        - a list for Vehicle Objects which are in charging Bays
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

#### methods:

- *repark()*: 
    Adds first vehicles to the charging bays until capacity is reached.
    Then, it reparks the vehicles based on their need to charge. The charging desire of a vehicle can be calculated as

     $\text{CD} = \frac{E_\text{necessary}}{E_\text{possible}} = \frac{E_{\text{desired,Vehicle}(t_\text{end})} - E_{\text{Vehicle}(t)}} { (t_\text{end} - t) \cdot P_\text{max}}$
     
     with 

     $P_\text{max} = \text{min}(P_\text{Charging Depot, max} , P_\text{Vehicle, max})$

     with an excemption: if $t >= t_\text{end} $, then $\text{CD} = \text{inf}$

    The underlying sorting algorithm sorts the vehicles based on their charging desire and makes sure in the same vein, that vehicle in the charging bays don't unnecessarily switch postions. It throws an repark event each time a vehicle changes its position from charging bay to queue and reversed. The repark process assumes that all charging bays have the same charging capability. TODO: leverage for use in Beam

- updateFromDerms: updates the Grid Power Limit based on DERMS output

- updateFromPhySim: updates the CES Soc based on the output of the physical Simulation. *not used so far to prevent mistakes for debugging*

- chBaInit, chBaActiveCharges, chBaAdd, chBaReleaseThreshold: This are functions to handle the fact, that a list with the same length than number of charging plugs is needed. ChBaInit initializes this array and sets all elements to False, which means that no vehicle is present. ChBaAdd adds an vehicle to the first available charging bay, chBaReleaseThreshold releases vehicles which are fully charged.   


### subclasses of ChaDepParent:

### ChaDepLimCon
Charging Depot with Limit Controller
Algorithm overview, implemented in *step()*-function:

- *self.repark()*: sorts the vehicles with the inherited repark method to charging bays and queue.
- calculate maximum total charge power: if BTMS is sufficiently charge, maximum charging power is the grid limit + the BTMS power. If BTMS is close to reach min SOC, an intermediate value for the BTMS power is chosen, which maintains SOC >= min SOC. If BTMS SOC is <= min SOC, the maximum charging power is the grid limit.
- sorted by the charging desire CD, charging power is now distributed to the vehicles until the maximum charge power is reached. the actual charging power of each vehicle is determined by the Vehicle method *getMaxChargingPower(timestep)*. 
- determine on how to charge or discharge the BTMS: if the sum of all charging powers of the vehicles does not exceed the grid power limit the BTMS can be charged with a power, up to reaching the grid limit or the maximum BTMS charging power. Intermediate Charging Power for BTMS is choosen if BTMS is close to reach maximal SOC.
- update the BTMS and vehicle SOC
- write new chargingStation and vehicle states for the end of the timestep
- calculate power desires for charging vehicles and btms for the next time step to pass it to the DERMS
- release vehicles when full (delete them from charging bays or queue and throw ResultWriter Events)


### ChaDepMpcBase:

This is the base MPC model. It has three main methods:

- *determineBtmsSize()*: In this function, an optimization is ran, which determines the BTMS size based on predictions for charging demand. The prediction for this are generated from Beam output with random noise in *.generatePredictions()*. *determineBtmsSize()* saves the informations of the planning process to results.
- *planning()*: In this function, (day-) planning is performed. This means the control variables are determined in an optimization problem depended on prediction for charging demand and grid constraints. Runtime of this method can be longer, as a long horizon is optimized. The prediction for this are generated from Beam output with random noise in *.generatePredictions()*.
Planning saves the informations of the planning process to results.
- *step()*: This is the function which determines the control signals for each time step. Runtime of this should be short and has a short horizon.

Further information about the MpcBase controller can be found in the MpcBase File.

The *determineBtmsSize()* and *planning():*-function needs as input information all the properties of the charging station, [prediction about grid power limit (P_Lim(t))] and the uncurtailed Charging Demand (P_Charge,total(t)). *determineBtmsSize()* determines the storage size and *planning()* delivers and optimal trajectory for the collocated energy storage. 

To determine the uncurtailed charging demand based on given BEAM results, we assume:

- charging depots are rather large (law of big numbers), so that individual arrivals does not have that large influence
- the charging demand can be quiet well predicted, e.g. with machine learning models.

Because of this, we use the BEAM-results for each TAZ and add some random noise to the generated power profile to mimique a prediction through ML models.
Another option would be, to use one general prediction for all charging stations and scale it based on numbers of plugs.  


### Vehicle

an object as a datastructure for all the vehicle information. Has also methods to addEngy and addPower (give Power and duration). can be used in lists to represent the queue and charging bays.

- Vehicle Energy: the energy level of the vehicle
- desired Energy: the desired energy level of the vehicle (not the energy to be refilled)

methods:

-*getMaxChargePower(timestep)*: returns the maximum charge power at the actual time, ensuring that the vehicle doesn't exceed the desired energy level. (for last step of charging, an intermediate power level is therefore choosen)

-*updateEnergyLag*: returns the energy lag of a vehicle while charging. This is a rating metric and defined as the difference between anticipated energy level (by Beam) and real energy level.

$ E_{\text{Lag}}(t) = E_{\text{real}}(t) - E_{\text{anticipated}}(t)$

where $E_{\text{anticipated}}(t)$ is interpolated between desired energy level and arrival energy level based on the time, if actual time exceeds desired end, it is set to desired energy level. This function must be called in the charging controller.

-*getChargingTrajectories*: returns charging trajectories, one as a lower, one as upper bound of the energy demand for charging. This uses the function *getMaxChargePower()*, which has a parameter inverse for calculating the power level when going backwards. For the lower energy trajectory, we simplify the problem a bit and use the charging power at the end of the step, as solving for the average power in the period is an iterative process and harder to implement. If you would somehow implement the trajectory as a function of time E(t), you would maybe find a more exact solution by shifting that function in time. But as charging trajectories can never be perfectly described by an equation, this approach will be considered as good enough to show the general behaviour.

### VehicleGenerator

generates vehicles objects based on the outputs (a pandas dataframe slice) of the SimBroker. Links vehicleType with their maximum energy. Implemented as an object, so that vehicle-properties-file isn't loaded repeatedly. three major dataframes:

- Simulation Results SimRes: used to determine the following RefuelSessionEvent of ChargingPlugInEvent (loaded from csv) to calculated the desired final energy level.
- Vehicle Data Base: Contains the Vehicle Data Base (loaded from csv)
- Vehicle Dataframe: Connects VehicleIds with the Vehicle Type

The VehicleGenerator automatically determines in the method generateVehicles the maximum charging power based on strings like "FC(150.0|DC)", "XFC(400.0|DC)" the maximum charging power, it therefore searches for the symbols "(" and "|)". If you change this format, the function must also be changed.

### Sim Broker

Object, which provides the BEAM-simulation results to charging station simulation.

- with the initialization, the SimBroker looks for the first line with the start time
- for every call of *.step()*, the index of the rows from the last simulation time to the next simulation time is determined and a dataframe-slice with all the events happening in between given back. 
- the Sim Broker also performs the time handling, the reference should therefore be passed to every object of the simulation which needs it.

### Result Writer

opens 4 pandas data frames and writes charging station states, vehicle states and events regularily in it and chargingStationProperties one time in it. 

            
Finally, the data frames are saved as .csv files.

- *arrivalEvent*: writes states at vehicle arrival into events dataframe
- *reparkEvent*: writes states when vehicle change from queue to charging bay (bay to queue) into events dataframe
- *releaseEvent*: writes states when vehicle is released from station into events dataframe

*look for more information in the result writer module*

### Rating Metrics (done in ResultWriter)


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

- change VehicleGenerator, such that the vehicle generation with their properites(especially desired charging level) is directly passed, with no need to reconstruct them. Need for implementation for interaction with Beam. - **Done**

- build of a wrapper package, with dummies for some components - **Done**

- change in the long *repark()* algorithm to also contain different plug power levels / need to delete this. - To be done

- send power to Grid Simulation functions - To be done