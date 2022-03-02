# xfc-btms-saev-controller

Developement of a controller for an extreme-fast-charging (XFC) depot with behind-the-meter storage (BTMS) for shared autonomous electric vehicle (SAEV) fleets in the project GEMINI-XFC with the transportation simulation software BEAM. This controller can be connected with HELICS to BEAM, PyDSS etc. 

## python environment

this framework was developed using python 3.10. There is an Andaconda-Image, which can be used to import a fitting environment. Please make sure, that this environment is used.

below, there is a list of important used packages:

- **dask**: used for processing the large output-csv for the independent controller developement framework