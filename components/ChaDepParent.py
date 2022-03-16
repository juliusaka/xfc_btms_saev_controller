class ChaDepParent:
    
    def __init__(self, BtmsSize = 100, BtmsC = 1, BtmsMaxSoc = 0.8, BtmsMinSOC = 0.2, BtmsSoc0 = 0.50, ChBaNum = 2, ChBaMaxPower = [200, 200], ChBaParkingZoneId = ["xxx1", "xxx2"], calcBtmsGridProp = False, GridPowerMax_Nom = 200, GridPowerLower = -1, GridPowerUpper = 1):

        '''BTMS'''
        # properties
        if calcBtmsGridProp:
            self.BtmsSize       = sum(ChBaMaxPower)/2 #empirical formula (check with literature)
        else:
            self.BtmsSize       = BtmsSize          # size of the BTMS in kWh
        self.BtmsC              = BtmsC             # C-Rating of BTMS (1C is a complete charge an hour)
        self.BtmsMaxSoc         = BtmsMaxSoc        # maximal allowed SOC of BTMS
        self.BtmsMinSoc         = BtmsMinSOC        # minimal allowed SOC of BTMS
        #variables:
        self.BtmsEn             = BtmsSoc0 * BtmsSize # start BTMS energy content at initialization [kWh]
        self.BtmsSOC            = BtmsSoc0          # start SOC at initialization [-]


        '''Charging Bays'''
        #properties
        self.ChBaNum            = ChBaNum           # number of charging bays
        self.ChBaMaxPower       = ChBaMaxPower      # list of maximum power for each charging bay in kW
        self.ChBaParkingZoneId  = ChBaParkingZoneId # list of parking zone ids associated with max power list
        #variables
        self.ChBaVehicles       = []                # list for Vehicles objects, which are in charging bays.

        if (ChBaNum != len(ChBaMaxPower)):
            raise ValueError(' number of charging bays doesnt equals size of list with maximal plug power')
        if (ChBaNum != len(ChBaParkingZoneId)):
            raise ValueError(' number of charging bays doesnt equals size of list with parking zone ids')
        if (len(ChBaMaxPower) != len(ChBaParkingZoneId)):
            raise ValueError(' size of list with maximal plug power doesnt equals size of list with parking zone ids')
        

        '''Grid Constraints'''
        if calcBtmsGridProp:
            self.GridPowerMax_Nom   = sum(ChBaMaxPower)/2 # empirical formula (check with literature)
        else:
            self.GridPowerMax_Nom   = GridPowerMax_Nom  # maximum power withdrawal from grid, nominal value (can be time-varying)
        self.GridPowerLower         = GridPowerLower  # will be assigned in step function
        self.GridPowerUpper         = GridPowerUpper  # will be assigned in step function


        '''charging depot infrastructure'''
        #variables
        self.QueueVehicles          = []                # list for Vehicles objects, which are in the queue.

        '''controller'''
        #properties
        self.Controller             = 0                 # add here Controller Object.



    def dayPlanning(self):
        # class method to perform day planning
        pass

    def arrival(self, *vehicles):
        # class method to let vehicles arrive
        '''Requirements: '''
            # put vehicles to the Queue
        pass

    def release(self):
        # class method to release vehicles
        # TODO will this be done by the chargingStation itself?

        return 0

    def step(self, timestep):
        # class method to perform control action for the next simulation step.
        '''Requirements:'''
            # release vehicles when fuel from charging bays
            # repark vehicles from queue to charging bays if possible
            # update control action from last step with new results for SOC, P_total, P_Btms
            # perform controller action
            # function INPUTS: Grid Limits, Revised SOC of Storage, 
            #                  Revised power withdrawals from last step
            # function OUTPUTS: Power from Grid, from BTMS


        pass

        