"""
RetailIQ — Database Models (MySQL Edition)
Includes SalesRecord for direct data entry.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date

db = SQLAlchemy()

PLAN_LIMITS = {'free': 50, 'pro': 99999, 'team': 99999}
PLAN_PRICES = {'free': '₹0 / mo', 'pro': '₹299 / mo', 'team': '₹799 / mo'}

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name    = db.Column(db.String(100), nullable=False)
    last_name     = db.Column(db.String(100), nullable=False)
    plan          = db.Column(db.String(20), nullable=False, default='free')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)
    predictions   = db.relationship('PredictionLog', backref='user', lazy=True)
    sales_records = db.relationship('SalesRecord', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def daily_limit(self):
        return PLAN_LIMITS.get(self.plan, 50)

    @property
    def predictions_today(self):
        today = date.today()
        return PredictionLog.query.filter(
            PredictionLog.user_id == self.id,
            db.func.date(PredictionLog.created_at) == today
        ).count()

    @property
    def can_predict(self):
        return self.predictions_today < self.daily_limit

    @property
    def remaining_today(self):
        return max(0, self.daily_limit - self.predictions_today)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<User {self.email} [{self.plan}]>'


class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'
    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category        = db.Column(db.String(50), index=True)
    region          = db.Column(db.String(50), index=True)
    prediction      = db.Column(db.Float)
    prediction_date = db.Column(db.String(20))
    created_at      = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<PredictionLog user={self.user_id} pred={self.prediction}>'


class SalesRecord(db.Model):
    """
    Direct sales data entry — replaces CSV file approach.
    Users enter real store data directly into MySQL via the web form.
    """
    __tablename__ = 'sales_records'
    id                  = db.Column(db.Integer, primary_key=True)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    date                = db.Column(db.Date, nullable=False, index=True)
    store_id            = db.Column(db.String(20), index=True)
    product_id          = db.Column(db.String(20), index=True)
    category            = db.Column(db.String(50), index=True)
    region              = db.Column(db.String(50), index=True)
    inventory_level     = db.Column(db.Float, default=0)
    units_sold          = db.Column(db.Float, default=0)
    units_ordered       = db.Column(db.Float, default=0)
    price               = db.Column(db.Float, default=0)
    discount            = db.Column(db.Float, default=0)
    weather_condition   = db.Column(db.String(30))
    holiday_promotion   = db.Column(db.Integer, default=0)
    competitor_pricing  = db.Column(db.Float, default=0)
    seasonality         = db.Column(db.String(20))
    notes               = db.Column(db.Text)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'date': str(self.date),
            'store_id': self.store_id,
            'product_id': self.product_id,
            'category': self.category,
            'region': self.region,
            'inventory_level': self.inventory_level,
            'units_sold': self.units_sold,
            'units_ordered': self.units_ordered,
            'price': self.price,
            'discount': self.discount,
            'weather_condition': self.weather_condition,
            'holiday_promotion': self.holiday_promotion,
            'competitor_pricing': self.competitor_pricing,
            'seasonality': self.seasonality,
            'notes': self.notes,
            'created_at': str(self.created_at),
        }

    def __repr__(self):
        return f'<SalesRecord {self.store_id}/{self.product_id} {self.date}>'
