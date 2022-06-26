import backtrader as bt

class StopLoss(bt.Indicator):
    lines = ('stoploss',)
    params = (('min_period', 5), ('atr_period', 20))

    def __init__(self):
        self.l.stoploss = bt.talib.MIN(self.data.close, timeperiod=self.p.min_period) - \
                              (bt.indicators.ATR(self.data, period=self.p.atr_period) * 0.25)