import os
import uuid
import qrcode
import base64
from io import BytesIO
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_required, current_user
from app import db
from app.models.batch import Batch
from app.models.product import Product
from app.models.user import User
from app.models.supply_chain_step import SupplyChainStep
import json

batches_bp = Blueprint('batches', __name__)

@batches_bp.route('/')
@login_required
def index():
    # Get query parameters for filtering and sorting
    product_id = request.args.get('product_id', '')
    status = request.args.get('status', '')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of batches per page

    # Start with all batches
    query = Batch.query

    # If user is a farmer, only show their batches
    if current_user.role == 'farmer':
        # Get all products owned by the farmer
        farmer_products = Product.query.filter_by(user_id=current_user.id).all()
        farmer_product_ids = [product.id for product in farmer_products]
        query = query.filter(Batch.product_id.in_(farmer_product_ids))

    # Apply product filter
    if product_id:
        query = query.filter(Batch.product_id == product_id)

    # Apply status filter
    if status:
        query = query.filter(Batch.status == status)

    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Batch.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Batch.created_at.asc())
    elif sort == 'harvest_date_asc':
        query = query.order_by(Batch.harvest_date.asc())
    elif sort == 'harvest_date_desc':
        query = query.order_by(Batch.harvest_date.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    batches = pagination.items

    # Load product information for each batch
    for batch in batches:
        batch.product = Product.query.get(batch.product_id)

    # Get products for filter dropdown
    if current_user.role == 'farmer':
        products = Product.query.filter_by(user_id=current_user.id).all()
    else:
        products = Product.query.all()

    return render_template('batches/index.html',
                          title='Lô hàng',
                          batches=batches,
                          pagination=pagination,
                          products=products,
                          product_id=product_id,
                          status=status,
                          sort=sort)

@batches_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Check if user is a farmer
    if current_user.role != 'farmer':
        flash('Chỉ nhà cung cấp mới có thể thêm lô hàng mới.', 'error')
        return redirect(url_for('batches.index'))

    # Get product_id from query parameter (if coming from product page)
    product_id = request.args.get('product_id')

    # Get all products owned by the farmer
    products = Product.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Get form data
        product_id = request.form.get('product_id')
        harvest_date = request.form.get('harvest_date')
        expiry_date = request.form.get('expiry_date')
        quantity = int(request.form.get('quantity'))
        location_data = json.loads(request.form.get('location'))
        status = request.form.get('status')

        # Validate required fields
        if not product_id or not harvest_date or not quantity or not location_data or not status:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('batches.create'))

        # Format location string
        location_parts = [
            location_data['address'],
            location_data['hamlet'] if location_data['hamlet'] else '',
            location_data['ward'],
            location_data['district'],
            location_data['province']
        ]
        location = ', '.join(filter(None, location_parts))

        # Check if product belongs to the farmer
        product = Product.query.get(product_id)
        if not product or product.user_id != current_user.id:
            flash('Sản phẩm không hợp lệ.', 'error')
            return redirect(url_for('batches.create'))

        try:
            # Create new batch
            new_batch = Batch(
                product_id=product_id,
                harvest_date=datetime.strptime(harvest_date, '%Y-%m-%d').date(),
                expiry_date=datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None,
                quantity=quantity,
                location=location,
                status=status,
                created_at=datetime.utcnow()
            )
            db.session.add(new_batch)

            db.session.commit()
            flash('Lô hàng đã được tạo thành công!', 'success')
            return redirect(url_for('batches.show', id=new_batch.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('batches.create'))

    return render_template('batches/create.html',
                          title='Thêm lô hàng',
                          products=products,
                          product_id=product_id)

@batches_bp.route('/<int:id>')
@login_required
def show(id):
    # Get batch by ID
    batch = Batch.query.get_or_404(id)

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Load user information for product
    batch.product.user = User.query.get(batch.product.user_id)

    # Load supply chain steps
    supply_chain_steps = SupplyChainStep.query.filter_by(batch_id=id).order_by(SupplyChainStep.timestamp.asc()).all()

    return render_template('batches/show.html',
                          title=f'Lô hàng #{id}',
                          batch=batch,
                          supply_chain_steps=supply_chain_steps)

@batches_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Get batch by ID
    batch = Batch.query.get_or_404(id)

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Check if user is the owner of the product
    if batch.product.user_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa lô hàng này.', 'error')
        return redirect(url_for('batches.show', id=id))

    # Get all products owned by the farmer
    products = Product.query.filter_by(user_id=current_user.id).all()

    if request.method == 'POST':
        # Get form data
        product_id = request.form.get('product_id')
        harvest_date = request.form.get('harvest_date')
        expiry_date = request.form.get('expiry_date')
        quantity = request.form.get('quantity')
        location = request.form.get('location')
        status = request.form.get('status')

        # Validate required fields
        if not product_id or not harvest_date or not quantity or not location or not status:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('batches.edit', id=id))

        # Check if product belongs to the farmer
        product = Product.query.get(product_id)
        if not product or product.user_id != current_user.id:
            flash('Sản phẩm không hợp lệ.', 'error')
            return redirect(url_for('batches.edit', id=id))

        # Update batch data
        batch.product_id = product_id
        batch.harvest_date = datetime.strptime(harvest_date, '%Y-%m-%d').date()
        batch.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date() if expiry_date else None
        batch.quantity = quantity
        batch.location = location
        batch.status = status

        try:
            db.session.commit()
            flash('Lô hàng đã được cập nhật thành công!', 'success')
            return redirect(url_for('batches.show', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('batches.edit', id=id))

    return render_template('batches/edit.html',
                          title='Chỉnh sửa lô hàng',
                          batch=batch,
                          products=products)

@batches_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Get batch by ID
    batch = Batch.query.get_or_404(id)

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Check if user is the owner of the product
    if batch.product.user_id != current_user.id:
        flash('Bạn không có quyền xóa lô hàng này.', 'error')
        return redirect(url_for('batches.show', id=id))

    try:
        # Check if there are any supply chain steps associated with this batch
        steps = SupplyChainStep.query.filter_by(batch_id=id).all()
        if steps:
            flash('Không thể xóa lô hàng vì có các bước chuỗi cung ứng liên kết.', 'error')
            return redirect(url_for('batches.edit', id=id))

        # Delete the batch
        db.session.delete(batch)
        db.session.commit()
        flash('Lô hàng đã được xóa thành công!', 'success')
        return redirect(url_for('batches.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('batches.edit', id=id))

@batches_bp.route('/<int:id>/generate_qr', methods=['GET'])
@login_required
def generate_qr(id):
    # Get batch by ID
    batch = Batch.query.get_or_404(id)

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Check if user is the owner of the product
    if batch.product.user_id != current_user.id:
        flash('Bạn không có quyền tạo mã QR cho lô hàng này.', 'error')
        return redirect(url_for('batches.show', id=id))

    # Generate a unique QR code identifier
    qr_code = f"batch_{id}_{uuid.uuid4().hex[:8]}"

    # Update batch with QR code
    batch.qr_code = qr_code

    try:
        db.session.commit()
        flash('Mã QR đã được tạo thành công!', 'success')
        return redirect(url_for('batches.qrcode', id=id))
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('batches.show', id=id))

@batches_bp.route('/<int:id>/qrcode')
@login_required
def qrcode(id):
    # Get batch by ID
    batch = Batch.query.get_or_404(id)

    # Check if batch has QR code
    if not batch.qr_code:
        flash('Lô hàng này chưa có mã QR.', 'error')
        return redirect(url_for('batches.show', id=id))

    # Load product information
    batch.product = Product.query.get(batch.product_id)

    # Sử dụng URL công khai từ file .env thay vì localhost
    public_url = os.getenv('PUBLIC_URL', 'http://tracechain.id.vn')

    # Tạo URL truy xuất
    trace_url = f"{public_url}{url_for('trace.batch_info', qr_code=batch.qr_code)}"

    # Generate a simple QR code image URL using an external service
    # This is a fallback method when the qrcode library is not available
    qr_code_image = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={trace_url}"
    print(f"Using external QR code service for URL: {trace_url}")

    return render_template('batches/qrcode.html',
                          title='Mã QR lô hàng',
                          batch=batch,
                          qr_code_image=qr_code_image,
                          trace_url=trace_url)
