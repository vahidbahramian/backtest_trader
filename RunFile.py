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
import warnings
warnings.filterwarnings('ignore')
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


def Run(strategy, params, file_path, divide_to_months):
    start_analyze_time = time.time()
    results_data_columns = [('', '', 'Strategy Name'), ('', '', 'Currency'), ('', '', 'TimeFrame'),
                            ('', 'Total_Return', 'Asset'), ('', 'Total_Return', 'Strategy'),
                            ('', 'Total_Return', 'Diff'), ('', 'STD', ''), ('', 'MaxDD(%)', 'Asset'),
                            ('', 'MaxDD(%)', 'Strategy'), ('', 'MaxDD(Time)', 'Asset'), ('', 'MaxDD(Time)', 'Strategy')]
    for i in params.keys():
        results_data_columns.append(('', 'Parameters', i))

    results_data_rows = {'Strategy Name': [], 'Currency': [], 'TimeFrame': [], 'Total_Asset_Return': [],
                         'Total_Strategy_Return': [], 'Total_Diff_Return': [], 'Total_STD': [],
                         'Total_MaxDD(%)_Asset': [], 'Total_MaxDD(%)_Strategy': [], 'Total_MaxDD(Time)_Asset': [],
                         'Total_MaxDD(Time)_Strategy': []}
    for i in params.keys():
        results_data_rows[i] = []

    # Datas are in a subfolder of the samples. Need to find where the script is
    # because it could have been called from anywhere
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))

    data_path = os.path.join(os.path.join(modpath, 'data'), file_path)

    asset = get_asset(data_path)
    range_dates = get_date(data_path)
    timeframe = get_timeframe(data_path)

    all_range_dates = pd.date_range(start=range_dates[0], end=range_dates[1], freq=None, periods=2)
    dates = ((all_range_dates[0], all_range_dates[1]),)
    if divide_to_months:
        divided_dates = pd.date_range(start=range_dates[0], end=range_dates[1], freq=pd.offsets.MonthBegin(2))
        dates = dates + tuple((divided_dates[i], divided_dates[i + 1]) for i in range(len(divided_dates) - 1))
    for index, v in enumerate(dates):
        from_date = datetime.datetime.fromtimestamp(v[0].value / 1e9).strftime('%Y-%m-%d')
        to_date = datetime.datetime.fromtimestamp(v[1].value / 1e9).strftime('%Y-%m-%d')
        data = bt.feeds.GenericCSVData(dataname=data_path, timeframe=bt.TimeFrame.Minutes, compression=60,
                                       fromdate=datetime.datetime.strptime(from_date, "%Y-%m-%d"),
                                       todate=datetime.datetime.strptime(to_date, "%Y-%m-%d"))
        if index > 0:
            month_title = from_date.split('-')[0] + '/' + from_date.split('-')[1] + '-' + \
                          to_date.split('-')[0] + '/' + to_date.split('-')[1]
            results_data_columns.append((month_title, 'Return', 'Asset'))
            results_data_columns.append((month_title, 'Return', 'Strategy'))
            results_data_columns.append((month_title, 'STD', ''))
            results_data_columns.append((month_title, 'MaxDrawdown(%)', 'Asset'))
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

        sum_return_asset = []
        max_dd_asset_percent = 0
        max_dd_asset_time = 0
        ret_asset = []
        return_asset = 0
        for st in strategy:
            start_time = time.time()
            # Create a cerebro entity
            # cerebro = bt.Cerebro()
            cerebro = bt.Cerebro(runonce=False)

            # Add a strategy
            if st.__name__ == "BuyAndHold":
                cerebro.optstrategy(st)
            else:
                cerebro.optstrategy(st, **params)
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
            # print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

            # Add analysis to cerebro
            cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio', timeframe=bt.TimeFrame.Minutes, compression=60)
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='mysharpe', timeframe=bt.TimeFrame.Minutes,
                                compression=60)
            cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='timereturn', timeframe=bt.TimeFrame.Minutes,
                                compression=60)
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drowdown')
            cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name='timedrowdown', timeframe=bt.TimeFrame.Minutes,
                                compression=60)
            cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, _name='logreturn', timeframe=bt.TimeFrame.Minutes,
                                compression=60)
            cerebro.addanalyzer(bt.analyzers.Transactions, _name='transactions')
            results = cerebro.run(timeframe=bt.TimeFrame.Minutes, compression=60)

            ### Log Block
            for res in results:
                for strat in res:
                    ret_strategy = []
                    sum_return_strategy = []
                    if index == 0:
                        if strat.strategycls.__name__ == "BuyAndHold":
                            max_dd_asset_percent = strat.analyzers.drowdown.get_analysis()['max']['drawdown']
                            max_dd_asset_time = strat.analyzers.timedrowdown.get_analysis()['maxdrawdownperiod']
                            for i in list(strat.analyzers.logreturn.get_analysis().items()):
                                if i[1] != 0:
                                    sum_return_asset.append(i[1])
                            # sum_return_asset = sum(j for i, j in list(strat.analyzers.logreturn.get_analysis().items()))
                            # sum_return_asset = abs(list(strat.analyzers.transactions.get_analysis().items())[-1][1][0][
                            #                        4]) - 10000
                        else:
                            for i in list(strat.analyzers.logreturn.get_analysis().items()):
                                if i[1] != 0:
                                    sum_return_strategy.append(i[1])
                            # sum_return_strategy = sum(j for i, j in list(strat.analyzers.logreturn.get_analysis().items()))
                            # sum_return_strategy = abs(list(strat.analyzers.transactions.get_analysis().items())[-1][1][0][
                            #                        4]) - 10000
                            results_data_rows['Strategy Name'].append(strat.strategycls.__name__)
                            results_data_rows['Currency'].append(asset)
                            results_data_rows['TimeFrame'].append(timeframe)
                            # results_data_rows['Total_Asset_Return'].append(sum_return_asset)
                            results_data_rows['Total_Asset_Return'].append(sum(sum_return_asset))
                            for p, value in params.items():
                                results_data_rows[p].append(strat.p._getkwargs()[p])
                            # results_data_rows['Total_Strategy_Return'].append(sum_return_strategy)
                            results_data_rows['Total_Strategy_Return'].append(sum(sum_return_strategy))
                            results_data_rows['Total_Diff_Return'].append(sum(sum_return_asset) - sum(sum_return_strategy))
                            try:
                                results_data_rows['Total_STD'].append((average(sum_return_strategy) - average(sum_return_asset))
                                                                              / standarddev(sum_return_asset))
                            except ZeroDivisionError as e:
                                results_data_rows['Total_STD'].append("")
                            results_data_rows['Total_MaxDD(%)_Asset'].append(max_dd_asset_percent)
                            results_data_rows['Total_MaxDD(%)_Strategy'].append(strat.analyzers.drowdown.get_analysis()['max']['drawdown'])
                            results_data_rows['Total_MaxDD(Time)_Asset'].append(max_dd_asset_time)
                            results_data_rows['Total_MaxDD(Time)_Strategy'].append(strat.analyzers.timedrowdown.get_analysis()['maxdrawdownperiod'])
                    else:  # Divided To Month
                        # for i in list(strat.analyzers.timereturn.get_analysis().items()):
                        #     if i[1] != 0:
                        #         if strat.strategycls.__name__ == "BuyAndHold":
                        #             max_dd_asset_percent = strat.analyzers.drowdown.get_analysis()['max']['drawdown']
                        #             max_dd_asset_time = strat.analyzers.timedrowdown.get_analysis()['maxdrawdownperiod']
                        #             ret_asset.append(i[1])
                        #         else:
                        #             ret_strategy.append(i[1])
                        if strat.strategycls.__name__ == "BuyAndHold":
                            for i in list(strat.analyzers.logreturn.get_analysis().items()):
                                if i[1] != 0:
                                    ret_asset.append(i[1])
                            max_dd_asset_percent = strat.analyzers.drowdown.get_analysis()['max']['drawdown']
                            max_dd_asset_time = strat.analyzers.timedrowdown.get_analysis()['maxdrawdownperiod']
                            # return_asset = abs(list(strat.analyzers.transactions.get_analysis().items())[-1][1][0][4]) - 10000

                        if strat.strategycls.__name__ != "BuyAndHold":
                            for i in list(strat.analyzers.logreturn.get_analysis().items()):
                                if i[1] != 0:
                                    ret_strategy.append(i[1])
                            results_data_rows['Return_Asset_' + str(index)].append(sum(ret_asset))
                            results_data_rows['Return_Strategy_' + str(index)].append(sum(ret_strategy))
                            # results_data_rows['Return_Asset_' + str(index)].append(return_asset)
                            # results_data_rows['Return_Strategy_' + str(index)].append(abs(list(strat.analyzers.transactions.get_analysis().items())[-1][1][0][4]) - 10000)
                            results_data_rows['MaxDrowDown(%)_Asset_' + str(index)].append(max_dd_asset_percent)
                            results_data_rows['MaxDrowDown(Time)_Asset_' + str(index)].append(max_dd_asset_time)
                            results_data_rows['MaxDrowDown(%)_Strategy_' + str(index)].append(
                                strat.analyzers.drowdown.get_analysis()['max']['drawdown'])
                            results_data_rows['MaxDrowDown(Time)_Strategy_' + str(index)].append(
                                strat.analyzers.timedrowdown.get_analysis()['maxdrawdownperiod'])
                            results_data_rows['MaxDrowDown(%)_Diff_' + str(index)].append(max_dd_asset_percent -
                                                                                          strat.analyzers.drowdown.get_analysis()[
                                                                                              'max']['drawdown'])
                            results_data_rows['MaxDrowDown(Time)_Diff_' + str(index)].append(max_dd_asset_time -
                                                                                             strat.analyzers.timedrowdown.get_analysis()[
                                                                                                 'maxdrawdownperiod'])
                            try:
                                results_data_rows['STD_' + str(index)].append((average(ret_strategy) - average(ret_asset))
                                                                              / standarddev(ret_asset))
                            except ZeroDivisionError as e:
                                results_data_rows['STD_' + str(index)].append("")
            ###########################################################
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
            # print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

            # Plot the result
            # cerebro.plot()
            # quantstats.plots.snapshot(positions, title='Facebook Performance')

            # matplotlib.pyplot.show()

            print("From:", from_date, "To:", to_date, "\n", "Strategy =", st.__name__,  "\n", "Process Time =",
                  (time.time() - start_time), "sec")
    columns = pd.MultiIndex.from_tuples(results_data_columns)
    df = pd.DataFrame(results_data_rows)
    df.columns = columns
    df.to_excel(os.path.join('Results', file_path) + '.xlsx', merge_cells=True)
    print("Total Process Time =", (time.time() - start_analyze_time) / 60, "min")
    # pd.DataFrame(results_data).to_csv('Results\\result.csv')
