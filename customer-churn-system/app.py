import streamlit as st
import pandas as pd
import joblib

from pathlib import Path
from src.bulk_prediction import bulk_predict

from src.train import train_models
from src.predict import predict_churn

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="Customer Churn Prediction System",
    layout="wide"
)

# -----------------------------
# TITLE
# -----------------------------

st.title("Customer Churn Prediction System")

st.write(
    "Dynamic AI-powered churn prediction dashboard"
)

# -----------------------------
# SIDEBAR
# -----------------------------

st.sidebar.title("Navigation")

page = st.sidebar.radio(

    "Go To",

    [
        "Upload & Train",
        "Predict Churn"
    ]
)

# ==================================================
# PAGE 1 — TRAINING
# ==================================================

if page == "Upload & Train":

    st.header("Upload Customer Dataset")

    uploaded_file = st.file_uploader(
        "Upload CSV File",
        type=["csv"]
    )

    if uploaded_file is not None:

        df = pd.read_csv(
            uploaded_file
        )

        st.subheader(
            "Dataset Preview"
        )

        st.dataframe(df.head())

        st.write(
            f"Dataset Shape: {df.shape}"
        )

        # -----------------------------
        # TRAIN MODEL
        # -----------------------------

        if st.button(
            "Train Model & Analyze Customers"
        ):

            with st.spinner(
                "Training AI model..."
            ):

                # Save temporary CSV
                temp_path = (
                    Path("uploads")
                    / "temp_dataset.csv"
                )

                temp_path.parent.mkdir(
                    exist_ok=True
                )

                df.to_csv(
                    temp_path,
                    index=False
                )

                # Train models
                train_models(
                    temp_path
                )

                st.success(
                    "Model Training Completed"
                )

            # -----------------------------
            # BULK PREDICTION
            # -----------------------------

            with st.spinner(
                "Analyzing customer churn..."
            ):

                result_df = bulk_predict(
                    df
                )

            st.success(
                "Customer Analysis Completed"
            )

            # -----------------------------
            # SHOW RESULTS
            # -----------------------------

            st.subheader(
                "Customer Churn Analysis"
            )

            st.dataframe(
                result_df
            )

            # -----------------------------
            # HIGH RISK CUSTOMERS
            # -----------------------------

            high_risk_df = result_df[
                result_df["Risk_Level"]
                == "High Risk"
            ]

            st.subheader(
                "High Risk Customers"
            )

            st.dataframe(
                high_risk_df
            )

            # -----------------------------
            # METRICS
            # -----------------------------

            total_customers = len(
                result_df
            )

            churn_customers = len(
                result_df[
                    result_df[
                        "Churn_Prediction"
                    ] == 1
                ]
            )

            churn_rate = (
                churn_customers
                / total_customers
            ) * 100

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Total Customers",
                total_customers
            )

            col2.metric(
                "Predicted Churn Customers",
                churn_customers
            )

            col3.metric(
                "Predicted Churn Rate",
                f"{churn_rate:.2f}%"
            )

            # -----------------------------
            # DOWNLOAD REPORT
            # -----------------------------

            csv = result_df.to_csv(
                index=False
            )

            st.download_button(

                label="Download Analysis Report",

                data=csv,

                file_name="churn_analysis.csv",

                mime="text/csv"
            )

# ==================================================
# PAGE 2 — PREDICTION
# ==================================================

elif page == "Predict Churn":

    st.header("Customer Churn Prediction")

    model_path = (
        Path("models")
        / "best_churn_model.pkl"
    )

    # Check if model exists
    if not model_path.exists():

        st.warning(
            "Please train model first"
        )

    else:

        # Load model package
        model_package = joblib.load(
            model_path
        )

        feature_names = (
            model_package["feature_names"]
        )

        encoders = (
            model_package["encoders"]
        )

        st.subheader(
            "Enter Customer Information"
        )

        customer_data = {}

        # -----------------------------
        # DYNAMIC INPUT FIELDS
        # -----------------------------

        for feature in feature_names:

            # Categorical feature
            if feature in encoders:

                options = list(
                    encoders[feature].classes_
                )

                customer_data[feature] = st.selectbox(
                    feature,
                    options
                )

            # Numerical feature
            else:

                customer_data[feature] = st.number_input(
                    feature,
                    value=0.0
                )

        # -----------------------------
        # PREDICT BUTTON
        # -----------------------------

        if st.button("Predict Churn"):

            result = predict_churn(
                customer_data
            )

            st.subheader("Prediction Result")

            # Prediction result
            if result["prediction"] == 1:

                st.error(
                    "Customer Likely to Churn"
                )

            else:

                st.success(
                    "Customer Not Likely to Churn"
                )

            # Probability
            st.metric(

                "Churn Probability",

                f"{result['churn_probability']}%"
            )

            # Risk level
            st.subheader("Risk Level")

            st.write(
                result["risk_level"]
            )

            # Reasons
            st.subheader(
                "Possible Churn Reasons"
            )

            if result["possible_reasons"]:

                for reason in result[
                    "possible_reasons"
                ]:

                    st.write(f"- {reason}")

            else:

                st.write(
                    "No major churn indicators detected"
                )