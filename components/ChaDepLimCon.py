import ChaDepParent

class ChaDepLimCon(ChaDepParent):

    def step(self, timestep):
        # class method to perform control action for the next simulation step.
        '''Requirements:'''
            # release vehicles when full from charging bays
            # repark vehicles from queue to charging bays if possible
            # update control action from last step with new results for SOC, P_total, P_Btms
            # perform controller action
            # function INPUTS: Grid Limits, Revised SOC of Storage, 
            #                  Revised power withdrawals from last step
            # function OUTPUTS: Power from Grid, from BTMS
        pass