import pandas as pd
import joblib
import numpy as np
from pathlib import Path

def bulk_predict(df: pd.DataFrame) -> pd.DataFrame:
    """
    Processes a bulk dataset, applies the pre-trained machine learning model to predict churn,
    and appends risk levels and potential churn reasons to the original dataset.

    Args:
        df (pd.DataFrame): The raw customer data uploaded by the user.

    Returns:
        pd.DataFrame: The original data appended with 'Churn_Prediction', 
                      'Churn_Probability', 'Risk_Level', and 'Possible_Reasons'.
    """
    
    # -----------------------------
    # 1. LOAD MODEL & METADATA
    # -----------------------------
    model_path = Path("models") / "best_churn_model.pkl"
    if not model_path.exists():
        raise Exception("Model file not found. Please train a model first.")
        
    model_package = joblib.load(model_path)
    
    model = model_package["model"]
    feature_names = list(model_package["feature_names"])
    encoders = model_package["encoders"]

    # -----------------------------
    # 2. PREPARE DATAFRAME FOR PREDICTION
    # -----------------------------
    prediction_df = df.copy()

    # Match types to training data (Convert to numeric where possible)
    for column in prediction_df.columns:
        if column in feature_names and column not in encoders:
            # This was a numeric column during training
            if prediction_df[column].dtype == object or str(prediction_df[column].dtype).startswith('string'):
                prediction_df[column] = pd.to_numeric(prediction_df[column], errors='coerce')

    # Remove non-informative ID columns (synchronized with preprocessing)
    id_keywords = ["id", "name", "row", "index"]
    feature_keywords = ["tfidf", "score", "rate", "prob", "mean", "std", "min", "max"]
    
    for column in list(prediction_df.columns):
        col_lower = column.lower()
        if any(k in col_lower for k in id_keywords):
            if not any(k in col_lower for k in feature_keywords):
                if column not in feature_names: # Don't drop if it's actually in the model
                    prediction_df.drop(column, axis=1, inplace=True)

    # Remove any existing target columns
    possible_targets = ["Churn", "churn", "Exited", "Attrition", "Leave", "Status"]
    for col in possible_targets:
        if col in prediction_df.columns:
            if col not in feature_names:
                prediction_df.drop(col, axis=1, inplace=True)

    # -----------------------------
    # 3. HANDLE MISSING VALUES
    # -----------------------------
    for column in prediction_df.columns:
        if pd.api.types.is_numeric_dtype(prediction_df[column]):
            # Numeric: median
            median_val = prediction_df[column].median()
            if pd.isna(median_val):
                median_val = 0
            prediction_df[column] = prediction_df[column].fillna(median_val)
        else:
            # Categorical: mode
            mode_series = prediction_df[column].mode()
            mode_val = mode_series[0] if not mode_series.empty else "Unknown"
            prediction_df[column] = prediction_df[column].fillna(mode_val)

    # -----------------------------
    # 4. ENCODE CATEGORICAL COLUMNS
    # -----------------------------
    for column, encoder in encoders.items():
        if column in prediction_df.columns:
            # Force to string and handle unseen labels by mapping them to the most frequent label or a default
            # For simplicity in this prototype, we use transform and catch errors
            try:
                prediction_df[column] = encoder.transform(prediction_df[column].astype(str))
            except ValueError:
                # If unseen label, use the first known label as fallback
                first_label = encoder.classes_[0]
                prediction_df[column] = prediction_df[column].astype(str).apply(
                    lambda x: encoder.transform([x])[0] if x in encoder.classes_ else encoder.transform([first_label])[0]
                )

    # Ensure the dataframe features match the exact order and presence expected by the model
    # Add missing columns with 0
    for col in feature_names:
        if col not in prediction_df.columns:
            prediction_df[col] = 0
            
    prediction_df = prediction_df[feature_names]

    # Convert all columns to numeric just in case something slipped through
    prediction_df = prediction_df.apply(pd.to_numeric, errors='coerce').fillna(0)

    # -----------------------------
    # 5. EXECUTE PREDICTIONS
    # -----------------------------
    predictions = model.predict(prediction_df)
    probabilities = model.predict_proba(prediction_df)[:, 1]

    # -----------------------------
    # 6. COMPILE RESULTS
    # -----------------------------
    result_df = df.copy()
    result_df["Churn_Prediction"] = predictions
    result_df["Churn_Probability"] = (probabilities * 100).round(2)

    # Calculate Risk Levels
    risk_levels = []
    for prob in probabilities:
        if prob >= 0.75:
            risk_levels.append("High Risk")
        elif prob >= 0.40:
            risk_levels.append("Medium Risk")
        else:
            risk_levels.append("Low Risk")
            
    result_df["Risk_Level"] = risk_levels

    # -----------------------------
    # 7. DYNAMIC CHURN REASONS (HEURISTICS)
    # -----------------------------
    churn_reasons = []
    ignore_keywords = ["id", "name", "row", "churn", "exited", "status", "leave"]
    
    for _, row in df.iterrows():
        reasons = []
        for column, value in row.items():
            col_lower = column.lower()
            if any(k in col_lower for k in ignore_keywords):
                continue
            
            # Numerical heuristic checks
            if isinstance(value, (int, float)) and not pd.isna(value):
                if value < 3:
                    reasons.append(f"Low {column}")
                if value > 1000:
                    reasons.append(f"High {column}")
                    
            # Categorical / Text heuristic checks
            if isinstance(value, str):
                val_lower = value.lower()
                if "month" in val_lower:
                    reasons.append("Month-to-month contract")
                if "no" == val_lower:
                    reasons.append(f"No {column}")
                    
        churn_reasons.append(", ".join(reasons) if reasons else "Normal")

    result_df["Possible_Reasons"] = churn_reasons

    return result_df