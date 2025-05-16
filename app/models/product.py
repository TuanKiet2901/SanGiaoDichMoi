from app import db
from datetime import datetime

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(10, 2))
    category = db.Column(db.String(100))
    image_url = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    batches = db.relationship('Batch', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    @property
    def status(self):
        return "Còn hàng" if self.quantity > 0 else "Hết hàng"

    @property
    def quantity(self):
        # Tổng số lượng của tất cả các lô hàng của sản phẩm này
        return sum(batch.quantity for batch in self.batches)

    def get_available_quantity(self, user_id=None):
        total = sum(batch.quantity for batch in self.batches)
        if user_id:
            from app.models.cart import Cart
            cart = Cart.query.filter_by(user_id=user_id).first()
            if cart:
                cart_item = next((item for item in cart.cart_items if item.product_id == self.id), None)
                if cart_item:
                    total -= cart_item.quantity
        return total
