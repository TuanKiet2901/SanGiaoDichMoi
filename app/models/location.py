from app import db

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)  # province, district, ward, hamlet
    parent_code = db.Column(db.String(20), db.ForeignKey('locations.code'), nullable=True)
    
    # Relationships
    parent = db.relationship('Location', remote_side=[code], backref='children')
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'level': self.level,
            'parent_code': self.parent_code
        } 