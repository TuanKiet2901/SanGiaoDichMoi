from app import db
from datetime import datetime, timedelta

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

    @property
    def nearest_expiry_date(self):
        """Lấy ngày hết hạn gần nhất từ các lô hàng còn tồn kho"""
        valid_batches = [batch for batch in self.batches if batch.get_available_quantity() > 0 and batch.expiry_date]
        if not valid_batches:
            return None
        return min(batch.expiry_date for batch in valid_batches)

    @property
    def is_near_expiry(self):
        """Kiểm tra xem sản phẩm có sắp hết hạn không (còn 2 ngày)"""
        if not self.nearest_expiry_date:
            return False
        days_until_expiry = (self.nearest_expiry_date - datetime.now().date()).days
        return 0 <= days_until_expiry <= 2

    @property
    def is_expired(self):
        """Kiểm tra xem sản phẩm đã hết hạn chưa"""
        if not self.nearest_expiry_date:
            return False
        return self.nearest_expiry_date < datetime.now().date()

    @property
    def discounted_price(self):
        """Tính giá sau khi giảm 30% nếu sản phẩm sắp hết hạn"""
        if self.is_near_expiry:
            return float(self.price) * 0.7  # Giảm 30%
        return float(self.price)

    @property
    def discount_percentage(self):
        """Trả về phần trăm giảm giá nếu có"""
        return 30 if self.is_near_expiry else 0
