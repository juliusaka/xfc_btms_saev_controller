
class ResultWriter:

    def __init__(self, filename, t_act) -> None:

        pass




'''What data could data output be like?

    - charging station focused (we have multiple charging stations)
        Bays and Queue with vehicle states, power
            Bays: columns for states
            Queue: no of vehicles + string with vehicle IDs and Charging Desire
        Vehicle repark events
        vehicle release events

    - vehicle event focused:
        vehicleId, chargingStation, arrival, repark, release
        VehicleType, VehicleArrival, VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleSoc, VehicleMaxEngy, VehicleMaxPower

    - vehicle state focused:
        vehicleId, chargingStation, 
        charging power, (queue/charge), VehicleDesEnd, VehicleEngy, VehicleDesEngy, VehicleSoc, ChargingDesire

example line

time | vehicle_event    | vehicleId | vehiclePos (for state) |chargingStation_event | chargingStationId |

xxxx | vehicle_arrival  | xxxx      |
xxxx | vehicle_repark   | xxxx      |
xxxx | vehicle_state    |
xxxx | vehicle_release  |

'''