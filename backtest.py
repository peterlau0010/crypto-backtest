# %%
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])
import matplotlib

# Import the backtrader platform
import backtrader as bt
import backtrader.indicators as btind
import backtrader.feeds as btfeeds

# config
import config as cfg

# Create a Stratey


class TestStrategy(bt.Strategy):
    params = (
        ('kdPeriod', 5),
        ('printlog', True),
        ('stoptype', bt.Order.StopTrail),
        ('trailamount', 0.0),
        ('trailpercent', 0.02),
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('percK', 20),
        ('kdPercK',20),
        ('kdPercD',20),
        ('rsiShort',9)
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
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
        # self.sma = btind.SimpleMovingAverage(self.data, period=self.p.maperiod)
        self.macd = bt.indicators.MACD(self.data)
        self.psar = bt.indicators.ParabolicSAR(self.data)
        self.kd = bt.indicators.StochasticFull(self.data)
        self.rsiShort = bt.indicators.RelativeStrengthIndex(self.data,period=self.p.rsiShort)
        # self.rsi12 = bt.indicators.RelativeStrengthIndex(self.data,period=12)

        # self.percKCrossoverPercD = bt.indicators.CrossOver(self.kd.lines.percK, self.kd.lines.percD)
        # self.percKCrossDownPercD = bt.indicators.CrossDown(self.kd.lines.percK, self.kd.lines.percD)
        # self.rsiCrossUp = bt.indicators.CrossUp(self.rsi6, self.rsi12)

        self.buysingal = bt.And(
            self.macd.lines.macd > self.macd.lines.signal,
            self.kd.lines.percK < 20,
            self.kd.lines.percD < 20,
            # bt.indicators.CrossUp(self.kd.lines.percD, self.kd.lines.percK),
            self.rsiShort.lines.rsi < 30, #RSI below 30, under buy, short turn use 9, long use 14
            self.dataclose > self.psar.lines.psar
            
            # self.rsiCrossUp,
        )

        self.sellsignal = bt.And(
            # self.percKCrossDownPercD,
            # self.kd.lines.percK < 80,
            # self.macd.lines.macd < self.macd.lines.signal,
            self.kd.lines.percD > 80,
            self.kd.lines.percK > 80,
            # bt.indicators.CrossDown(self.kd.lines.percD, self.kd.lines.percK),
            self.rsiShort.lines.rsi > 70, #RSI over 70, over buy
            self.dataclose < self.psar.lines.psar
        )

    def notify_order(self, order):
        # self.log('An order new/changed/executed/canceled has been received')
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
        # Simply log the closing price of the series from the reference
        # self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.buysingal:

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        else:

            if self.sellsignal:
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

        # elif self.order is None:
        #     self.log('SELL CREATE Stop lose, %.2f' % self.dataclose[0])
        #     self.order = self.sell(exectype=self.p.stoptype,
        #                            trailamount=self.p.trailamount,
        #                            trailpercent=self.p.trailpercent)

        #     if self.p.trailamount:
        #         tcheck = self.data.close - self.p.trailamount
        #     else:
        #         tcheck = self.data.close * (1.0 - self.p.trailpercent)
        # else:
        #     if self.p.trailamount:
        #         tcheck = self.data.close - self.p.trailamount
        #     else:
        #         tcheck = self.data.close * (1.0 - self.p.trailpercent)
        #     print(','.join(
        #         map(str, [self.datetime.date(), self.data.close[0],
        #                   self.order.created.price, tcheck])
        #     )
        #     )

    def stop(self):
        self.log('(KD Period %2d)  (KD percK %2d) (KD percD %2d) Ending Value %.2f' %
                 (self.params.kdPeriod, self.params.kdPercK, self.params.kdPercD, self.broker.getvalue()), doprint=True)


if __name__ == '__main__':
    try:
        # Create a cerebro entity
        cerebro = bt.Cerebro()

        # Add a strategy
        # strats = cerebro.optstrategy(TestStrategy,kdPeriod=range(3, 10), kdPercK=range(10,30,5),kdPercD=range(10,30,5))
        cerebro.addstrategy(TestStrategy)
        # Datas are in a subfolder of the samples. Need to find where the script is
        # because it could have been called from anywhere
        modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
        datapath = os.path.abspath(
            os.getcwd() + '/' + cfg.currency['currency'] + '_' + str(datetime.datetime.now().strftime("%Y_%m_%d")))

        # Create a Data Feed
        data = bt.feeds.GenericCSVData(
            dataname=datapath,
            fromdate=datetime.datetime(2018, 1, 1),
            todate=datetime.datetime(2018, 12, 31),
            dtformat=('%Y-%m-%d %H:%M:%S'),
            datetime=0,
            high=2,
            low=3,
            open=1,
            close=4,
            volume=5,
            openinterest=-1,
            timeframe=bt.TimeFrame.Minutes,
            compression=1
        )

        # Add the Data Feed to Cerebro
        cerebro.adddata(data)

        # Set our desired cash start
        cerebro.broker.setcash(500.0)

        # Add a FixedSize sizer according to the stake
        cerebro.addsizer(bt.sizers.PercentSizer, percents=90)

        # Set the commission
        cerebro.broker.setcommission(commission=0.00075)

        # Print out the starting conditions
        print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Run over everything
        cerebro.run()

        # Print out the final result
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

        # Plot the result
        cerebro.plot()
    except Exception as ex:
        print(ex)
