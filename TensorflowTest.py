# Importing the libraries
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from keras.models import load_model
import math
from numpy import array

dataset = pd.read_csv('BNBUSDT_2019_04_09', index_col="Open Time",
                      parse_dates=True, engine='python', usecols=[0, 4],)
# plt.plot(dataset)
# plt.show()

# fix random seed for reproducibility
np.random.seed(7)

# load the dataset
dataframe = pd.read_csv('BNBUSDT_2019_04_09', index_col="Open Time",
                        parse_dates=True, engine='python', usecols=[0, 4],)
dataset = dataframe.values
dataset = dataset.astype('float32')

# normalize the dataset
scaler = MinMaxScaler(feature_range=(0, 1))
dataset = scaler.fit_transform(dataset)

# split into train and test sets
train_size = int(len(dataset) * 1)
test_size = len(dataset) - train_size
train, test = dataset[0:train_size, :], dataset[train_size:len(dataset), :]
print(len(train), len(test))

# convert an array of values into a dataset matrix


def create_dataset(dataset, look_back=1):
    dataX, dataY = [], []
    for i in range(len(dataset)-look_back-1):
        a = dataset[i:(i+look_back), 0]
        dataX.append(a)
        dataY.append(dataset[i + look_back, 0])
    return np.array(dataX), np.array(dataY)

# reshape into X=t and Y=t+1
look_back = 5
trainX, trainY = create_dataset(train, look_back)
# testX, testY = create_dataset(test, look_back)

# reshape input to be [samples, time steps, features]

trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
print('trainX 1 ', np.shape(trainX))
# testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

# create and fit the LSTM network
model = Sequential()
model.add(LSTM(4, input_shape=(1, look_back)))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(trainX, trainY, epochs=5, batch_size=1, verbose=2)

# save model for later use
# model.save('./savedModel')

# load_model
# model = load_model('./savedModel')

# make predictions
# print('trainX 2', np.shape(trainX))
trainPredict = model.predict(trainX)
print('trainPredict', np.shape(trainPredict))
trainPredict = scaler.inverse_transform(trainPredict)
trainY = scaler.inverse_transform([trainY])
trainScore = math.sqrt(mean_squared_error(trainY[0], trainPredict[:, 0]))
print('Train Score: %.2f RMSE' % (trainScore))
print(trainPredict[-1:])

yhat = model.predict(trainX, verbose=0)
yhat = scaler.inverse_transform(yhat)
print(yhat[-1:])

# testPredict = model.predict(testX)
# invert predictions


# testPredict = scaler.inverse_transform(testPredict)
# testY = scaler.inverse_transform([testY])
# calculate root mean squared error

# testScore = math.sqrt(mean_squared_error(testY[0], testPredict[:,0]))
# print('Test Score: %.2f RMSE' % (testScore))

# realPrice = scaler.inverse_transform(dataset)
# print('trainPredict', np.shape(trainPredict))
# print(trainPredict[-5:])
# print('realPrice', np.shape(realPrice))
# print(realPrice[-5:])

# furtherX = scaler.fit_transform(trainPredict)
# print('furtherX 1', np.shape(furtherX))
# furtherX = np.reshape(furtherX, (furtherX.shape[0], 1, 1))
# print('furtherX 2', np.shape(furtherX))
# furtherPrice = model.predict(furtherX, verbose=0)
# print('furtherPrice', np.shape(furtherPrice))
# furtherPrice = scaler.inverse_transform(furtherPrice)
# print(furtherPrice[-5:])

# shift train predictions for plotting
trainPredictPlot = np.empty_like(dataset)
trainPredictPlot[:, :] = np.nan
trainPredictPlot[look_back:len(trainPredict)+look_back, :] = trainPredict
# # # shift test predictions for plotting
# # testPredictPlot = np.empty_like(dataset)
# # testPredictPlot[:, :] = np.nan
# # testPredictPlot[len(trainPredict)+(look_back*2)+1:len(dataset)-1, :] = testPredict

# # # shift test predictions for plotting
# furtherPricePlot = np.empty_like(dataset)
# furtherPricePlot[:, :] = np.nan
# furtherPricePlot[look_back:len(trainPredict)+look_back, :] = furtherPrice

# # plot baseline and predictions
plt.plot(scaler.inverse_transform(dataset))
plt.plot(trainPredictPlot)
# plt.plot(furtherPricePlot)
# # plt.plot(testPredictPlot)
plt.show()
