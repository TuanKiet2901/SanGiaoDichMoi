from app import create_app

app = create_app()

if __name__ == '__main__':
    # Chạy ứng dụng trên tất cả các giao diện mạng (0.0.0.0)
    # và cho phép truy cập từ các thiết bị khác trong mạng
    app.run(host='0.0.0.0', port=5000, debug=True)
