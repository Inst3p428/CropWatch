from extensions import db
from datetime import datetime

class CountyAverages(db.Model):
    __tablename__ = 'county_averages'

    id = db.Column(db.Integer, primary_key=True)
    county = db.Column(db.String(50), nullable=False)
    crop_id = db.Column(db.Integer, db.ForeignKey('crops.id'), nullable=False)

    average_yield = db.Column(db.Float)
    average_rainfall = db.Column(db.Float)

    crop = db.relationship('Crop')

    def __repr__(self):
        return f"<CountyAverage {self.county} Crop:{self.crop_id}>"
