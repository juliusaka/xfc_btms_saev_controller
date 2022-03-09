# explanations of data files
## event file:
- Time: The moment the event was fired
- DepartureTime is the time of departure (might be different due to asynchronous simulation)
- type: for charging interesting:
    - ChargingPlugInEvent: start of charging session
    - RefuelSessionEvent: the time of the end of charging event
        - calc start charge time from this event as time – duration
    - ChargingPlugOutEvent
- arrivalTime, departureTime, duration, fuel (energy in [J])
## parking file (gemini-base-scenario-3-charging-no-household-infra16.csv) 
87% of EVs have acces to at home charging, 15% EV-penetration
- unitil now: no ride-hail, no autonomous fleets
- to make up charging depots: aggregate taz --> change parktypeid and set sum of chargePoints, calculate avg Price
- could make one for fast charging (fc) and one for extreme fast charging (xfc) or together
vehicle file (vehicletypes-Base_2035_20210204_updated.csv)
- if charging capability is empty -> charging power has no limits