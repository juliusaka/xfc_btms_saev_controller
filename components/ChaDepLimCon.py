from components import ChaDepParent

class ChaDepLimCon(ChaDepParent):

    def step(self, timestep):
        # class method to perform control action for the next simulation step.

        # repark vehicles from queue to charging bays if possible
        '''update that method!'''
        self.repark()
            # include ResultWriter

        # control action

            # if SOC < SOC_min
                # P_max = GridUpper (choose middle value for intermediate)
            # else P_Max = GridUpper + P_BTMS

            # while vehicles in ChargingBays
                # if sum(P_ChargingBays) < P_max - P_OneChargingBay:
                    # assign power values for vehicles in the order of the charging desire
                # else 
                    # for last vehicle P_chargingBay = P_max - sum(Pchargingbays)
                # if len(chargingBays) > No of Stalls:
                    #break

            # if SOC > SOC_max
                # P_BTMS = 0
            # elseif: 
                # add intermediate solution
            # else
                # P_BTMS = P_Grid - sum(P_chargingBays)

        # calculate new SOC BTMS, vehicles and update vehicle states
        # SOC_BTMS = BTMS_EN + P_BTMS * timestep
        # for vehicles in chargingbays:
            # vehicle.addEngy(P, timestep)
        
        # result Writer for chargingStation states and vehicle states

        # release vehicles when full from charging bays - add epsilon!
            # determine also max power to reach SOC_target
    pass