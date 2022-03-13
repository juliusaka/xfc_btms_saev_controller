# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc.

## python environment

this framework was developed using python 3.10. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

*first, I couldn't run python with anaconda on my PC. I then added path variables like described in this [video](https://www.youtube.com/watch?v=3Wt00qGlh3s). I also had to change the execution policy of Windows Powershell to RemoteSigned (Open PowerShell, Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser*

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework
- **numpy**

## components

*include here description of the object oriented approach*

the components folder contains all objects which are necessary for the object oriented approach.

### ChargingStation

This is the class for the chargingStation

#### Properties:
- BTMS: Size, C-Rating, minSOC, maxSOC 

(could add min/max SOC for planning and for operation differently)
- Charging Bays (ChBa)

(could initialize charging bays also with opening parking file, maybe add this later)

### Vehicle
an object, as a datastructure for all the vehicle information. Has also methods to addEngy and addPower (give Power and duration). can be used in lists to code the queue and charging bays.