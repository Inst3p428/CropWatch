from datetime import datetime
from extensions import db

class Advisory(db.Model):
    __tablename__ = 'advisory'

    id = db.Column(db.Integer, primary_key=True)
    
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmers.id'))

    officer_id = db.Column(db.Integer, db.ForeignKey('officers.id'))
    
    crop_health_id = db.Column(db.Integer, db.ForeignKey('crop_health.id'))

    recommendation = db.Column(db.Text, nullable=False)

    priority = db.Column(
        db.Enum('High','Medium','Low'),
        nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    is_read = db.Column(db.Boolean, default=False)

    # Relationships
    crop_health = db.relationship('CropHealth', backref='advisories')
    
    def __repr__(self):
        return f"<Advisory Farmer:{self.farmer_id} Officer:{self.officer_id} Priority:{self.priority}>"