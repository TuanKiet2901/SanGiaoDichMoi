import os
import sys
import pymysql
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def init_database():
    # Lấy thông tin kết nối từ biến môi trường
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = int(os.getenv('DB_PORT', 3306))
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', '2025-python-agri-tracechain')

    # Kết nối đến MySQL server (không chỉ định database)
    try:
        connection = pymysql.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password
        )
        cursor = connection.cursor()

        # Tạo database nếu chưa tồn tại
        print(f"Tạo database {db_name} nếu chưa tồn tại...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}`")

        # Chọn database
        cursor.execute(f"USE `{db_name}`")

        # Đọc file schema SQL
        print("Đọc file schema SQL...")
        with open('docs/database/schema_agri_tracechain.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()

        # Thực thi script SQL
        print("Thực thi script SQL...")
        for statement in sql_script.split(';'):
            if statement.strip():
                cursor.execute(statement)

        # Commit các thay đổi
        connection.commit()

        print("Khởi tạo cơ sở dữ liệu thành công!")

    except Exception as e:
        print(f"Lỗi: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

if __name__ == "__main__":
    init_database()
