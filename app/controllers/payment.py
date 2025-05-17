from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify, current_app
from app import db
from app.models.order import Order
from app.models.payment import Payment, vnpay_create_payment_url
from datetime import datetime
import uuid
from flask_login import login_required, current_user

payment_bp = Blueprint('payment', __name__)

# API tạo giao dịch thanh toán
@payment_bp.route('/create/<int:order_id>', methods=['POST'])
@login_required
def create_payment(order_id):
    # Lấy thông tin đơn hàng
    order = Order.query.get_or_404(order_id)

    # Kiểm tra quyền truy cập
    if order.buyer_id != current_user.id:
        return jsonify({'success': False, 'message': 'Bạn không có quyền thanh toán đơn hàng này.'}), 403

    # Kiểm tra trạng thái đơn hàng
    if order.status == 'cancelled':
        return jsonify({'success': False, 'message': 'Đơn hàng đã bị hủy, không thể thanh toán.'}), 400

    # Kiểm tra trạng thái thanh toán
    if order.payment_status == 'paid':
        return jsonify({'success': False, 'message': 'Đơn hàng đã được thanh toán.'}), 400

    # Lấy dữ liệu từ request
    data = request.get_json()
    payment_method = data.get('payment_method', order.payment_method)

    # Tạo mã giao dịch
    transaction_id = f"PAY-{uuid.uuid4().hex[:8]}-{order_id}"

    try:
        # Tạo giao dịch thanh toán mới
        payment = Payment(
            order_id=order_id,
            user_id=current_user.id,
            amount=float(order.total_price),
            payment_method=payment_method,
            transaction_id=transaction_id,
            status='pending',
            created_at=datetime.utcnow()
        )

        # Xử lý theo phương thức thanh toán
        if payment_method == 'cod':
            # Thanh toán khi nhận hàng
            order.status = 'confirmed'  # Xác nhận đơn hàng ngay
            order.payment_status = 'pending'  # Đánh dấu là chờ thanh toán khi nhận hàng
            payment.status = 'pending'
            payment.message = 'Chờ thanh toán khi nhận hàng'
        elif payment_method == 'bank_transfer':
            # Chuyển khoản ngân hàng
            order.status = 'pending'  # Chờ xác nhận thanh toán
            order.payment_status = 'pending'
            payment.status = 'pending'
            payment.message = 'Chờ xác nhận chuyển khoản'
            # Thêm thông tin ngân hàng
            payment.bank_name = 'Vietcombank'
            payment.bank_account = '1234567890'
            payment.bank_account_name = 'CÔNG TY NÔNG SẢN SẠCH'
        
        db.session.add(payment)
        db.session.commit()

        # Chuẩn bị thông tin phản hồi
        response_data = {
            'success': True,
            'message': 'Giao dịch thanh toán đã được tạo.',
            'payment_id': payment.id,
            'transaction_id': transaction_id,
            'amount': float(order.total_price),
            'payment_method': payment_method
        }

        # Thêm thông tin theo phương thức thanh toán
        if payment_method == 'bank_transfer':
            response_data['bank_info'] = {
                'bank_name': payment.bank_name,
                'account_number': payment.bank_account,
                'account_name': payment.bank_account_name,
                'transfer_content': f'Thanh toan don hang #{order_id}'
            }
            response_data['message'] = 'Vui lòng chuyển khoản theo thông tin bên dưới và chờ xác nhận.'
        elif payment_method == 'cod':
            response_data['message'] = 'Đơn hàng đã được xác nhận. Vui lòng chuẩn bị số tiền để thanh toán khi nhận hàng.'
            response_data['cod_info'] = {
                'amount_to_pay': float(order.total_price),
                'payment_status': 'pending',
                'delivery_status': 'confirmed'
            }

        return jsonify(response_data)
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API cập nhật trạng thái thanh toán
@payment_bp.route('/update/<int:payment_id>', methods=['POST'])
@login_required
def update_payment(payment_id):
    # Lấy thông tin giao dịch thanh toán
    payment = Payment.query.get_or_404(payment_id)

    # Kiểm tra quyền truy cập (chỉ người dùng hoặc admin mới có thể cập nhật)
    if payment.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Bạn không có quyền cập nhật giao dịch này.'}), 403

    # Lấy dữ liệu từ request
    data = request.get_json()
    new_status = data.get('status')

    # Kiểm tra trạng thái hợp lệ
    valid_statuses = ['pending', 'completed', 'failed', 'refunded']
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': 'Trạng thái không hợp lệ.'}), 400

    try:
        # Cập nhật trạng thái thanh toán
        payment.status = new_status

        # Lấy thông tin đơn hàng
        order = Order.query.get(payment.order_id)
        if order:
            # Xử lý theo phương thức thanh toán
            if payment.payment_method == 'cod':
                if new_status == 'completed':
                    order.payment_status = 'paid'
                    order.status = 'delivered'  # Cập nhật trạng thái đơn hàng thành đã giao
                elif new_status == 'failed':
                    order.payment_status = 'unpaid'
                    order.status = 'cancelled'  # Hủy đơn hàng nếu không thanh toán
            elif payment.payment_method == 'bank_transfer':
                if new_status == 'completed':
                    order.payment_status = 'paid'
                    order.status = 'confirmed'  # Xác nhận đơn hàng sau khi thanh toán thành công
                elif new_status == 'failed':
                    order.payment_status = 'unpaid'
                    order.status = 'pending'  # Giữ nguyên trạng thái pending để người dùng có thể thử lại
            else:
                # Xử lý cho các phương thức thanh toán khác
                if new_status == 'completed':
                    order.payment_status = 'paid'
                    if order.status == 'pending':
                        order.status = 'confirmed'
                elif new_status == 'failed':
                    order.payment_status = 'unpaid'
                elif new_status == 'refunded':
                    order.payment_status = 'refunded'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Trạng thái thanh toán đã được cập nhật thành {new_status}.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Có lỗi xảy ra: {str(e)}'}), 500

# API xem lịch sử thanh toán
@payment_bp.route('/history')
@login_required
def payment_history():
    # Lấy các tham số tìm kiếm và lọc
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Số giao dịch trên mỗi trang

    # Lấy giao dịch thanh toán của người dùng
    query = Payment.query.filter_by(user_id=current_user.id)

    # Lọc theo trạng thái
    if status:
        query = query.filter_by(status=status)

    # Sắp xếp theo thời gian mới nhất
    query = query.order_by(Payment.created_at.desc())

    # Phân trang
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    payments = pagination.items

    # Lấy thông tin đơn hàng cho mỗi giao dịch
    for payment in payments:
        payment.order = Order.query.get(payment.order_id)

    return render_template('payment/history.html',
                          title='Lịch sử thanh toán',
                          payments=payments,
                          pagination=pagination,
                          status=status)

# API tạo báo cáo thanh toán
@payment_bp.route('/report', methods=['GET', 'POST'])
def payment_report():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để tạo báo cáo thanh toán.', 'error')
        return redirect(url_for('auth.login'))

    # Kiểm tra quyền truy cập (chỉ admin mới có thể tạo báo cáo)
    if session.get('user_role') != 'admin':
        flash('Bạn không có quyền tạo báo cáo thanh toán.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status')

        # Kiểm tra dữ liệu
        if not start_date or not end_date:
            flash('Vui lòng chọn khoảng thời gian.', 'error')
            return redirect(url_for('payment.payment_report'))

        # Chuyển đổi ngày tháng
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Lấy giao dịch thanh toán trong khoảng thời gian
        query = Payment.query.filter(Payment.created_at.between(start_date, end_date))

        # Lọc theo trạng thái
        if status:
            query = query.filter_by(status=status)

        # Lấy tất cả giao dịch
        payments = query.all()

        # Tính tổng số tiền
        total_amount = sum(payment.amount for payment in payments)

        # Tính số lượng giao dịch theo trạng thái
        status_counts = {
            'pending': sum(1 for p in payments if p.status == 'pending'),
            'completed': sum(1 for p in payments if p.status == 'completed'),
            'failed': sum(1 for p in payments if p.status == 'failed'),
            'refunded': sum(1 for p in payments if p.status == 'refunded')
        }

        return render_template('payment/report.html',
                              title='Báo cáo thanh toán',
                              payments=payments,
                              total_amount=total_amount,
                              status_counts=status_counts,
                              start_date=start_date.strftime('%Y-%m-%d'),
                              end_date=end_date.strftime('%Y-%m-%d'),
                              status=status,
                              report_generated=True)

    return render_template('payment/report.html',
                          title='Báo cáo thanh toán',
                          report_generated=False)

@payment_bp.route('/vnpay/<int:order_id>')
def vnpay_payment(order_id):
    order = Order.query.get_or_404(order_id)
    vnp_TmnCode = current_app.config['VNP_TMNCODE']
    vnp_HashSecret = current_app.config['VNP_HASHSECRET']
    vnp_Url = current_app.config['VNP_URL']
    vnp_ReturnUrl = current_app.config['VNP_RETURNURL']
    payment_url = vnpay_create_payment_url(order.id, order.total_price, vnp_ReturnUrl, vnp_TmnCode, vnp_HashSecret, vnp_Url)
    return redirect(payment_url)

@payment_bp.route('/vnpay_return')
def vnpay_return():
    vnp_ResponseCode = request.args.get('vnp_ResponseCode')
    vnp_TxnRef = request.args.get('vnp_TxnRef')
    # Kiểm tra mã đơn hàng và cập nhật trạng thái thanh toán
    if vnp_ResponseCode == '00':
        # Thành công
        # Cập nhật trạng thái đơn hàng, payment...
        flash('Thanh toán thành công!', 'success')
    else:
        flash('Thanh toán thất bại hoặc bị hủy.', 'error')
    return redirect(url_for('marketplace.orders'))
