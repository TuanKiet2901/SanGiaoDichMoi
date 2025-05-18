import os
import uuid
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models.product import Product
from app.models.user import User
from app.models.batch import Batch
from app.models.review import Review
import cloudinary.uploader
from flask_login import login_required, current_user

products_bp = Blueprint('products', __name__)

# Helper function to check if file is allowed
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper function to save uploaded file
def save_image(file):
    print(f"save_image called with file: {file}")
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        print(f"Secured filename: {filename}")
        # Add unique identifier to prevent filename collisions
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        print(f"Unique filename: {unique_filename}")

        # Get upload folder from app config
        upload_folder = current_app.config['UPLOAD_FOLDER']
        print(f"Upload folder from config: {upload_folder}")

        # Create uploads directory if it doesn't exist
        os.makedirs(upload_folder, exist_ok=True)
        print(f"Uploads directory created/verified: {upload_folder}")

        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        print(f"Full file path: {file_path}")

        try:
            file.save(file_path)
            print(f"File saved successfully at: {file_path}")

            # Return URL path for static file
            # We need to return a URL path that the browser can access
            # This should be relative to the static folder
            # Assuming the file is saved in app/static/uploads, the URL should be /static/uploads/...
            return f"/static/uploads/{unique_filename}"
        except Exception as e:
            print(f"Error saving file: {str(e)}")
            return None
    return None

@products_bp.route('/')
def index():
    # Get query parameters for filtering and sorting
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'newest')
    page = request.args.get('page', 1, type=int)
    per_page = 12  # Number of products per page

    # Start with all products
    query = Product.query

    # Apply search filter
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%') |
                            Product.description.ilike(f'%{search}%'))

    # Apply category filter
    if category:
        query = query.filter(Product.category == category)

    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort == 'name_desc':
        query = query.order_by(Product.name.desc())

    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items

    # Kiểm tra và cập nhật trạng thái sản phẩm hết hạn
    for product in products:
        if product.is_expired:
            # Cập nhật số lượng tồn kho của các lô hàng hết hạn về 0
            for batch in product.batches:
                if batch.expiry_date and batch.expiry_date < datetime.now().date():
                    batch.quantity = 0
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Error updating expired batch quantities: {str(e)}")

    return render_template('products/index.html',
                          title='Sản phẩm',
                          products=products,
                          pagination=pagination,
                          search=search,
                          category=category,
                          sort=sort)

@products_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Check if user is logged in and is a farmer
    if current_user.role != 'farmer':
        flash('Chỉ nhà cung cấp mới có thể thêm sản phẩm mới.', 'error')
        return redirect(url_for('products.index'))

    if request.method == 'POST':
        # Debug request.files
        print(f"Files in request: {request.files}")
        print(f"'image' in request.files: {'image' in request.files}")

        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        image = request.files.get('image')

        print(f"Image object: {image}")

        # Validate required fields
        if not name or not description or not category or not price:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('products.create'))

        # Save image if provided
        image_url = None
        if image:
            print(f"Image received: {image.filename}")
            if image.filename == '':
                print("Empty filename")
            elif not allowed_file(image.filename):
                print(f"File not allowed: {image.filename}")
                flash('Chỉ chấp nhận file ảnh: PNG, JPG, JPEG, GIF, WEBP', 'error')
            else:
                # Upload lên Cloudinary
                result = cloudinary.uploader.upload(image)
                image_url = result.get('secure_url')
                print(f"Image uploaded to Cloudinary with URL: {image_url}")

        # Create new product
        new_product = Product(
            name=name,
            description=description,
            category=category,
            price=price,
            image_url=image_url,
            user_id=current_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        try:
            db.session.add(new_product)
            db.session.commit()
            flash('Sản phẩm đã được tạo thành công!', 'success')
            return redirect(url_for('products.show', id=new_product.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('products.create'))

    return render_template('products/create.html', title='Thêm sản phẩm')

@products_bp.route('/<int:id>')
def show(id):
    # Get product by ID
    product = Product.query.get_or_404(id)

    # Get user information
    producer = User.query.get(product.user_id)

    # Get available batches for this product
    batches = Batch.query.filter_by(product_id=id).all()

    # Get reviews for this product
    reviews = Review.query.filter_by(product_id=id).order_by(Review.created_at.desc()).all()

    # Get user information for each review
    for review in reviews:
        review.user = User.query.get(review.user_id)

    return render_template('products/detail.html',
                          title=product.name,
                          product=product,
                          producer=producer,
                          batches=batches,
                          reviews=reviews)

@products_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    # Get product by ID
    product = Product.query.get_or_404(id)

    # Check if user is the owner of the product
    if product.user_id != current_user.id:
        flash('Bạn không có quyền chỉnh sửa sản phẩm này.', 'error')
        return redirect(url_for('products.show', id=id))

    if request.method == 'POST':
        # Debug request.files
        print(f"Edit - Files in request: {request.files}")
        print(f"Edit - 'image' in request.files: {'image' in request.files}")

        # Get form data
        name = request.form.get('name')
        description = request.form.get('description')
        category = request.form.get('category')
        price = request.form.get('price')
        image = request.files.get('image')

        print(f"Edit - Image object: {image}")

        # Validate required fields
        if not name or not description or not category or not price:
            flash('Vui lòng điền đầy đủ thông tin.', 'error')
            return redirect(url_for('products.edit', id=id))

        # Update product data
        product.name = name
        product.description = description
        product.category = category
        product.price = price
        product.updated_at = datetime.utcnow()

        # Save new image if provided
        if image and image.filename:
            print(f"Edit - Image received: {image.filename}")
            if image.filename == '':
                print("Edit - Empty filename")
            elif not allowed_file(image.filename):
                print(f"Edit - File not allowed: {image.filename}")
                flash('Chỉ chấp nhận file ảnh: PNG, JPG, JPEG, GIF, WEBP', 'error')
            else:
                # Upload lên Cloudinary
                result = cloudinary.uploader.upload(image)
                image_url = result.get('secure_url')
                print(f"Edit - Image uploaded to Cloudinary with URL: {image_url}")
                if image_url:
                    product.image_url = image_url

        try:
            db.session.commit()
            flash('Sản phẩm đã được cập nhật thành công!', 'success')
            return redirect(url_for('products.show', id=id))
        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}', 'error')
            return redirect(url_for('products.edit', id=id))

    return render_template('products/edit.html',
                          title='Chỉnh sửa sản phẩm',
                          product=product)

@products_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Vui lòng đăng nhập để xóa sản phẩm.', 'error')
        return redirect(url_for('auth.login'))

    # Get product by ID
    product = Product.query.get_or_404(id)

    # Check if user is the owner of the product
    if product.user_id != session['user_id']:
        flash('Bạn không có quyền xóa sản phẩm này.', 'error')
        return redirect(url_for('products.show', id=id))

    try:
        # Check if there are any batches associated with this product
        batches = Batch.query.filter_by(product_id=id).all()
        if batches:
            flash('Không thể xóa sản phẩm vì có lô hàng liên kết.', 'error')
            return redirect(url_for('products.edit', id=id))

        # Delete the product
        db.session.delete(product)
        db.session.commit()
        flash('Sản phẩm đã được xóa thành công!', 'success')
        return redirect(url_for('products.index'))
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'error')
        return redirect(url_for('products.edit', id=id))
