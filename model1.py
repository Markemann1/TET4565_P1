import pyomo.environ as pyo
from pyomo.opt import SolverFactory


def task1_model():
    # Sets data
    T = list(range(1, 49))  # t = {1, 48}
    S = list(range(1, 6))  # s = {1, 5}

    # Parameters data
    MP_t = 50 + T(i)  # TODO: Hvordan får man denne til å telle fremover?
    WV_end = 13000  # EUR/Mm^3
    prob = 0.2  # 1/5 pr scenario
    Q_max = 0.36  # Mm^3
    P_max = 100  # MW
    E_conv = 0.000000981  # MWh/Mm^3
    V_max = 10  # Mm^3
    IF_1 = 0.18  #Mm^3/h, Inflow Stage 1
    IF_2 = 0.09 * S(j) - 0.09  # Mm^3/h, Inflow Stage 2  # TODO: Hvordan får man denne til å telle gjennom
    V_01 = 5  # Mm^3, initial water level, Stage 1
    V_02 = v_res1[24]  # Mm^3initial water level, Stage 2  # TODO: dafuq gjør man her

    model = pyo.ConcreteModel('Task 1b')

    # Declaring sets
    model.T = pyo.Set(initialize=T)  # Time, t, hours
    model.S = pyo.Set(initialize=S)  # Scenarios, s

    # Declaring parameters
    model.MP = pyo.Param(model.T, initialize=MP_t)  # Market price at t
    model.WV = pyo.Param(model.T, model.S, initialize=WV_end)  # Water value at t = 48
    model.Prob = pyo.Param(model.S, initialize=prob)  # Probability of scenario
    model.Q_max = pyo.Param(initialize=Q_max)  # Max discharge of water to hydropower unit
    model.P_max = pyo.Param(initialize=P_max)  # Max power production of hydropower unit
    model.E_conv = pyo.Param(initialize=E_conv)  # Conversion of power, p, produced pr. discarged water, q
    model.V_max = pyo.Param(initialize=V_max)  # Max water capacity in reservoir
    model.IF_1 = pyo.Param(initialize=IF_1)  # Inflow in stage 1, deterministic
    model.IF_2 = pyo.Param(model.S, initialize=IF_2)  # Inflow in stage 2, stochastic
    model.V_01 = pyo.Param(model.T, initialize=V_01)  # Initial water level t = 1
    model.V_02 = pyo.Param(model.T, initialize=V_02)  # Initial water level t = 24

    # Declaring decision variables
    model.q1 = pyo.Var(model.T, within=pyo.NonNegativeReals)
    model.v_res1 = pyo.Var(model.T, model.V_01 + model.IF_1 - model.q1, within=pyo.NonNegativeReals)
    model.p1 = pyo.Var(model.T, model.q1 * model.E_conv, within=pyo.NonNegativeReals)

    model.q2 = pyo.Var(model.T, model.S, within=pyo.NonNegativeReals)
    model.v_res2 = pyo.Var(model.T, model.S, model.V_02 + model.IF_2 - model.q2, within=pyo.NonNegativeReals)
    model.p2 = pyo.Var(model.T, model.S, model.q2 * model.E_conv, within=pyo.NonNegativeReals)

    # Objective function
    def objective(model):  # TODO: Hvordan skille T1 og T2, for dette må jo være feil måte å gjøre det på
        return sum(model.p1[i] * model.MP[i] for i in model.T[1 - 24]) + sum((model.Prob[j]) * sum(
            model.p2[i][j] * model.MP[i] + model.WV * model.v_res2[i][j] for i in model.T[25-48]) for j in model.S)

    model.OBJ = pyo.Objective(rule=objective(model), sense=pyo.maximize)

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

    # Solver and solving the problem
    opt = SolverFactory('Gurobi')
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(model)
    # results = opt.solve(model, load_solutions=True)

    model.display()
    model.dual.display()

