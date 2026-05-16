import pandas as pd

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    classification_report
)

# -----------------------------
# LOAD DATA
# -----------------------------

data_path = (
    Path(__file__).parent.parent
    / "data"
    / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
)

df = pd.read_csv(data_path)

# -----------------------------
# PREPROCESSING
# -----------------------------

# Remove unnecessary column
df.drop("customerID", axis=1, inplace=True)

# Convert TotalCharges
df["TotalCharges"] = pd.to_numeric(
    df["TotalCharges"],
    errors="coerce"
)

# Fill missing values
median_total = df["TotalCharges"].median()

df["TotalCharges"] = df["TotalCharges"].fillna(
    median_total
)

# Convert target
df["Churn"] = df["Churn"].map({
    "Yes": 1,
    "No": 0
})

# Encode categorical columns
encoders = {}

for column in df.columns:

    if df[column].dtype == "object":

        encoder = LabelEncoder()

        df[column] = encoder.fit_transform(
            df[column]
        )

        encoders[column] = encoder

# -----------------------------
# FEATURES & TARGET
# -----------------------------

X = df.drop("Churn", axis=1)
y = df["Churn"]

# -----------------------------
# TRAIN TEST SPLIT
# -----------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# -----------------------------
# MODEL TRAINING
# -----------------------------

model = LogisticRegression(max_iter=1000)

model.fit(X_train, y_train)

# -----------------------------
# PREDICTIONS
# -----------------------------

y_pred = model.predict(X_test)

# -----------------------------
# EVALUATION
# -----------------------------

accuracy = accuracy_score(y_test, y_pred)

print("\nAccuracy:")
print(accuracy)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))