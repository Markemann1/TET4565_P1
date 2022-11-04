---- How to run: ----
The following functions are the only one's required to run part 1, 2 and 3.
For testing the different a, b, [..] task of the parts, these are also the functions to change
*Part 1:
task1_model()
*Part 2:
Benders_loop()
*Part 3:
SDP_loop()

---- Packages: ----
- import pyomo.environ as pyo
- from pyomo.opt import SolverFactory
- import matplot.pyplot as plt


---- model1.py - File for solving Part 1: ----
* Functions:
- task1_model()
    The only function in Part 1, with the information and all to solve the optimization problem for hour 1-48


---- Benders.py - file for solving Part 2: ----
* Functions:
- masterProblem()
    Independent model of the first 24 hours, deterministic input.
    Returns v_res value at the 24'th hour
- subProblem()
    Independent model of the last 24 hours, stochastic input.
    Returns OBJ and Dual to generate cuts to the masterproblem
- generate_cuts()
    Takes OBJ and Dual from subproblem to generate and add cuts to a list, to be run in the masterproblem

-- Benders_loop()
    The actual Benders methodology algorithm, that sets the order of how and when to call the other functions
    This is the only function that needs to be called in order to solve the problem

    To run a single scenario, this variable need to be updated to "num_scenario = 1" .
    To run all scenario's, the "num_scenario" variable can be set to any number other than 1.

    To change the single scenario that is modelled, you need to change the
    " if num_scenario == 1
            S = [a number between 0 and 4]"


---- StochasticDP.py - file for solving Part 3: ----
* Functions:
- masterProblem()
    Independent model of the first 24 hours, deterministic input.
    Returns the objective value for all 48 hours
- subProblem()
    Independent model of the last 24 hours, stochastic input.
    Returns OBJ and Dual to generate cuts to the masterproblem
- generate_cuts()
    Takes OBJ and Dual from subproblem to generate and add cuts to a list, to be run in the masterproblem

-- SDP_loop()
    The actual SDP methodology algorithm, that sets the order of how and when to call the other functions
    This is the only function that needs to be called in order to solve the problem

    To run a single scenario, this variable need to be updated to "num_scenario = 1" .
    To run all scenario's, the "num_scenario" variable can be set to any number other than 1.

    To change the single scenario that is modelled, you need to change the
    " if num_scenario == 1
            S = [a number between 0 and 4]"

    To change the number of cuts generated, you need to change the "list_of_guess" list of state variables