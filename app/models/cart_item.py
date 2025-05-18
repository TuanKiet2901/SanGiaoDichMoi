from app import db
from datetime import datetime

class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batches.id'), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='cart_items')
    batch = db.relationship('Batch', foreign_keys=[batch_id])

    def __repr__(self):
        return f'<CartItem {self.id}>'

    @property
    def unit_price(self):
        if self.product:
            return self.product.discounted_price
        return 0

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
