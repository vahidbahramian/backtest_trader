from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import random
import re
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import threading
import time


import backtrader as bt
import matplotlib.pyplot
import pandas as pd

import quantstats
import pyfolio as pf

def get_date(s_date):
    match = re.findall(r'\d{4}-\d{2}-\d{2}', s_date)
    return match

def get_asset(s_date):
    match = re.findall("(?<=_)(.*?)(?=USDT_)", s_date)[0].split("_")[1]
    return match

def Run(strategy, out):

    results_data = {'Currency': [], 'SharpRatio': [], 'MaPeriod': []}

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    data_path = os.path.join(modpath, 'data\\Binance_BNBUSDT_1h_2018-01-01 00-00-00_2022-07-31 23-00-00.csv')
    asset = get_asset(data_path)
    range_dates = get_date(data_path)
    dates = pd.date_range(start=range_dates[0], end=range_dates[1], freq=pd.offsets.MonthBegin(6))
    for i in range(len(dates)-1):
        data = bt.feeds.GenericCSVData(dataname=data_path, timeframe=bt.TimeFrame.Minutes, compression=60,
                                       fromdate=datetime.datetime.utcfromtimestamp(dates.values[i].tolist() / 1e9),
                                       todate=datetime.datetime.utcfromtimestamp(dates.values[i+1].tolist() / 1e9))

        # Create a cerebro entity
        # cerebro = bt.Cerebro()
        cerebro = bt.Cerebro(maxcpus=4, runonce=False, optreturn=True)

        # Add a strategy
        # cerebro.addstrategy(strategy)
        cerebro.optstrategy(strategy, maperiod=range(20, 25))

        # Add the Data Feed to Cerebro
        cerebro.adddata(data)
        # cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=60)

        # Set our desired cash start
        cerebro.broker.setcash(10000.0)

        # Add a FixedSize sizer according to the stake
        cerebro.addsizer(bt.sizers.PercentSizer, percents=98)

        # Set the commission
        cerebro.broker.setcommission(commission=0.001)


        # cerebro.addwriter(bt.WriterFile, csv=True, out="1.csv")

        # Print out the starting conditions
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Add analysis to cerebro
        cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe', timeframe=bt.TimeFrame.Minutes, compression=60)
        cerebro.addanalyzer(bt.analyzers.Returns, _name='myreturns')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydrowdown')

        results = cerebro.run(timeframe=bt.TimeFrame.Minutes, compression=60)
        print('==================================================')
        for res in results:
            print(res)
            for strat in res:
                print('Sharpe Ratio:', strat.analyzers.mysharpe.get_analysis())
                print(strat.p._getkwargs()['maperiod'])
                print('--------------------------------------------------')
                results_data['Currency'].append(asset)
                results_data['SharpRatio'].append(strat.analyzers.mysharpe.get_analysis()['sharperatio'])
                results_data['MaPeriod'].append(strat.p._getkwargs()['maperiod'])
        print('==================================================')

        # res = results[0]
        # print('Sharpe Ratio:', res.analyzers.mysharpe.get_analysis())
        # print('Returns:', res.analyzers.myreturns.get_analysis())
        # print('DrowDown:', res.analyzers.mydrowdown.get_analysis())
        # pyfoliozer = res.analyzers.getbyname('pyfolio')
        # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
        # ax = pf.plot_returns(returns)
        # ax.plot()
        # fig = pf.create_position_tear_sheet(returns, positions, return_fig=True)
        # fig = pf.create_txn_tear_sheet(returns, positions, transactions, return_fig=True)
        # pf.create_full_tear_sheet(
        #     returns,
        #     positions=positions,
        #     transactions=transactions,
        #     live_start_date='2021-05-01',
        #     round_trips=True)

        # returns.index = returns.index.tz_convert(None)
        # quantstats.reports.html(returns, output='returns.html')

        # Print out the final result
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Plot the result
        # cerebro.plot()
        # quantstats.plots.snapshot(positions, title='Facebook Performance')

        # matplotlib.pyplot.show()
    pd.DataFrame(results_data).to_csv('Results\\result.csv')