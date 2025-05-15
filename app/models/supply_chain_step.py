from app import db
from datetime import datetime

class SupplyChainStep(db.Model):
    __tablename__ = 'supply_chain_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    step_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    blockchain_tx = db.Column(db.String(255))
    
    def __repr__(self):
        return f'<SupplyChainStep {self.id} - {self.step_name}>'
