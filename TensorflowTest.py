# %%
import matplotlib.pyplot as plt
from keras.layers import LSTM
from keras.layers import Dense
from keras.models import Sequential
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
import config as cfg
import pandas as pd
import datetime
from binance.client import Client
import math
# %matplotlib inline


# client = Client(cfg.binanceKey['api_key'], cfg.binanceKey['api_secret'])
# symbol = cfg.currency['currency']
# cryptocurrency = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1DAY, "1 Jan, 2018 UTC", "1 Jan, 2019")
# cryptocurrency = pd.read_csv('BNBUSDT_2019_04_08', engine='python')
# cryptocurrency = pd.DataFrame(cryptocurrency, columns=['Open Time', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Close time',
                                                    #    'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
# cryptocurrency['Open Time'] = pd.to_datetime(
# cryptocurrency['Open Time'], unit='ms')
# cryptocurrency.set_index('Open Time', inplace=True)
# cryptocurrency['Close'] = cryptocurrency['Close'].astype(float)
# cryptocurrency['Close'].plot(figsize=(20, 10), title='1 year price')

# data = cryptocurrency.iloc[:, 3:4].astype(float).values


# scaler = MinMaxScaler()

# data = scaler.fit_transform(data)

# training_set = data[:int((len(data)/2))]
# test_set = data[int((len(data))/2):]
# # training_set = data[:8600]
# # test_set = data[8600:]

# X_train = training_set[0:len(training_set) - 1]
# y_train = training_set[1:len(training_set)]

# X_test = test_set[0:len(test_set)-1]
# y_test = test_set[1:len(test_set)]


# X_train = np.reshape(X_train, (len(X_train), 1, X_train.shape[1]))
# X_test = np.reshape(X_test, (len(X_test), 1, X_test.shape[1]))


# model = Sequential()
# model.add(LSTM(256, return_sequences=True, input_shape=(
#     X_train.shape[1], X_train.shape[2])))

# model.add(LSTM(256))
# model.add(Dense(1))
# model.compile(loss='mean_squared_error', optimizer='adam')
# model.fit(X_train, y_train, epochs=50, batch_size=16, shuffle=False)
# # print(X_test)
# predicted_price = model.predict(X_test)
# # print(predicted_price)
# predicted_price = scaler.inverse_transform(predicted_price)
# real_price = scaler.inverse_transform(y_test)


# print('Price for last 5 : ')
# print(predicted_price[-5:])
# future_price = model.predict(np.asarray([[predicted_price[-1]]]))
# future_price = scaler.inverse_transform(future_price)
# print('Next price is ', future_price)

# plt.figure(figsize=(20, 8))
# plt.plot(predicted_price, color='red', label='Predicted Price')
# plt.plot(real_price, color='blue', label='Real Price')
# # plt.plot(future_price, color='green', label='Future Price')
# plt.title('Predicted vs. Real Price')
# plt.xlabel('Time')
# plt.ylabel('Price')
# plt.show()
# normalize the dataset

# convert an array of values into a dataset matrix
def create_dataset(dataset):
    dataX, dataY = [], []
    for i in range(len(dataset)-1):
        dataX.append(dataset[i])
        dataY.append(dataset[i + 1])
    return np.asarray(dataX), np.asarray(dataY)


# fix random seed for reproducibility
np.random.seed(7)

# load the dataset
df = pd.read_csv('BNBUSDT_2019_04_08', engine='python')
df.set_index('Open Time', inplace=True)
df['Close'] = df['Close'].astype(float)
# df = df.iloc[::-1]
# df = df.drop(['Open Time', 'Open', 'High', 'Low',
            #   'Volumn', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'], axis=1)
# dataset = df.values
dataset = df.iloc[:, 3:4].astype(float).values

scaler = MinMaxScaler(feature_range=(0, 1))
dataset = scaler.fit_transform(dataset)

# prepare the X and Y label
X, y = create_dataset(dataset)

# Take 80% of data as the training sample and 20% as testing sample
trainX, testX, trainY, testY = train_test_split(
    X, y, test_size=0.20, shuffle=False)

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

# create and fit the LSTM network
# model = Sequential()
# model.add(LSTM(4, input_shape=(1, 1)))
# model.add(Dense(1))
# model.compile(loss='mean_squared_error', optimizer='adam')
model = Sequential()
model.add(LSTM(256, return_sequences=True, input_shape=(
    trainX.shape[1], trainX.shape[2])))

model.add(LSTM(256))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(trainX, trainY, epochs=5, batch_size=1, verbose=2)

# save model for later use
model.save('./savedModel')

# load_model
# model = load_model('./savedModel')

# make predictions
trainPredict = model.predict(trainX)
testPredict = model.predict(testX)

futurePredict = model.predict(np.asarray([[testPredict[-1]]]))
futurePredict = scaler.inverse_transform(futurePredict)

# invert predictions
trainPredict = scaler.inverse_transform(trainPredict)
trainY = scaler.inverse_transform(trainY)
testPredict = scaler.inverse_transform(testPredict)
testY = scaler.inverse_transform(testY)

realPrice = scaler.inverse_transform(dataset)

print("Price for last 5 days: ")
print(testPredict[-5:])
print(realPrice[-5:])
print("Bitcoin price for tomorrow: ", futurePredict)

# calculate root mean squared error
trainScore = math.sqrt(mean_squared_error(trainY[:, 0], trainPredict[:, 0]))
print('Train Score: %.2f RMSE' % (trainScore))
testScore = math.sqrt(mean_squared_error(testY[:, 0], testPredict[:, 0]))
print('Test Score: %.2f RMSE' % (testScore))

# shift train predictions for plotting
trainPredictPlot = np.empty_like(dataset)
trainPredictPlot[:, :] = np.nan
trainPredictPlot[1:len(trainPredict)+1, :] = trainPredict

# shift test predictions for plotting
testPredictPlot = np.empty_like(dataset)
testPredictPlot[:, :] = np.nan
testPredictPlot[len(trainPredict):len(dataset)-1, :] = testPredict

# plot baseline and predictions
plt.plot(scaler.inverse_transform(dataset))
# plt.plot(trainPredictPlot)
plt.plot(testPredictPlot)
plt.show()
