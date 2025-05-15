from app import db, create_app
from app.models.user import User
from werkzeug.security import generate_password_hash
from datetime import datetime

def seed_users():
    """
    Khởi tạo dữ liệu người dùng mẫu
    """
    print("Seeding users...")
    
    # Kiểm tra xem đã có dữ liệu chưa
    if User.query.count() > 0:
        print("Users already exist, skipping seeding.")
        return
    
    # Tạo tài khoản người dùng thông thường
    user = User(
        name="Người Dùng",
        email="phuphan@gmail.com",
        password=generate_password_hash("123456789"),
        role="buyer",
        phone="0987654321",
        address="123 Đường ABC, Quận 1, TP.HCM",
        created_at=datetime.utcnow()
    )
    
    # Tạo tài khoản đại lý (farmer)
    farmer = User(
        name="Đại Lý Nông Sản",
        email="adm@gmail.com",
        password=generate_password_hash("123456789"),
        role="farmer",
        phone="0123456789",
        address="456 Đường XYZ, Quận 2, TP.HCM",
        created_at=datetime.utcnow()
    )
    
    # Thêm vào database
    db.session.add(user)
    db.session.add(farmer)
    
    # Lưu thay đổi
    db.session.commit()
    
    print(f"Created {User.query.count()} users")
    print(f"- User: email=user@example.com, password=password")
    print(f"- Farmer: email=farmer@example.com, password=password")

def run_seeds():
    """
    Chạy tất cả các hàm seed
    """
    seed_users()
    # Thêm các hàm seed khác ở đây nếu cần

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        run_seeds()
