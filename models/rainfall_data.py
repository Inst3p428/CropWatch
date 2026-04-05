from extensions import db
from datetime import datetime

class RainfallData(db.Model):
    __tablename__ = 'rainfall_data'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'), nullable=False)
    county = db.Column(db.String(50), nullable=False)
    sub_county = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    rainfall_mm = db.Column(db.Float, nullable=False)
    recorded_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    farmer = db.relationship('Farmer', backref='rainfall_records')

    def __repr__(self):
        return f"<Rainfall {self.county} {self.date}>"