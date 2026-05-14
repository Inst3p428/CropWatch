from extensions import db
from datetime import datetime

class SoilHealth(db.Model):
    __tablename__ = 'soil_health'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    moisture_percentage = db.Column(db.Float, nullable=False)
    observation = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
  
    def __repr__(self):
        return f"<SoilHealth Farmer:{self.farmer_id} {self.date}>"