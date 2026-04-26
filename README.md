# RetailIQ Sales Forecasting System

## Overview
RetailIQ is an end-to-end sales and demand forecasting system designed for retail businesses. It leverages machine learning to provide accurate predictions and trend analysis.

## Features
- **Exploratory Data Analysis**: Deep insights into retail trends.
- **Machine Learning Models**: Linear Regression, RandomForest, and XGBoost based forecasting.
- **Flask Web Interface**: Interactive dashboard for real-time predictions.
- **Database Integration**: PostgreSQL (Render) and SQLite for data persistence.

## Project Structure
- `main.py`: Entry point for the application.
- `notebooks/`: Comprehensive Jupyter notebooks for the entire data science pipeline.
  - `01_data_exploration.ipynb`: Initial data investigation.
  - `02_data_cleaning.ipynb`: Data preprocessing and handling missing values.
  - `03_eda.ipynb`: Detailed Exploratory Data Analysis.
  - `04_feature_engineering.ipynb`: Creating lag features and rolling averages.
  - `05_model_building.ipynb`: Training and cross-validating models.
  - `06_model_evaluation.ipynb`: Analyzing model performance (MAE, RMSE).
  - `07_forecasting.ipynb`: Final forecasting logic and deployment preparation.
- `sales-forecast/`: Core application logic and assets.

## Deployment
This project is configured for deployment on **Render** with PostgreSQL.
- `render.yaml`: Deployment configuration.
- `requirements.txt`: Python dependencies.

## How to Run locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the app: `python main.py`
4. Access at `http://127.0.0.1:5000`
