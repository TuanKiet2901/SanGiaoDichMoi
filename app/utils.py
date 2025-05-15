from app import login_manager

def init_login_manager():
    """
    Khởi tạo login manager và đăng ký user_loader
    """
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
