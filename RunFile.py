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
from backtrader.mathsupport import average, standarddev
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

def get_timeframe(s_date):
    match = re.findall("(?<=USDT_)(.*?)(?=_)", s_date)[0]
    return match

def Run(strategy, out):

    results_data_columns = [('', '', 'Strategy Name'), ('', '', 'Currency'), ('', '', 'TimeFrame'),
                            ('', 'Total_Return', 'Asset'), ('', 'Total_Return', 'Strategy'),
                            ('', 'Total_Return', 'Diff')]
    results_data_rows = {'Strategy Name': [], 'Currency': [], 'TimeFrame': [], 'Total_Asset_Return': [],
                         'Total_Strategy_Return': [], 'Total_Diff_Return': []}
    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    data_path = os.path.join(modpath, 'data\\Binance_BNBUSDT_1h_2022-05-01 00-00-00_2022-07-31 23-00-00.csv')
    asset = get_asset(data_path)
    range_dates = get_date(data_path)
    timeframe = get_timeframe(data_path)
    divided_dates = pd.date_range(start=range_dates[0], end=range_dates[1], freq=pd.offsets.MonthBegin(2))
    all_range_dates = pd.date_range(start=range_dates[0], end=range_dates[1], freq=None, periods=2)
    dates = ((all_range_dates[0], all_range_dates[1]),)
    dates = dates + tuple((divided_dates[i], divided_dates[i+1]) for i in range(len(divided_dates)-1))
    for index, v in enumerate(dates):
        from_date = datetime.datetime.fromtimestamp(v[0].value / 1e9).strftime('%Y-%m-%d')
        to_date = datetime.datetime.fromtimestamp(v[1].value / 1e9).strftime('%Y-%m-%d')
        data = bt.feeds.GenericCSVData(dataname=data_path, timeframe=bt.TimeFrame.Minutes, compression=60,
                                       fromdate=datetime.datetime.strptime(from_date, "%Y-%m-%d"),
                                       todate=datetime.datetime.strptime(to_date, "%Y-%m-%d"))
        if index > 0:
            month_title = from_date.split('-')[0] + '/' + from_date.split('-')[1] + '-' +\
                          to_date.split('-')[0] + '/' + to_date.split('-')[1]
            results_data_columns.append((month_title, 'Return', 'Asset'))
            results_data_columns.append((month_title, 'Return', 'Strategy'))
            results_data_columns.append((month_title, 'STD', ''))
            results_data_columns.append((month_title, 'MaxDrawdown(%)', 'Asset' ))
            results_data_columns.append((month_title, 'MaxDrawdown(%)', 'Strategy'))
            results_data_columns.append((month_title, 'MaxDrawdown(%)', 'Diff'))
            results_data_columns.append((month_title, 'MaxDrawdown(Time)', 'Asset'))
            results_data_columns.append((month_title, 'MaxDrawdown(Time)', 'Strategy'))
            results_data_columns.append((month_title, 'MaxDrawdown(Time)', 'Diff'))
            results_data_rows['Return_Asset_' + str(index)] = []
            results_data_rows['Return_Strategy_' + str(index)] = []
            results_data_rows['STD_' + str(index)] = []
            results_data_rows['MaxDrowDown(%)_Asset_' + str(index)] = []
            results_data_rows['MaxDrowDown(%)_Strategy_' + str(index)] = []
            results_data_rows['MaxDrowDown(%)_Diff_' + str(index)] = []
            results_data_rows['MaxDrowDown(Time)_Asset_' + str(index)] = []
            results_data_rows['MaxDrowDown(Time)_Strategy_' + str(index)] = []
            results_data_rows['MaxDrowDown(Time)_Diff_' + str(index)] = []

        ret_asset = []
        ret_strategy = []
        for st in strategy:
            # Create a cerebro entity
            # cerebro = bt.Cerebro()
            cerebro = bt.Cerebro(maxcpus=4, runonce=False, optreturn=True)

            # Add a strategy
            cerebro.optstrategy(st)
            # cerebro.optstrategy(strategy[0])
            # cerebro.optstrategy(strategy, maperiod=range(20, 25))

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
            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio', timeframe=bt.TimeFrame.Minutes, compression=60)
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe', timeframe=bt.TimeFrame.Minutes, compression=60)
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn', timeframe=bt.TimeFrame.Minutes, compression=1)
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drowdown')
            cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='timedrowdown', timeframe=bt.TimeFrame.Minutes, compression=60)

            results = cerebro.run(timeframe=bt.TimeFrame.Minutes, compression=60)
            print('==================================================')
            for res in results:
                for strat in res:
                    if index == 0:
                        ret = 0
                        for i in list(strat.analyzers.timereturn.get_analysis().items()):
                            ret += i[1]
                        if strat.strategycls.__name__ == "BuyAndHold":
                            results_data_rows['Total_Asset_Return'].append(ret)
                        else:
                            results_data_rows['Total_Strategy_Return'].append(ret)
                            results_data_rows['Strategy Name'].append(strat.strategycls.__name__)
                    else:
                        if strat.strategycls.__name__ == "BuyAndHold":
                            for i in list(strat.analyzers.timereturn.get_analysis().items()):
                                if i[1] != 0:
                                    ret_asset.append(i[1])
                            results_data_rows['MaxDrowDown(%)_Asset_' + str(index)].append(
                                strat.analyzers.drowdown.get_analysis()['max']['drawdown'])
                            results_data_rows['MaxDrowDown(Time)_Asset_' + str(index)].append(
                                strat.analyzers.drowdown.get_analysis()['len'])
                            results_data_rows['Return_Asset_' + str(index)].append(sum(ret_asset))
                        else:
                            for i in list(strat.analyzers.timereturn.get_analysis().items()):
                                if i[1] != 0:
                                    ret_strategy.append(i[1])
                            results_data_rows['MaxDrowDown(%)_Strategy_' + str(index)].append(
                                strat.analyzers.drowdown.get_analysis()['max']['drawdown'])
                            results_data_rows['MaxDrowDown(Time)_Strategy_' + str(index)].append(
                                strat.analyzers.drowdown.get_analysis()['len'])
                            results_data_rows['Return_Strategy_' + str(index)].append(sum(ret_strategy))
            print('==================================================')
            # res = results[0]
            # print('Sharpe Ratio:', res.analyzers.mysharpe.get_analysis())
            # print('Returns:', res.analyzers.myreturns.get_analysis())
            # print('DrowDown:', res.analyzers.mydrowdown.get_analysis())
            # standarddev()
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
        if index == 0:
            results_data_rows['Currency'].append(asset)
            results_data_rows['TimeFrame'].append(timeframe)
            results_data_rows['Total_Diff_Return'].append(results_data_rows['Total_Asset_Return'][-1] -
                                                          results_data_rows['Total_Strategy_Return'][-1])
        else:
            results_data_rows['STD_' + str(index)].append((average(ret_strategy) - average(ret_asset)) / standarddev(ret_asset))
            results_data_rows['MaxDrowDown(%)_Diff_' + str(index)].append(
                results_data_rows['MaxDrowDown(%)_Asset_' + str(index)][-1] -
                results_data_rows['MaxDrowDown(%)_Strategy_' + str(index)][-1])
            results_data_rows['MaxDrowDown(Time)_Diff_' + str(index)].append(
                results_data_rows['MaxDrowDown(Time)_Asset_' + str(index)][-1] -
                results_data_rows['MaxDrowDown(Time)_Strategy_' + str(index)][-1])
    columns = pd.MultiIndex.from_tuples(results_data_columns)
    df = pd.DataFrame(results_data_rows)
    df.columns = columns
    df.to_excel('Results\\' + asset + timeframe + '.xlsx', merge_cells=True)
    # pd.DataFrame(results_data).to_csv('Results\\result.csv')
