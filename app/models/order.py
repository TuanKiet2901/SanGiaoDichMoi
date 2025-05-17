from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'))
    quantity = db.Column(db.Integer)
    total_price = db.Column(db.Numeric(10, 2))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.DateTime)
    status = db.Column(db.Enum('pending', 'confirmed', 'shipped', 'delivered', 'cancelled', name='order_status_enum'), default='pending')

    # Relationships
    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")
    reviews = db.relationship('Review', backref='order', lazy=True)
    payments = db.relationship('Payment', backref='order', lazy=True)

    def __repr__(self):
        return f'<Order {self.id}>'
