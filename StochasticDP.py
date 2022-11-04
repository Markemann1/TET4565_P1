import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt


def masterProblem(dict_of_cuts):
    """
    The master problem aka the first 24 hours of the optimization problem, and the part of the problem that
    has the deterministic input, and a "dummy variable"-alpha, to represent the subproblem solution.

    The solution to this part of the problem provides the optimal solution to the complete optimization problem.
    """
    # Set data
    T1 = list(range(1, 25))      # Hour 1-24

    # Parameters data
    M3S_TO_MM3 = 3.6/1000        # Convesion factor to MM^3
    MP = 50                      # Start-value of market price
    Q_max = 100 * M3S_TO_MM3     # Mm^3
    P_max = 100                  # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
    V_max = 10                   # Mm^3
    IF_1 = 50 * M3S_TO_MM3       # Mm^3/h, Inflow Stage 1
    V_01 = 5                     # Mm^3, initial water level, Stage 1

    # -------- Initiate masterproblem -------------
    mastermodel = pyo.ConcreteModel()

    # -------- Declaring sets ---------------------
    mastermodel.T1 = pyo.Set(initialize=T1)
    mastermodel.dict_of_cuts = dict_of_cuts
    # -------- Declaring parameters ---------------
    mastermodel.MP = pyo.Param(initialize=MP)           # Market price at t
    mastermodel.Q_max = pyo.Param(initialize=Q_max)     # Max discharge of water to hydropower unit
    mastermodel.P_max = pyo.Param(initialize=P_max)     # Max power production of hydropower unit
    mastermodel.E_conv = pyo.Param(initialize=E_conv)   # Conversion of power, p, produced pr. discarged water, q
    mastermodel.V_max = pyo.Param(initialize=V_max)     # Max water capacity in reservoir
    mastermodel.IF_1 = pyo.Param(initialize=IF_1)       # Inflow in stage 1, deterministic
    mastermodel.V_01 = pyo.Param(initialize=V_01)       # Initial water level t = 1

    # -------- Declaring decision variables -------
    mastermodel.alpha = pyo.Var(bounds=(-1000000, 1000000))          # alpha is the masterproblem's substitute for the subproblem
    mastermodel.q1 = pyo.Var(mastermodel.T1, bounds=(0, Q_max))      # variable of discharged water from reservoir in T1
    mastermodel.p1 = pyo.Var(mastermodel.T1, bounds=(0, P_max))      # variable for production of power in T1
    mastermodel.v_res1 = pyo.Var(mastermodel.T1, bounds=(0, V_max))  # variable for reservoir level in T1

    # -------- Declaring Objective function --------
    def objective(mastermodel):
        obj = sum(mastermodel.p1[t] * (mastermodel.MP + t) for t in mastermodel.T1) + mastermodel.alpha
        return obj      # profits for T1 + the alpha "dummy variable"
    mastermodel.OBJ = pyo.Objective(rule=objective(mastermodel), sense=pyo.maximize)  # setting the objective to maximize profits

    # -------- Declaring constraints ---------------
    def math_production1(mastermodel, t):  # variable dependency for production in T1
        return mastermodel.p1[t] == mastermodel.q1[t] * mastermodel.E_conv  # production = water discharge * power equivalent
    mastermodel.constr_productionDependency1 = pyo.Constraint(mastermodel.T1, rule=math_production1)

    def math_v_res1(mastermodel, t):  # variable dependency for production in T1
        if t == 1:  # setting the start value of water reservoir at the start of day 1
            return mastermodel.v_res1[t] == mastermodel.V_01 + mastermodel.IF_1 - mastermodel.q1[t]  # water reservoir = initial volume + inflow - discharge
        else:  # for the rest of time in T1
            return mastermodel.v_res1[t] == mastermodel.v_res1[t - 1] + mastermodel.IF_1 - mastermodel.q1[t]  # water reservoir = previous water level + inflow - discharge
    mastermodel.constr_math_v_res1 = pyo.Constraint(mastermodel.T1, rule=math_v_res1)

    mastermodel.listOfCuts = pyo.ConstraintList()  # A constraint of a list of constraints based on cuts
    for cut in dict_of_cuts.keys():  # Going through all the keys in the cut dictionary generated in the SDP_loop
        mastermodel.listOfCuts.add(mastermodel.alpha <= mastermodel.dict_of_cuts[cut]['a'] * mastermodel.v_res1[24] + mastermodel.dict_of_cuts[cut]['b'])
        # adding the 'a' and 'b' value from dict_cuts to generate a "Y = ax + b" linear cut, where 'x' is the v_res1[24] complicating variable from this "next" iteration

    # ---------- Initializing solver and solving the problem ----------
    SolverFactory('gurobi').solve(mastermodel)
    # mastermodel.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

    obj_value = mastermodel.OBJ()
    print('Total objective', obj_value)

    # ---- Plotting av graf ----

    resultat = []  # Plotting av graf
    for x in T1:
        y = mastermodel.v_res1[x].value
        resultat.append(y)
    print(resultat)
    plt.plot(T1, resultat)


    print("jeg test printer noe: ", resultat) #todo må fjernes når jeg er ferdig .

    return mastermodel.v_res1[24].value


def subProblem(v_res_guess, num_scenario):
    """
    The sub-problem aka the last 24 hours of the optimization problem, and the part of the problem that
    contains the stochastic input.
    The solution to this part of the problem provides the data to generate cuts and solve the entire problem
    through the Master problem.
    """
    # ---------- Set data ----------
    T2 = list(range(25, 49))     # Hour 25-48
    if num_scenario == 1:        # for running only one scenario, num_scenario written in SDP_loop
        S = [2]                  # the scenario being run
    else:
        S = list(range(0, 5))    # if not one, we run all 5 scenario's 0-4

    # Parameters data
    M3S_TO_MM3 = 3.6/1000        # Convesion factor to MM^3
    MP = 50                      # Start-value of market price
    WV_end = 13000               # EUR/Mm^3
    prob = 0.2                   # 1/5 pr scenario
    Q_max = 100 * M3S_TO_MM3     # Mm^3
    P_max = 100                  # MW (over 1 hour)
    E_conv = 0.981 / M3S_TO_MM3  # MWh/Mm^3
    V_max = 10                   # Mm^3
    IF_2 = 25 * M3S_TO_MM3       # Mm^3/h, Inflow Stage 2

    modelSub = pyo.ConcreteModel()

    # ---------- Declaring sets ----------
    modelSub.T2 = pyo.Set(initialize=T2)        # Last 24 hours, t
    modelSub.S = pyo.Set(initialize=S)          # Scenarios, s

    # ---------- Declaring parameters ----------
    modelSub.MP = pyo.Param(initialize=MP)                    # Market price at t
    modelSub.WV = pyo.Param(initialize=WV_end)                # Water value at t = 48
    modelSub.Prob = pyo.Param(initialize=prob)                # Probability of scenario
    modelSub.Q_max = pyo.Param(initialize=Q_max)              # Max discharge of water to hydropower unit
    modelSub.P_max = pyo.Param(initialize=P_max)              # Max power production of hydropower unit
    modelSub.E_conv = pyo.Param(initialize=E_conv)            # Conversion of power, p, produced pr. discarged water, q
    modelSub.V_max = pyo.Param(initialize=V_max)              # Max water capacity in reservoir
    modelSub.IF_2 = pyo.Param(initialize=IF_2)                # Inflow in stage 2, stochastic
    modelSub.v_res_guess = pyo.Param(initialize=v_res_guess)  # Guess values of what v_res is in t=24

    # ---------- Declaring decision variables ----------
    modelSub.q2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, Q_max))       # variable of discharged water from reservoir in T2 pr. scenario
    modelSub.p2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, P_max))       # variable for production of power in T2 pr. scenario
    modelSub.v_res2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, V_max))   # variable for reservoir level in T2 pr. scenario
    modelSub.v_res_guess_var = pyo.Var(bounds=(0, V_max))                   # complicating variable, v_res[24], with the guesses

    # ---------- Objective function ----------
    def objective(modelSub):
        if num_scenario == 1:
            o2 = sum(sum(modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in
                     modelSub.S)  # profits for T2 for rach scenario * probability
            o3 = sum(modelSub.WV * modelSub.v_res2[48, s] for s in modelSub.S)  # profits from Water Value * remaining reservoir level at the end of day 2
            obj = o2 + o3  # summing all profit areas
            return obj

        else:
            o2 = sum(sum(modelSub.Prob * modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in
                     modelSub.S)    # profits for T2 for rach scenario * probability
            o3 = modelSub.Prob * sum(
                modelSub.WV * modelSub.v_res2[48, s] for s in modelSub.S)  # profits from Water Value * remaining reservoir level at the end of day 2
            obj = o2 + o3   # summing all profit areas
            return obj
    modelSub.OBJ = pyo.Objective(rule=objective(modelSub), sense=pyo.maximize)  # setting the objective to maximize profits

    # ---------- Declaring constraints ----------
    def math_production2(modelSub, t, s):  # variable dependency for production in T2 over all scenarios, S
        return modelSub.p2[t, s] == modelSub.q2[t, s] * modelSub.E_conv  # production = water discharge * power equivalent
    modelSub.constr_productionDependency2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_production2)

    def math_v_res2(modelSub, t, s):  # variable dependency for production in T2
        if t == 25:     # setting the start value of water reservoir at the start of day 2
            return modelSub.v_res2[t, s] == modelSub.v_res_guess_var + (modelSub.IF_2 * s) - modelSub.q2[t, s]  # water reservoir = initial volume + inflow - discharge
        else:   # for the rest of time in T2
            return modelSub.v_res2[t, s] == modelSub.v_res2[(t - 1), s] + (modelSub.IF_2 * s) - modelSub.q2[t, s]  # water reservoir = previous water level + inflow - discharge
    modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_v_res2)

    def v_res_start(modelSub):  # constraint to explain the v_res relationship in t = 24 so we can get the dual value
        return modelSub.v_res_guess_var == modelSub.v_res_guess
    modelSub.constr_dualvalue = pyo.Constraint(rule=v_res_start)

    # ---------- Initializing solver and solving the problem ----------
    opt = SolverFactory('gurobi')
    modelSub.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(modelSub)
    results = opt.solve(modelSub, load_solutions=True)

    obj_value = modelSub.OBJ()
    dual_value = modelSub.dual.get(modelSub.constr_dualvalue)

    '''
    print(" Jeg tester å skrive ut noe fra sub_:", modelSub.v_res2[25,0].value) #todo slett når ferdig med test

    s1_plot = []  # TODO Varshan
    s2_plot = []
    s3_plot = []
    s4_plot = []
    s0_plot = []

    print("Her kommer resultatene du vil skrive ut:",
          modelSub.v_res2[25, 1].value)  # todo denne kan fjernes når test er ferdig.

    for x_2 in range(25, 49):
        #y_0 = modelSub.v_res2[(x_2, 0)].value
        s0_plot.append(y_0)
        #LS_0.append(y_0)

        #y_1 = modelSub.v_res2[(x_2, 1)].value
        s1_plot.append(y_1)
        #LS_1.append(y_1)

        #y_2 = modelSub.v_res2[(x_2, 2)].value
        s2_plot.append(y_2)
        #LS_2.append(y_2)

        #y_3 = modelSub.v_res2[(x_2, 3)].value
        s3_plot.append(y_3)
        #LS_3.append(y_3)

        #y_4 = modelSub.v_res2[(x_2, 4)].value
        s4_plot.append(y_4)
        #LS_4.append(y_4)

#    print(f'Dette burde være tallene 's2_plot)

    #plt.plot(T2,s0_plot,  color="blue")
    #plt.plot(T2, s1_plot,  color="pink")
    #plt.plot(T2, s2_plot, color="green")
    #plt.plot(T2, s3_plot, color = "cyan")
    #plt.plot(T2, s4_plot, color = "red")
    plt.show()'''

    return obj_value, dual_value  # returning the OBJ and dual of v_res_start constraint to be used in cut generation


def generate_cuts(v_res_guess, OBJ, Dual, dict_of_cuts, iterator):
    """
    Function to generate linear cuts and add them to the cut dictionary to be put into the master problem
    """
    b = OBJ - Dual * v_res_guess        # calculating value 'b' for the linear function
    cut = {'a': Dual, 'b': b}  # 'x': v_res1: trenger ikke
    dict_of_cuts[iterator] = cut
    return


def SDP_loop():
    """
    The function to go through the Master- and Subproblem in accordance with
    the Stochastic Dynamic Programming method
    """
    list_of_guess = [1,2,3,4,5,6,7,8,9,10]     # for v_res value to be put into the Subproblem
    dict_of_cuts = {}                               # dictionary to keep the cuts
    iterator = 0                                    # to organize the dict cut keys
    num_scenario = 5                                # to set number of scenario's in the subproblem
    for guess in list_of_guess:
        print(f'Entering subproblem for the {guess} time')
        OBJ, Dual = subProblem(guess, num_scenario)     # getting the OBJ and dual from v_res guess-list

        print('Generating cuts')
        generate_cuts(guess, OBJ, Dual, dict_of_cuts, iterator)     # generating cuts from the subproblem values
        iterator += 1

    print('Entering masterproblem')
    masterProblem(dict_of_cuts)     # solving the master problem with the cuts generated
