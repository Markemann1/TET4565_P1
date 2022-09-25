
# Hydropower unit
V_0 = 5  # mm3
V_MAX = 10  # mm3
Q_MAX = 100  # m^3/s
M3S_TO_MM3 = 3.6/1000  # mm3/m^3
E_conv = 0.981  # MWh/m^3
WV_end = 13000  # EUR/mm3

scen = 'scenarios'
t = list(range(0, 48))
# Inflow & prices
Inflow_24t = 50  # m^3/s
Inflow_48t = 25*scen  # m^3/s
N_Scenarios = 5  # 5 scenarios for the last 24 hours
P_scenario = 1/5  # [per unit], probability each scenario
Price = 50 + t  # linearly increasing cost based on timestep, from 0 to 48 hour
