# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 00:17:10 2020

@author: Amin
"""

import numpy as np
import pandas as pd
from datetime import datetime, timezone, date

from binance.client import Client

# Binance python client library:
#   https://github.com/sammchardy/python-binance
# Library docs:
#   https://python-binance.readthedocs.io/en/latest/index.html

api_key = 'NfjCKix0SSnVigM7dPhluUKxpFZnmd3s5bUVdfZMer4KlSZGpnMdw2815Oa5BiMR'
api_secret = 'ChEyzzYY7EMtbrmKvZ3Jltfip1loihGoaT2UtGEeLHHI5bMfSNqDHPQuPq7I7Ezi'
client = Client(api_key, api_secret)
def get_all_markets_data(timeframe='1d', bars_count=500, min_rows=40):    
    
    dfs = {}
    
    index = 1
    symbol_names = get_symbol_names()[:]
    for symbol_name in symbol_names:
        i_of_all = '{} - {})'.format(index, len(symbol_names))
        print(i_of_all, 'Getting data for ', symbol_name)
        
        try:
            df = get_market_data(symbol_name, 
                                 timeframe=timeframe, 
                                 bars_count=bars_count)
            
            if df.shape[0] >= min_rows:  
                dfs[symbol_name] = df
                
        except Exception as ex:
            print("\t", "exception thrown:", ex)
            
        index += 1
        
    return dfs

def get_market_data(asset, timeFrame='4h', start_time=date(2019, 11, 1), end_time=None,saveFile=False):
    """"""

    tf = translate_time_frame(timeFrame)

    try:
        if end_time is None:
            candles = client.get_historical_klines(asset.upper(), tf,
                                                   start_time.strftime("%d %b, %Y"))
        else:
            candles = client.get_historical_klines(asset.upper(), tf,
                                                   start_time.strftime("%d %b, %Y"), end_time.strftime("%d %b, %Y"))
        arrData = np.array(candles)
        
        dates = arrData[:,0].reshape(-1,1)
        dates = [epoch_to_datetime(t) for t in dates]                    
    
        df = pd.DataFrame(index=dates)
        df.index.name = 'Date Time'
        df['Open'] = arrData[:,1]
        df['High'] = arrData[:,2]
        df['Low'] = arrData[:,3]
        df['Close'] = arrData[:,4]
        df['Volume'] = arrData[:,5]
        df['Adj Close'] = df['Close']
        df['Quote Volume'] = arrData[:,7]
        df['Trades Count'] = arrData[:,8]
        
        df = df[:-1]    
        df = df_to_numeric(df)
    
        if saveFile:            
            fromTime = df.index[0]
            toTime = df.index[-1]
            fileName = 'data\\Binance_{}_{}_{}_{}.csv'.format(asset, timeFrame, fromTime, toTime).replace(':', '-')
            df.to_csv(fileName, index=True)
    
        return df
    except:
        return pd.DataFrame()
    
def get_symbol_names():    
    
    stable_pairs = ['PAXUSDT', 'TUSDUSDT', 'USDCUSDT', 'USDSUSDT', 'BUSDUSDT']
    
    info = client.get_exchange_info()
    symbol_names = [symbol['symbol'] for symbol in info['symbols'] \
                    if (symbol['status']=='TRADING') and 
                    (symbol['symbol'] not in stable_pairs) and
                    ('USDT' in symbol['symbol'])]
    
    return symbol_names
    
# %% Helper methods
    
def epoch_to_datetime(epoch):
    return datetime.fromtimestamp(int(epoch) // 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
  
def translate_time_frame(tf):

    mapping = {
        "1m": Client.KLINE_INTERVAL_1MINUTE,
        "3m": Client.KLINE_INTERVAL_3MINUTE,
        "5m": Client.KLINE_INTERVAL_5MINUTE,
        "15m": Client.KLINE_INTERVAL_15MINUTE,
        "30m": Client.KLINE_INTERVAL_30MINUTE,
        "1h": Client.KLINE_INTERVAL_1HOUR,
        "2h": Client.KLINE_INTERVAL_2HOUR,
        "4h": Client.KLINE_INTERVAL_4HOUR,
        "6h": Client.KLINE_INTERVAL_1HOUR,
        "8h": Client.KLINE_INTERVAL_8HOUR,
        "12h": Client.KLINE_INTERVAL_12HOUR,
        "1d": Client.KLINE_INTERVAL_1DAY,
        "3d": Client.KLINE_INTERVAL_3DAY,
        "1w": Client.KLINE_INTERVAL_1WEEK,
        "1M": Client.KLINE_INTERVAL_1MONTH
    }

    return mapping.get(str(tf))

def df_to_numeric(df):
    
    df['Open'] = pd.to_numeric(df['Open'])
    df['High'] = pd.to_numeric(df['High'])
    df['Low'] = pd.to_numeric(df['Low'])
    df['Close'] = pd.to_numeric(df['Close'])
    df['Volume'] = pd.to_numeric(df['Volume'])
    
    return df
get_market_data("ETHUSDT", "1h", date(2018,1,1), date(2022,8,1), saveFile=True)
#KLINE_INTERVAL_1MINUTE = '1m'
#KLINE_INTERVAL_3MINUTE = '3m'
#KLINE_INTERVAL_5MINUTE = '5m'
#KLINE_INTERVAL_15MINUTE = '15m'
#KLINE_INTERVAL_30MINUTE = '30m'
#KLINE_INTERVAL_1HOUR = '1h'
#KLINE_INTERVAL_2HOUR = '2h'
#KLINE_INTERVAL_4HOUR = '4h'
#KLINE_INTERVAL_6HOUR = '6h'
#KLINE_INTERVAL_8HOUR = '8h'
#KLINE_INTERVAL_12HOUR = '12h'
#KLINE_INTERVAL_1DAY = '1d'
#KLINE_INTERVAL_3DAY = '3d'
#KLINE_INTERVAL_1WEEK = '1w'
#KLINE_INTERVAL_1MONTH = '1M'
