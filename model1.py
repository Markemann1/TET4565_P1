import pyomo.environ as pyo
from pyomo.opt import SolverFactory


def task1_model():
    # Set data
    T1 = list(range(1, 25))     # Hour 1-24
    T2 = list(range(25, 49))    # Hour 25-48
    S = list(range(0, 4))       # Scenario 0-4

    # Parameters data
    MP = 50                 # Start-value of market price
    WV_end = 13000          # EUR/Mm^3
    prob = 0.2              # 1/5 pr scenario
    Q_max = 0.36            # Mm^3
    P_max = 100             # MW
    E_conv = 0.000000981    # MWh/Mm^3
    V_max = 10              # Mm^3
    IF_1 = 0.18             # Mm^3/h, Inflow Stage 1
    IF_2 = 0.09             # Mm^3/h, Inflow Stage 2
    V_01 = 5                # Mm^3, initial water level, Stage 1

    model = pyo.ConcreteModel('Task 1b')

    # ---------- Declaring sets ----------
    model.T1 = pyo.Set(initialize=T1)   # First 24 hours, t
    model.T2 = pyo.Set(initialize=T2)   # Last 24 hours, t
    model.S = pyo.Set(initialize=S)     # Scenarios, s

    # ---------- Declaring parameters ----------
    model.MP = pyo.Param(model.T, initialize=MP)        # Market price at t
    model.WV = pyo.Param(initialize=WV_end)             # Water value at t = 48
    model.Prob = pyo.Param(initialize=prob)             # Probability of scenario
    model.Q_max = pyo.Param(initialize=Q_max)           # Max discharge of water to hydropower unit
    model.P_max = pyo.Param(initialize=P_max)           # Max power production of hydropower unit
    model.E_conv = pyo.Param(initialize=E_conv)         # Conversion of power, p, produced pr. discarged water, q
    model.V_max = pyo.Param(initialize=V_max)           # Max water capacity in reservoir
    model.IF_1 = pyo.Param(model.T, initialize=IF_1)    # Inflow in stage 1, deterministic
    model.IF_2 = pyo.Param(model.S, initialize=IF_2)    # Inflow in stage 2, stochastic
    model.V_01 = pyo.Param(model.T, initialize=V_01)    # Initial water level t = 1

    # ---------- Declaring decision variables ----------
    model.q1 = pyo.Var(model.T1, bounds=(0, Q_max))
    model.p1 = pyo.Var(model.T1, bounds=(0, P_max))
    model.v_res1 = pyo.Var(model.T1, bounds=(0, V_max))

    model.q2 = pyo.Var(model.T2, model.S, bounds=(0, Q_max))
    model.p2 = pyo.Var(model.T2, model.S, bounds=(0, P_max))
    model.v_res2 = pyo.Var(model.T2, model.S, bounds=(0, V_max))

    # ---------- Objective function ----------
    def objective(model):
        o1 = sum(model.p1[t] * (model.MP + t) for t in model.T1)  # t=(1,24) production * market price
        o2 = sum(model.Prob * model.p2[t][s] * (model.MP[t] + t) for t in model.T2 for s in model.S)  # t=(25,48) scenario probability * production(s) * market price
        o3 = sum(model.WV * model.v_res2[48][s] for s in model.S)  # t=48 reservoir level * water value
        obj = o1 + o2 + o3  # summing all profits
        return obj
    model.OBJ = pyo.Objective(rule=objective(model), sense=pyo.maximize)

    # ---------- Declaring constraints ----------
    def math_production1(model):  # production = water discharge * power equivalent
        return sum(model.p1[t] == model.q1[t] * model.E_conv for t in model.T1)
    model.constr_productionDependency1 = pyo.Constraint(rule=math_production1)

    def math_production2(model):  # production = water discharge * power equivalent
        return sum(model.p2[t] == model.q2[t] * model.E_conv for t in model.T2)
    model.constr_productionDependency2 = pyo.Constraint(rule=math_production2)

    def math_v_res1(model):  # water reservoir = init volume + inflow - discharge # TODO: Hvordan legge inn V0 = 5 i første t
        return sum(model.v_res1[t] == model.V01[1] + model.IF_1 - model.q1[t] for t in model.T1)
    model.constr_math_v_res1 = pyo.Constraint(rule=math_v_res1)

    def math_v_res2(model):  # water reservoir = init volume + inflow - discharge # TODO: Hvordan legge inn v_res[24] = ? i første t
        return sum(model.v_res2[t] == model.v_res1[24] + (model.IF_2 * s) - model.q2[t][s] for t in model.T2 for s in model.S)
    model.constr_math_v_res2 = pyo.Constraint(rule=math_v_res2)

    # TODO: Oppg C = Endre på ting og si fra hva jeg endret

    # ---------- Solver and solving the problem ----------
    opt = SolverFactory('Gurobi')
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(model)
    results = opt.solve(model, load_solutions=True)

    model.display()
    model.dual.display()


task1_model()
