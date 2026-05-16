import pandas as pd
import pandas as pd

# Load dataset
df = pd.read_csv("data/WA_Fn-UseC_-Telco-Customer-Churn.csv")

# Show first 5 rows
print(df.head())

# Dataset shape
print("\nShape:")
print(df.shape)

# Column names
print("\nColumns:")
print(df.columns)

# Information about dataset
print("\nInfo:")
print(df.info())

# Missing values
print("\nMissing Values:")
print(df.isnull().sum())