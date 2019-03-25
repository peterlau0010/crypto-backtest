import config as cfg 
import pandas as pd
import datetime
from binance.client import Client

client = Client(cfg.binanceKey['api_key'], cfg.binanceKey['api_secret'])

symbol ='BNBUSDT'

cryptocurrency = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")

cryptocurrency = pd.DataFrame(cryptocurrency, columns=['Open Time','Open','High','Low','Close','Volumn','Close time','Quote asset volume','Number of trades','Taker buy base asset volume','Taker buy quote asset volume','Ignore'])

cryptocurrency['Open Time'] = pd.to_datetime(cryptocurrency['Open Time'],unit='ms')

cryptocurrency.set_index('Open Time', inplace=True)

cryptocurrency.to_csv( str(symbol) + '_'+ str(datetime.datetime.now().strftime('%Y_%m_%d')), date_format='%Y-%m-%d %H:%M:%S')