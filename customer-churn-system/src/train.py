import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from .preprocessing import preprocess_data

def train_models(csv_path: str) -> dict:
    """
    Automated Machine Learning pipeline for training churn models.
    
    Reads the given dataset, cleans it using preprocess_data, trains multiple 
    classification models (Logistic Regression, Decision Tree, Random Forest), 
    and automatically selects and saves the model with the highest accuracy.

    Args:
        csv_path (str): The file path to the uploaded CSV dataset.

    Returns:
        dict: A package containing the best trained model and its associated metadata.
    """

    # -----------------------------
    # 1. LOAD DATA
    # -----------------------------
    df = pd.read_csv(csv_path, low_memory=False)

    # Downsample if dataset is very large to speed up training and prevent timeouts (e.g. Render 30s limit)
    if len(df) > 20000:
        df_train = df.sample(n=20000, random_state=42)
    else:
        df_train = df

    # -----------------------------
    # 2. PREPROCESS DATA
    # -----------------------------
    (
        X_train,
        X_test,
        y_train,
        y_test,
        feature_names,
        target_column,
        encoders,
        target_encoder
    ) = preprocess_data(df_train)

    # -----------------------------
    # 3. DEFINE MODELS (OPTIMIZED FOR SPEED)
    # -----------------------------
    models = {
        "Logistic Regression": LogisticRegression(max_iter=300, tol=1e-2, n_jobs=1, random_state=42),
        "Decision Tree": DecisionTreeClassifier(max_depth=12, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=30, max_depth=12, n_jobs=1, random_state=42)
    }

    best_model = None
    best_accuracy = 0
    best_model_name = ""

    # -----------------------------
    # 4. TRAIN & EVALUATE
    # -----------------------------
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(classification_report(y_test, y_pred))

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = model
            best_model_name = name

    # -----------------------------
    # 5. CALCULATE FEATURE IMPORTANCE
    # -----------------------------
    importance_data = {}
    if hasattr(best_model, "feature_importances_"):
        importance_data = dict(zip(feature_names, best_model.feature_importances_))
    elif hasattr(best_model, "coef_"):
        # For Logistic Regression, use absolute value of coefficients
        importance_data = dict(zip(feature_names, abs(best_model.coef_[0])))
    
    # Sort and take top 10
    sorted_importance = sorted(importance_data.items(), key=lambda x: x[1], reverse=True)[:10]
    final_importance = [{"feature": f, "importance": float(i)} for f, i in sorted_importance]

    # -----------------------------
    # 6. SAVE BEST MODEL
    # -----------------------------
    models_folder = Path("models")
    models_folder.mkdir(exist_ok=True)

    model_package = {
        "model": best_model,
        "feature_names": feature_names,
        "encoders": encoders,
        "target_encoder": target_encoder,
        "target_column": target_column,
        "accuracy": best_accuracy,
        "feature_importance": final_importance
    }

    model_path = models_folder / "best_churn_model.pkl"
    joblib.dump(model_package, model_path)

    print("\n" + "=" * 50)
    print(f"Best Model Saved Successfully: {best_model_name}")
    print(f"Final Accuracy: {best_accuracy:.4f}")

    return model_package