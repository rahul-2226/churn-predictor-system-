import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def preprocess_data(df: pd.DataFrame):
    """
    Cleans and prepares a raw customer dataset for machine learning model training.
    
    This function automatically detects the churn target column, removes irrelevant 
    identifiers, handles missing data by imputing median/mode values, and encodes 
    all categorical string values into numeric formats required by scikit-learn.

    Args:
        df (pd.DataFrame): Raw customer dataset.

    Returns:
        tuple: (X_train, X_test, y_train, y_test, feature_columns, target_column_name, 
                feature_encoders_dict, target_encoder)
    """

    # -----------------------------
    # 1. DETECT TARGET COLUMN
    # -----------------------------
    possible_targets = ["Churn", "churn", "Exited", "Attrition", "Leave", "Status"]
    target_column = None

    for col in possible_targets:
        if col in df.columns:
            target_column = col
            break

    if target_column is None:
        for col in df.columns:
            if "churn" in col.lower():
                target_column = col
                break
    
    if target_column is None:
        raise Exception("No churn target column found in the dataset. Please ensure a column like 'Churn' exists.")

    # -----------------------------
    # 2. REMOVE ID COLUMNS
    # -----------------------------
    # Keywords that usually indicate a non-informative identifier
    id_keywords = ["id", "name", "row", "index"]
    # Keywords that suggest a column is actually a feature and should NOT be dropped
    feature_keywords = ["tfidf", "score", "rate", "prob", "mean", "std", "min", "max"]
    
    columns_to_drop = []
    for col in df.columns:
        col_lower = col.lower()
        # If the column has an ID keyword AND doesn't have a feature keyword, drop it
        if any(k in col_lower for k in id_keywords):
            if not any(k in col_lower for k in feature_keywords):
                # Extra check: if it's the target column, don't drop it
                if col != target_column:
                    columns_to_drop.append(col)
    
    df = df.drop(columns=columns_to_drop)

    # -----------------------------
    # 3. CONVERT NUMERIC COLUMNS
    # -----------------------------
    for column in df.columns:
        if column == target_column:
            continue
            
        # Try to convert to numeric if it's currently an object/string
        if df[column].dtype == object or str(df[column].dtype).startswith('string'):
            converted = pd.to_numeric(df[column], errors='coerce')
            # If at least 50% of the column can be converted to numeric, keep it as numeric
            if not converted.isna().all() and (converted.notna().sum() >= len(df) * 0.5):
                df[column] = converted

    # -----------------------------
    # 4. HANDLE MISSING VALUES
    # -----------------------------
    for column in df.columns:
        if pd.api.types.is_numeric_dtype(df[column]):
            # Numeric: median
            median_val = df[column].median()
            if pd.isna(median_val):
                median_val = 0
            df[column] = df[column].fillna(median_val)
        else:
            # Categorical: mode
            mode_series = df[column].mode()
            mode_val = mode_series[0] if not mode_series.empty else "Unknown"
            df[column] = df[column].fillna(mode_val)

    # -----------------------------
    # 5. ENCODE TARGET COLUMN
    # -----------------------------
    target_encoder = LabelEncoder()
    df[target_column] = target_encoder.fit_transform(df[target_column].astype(str))

    # -----------------------------
    # 6. ENCODE CATEGORICAL FEATURES
    # -----------------------------
    encoders = {}
    for column in df.columns:
        if column == target_column:
            continue
            
        # If NOT numeric, it MUST be encoded for sklearn
        if not pd.api.types.is_numeric_dtype(df[column]):
            encoder = LabelEncoder()
            df[column] = encoder.fit_transform(df[column].astype(str))
            encoders[column] = encoder

    # -----------------------------
    # 7. FEATURES & TARGET SPLIT
    # -----------------------------
    X = df.drop(target_column, axis=1)
    y = df[target_column]

    # Ensure all column names are strings for sklearn
    X.columns = [str(col) for col in X.columns]

    # -----------------------------
    # 8. TRAIN / TEST SPLIT
    # -----------------------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    return (
        X_train,
        X_test,
        y_train,
        y_test,
        X.columns,
        target_column,
        encoders,
        target_encoder
    )