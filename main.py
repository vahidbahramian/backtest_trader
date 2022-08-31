import Strategy as strat
from multiprocessing import Process, Queue

from RunFile import Run


if __name__ == '__main__':
    strategys = [strat.BuyAndHold, strat.Strategy_2]

    # for strategy in strategys:
    #     output = Queue()
    #     p = Process(target=Run, args=(strategy, output,))
    #     p.start()
    # p.join()

    # for strategy in strategys:
    #     output = Queue()
    #     p = Run(strategy, output)

    parameters = {'ma_period': [20, 25], 'avg_period': [20, 25], 'std_period':  [20, 25],
                  'multiplier': [2], 'a': 1, 'b': 1, 'c': 1, 'd': 1, 'x': 2, 'y': 2}
    file_path = "Binance_ETHUSDT_1h_2018-01-01 00-00-00_2022-07-31 23-00-00.csv"
    divide_to_months = True
    Run(strategys, parameters, file_path, divide_to_months)
