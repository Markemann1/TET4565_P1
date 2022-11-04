from model1 import task1_model
from Benders import Benders_loop
from StochasticDP import SDP_loop


def main():
    print('-------------')
    print('---Part 1:---')
    print('-------------')
    task1_model()

    print('-------------')
    print('---Part 2:---')
    print('-------------')
    Benders_loop()

    print('-------------')
    print('---Part 3:---')
    print('-------------')
    SDP_loop()


if __name__ == '__main__':
    main()
