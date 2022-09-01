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

    parameters = {'ma_period': [10, 25, 50], 'avg_period': [10, 25, 50], 'std_period':  [10, 25, 50],
                  'multiplier': [2, 4, 6], 'a': [1], 'b': [1], 'c': [1], 'd': [1], 'x': [1, 2, 3], 'y': [1, 2, 3]}
    file_path = "Binance_BTCUSDT_1h_2018-01-01 00-00-00_2022-07-24 23-00-00.csv"
    divide_to_months = False
    Run(strategys, parameters, file_path, divide_to_months)