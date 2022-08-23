from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import random
import sys  # To find out the script name (in argv[0])

# Import the backtrader platform
import threading
import time


import backtrader as bt
import matplotlib.pyplot

import quantstats
import pyfolio as pf

def Run(strategy, out):
    # Create a cerebro entity
    cerebro = bt.Cerebro()

    # Add a strategy
    cerebro.addstrategy(strategy)
    # cerebro.addstrategy(strat.BuyAndHold)

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    # datapath = os.path.join(modpath, 'data\\Binance_BTCUSDT_4h_2021-01-01 00-00-00_2022-06-22 16-00-00.csv')
    datapath = os.path.join(modpath, 'data\\Binance_ADAUSDT_1h_2021-01-01 00-00-00_2022-07-24 23-00-00.csv')
    # datapath1 = os.path.join(modpath, 'data\\Binance_BTCUSDT_1m_2021-01-01 00-00-00_2022-06-26 14-30-00.csv')
    # Create a Data Feed
    # data = bt.feeds.YahooFinanceCSVData(
    #     dataname=datapath,
    #     # Do not pass values before this date
    #     fromdate=datetime.datetime(2000, 1, 1),
    #     # Do not pass values before this date
    #     todate=datetime.datetime(2000, 12, 31),
    #     # Do not pass values after this date
    #     reverse=False)
    data = bt.feeds.GenericCSVData(dataname=datapath, timeframe=bt.TimeFrame.Minutes, compression=60)
    # data1 = bt.feeds.GenericCSVData(dataname=datapath1, timeframe=bt.TimeFrame.Minutes, compression=60)
    # Add the Data Feed to Cerebro
    # cerebro.adddata(data1)
    cerebro.adddata(data)
    # cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=60)
    # cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=98)

    # Set the commission
    cerebro.broker.setcommission(commission=0.001)
    cerebro.addwriter(bt.WriterFile, csv=True, out="1.csv")
    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe')
    cerebro.addanalyzer(bt.analyzers.Returns, _name='myreturns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='mydrowdown')
    results = cerebro.run(tradehistory=True, timeframe=bt.TimeFrame.Minutes, compression=60)
    res = results[0]
    print('Sharpe Ratio:', res.analyzers.mysharpe.get_analysis())
    print('Returns:', res.analyzers.myreturns.get_analysis())
    print('DrowDown:', res.analyzers.mydrowdown.get_analysis())
    pyfoliozer = res.analyzers.getbyname('pyfolio')
    returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
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
    cerebro.plot()
    # quantstats.plots.snapshot(positions, title='Facebook Performance')

    # matplotlib.pyplot.show()