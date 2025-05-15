from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from app import db
from app.models.review import Review
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User
from datetime import datetime

reviews_bp = Blueprint('reviews', __name__)

# Trang đánh giá sản phẩm
@reviews_bp.route('/product/<int:product_id>', methods=['GET', 'POST'])
def product_review(product_id):
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để đánh giá sản phẩm.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy thông tin sản phẩm
    product = Product.query.get_or_404(product_id)

    # Kiểm tra người dùng đã mua sản phẩm này chưa
    order_items = OrderItem.query.join(Order).filter(
        OrderItem.product_id == product_id,
        Order.buyer_id == session['user_id'],
        Order.status == 'delivered'
    ).all()

    if not order_items:
        flash('Bạn cần mua và nhận sản phẩm trước khi đánh giá.', 'error')
        return redirect(url_for('marketplace.index'))

    # Kiểm tra người dùng đã đánh giá sản phẩm này chưa
    existing_review = Review.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()

    if request.method == 'POST':
        # Nếu đã có đánh giá, cập nhật đánh giá
        if existing_review:
            existing_review.rating = request.form.get('rating', type=int)
            existing_review.comment = request.form.get('comment')
            db.session.commit()
            flash('Đánh giá của bạn đã được cập nhật.', 'success')
        else:
            # Tạo đánh giá mới
            review = Review(
                user_id=session['user_id'],
                product_id=product_id,
                order_id=order_items[0].order_id,  # Lấy order_id từ order_item đầu tiên
                rating=request.form.get('rating', type=int),
                comment=request.form.get('comment'),
                created_at=datetime.utcnow()
            )
            db.session.add(review)
            db.session.commit()
            flash('Cảm ơn bạn đã đánh giá sản phẩm!', 'success')

        return redirect(url_for('products.detail', id=product_id))

    # Lấy tất cả đánh giá của sản phẩm
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()

    return render_template('reviews/product_review.html',
                          title=f'Đánh giá sản phẩm: {product.name}',
                          product=product,
                          reviews=reviews,
                          existing_review=existing_review)

# API lấy đánh giá của sản phẩm
@reviews_bp.route('/api/product/<int:product_id>')
def api_product_reviews(product_id):
    # Lấy tất cả đánh giá của sản phẩm
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()

    # Chuyển đổi đánh giá thành JSON
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'user_name': review.user.name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%d/%m/%Y %H:%M')
        })

    # Tính điểm đánh giá trung bình
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)

    return jsonify({
        'success': True,
        'reviews': reviews_data,
        'avg_rating': round(avg_rating, 1),
        'count': len(reviews)
    })

# Trang đánh giá đơn hàng
@reviews_bp.route('/order/<int:order_id>', methods=['GET', 'POST'])
def order_review(order_id):
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để đánh giá đơn hàng.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy thông tin đơn hàng
    order = Order.query.get_or_404(order_id)

    # Kiểm tra quyền truy cập
    if order.buyer_id != session['user_id']:
        flash('Bạn không có quyền đánh giá đơn hàng này.', 'error')
        return redirect(url_for('marketplace.orders'))

    # Kiểm tra đơn hàng đã giao chưa
    if order.status != 'delivered':
        flash('Bạn chỉ có thể đánh giá đơn hàng đã giao.', 'error')
        return redirect(url_for('marketplace.order_detail', id=order_id))

    # Lấy các sản phẩm trong đơn hàng
    order_items = OrderItem.query.filter_by(order_id=order_id).all()

    for item in order_items:
        item.product = Product.query.get(item.product_id)
        # Kiểm tra đã đánh giá sản phẩm này chưa
        item.review = Review.query.filter_by(
            user_id=session['user_id'],
            product_id=item.product_id,
            order_id=order_id
        ).first()

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        product_id = request.form.get('product_id', type=int)
        rating = request.form.get('rating', type=int)
        comment = request.form.get('comment')

        # Kiểm tra sản phẩm có trong đơn hàng không
        order_item = next((item for item in order_items if item.product_id == product_id), None)
        if not order_item:
            flash('Sản phẩm không có trong đơn hàng.', 'error')
            return redirect(url_for('reviews.order_review', order_id=order_id))

        # Kiểm tra đã đánh giá sản phẩm này chưa
        existing_review = Review.query.filter_by(
            user_id=session['user_id'],
            product_id=product_id,
            order_id=order_id
        ).first()

        if existing_review:
            # Cập nhật đánh giá
            existing_review.rating = rating
            existing_review.comment = comment
            db.session.commit()
            flash('Đánh giá của bạn đã được cập nhật.', 'success')
        else:
            # Tạo đánh giá mới
            review = Review(
                user_id=session['user_id'],
                product_id=product_id,
                order_id=order_id,
                rating=rating,
                comment=comment,
                created_at=datetime.utcnow()
            )
            db.session.add(review)
            db.session.commit()
            flash('Cảm ơn bạn đã đánh giá sản phẩm!', 'success')

        return redirect(url_for('reviews.order_review', order_id=order_id))

    return render_template('reviews/order_review.html',
                          title=f'Đánh giá đơn hàng #{order_id}',
                          order=order,
                          order_items=order_items)
