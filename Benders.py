import pyomo.environ as pyo
from pyomo.opt import SolverFactory
import matplotlib.pyplot as plt


def masterProblem(dict_of_cuts):
    """
    The master problem aka the first 24 hours of the optimization problem, and the part of the problem that
    has the deterministic input, and a "dummy variable"-alpha, to represent the subproblem solution.

    The solution to this part of the overall problem returns the complicating variable v_res[24],
    and contains the optimal solution to the complete optimization problem
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

    resultat = [] #Plotting av graf
    for x in T1:
        y = mastermodel.v_res1[x].value
        resultat.append(y)

    plt.plot(T1, resultat)

    return mastermodel.v_res1[24].value


def subProblem(v_res_t24, num_scenario,LS_0, LS_1, LS_2, LS_3, LS_4): #TODO Liste i liste?
    """
    The sub-problem aka the last 24 hours of the optimization problem, and the part of the problem that
    contains the stochastic input.
    The solution to this part of the problem provides the data to generate cuts and solve the entire problem
    through the Master problem with the applied cuts.
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
    modelSub.v_res_t24 = pyo.Param(initialize=v_res_t24)      # value of v_res is in t=24 from the master problem solve

    # ---------- Declaring decision variables ----------
    modelSub.q2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, Q_max))       # variable of discharged water from reservoir in T2 pr. scenario
    modelSub.p2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, P_max))       # variable for production of power in T2 pr. scenario
    modelSub.v_res2 = pyo.Var(modelSub.T2, modelSub.S, bounds=(0, V_max))   # variable for reservoir level in T2 pr. scenario
    modelSub.v_res_t24_var = pyo.Var(bounds=(0, V_max))                     # complicating variable, v_res[24] from the master problem

    # ---------- Objective function ----------
    def objective(modelSub):
        if num_scenario == 1:
            o2 = sum(sum(modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in
                     modelSub.S)  # profits for T2 for rach scenario * probability
            o3 = sum(modelSub.WV * modelSub.v_res2[48, s] for s in
                     modelSub.S)  # profits from Water Value * remaining reservoir level at the end of day 2
            obj = o2 + o3  # summing all profit areas
            return obj

        else:
            o2 = sum(sum(modelSub.Prob * modelSub.p2[t, s] * (modelSub.MP + t) for t in modelSub.T2) for s in
                     modelSub.S)  # profits for T2 for rach scenario * probability
            o3 = modelSub.Prob * sum(
                modelSub.WV * modelSub.v_res2[48, s] for s in
                modelSub.S)  # profits from Water Value * remaining reservoir level at the end of day 2
            obj = o2 + o3  # summing all profit areas
            return obj
    modelSub.OBJ = pyo.Objective(rule=objective(modelSub), sense=pyo.maximize)  # setting the objective to maximize profits

    # ---------- Declaring constraints ----------
    def math_production2(modelSub, t, s):  # variable dependency for production in T2 over all scenarios, S
        return modelSub.p2[t, s] == modelSub.q2[t, s] * modelSub.E_conv  # production = water discharge * power equivalent
    modelSub.constr_productionDependency2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_production2)
    
    def math_v_res2(modelSub, t, s):  # variable dependency for production in T2
        if t == 25:     # setting the start value of water reservoir at the start of day 2
            return modelSub.v_res2[t, s] == modelSub.v_res_t24_var + (modelSub.IF_2 * s) - modelSub.q2[t, s]  # water reservoir = initial volume + inflow - discharge
        else:  # for the rest of time in T2
            return modelSub.v_res2[t, s] == modelSub.v_res2[(t-1), s] + (modelSub.IF_2 * s) - modelSub.q2[t, s]  # water reservoir = previous water level + inflow - discharge
    modelSub.constr_math_v_res2 = pyo.Constraint(modelSub.T2, modelSub.S, rule=math_v_res2)

    def v_res_start(modelSub):  # constraint to explain the v_res relationship in t = 24 so we can get the dual value
        return modelSub.v_res_t24_var == modelSub.v_res_t24
    modelSub.constr_dualvalue = pyo.Constraint(rule=v_res_start)

    # ---------- Initializing solver and solving the problem ----------
    opt = SolverFactory('gurobi')
    modelSub.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    opt.solve(modelSub)
    results = opt.solve(modelSub, load_solutions=True)

    obj_value = modelSub.OBJ()
    dual_value = modelSub.dual.get(modelSub.constr_dualvalue)

    """s1_plot = [] # TODO Varshan
    s2_plot = []
    s3_plot = []
    s4_plot = []
    s0_plot = []

    print("Her kommer resultatene du vil skrive ut:", modelSub.v_res2[25,1].value ) #todo denne skal fjernes når test er ferdig.

    for x_2 in range(25, 49):
        y_0 = modelSub.v_res2[(x_2, 0)].value
        s0_plot.append(y_0)
        LS_0.append(y_0)

        y_1 = modelSub.v_res2[(x_2, 1)].value
        s1_plot.append(y_1)
        LS_1.append(y_1)

        y_2 = modelSub.v_res2[(x_2, 2)].value
        s2_plot.append(y_2)
        LS_2.append(y_2)

        y_3 = modelSub.v_res2[(x_2, 3)].value
        s3_plot.append(y_3)
        LS_3.append(y_3)

        y_4 = modelSub.v_res2[(x_2, 4)].value
        s4_plot.append(y_4)
        LS_4.append(y_4)

    #print(s0_plot, s1_plot, s2_plot, s3_plot, s4_plot)

    plt.plot(T2,s0_plot,  color="blue")
    plt.plot(T2, s1_plot,  color="pink")
    plt.plot(T2, s2_plot, color="green")
    plt.plot(T2, s3_plot, color = "cyan")
    plt.plot(T2, s4_plot, color = "red")"""

    return obj_value, dual_value


def generate_cuts(OBJ, dual, v_res1, it, dict_of_cuts):
    """
        Function to generate linear cuts and add them to the cut dictionary to be put into the master problem
    """
    b = OBJ - dual * v_res1         # calculating value 'b' for the linear function
    cut = {'a': dual, 'b': b}
    dict_of_cuts[it] = cut

    print("Her er det du trenger nå varshan : " , v_res1)


def Benders_loop():
    num_scenario = 5  # oppgave b
    dict_of_cuts = {}
    LS_0 = []
    LS_1 = []
    LS_2 = []
    LS_3 = []
    LS_4 = []
    T2 = list(range(25,49))
    testavcut = []


    iteration = 0
    for iteration in range(1, 10):

        print('entering master')
        v_res1_t24 = masterProblem(dict_of_cuts)
        print(f'master returned {v_res1_t24}')

        print('entering sub')
        OBJ, Dual = subProblem(v_res1_t24, num_scenario,LS_0,LS_1, LS_2, LS_3, LS_4)
        print(f'sub returned OBJ = {OBJ} and Dual = {Dual}')

        print('entering generate cuts')
        generate_cuts(OBJ, Dual, v_res1_t24, iteration, dict_of_cuts)
        print(f' Dual/a, b Vres/x = {dict_of_cuts[iteration]}')

        alfa = dict_of_cuts[iteration]
        testavcut.append(alfa)
        print(v_res1_t24, "Varshan tester")

    #Dette blir kaos
        y_plot = []
        x_plot = []
        a_plot = [0, 21784.0, 13000.0, 16738.0, 16847.0, 16847.0, 16847.0, 16847.0, 16847.0, 16847.0]
        b_plot = [0, 105437.88, 147495.6, 120158.46, 119648.34, 119648.34, 119648.34, 119648.34, 119648.34, 119648.34]
        x_v_res = [0,1,2,3,4,5,6,7,8,9,10]
        for beta in range(0,9):
            if iteration == 2 or iteration == 3 or iteration == 4 or iteration == 5 or iteration == 6 or iteration == 7 or iteration == 8 or iteration == 9 or iteration == 10:
                y_plot_beregn = float(a_plot[beta]) * x_v_res[beta] + float(b_plot[beta])
                y_plot.append(y_plot_beregn)
                x_plot.append(x_v_res[beta])
        print(x_plot)
        print(y_plot)
        plt.plot(x_plot,y_plot)

    #Kode for å printe ut cuts



    #Kode for å printe ut no greier
    """print("Her er tabell med L0!", LS_0)
    print("Her er tabell med L1!", LS_1)
    print("Her er tabell med L2!", LS_2)
    print("Her er tabell med L3!", LS_3)
    print("Her er tabell med L4!", LS_4)

    plt.plot(T2, LS_0[-24:], color="blue")
    plt.plot(T2, LS_1[-24:], color="pink")
    plt.plot(T2, LS_2[-24:], color="green")
    plt.plot(T2, LS_3[-24:], color="cyan")
    plt.plot(T2, LS_4[-24:], color="red")
        # if dict_of_cuts[iteration]['a'] == dict_of_cuts[iteration-1]['a'] and dict_of_cuts[iteration]['b'] == dict_of_cuts[iteration-1]['b']:
        #     print('Getting repeating cuts')  # todo: kan exite loopen her, tror koden funker."""
    # plotting av graf under
    plt.title("Oppgave 2")
    plt.xlabel("Time")
    plt.ylabel("Water value")
    plt.grid(
        linestyle = '--'
             )
plt.show()
