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
    Run(strategys, None)