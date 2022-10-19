import pyomo.environ as pyo
from pyomo.opt import SolverFactory

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

