import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager
from dotenv import load_dotenv
from flask_mail import Mail, Message

# Load biến môi trường từ file .env
load_dotenv()

# Khởi tạo các extension
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
mail = Mail()
login_manager = LoginManager()

from app.models.user import User
from app.models.chat_history import ChatHistory

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)

    # Cấu hình ứng dụng
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')    
    app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', '240421')
    #app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Đặt UPLOAD_FOLDER
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
    # app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    app.config['QR_CODE_DIR'] = os.getenv('QR_CODE_DIR', 'static/qrcodes')
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'kiet81036@gmail.com'
    app.config['MAIL_PASSWORD'] = 'yfqjutgvjsfkjymj'
    app.config['MAIL_DEFAULT_SENDER'] = 'kiet81036@gmail.com'

    # Cấu hình session cho production
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Khởi tạo các extension với app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Cấu hình CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # Không giới hạn thời gian cho CSRF token
    csrf.init_app(app)

    # Import các model
    with app.app_context():
        from app.models.user import User
        from app.models.product import Product
        from app.models.batch import Batch
        from app.models.trace_log import TraceLog
        from app.models.supply_chain_step import SupplyChainStep
        from app.models.order import Order
        from app.models.review import Review
        from app.models.payment import Payment
        from app.models.blockchain_transaction import BlockchainTransaction
        from app.models.chat_history import ChatHistory

    # Đăng ký các blueprint
    from app.controllers.main import main_bp
    from app.controllers.auth import auth_bp
    from app.controllers.products import products_bp
    from app.controllers.batches import batches_bp
    from app.controllers.trace import trace_bp
    from app.controllers.marketplace import marketplace_bp
    from app.controllers.supply_chain import supply_chain_bp
    from app.controllers.payment import payment_bp
    from app.controllers.reviews import reviews_bp
    from app.chatbot import chat_api  # Sửa import chat_api

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(products_bp, url_prefix='/products')
    app.register_blueprint(batches_bp, url_prefix='/batches')
    app.register_blueprint(trace_bp, url_prefix='/trace')
    app.register_blueprint(marketplace_bp, url_prefix='/marketplace')
    app.register_blueprint(supply_chain_bp, url_prefix='/supply-chain')
    app.register_blueprint(payment_bp, url_prefix='/payment')
    app.register_blueprint(reviews_bp, url_prefix='/reviews')
    app.register_blueprint(chat_api, url_prefix='/chat')  # Sửa đăng ký chat_api
    csrf.exempt(chat_api)

    # Tạo thư mục uploads nếu chưa tồn tại
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'qrcodes'), exist_ok=True)

    print(f"Static folder: {app.static_folder}")
    print(f"Upload folder: {app.config['UPLOAD_FOLDER']}")

    # Khởi tạo blockchain integration
    try:
        from app.blockchain.ethereum import EthereumClient
        ganache_url = os.getenv('GANACHE_URL', 'http://127.0.0.1:7545')
        print("Initializing Ethereum client with URL:", ganache_url)
        
        # Thêm dấu / nếu chưa có
        if not ganache_url.endswith('/'):
            ganache_url = ganache_url + '/'
        
        app.config['ETHEREUM_CLIENT'] = EthereumClient(ganache_url)
        
        if app.config['ETHEREUM_CLIENT'].is_connected():
            app.logger.info(f'Ethereum client initialized successfully with URL: {ganache_url}')
            print("Web3 connected: True")
        else:
            app.logger.error('Failed to connect to Ethereum node')
            print("Web3 connected: False")
        
    except Exception as e:
        app.logger.error(f'Failed to initialize Ethereum client: {str(e)}')
        print(f"Error initializing Ethereum client: {str(e)}")

    mail.init_app(app)

    return app
