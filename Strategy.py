import backtrader as bt
import Indicator as ind


class BuyAndHold(bt.Strategy):

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None

    def next(self):

        if self.order:
            return

        if not self.position:
            self.order = self.buy()


class Strategy_1(bt.Strategy):
    params = (
        ('maperiod', 50),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)
        self.percentile = bt.indicators.PercentRank(self.dataclose / self.sma, period=100)
        self.avg = bt.indicators.SimpleMovingAverage(self.dataclose / self.sma, period=25)
        self.stddev = bt.indicators.StandardDeviation(self.dataclose, period=100, plot=False)

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        self.atr = bt.indicators.ATR(self.datas[0], plot=False)
        self.SL = ind.StopLoss(self.datas[0], plot=False)
        self.super_trend = ind.SuperTrend(self.datas[0], plot=False)
        # self.a = bt.indicators.MACD(self.datas[0], plot=False)
        self.momentum = bt.indicators.Momentum(self.datas[0], period=5, plot=False)
        # self.close_cross_over = bt.ind.CrossOver(self.datas[0].close, self.datas[-1].close)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        self.log('Percentile, %2f' % self.percentile[0])
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # self.log('Percentile, %2f' % self.percentile[0])
        # self.log('Super_Trend, %2f' % self.super_trend[0])
        # self.log('UpperBand, %2f' % self.super_trend.l.final_upperband[0])
        # self.log('LowerBand, %2f' % self.super_trend.l.final_lowerband[0])
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if (self.dataclose[0] < self.sma[0]) and self.momentum[0] > 0 and self.stddev[0] > self.atr \
                    and (self.percentile[-1] < 0.1 or self.percentile[-2] < 0.1 or self.percentile[-3] < 0.1 or
                         self.percentile[-4] < 0.1) \
                    and self.avg[0] < self.avg[-25]:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.SL_buy = self.SL[0]

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()
        else:
            if self.dataclose[0] < self.SL_buy or \
                    (self.percentile[0] < 0.9 and self.percentile[-1] > 0.9 and self.dataclose[0] < self.dataclose[-1]) \
                    or (self.dataclose[-1] > self.sma[-1] - (self.atr[-1] * 0.5) and
                        self.dataclose[0] < self.sma[0] - (self.atr[0] * 0.5)):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()


class Strategy_2(bt.Strategy):
    params = (
        ('maperiod', 25),
        ('avg_period', 25),
        ('std_period', 25),
        ('multiplier', 2),
        ('a', 1),
        ('b', 1),
        ('c', 1),
        ('d', 1),
        ('x', 1),
        ('y', 1),
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.datetime(0)
        # print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)
        self.avg = bt.indicators.SimpleMovingAverage(self.dataclose / self.sma, period=self.params.avg_period)
        # self.super_trend_S = ind.SuperTrend_S(self.datas[0], plot=False)
        self.super_trend_F = ind.SuperTrend_F(self.datas[0], plot=False, multiplier=self.params.multiplier)
        self.ichimoku = bt.indicators.Ichimoku(self.datas[0], senkou_lead=0, plot=False)
        # self.macd = bt.indicators.MACD(self.datas[0], plot=False)
        # self.rsi = bt.indicators.RSI(self.datas[0], period=100,  plot=False)
        # self.momentum = bt.indicators.Momentum(self.datas[0], period=20, plot=False)
        self.atr = bt.indicators.ATR(self.datas[0], plot=False)
        self.stddev = bt.indicators.StandardDeviation(self.dataclose, period=self.params.std_period, plot=False)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        E = 0
        STD = 0
        for i in range(0, -51):
            E += (self.dataclose[i] - self.sma[0])
        STD = E / self.sma[0]
        #self.log('Super_Trend, %2f' % self.super_trend[0])
        #self.log('UpperBand, %2f' % self.super_trend.l.final_upperband[0])
        #self.log('LowerBand, %2f' % self.super_trend.l.final_lowerband[0])
        #self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.ichimoku.l.senkou_span_b[-25]:
                    #self.sma[0] > self.dataclose[0]:
                    #self.dataclose[0] < self.ichimoku.l.senkou_span_b[-25] and self.avg > 1:
                #self.ichimoku.l.senkou_span_b[-25] > self.ichimoku.l.senkou_span_a[-25]):
                #(self.ichimoku.l.senkou_span_b[0] - self.ichimoku.l.senkou_span_a[0]) > 2 * self.atr[0]
                    if (self.ichimoku.l.senkou_span_b[0] - self.ichimoku.l.senkou_span_a[0] <
                          self.ichimoku.l.senkou_span_b[-25] - self.ichimoku.l.senkou_span_a[-25] and
                          (1 - self.params.a * self.stddev[0] / self.sma[0]) < self.avg[0]) or \
                          ((self.ichimoku.l.senkou_span_b[0] - self.ichimoku.l.senkou_span_a[0]) > self.params.x * self.stddev[0] and
                          (self.ichimoku.l.senkou_span_b[0] + self.ichimoku.l.senkou_span_a[0]) / 2 < self.dataclose[0] and
                          (1 - self.params.b * self.stddev[0] / self.sma[0]) > self.avg[0]):
                          #self.ichimoku.l.senkou_span_b[-25] - self.ichimoku.l.senkou_span_a[-25]) > 3 * self.atr[0]
                          #(self.ichimoku.l.senkou_span_b[0] + self.ichimoku.l.senkou_span_a[0])/2 < self.dataclose[0] and \
                          #self.ichimoku.l.senkou_span_a[0] >= self.ichimoku.l.senkou_span_a[-1] and self.momentum[0] > 0)

                        if self.super_trend_F[-1] == 0 and self.super_trend_F[0] == 1:
                            # BUY, BUY, BUY!!! (with all possible default parameters)
                            self.log('BUY CREATE, %.2f' % self.dataclose[0])

                            # Keep track of the created order to avoid a 2nd order
                            self.order = self.buy()
            else:
                if (1 - self.params.c * self.stddev[0]/self.sma[0]) < self.avg[0] < (1 + self.params.d * self.stddev[0]/self.sma[0]) and \
                        (self.ichimoku.l.senkou_span_a[0] - self.ichimoku.l.senkou_span_b[0]) < self.params.y * self.stddev[0]:
                        #self.ichimoku.l.senkou_span_b[0] - self.ichimoku.l.senkou_span_a[0] < \
                        #self.ichimoku.l.senkou_span_b[-25] - self.ichimoku.l.senkou_span_a[-25]):
                    if self.super_trend_F[-1] == 0 and self.super_trend_F[0] == 1:
                            # BUY, BUY, BUY!!! (with all possible default parameters)
                            self.log('BUY CREATE, %.2f' % self.dataclose[0])

                            # Keep track of the created order to avoid a 2nd order
                            self.order = self.buy()

        else:
            if self.super_trend_F[-1] == 1 and self.super_trend_F[0] == 0:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()
