from app import db
from datetime import datetime

class TraceLog(db.Model):
    __tablename__ = 'trace_logs'

    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    action = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    blockchain_tx = db.Column(db.String(255))
    ip_address = db.Column(db.String(50))

    def __repr__(self):
        return f'<TraceLog {self.id} - {self.action[:20]}...>'
