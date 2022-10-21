import pyomo.environ as pyo
from pyomo.opt import SolverFactory

#Set data
T1 = list(range(1, 25))  # Hour 1-24
T2 = list(range(25, 49))  # Hour 25-48
S = list(range(0, 5))  # Scenario 0-4

#Parameter data
M3S_TO_MM3 = 3.6 / 1000  # Convesion factor to MM^3
MP = 50  # Start-value of market price
WV_end = 13000  # EUR/Mm^3
prob = 0.2  # 1/5 pr scenario
Q_max = 100 * M3S_TO_MM3  # Mm^3
P_max = 100  # MW (over 1 hour)
E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
V_max = 10  # Mm^3
IF_1 = 50 * M3S_TO_MM3  # Mm^3/h, Inflow Stage 1
IF_2 = 25 * M3S_TO_MM3  # Mm^3/h, Inflow Stage 2
V_01 = 5  # Mm^3, initial water level, Stage 1

print(skjdfnksjd)