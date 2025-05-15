from app import db
from datetime import datetime

class Batch(db.Model):
    __tablename__ = 'batches'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    qr_code = db.Column(db.String(255))
    harvest_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    quantity = db.Column(db.Integer)
    location = db.Column(db.String(255))
    status = db.Column(db.Enum('harvested', 'processing', 'shipping', 'delivered'), default='harvested')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trace_logs = db.relationship('TraceLog', backref='batch', lazy=True)
    supply_chain_steps = db.relationship('SupplyChainStep', backref='batch', lazy=True)
    order_items = db.relationship('OrderItem', foreign_keys='OrderItem.batch_id', lazy=True)
    cart_items = db.relationship('CartItem', foreign_keys='CartItem.batch_id', lazy=True)

    def __repr__(self):
        return f'<Batch {self.id} - {self.product.name if self.product else "Unknown"}>'
