import components
class ControlWrapper():

    def __init__(self) -> None:
        pass
    
    def departure(self, vehicleInfo) -> None:
        # for future implementation, should throw an error message
        pass

    def arrival(self, vehicleInfo) -> None:
        pass

    def step (self, timestep):
        pass
        # return dict structure with vehicleId, power and release


    def test_time(self, time):
        Bro = components.GeminiWrapper.SimBrokerDummy()
        Bro.updateTime(time)
        print('hello')
        print(Bro.t_act)

    