# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc.

This code is set up so that it can be tested in a stand-alone version (without connection to other parts of the GEMINI-XFC framework), and also implemented in the GEMINI-XFC framework. The reason for this is, that the stand-alone version shall allow the user to quickly test changes of the control scheme, without waiting for results of the long-lasting BEAM simulation.

## python environment

this framework was developed using python 3.10. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

*first, I couldn't run python with anaconda on my PC. I then added path variables like described in this [video](https://www.youtube.com/watch?v=3Wt00qGlh3s). I also had to change the execution policy of Windows Powershell to RemoteSigned (Open PowerShell, Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework
- **numpy**

## components

*include here description of the object oriented approach*

the components folder contains all objects which are necessary for the object oriented approach.

### ChaDepParent

This is the parent class for Charging Depots. You can inherit subclasses from this, in which you implement the different Controllers

#### Properties / parts:
please look in the source code for a complete lis of this.
- BTMS properties
- Charging Bays properties; also a list for Vehicle Objects which are in charging Bays
- Grid Constraints; nomial variables for grid power limits
- Queue: for vehicles, if charging station is full.

#### subclasses:

- ChaDepLimCon: Charging Depot with Limit Controller
- ChaDepMPC: 


### Vehicle

an object, as a datastructure for all the vehicle information. Has also methods to addEngy and addPower (give Power and duration). can be used in lists to code the queue and charging bays.


### VehicleGenerator:

generates vehicles objects based on the outputs of the SimBroker. Links vehicleType with their maximum energy. Implemented like this, so that vehicle-properties-file isn't loaded repeatedly 

### Sim Broker
Object, which provides the BEAM-simulation results to charging station simulation.

- with the initialization, the SimBroker looks for the first line after the start time
- for every call of step, the index of the rows from the last simulation time to the next simulation time is determined and a dataframe-slice with all the events happening in between given back. 