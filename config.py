import os
from dotenv import load_dotenv

# Load .env file only for local development
if os.path.exists('.env'):
    load_dotenv()

class Config:
    # Try environment variable first, fallback for local dev
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-do-not-use-in-production')
    
    # Database URL from environment or default to SQLite for local
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///cropwatch.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
     # OpenWeather API Key
    OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', '')