from extensions import db
from datetime import datetime

class Crop(db.Model):
    __tablename__ = 'crops'

    id = db.Column(db.Integer, primary_key=True)
    crop_name = db.Column(db.String(50), nullable=False)
    crop_type = db.Column(db.String(50))
    duration_growth = db.Column(db.Integer)  # months

    # Relationships
    farm_records = db.relationship('FarmRecord', backref='crop', lazy=True)
    crop_health_records = db.relationship('CropHealth', backref='crop', lazy=True)

    def __repr__(self):
        return f"<Crop {self.crop_name}>"