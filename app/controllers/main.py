
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from app.models.product import Product
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    # Lấy 8 sản phẩm nổi bật (mới nhất) để hiển thị trên trang chủ
    featured_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()

    return render_template('index.html',
                          title='Trang chủ',
                          featured_products=featured_products)

@main_bp.route('/about')
def about():
    return render_template('about.html', title='Giới thiệu')
