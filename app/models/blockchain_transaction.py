from app import db
from datetime import datetime

class BlockchainTransaction(db.Model):
    __tablename__ = 'blockchain_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    tx_hash = db.Column(db.String(255), nullable=False)
    related_entity = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)

    #-----------

    batch_id = db.Column(db.Integer, nullable=True)
    supply_chain_step_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=True)
    #-------------
    data = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BlockchainTransaction {self.id} - {self.tx_hash[:10]}...>'
