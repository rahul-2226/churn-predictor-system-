# 🔮 Customer Churn Prediction System

An AI-powered web application that helps businesses predict and prevent customer churn. This system features a powerful machine learning backend and a modern, interactive dashboard to analyze customer data, identify at-risk individuals, and understand the key drivers behind customer attrition.

## 🚀 Features

- **Automated Machine Learning**: Upload your customer dataset and the system will automatically train a Random Forest classifier.
- **Bulk Analysis**: Upload CSV or Excel files containing hundreds or thousands of customers to get instant churn probability scores and risk categorizations.
- **Individual Prediction**: Input a single customer's details via the API or dashboard to get an immediate churn prediction.
- **Feature Importance**: Understand *why* customers are leaving with automated feature importance visualization.
- **Modern Dashboard**: A beautiful, responsive "Midnight Graphite" themed UI for data visualization and reporting.
- **Exportable Reports**: Download categorized risk reports directly from the dashboard.

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3
- **Machine Learning**: Scikit-Learn, Pandas, NumPy, Joblib
- **Frontend**: HTML5, Vanilla JavaScript, CSS3 (Custom Design System)
- **Deployment Ready**: Fully configured for containerized or PaaS deployment.

## 💻 Running Locally

### Prerequisites
- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/customer-churn-system.git
   cd customer-churn-system
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Mac/Linux:
   source .venv/bin/activate
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the server:
   ```bash
   python server.py
   # OR
   uvicorn server:app --host 0.0.0.0 --port 8000
   ```

5. Access the application:
   Open your browser and navigate to `http://localhost:8000`

## 📡 API Endpoints

- `GET /api/model-info`: Retrieves metadata about the currently trained model.
- `POST /api/train`: Upload a `.csv` file to manually trigger the training pipeline.
- `POST /api/predict`: Generate a churn prediction for a single customer (JSON).
- `POST /api/bulk-predict`: Upload a dataset for automated bulk analysis.
- `GET /api/download?filter_type={all|high|medium|low}`: Download the most recent analysis report.

## 📦 Deployment (Render/Railway)

1. Connect your GitHub repository to your PaaS of choice.
2. Set the build command: `pip install -r requirements.txt`
3. Set the start command: `uvicorn server:app --host 0.0.0.0 --port $PORT`

> **Note:** Free-tier platforms usually have ephemeral file systems. Uploaded data and locally trained models (`.pkl` files) will be reset when the server goes to sleep. To mitigate this, train the model locally and commit the `models/best_churn_model.pkl` to your repository before deploying.

## 📄 License
MIT License
