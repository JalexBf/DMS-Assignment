import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_error
import matplotlib.pyplot as plt

# Load the dataset from the CSV file
dataset = pd.read_csv('File_series.csv')
dataset['date'] = pd.to_datetime(dataset['date'])
dataset.set_index('date', inplace=True)
dataset = dataset.asfreq('D')

# Split the dataset into training and testing sets
train_size = int(len(dataset) * 0.76)
train_data, test_data = dataset[:train_size], dataset[train_size:]

# Train the ARIMA model
model = ARIMA(train_data['price'], order=(1, 0, 0))
model_fit = model.fit()

# Make predictions on the training set
predictions = model_fit.predict(start=train_data.index[0], end=train_data.index[-1])

# Predict the lowest price for the next day
next_day = dataset.index[-1] + pd.DateOffset(days=1)
next_day_prediction = model_fit.forecast(steps=1)

# Print the predicted lowest price for the next day
print('Predicted lowest price for the next day:', next_day_prediction[0])

# Evaluate the model's performance on the training set
mse = mean_squared_error(train_data['price'], predictions)
mae = mean_absolute_error(train_data['price'], predictions)

# Print the evaluation metrics
print("Mean Squared Error (MSE) on training set:", mse)
print("Mean Absolute Error (MAE) on training set:", mae)

# Visualize the actual prices and predicted prices
plt.figure(figsize=(10, 6))
plt.plot(train_data.index, train_data['price'], label='Actual Prices')
plt.plot(train_data.index, predictions, label='Predicted Prices')
plt.title('Actual Prices vs. Predicted Prices')
plt.xlabel('Date')
plt.ylabel('Price')
plt.legend()
plt.show()
