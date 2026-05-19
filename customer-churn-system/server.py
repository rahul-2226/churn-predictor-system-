from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
import pandas as pd
import joblib
import os
import io
import json
import math
from pathlib import Path
from src.train import train_models
from src.predict import predict_churn
from src.bulk_prediction import bulk_predict

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Global state for prototype (in-memory storage)
LAST_ANALYSIS_RESULTS = None

@app.get("/api/model-info")
async def get_model_info():
    """
    Retrieves metadata about the currently trained best model.
    Provides feature names and label encoder classes needed for individual predictions.
    """
    model_path = MODELS_DIR / "best_churn_model.pkl"
    if not model_path.exists():
        return {"status": "error", "message": "Model not trained yet"}
    
    model_package = joblib.load(model_path)
    
    # Convert feature names to standard list
    feature_names = list(model_package["feature_names"])
    
    # Convert encoder classes to standard Python types
    processed_encoders = {}
    for k, v in model_package["encoders"].items():
        classes = v.classes_
        if hasattr(classes, "tolist"):
            classes = classes.tolist()
        else:
            classes = list(classes)
        # Ensure all elements in the list are JSON serializable
        processed_encoders[k] = [x.item() if hasattr(x, "item") else x for x in classes]

    return {
        "status": "success",
        "feature_names": feature_names,
        "encoders": processed_encoders
    }

@app.post("/api/train")
async def train(file: UploadFile = File(...)):
    """
    Manually triggers the training pipeline with an uploaded dataset.
    Saves the data temporarily and invokes the train_models logic.
    """
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents), low_memory=False)
    
    temp_path = UPLOADS_DIR / "training_data.csv"
    df.to_csv(temp_path, index=False)
    
    try:
        model_package = await run_in_threadpool(train_models, temp_path)
        return {
            "status": "success",
            "message": "Model trained successfully",
            "accuracy": round(model_package.get("accuracy", 0.85) * 100, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict")
async def predict(data: dict):
    """
    Generates a churn prediction for a single individual customer.
    Accepts JSON data matching the model's feature space.
    """
    try:
        result = await run_in_threadpool(predict_churn, data)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bulk-predict")
async def bulk_predict_api(file: UploadFile = File(...)):
    """
    Handles bulk customer analysis. 
    1. Uploads a CSV/Excel dataset.
    2. Auto-trains the model on the new data.
    3. Analyzes all records to predict churn and risk levels.
    4. Serializes data safely (handling NaN/Inf values).
    """
    global LAST_ANALYSIS_RESULTS
    filename = file.filename.lower()
    contents = await file.read()
    
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents), low_memory=False)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload CSV or Excel.")

        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        # Save to temp for training
        temp_path = UPLOADS_DIR / "auto_train_data.csv"
        df.to_csv(temp_path, index=False)

        # 1. Automatically train the model on the new data
        model_package = await run_in_threadpool(train_models, temp_path)
        accuracy = model_package.get("accuracy", 0.85)

        # 2. Perform predictions using the newly trained model
        result_df = await run_in_threadpool(bulk_predict, df)
        
        # Replace NaN/Inf with None for JSON compatibility
        clean_df = result_df.replace([float('inf'), float('-inf')], float('nan'))
        clean_df = clean_df.where(pd.notnull(clean_df), None)
        
        # Convert to JSON records with standard Python types
        records = clean_df.to_dict(orient="records")
        
        # Calculate summary metrics
        total = len(result_df)
        churn_count = int(result_df["Churn_Prediction"].sum())
        churn_rate = round((churn_count / total) * 100, 2) if total > 0 else 0
        
        high_risk = len(result_df[result_df["Risk_Level"] == "High Risk"])
        
        # Ensure summary values are JSON safe
        accuracy_val = round(accuracy * 100, 2) if accuracy else 0
        if math.isnan(accuracy_val) or math.isinf(accuracy_val):
            accuracy_val = 0
            
        summary = {
            "total_customers": total,
            "churn_customers": churn_count,
            "churn_rate": churn_rate if not math.isnan(churn_rate) else 0,
            "high_risk_customers": high_risk,
            "accuracy": accuracy_val,
            "feature_importance": model_package.get("feature_importance", [])
        }

        # Store for download
        LAST_ANALYSIS_RESULTS = result_df
        
        return {
            "status": "success",
            "data": records,
            "summary": summary
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import FileResponse

@app.get("/api/download")
async def download_results(filter_type: str = Query("all")):
    """
    Allows the user to download the most recent bulk analysis results
    as a complete CSV report directly via the browser. Supports filtering by risk.
    """
    global LAST_ANALYSIS_RESULTS
    if LAST_ANALYSIS_RESULTS is None:
        raise HTTPException(status_code=404, detail="No analysis results available")
    
    df_out = LAST_ANALYSIS_RESULTS
    if filter_type == "high":
        df_out = df_out[df_out["Risk_Level"] == "High Risk"]
    elif filter_type == "medium":
        df_out = df_out[df_out["Risk_Level"] == "Medium Risk"]
    elif filter_type == "low":
        df_out = df_out[df_out["Risk_Level"] == "Low Risk"]
    
    file_path = UPLOADS_DIR / f"churn_report_{filter_type}.xlsx"
    df_out.to_excel(file_path, index=False)
    
    return FileResponse(
        path=file_path,
        filename=f"churn_analysis_{filter_type}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Mount static files (frontend)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
