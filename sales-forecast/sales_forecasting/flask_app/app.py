"""
RetailIQ — Sales Forecasting Flask API (MySQL Edition)
"""

import os
import traceback
from datetime import datetime
from dateutil.relativedelta import relativedelta
import joblib
import numpy as np
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_login import LoginManager, login_required, current_user

from models import db, User, PredictionLog, SalesRecord
app = Flask(__name__)

MYSQL_HOST     = os.environ.get('MYSQL_HOST',     'localhost')
MYSQL_PORT     = os.environ.get('MYSQL_PORT',     '3306')
MYSQL_USER     = os.environ.get('MYSQL_USER',     'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'nezuko2405')
MYSQL_DB       = os.environ.get('MYSQL_DB',       'retailiq')

MYSQL_URI = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
)

app.config['SECRET_KEY']                  = os.environ.get('SECRET_KEY', 'retailiq-dev-secret')
app.config['SQLALCHEMY_DATABASE_URI']     = os.environ.get('DATABASE_URL', MYSQL_URI)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS']   = {
    'pool_recycle': 280, 'pool_pre_ping': True,
    'pool_size': 10, 'max_overflow': 20,
}

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view           = 'auth.login'
login_manager.login_message        = 'Please log in to use RetailIQ.'
login_manager.login_message_category = 'error'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from auth import auth as auth_blueprint
app.register_blueprint(auth_blueprint)

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, '..', 'models')

model          = joblib.load(os.path.join(MODELS_DIR, 'linear_regression_model.pkl'))
feature_list   = joblib.load(os.path.join(MODELS_DIR, 'feature_list.pkl'))
encoders       = joblib.load(os.path.join(MODELS_DIR, 'encoders.pkl'))
category_stats = joblib.load(os.path.join(MODELS_DIR, 'category_stats.pkl'))

VALID_CATEGORIES  = list(encoders['Category'].classes_)
VALID_REGIONS     = list(encoders['Region'].classes_)
VALID_WEATHER     = list(encoders['Weather Condition'].classes_)
VALID_SEASONALITY = list(encoders['Seasonality'].classes_)

REQUIRED_FIELDS = ['category', 'region', 'weather', 'seasonality']

def validate_request(data):
    for field in REQUIRED_FIELDS:
        if field not in data:
            return False, f"Missing required field: '{field}'"
    checks = {
        'category': (data['category'], VALID_CATEGORIES),
        'region': (data['region'], VALID_REGIONS),
        'weather': (data['weather'], VALID_WEATHER),
        'seasonality': (data['seasonality'], VALID_SEASONALITY),
    }
    for field, (value, valid) in checks.items():
        if value not in valid:
            return False, f"Invalid '{field}': '{value}'. Allowed: {valid}"
    if 'date' in data:
        try:
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return False, "Invalid 'date' format. Expected YYYY-MM-DD"
    if 'discount' in data:
        d = float(data['discount'])
        if not (0 <= d <= 100):
            return False, f"'discount' must be 0-100, got {d}"
    if 'months' in data:
        try:
            m = int(data['months'])
            if not (1 <= m <= 6):
                return False, f"'months' must be 1-6, got {m}"
        except:
            return False, "Invalid 'months' value"
    return True, None

def build_feature_vector(data):
    date_str = data.get('date', datetime.today().strftime('%Y-%m-%d'))
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    category = data['category']; region = data['region']
    weather = data['weather']; seasonality = data['seasonality']
    cat_enc = int(encoders['Category'].transform([category])[0])
    reg_enc = int(encoders['Region'].transform([region])[0])
    wea_enc = int(encoders['Weather Condition'].transform([weather])[0])
    sea_enc = int(encoders['Seasonality'].transform([seasonality])[0])
    stats = category_stats
    lag1  = float(data.get('sales_lag1',  stats['Sales_Lag1'].get(category, 136)))
    lag7  = float(data.get('sales_lag7',  stats['Sales_Lag7'].get(category, 136)))
    roll7 = float(data.get('rolling_avg', stats['Rolling_7day_avg'].get(category, 136)))
    row = {
        'Month': date_obj.month, 'Week': date_obj.isocalendar()[1],
        'DayOfWeek': date_obj.weekday(), 'Year': date_obj.year,
        'Quarter': (date_obj.month - 1) // 3 + 1,
        'IsWeekend': int(date_obj.weekday() >= 5),
        'Price': float(data.get('price', 50.0)),
        'Discount': float(data.get('discount', 10.0)),
        'Competitor Pricing': float(data.get('competitor_price', 50.0)),
        'Inventory Level': float(data.get('inventory_level', 300.0)),
        'Units Ordered': float(data.get('units_ordered', 100.0)),
        'Holiday/Promotion': int(data.get('holiday_promotion', 0)),
        'Category_enc': cat_enc, 'Region_enc': reg_enc,
        'Weather Condition_enc': wea_enc, 'Seasonality_enc': sea_enc,
        'Sales_Lag1': lag1, 'Sales_Lag7': lag7, 'Sales_Lag14': lag7,
        'Sales_Lag30': lag7, 'Rolling_7day_avg': roll7,
        'Rolling_14day_avg': roll7, 'Rolling_30day_avg': roll7,
        'Store_Cat_enc': cat_enc,
    }
    return np.array([[row.get(f, 0) for f in feature_list]])

def check_rate_limit():
    if not current_user.can_predict:
        return False, jsonify({
            'success': False,
            'error': f"Daily limit reached ({current_user.daily_limit}/day on {current_user.plan} plan).",
            'plan': current_user.plan, 'limit': current_user.daily_limit,
        }), 429
    return True, None, None

def log_prediction(category, region, prediction, date_str=None):
    entry = PredictionLog(
        user_id=current_user.id, category=category,
        region=region, prediction=prediction,
        prediction_date=date_str,
    )
    db.session.add(entry)
    db.session.commit()

@app.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    from sqlalchemy import func
    from datetime import date, timedelta

    today = date.today()
    week_ago = today - timedelta(days=6)

    # ✅ DAILY COUNTS FIX
    daily_counts_raw = (
        db.session.query(
            func.date(PredictionLog.created_at).label('day'),
            func.count(PredictionLog.id).label('count')
        )
        .filter(PredictionLog.user_id == current_user.id)
        .filter(func.date(PredictionLog.created_at) >= week_ago)
        .group_by(func.date(PredictionLog.created_at))
        .all()
    )

    daily_counts = [
        {
            "day": str(row.day),
            "count": row.count
        }
        for row in daily_counts_raw
    ]

    # ✅ TOP CATEGORIES FIX
    top_cats_raw = (
        db.session.query(
            PredictionLog.category,
            func.count(PredictionLog.id).label('cnt'),
            func.avg(PredictionLog.prediction).label('avg_pred')
        )
        .filter(PredictionLog.user_id == current_user.id)
        .group_by(PredictionLog.category)
        .order_by(func.count(PredictionLog.id).desc())
        .limit(5)
        .all()
    )

    top_cats = [
    {
        "category": row.category,
        "cnt": int(row.cnt),   # 🔥 FIXED
        "avg_pred": float(row.avg_pred or 0)
    }
    for row in top_cats_raw
]

    total_preds = PredictionLog.query.filter_by(user_id=current_user.id).count()

    recent_preds = (
        PredictionLog.query.filter_by(user_id=current_user.id)
        .order_by(PredictionLog.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        'dashboard.html',
        daily_counts=daily_counts,
        top_cats=top_cats,
        total_preds=total_preds,
        recent_preds=recent_preds,
    )

@app.route('/predict')
@login_required
def predict_page():
    return render_template('predict.html')

@app.route('/forecast/1m')
@login_required
def forecast_1m():
    return render_template('forecast_1m.html')

@app.route('/forecast/6m')
@login_required
def forecast_6m():
    return render_template('forecast_6m.html')

@app.route('/reports')
@login_required
def reports():
    logs = (
        PredictionLog.query.filter_by(user_id=current_user.id)
        .order_by(PredictionLog.created_at.desc()).limit(100).all()
    )
    return render_template('reports.html', logs=logs)

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/data-entry')
@login_required
def data_entry():
    recent_records = (
        SalesRecord.query.filter_by(user_id=current_user.id)
        .order_by(SalesRecord.created_at.desc()).limit(20).all()
    )
    return render_template('data_entry.html',
        categories=VALID_CATEGORIES, regions=VALID_REGIONS,
        weather_options=VALID_WEATHER, seasonality_options=VALID_SEASONALITY,
        recent_records=recent_records,
    )

@app.route('/api/predict', methods=['POST'])
@login_required
def predict():
    try:
        data = request.get_json(force=True)
        ok, err = validate_request(data)
        if not ok: return jsonify({'success': False, 'error': err}), 400
        allowed, err_resp, status = check_rate_limit()
        if not allowed: return err_resp, status
        X = build_feature_vector(data)
        prediction = max(0, round(float(model.predict(X)[0]), 1))
        log_prediction(data['category'], data['region'], prediction, data.get('date'))
        MAE = 68.83
        return jsonify({
            'success': True, 'prediction': prediction,
            'confidence_low': max(0, round(prediction - MAE, 1)),
            'confidence_high': round(prediction + MAE, 1),
            'category': data['category'],
            'date': data.get('date', datetime.today().strftime('%Y-%m-%d')),
            'region': data['region'],
            'remaining_today': current_user.remaining_today,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()}), 400

@app.route('/api/forecast', methods=['POST'])
@login_required
def forecast():
    try:
        data = request.get_json(force=True)
        ok, err = validate_request(data)
        if not ok: return jsonify({'success': False, 'error': err}), 400
        months = max(1, min(int(data.get('months', 1)), 6))
        if current_user.remaining_today < months:
            return jsonify({
                'success': False,
                'error': f"Need {months} predictions, only {current_user.remaining_today} left.",
                'plan': current_user.plan,
            }), 429
        results = []; base = datetime.today().replace(day=1)
        for m in range(months):
            d = base + relativedelta(months=m)
            data['date'] = d.strftime('%Y-%m-%d')
            X = build_feature_vector(data)
            pred = max(0, round(float(model.predict(X)[0]), 1))
            data['sales_lag1'] = pred
            log_prediction(data['category'], data['region'], pred, data['date'])
            results.append({
                'month': d.strftime('%B %Y'), 'date': data['date'],
                'prediction': pred,
                'confidence_low': max(0, round(pred - 68.83, 1)),
                'confidence_high': round(pred + 68.83, 1),
            })
        return jsonify({
            'success': True, 'forecasts': results,
            'category': data['category'],
            'remaining_today': current_user.remaining_today,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sales-records', methods=['POST'])
@login_required
def add_sales_record():
    try:
        data = request.get_json(force=True)
        record = SalesRecord(
            user_id=current_user.id,
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            store_id=data.get('store_id', ''),
            product_id=data.get('product_id', ''),
            category=data['category'], region=data['region'],
            inventory_level=float(data.get('inventory_level', 0)),
            units_sold=float(data.get('units_sold', 0)),
            units_ordered=float(data.get('units_ordered', 0)),
            price=float(data.get('price', 0)),
            discount=float(data.get('discount', 0)),
            weather_condition=data.get('weather_condition', ''),
            holiday_promotion=int(data.get('holiday_promotion', 0)),
            competitor_pricing=float(data.get('competitor_pricing', 0)),
            seasonality=data.get('seasonality', ''),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({'success': True, 'id': record.id, 'message': 'Record saved to MySQL'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/sales-records', methods=['GET'])
@login_required
def get_sales_records():
    category = request.args.get('category')
    region   = request.args.get('region')
    limit    = min(int(request.args.get('limit', 50)), 500)
    q = SalesRecord.query.filter_by(user_id=current_user.id)
    if category: q = q.filter_by(category=category)
    if region:   q = q.filter_by(region=region)
    records = q.order_by(SalesRecord.date.desc()).limit(limit).all()
    return jsonify({'success': True, 'records': [r.to_dict() for r in records], 'total': q.count()})

@app.route('/api/sales-records/<int:record_id>', methods=['DELETE'])
@login_required
def delete_sales_record(record_id):
    record = SalesRecord.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record: return jsonify({'success': False, 'error': 'Not found'}), 404
    db.session.delete(record); db.session.commit()
    return jsonify({'success': True})

@app.route('/api/options', methods=['GET'])
@login_required
def options():
    return jsonify({
        'categories': VALID_CATEGORIES, 'regions': VALID_REGIONS,
        'weather': VALID_WEATHER, 'seasonality': VALID_SEASONALITY,
    })

@app.route('/api/health', methods=['GET'])
def health():
    try:
        db.session.execute(db.text('SELECT 1')); db_status = 'connected'
    except: db_status = 'error'
    return jsonify({'status': 'ok', 'database': db_status, 'db_type': 'MySQL', 'model': 'Linear Regression', 'features': len(feature_list)})

@app.route('/api/dashboard-stats', methods=['GET'])
@login_required
def dashboard_stats():
    from sqlalchemy import func
    from datetime import date, timedelta
    today = date.today(); week_ago = today - timedelta(days=6)
    daily = (
        db.session.query(
            func.date(PredictionLog.created_at).label('day'),
            func.count(PredictionLog.id).label('count'),
            func.avg(PredictionLog.prediction).label('avg_pred')
        )
        .filter(PredictionLog.user_id == current_user.id)
        .filter(func.date(PredictionLog.created_at) >= week_ago)
        .group_by(func.date(PredictionLog.created_at)).all()
    )
    by_category = (
        db.session.query(PredictionLog.category, func.count(PredictionLog.id).label('count'), func.avg(PredictionLog.prediction).label('avg'))
        .filter(PredictionLog.user_id == current_user.id)
        .group_by(PredictionLog.category).all()
    )
    return jsonify({
        'daily': [{'day': str(r.day), 'count': r.count, 'avg_pred': round(float(r.avg_pred or 0), 1)} for r in daily],
        'by_category': [{'category': r.category, 'count': r.count, 'avg': round(float(r.avg or 0), 1)} for r in by_category],
        'total_predictions': PredictionLog.query.filter_by(user_id=current_user.id).count(),
        'remaining_today': current_user.remaining_today, 'plan': current_user.plan,
    })

with app.app_context():
    db.create_all()
    print("✅ MySQL tables ready.")

if __name__ == '__main__':
    print("\n" + "="*50 + "\n  RetailIQ — MySQL Edition\n  Open: http://127.0.0.1:5000\n" + "="*50 + "\n")
    app.run(debug=True, port=5000)
