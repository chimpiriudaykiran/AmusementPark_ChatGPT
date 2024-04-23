import pickle

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error

day_mapping = {
    "Sunday": 0,
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6
}

# Load dataset
df = pd.read_excel("amusement_park_ride_data.xlsx")

df['Time'] = pd.to_datetime(df['Time'])
df['Time_minutes'] = df['Time'].dt.hour * 60 + df['Time'].dt.minute
df.drop(columns=["Date"], inplace=True)
df.drop(columns=["Time"], inplace=True)

# Convert categorical variables to numerical
df["Day"] = df["Day"].map(day_mapping)

# Split data into features and target variable
X = df.drop(columns=["Wait Time"])
y = df["Wait Time"]

# Split dataset into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize Random Forest Regressor model
model = RandomForestRegressor()

# Train the model
model.fit(X_train, y_train)

# Predict on the testing set
y_pred = model.predict(X_test)

# Evaluate the model
mse = mean_squared_error(y_test, y_pred)
print("Mean Squared Error:", mse)

filename = 'WaitTimeModel.model'
pickle.dump(model, open(filename, 'wb'))