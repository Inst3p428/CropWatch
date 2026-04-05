from extensions import db
from datetime import datetime

class FarmRecord(db.Model):
    __tablename__ = 'farm_records'

    id = db.Column(db.Integer, primary_key=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id', ondelete='CASCADE'), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)

    season = db.Column(db.String(50))
    planting_date = db.Column(db.Date)
    harvest_date = db.Column(db.Date)
    yield_kg = db.Column(db.Float)
    remarks = db.Column(db.Text)

    def __repr__(self):
        return f"<FarmRecord Farmer:{self.farmer_id} Crop:{self.crop_id}>"