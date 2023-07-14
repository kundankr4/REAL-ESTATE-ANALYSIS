# REAL-ESTATE-ANALYSIS
OBJECTIVE:
At some point in their lives, everyone must deal with the real estate or housing market. It will be easier to buy or sell a house on the market at the right price if you have a thorough understanding of the market.

In this project, estimate the cost per square foot of homes based on their attributes.

Data Preprocessing:

Drop Outliers: There were outliers in house prices, unit area, longitude, and distance to the nearest MRT station.

Check Correlation:

The number of convenience stores is moderately correlated to the price of unit area, while the distance to the nearest MRT station negatively correlated.

Preprocessing Data:
    Convert transaction date to day, month and year columns
    Scaling the data

Model used:
-Polynomial Regresdsion
-XGB Regression
-Ridge Regression
-Lasso Regression 

Result:
XGB Regression performs the best:

-R2 Score: 0.780957

-RMSE: 6.09142
