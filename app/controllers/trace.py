import os
import uuid
import csv
import io
import tempfile
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session, send_file, Response
from app import db
from app.models.batch import Batch
from app.models.product import Product
from app.models.user import User
from app.models.trace_log import TraceLog
from app.models.supply_chain_step import SupplyChainStep
from app.models.report import Report

trace_bp = Blueprint('trace', __name__)

@trace_bp.route('/')
def index():
    return render_template('trace/index.html', title='Truy xuất nguồn gốc')

@trace_bp.route('/scan')
def scan():
    return render_template('trace/scan.html', title='Quét mã QR')

@trace_bp.route('/search')
def search():
    qr_code = request.args.get('qr_code')
    if not qr_code:
        flash('Vui lòng nhập mã QR.', 'error')
        return redirect(url_for('trace.index'))

    return redirect(url_for('trace.batch_info', qr_code=qr_code))

@trace_bp.route('/upload_qr', methods=['POST'])
def upload_qr():
    # Xử lý upload hình ảnh QR (sẽ triển khai sau)
    flash('Tính năng đang được phát triển.', 'info')
    return redirect(url_for('trace.scan'))

@trace_bp.route('/batch/<string:qr_code>')
def batch_info(qr_code):
    # Tìm lô hàng theo mã QR
    batch = Batch.query.filter_by(qr_code=qr_code).first()

    if not batch:
        flash('Không tìm thấy thông tin lô hàng với mã QR này.', 'error')
        return redirect(url_for('trace.index'))

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Load user information for product
    batch.product.user = User.query.get(batch.product.user_id)

    # Load supply chain steps
    supply_chain_steps = SupplyChainStep.query.filter_by(batch_id=batch.id).order_by(SupplyChainStep.timestamp.asc()).all()

    # Log trace access
    trace_log = TraceLog(
        batch_id=batch.id,
        action=f"Truy xuất thông tin lô hàng",
        timestamp=datetime.utcnow(),
        ip_address=request.remote_addr
    )

    try:
        db.session.add(trace_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging trace: {str(e)}")

    return render_template('trace/batch_info.html',
                          title=f'Truy xuất {batch.product.name}',
                          batch=batch,
                          supply_chain_steps=supply_chain_steps)

@trace_bp.route('/api/verify/<string:tx_hash>')
def verify_blockchain(tx_hash):
    # Giả lập xác thực blockchain (sẽ triển khai thực tế sau)
    # Trong thực tế, chúng ta sẽ kết nối với Ethereum node để xác thực giao dịch
    return jsonify({
        'verified': True,
        'timestamp': '2023-04-21T10:30:15Z',
        'block_number': 12345678,
        'network': 'Ethereum Testnet'
    })

@trace_bp.route('/history')
def history():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xem lịch sử truy xuất.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy các tham số tìm kiếm và lọc
    batch_id = request.args.get('batch_id', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Số log trên mỗi trang

    # Bắt đầu với tất cả các log
    query = TraceLog.query

    # Nếu là nông dân, chỉ hiển thị các log của lô hàng của họ
    if session.get('user_role') == 'farmer':
        # Lấy tất cả sản phẩm của nông dân
        farmer_products = Product.query.filter_by(user_id=session['user_id']).all()
        farmer_product_ids = [product.id for product in farmer_products]

        # Lấy tất cả lô hàng của các sản phẩm đó
        farmer_batches = Batch.query.filter(Batch.product_id.in_(farmer_product_ids)).all()
        farmer_batch_ids = [batch.id for batch in farmer_batches]

        # Lọc các log theo lô hàng
        query = query.filter(TraceLog.batch_id.in_(farmer_batch_ids))

    # Áp dụng lọc theo lô hàng
    if batch_id:
        query = query.filter(TraceLog.batch_id == batch_id)

    # Áp dụng lọc theo ngày
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(TraceLog.timestamp >= date_from_obj)

    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)  # Kết thúc ngày
        query = query.filter(TraceLog.timestamp < date_to_obj)

    # Sắp xếp theo thời gian mới nhất
    query = query.order_by(TraceLog.timestamp.desc())

    # Phân trang kết quả
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    logs = pagination.items

    # Lấy thông tin lô hàng và sản phẩm cho mỗi log
    for log in logs:
        log.batch = Batch.query.get(log.batch_id)
        log.batch.product = Product.query.get(log.batch.product_id)

    # Lấy danh sách lô hàng cho dropdown lọc
    if session.get('user_role') == 'farmer':
        batches = Batch.query.filter(Batch.product_id.in_(farmer_product_ids)).all()
    else:
        batches = Batch.query.all()

    # Lấy thông tin sản phẩm cho mỗi lô hàng
    for batch in batches:
        batch.product = Product.query.get(batch.product_id)

    return render_template('trace/history.html',
                          title='Lịch sử truy xuất',
                          logs=logs,
                          pagination=pagination,
                          batches=batches,
                          batch_id=batch_id,
                          date_from=date_from,
                          date_to=date_to)

@trace_bp.route('/report')
def report():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để tạo báo cáo.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy danh sách lô hàng và sản phẩm cho form
    if session.get('user_role') == 'farmer':
        products = Product.query.filter_by(user_id=session['user_id']).all()
        product_ids = [product.id for product in products]
        batches = Batch.query.filter(Batch.product_id.in_(product_ids)).all()
    else:
        products = Product.query.all()
        batches = Batch.query.all()

    # Lấy thông tin sản phẩm cho mỗi lô hàng
    for batch in batches:
        batch.product = Product.query.get(batch.product_id)

    # Lấy các báo cáo gần đây
    reports = Report.query.filter_by(user_id=session['user_id']).order_by(Report.created_at.desc()).limit(5).all()

    return render_template('trace/report.html',
                          title='Báo cáo truy xuất',
                          batches=batches,
                          products=products,
                          reports=reports)

@trace_bp.route('/report/generate', methods=['POST'])
def generate_report():
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để tạo báo cáo.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy dữ liệu từ form
    report_type = request.form.get('report_type')
    batch_id = request.form.get('batch_id')
    product_id = request.form.get('product_id')
    date_from = request.form.get('date_from')
    date_to = request.form.get('date_to')
    format = request.form.get('format')

    # Kiểm tra dữ liệu
    if not report_type or not format:
        flash('Vui lòng điền đầy đủ thông tin.', 'error')
        return redirect(url_for('trace.report'))

    # Tạo tiêu đề báo cáo
    title = f"Báo cáo truy xuất "

    # Lấy dữ liệu cho báo cáo
    query = TraceLog.query

    if report_type == 'batch':
        if not batch_id:
            flash('Vui lòng chọn lô hàng.', 'error')
            return redirect(url_for('trace.report'))

        batch = Batch.query.get(batch_id)
        if not batch:
            flash('Lô hàng không tồn tại.', 'error')
            return redirect(url_for('trace.report'))

        # Kiểm tra quyền truy cập
        if session.get('user_role') == 'farmer':
            product = Product.query.get(batch.product_id)
            if product.user_id != session['user_id']:
                flash('Bạn không có quyền tạo báo cáo cho lô hàng này.', 'error')
                return redirect(url_for('trace.report'))

        query = query.filter(TraceLog.batch_id == batch_id)
        title += f"lô hàng #{batch_id}"

    elif report_type == 'product':
        if not product_id:
            flash('Vui lòng chọn sản phẩm.', 'error')
            return redirect(url_for('trace.report'))

        product = Product.query.get(product_id)
        if not product:
            flash('Sản phẩm không tồn tại.', 'error')
            return redirect(url_for('trace.report'))

        # Kiểm tra quyền truy cập
        if session.get('user_role') == 'farmer' and product.user_id != session['user_id']:
            flash('Bạn không có quyền tạo báo cáo cho sản phẩm này.', 'error')
            return redirect(url_for('trace.report'))

        # Lấy tất cả lô hàng của sản phẩm
        batches = Batch.query.filter_by(product_id=product_id).all()
        batch_ids = [batch.id for batch in batches]

        query = query.filter(TraceLog.batch_id.in_(batch_ids))
        title += f"sản phẩm {product.name}"

    elif report_type == 'date':
        if not date_from or not date_to:
            flash('Vui lòng chọn khoảng thời gian.', 'error')
            return redirect(url_for('trace.report'))

        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)  # Kết thúc ngày

        query = query.filter(TraceLog.timestamp >= date_from_obj, TraceLog.timestamp < date_to_obj)
        title += f"từ {date_from} đến {date_to}"

    # Nếu là nông dân, chỉ hiển thị các log của lô hàng của họ
    if session.get('user_role') == 'farmer' and report_type == 'date':
        # Lấy tất cả sản phẩm của nông dân
        farmer_products = Product.query.filter_by(user_id=session['user_id']).all()
        farmer_product_ids = [product.id for product in farmer_products]

        # Lấy tất cả lô hàng của các sản phẩm đó
        farmer_batches = Batch.query.filter(Batch.product_id.in_(farmer_product_ids)).all()
        farmer_batch_ids = [batch.id for batch in farmer_batches]

        # Lọc các log theo lô hàng
        query = query.filter(TraceLog.batch_id.in_(farmer_batch_ids))

    # Sắp xếp theo thời gian
    query = query.order_by(TraceLog.timestamp.desc())

    # Lấy kết quả
    logs = query.all()

    # Lấy thông tin lô hàng và sản phẩm cho mỗi log
    for log in logs:
        log.batch = Batch.query.get(log.batch_id)
        log.batch.product = Product.query.get(log.batch.product_id)

    # Tạo file báo cáo
    file_path = f"app/static/reports/{uuid.uuid4().hex}.{format}"

    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Giả lập tạo file báo cáo (trong thực tế sẽ sử dụng thư viện để tạo PDF, Excel, ...)
    if format == 'csv':
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['ID', 'Lô hàng', 'Sản phẩm', 'Hành động', 'Thời gian', 'IP'])
            for log in logs:
                writer.writerow([log.id, f"#{log.batch_id}", log.batch.product.name, log.action, log.timestamp.strftime('%d/%m/%Y %H:%M'), log.ip_address or ''])
    else:
        # Giả lập tạo file PDF hoặc Excel
        with open(file_path, 'w') as f:
            f.write(f"Báo cáo truy xuất\n")
            f.write(f"Tiêu đề: {title}\n")
            f.write(f"Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            f.write(f"ID\tLô hàng\tSản phẩm\tHành động\tThời gian\tIP\n")
            for log in logs:
                f.write(f"{log.id}\t#{log.batch_id}\t{log.batch.product.name}\t{log.action}\t{log.timestamp.strftime('%d/%m/%Y %H:%M')}\t{log.ip_address or ''}\n")

    # Lưu thông tin báo cáo vào cơ sở dữ liệu
    report = Report(
        title=title,
        file_path=file_path,
        file_type=format,
        user_id=session['user_id'],
        created_at=datetime.utcnow()
    )

    try:
        db.session.add(report)
        db.session.commit()
        flash('Báo cáo đã được tạo thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('trace.report'))

    # Lấy danh sách sản phẩm cho form
    if session.get('user_role') == 'farmer':
        products = Product.query.filter_by(user_id=session['user_id']).all()
    else:
        products = Product.query.all()

    return render_template('trace/report.html',
                          title='Báo cáo truy xuất',
                          batches=batches,
                          products=products,
                          reports=Report.query.filter_by(user_id=session['user_id']).order_by(Report.created_at.desc()).limit(5).all(),
                          generated_report=report)

@trace_bp.route('/report/download/<int:id>')
def download_report(id):
    # Kiểm tra đã đăng nhập chưa
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để tải báo cáo.', 'error')
        return redirect(url_for('auth.login'))

    # Lấy thông tin báo cáo
    report = Report.query.get_or_404(id)

    # Kiểm tra quyền truy cập
    if report.user_id != session['user_id']:
        flash('Bạn không có quyền tải báo cáo này.', 'error')
        return redirect(url_for('trace.report'))

    # Kiểm tra file tồn tại
    if not os.path.exists(report.file_path):
        flash('File báo cáo không tồn tại.', 'error')
        return redirect(url_for('trace.report'))

    # Tải file
    return send_file(report.file_path, as_attachment=True, download_name=f"report_{report.id}.{report.file_type}")
