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
    V_02 = 0                # Mm^3initial water level, Stage 2

    model = pyo.ConcreteModel('Task 1b')

    # Declaring sets
    model.T1 = pyo.Set(initialize=T1)   # First 24 hours, t
    model.T2 = pyo.Set(initialize=T2)   # Last 24 hours, t
    model.S = pyo.Set(initialize=S)     # Scenarios, s

    # Declaring parameters
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
    model.V_02 = pyo.Param(model.T, initialize=V_02)    # Initial water level t = 24  # TODO: mulig fjerne, eller constr?

    # Declaring decision variables
    model.q1 = pyo.Var(model.T1, bounds=(0, Q_max))
    model.p1 = pyo.Var(model.T1, bounds=(0, P_max))
    model.v_res1 = pyo.Var(model.T1, bounds=(0, V_max))

    model.q2 = pyo.Var(model.T2, model.S, bounds=(0, Q_max))
    model.p2 = pyo.Var(model.T2, model.S, bounds=(0, P_max))
    model.v_res2 = pyo.Var(model.T2, model.S, bounds=(0, V_max))

    def objective(model):
        o1 = sum(model.p1[t] * (model.MP + t) for t in model.T1)
        o2 = sum(model.Prob * model.p2[t][s] * (model.MP[t] + t) for t in model.T2 for s in model.S)
        o3 = sum(model.WV * model.v_res2[48][s] for s in model.S)
        obj = o1 + o2 + o3
        return obj
    model.OBJ = pyo.Objective(rule=objective(model), sense=pyo.maximize)

    def math_production1(model):
        return sum(model.p1[t] == model.q1[t] * model.E_conv for t in model.T1)
    model.constr_productionDependency1 = pyo.Constraint(rule=math_production1)

    def math_production2(model):
        return sum(model.p2[t] == model.q2[t] * model.E_conv for t in model.T2)
    model.constr_productionDependency2 = pyo.Constraint(rule=math_production2)

    def math_v_res1(model):  # TODO: Hvordan legge inn V0 = 5 i første t
        return sum(model.v_res1[t] == model.V01[1] + model.IF_1 - model.q1[t] for t in model.T1)
    model.constr_math_v_res1 = pyo.Constraint(rule=math_v_res1)

    def math_v_res2(model):  # TODO: Hvordan legge inn v_res[24] = ? i første t
        return sum(model.v_res2[t] == model.v_res1[24] + (model.IF_2 * s) - model.q2[t][s] for t in model.T2 for s in model.S)
    model.constr_math_v_res2 = pyo.Constraint(rule=math_v_res2)

    # Declaring constraints
    def productionLimit1(model):  # We cannot produce more than P_max
        return sum(model.p1[i] <= model.P_max for i in model.T)
    model.productionLimit1_constr = pyo.Constraint(rule=productionLimit1)

    def productionLimit2(model):  # Still cannot produce more than P_max
        return sum(model.p2[i][j] <= model.P_max for i in model.T for j in model.S)
    model.productionLimit2_constr = pyo.Constraint(rule=productionLimit2)

    def dischargeLimit1(model):  # We cannot discharge more water than Q_max
        return sum(model.q1[i] <= model.Q_max for i in model.T)
    model.dischargeLimit1_constr = pyo.Constraint(rule=dischargeLimit1)

    def dischargeLimit2(model):  # We cannot discharge more water than Q_max
        return sum(model.q2[i][j] <= model.P_max for i in model.T for j in model.S)
    model.dischargeLimit2_constr = pyo.Constraint(rule=dischargeLimit2)

    def reservoirLimit1(model):  # The water level cannot exceed V_max
        return sum(model.v_res1[i] <= model.V_max for i in model.T)
    model.reservoirLimit1_constr = pyo.Constraint(rule=reservoirLimit1)

    def reservoirLimit2(model):  # The water level cannot exceed V_max
        sum(model.v_res2[i][j] <= model.V_max for i in model.T for j in model.S)
    model.reservoirLimit2_constr = pyo.Constraint(rule=reservoirLimit2)

    # TODO: Oppg C = Endre på ting og si fra hva jeg endret

    # Solver and solving the problem
    opt = SolverFactory('Gurobi')
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(model)
    # results = opt.solve(model, load_solutions=True)

    model.display()
    model.dual.display()

