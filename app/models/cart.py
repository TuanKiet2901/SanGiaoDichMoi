from app import db
from datetime import datetime

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    cart_items = db.relationship('CartItem', backref='cart', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Cart {self.id}>'
    
    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.cart_items)
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.cart_items)
