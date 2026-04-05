from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user,logout_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from models import Farmer, Officer, Admin
from extensions import db
import re
from itsdangerous import URLSafeTimedSerializer
from config import Config

auth_bp = Blueprint('auth', __name__)

OPENWEATHER_API_KEY = Config.OPENWEATHER_API_KEY


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = Farmer.query.filter_by(email=email).first()
        #user_type = 'farmer'

        if not user:
            user = Officer.query.filter_by(email=email).first()
            #user_type = 'officer'

        if not user:
            user = Admin.query.filter_by(email=email).first()
            #user_type = 'admin'

        if user and check_password_hash(user.password, password):
            login_user(user)

            if user.role == 'farmer':
                return redirect(url_for('farmer.dashboard'))
            elif user.role == 'officer':
                return redirect(url_for('officer.officer_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))

        flash("Invalid login details")

    return render_template('auth/login.html')



@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        county = request.form.get('county')
        sub_county = request.form.get('sub_county')
        farm_size_acres = request.form.get('farm_size_acres')
        
        # ========== GET COORDINATES FROM OPENWEATHER API ==========
        latitude = None
        longitude = None
        
        location_query = f"{sub_county}, {county}, Kenya"
        
        try:
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={location_query}&limit=1&appid={OPENWEATHER_API_KEY}"
            response = requests.get(geo_url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    latitude = data[0].get('lat')
                    longitude = data[0].get('lon')
                    print(f" Found coordinates for {location_query}: {latitude}, {longitude}")
                else:
                    print(f" No coordinates found for {location_query}")
            else:
                print(f" API error: {response.status_code}")
        except Exception as e:
            print(f" Geocoding error: {e}")
        # ============================================================

        # Validation
        if not all([full_name, email, password, county, sub_county, farm_size_acres]):
            flash("All fields are required", "error")
            return redirect(url_for('auth.register'))

        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match", "error")
            return redirect(url_for('auth.register'))

        # Validate email format
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email address", "error")
            return redirect(url_for('auth.register'))

        # Check if email already exists
        existing_farmer = Farmer.query.filter_by(email=email).first()
        
        if existing_farmer:
            flash("Email already registered", "error")
            return redirect(url_for('auth.register'))

        # Hash password
        hashed_password = generate_password_hash(password)

        # Create farmer account with coordinates
        try:
            new_farmer = Farmer(
                full_name=full_name,
                email=email,
                password=hashed_password,
                county=county,
                sub_county=sub_county,
                farm_size_acres=farm_size_acres,
                role='farmer',
                latitude=latitude,   # ADD THIS - auto-filled from API
                longitude=longitude  # ADD THIS - auto-filled from API
            )
            
            db.session.add(new_farmer)
            db.session.commit()
            flash("Registration successful! Please login.", "success")
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html')

from flask_login import logout_user

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Step 1: User requests password reset"""
    reset_link = None
    user_email = None
    user_role = None
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        user = Farmer.query.filter_by(email=email).first()
        user_role = 'farmer'
        
        
        # If not farmer, check if officer
        if not user:
            user = Officer.query.filter_by(email=email).first()
            user_role = 'officer'
        
        
        if user:
            token = user.get_reset_token()
            reset_link = url_for('auth.reset_password', token=token, role=user_role,  _external=True)
            user_email = email
            
            # Also print to console for backup
            print("\n" + "="*70)
            print(f" PASSWORD RESET REQUEST FOR: {user.full_name}")
            print("="*70)
            print(f" Email: {user.email}")
            print(f" Reset Link: {reset_link}")
            print("="*70)
            print("  This link expires in 1 hour")
            print("="*70 + "\n")
            
            # Show the link on the page instead of redirecting
            return render_template('auth/forgot_password.html', reset_link=reset_link, email=user_email)
        else:
            flash('Email address not found in our system.', 'error')
    
    return render_template('auth/forgot_password.html', reset_link=None, email=None)

@auth_bp.route('/reset-password/<token>/<role>', methods=['GET', 'POST'])
def reset_password(token, role):
    """Step 2: User clicks link and sets new password"""
    
    # Get user based on role from URL
    if role == 'farmer':
        user = Farmer.verify_reset_token(token)
    elif role == 'officer':
        user = Officer.verify_reset_token(token)
    else:
        user = None
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.reset_password', token=token, role=role))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('auth.reset_password', token=token, role=role))
        
        if not user:
            flash('Invalid or expired reset link. Please request a new one.', 'error')
            return redirect(url_for('auth.forgot_password'))
        
        # Update password
        user.set_password(password)
        db.session.commit()
        
        flash(' Your password has been reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    # GET request - show the form
    if not user:
        flash('Invalid or expired reset link. Please request a new one.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/reset_password.html', role=role)