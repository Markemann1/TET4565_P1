import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from model1 import task1_model
#from Benders import Benders_loop


def main():
    task1_model()

    # oppgave 2
    # Benders_loop()


if __name__ == '__main__':
    main()
