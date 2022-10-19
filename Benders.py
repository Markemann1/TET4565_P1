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


