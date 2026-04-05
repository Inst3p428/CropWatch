# scripts/fetch_rainfall.py
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


import requests
from datetime import date, timedelta
from app import app, db
from config import Config
from models import Farmer, RainfallData

# Get API key from Config (which reads from environment variables)
OPENWEATHER_API_KEY = Config.OPENWEATHER_API_KEY if hasattr(Config, 'OPENWEATHER_API_KEY') else os.environ.get('OPENWEATHER_API_KEY')

def fetch_rainfall_for_farmer(farmer):
    """Fetch daily rainfall for a single farmer"""
    
    # Get coordinates directly from farmer record
    if not farmer.latitude or not farmer.longitude:
        print(f"No coordinates found for farmer {farmer.id} ({farmer.county}, {farmer.sub_county})")
        return False
    
    # Get yesterday's date
    yesterday = date.today() - timedelta(days=1)
    
    # Use Current Weather API (simpler, free tier)
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={farmer.latitude}&lon={farmer.longitude}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        weather_data = response.json()
        
        # Extract rainfall (last 1 hour or 3 hours)
        rainfall_mm = 0
        if 'rain' in weather_data:
            rainfall_mm = weather_data['rain'].get('1h', 0)
            if rainfall_mm == 0:
                rainfall_mm = weather_data['rain'].get('3h', 0)
        
        # Check if record already exists for this farmer and date
        existing = RainfallData.query.filter_by(
            farmer_id=farmer.id,
            date=yesterday
        ).first()
        
        if existing:
            # Update existing record
            existing.rainfall_mm = round(rainfall_mm, 1)
            print(f"Updated: Farmer {farmer.id} ({farmer.county}) - {yesterday}: {round(rainfall_mm, 1)} mm")
        else:
            # Create new record
            new_record = RainfallData(
                farmer_id=farmer.id,
                county=farmer.county,
                sub_county=farmer.sub_county,
                date=yesterday,
                rainfall_mm=round(rainfall_mm, 1)
            )
            db.session.add(new_record)
            print(f"Added: Farmer {farmer.id} ({farmer.county}) - {yesterday}: {round(rainfall_mm, 1)} mm")
        
        db.session.commit()
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"API Error for farmer {farmer.id}: {e}")
        return False
    except Exception as e:
        print(f"Database Error for farmer {farmer.id}: {e}")
        db.session.rollback()
        return False

def fetch_all_farmers_rainfall():
    """Fetch daily rainfall for ALL farmers"""
    farmers = Farmer.query.all()
    print(f"Fetching daily rainfall for {len(farmers)} farmers...")
    
    success_count = 0
    for farmer in farmers:
        if fetch_rainfall_for_farmer(farmer):
            success_count += 1
    
    print(f"\nCompleted: {success_count}/{len(farmers)} farmers updated")
    
    # Show summary of yesterday's rainfall
    yesterday = date.today() - timedelta(days=1)
    summary = db.session.query(
        RainfallData.county,
        db.func.avg(RainfallData.rainfall_mm).label('avg_rainfall')
    ).filter(RainfallData.date == yesterday).group_by(RainfallData.county).all()
    
    if summary:
        print("\n--- Daily Rainfall Summary ---")
        for county, avg in summary:
            print(f"{county}: {round(avg, 1)} mm average")
    else:
        print("\nNo rainfall data recorded for yesterday")

if __name__ == "__main__":
    with app.app_context():
        fetch_all_farmers_rainfall()