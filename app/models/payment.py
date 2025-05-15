from app import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)  # cod, bank_transfer, e_wallet
    transaction_id = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='pending')  # pending, completed, failed, refunded
    message = db.Column(db.String(255), nullable=True)  # Thông báo trạng thái thanh toán
    bank_name = db.Column(db.String(100), nullable=True)  # Tên ngân hàng (cho chuyển khoản)
    bank_account = db.Column(db.String(50), nullable=True)  # Số tài khoản (cho chuyển khoản)
    bank_account_name = db.Column(db.String(100), nullable=True)  # Tên chủ tài khoản (cho chuyển khoản)
    payment_proof = db.Column(db.String(255), nullable=True)  # Đường dẫn ảnh chứng minh thanh toán
    payment_date = db.Column(db.DateTime, nullable=True)  # Thời gian thanh toán thực tế
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}>'

    def to_dict(self):
        """Chuyển đổi đối tượng Payment thành dictionary"""
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'payment_method': self.payment_method,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'message': self.message,
            'bank_name': self.bank_name,
            'bank_account': self.bank_account,
            'bank_account_name': self.bank_account_name,
            'payment_proof': self.payment_proof,
            'payment_date': self.payment_date.strftime('%Y-%m-%d %H:%M:%S') if self.payment_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
