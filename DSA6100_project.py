# -*- coding: utf-8 -*-
"""DSA6100_PROJECT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1gywEF7PshqiEBGg0yfBela55nzspgNvz

IMPORT ALL LIBRARIES
"""

import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import RobustScaler, StandardScaler
from datetime import datetime
import math
from xgboost import XGBRegressor
import xgboost as xgb
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Ridge, RidgeCV, Lasso, LassoCV, LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.model_selection import cross_val_score, KFold, RepeatedKFold, learning_curve
from sklearn.metrics import accuracy_score, f1_score, r2_score, precision_score, recall_score, classification_report, confusion_matrix
from yellowbrick.datasets import load_concrete
from yellowbrick.regressor import ResidualsPlot

pip install yellowbrick

"""LOAD AND SPLIT THE DATA"""

# First, let's load the data
df = pd.read_csv('/content/Zillow_Analysis/Real estate1.csv')

df.head()

# Remove the id column
df.drop('No', inplace=True, axis=1)

# Rename the columns (remove X1..X2..X3.. and Y)
df.columns = ['transaction date', 'house age', 'distance to the nearest MRT station', 'number of convenience stores', 'latitude', 'longitude', 'house price of unit area']
df.head()

# Split the data into train and test
train_data, test_data = train_test_split(df, test_size=0.2, random_state=1)

print("Train set size:",len(train_data))
print("Test set size:",len(test_data))

"""UNDERSTANDING THE DATA"""

train_data.head()

train_data.info()

train_data.describe()

"""VISUALIZATION OF FEATURES AGAINST PRICE"""

fig, ax = plt.subplots(2, 3, figsize=(20, 9))
ax = ax.flatten()

sns.set()
sns.lineplot(data=train_data, x="transaction date", y="house price of unit area", ax=ax[0])
ax[0].set_title("Price of Unit Area vs. Transaction Date")

sns.lineplot(data=train_data, x="house age", y="house price of unit area", ax=ax[1])
ax[1].set_title("Price of Unit Area vs. House Age")

sns.lineplot(data=train_data, x="distance to the nearest MRT station", y="house price of unit area", ax=ax[2])
ax[2].set_title("Price of Unit Area vs. Distance to the nearest MRT station")

sns.lineplot(data=train_data, x="number of convenience stores", y="house price of unit area", ax=ax[3])
ax[3].set_title("Price of Unit Area vs. no. of Convenience Stores")

sns.lineplot(data=train_data, x="latitude", y="house price of unit area", ax=ax[4])
ax[4].set_title("Price of Unit Area vs. Latitude")

sns.lineplot(data=train_data, x="longitude", y="house price of unit area", ax=ax[5])
ax[5].set_title("Price of Unit Area vs. Longitude")

# set the spacing between subplots
plt.subplots_adjust(left=0.1,
                    bottom=0.1,
                    right=0.9,
                    top=0.9,
                    wspace=0.4,
                    hspace=0.4)
plt.show();

"""It is obvious that the cost of housing per square foot is *proportional* to the number of convenience stores.
We can also see that the price of a unit is *higher* the closer a home is to the nearest MRT station.
The price of the unit area will increase the *more* convenience stores there are close to the home.
Unexpectedly, the house age and price per square foot are *not proportional,* yet we can still identify a trend and a clear outlier.
Longitude and latitude show a pattern, but further investigation is required.

*DATA PREPARATION*
"""

# Histograms
fig = plt.figure(figsize=(16,16))
for index,col in enumerate(train_data):
    plt.subplot(6,3,index+1)
    sns.histplot(train_data.loc[:,col].dropna(), kde=True, stat="density", linewidth=0.5);
fig.tight_layout(pad=1.0);

# Check outliers
fig = plt.figure(figsize=(14,15))
for index,col in enumerate(train_data):
    plt.subplot(6,3,index+1)
    sns.boxplot(y=col, data=train_data.dropna())
    plt.grid()
fig.tight_layout(pad=1.0)

"""It is evident that there are glaring outliers in:
housing cost per square foot, longitude, and the distance to the closest MRT station
"""

train_data = train_data[train_data['house price of unit area']<80]
train_data = train_data[train_data['distance to the nearest MRT station']<3000]
train_data = train_data[train_data['longitude']>121.50]

# Check outliers
# Histograms
fig = plt.figure(figsize=(16,16))
for index,col in enumerate(train_data):
    plt.subplot(6,3,index+1)
    sns.histplot(train_data.loc[:,col].dropna(), kde=True, stat="density", linewidth=0.5);
fig.tight_layout(pad=1.0);

# Corr to price of unit area
numeric_train = train_data
correlation = numeric_train.corr()
correlation[['house price of unit area']].sort_values(['house price of unit area'], ascending=False)

# correlation plot (heatmap)
corr = train_data.corr()
sns.heatmap(corr, cmap = 'YlGnBu', annot= True, linewidths=.5);

"""Data Preprocessing"""

train_data.head()

# Concat to perform preprocessing and scaling
dfs = [train_data, test_data]
data = pd.concat(dfs)

def to_date(data):
    # STEP 1: Convert transaction date to day, month and year columns
    # Create date column with `transaction date` as a date
    data['date'] = pd.to_datetime(data['transaction date'], format='%Y')

    # Create year column
    data['year'] = pd.DatetimeIndex(data['date']).year

    # Create month column by extracting the decimal part of `transaction date` and multiplying it by 12
    data['month'], data['year1'] = data['transaction date'].apply(lambda x: math.modf(x)).str
    data['month'] = data['month']*12

    # Create day column by extracting the decimal part of int
    data['day'], data['month'] = data['month'].apply(lambda x: math.modf(x)).str

    # Convert month to int
    data['month'] = (data['month']).astype(int)

    # Multiply `day` column by 30 + 1 to convert it to days
    data['day'] = (data['day']*30+1).astype(int)

    # Drop unnecessary columns
    data = data.drop(['transaction date', 'date', 'year1'], axis=1, inplace=True)

to_date(data)

"""scaling the features"""

# Split the data into X and y
X=data.drop('house price of unit area',axis=1)
y=data['house price of unit area']

# Standardize features by removing the mean and scaling to unit variance.
# The standard score of a sample x is calculated as:
#       z = (x - u) / s
transformer = StandardScaler().fit(X)
X_prep = transformer.transform(X)

# Polynomial Features
polynomial_converter = PolynomialFeatures(degree=2, include_bias=False)

# Fit and transform
poly_features = polynomial_converter.fit(X_prep)
poly_features = polynomial_converter.transform(X_prep)

poly_features.shape

"""DATA MODELING:
Split the data into X & Y
"""

# SPLIT THE DATA
X_train, X_test, y_train, y_test = train_test_split(poly_features, y, test_size=0.2, random_state=1)

X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.25, random_state=1)

# Fit the model
model_poly = LinearRegression()
model_poly.fit(X_train, y_train)

# Predict on train data
pred_train_poly = model_poly.predict(X_train)

r2_train_poly = r2_score(y_train, pred_train_poly)
mse_train_poly = mean_squared_error(y_train, pred_train_poly)
rmse_train_poly = np.sqrt(mse_train_poly)
mae_train_poly = mean_absolute_error(y_train, pred_train_poly)

# Predict on validation data
pred_val_poly = model_poly.predict(X_val)

r2_val_poly = r2_score(y_val, pred_val_poly)
mse_val_poly = mean_squared_error(y_val, pred_val_poly)
rmse_val_poly = np.sqrt(mse_val_poly)
mae_val_poly = mean_absolute_error(y_val, pred_val_poly)

pd.DataFrame({'Validation':  [r2_val_poly, mse_val_poly, rmse_val_poly, mae_val_poly],
               'Training': [r2_train_poly, mse_train_poly, rmse_train_poly, mae_train_poly],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

# Finally, predict on test data
pred_test_poly = model_poly.predict(X_test)

r2_test_poly = r2_score(y_test, pred_test_poly)
mse_test_poly = mean_squared_error(y_test, pred_test_poly)
rmse_test_poly = np.sqrt(mse_test_poly)
mae_test_poly = mean_absolute_error(y_test, pred_test_poly)

print('R2 Score: ', r2_test_poly)
print('MSE: ', mse_test_poly)
print('RMSE: ', rmse_test_poly)
print('MAE: ', mae_test_poly)

visualizer = ResidualsPlot(model_poly, hist=False, qqplot=True)
visualizer.fit(X_train, y_train)
visualizer.score(X_test, y_test)
visualizer.show();

pd.DataFrame({'Y_Test': y_test,'Y_Pred':pred_test_poly, 'Residuals':(y_test-pred_test_poly) }).head(5)

plt.scatter(y_test, pred_test_poly)
plt.xlabel('Real')
plt.ylabel('Pred')
plt.title('Polynomial Reg pred against real')
plt.show()

# XGBRegressor
# Fit the model
model_xgbr = XGBRegressor(objective ='reg:squarederror', n_estimators = 10, seed = 0, max_depth = 3)

model_xgbr.fit(X_train, y_train)

# Predict on train data
pred_train_xgbr = model_xgbr.predict(X_train)

r2_train_xgbr = r2_score(y_train, pred_train_xgbr)
mse_train_xgbr = mean_squared_error(y_train, pred_train_xgbr)
rmse_train_xgbr = np.sqrt(mse_train_xgbr)
mae_train_xgbr = mean_absolute_error(y_train, pred_train_xgbr)

# Predict on validation data
pred_val_xgbr = model_xgbr.predict(X_val)

r2_val_xgbr = r2_score(y_val, pred_val_xgbr)
mse_val_xgbr = mean_squared_error(y_val, pred_val_xgbr)
rmse_val_xgbr = np.sqrt(mse_val_xgbr)
mae_val_xgbr = mean_absolute_error(y_val, pred_val_xgbr)

pd.DataFrame({'Validation':  [r2_val_xgbr, mse_val_xgbr, rmse_val_xgbr, mae_val_xgbr],
               'Training': [r2_train_xgbr, mse_train_xgbr, rmse_train_xgbr, mae_train_xgbr],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

# Finally, predict on test data
pred_test_xgbr = model_xgbr.predict(X_test)

r2_test_xgbr = r2_score(y_test, pred_test_xgbr)
mse_test_xgbr = mean_squared_error(y_test, pred_test_xgbr)
rmse_test_xgbr = np.sqrt(mse_test_xgbr)
mae_test_xgbr = mean_absolute_error(y_test, pred_test_xgbr)

print('R2 Score: ', r2_test_xgbr)
print('MSE: ', mse_test_xgbr)
print('RMSE: ', rmse_test_xgbr)
print('MAE: ', mae_test_xgbr)

# RESIDUAL PLOTvisualizer = ResidualsPlot(model_xgbr, hist=False, qqplot=True)
visualizer.fit(X_train, y_train)
visualizer.score(X_test, y_test)
visualizer.show();

pd.DataFrame({'Y_Test': y_test,'Y_Pred':pred_test_poly, 'Residuals':(y_test-pred_test_xgbr) }).head(5)

plt.scatter(y_test, pred_test_xgbr)
plt.xlabel('Real')
plt.ylabel('Pred')
plt.title('XGBRegression pred against real')
plt.show()

# RIDGE REGRESSION
model_ridge = Ridge(alpha=10)
model_ridge.fit(X_train, y_train)

# Predict on train data
pred_train_ridge = model_ridge.predict(X_train)

r2_train = r2_score(y_train, pred_train_ridge)
mse_train = mean_squared_error(y_train, pred_train_ridge)
rmse_train = np.sqrt(mse_train)
mae_train = mean_absolute_error(y_train, pred_train_ridge)

# Predict on validation data
pred_val_ridge = model_ridge.predict(X_val)

r2_val = r2_score(y_val, pred_val_ridge)
mse_val = mean_squared_error(y_val, pred_val_ridge)
rmse_val = np.sqrt(mse_val)
mae_val = mean_absolute_error(y_val, pred_val_ridge)

pd.DataFrame({'Validation':  [r2_val, mse_val, rmse_val, mae_val],
               'Training': [r2_train, mse_train, rmse_train, mae_train],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

# Cross-validation method to evaluate model
model_ridge_cv = RidgeCV(alphas=(0.001, 0.01), scoring='neg_mean_absolute_error')

model_ridge_cv.fit(X_train, y_train)

print("alpha: ", model_ridge_cv.alpha_)

# Predict on validation data
pred_val_ridge = model_ridge_cv.predict(X_val)

r2_val2 = r2_score(y_val, pred_val_ridge)
mse_val2 = mean_squared_error(y_val, pred_val_ridge)
rmse_val2 = np.sqrt(mse_val)
mae_val2 = mean_absolute_error(y_val, pred_val_ridge)

# Compare this model (validation 2) with the previous one (validation 1)
pd.DataFrame({'Validation 1':  [r2_val, mse_val, rmse_val, mae_val],
               'Validation 2': [r2_val2, mse_val2, rmse_val2, mae_val2],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

"""The model has improved and we can see that alpha = 0.01 is better"""

# Finally, predict on test data
pred_test_ridge = model_ridge_cv.predict(X_test)

r2_test_ridge = r2_score(y_test, pred_test_ridge)
mse_test_ridge = mean_squared_error(y_test, pred_test_ridge)
rmse_test_ridge = np.sqrt(mse_val)
mae_test_ridge = mean_absolute_error(y_test, pred_test_ridge)

print('R2 Score: ', r2_test_ridge)
print('MSE: ', mse_test_ridge)
print('RMSE: ', rmse_test_ridge)
print('MAE: ', mae_test_ridge)

visualizer = ResidualsPlot(model_ridge_cv, hist=False, qqplot=True)
visualizer.fit(X_train, y_train)
visualizer.score(X_test, y_test)
visualizer.show();

pd.DataFrame({'Y_Test': y_test,'Y_Pred':pred_test_poly, 'Residuals':(y_test-pred_test_ridge) }).head(5)

plt.scatter(y_test, pred_test_ridge)
plt.xlabel('Real')
plt.ylabel('Pred')
plt.title('Ridge Regression pred against real')
plt.show()

# LASSO REGRESSION
model_lasso = Lasso(alpha=0.1)
model_lasso.fit(X_train, y_train)

# Predict on train data
pred_train_lasso = model_lasso.predict(X_train)

r2_train_lasso = r2_score(y_train, pred_train_lasso)
mse_train_lasso = mean_squared_error(y_train, pred_train_lasso)
rmse_train_lasso = np.sqrt(mse_train)
mae_train_lasso = mean_absolute_error(y_train, pred_train_lasso)

# Predict on validation data
pred_val_lasso = model_lasso.predict(X_val)

r2_val_lasso = r2_score(y_val, pred_val_lasso)
mse_val_lasso = mean_squared_error(y_val, pred_val_lasso)
rmse_val_lasso = np.sqrt(mse_val)
mae_val_lasso = mean_absolute_error(y_val, pred_val_lasso)

pd.DataFrame({'Validation':  [r2_val_lasso, mse_val_lasso, rmse_val_lasso, mae_val_lasso],
               'Training': [r2_train_lasso, mse_train_lasso, rmse_train_lasso, mae_train_lasso],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

# Cross-validation method to evaluate model
#model_lasso_cv = LassoCV(eps=0.01, n_alphas=50000, cv=10)
model_lasso_cv = LassoCV(eps=0.01, n_alphas=100, cv=10, max_iter=10000)

model_lasso_cv.fit(X_train, y_train)

print("alpha: ", model_lasso_cv.alpha_)

# Predict on validation data
pred_val_lasso2 = model_lasso_cv.predict(X_val)

r2_val2_lasso = r2_score(y_val, pred_val_lasso2)
mse_val2_lasso = mean_squared_error(y_val, pred_val_lasso2)
rmse_val2_lasso = np.sqrt(mse_val)
mae_val2_lasso = mean_absolute_error(y_val, pred_val_lasso2)

# Compare this model (validation 2) with the previous one (validation 1)
pd.DataFrame({'Validation 1':  [r2_val_lasso, mse_val_lasso, rmse_val_lasso, mae_val_lasso],
               'Validation 2': [r2_val2_lasso, mse_val2_lasso, rmse_val2_lasso, mae_val2_lasso],
             },
              index=['R2', 'MSE', 'RMSE', 'MAE'])

"""NO significant change"""

model_lasso_cv.coef_

# Finally, predict on test data
pred_test_lasso = model_lasso_cv.predict(X_test)

r2_test_lasso = r2_score(y_test, pred_test_lasso)
mse_test_lasso = mean_squared_error(y_test, pred_test_lasso)
rmse_test_lasso = np.sqrt(mse_val)
mae_test_lasso = mean_absolute_error(y_test, pred_test_lasso)

print('R2 Score: ', r2_test_lasso)
print('MSE: ', mse_test_lasso)
print('RMSE: ', rmse_test_lasso)
print('MAE: ', mae_test_lasso)

isualizer = ResidualsPlot(model_lasso_cv, hist=False, qqplot=True)
visualizer.fit(X_train, y_train)
visualizer.score(X_test, y_test)
visualizer.show();

pd.DataFrame({'Y_Test': y_test,'Y_Pred':pred_test_poly, 'Residuals':(y_test-pred_test_lasso) }).head(5)

plt.scatter(y_test, pred_test_lasso)
plt.xlabel('Real')
plt.ylabel('Pred')
plt.title('Lasso Regression pred against real')
plt.show()

"""RESULT

"""

#R2 Score of the models
sns.set()
plt.figure(figsize=(8,6))

models = ['Polynomial Regression', 'XGBRegression', 'RidgeCV', 'LassoCV']
r2 = [r2_test_poly, r2_test_xgbr, r2_test_ridge, r2_test_lasso]
ax = sns.barplot(x = models, y = r2, palette='pastel')
ax.bar_label(ax.containers[0])
plt.xlabel('Models')
plt.ylabel('R2 Score')
plt.title('Comparing R2 Score of Models');

#RMSE of the Model
sns.set()
plt.figure(figsize=(8,6))
rmse = [rmse_test_poly, rmse_test_xgbr, rmse_test_ridge, rmse_test_lasso]
ax = sns.barplot(x = models, y = rmse, palette = 'pastel')
ax.bar_label(ax.containers[0])
plt.xlabel('Models')
plt.ylabel('RMSE')
plt.title('Comparing RMSE of Models');

"""According to observations ,the XGBRegression Model performs the best
R2 Score: 0.780957
RMSE: 6.0914
"""