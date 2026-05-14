from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from flask import current_app

class Farmer(db.Model, UserMixin):
    __tablename__ = 'farmers'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    county = db.Column(db.String(50), nullable=False)
    sub_county = db.Column(db.String(50), nullable=False)
    farm_size_acres = db.Column(db.Float)
    role = db.Column(db.String(20))
    
    # NEW COLUMNS 
    latitude = db.Column(db.Float, nullable=True)   # nullable=True since existing farmers won't have it
    longitude = db.Column(db.Float, nullable=True)  # nullable=True since existing farmers won't have it

    # Relationships
    farm_records = db.relationship('FarmRecord',backref='farmer',cascade="all, delete-orphan", passive_deletes=True)
    crop_health_records = db.relationship('CropHealth', backref='farmer',cascade="all, delete-orphan", passive_deletes=True)
    soil_health_records = db.relationship('SoilHealth', backref='farmer',cascade="all, delete-orphan" ,lazy=True)

    def __repr__(self):
        return f"<Farmer {self.full_name}>"
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_reset_token(self, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(self.email, salt='password-reset-salt')
    
    @staticmethod
    def verify_reset_token(token, expires_sec=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(token, salt='password-reset-salt', max_age=expires_sec)
        except:
            return None
        return Farmer.query.filter_by(email=email).first()