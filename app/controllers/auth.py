from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from itsdangerous import URLSafeTimedSerializer
import os
from flask_mail import Message
from app import mail
from flask_login import login_user

auth_bp = Blueprint('auth', __name__)

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
        return email
    except:
        return None

def send_reset_email(to_email, reset_url):
    msg = Message('Đặt lại mật khẩu Agri TraceChain',
                  recipients=[to_email])
    msg.body = f'Bạn nhận được email này vì đã yêu cầu đặt lại mật khẩu cho tài khoản Agri TraceChain.\n\n' \
               f'Nhấn vào link sau để đặt lại mật khẩu:\n{reset_url}\n\n' \
               f'Nếu bạn không yêu cầu, hãy bỏ qua email này.'
    mail.send(msg)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(email=email).first()

        # Kiểm tra nếu user tồn tại và mật khẩu đúng
        if not user or not user.check_password(password):
            flash('Email hoặc mật khẩu không đúng. Vui lòng thử lại.', 'error')
            return redirect(url_for('auth.login'))

        # Đăng nhập user bằng Flask-Login
        login_user(user, remember=remember)

        flash('Bạn đã đăng nhập thành công!', 'success')
        return redirect(url_for('main.index'))

    return render_template('auth/login.html', title='Đăng nhập')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        phone = request.form.get('phone')
        role = request.form.get('role')
        terms = request.form.get('terms')

        # Kiểm tra các trường bắt buộc
        if not name or not email or not password or not role or not terms:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('auth.register'))

        # Kiểm tra mật khẩu xác nhận
        if password != password_confirm:
            flash('Mật khẩu xác nhận không khớp.', 'error')
            return redirect(url_for('auth.register'))

        # Kiểm tra email đã tồn tại chưa
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email này đã được sử dụng. Vui lòng chọn email khác.', 'error')
            return redirect(url_for('auth.register'))

        # Tạo user mới
        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            phone=phone
        )

        # Lưu vào database
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Tài khoản đã được tạo thành công! Vui lòng đăng nhập.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('auth.register'))

    return render_template('auth/register.html', title='Đăng ký')

@auth_bp.route('/logout')
def logout():
    # Xóa thông tin user khỏi session
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    session.pop('user_role', None)

    flash('Bạn đã đăng xuất thành công!', 'success')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('Không tìm thấy thông tin người dùng.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Cập nhật thông tin cá nhân
        user.name = request.form.get('name')
        user.phone = request.form.get('phone')
        user.address = request.form.get('address')

        try:
            db.session.commit()
            # Cập nhật lại session
            session['user_name'] = user.name
            flash('Thông tin tài khoản đã được cập nhật!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')

    # Lấy danh sách sản phẩm (nếu là farmer)
    products = []
    if user.role == 'farmer':
        products = Product.query.filter_by(user_id=user.id).all()

    # Lấy danh sách đơn hàng gần đây
    orders = Order.query.filter_by(buyer_id=user.id).order_by(Order.order_date.desc()).limit(5).all()

    return render_template('auth/profile.html', title='Thông tin tài khoản', user=user, products=products, orders=orders)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem trang này.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash('Không tìm thấy thông tin người dùng.', 'error')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        new_password_confirm = request.form.get('new_password_confirm')

        # Kiểm tra mật khẩu hiện tại
        if not user.check_password(current_password):
            flash('Mật khẩu hiện tại không đúng.', 'error')
            return redirect(url_for('auth.change_password'))

        # Kiểm tra mật khẩu mới và xác nhận
        if new_password != new_password_confirm:
            flash('Mật khẩu mới và xác nhận không khớp.', 'error')
            return redirect(url_for('auth.change_password'))

        # Cập nhật mật khẩu
        user.password = generate_password_hash(new_password)

        try:
            db.session.commit()
            flash('Mật khẩu đã được cập nhật!', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')

    return render_template('auth/change_password.html', title='Đổi mật khẩu')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Trong thực tế, bạn sẽ gửi email ở đây
            # Ví dụ: send_reset_email(user.email, reset_url)
            # current_app.logger.info(f"Reset password link: {reset_url}")
            send_reset_email(user.email, reset_url)
            
            flash('Hướng dẫn đặt lại mật khẩu đã được gửi đến email của bạn.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Email không tồn tại trong hệ thống.', 'error')
    return render_template('auth/forgot_password.html', title='Quên mật khẩu')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash('Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Không tìm thấy người dùng.', 'error')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Mật khẩu không khớp.', 'error')
            return redirect(url_for('auth.reset_password', token=token))
        
        user.password = generate_password_hash(password)
        db.session.commit()
        flash('Mật khẩu đã được cập nhật thành công.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Đặt lại mật khẩu', token=token)
