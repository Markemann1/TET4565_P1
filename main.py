import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from model1 import task1_model
from Benders import Benders_loop
from StochasticDP import SDP_loop


def main():
    # print('Oppgave 1:')
    # task1_model()
    #
    # print('Oppgave 2:')
    # Benders_loop()

    print('Oppgave 3:')
    SDP_loop()


if __name__ == '__main__':
    main()
