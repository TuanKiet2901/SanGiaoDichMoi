import os
import psycopg2
import sys

# Lấy thông tin kết nối từ biến môi trường
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Đường dẫn tới các file SQL
SCHEMA_FILE = "docs/database/schema_agri_tracechain.sql"
ADD_COLUMN_FILE = "docs/database/add_message_column.sql"
DROP_ALL_FILE = "docs/database/drop_all_tables.sql"

def run_sql_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()
    # Kết nối tới database
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cur = conn.cursor()
    try:
        cur.execute(sql)  # Chạy toàn bộ file một lần
        conn.commit()
        print(f"Chạy file {file_path} thành công!")
    except Exception as e:
        print(f"Lỗi khi chạy file {file_path}:", e)
    finally:
        cur.close()
        conn.close()

def run_all_sql_files():
    # Chạy schema chính
    run_sql_file(SCHEMA_FILE)
    # Không chạy file thêm cột nữa
    # run_sql_file(ADD_COLUMN_FILE)
    run_sql_file("docs/database/create_triggers.sql")

def drop_all_tables():
    print("Đang xóa tất cả các bảng...")
    run_sql_file(DROP_ALL_FILE)
    print("Xóa tất cả các bảng thành công!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drop":
        drop_all_tables()
    else:
        run_all_sql_files()
