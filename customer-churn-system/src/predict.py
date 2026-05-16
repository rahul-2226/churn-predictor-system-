import pandas as pd
import joblib
from pathlib import Path

def predict_churn(customer_data: dict) -> dict:
    """
    Predicts the churn probability and risk level for a single customer.

    Args:
        customer_data (dict): A dictionary representing a single customer's details.

    Returns:
        dict: A dictionary containing the boolean prediction, churn probability percentage, 
              calculated risk level, and heuristic reasons for the risk.
    """

    # -----------------------------
    # 1. LOAD MODEL PACKAGE
    # -----------------------------
    model_path = Path("models") / "best_churn_model.pkl"
    model_package = joblib.load(model_path)

    model = model_package["model"]
    feature_names = model_package["feature_names"]
    encoders = model_package["encoders"]

    # -----------------------------
    # 2. CREATE DATAFRAME
    # -----------------------------
    customer_df = pd.DataFrame([customer_data])

    # -----------------------------
    # 3. ENCODE CATEGORICAL DATA
    # -----------------------------
    for column, encoder in encoders.items():
        if column in customer_df.columns:
            # Force to string to avoid mixed type errors
            customer_df[column] = encoder.transform(customer_df[column].astype(str))

    # -----------------------------
    # 4. ENSURE FEATURE ORDER
    # -----------------------------
    # The model expects columns in the exact order they were trained on
    customer_df = customer_df[feature_names]

    # -----------------------------
    # 5. PREDICTION
    # -----------------------------
    prediction = model.predict(customer_df)
    probability = model.predict_proba(customer_df)
    
    churn_probability = probability[0][1]

    # -----------------------------
    # 6. DYNAMIC RISK LEVEL
    # -----------------------------
    if churn_probability >= 0.75:
        risk_level = "High Risk"
    elif churn_probability >= 0.40:
        risk_level = "Medium Risk"
    else:
        risk_level = "Low Risk"

    # -----------------------------
    # 7. DYNAMIC REASON ANALYSIS
    # -----------------------------
    reasons = []
    ignore_keywords = ["id", "name", "row", "churn", "exited", "status", "leave"]

    for column, value in customer_data.items():
        col_lower = column.lower()
        if any(k in col_lower for k in ignore_keywords):
            continue

        # Numerical checks
        if isinstance(value, (int, float)):
            if value > 1000:
                reasons.append(f"High value detected in {column}")
            if value < 3:
                reasons.append(f"Low value detected in {column}")

        # Text checks
        if isinstance(value, str):
            val_lower = value.lower()
            if "month" in val_lower:
                reasons.append("Month-to-month contract detected")

    return {
        "prediction": int(prediction[0]),
        "churn_probability": round(churn_probability * 100, 2),
        "risk_level": risk_level,
        "possible_reasons": reasons
    }