from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import os.path  # To manage paths
import backtrader as bt
# config
import config as cfg

class St(bt.Strategy):
    params = dict(
        ma=bt.ind.SMA,
        p1=10,
        p2=30,
        stoptype=bt.Order.StopTrail,
        trailamount=0.0,
        trailpercent=0.00,
        printlog=True,
    )

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # self.dataclose = self.datas[0].close
        self.order = None
        self.previousbuyprice=None
        self.kd = bt.indicators.StochasticFull(self.data,period=5, safediv=True)
        self.macd = bt.indicators.MACD(self.data)
        self.rsiShort = bt.indicators.RelativeStrengthIndex(self.data,period=9)
        self.emaShort = bt.indicators.ExponentialMovingAverage(self.data,period=50)
        self.emaLong = bt.indicators.ExponentialMovingAverage(self.data,period=100)
        self.buysingal = bt.And(
            self.macd.lines.macd > self.macd.lines.signal,
            self.kd.lines.percK < 20,
            self.kd.lines.percD < 20,
            self.kd.lines.percK > self.kd.lines.percD,
            # EMA
            self.emaShort>self.emaLong,
            # bt.indicators.CrossUp(self.kd.lines.percD, self.kd.lines.percK),
            self.rsiShort.lines.rsi < 20, #RSI below 30, over sell, short turn use 9, long use 14
            # self.dataclose > self.psar.lines.psar
            
            # self.rsiCrossUp,
        )

        self.sellsingal = bt.And(
            # self.emaShort < self.emaLong,
            # self.percKCrossDownPercD,
            # self.kd.lines.percK > 80,
            # self.macd.lines.macd < self.macd.lines.signal,
            # self.kd.lines.percD > 85,
            # self.kd.lines.percK > 85,
            # bt.indicators.CrossDown(self.kd.lines.percD, self.kd.lines.percK),
            self.rsiShort.lines.rsi > 70, #RSI over 70, over buy
            # self.dataclose < self.psar.lines.psar
        )
    # def stop(self):
    #     self.log('(KD Period %2d)  (KD percK %2d) (KD percD %2d) Ending Value %.2f' %
    #              (self.params.kdPeriod, self.params.kdPercK, self.params.kdPercD, self.broker.getvalue()), doprint=True)
    def notify_order(self, order):
        # self.log('An order new/changed/executed/canceled has been received')
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.previousbuyprice=order.executed.price
                # self.log(
                #     'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #     (order.executed.price,
                #      order.executed.value,
                #      order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            # else:  # Sell
                # self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                #          (order.executed.price,
                #           order.executed.value,
                #           order.executed.comm))

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
        if not self.position:
            if self.buysingal:
                if self.rsiShort[0] > self.rsiShort[-1]:
                    if self.kd.lines.percK[0] > self.kd.lines.percK[-1]:
                        # print('Buy singal')
                        o = self.buy()
                        self.order = None
                # print('*' * 50)
        elif self.order is None:
            if self.sellsingal:
                print('Sell singal')
                self.order = self.sell()
            else:
                print('Sell stop limit')
                # self.order = self.sell(price=self.previousbuyprice, exectype=self.p.stoptype,trailamount=self.p.trailamount, trailpercent=self.p.trailpercent)
                self.order = self.sell(exectype=self.p.stoptype,trailamount=self.p.trailamount, trailpercent=self.p.trailpercent)

            if self.p.trailamount:
                tcheck = self.data.close - self.p.trailamount
            else:
                tcheck = self.data.close * (1.0 - self.p.trailpercent)
        else:
            if self.p.trailamount:
                tcheck = self.data.close - self.p.trailamount
            else:
                tcheck = self.data.close * (1.0 - self.p.trailpercent)


def runstrat(args=None):
    args = parse_args(args)

    cerebro = bt.Cerebro()

    # Data feed kwargs
    kwargs = dict()

    # Parse from/to-date
    dtfmt, tmfmt = '%Y-%m-%d', 'T%H:%M:%S'
    for a, d in ((getattr(args, x), x) for x in ['fromdate', 'todate']):
        if a:
            strpfmt = dtfmt + tmfmt * ('T' in a)
            kwargs[d] = datetime.datetime.strptime(a, strpfmt)

    # Data feed
    datapath = os.path.abspath(
    os.getcwd() + '/' + cfg.currency['currency'] + '_' + str(datetime.datetime.now().strftime("%Y_%m_%d")))
    # data0 = bt.feeds.BacktraderCSVData(dataname=args.data0, **kwargs)
    data0 = bt.feeds.GenericCSVData(
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
    cerebro.adddata(data0)

    # Broker
    cerebro.broker = bt.brokers.BackBroker(**eval('dict(' + args.broker + ')'))

    # Sizer
    # cerebro.addsizer(bt.sizers.FixedSize, **eval('dict(' + args.sizer + ')'))

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.PercentSizer, percents=50)

    # Set the commission
    cerebro.broker.setcommission(commission=0.00075)

    # Strategy
    cerebro.addstrategy(St, **eval('dict(' + args.strat + ')'))
    
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())
    # Execute
    cerebro.run(**eval('dict(' + args.cerebro + ')'))

    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    if args.plot:  # Plot if requested to
        cerebro.plot(**eval('dict(' + args.plot + ')'))


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=(
            'StopTrail Sample'
        )
    )

    parser.add_argument('--data0', default='../../datas/2005-2006-day-001.txt',
                        required=False, help='Data to read in')

    # Defaults for dates
    parser.add_argument('--fromdate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--todate', required=False, default='',
                        help='Date[time] in YYYY-MM-DD[THH:MM:SS] format')

    parser.add_argument('--cerebro', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--broker', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--sizer', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--strat', required=False, default='',
                        metavar='kwargs', help='kwargs in key=value format')

    parser.add_argument('--plot', required=False, default='',
                        nargs='?', const='{}',
                        metavar='kwargs', help='kwargs in key=value format')

    return parser.parse_args(pargs)


if __name__ == '__main__':
    runstrat()