from extensions import db
from datetime import datetime

class CropHealth(db.Model):
    __tablename__ = 'crop_health'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)

    date = db.Column(db.Date, nullable=False)
    health_status = db.Column(
        db.Enum('Healthy', 'Fair', 'Poor'),
        nullable=False
    )
    pest_or_disease = db.Column(db.String(100))
    notes = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
   
    
    def __repr__(self):
        return f"<CropHealth Farmer:{self.farmer_id} Crop:{self.crop_id}>"