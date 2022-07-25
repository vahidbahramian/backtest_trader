import backtrader as bt
import numpy as np
import pandas_ta as pandasTa

class StopLoss(bt.Indicator):
    lines = ('stoploss',)
    params = (('min_period', 5), ('atr_period', 20))

    def __init__(self):
        self.l.stoploss = bt.talib.MIN(self.data.close, timeperiod=self.p.min_period) - \
                              (bt.indicators.ATR(self.data, period=self.p.atr_period) * 0.25)

class SuperTrend(bt.Indicator):
    lines = ('super_trend', 'final_upperband', 'final_lowerband')
    params = (('atr_period', 15), ('multiplier', 2))

    def __init__(self):
        self.atr = bt.indicators.ATR(self.data, period=self.p.atr_period)
        self.hl2 = (self.data.high + self.data.low) / 2
        self.l.final_upperband = self.hl2 + (self.p.multiplier * self.atr)
        self.l.final_lowerband = self.hl2 - (self.p.multiplier * self.atr)

    def next(self):
        # if current close price crosses above upperband
        if self.data.close[0] > self.l.final_upperband[-1]:
            self.l.super_trend[0] = True
        # if current close price crosses below lowerband
        elif self.data.close[0] < self.l.final_lowerband[-1]:
            self.l.super_trend[0] = False
        # else, the trend continues
        else:
            self.l.super_trend[0] = self.l.super_trend[-1]

            # adjustment to the final bands
            if self.l.super_trend[0] == True and self.l.final_lowerband[0] < self.l.final_lowerband[-1]:
                self.l.final_lowerband[0] = self.l.final_lowerband[-1]
            if self.l.super_trend[0] == False and self.l.final_upperband[0] > self.l.final_upperband[-1]:
                self.l.final_upperband[0] = self.l.final_upperband[-1]

        # to remove bands according to the trend direction
        if self.l.super_trend[0] == True:
            self.l.final_upperband[0] = np.nan
        else:
            self.l.final_lowerband[0] = np.nan
