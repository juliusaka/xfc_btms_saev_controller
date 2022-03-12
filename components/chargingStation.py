class ChargingStation:
    
    def __init__(self, BtmsSize = 100, BtmsC = 1, BtmsMaxSoc = 0.8, BtmsMinSOC = 0.2, ChBaNum = 2, ChBaMaxPower = [200, 200], ChBaParkingZoneId = ["xxx1", "xxx2"], calcBtmsGridProp = False, GridPowerMax_Nom = 200 ):

        '''BTMS properties'''
        if calcBtmsGridProp:
            self.BtmsSize       = sum(ChBaMaxPower)/2 #empirical formula (check with literature)
        else:
            self.BtmsSize       = BtmsSize        # size of the BTMS in kWh
        self.BtmsC              = BtmsC           # C-Rating of BTMS (1C is a complete charge an hour)
        self.BtmsMaxSoc         = BtmsMaxSoc      # maximal allowed SOC of BTMS
        self.BtmsMinSoc         = BtmsMinSOC      # minimal allowed SOC of BTMS

        '''Charging Bays'''
        #properties
        self.ChBaNum            = ChBaNum           # number of charging bays
        self.ChBaMaxPower       = ChBaMaxPower      # list of maximum power for each charging bay in kW
        self.ChBaParkingZoneId  = ChBaParkingZoneId # list of parking zone ids associated with max power list
        #variables
        self.ChBaVehicle        = []                # vehicles IDs, which are currently charging in a bay
        self.ChBaVehicleArrival = []                # list for arrival time of vehicles
        self.ChBaVehicleDesEnd  = []                # list of desired end times of charging
        self.ChBaVehicleEn      = []                # list for Energy State of vehicles [kWh]
        self.ChBaVehicleDesEn   = []                # list of desired Energy State of vehicles [kWh]
        self.ChBaVehicleSoc     = []                # list of SOC of vehicles [%]
        self.ChBaVehicleMaxEn   = []                # list of maximal energy state of vehicles [kWh]

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

        '''charging depot infrastructure'''
        self.Queue                  = []                # list for vehicles, which are currently in the queue, waiting for a free charging site

    def dayPlanning():
        # class method to perform day planning
        pass

    def arrival():
        # class method to let vehicles arrive
        pass

    def step():
        # class method to perform control action for the next simulation step.
        pass

        