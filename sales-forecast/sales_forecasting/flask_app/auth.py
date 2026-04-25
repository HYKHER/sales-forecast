"""
RetailIQ — Auth Blueprint
==========================
Handles login, signup, and logout routes.
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, PredictionLog

auth = Blueprint('auth', __name__)


# ── Login ─────────────────────────────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data     = request.get_json(force=True) if request.is_json else request.form
        email    = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        remember = bool(data.get('remember', False))

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
            flash('Invalid email or password', 'error')
            return render_template('login.html', email=email)

        if not user.is_active:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Account is disabled'}), 403
            flash('Your account has been disabled. Contact support.', 'error')
            return render_template('login.html', email=email)

        login_user(user, remember=remember)

        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard'))

    return render_template('login.html')


# ── Signup ────────────────────────────────────────────────────────────────────
@auth.route('/signup', methods=['GET', 'POST'])
@auth.route('/register', methods=['GET', 'POST'])
def signup():
    # Clear flash messages about 'Please log in to use RetailIQ.' if we are on signup
    _ = request.get_json(silent=True) # just a sanity check line
    session = __import__('flask').session
    if '_flashes' in session:
        session['_flashes'] = [f for f in session['_flashes'] if f[1] != 'Please log in to use RetailIQ.']

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        data       = request.get_json(force=True) if request.is_json else request.form
        email      = (data.get('email') or '').strip().lower()
        password   = data.get('password') or ''
        first_name = (data.get('first_name') or '').strip()
        last_name  = (data.get('last_name') or '').strip()
        full_name  = f'{first_name} {last_name}'.strip()
        plan       = data.get('plan', 'free').lower()

        # ── Validation ──
        errors = {}

        if not email or '@' not in email:
            errors['email'] = 'Enter a valid email address'

        if User.query.filter_by(email=email).first():
            errors['email'] = 'An account with this email already exists'

        if len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'

        if not first_name:
           errors['first_name'] = 'First name is required'

        if not last_name:
            errors['last_name'] = 'Last name is required'

        if plan not in ('free', 'pro', 'team'):
            plan = 'free'

        if errors:
            if request.is_json:
                return jsonify({'success': False, 'errors': errors, 'error': list(errors.values())[0]}), 400
            return render_template('signup.html', errors=errors,
                                   email=email, full_name=full_name, plan=plan)

        # ── Create user ──
        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name  = parts[1] if len(parts) > 1 else ""

        user = User(
            email      = email,
            first_name = first_name,
            last_name  = last_name,
            plan       = plan,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)

        if request.is_json:
            return jsonify({'success': True, 'redirect': url_for('dashboard')})

        flash(f'Welcome to RetailIQ, {first_name}!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


# ── Logout ────────────────────────────────────────────────────────────────────
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


# ── Account info (API) ────────────────────────────────────────────────────────
@auth.route('/api/me', methods=['GET'])
@login_required
def me():
    return jsonify({
        'id'              : current_user.id,
        'email'           : current_user.email,
        'full_name'       : current_user.full_name,
        'plan'            : current_user.plan,
        'predictions_today': current_user.predictions_today,
        'daily_limit'     : current_user.daily_limit,
        'remaining_today' : current_user.remaining_today,
    })
