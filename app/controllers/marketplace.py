from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from flask_login import login_required, current_user
from app import db, csrf
from app.models.product import Product
from app.models.batch import Batch
from app.models.user import User
from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payment import Payment
from datetime import datetime
import json
import requests
import os

marketplace_bp = Blueprint('marketplace', __name__)

# API danh sách sản phẩm đang bán
@marketplace_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Số sản phẩm trên mỗi trang
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')

    # Lọc sản phẩm đang bán
    query = Product.query

    # Lọc theo danh mục
    if category:
        query = query.filter(Product.category == category)

    # Tìm kiếm theo tên hoặc mô tả
    if search:
        query = query.filter(db.or_(
            Product.name.ilike(f'%{search}%'),
            Product.description.ilike(f'%{search}%')
        ))

    # Sắp xếp
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'name':
        query = query.order_by(Product.name.asc())

    # Phân trang
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Lấy danh sách danh mục
    categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in categories if c[0]]

    return render_template('marketplace/index.html',
                          title='Sàn giao dịch',
                          products=products,
                          pagination=pagination,
                          categories=categories,
                          current_category=category,
                          search=search,
                          sort=sort)

# API lấy số lượng sản phẩm trong giỏ hàng
@marketplace_bp.route('/cart/count')
def get_cart_count():
    # Nếu chưa đăng nhập, trả về 0
    if not current_user.is_authenticated:
        return jsonify({'success': True, 'count': 0})

    # Lấy giỏ hàng của người dùng
    cart = Cart.query.filter_by(user_id=current_user.id).first()

    # Nếu chưa có giỏ hàng, trả về 0
    if not cart:
        return jsonify({'success': True, 'count': 0})

    # Đếm số lượng sản phẩm trong giỏ hàng
    count = sum(item.quantity for item in cart.cart_items)

    return jsonify({'success': True, 'count': count})

# API thêm sản phẩm vào giỏ hàng
@marketplace_bp.route('/cart/add', methods=['POST'])
@csrf.exempt
@login_required
def add_to_cart():
    # Lấy dữ liệu từ request
    data = request.get_json()
    product_id = data.get('product_id')
    batch_id = data.get('batch_id')
    quantity = data.get('quantity', 1)

    # Kiểm tra sản phẩm
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': 'Sản phẩm không tồn tại.'}), 404

    # Kiểm tra lô hàng (nếu có)
    if batch_id:
        batch = Batch.query.get(batch_id)
        if not batch or batch.product_id != product.id:
            return jsonify({'success': False, 'message': 'Lô hàng không hợp lệ.'}), 404

    # Lấy hoặc tạo giỏ hàng cho người dùng
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    # Kiểm tra sản phẩm đã có trong giỏ hàng chưa
    cart_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product_id,
        batch_id=batch_id
    ).first()

    if cart_item:
        # Cập nhật số lượng
        cart_item.quantity += quantity
    else:
        # Thêm sản phẩm mới vào giỏ hàng
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            batch_id=batch_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Sản phẩm đã được thêm vào giỏ hàng.',
            'cart_count': cart.total_items
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API xem giỏ hàng
@marketplace_bp.route('/cart')
@login_required
def cart():
    # Lấy giỏ hàng của người dùng
    cart = Cart.query.filter_by(user_id=current_user.id).first()

    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    # Lấy thông tin sản phẩm trong giỏ hàng
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

    for item in cart_items:
        item.product = Product.query.get(item.product_id)
        if item.batch_id:
            item.batch = Batch.query.get(item.batch_id)

    return render_template('marketplace/cart.html',
                          title='Giỏ hàng',
                          cart=cart,
                          cart_items=cart_items)

# API cập nhật giỏ hàng
@marketplace_bp.route('/cart/update', methods=['POST'])
@csrf.exempt
@login_required
def update_cart():
    # Lấy dữ liệu từ request
    data = request.get_json()
    item_id = data.get('item_id')
    quantity = data.get('quantity', 0)

    # Kiểm tra sản phẩm trong giỏ hàng
    cart_item = CartItem.query.get(item_id)
    if not cart_item:
        return jsonify({'success': False, 'message': 'Sản phẩm không có trong giỏ hàng.'}), 404

    # Kiểm tra quyền truy cập
    cart = Cart.query.get(cart_item.cart_id)
    if cart.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật giỏ hàng này.'}), 403

    try:
        if quantity <= 0:
            # Xóa sản phẩm khỏi giỏ hàng
            db.session.delete(cart_item)
        else:
            # Cập nhật số lượng
            cart_item.quantity = quantity

        db.session.commit()

        # Tính toán lại tổng tiền
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        total_amount = sum(item.subtotal for item in cart_items)

        return jsonify({
            'success': True,
            'message': 'Giỏ hàng đã được cập nhật.',
            'cart_count': cart.total_items,
            'total_amount': total_amount
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API tạo đơn hàng mới
@marketplace_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Lấy giỏ hàng của người dùng
    cart = Cart.query.filter_by(user_id=current_user.id).first()

    if not cart or not cart.cart_items:
        flash('Giỏ hàng của bạn đang trống.', 'error')
        return redirect(url_for('marketplace.cart'))

    # Lấy thông tin người dùng
    user = current_user

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        shipping_name = request.form.get('shipping_name')
        shipping_phone = request.form.get('shipping_phone')
        shipping_address = request.form.get('shipping_address')
        payment_method = request.form.get('payment_method')
        notes = request.form.get('notes')

        # Kiểm tra dữ liệu
        if not shipping_name or not shipping_phone or not shipping_address or not payment_method:
            flash('Vui lòng điền đầy đủ thông tin giao hàng.', 'error')
            return redirect(url_for('marketplace.checkout'))

        # Tính tổng tiền
        total_amount = sum(item.subtotal for item in cart.cart_items)

        # Tạo đơn hàng mới
        order = Order(
            buyer_id=current_user.id,
            batch_id=None,  # Sẽ được cập nhật sau
            quantity=1,  # Sẽ được cập nhật sau
            total_price=total_amount,
            order_date=datetime.utcnow(),
            status='pending'
        )

        db.session.add(order)
        db.session.flush()  # Để lấy order.id

        # Thêm các sản phẩm vào đơn hàng
        for cart_item in cart.cart_items:
            product = Product.query.get(cart_item.product_id)

            # Cập nhật thông tin đơn hàng
            if order.batch_id is None and cart_item.batch_id is not None:
                order.batch_id = cart_item.batch_id

            order.quantity = cart_item.quantity

            # Lưu thông tin sản phẩm vào OrderItem
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                batch_id=cart_item.batch_id,
                quantity=cart_item.quantity,
                unit_price=float(product.price),
                subtotal=float(product.price) * cart_item.quantity
            )

            db.session.add(order_item)

            # Trừ số lượng sản phẩm
            deduct_product_quantity(product, cart_item.quantity)

        try:
            # Xóa giỏ hàng
            for item in cart.cart_items:
                db.session.delete(item)

            db.session.commit()

            flash('Đơn hàng đã được tạo thành công!', 'success')
            return redirect(url_for('marketplace.order_detail', id=order.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('marketplace.checkout'))

    # Lấy thông tin sản phẩm trong giỏ hàng
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()

    for item in cart_items:
        item.product = Product.query.get(item.product_id)
        if item.batch_id:
            item.batch = Batch.query.get(item.batch_id)

    return render_template('marketplace/checkout.html',
                          title='Thanh toán',
                          cart=cart,
                          cart_items=cart_items,
                          user=user)

# API danh sách đơn hàng
@marketplace_bp.route('/orders')
@login_required
def orders():
    # Lấy các tham số tìm kiếm và lọc
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Số đơn hàng trên mỗi trang

    # Lấy đơn hàng của người dùng
    query = Order.query.filter_by(buyer_id=current_user.id)

    # Lọc theo trạng thái
    if status:
        query = query.filter_by(status=status)

    # Sắp xếp theo thời gian mới nhất
    query = query.order_by(Order.order_date.desc())

    # Phân trang
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    return render_template('marketplace/orders.html',
                          title='Đơn hàng của tôi',
                          orders=orders,
                          pagination=pagination,
                          status=status)

# API chi tiết đơn hàng
@marketplace_bp.route('/orders/<int:id>')
@login_required
def order_detail(id):
    # Lấy thông tin đơn hàng
    order = Order.query.get_or_404(id)

    # Kiểm tra quyền truy cập
    if order.buyer_id != current_user.id and not current_user.is_admin:
        flash('Bạn không có quyền xem đơn hàng này.', 'error')
        return redirect(url_for('marketplace.orders'))

    # Lấy các sản phẩm trong đơn hàng
    order_items = OrderItem.query.filter_by(order_id=id).all()

    # Thông tin thanh toán
    payment = Payment.query.filter_by(order_id=id).first()
    if payment:
        current_app.logger.info(f"payment order id: {id}, transaction_id: {payment.status}")
    else:
        current_app.logger.info(f"No payment found for order id: {id}")

    for item in order_items:
        item.product = Product.query.get(item.product_id)
        if item.batch_id:
            item.batch = Batch.query.get(item.batch_id)

    return render_template('marketplace/order_detail.html',
                          title=f'Đơn hàng #{id}',
                          order=order,
                          payment=payment,
                          order_items=order_items)

# API cập nhật trạng thái đơn hàng
@marketplace_bp.route('/orders/<int:id>/update-status', methods=['POST'])
@login_required
def update_order_status(id):
    # Kiểm tra quyền truy cập (chỉ admin hoặc người bán mới có thể cập nhật trạng thái)
    if not current_user.is_admin and current_user.role != 'farmer':
        return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật trạng thái đơn hàng.'}), 403

    # Lấy thông tin đơn hàng
    order = Order.query.get_or_404(id)

    # Lấy dữ liệu từ request
    data = request.get_json()
    new_status = data.get('status')

    # Kiểm tra trạng thái hợp lệ
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Trạng thái không hợp lệ.'}), 400

    try:
        # Cập nhật trạng thái
        order.status = new_status
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Trạng thái đơn hàng đã được cập nhật thành {new_status}.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API tạo đơn hàng qua AJAX (cho thanh toán online)
@marketplace_bp.route('/create-order', methods=['POST'])
@login_required
def create_order():
    # Lấy giỏ hàng của người dùng
    cart = Cart.query.filter_by(user_id=current_user.id).first()

    if not cart or not cart.cart_items:
        return jsonify({'success': False, 'message': 'Giỏ hàng của bạn đang trống.'}), 400

    # Lấy dữ liệu từ form
    shipping_name = request.form.get('shipping_name')
    shipping_phone = request.form.get('shipping_phone')
    shipping_address = request.form.get('shipping_address')
    payment_method = request.form.get('payment_method')
    notes = request.form.get('notes')

    # Kiểm tra dữ liệu
    if not shipping_name or not shipping_phone or not shipping_address or not payment_method:
        return jsonify({'success': False, 'message': 'Vui lòng điền đầy đủ thông tin giao hàng.'}), 400

    try:
        # Tính tổng tiền
        total_amount = sum(item.subtotal for item in cart.cart_items)

        # Tạo đơn hàng mới
        order = Order(
            buyer_id=current_user.id,
            batch_id=None,  # Sẽ được cập nhật sau
            quantity=1,  # Sẽ được cập nhật sau
            total_price=total_amount,
            order_date=datetime.utcnow(),
            status='pending'
        )

        db.session.add(order)
        db.session.flush()  # Để lấy order.id

        # Thêm các sản phẩm vào đơn hàng và trừ số lượng
        for cart_item in cart.cart_items:
            product = Product.query.get(cart_item.product_id)
            
            # Kiểm tra số lượng tồn kho
            if product.quantity < cart_item.quantity:
                db.session.rollback()
                return jsonify({
                    'success': False, 
                    'message': f'Sản phẩm {product.name} chỉ còn {product.quantity} sản phẩm.'
                }), 400

            # Cập nhật thông tin đơn hàng
            if order.batch_id is None and cart_item.batch_id is not None:
                order.batch_id = cart_item.batch_id

            order.quantity = cart_item.quantity

            # Lưu thông tin sản phẩm vào OrderItem
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                batch_id=cart_item.batch_id,
                quantity=cart_item.quantity,
                unit_price=float(product.price),
                subtotal=float(product.price) * cart_item.quantity
            )

            db.session.add(order_item)

            # Trừ số lượng sản phẩm
            deduct_product_quantity(product, cart_item.quantity)

        # Tạo bản ghi thanh toán
        payment = Payment(
            order_id=order.id,
            user_id=current_user.id,
            amount=float(total_amount),
            payment_method=payment_method,
            status='pending'
        )
        db.session.add(payment)

        # Xóa giỏ hàng
        for item in cart.cart_items:
            db.session.delete(item)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Đơn hàng đã được tạo thành công!',
            'order_id': order.id,
            'total_amount': float(total_amount)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API xử lý thanh toán online
@marketplace_bp.route('/process-payment', methods=['POST'])
@csrf.exempt
@login_required
def process_payment():
    # Lấy dữ liệu từ request
    data = request.get_json()
    order_id = data.get('order_id')
    url_return = data.get('url_return')
    amount = data.get('amount')
    service_code = data.get('service_code')
    url_callback = data.get('url_callback')

    # Kiểm tra dữ liệu
    if not order_id or not url_return or not amount:
        return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ.'}), 400

    # Kiểm tra đơn hàng
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': 'Đơn hàng không tồn tại.'}), 404

    # Kiểm tra quyền truy cập
    if order.buyer_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền thanh toán đơn hàng này.'}), 403

    try:
        # Trong môi trường thực tế, bạn sẽ gọi API của VNPay ở đây
        # Đây là mô phỏng để chuyển hướng đến trang thanh toán VNPay

        # Gọi API thanh toán của 123code.net
        payment_data = {
            'order_id': order_id,
            'url_return': url_return,
            'amount': amount,
            'service_code': service_code or 'agri_tracechain',
            'url_callback': url_callback
        }

        current_app.logger.info(f"Calling 123code.net API with data: {payment_data}")

        # Gọi API thanh toán
        response = requests.post(
            "https://123code.net/api/v1/payment/add",
            json=payment_data,
            headers={'Content-Type': 'application/json'}
        )

        # Kiểm tra kết quả
        if response.status_code == 200:
            response_data = response.json()
            current_app.logger.info(f"123code.net API response: {response_data}")

            # Cập nhật thông tin thanh toán
            payment = Payment.query.filter_by(order_id=order_id).first()
            if payment:
                payment.transaction_id = response_data.get('transaction_id', '')
                db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Đã chuyển hướng đến trang thanh toán.',
                'payment_url': response_data.get('link')
            })
        else:
            current_app.logger.error(f"123code.net API error: {response.text}")
            return jsonify({'success': False, 'message': 'Không thể kết nối đến cổng thanh toán.'}), 500

    except Exception as e:
        current_app.logger.error(f"Payment error: {str(e)}")
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API callback khi thanh toán thành công
@marketplace_bp.route('/payment/callback', methods=['POST'])
@csrf.exempt
def payment_callback():
    # Lấy dữ liệu từ request
    data = request.get_json()
    current_app.logger.info(f"Payment callback received: {data}")

    # Xử lý dữ liệu từ 123code.net
    order_id = data.get('order_id')
    transaction_id = data.get('transaction_id')
    status = data.get('status')

    # Kiểm tra dữ liệu
    if not order_id:
        return jsonify({'success': False, 'message': 'Dữ liệu không hợp lệ.'}), 400

    try:
        # Cập nhật trạng thái thanh toán
        payment = Payment.query.filter_by(order_id=order_id).first()
        if not payment:
            return jsonify({'success': False, 'message': 'Không tìm thấy thông tin thanh toán.'}), 404

        if transaction_id:
            payment.transaction_id = transaction_id

        payment.status = 'completed' if status == 'success' else 'failed'

        # Cập nhật trạng thái đơn hàng
        order = Order.query.get(order_id)
        if order:
            order.status = 'confirmed' if status == 'success' else 'cancelled'

        db.session.commit()

        return jsonify({'success': True, 'message': 'Cập nhật trạng thái thanh toán thành công.'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Payment callback error: {str(e)}")
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# Trang thanh toán thành công
@marketplace_bp.route('/payment/success')
@login_required
def payment_success():
    # Log tất cả các tham số nhận được
    current_app.logger.info(f"Payment success page accessed with params: {request.args}")

    # Lấy thông tin từ query params của 123code.net
    order_id = request.args.get('vnp_TxnRef')
    transaction_id = request.args.get('vnp_BankTranNo')
    status = request.args.get('status', 'success')  # Mặc định là success vì đây là trang thành công

    # Nếu có mã đơn hàng, cập nhật trạng thái thanh toán
    if order_id:
        try:
            # Cập nhật trạng thái thanh toán
            payment = Payment.query.filter_by(order_id=order_id).first()
            if payment:
                payment.transaction_id = transaction_id
                payment.status = 'completed'

                # Cập nhật trạng thái đơn hàng
                order = Order.query.get(order_id)
                if order:
                    order.status = 'confirmed'

                db.session.commit()

                # Hiển thị trang thành công
                return render_template('marketplace/payment_success.html',
                                      title='Thanh toán thành công',
                                      order_id=order_id)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Payment success page error: {str(e)}")

    # Nếu không có thông tin đơn hàng hoặc xảy ra lỗi, hiển thị trang thành công chung
    return render_template('marketplace/payment_success.html',
                          title='Thanh toán thành công',
                          order_id=None)

# Trang thanh toán thất bại
@marketplace_bp.route('/payment/failure')
@login_required
def payment_failure():
    # Log tất cả các tham số nhận được
    current_app.logger.info(f"Payment failure page accessed with params: {request.args}")

    # Lấy thông tin từ query params của 123code.net
    order_id = request.args.get('order_id')
    transaction_id = request.args.get('transaction_id')
    error_code = request.args.get('error_code')
    message = request.args.get('message')

    # Mặc định message lỗi
    error_message = message or 'Có lỗi xảy ra trong quá trình thanh toán.'

    # Nếu có mã đơn hàng, cập nhật trạng thái thanh toán
    if order_id:
        try:
            # Cập nhật trạng thái thanh toán
            payment = Payment.query.filter_by(order_id=order_id).first()
            if payment:
                payment.status = 'failed'
                if transaction_id:
                    payment.transaction_id = transaction_id

                # Cập nhật trạng thái đơn hàng
                order = Order.query.get(order_id)
                if order:
                    order.status = 'pending'  # Để người dùng có thể thử lại

                db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Payment failure page error: {str(e)}")

    # Hiển thị trang thất bại
    return render_template('marketplace/payment_failure.html',
                          title='Thanh toán thất bại',
                          order_id=order_id,
                          error_message=error_message)

# Route cho farmer xem tất cả đơn hàng (cả mua và bán)
@marketplace_bp.route('/farmer/orders')
@login_required
def farmer_orders():
    if current_user.role != 'farmer':
        flash('Bạn không có quyền truy cập.', 'error')
        return redirect(url_for('main.index'))

    farmer_id = current_user.id

    # Lấy đơn hàng mà farmer mua
    bought_orders = Order.query.filter_by(buyer_id=farmer_id).order_by(Order.order_date.desc()).all()

    # Lấy đơn hàng có sản phẩm do farmer bán
    sold_orders = (
        db.session.query(Order)
        .join(OrderItem, Order.id == OrderItem.order_id)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(Product.user_id == farmer_id)
        .distinct()
        .order_by(Order.order_date.desc())
        .all()
    )

    return render_template('marketplace/farmer_orders.html',
                           bought_orders=bought_orders,
                           sold_orders=sold_orders)

def deduct_product_quantity(product, quantity_to_deduct):
    # Lấy các batch còn hàng, ưu tiên batch cũ trước (theo ngày thu hoạch)
    batches = sorted([b for b in product.batches if b.quantity > 0], key=lambda x: x.harvest_date)
    for batch in batches:
        if quantity_to_deduct <= 0:
            break
        deduct = min(batch.quantity, quantity_to_deduct)
        batch.quantity -= deduct
        quantity_to_deduct -= deduct
    if quantity_to_deduct > 0:
        raise Exception("Không đủ hàng trong các lô!")