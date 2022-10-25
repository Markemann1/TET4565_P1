import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt


def task1_model():
    # Set data
    T1 = list(range(1, 25))      # Hour 1-24, day 1
    T2 = list(range(25, 49))     # Hour 25-48, day 2
    S = list(range(0, 5))        # Scenario 0-4

    # Parameters data
    M3S_TO_MM3 = 3.6/1000        # Convesion factor to MM^3
    MP = 50                      # Start-value of market price
    WV_end = 13000               # EUR/Mm^3
    prob = 0.2                   # 1/5 pr scenario
    Q_max = 100 * M3S_TO_MM3     # Mm^3
    P_max = 100                  # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
    V_max = 10                   # Mm^3
    IF_1 = 50 * M3S_TO_MM3       # Mm^3/h, Inflow Stage 1
    IF_2 = 25 * M3S_TO_MM3       # Mm^3/h, Inflow Stage 2
    V_01 = 5                     # Mm^3, initial water level, Stage 1

    model = pyo.ConcreteModel('Task 1')

    # ---------- Declaring sets ----------
    model.T1 = pyo.Set(initialize=T1)   # First 24 hours, t
    model.T2 = pyo.Set(initialize=T2)   # Last 24 hours, t
    model.S = pyo.Set(initialize=S)     # Scenarios, s

    # ---------- Declaring parameters ----------
    model.MP = pyo.Param(initialize=MP)                 # Market price at t
    model.WV = pyo.Param(initialize=WV_end)             # Water value at t = 48
    model.Prob = pyo.Param(initialize=prob)             # Probability of scenario
    model.Q_max = pyo.Param(initialize=Q_max)           # Max discharge of water to hydropower unit
    model.P_max = pyo.Param(initialize=P_max)           # Max power production of hydropower unit
    model.E_conv = pyo.Param(initialize=E_conv)         # Conversion of power, p, produced pr. discarged water, q
    model.V_max = pyo.Param(initialize=V_max)           # Max water capacity in reservoir
    model.IF_1 = pyo.Param(initialize=IF_1)             # Inflow in stage 1, deterministic
    model.IF_2 = pyo.Param(initialize=IF_2)             # Inflow in stage 2, stochastic
    model.V_01 = pyo.Param(initialize=V_01)             # Initial water level t = 1

    # ---------- Declaring decision variables ----------
    model.q1 = pyo.Var(model.T1, bounds=(0, Q_max))         # variable of discharged water from reservoir in T1
    model.p1 = pyo.Var(model.T1, bounds=(0, P_max))         # variable for production of power in T1
    model.v_res1 = pyo.Var(model.T1, bounds=(0, V_max))     # variable for reservoir level in T1

    model.q2 = pyo.Var(model.T2, model.S, bounds=(0, Q_max))        # variable of discharged water from reservoir in T2 pr. scenario
    model.p2 = pyo.Var(model.T2, model.S, bounds=(0, P_max))        # variable for production of power in T2 pr. scenario
    model.v_res2 = pyo.Var(model.T2, model.S, bounds=(0, V_max))    # variable for reservoir level in T2 pr. scenario

    # ---------- Objective function ----------
    def objective(model):
        o1 = sum(model.p1[t] * (model.MP + t) for t in model.T1)        # profits for T1
        o2 = sum(sum(model.Prob * model.p2[t, s] * (model.MP + t) for t in model.T2) for s in model.S)  # profits for T2 for rach scenario * probability
        o3 = model.Prob * sum(model.WV * model.v_res2[48, s] for s in model.S)  # profits from Water Value * remaining reservoir level at the end of day 2
        obj = o1 + o2 + o3  # summing all profit areas
        return obj
    model.OBJ = pyo.Objective(rule=objective(model), sense=pyo.maximize)  # setting the objective to maximize profits

    # ---------- Declaring constraints ----------
    def math_production1(model, t):  # variable dependency for production in T1
        return model.p1[t] == model.q1[t] * model.E_conv  # production = water discharge * power equivalent
    model.constr_productionDependency1 = pyo.Constraint(model.T1, rule=math_production1)

    def math_production2(model, t, s):  # variable dependency for production in T2 over all scenarios, S
        return model.p2[t, s] == model.q2[t, s] * model.E_conv  # production = water discharge * power equivalent
    model.constr_productionDependency2 = pyo.Constraint(model.T2, model.S, rule=math_production2)

    def math_v_res1(model, t):  # variable dependency for production in T1
        if t == 1:  # setting the start value of water reservoir at the start of day 1
            return model.v_res1[t] == model.V_01 + model.IF_1 - model.q1[t]  # water reservoir = initial volume + inflow - discharge
        else:  # for the rest of time in T1
            return model.v_res1[t] == model.v_res1[t-1] + model.IF_1 - model.q1[t]  # water reservoir = previous water level + inflow - discharge
    model.constr_math_v_res1 = pyo.Constraint(model.T1, rule=math_v_res1)

    def math_v_res2(model, t, s):  # variable dependency for production in T2
        if t == 25:  # setting the start value of water reservoir at the start of day 2
            return model.v_res2[t, s] == model.v_res1[24] + (model.IF_2 * s) - model.q2[t, s]  # water reservoir = volume from t=24 + inflow - discharge
        else:  # for the rest of time in T1
            return model.v_res2[t, s] == model.v_res2[(t-1), s] + (model.IF_2 * s) - model.q2[t, s]  # water reservoir = previous water level + inflow - discharge
    model.constr_math_v_res2 = pyo.Constraint(model.T2, model.S, rule=math_v_res2)

    # TODO: Oppg C = Endre på ting og si fra hva jeg endret - kommenter hvordan det endrer
    # todo: forslag: inflow, WV_end. KANSKJE sannsynlighet, men da må vi oppdatere Parameter_sannsynlighet -> liste, og oppdatere o3 i OBJ

    # ---------- Initializing solver and solving the problem ----------
    SolverFactory('gurobi').solve(model)
    # model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    # model.OBJ.display()
    # model.v_res1.display()
    # model.v_res2.display()

    # todo: rydde og forklare
    # Varshan tester ut plotting av graf under her
    resultat = []
    s1_plot = []
    s2_plot = []
    s3_plot = []
    s4_plot = []
    s0_plot = []

    for x in T1:
        y = model.v_res1[x].value
        resultat.append(y)

    # print(model.v_res2[(25, 0)].value)

    for x_2 in range(25, 49):
        y_0 = model.v_res2[(x_2, 0)].value
        s0_plot.append(y_0)

        y_1 = model.v_res2[(x_2, 1)].value
        s1_plot.append(y_1)

        y_2 = model.v_res2[(x_2, 2)].value
        s2_plot.append(y_2)

        y_3 = model.v_res2[(x_2, 3)].value
        s3_plot.append(y_3)

        y_4 = model.v_res2[(x_2, 4)].value
        s4_plot.append(y_4)

    print(s0_plot, s1_plot, s2_plot, s3_plot, s4_plot)

    plt.plot(T1, resultat)
    plt.plot(T2, s0_plot)
    plt.plot(T2, s1_plot)
    plt.plot(T2, s2_plot)
    plt.plot(T2, s3_plot)
    plt.plot(T2, s4_plot)
    plt.title("Her kommer tittel")
    plt.xlabel("Time")
    plt.ylabel("Water value")
    plt.grid(
        linestyle='--'
             )  # TODO: Trengs kanskje ikke men kan fjernes senere.
    plt.show()
    print(resultat)


#  def plotgraf(y_list):
#      for x in range (25):
#          for y in model.vres1:
#              print(model.vres1)
#      print(model)
