#CropWatch - Farm Management System
CropWatch is a comprehensive farm management system designed to help farmers track crop health, soil conditions, farm records, and receive expert advice from agricultural officers.

# Features
For Farmers
Dashboard Overview - View key metrics and charts at a glance

Crop Health Tracking - Record and monitor crop health status (Healthy/Fair/Poor)

Soil Health Monitoring - Track soil moisture levels over time

Farm Records - Log planting dates, harvest dates, and yields

Officer Alerts - Receive recommendations from agricultural officers

Rainfall Data - View automated rainfall trends using OpenWeatherMap API

Data Export - Download crop health, farm records, and soil data as CSV

For Officers
Farmer Management - View and manage all farmers in their county

Crop Health Overview - Monitor crop health issues across farmers

Advisory System - Provide recommendations to farmers

Harvest Protection - Lock advice for harvested crops

County Filtering - Filter farmers by county

For Admins
User Management - Create and manage officer accounts

System Overview - View all platform activity

# Technology Stack
Backend: Flask (Python)

Database: SQLite / MySQL

Authentication: Flask-Login

Charts: Plotly

API Integration: OpenWeatherMap (rainfall & geocoding)

Frontend: HTML, CSS, JavaScript

# Prerequisites
Python 3.10 or higher

pip (Python package manager)

Virtual environment (recommended)

OpenWeatherMap API key (free tier available)

# Installation
1. Clone the repository
bash
git clone https://github.com/yourusername/CropWatch.git
cd CropWatch
2. Create and activate virtual environment
Windows:

bash
python -m venv venv
venv\Scripts\activate
Mac/Linux:

bash
python3 -m venv venv
source venv/bin/activate
3. Install dependencies
bash
pip install -r requirements.txt
4. Configure environment variables
Create a .env file in the root directory:

env
SECRET_KEY=your-secret-key-here
OPENWEATHER_API_KEY=your-openweather-api-key
DATABASE_URL=sqlite:///cropwatch.db
5. Initialize the database
bash
flask db upgrade
6. Add initial crops
bash
python
>>> from app import app, db
>>> from models import Crop
>>> with app.app_context():
...     crops = ["Maize", "Beans", "Rice", "Potatoes", "Tomatoes", "Onions", "Cabbage"]
...     for c in crops:
...         db.session.add(Crop(crop_name=c))
...     db.session.commit()
7. Run the application
bash
python app.py
Visit http://127.0.0.1:5000 in your browser.

# Project Structure
text
CropWatch/
├── app.py                 # Main application file
├── config.py              # Configuration settings
├── extensions.py          # Flask extensions
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not committed)
├── models/                # Database models
│   ├── farmer.py
│   ├── officer.py
│   ├── admin.py
│   ├── crop.py
│   ├── farm_record.py
│   ├── crop_health.py
│   ├── soil_health.py
│   ├── advisory.py
│   └── rainfall_data.py
├── routes/                # Route handlers
│   ├── auth_routes.py
│   ├── farmer_routes.py
│   ├── officer_routes.py
│   └── admin_routes.py
├── templates/             # HTML templates
│   ├── base.html
│   ├── landing.html
│   ├── auth/
│   ├── farmer/
│   ├── officer/
│   └── admin/
├── static/                # CSS, JS, images
│   ├── css/
│   └── js/
└── scripts/               # Utility scripts
    └── fetch_rainfall.py  # Rainfall data fetcher
# User Roles
Farmer Registration
Farmers register through the public registration page

Coordinates are automatically geocoded from county/sub-county

Can only access farmer dashboard

Officer Accounts
Created by admin only (not public registration)

Can manage farmers and provide advice

Admin Account
Create first admin via command line:

python
from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = Admin(
        full_name="System Admin",
        email="admin@cropwatch.com",
        password=generate_password_hash("admin123"),
        role="admin"
    )
    db.session.add(admin)
    db.session.commit()
# Rainfall Data
Rainfall data is fetched daily from OpenWeatherMap API:

bash
python scripts/fetch_rainfall.py
# Data Export
Farmers can export their data as CSV files:

Crop Health Records

Farm Records

Soil Health Records

#  Deployment
PythonAnywhere Deployment
Create account at pythonanywhere.com

Upload code via Git or manual upload

Set up virtual environment

Configure WSGI file

Set environment variables in Web tab

Initialize database

# Troubleshooting
Common Issues
SQLite Date Error: Ensure dates are converted to date objects before saving:

python
from datetime import datetime
date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
Geocoding Failure: Add fallback coordinates in registration route for unrecognized locations.

Module Not Found: Activate virtual environment before running.

# License
This project is for educational purposes.
