from app.models.product import Product
from flask import Blueprint

test_bp = Blueprint('test', __name__)

@test_bp.route('/test-db')
def test_db():
    products = Product.query.all()
    return f"Số sản phẩm: {len(products)}"