import pandas as pd
import joblib
import numpy as np
from pathlib import Path

def bulk_predict(df: pd.DataFrame) -> pd.DataFrame:
    """Predict churn for a dataset and add result columns."""
    
    # Load trained model and metadata
    model_path = Path("models") / "best_churn_model.pkl"
    if not model_path.exists():
        raise Exception("Model file not found. Please train a model first.")
        
    model_package = joblib.load(model_path)
    
    model = model_package["model"]
    feature_names = list(model_package["feature_names"])
    encoders = model_package["encoders"]

    # Prepare the dataframe for prediction
    prediction_df = df.copy()

    # Convert numeric-like fields to numeric type
    for column in prediction_df.columns:
        if column in feature_names and column not in encoders:
            if prediction_df[column].dtype == object or str(prediction_df[column].dtype).startswith('string'):
                prediction_df[column] = pd.to_numeric(prediction_df[column], errors='coerce')

    # Drop ID-like columns that are not model features
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

    # Handle missing values for every column
    for column in prediction_df.columns:
        if pd.api.types.is_numeric_dtype(prediction_df[column]):
            median_val = prediction_df[column].median()
            if pd.isna(median_val):
                median_val = 0
            prediction_df[column] = prediction_df[column].fillna(median_val)
        else:
            mode_series = prediction_df[column].mode()
            mode_val = mode_series[0] if not mode_series.empty else "Unknown"
            prediction_df[column] = prediction_df[column].fillna(mode_val)

    # Encode categorical fields using saved encoders
    for column, encoder in encoders.items():
        if column in prediction_df.columns:
            series_str = prediction_df[column].astype(str)
            known_classes = set(encoder.classes_)
            first_label = encoder.classes_[0]
            series_str = series_str.where(series_str.isin(known_classes), first_label)
            prediction_df[column] = encoder.transform(series_str)

    # Keep model features in the right order
    for col in feature_names:
        if col not in prediction_df.columns:
            prediction_df[col] = 0

    prediction_df = prediction_df[feature_names]
    prediction_df = prediction_df.apply(pd.to_numeric, errors='coerce').fillna(0)

    predictions = model.predict(prediction_df)
    probabilities = model.predict_proba(prediction_df)[:, 1]

    result_df = df.copy()
    result_df["Churn_Prediction"] = predictions
    result_df["Churn_Probability"] = (probabilities * 100).round(2)

    risk_levels = []
    for prob in probabilities:
        if prob >= 0.75:
            risk_levels.append("High Risk")
        elif prob >= 0.40:
            risk_levels.append("Medium Risk")
        else:
            risk_levels.append("Low Risk")

    result_df["Risk_Level"] = risk_levels

    ignore_keywords = ["id", "name", "row", "churn", "exited", "status", "leave"]
    valid_cols = [col for col in df.columns if not any(k in col.lower() for k in ignore_keywords)]

    is_at_risk = np.ones(len(df), dtype=bool)
    reasons_list = [[] for _ in range(len(df))]

    for col in valid_cols:
        series = df[col]
        if pd.api.types.is_numeric_dtype(series):
            low_mask = (series < 3) & is_at_risk
            high_mask = (series > 1000) & is_at_risk
            for idx in np.where(low_mask)[0]:
                reasons_list[idx].append(f"Low {col}")
            for idx in np.where(high_mask)[0]:
                reasons_list[idx].append(f"High {col}")
        else:
            str_series = series.astype(str).str.lower()
            month_mask = str_series.str.contains("month", na=False) & is_at_risk
            no_mask = (str_series == "no") & is_at_risk
            for idx in np.where(month_mask)[0]:
                reasons_list[idx].append("Month-to-month contract")
            for idx in np.where(no_mask)[0]:
                reasons_list[idx].append(f"No {col}")
                
    result_df["Possible_Reasons"] = [", ".join(r) if r else "Normal" for r in reasons_list]

    return result_df