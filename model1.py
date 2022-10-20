import pyomo.environ as pyo
from pyomo.opt import SolverFactory


def task1_model():
    # Set data
    T1 = list(range(1, 25))     # Hour 1-24
    T2 = list(range(25, 49))    # Hour 25-48
    S = list(range(0, 5))       # Scenario 0-4

    # Parameters data
    M3S_TO_MM3 = 3.6/1000   # Convesion factor to MM^3
    MP = 50                 # Start-value of market price
    WV_end = 13000          # EUR/Mm^3
    prob = 0.2              # 1/5 pr scenario
    Q_max = 100 * M3S_TO_MM3        # Mm^3
    P_max = 100             # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3         # MWh/Mm^3
    V_max = 10              # Mm^3
    IF_1 = 50 * M3S_TO_MM3             # Mm^3/h, Inflow Stage 1
    IF_2 = 25 * M3S_TO_MM3             # Mm^3/h, Inflow Stage 2
    V_01 = 5                # Mm^3, initial water level, Stage 1

    model = pyo.ConcreteModel('Task 1b')

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
    model.q1 = pyo.Var(model.T1, bounds=(0, Q_max))
    model.p1 = pyo.Var(model.T1, bounds=(0, P_max))
    model.v_res1 = pyo.Var(model.T1, bounds=(0, V_max), initialize=model.V_01)

    model.q2 = pyo.Var(model.T2, model.S, bounds=(0, Q_max))
    model.p2 = pyo.Var(model.T2, model.S, bounds=(0, P_max))
    model.v_res2 = pyo.Var(model.T2, model.S, bounds=(0, V_max), initialize=model.v_res1[24])

    # ---------- Objective function ----------
    def objective(model):  # t - 1 fordi ikke null-indeksert
        o1 = sum(model.p1[t] * (model.MP + t) for t in model.T1)  # t=(1,24) production * market price
        o2 = sum(sum(model.Prob * model.p2[t, s] * (model.MP + t) for t in model.T2) for s in model.S)  # t=(25,48) scenario probability * production(s) * market price
        o3 = model.Prob * sum(model.WV * model.v_res2[48, s] for s in model.S)  # t=48 reservoir level * water value
        obj = o1 + o2 + o3  # summing all profits
        return obj
    model.OBJ = pyo.Objective(rule=objective(model), sense=pyo.maximize)

    # ---------- Declaring constraints ----------
    def math_production1(model, t):  # production = water discharge * power equivalent
        return model.p1[t] == model.q1[t] * model.E_conv
    model.constr_productionDependency1 = pyo.Constraint(model.T1, rule=math_production1)

    def math_production2(model, t, s):  # production = water discharge * power equivalent
        return model.p2[t, s] == model.q2[t, s] * model.E_conv
    model.constr_productionDependency2 = pyo.Constraint(model.T2, model.S, rule=math_production2)

    def math_v_res1(model, t):  # water reservoir = init volume + inflow - discharge
        if t == 1:
            return model.v_res1[t] == model.V_01 + model.IF_1 - model.q1[t]  # time index is what has happened up until t == [number]
        else:
            return model.v_res1[t] == model.v_res1[t-1] + model.IF_1 - model.q1[t]
    model.constr_math_v_res1 = pyo.Constraint(model.T1, rule=math_v_res1)

    def math_v_res2(model, t, s):  # water reservoir = init volume + inflow - discharge
        if t == 25:
            return model.v_res2[t, s] == model.v_res1[24] + (model.IF_2 * s) - model.q2[t, s]
        else:
            return model.v_res2[t, s] == model.v_res2[(t-1), s] + (model.IF_2 * s) - model.q2[t, s]
    model.constr_math_v_res2 = pyo.Constraint(model.T2, model.S, rule=math_v_res2)

    # TODO: Oppg C = Endre på ting og si fra hva jeg endret

    # ---------- Solver and solving the problem ----------
    opt = SolverFactory('gurobi')
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(model)
    results = opt.solve(model, load_solutions=True)

    model.OBJ.display()
    model.v_res1.display()
    model.v_res2.display()
    # model.q1.display()
    # model.p1.display()
    # model.q2.display()
    # model.p2.display()
    #model.display()
    #model.dual.display()

