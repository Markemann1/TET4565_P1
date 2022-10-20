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
MP = 50  # Start-value of market price
WV_end = 13000  # EUR/Mm^3
prob = 0.2  # 1/5 pr scenario
Q_max = 0.36  # Mm^3
P_max = 100  # MW
E_conv = 0.000000981  # MWh/Mm^3
V_max = 10  # Mm^3
IF_1 = 0.18  # Mm^3/h, Inflow Stage 1
IF_2 = 0.09  # Mm^3/h, Inflow Stage 2
V_01 = 5  # Mm^3, initial water level, Stage 1

#Useful dictionaries
v_res1_data = {}
Cuts_data = {}
Premilimanry_results = {}

def masterProblem(Cuts_data):

    "Declare sets"
    "Declare parameters"
    "Declare variables (define alpha with constraints -1000000 til +1000000"
    "Objective function"
    "constraints for stage 1 (add cuts from Cuts_data)"
    "Solve problem and return reservoir level for t=24"
    return(v_res1(24))

def subProblem(v_res_t24, num_scenario):

    # Set data
    T2 = list(range(25, 49))  # Hour 25-48

    if num_scenario <= 1:
        S = 3
    else:
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
    IF_2 = 25 * M3S_TO_MM3  # Mm^3/h, Inflow Stage 2

    modelSub = pyo.ConcreteModel()

    # "Declare sets"
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
    modelSub.v_res2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, V_max), initialize=modelSub.v_res1[24])  # todo: må mulig fjernes

    # ---------- Objective function ----------
    def objective(modelSub):
        o2 = sum(sum(modelSub.Prob * modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in modelSub.S)  # t=(25,48) scenario probability * production(s) * market price
        o3 = modelSub.Prob * sum(modelSub.WV * modelSub.v_res2[48, s] for s in modelSub.S)  # t=48 reservoir level * water value
        obj = o2 + o3
        return obj
    modelSub.OBJ = pyo.Objective(rule=objective(modelSub), sense=pyo.maximize)
    
    def math_production2(modelSub, t, s):  # production = water discharge * power equivalent
        return modelSub.p2[t, s] == modelSub.q2[t, s] * modelSub.E_conv
    modelSub.constr_productionDependency2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_production2)
    
    def math_v_res2(modelSub, t, s):  # water reservoir = init volume + inflow - discharge
        if t == 25:
            return modelSub.v_res2[t, s] == modelSub.v_res_t24 + (modelSub.IF_2 * s) - modelSub.q2[t, s]
        else:
            return modelSub.v_res2[t, s] == modelSub.v_res2[(t-1), s] + (modelSub.IF_2 * s) - modelSub.q2[t, s]
    modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_v_res2)

    def v_res_start(modelSub, t, s):
        if t == 25:  # todo: må muligens legge inn en skip
            return modelSub.v_res2[t, s] == modelSub.v_res_t24 + (modelSub.IF_2 * s) - modelSub.q2[t, s]
        modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=v_res_start)

    opt = SolverFactory('gurobi')
    modelSub.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(modelSub)
    results = opt.solve(modelSub, load_solutions=True)

    return modelSub.OBJ, modelSub.dual[v_res_start]  # todo: usikker på om dette er sånn man tar ut dual verdien til en const


def generate_cuts(OBJ, dual, v_res1_24):
    "Make cut as a constraint for masterproblem"
    "cut = OBJ + dual*(v_res1_next_iteration_(24) - v_res1(24) ) "
    "Add/append cut to cuts_data"


def Benders_loop():
    scen = 1 # oppgave b
    for iteration in range(1,10):

        "Initiate masterproblem"
        v_res1_24 = masterProblem(Cuts_data)
        v_res1_data[iteration] = v_res1_24

        "Initiate subproblem"
        Premilimanry_results[iteration] = {}
        for scen in range(3):
            OBJ, Dual = subProblem(v_res1_24)
            print("OBJ, Dual:", OBJ, dual)
            Premilimanry_results[iteration][scen] = {"OBJ": OBJ, "Dual": dual, "v_res1": v_res1_24}

        "Create cuts"
        generate_cuts(OBJ, dual, v_res1_24)

        print("This is Cut (", iteration,")")


