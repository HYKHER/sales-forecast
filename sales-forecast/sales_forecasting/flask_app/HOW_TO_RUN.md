# 🚀 How to Run the Flask Web App

## Step 1 — Install Flask dependencies
Open your terminal inside the `flask_app/` folder and run:
```bash
pip install -r requirements_flask.txt
```

## Step 2 — Make sure the model is trained first
Before running the Flask app, you must run **all 7 Jupyter notebooks** (01 → 07)
so that the model files are saved in the `models/` folder:
```
models/
  linear_regression_model.pkl   ← created by Notebook 05
  feature_list.pkl              ← created by Notebook 05
  encoders.pkl                  ← created by Notebook 05
  category_stats.pkl            ← created by Notebook 05
```

## Step 3 — Start the Flask server
From the `flask_app/` folder:
```bash
python app.py
```

You should see:
```
==================================================
  RetailIQ Flask Server
  Open: http://127.0.0.1:5000
==================================================
```

## Step 4 — Open the website
Open your browser and go to:
```
http://127.0.0.1:5000
```

---

## Website Pages / Sections

| Section | Description |
|---------|-------------|
| Hero | Overview, model stats, project info |
| Single Predict | Fill a form → get instant prediction for one day |
| Multi-Month Forecast | Choose category → see 1–6 month demand forecast chart |
| API Docs | Test the API endpoints directly from the browser |

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET  | `/` | Serves the website |
| GET  | `/api/health` | Check server status |
| GET  | `/api/options` | Get all valid dropdown values |
| POST | `/api/predict` | Predict units sold for one day |
| POST | `/api/forecast` | Predict units sold for 1–6 months |

---

## Project Structure (full)
```
sales_forecasting/
├── data/                          ← CSV datasets
├── notebooks/                     ← 7 Jupyter notebooks
├── models/                        ← saved ML model files
├── outputs/                       ← charts, dashboard, forecast JSON
├── flask_app/
│   ├── app.py                     ← Flask backend (run this!)
│   ├── requirements_flask.txt     ← Flask dependencies
│   ├── HOW_TO_RUN.md              ← this file
│   ├── templates/
│   │   └── index.html             ← main website page
│   └── static/
│       ├── css/style.css          ← all styles
│       └── js/main.js             ← all frontend logic
├── requirements.txt               ← data science dependencies
└── README.md                      ← full project guide
```
