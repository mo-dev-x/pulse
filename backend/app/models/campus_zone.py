"""
CampusZone Model - Campus Locations
Represents physical zones on UniversitÃ© Laval campus
"""

from app import db

class CampusZone(db.Model):
    __tablename__ = 'campus_zones'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Zone Information
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    zone_type = db.Column(
        db.Enum('academic', 'residence', 'social', 'sports', 'dining', 'other', name='zone_type_enum'),
        nullable=False
    )
    
    # Timestamp
    created_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<CampusZone {self.id}: {self.name}>'
    
    def to_dict(self):
        """Serialize zone to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.zone_type,
            'zone_type': self.zone_type,
        }
    
    @staticmethod
    def get_all_active():
        """Get all campus zones"""
        return CampusZone.query.all()
    
    @staticmethod
    def get_by_id(zone_id):
        """Get zone by ID"""
        return CampusZone.query.get(zone_id)
