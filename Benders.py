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

def masterProblem("noe input, og dict/list of cuts elns"):

    print("dette skal være et selvstendig optimeringsprogram")

    return "noe outputs som skal inn i subproblem"

def subProblem("noe input som kommer fra masterProblem()"):

    print("dette skal være et selvstendig optimeringsprogram")

    return "noe output vi trenger i masterproblem ++ for å generere cuts"


def generate_cuts("noe input fra subProblem() og en Xi fra masterProblem()"):


    return "trenger kanskje ikke returne noe. Skal appende det nye cuttet i liste av cuts"


def Benders_loop("tror ikke den trenger input"):
    "noe initialisering av list of cuts elns"

    for i in len(1,2,3,4,5,6,7,8,9):
        "returns som kommer fra master a, b, c" = masterProblem("input")


        Dual, OBJ = subProblem("problem init data", x_i)

        generate_cuts(Xi, d, e, f)

        print("noe greier så man kan se resultatene underveis")


