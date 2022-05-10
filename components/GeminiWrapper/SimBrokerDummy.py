class SimBrokerDummy():

    # simple wrapper for time. usage of this object, because historically the Simulation Broker Object reference is given to a lot of modules and functions to provide the correct time.

    def __init__(self,t_start) -> None:
        self.t_act = t_start   # in seconds

    def updateTime(self, newTime):
        self.t_act = newTime
