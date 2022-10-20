import pyomo.environ as pyo
from pyomo.opt import SolverFactory

"""
cuts_dict = {}  # dict i dict: cut 0: {'slope':(a), 'constant':(b)} for alle cuts

model = pyo.ConcreteModel()

model.Alpha = pyo.Var()

model.Cuts = pyo.Set(initialize=List_of_cuts)  # må være en liste m/antall så den vet hvor mange
model.Cuts.display()

model.cuts_dict = cuts_dict

def constraint_cuts(model, cut):
    # sjekk og print ogsånt
    print(model.cut_dict[cut]['Slope'], model.cut_dict[cut]['Constant'])
    print(f'creating cut: {cut}')
    return model.Alpha == 2
model.cut_constraint = pyo.Constraint(model.Cuts, rule = constraint_cuts)  # Kan kjøre pyo.Constraint(model.Cuts, model.Cuts [...]

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

#Useful dictionaries
v_res1_data = {}
Cuts_data = {}
Premilimanry_results = {}

def masterProblem(Cuts_data):
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

    # -------- Declaring parameters ---------------
    mastermodel.MP = pyo.Param(initialize=MP)
    mastermodel.Q_max = pyo.Param(initialize=Q_max)  # Max discharge of water to hydropower unit
    mastermodel.P_max = pyo.Param(initialize=P_max)  # Max power production of hydropower unit
    mastermodel.E_conv = pyo.Param(initialize=E_conv)  # Conversion of power, p, produced pr. discarged water, q
    mastermodel.V_max = pyo.Param(initialize=V_max)  # Max water capacity in reservoir
    mastermodel.IF_1 = pyo.Param(initialize=IF_1)
    mastermodel.V_01 = pyo.Param(initialize=V_01)

    # -------- Declaring decision variables -------
    mastermodel.alpha = pyo.Var(mastermodel.T1, bounds=(-1000000, 1000000))
    mastermodel.q1 = pyo.Var(mastermodel.T1, bounds=(0, Q_max))
    mastermodel.p1 = pyo.Var(mastermodel.T1, bounds=(0, P_max))
    mastermodel.v_res1 = pyo.Var(mastermodel.T1, bounds=(0, V_max), initialize=mastermodel.V_01)

    # -------- Declaring Objective function --------
    def objective(mastermodel):
        o1 = sum(mastermodel.p1[t] * (mastermodel.MP + t) for t in mastermodel.T1)  # t=(1,24) production * market price

        obj = o1 + mastermodel.alpha
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
    def alpha_cuts(mastermodel, ):
        return(mastermodel.alpha <= "obj + dual*(v_res - v_rest24) ")

    # TODO : Løse masterproblem og returnere rervoirnivå t=24
    "Solve problem and return reservoir level for t=24"
    return(v_res1(24))

def subProblem(v_res1(24)):
    "Declare sets"
    "Declare parameters"
    "Declare variables"
    "Objective function (Basically the same as task 1, without the first stage)"
    "Constraints for stage 1+2 (here we will use v_res1(24) from masterproblem as a parameter"
    "Solve Problem and return objective value and dual value for v_res1"
    return(OBJ, dual )


def generate_cuts(OBJ, dual, v_res1_24):
    "Make cut as a constraint for masterproblem"
    "cut = OBJ + dual*(v_res1_next_iteration_(24) - v_res1(24) ) "
    "Add/append cut to cuts_data"


def Benders_loop():

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


