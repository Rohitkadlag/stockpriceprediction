import math
import numpy as np
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from pandas_datareader import data as pdr
from sklearn.preprocessing import MinMaxScaler
from keras.layers import Dense, Dropout
from keras.models import Sequential

# Initialize yfinance
yf.pdr_override()

# Load the model
model = Sequential()
model.add(Dense(64, input_shape=(60,)))
model.add(Dropout(0.2))
model.add(Dense(64, activation='relu'))
model.add(Dropout(0.2))
model.add(Dense(1, activation='linear'))
model.compile(optimizer='adam', loss='mean_squared_error')
model.load_weights('future_fnn_model.h5')  # Replace with your model weights file

# Function to make future predictions
def make_future_predictions(seed_sequence, n_future_predictions):
    future_predictions = []
    for _ in range(n_future_predictions):
        next_value = model.predict(np.array([seed_sequence]))[0][0]
        future_predictions.append(next_value)
        seed_sequence = np.append(seed_sequence[1:], next_value)
    return future_predictions

# Streamlit app
st.set_page_config(page_title="Interactive Stock Price Prediction", layout="wide")
st.title('Stock Price Prediction')

# Sidebar for user input
st.sidebar.header('Settings')
start_date = st.sidebar.date_input('Start Date', pd.to_datetime('2022-09-01'))
end_date = st.sidebar.date_input('End Date', pd.to_datetime('2023-11-03'))
n_future_predictions = st.sidebar.number_input('Number of Future Predictions', min_value=1, value=5, step=1)

# Add a dropdown menu for stock symbol selection
stock_symbol = st.sidebar.text_input('Stock Symbol (e.g., GOOG)', 'AAPL')

# Button to make predictions
if st.sidebar.button('Make Predictions'):
    # Retrieve historical stock data for the selected symbol
    df = pdr.get_data_yahoo(stock_symbol, start=start_date, end=end_date)
    st.write('Historical Stock Data:')
    st.write(df)
    
    # Prepare input data for prediction
    data = df.filter(['Close'])
    dataset = data.values
    
    if len(dataset) == 0:
        st.error('Insufficient data for predictions. Please select a different date range or stock symbol.')
    else:
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(dataset)

        training_data_len = math.ceil(len(dataset) * 0.8)
        test_data = scaled_data[training_data_len - 60:, :]

        x_test = []
        for i in range(60, len(test_data)):
            x_test.append(test_data[i-60:i, 0])
        x_test = np.array(x_test)
        x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

        # Make future predictions
        seed_sequence = x_test[-1]
        future_predictions = make_future_predictions(seed_sequence, n_future_predictions)

        # Inverse transform predictions
        future_predictions = scaler.inverse_transform(np.array(future_predictions).reshape(-1, 1))

        # Create future dates (excluding the start date)
        future_dates = pd.date_range(start=df.index[-1] + pd.DateOffset(days=1), periods=n_future_predictions)
        future_df = pd.DataFrame(data=future_predictions, index=future_dates, columns=['Predictions'])

        # Display future predictions
        st.markdown("## Future Predictions")
        st.write('Future Predictions:')
        st.write(future_df)

        # Create Matplotlib figure for combined historical data and future predictions
        fig_combined, ax_combined = plt.subplots(figsize=(12, 6))
        ax_combined.set_title('Historical Data and Future Predictions')
        ax_combined.set_xlabel('Time')
        ax_combined.set_ylabel('Close Price USD')
        ax_combined.plot(df.index, df['Close'], label='Historical Data', linestyle='-')
        ax_combined.plot(future_df.index, future_predictions, label='Future Predictions', linestyle='--')
        ax_combined.legend(loc='lower right')

        # Replace the usage of st.pyplot() to display combined plot
        st.markdown("## Historical Data and Future Predictions")
        st.pyplot(fig_combined)
