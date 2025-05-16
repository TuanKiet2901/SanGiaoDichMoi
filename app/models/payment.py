from app import db
from datetime import datetime
import hashlib
import hmac
import urllib.parse
from flask import current_app

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

def vnpay_create_payment_url(order_id, amount, return_url, vnp_TmnCode, vnp_HashSecret, vnp_Url):
    vnp_Params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': vnp_TmnCode,
        'vnp_Amount': str(int(amount) * 100),  # VNPay yêu cầu nhân 100
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': str(order_id),
        'vnp_OrderInfo': f'Thanh toan don hang {order_id}',
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': '127.0.0.1',
        'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
    }
    sorted_params = sorted(vnp_Params.items())
    query_string = '&'.join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params])
    hashdata = '&'.join([f"{k}={v}" for k, v in sorted_params])
    secure_hash = hmac.new(vnp_HashSecret.encode(), hashdata.encode(), hashlib.sha512).hexdigest()
    payment_url = f"{vnp_Url}?{query_string}&vnp_SecureHash={secure_hash}"
    return payment_url
