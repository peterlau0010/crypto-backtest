# %%
import matplotlib.pyplot as plt
from keras.layers import LSTM
from keras.layers import Dense
from keras.models import Sequential
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import config as cfg
import pandas as pd
import datetime
from binance.client import Client
# %matplotlib inline


# client = Client(cfg.binanceKey['api_key'], cfg.binanceKey['api_secret'])
# symbol = cfg.currency['currency']
# cryptocurrency = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "1 Jan, 2018 UTC", "1 Jan, 2019")
cryptocurrency = pd.read_csv('BTCUSDT_2019_04_05', engine='python')
cryptocurrency = pd.DataFrame(cryptocurrency, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Close time',
                                                       'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
# cryptocurrency['Open Time'] = pd.to_datetime(
# cryptocurrency['Open Time'], unit='ms')
cryptocurrency.set_index('Open Time', inplace=True)
cryptocurrency['Close'] = cryptocurrency['Close'].astype(float)
cryptocurrency['Close'].plot(figsize=(20, 10), title='1 year price')

data = cryptocurrency.iloc[:, 3:4].astype(float).values


scaler = MinMaxScaler()

data = scaler.fit_transform(data)

# training_set = data[:int((len(data)/2))]
# test_set = data[int((len(data))/2):]
training_set = data[:8600]
test_set = data[8600:]

X_train = training_set[0:len(training_set) - 1]
y_train = training_set[1:len(training_set)]

X_test = test_set[0:len(test_set)-1]
y_test = test_set[1:len(test_set)]


X_train = np.reshape(X_train, (len(X_train), 1, X_train.shape[1]))
X_test = np.reshape(X_test, (len(X_test), 1, X_test.shape[1]))


model = Sequential()
model.add(LSTM(256, return_sequences=True, input_shape=(
    X_train.shape[1], X_train.shape[2])))

model.add(LSTM(256))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(X_train, y_train, epochs=10, batch_size=16, shuffle=False)
# print(X_test)
predicted_price = model.predict(X_test)
# print(predicted_price)
predicted_price = scaler.inverse_transform(predicted_price)
real_price = scaler.inverse_transform(y_test)


print('Price for last 5 : ')
print(predicted_price[-5:])
future_price = model.predict(np.asarray([[predicted_price[-1]]]))
future_price = scaler.inverse_transform(future_price)
print('Next price is ', future_price)

plt.figure(figsize=(20, 8))
plt.plot(predicted_price, color='red', label='Predicted Price')
plt.plot(real_price, color='blue', label='Real Price')
# plt.plot(future_price, color='green', label='Future Price')
plt.title('Predicted vs. Real Price')
plt.xlabel('Time')
plt.ylabel('Price')
plt.show()
