import pyomo.environ as pyo
from pyomo.opt import SolverFactory

"""
cuts_dict = {}  # dict i dict: cut 0: {'slope':(a), 'constant':(b)} for alle cuts

modelSub = pyo.ConcreteModel()

modelSub.Alpha = pyo.Var()

modelSub.Cuts = pyo.Set(initialize=List_of_cuts)  # må være en liste m/antall så den vet hvor mange
modelSub.Cuts.display()

modelSub.cuts_dict = cuts_dict

def constraint_cuts(modelSub, cut):
    # sjekk og print ogsånt
    print(modelSub.cut_dict[cut]['Slope'], modelSub.cut_dict[cut]['Constant'])
    print(f'creating cut: {cut}')
    return modelSub.Alpha == 2
modelSub.cut_constraint = pyo.Constraint(modelSub.Cuts, rule = constraint_cuts)  # Kan kjøre pyo.Constraint(modelSub.Cuts, modelSub.Cuts [...]

# --- Funksjon "generate cuts" --- denne er fejjjl
List_of_cuts.append(iteration)
cuts_dict[iteration] = {}
cuts_dict[iteration]['Slope'] = 30*iteration
cuts_dict[iteration]['Constraint'] = 700-iteration
"""
# ^ Noe notater fra Q&A timen ^


# Set data
T1 = list(range(1, 25))  # Hour 1-24
T2 = list(range(25, 49))  # Hour 25-48
S = list(range(0, 5))  # Scenario 0-4

# Parameters data
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

# Useful dictionaries
# v_res1_data = {}
# Cuts_data = {}
# Premilimanry_results = {}

def masterProblem(dict_of_cuts):
    # Set data
    T1 = list(range(1, 25))  # Hour 1-24
    T2 = list(range(25, 49))  # Hour 25-48
    S = list(range(0, 5))  # Scenario 0-4

    # Parameters data
    M3S_TO_MM3 = 3.6 / 1000  # Convesion factor to MM^3
    MP = 50  # Start-value of market price
    Q_max = 100 * M3S_TO_MM3  # Mm^3
    P_max = 100  # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
    V_max = 10  # Mm^3
    IF_1 = 50 * M3S_TO_MM3  # Mm^3/h, Inflow Stage 1
    V_01 = 5  # Mm^3, initial water level, Stage 1

    # Useful dictionaries

    v_res1_data = {}
    Cuts_data = {}
    Premilimanry_results = {}

    # -------- Initiate masterproblem -------------
    mastermodel = pyo.ConcreteModel()

    # -------- Declaring sets ---------------------
    mastermodel.T1 = pyo.Set(initialize=T1)
    # mastermodel.Cuts = pyo.Set(initialize=dict_of_cuts)
    mastermodel.dict_of_cuts = dict_of_cuts

    # -------- Declaring parameters ---------------
    mastermodel.MP = pyo.Param(initialize=MP)
    mastermodel.Q_max = pyo.Param(initialize=Q_max)  # Max discharge of water to hydropower unit
    mastermodel.P_max = pyo.Param(initialize=P_max)  # Max power production of hydropower unit
    mastermodel.E_conv = pyo.Param(initialize=E_conv)  # Conversion of power, p, produced pr. discarged water, q
    mastermodel.V_max = pyo.Param(initialize=V_max)  # Max water capacity in reservoir
    mastermodel.IF_1 = pyo.Param(initialize=IF_1)
    mastermodel.V_01 = pyo.Param(initialize=V_01)

    # -------- Declaring decision variables -------
    mastermodel.alpha = pyo.Var(bounds=(-1000000, 1000000))
    mastermodel.q1 = pyo.Var(mastermodel.T1, bounds=(0, Q_max))
    mastermodel.p1 = pyo.Var(mastermodel.T1, bounds=(0, P_max))
    mastermodel.v_res1 = pyo.Var(mastermodel.T1, bounds=(0, V_max), initialize=mastermodel.V_01)


    # -------- Declaring Objective function --------
    def objective(mastermodel):
        obj = sum(mastermodel.p1[t] * (mastermodel.MP + t) for t in mastermodel.T1) + mastermodel.alpha  # t=(1,24) production * market price

        return obj
    mastermodel.OBJ = pyo.Objective(rule=objective(mastermodel), sense=pyo.maximize )

    # -------- Declaring constraints ---------------
    def math_production1(mastermodel, t):  # production = water discharge * power equivalent
        return mastermodel.p1[t] == mastermodel.q1[t] * mastermodel.E_conv
    mastermodel.constr_productionDependency1 = pyo.Constraint(mastermodel.T1, rule=math_production1)

    def math_v_res1(mastermodel, t):  # water reservoir = init volume + inflow - discharge
        if t == 1:
            return mastermodel.v_res1[t] == mastermodel.V_01 + mastermodel.IF_1 - mastermodel.q1[
                t]  # time index is what has happened up until t == [number]
        else:
            return mastermodel.v_res1[t] == mastermodel.v_res1[t - 1] + mastermodel.IF_1 - mastermodel.q1[t]
    mastermodel.constr_math_v_res1 = pyo.Constraint(mastermodel.T1, rule=math_v_res1)



    # TODO: Må fikse constriant som legger inn cuts
    mastermodel.listOfCuts = pyo.ConstraintList()
    it = 0
    for cut in range(len(dict_of_cuts)):  # todo: skal telle gjennom antall keys i dict of cuts
        it += 1
        mastermodel.listOfCuts.add(mastermodel.alpha <= mastermodel.dict_of_cuts[it]['a']*mastermodel.v_res1[24] + mastermodel.dict_of_cuts[it]['b'])



    # TODO : Løse masterproblem og returnere rervoirnivå t=24

    opt = SolverFactory('gurobi')
    mastermodel.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(mastermodel)
    results = opt.solve(mastermodel, load_solutions=True)
    mastermodel.display()
    return mastermodel.v_res1[24].value

def subProblem(v_res_t24, num_scenario):

    # ---------- Set data ----------
    T2 = list(range(25, 49))  # Hour 25-48
    if num_scenario == 1:
        S = 3
    else:
        S = list(range(0, 5))  # Scenario 0-4
    
    # ---------- Parameters data ----------
    M3S_TO_MM3 = 3.6 / 1000  # Convesion factor to MM^3
    MP = 50  # Start-value of market price
    WV_end = 13000  # EUR/Mm^3
    prob = 0.2  # 1/5 pr scenario
    Q_max = 100 * M3S_TO_MM3  # Mm^3
    P_max = 100  # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
    V_max = 10  # Mm^3
    IF_2 = 25 * M3S_TO_MM3  # Mm^3/h, Inflow Stage 2

    modelSub = pyo.ConcreteModel()

    # ---------- Declaring sets ----------
    modelSub.T2 = pyo.Set(initialize=T2)  # Last 24 hours, t
    modelSub.S = pyo.Set(initialize=S)  # Scenarios, s

    # ---------- Declaring parameters ----------
    modelSub.MP = pyo.Param(initialize=MP)                 # Market price at t
    modelSub.WV = pyo.Param(initialize=WV_end)             # Water value at t = 48
    modelSub.Prob = pyo.Param(initialize=prob)             # Probability of scenario
    modelSub.Q_max = pyo.Param(initialize=Q_max)           # Max discharge of water to hydropower unit
    modelSub.P_max = pyo.Param(initialize=P_max)           # Max power production of hydropower unit
    modelSub.E_conv = pyo.Param(initialize=E_conv)         # Conversion of power, p, produced pr. discarged water, q
    modelSub.V_max = pyo.Param(initialize=V_max)           # Max water capacity in reservoir
    modelSub.IF_2 = pyo.Param(initialize=IF_2)             # Inflow in stage 2, stochastic
    modelSub.v_res_t24 = pyo.Param(initialize=v_res_t24)

    # ---------- Declaring decision variables ----------
    modelSub.q2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, Q_max))
    modelSub.p2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, P_max))
    modelSub.v_res2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, V_max))
    modelSub.v_res_t24var = pyo.Var(bounds=(0, V_max))

    # ---------- Objective function ----------
    def objective(modelSub):
        o2 = sum(sum(modelSub.Prob * modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in modelSub.S)  # t=(25,48) scenario probability * production(s) * market price
        o3 = modelSub.Prob * sum(modelSub.WV * modelSub.v_res2[48, s] for s in modelSub.S)  # t=48 reservoir level * water value
        obj = o2 + o3
        return obj
    modelSub.OBJ = pyo.Objective(rule=objective(modelSub), sense=pyo.maximize)

    # ---------- Constraints ----------
    def math_production2(modelSub, t, s):  # production = water discharge * power equivalent
        return modelSub.p2[t, s] == modelSub.q2[t, s] * modelSub.E_conv
    modelSub.constr_productionDependency2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_production2)
    
    def math_v_res2(modelSub, t, s):  # water reservoir = init volume + inflow - discharge
        if t == 25:
            return modelSub.v_res2[t, s] == modelSub.v_res_t24 + (modelSub.IF_2 * s) - modelSub.q2[t, s]
        else:
            return modelSub.v_res2[t, s] == modelSub.v_res2[(t-1), s] + (modelSub.IF_2 * s) - modelSub.q2[t, s]
    modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_v_res2)

    def v_res_start(modelSub, t):  #, t, s
        if t == 24:  # todo: Her erre noe feil for fan
            return modelSub.v_res_t24var == modelSub.v_res_t24
        modelSub.constr_dualvalue = pyo.Constraint(rule=v_res_start)
        #     return modelSub.v_res2[t, s] == modelSub.v_res_t24 + (modelSub.IF_2 * s) - modelSub.q2[t, s]
        # modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=v_res_start)

    opt = SolverFactory('gurobi')
    modelSub.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(modelSub)
    results = opt.solve(modelSub, load_solutions=True)

    return modelSub.OBJ, modelSub.dual[v_res_start(modelSub, 1).value]  # todo: fikse constrainten og blæ


def generate_cuts(OBJ, dual, v_res1, it, dict_of_cuts):

    b = OBJ - dual * v_res1
    cut = {it: {'a': dual, 'b': b}}  # 'x': v_res1: trenger ikke
    dict_of_cuts.append(cut)


def Benders_loop():
    num_scenario = 4  # oppgave b
    dict_of_cuts = {}
    iteration = 0
    for iteration in range(1, 10):

        print('entering master')
        v_res1_t24 = masterProblem(dict_of_cuts)
        print(f'master returned {v_res1_t24}')

        print('entering sub')
        OBJ, Dual = subProblem(v_res1_t24, num_scenario)
        print(f'sub returned OBJ = {OBJ} and Dual = {Dual}')

        print('entering generate cuts')
        generate_cuts(OBJ, Dual, v_res1_t24, iteration, dict_of_cuts)
        print(f' Dual/a, b, Vres/x = {dict_of_cuts[iteration]}')




