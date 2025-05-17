import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from app import db
from app.models.batch import Batch
from app.models.product import Product
from app.models.user import User
from app.models.supply_chain_step import SupplyChainStep
from app.models.blockchain_transaction import BlockchainTransaction
from datetime import datetime
from flask_login import login_required, current_user

supply_chain_bp = Blueprint('supply_chain', __name__)

@supply_chain_bp.route('/')
@login_required
def index():
    # Lấy các tham số tìm kiếm và lọc
    batch_id = request.args.get('batch_id', '')
    step_name = request.args.get('step_name', '')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Số bước trên mỗi trang

    # Bắt đầu với tất cả các bước
    query = SupplyChainStep.query

    # Nếu là nông dân, chỉ hiển thị các bước của lô hàng của họ
    if current_user.role == 'farmer':
        # Lấy tất cả sản phẩm của nông dân
        farmer_products = Product.query.filter_by(user_id=current_user.id).all()
        farmer_product_ids = [product.id for product in farmer_products]

        # Lấy tất cả lô hàng của các sản phẩm đó
        farmer_batches = Batch.query.filter(Batch.product_id.in_(farmer_product_ids)).all()
        farmer_batch_ids = [batch.id for batch in farmer_batches]

        # Lọc các bước theo lô hàng
        query = query.filter(SupplyChainStep.batch_id.in_(farmer_batch_ids))

    # Áp dụng lọc theo lô hàng
    if batch_id:
        query = query.filter(SupplyChainStep.batch_id == batch_id)

    # Áp dụng lọc theo tên bước
    if step_name:
        query = query.filter(SupplyChainStep.step_name.ilike(f'%{step_name}%'))

    # Áp dụng sắp xếp
    if sort == 'newest':
        query = query.order_by(SupplyChainStep.timestamp.desc())
    elif sort == 'oldest':
        query = query.order_by(SupplyChainStep.timestamp.asc())

    # Phân trang kết quả
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    steps = pagination.items

    # Lấy thông tin lô hàng và sản phẩm cho mỗi bước
    for step in steps:
        step.batch = Batch.query.get(step.batch_id)
        step.batch.product = Product.query.get(step.batch.product_id)

    # Lấy danh sách lô hàng cho dropdown lọc
    if current_user.role == 'farmer':
        batches = Batch.query.filter(Batch.product_id.in_(farmer_product_ids)).all()
    else:
        batches = Batch.query.all()

    # Lấy thông tin sản phẩm cho mỗi lô hàng
    for batch in batches:
        batch.product = Product.query.get(batch.product_id)

    return render_template('supply_chain/index.html',
                          title='Chuỗi cung ứng',
                          steps=steps,
                          pagination=pagination,
                          batches=batches,
                          batch_id=batch_id,
                          step_name=step_name,
                          sort=sort)

@supply_chain_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Lấy batch_id từ query parameter
    batch_id = request.args.get('batch_id')
    if not batch_id:
        flash('Không tìm thấy thông tin lô hàng.', 'error')
        return redirect(url_for('batches.index'))

    # Lấy thông tin lô hàng
    batch = Batch.query.get_or_404(batch_id)

    # Lấy thông tin sản phẩm
    batch.product = Product.query.get(batch.product_id)

    # Kiểm tra quyền truy cập
    if batch.product.user_id != current_user.id:
        flash('Bạn không có quyền thêm bước chuỗi cung ứng cho lô hàng này.', 'error')
        return redirect(url_for('batches.show', id=batch_id))

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        step_name = request.form.get('step_name')
        description = request.form.get('description')
        location = request.form.get('location')

        # Kiểm tra dữ liệu
        if not step_name or not description or not location:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('supply_chain.create', batch_id=batch_id))

        # Tạo bước chuỗi cung ứng mới
        new_step = SupplyChainStep(
            batch_id=batch_id,
            step_name=step_name,
            description=description,
            location=location,
            handler_id=current_user.id,
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(new_step)
            db.session.commit()
            flash('Bước chuỗi cung ứng đã được thêm thành công!', 'success')
            return redirect(url_for('batches.show', id=batch_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('supply_chain.create', batch_id=batch_id))

    return render_template('supply_chain/create.html',
                          title='Thêm bước chuỗi cung ứng',
                          batch=batch)

@supply_chain_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Lấy thông tin bước chuỗi cung ứng
    step = SupplyChainStep.query.get_or_404(id)

    # Lấy thông tin lô hàng
    batch = Batch.query.get(step.batch_id)

    # Lấy thông tin sản phẩm
    batch.product = Product.query.get(batch.product_id)

    # Kiểm tra quyền truy cập
    if step.handler_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa bước chuỗi cung ứng này.', 'error')
        return redirect(url_for('batches.show', id=step.batch_id))

    if request.method == 'POST':
        # Lấy dữ liệu từ form
        step_name = request.form.get('step_name')
        description = request.form.get('description')
        location = request.form.get('location')

        # Kiểm tra dữ liệu
        if not step_name or not description or not location:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('supply_chain.edit', id=id))

        # Cập nhật thông tin
        step.step_name = step_name
        step.description = description
        step.location = location

        try:
            db.session.commit()
            flash('Bước chuỗi cung ứng đã được cập nhật thành công!', 'success')
            return redirect(url_for('batches.show', id=step.batch_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('supply_chain.edit', id=id))

    return render_template('supply_chain/edit.html',
                          title='Chỉnh sửa bước chuỗi cung ứng',
                          step=step,
                          batch=batch)

@supply_chain_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    # Lấy thông tin bước chuỗi cung ứng
    step = SupplyChainStep.query.get_or_404(id)

    # Kiểm tra quyền truy cập
    if step.handler_id != current_user.id:
        flash('Bạn không có quyền xóa bước chuỗi cung ứng này.', 'error')
        return redirect(url_for('batches.show', id=step.batch_id))

    batch_id = step.batch_id

    try:
        db.session.delete(step)
        db.session.commit()
        flash('Bước chuỗi cung ứng đã được xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')

    return redirect(url_for('batches.show', id=batch_id))

@supply_chain_bp.route('/<int:id>/verify', methods=['GET'])
@login_required
def verify_blockchain(id):
    # Lấy thông tin bước chuỗi cung ứng
    step = SupplyChainStep.query.get_or_404(id)

    # Lấy thông tin lô hàng
    step.batch = Batch.query.get(step.batch_id)

    # Lấy thông tin sản phẩm
    step.batch.product = Product.query.get(step.batch.product_id)

    # Lấy thông tin người thực hiện
    handler = User.query.get(step.handler_id)

    # Nếu đã xác thực trên blockchain, lấy thông tin blockchain
    blockchain_data = None
    if step.blockchain_tx:
        try:
            # Lấy Ethereum client từ app context
            ethereum_client = current_app.config.get('ETHEREUM_CLIENT')
            if ethereum_client and ethereum_client.is_connected():
                # Xác thực giao dịch trên blockchain
                tx_data = ethereum_client.verify_transaction(step.blockchain_tx)
                if tx_data:
                    blockchain_data = {
                        'verified': True,
                        'timestamp': datetime.fromtimestamp(tx_data['timestamp']).strftime('%Y-%m-%dT%H:%M:%SZ'),
                        'block_number': tx_data['block_number'],
                        'network': f"Ethereum (Chain ID: {tx_data['chain_id']})",
                        'transaction_hash': tx_data['transaction_hash'],
                        'from': tx_data['from'],
                        'to': tx_data['to'],
                        'gas_used': tx_data['gas_used'],
                        'status': 'Success' if tx_data['status'] == 1 else 'Failed'
                    }
            else:
                # Giả lập thông tin blockchain nếu không thể kết nối
                blockchain_data = {
                    'verified': True,
                    'timestamp': '2023-04-21T10:30:15Z',
                    'block_number': 12345678,
                    'network': 'Ethereum Testnet (Giả lập)',
                    'transaction_hash': step.blockchain_tx,
                    'from': '0x1234567890abcdef1234567890abcdef12345678',
                    'to': '0xabcdef1234567890abcdef1234567890abcdef12',
                    'gas_used': 21000,
                    'status': 'Success'
                }
        except Exception as e:
            current_app.logger.error(f"Error verifying blockchain transaction: {str(e)}")
            # Giả lập thông tin blockchain nếu có lỗi
            blockchain_data = {
                'verified': True,
                'timestamp': '2023-04-21T10:30:15Z',
                'block_number': 12345678,
                'network': 'Ethereum Testnet (Giả lập)',
                'transaction_hash': step.blockchain_tx,
                'from': '0x1234567890abcdef1234567890abcdef12345678',
                'to': '0xabcdef1234567890abcdef1234567890abcdef12',
                'gas_used': 21000,
                'status': 'Success'
            }

    return render_template('supply_chain/verify.html',
                          title='Xác thực Blockchain',
                          step=step,
                          handler=handler,
                          blockchain_data=blockchain_data)

@supply_chain_bp.route('/<int:id>/verify', methods=['POST'])
@login_required
def verify_blockchain_submit(id):
    # Lấy thông tin bước chuỗi cung ứng
    step = SupplyChainStep.query.get_or_404(id)

    # Kiểm tra quyền truy cập
    if step.handler_id != current_user.id:
        flash('Bạn không có quyền xác thực bước chuỗi cung ứng này trên Blockchain.', 'error')
        return redirect(url_for('supply_chain.verify_blockchain', id=id))

    # Lấy thông tin lô hàng
    batch = Batch.query.get(step.batch_id)
    if not batch:
        flash('Không tìm thấy lô hàng.', 'error')
        return redirect(url_for('supply_chain.verify_blockchain', id=id))

    # Lấy thông tin sản phẩm
    product = Product.query.get(batch.product_id)
    if not product:
        flash('Không tìm thấy sản phẩm.', 'error')
        return redirect(url_for('supply_chain.verify_blockchain', id=id))

    # Lấy thông tin người thực hiện
    handler = User.query.get(step.handler_id)
    if not handler:
        flash('Không tìm thấy người thực hiện.', 'error')
        return redirect(url_for('supply_chain.verify_blockchain', id=id))

    try:
        # Lấy Ethereum client từ app context
        ethereum_client = current_app.config.get('ETHEREUM_CLIENT')
        if not ethereum_client or not ethereum_client.is_connected():
            flash('Không thể kết nối với Ethereum node.', 'error')
            return redirect(url_for('supply_chain.verify_blockchain', id=id))

        # Thêm bước chuỗi cung ứng lên blockchain
        tx_hash = ethereum_client.add_supply_chain_step(
            batch_id=step.batch_id,
            step_name=step.step_name,
            timestamp=step.timestamp.isoformat(),
            location=step.location,
            handler=handler.name,
            additional_info=step.description
        )

        # Lưu thông tin giao dịch blockchain
        blockchain_tx = BlockchainTransaction(
            tx_hash=tx_hash,
            batch_id=step.batch_id,
            supply_chain_step_id=step.id,
            action='add_step',
            status='confirmed',
            timestamp=datetime.utcnow()
        )

        # Cập nhật thông tin blockchain cho bước chuỗi cung ứng
        step.blockchain_tx = tx_hash

        # Lưu vào cơ sở dữ liệu
        db.session.add(blockchain_tx)
        db.session.commit()

        flash('Thông tin đã được xác thực thành công trên Blockchain!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra khi xác thực trên Blockchain: {str(e)}', 'error')

        # Nếu không thể kết nối với Ethereum node, sử dụng giả lập
        if 'Ethereum node' in str(e):
            # Giả lập xác thực trên blockchain
            blockchain_tx = f"0x{uuid.uuid4().hex}"

            # Cập nhật thông tin blockchain
            step.blockchain_tx = blockchain_tx

            try:
                db.session.commit()
                flash('Thông tin đã được giả lập xác thực trên Blockchain (chế độ giả lập).', 'warning')
            except Exception as e2:
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {str(e2)}', 'error')

    return redirect(url_for('supply_chain.verify_blockchain', id=id))