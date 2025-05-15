
# Agri TraceChain 2025

> Đồ án Python: Xây dựng hệ thống kinh doanh và truy xuất nguồn gốc sản phẩm nông nghiệp tích hợp Blockchain.

## 🧩 Mục tiêu
- Quản lý sản phẩm nông nghiệp và chuỗi cung ứng
- Truy xuất nguồn gốc qua mã QR
- Đảm bảo tính minh bạch qua Blockchain
- Phát triển sàn giao dịch sản phẩm nông nghiệp

---

## 🛠️ Công nghệ sử dụng

| Thành phần            | Công nghệ                     |
|----------------------|-------------------------------|
| Backend & Web UI     | Python Flask + Jinja2         |
| Giao diện            | TailwindCSS                   |
| Cơ sở dữ liệu        | MySQL                         |
| QR Code              | `qrcode`, `Pillow`            |
| Blockchain tích hợp  | Web3.py + Ganache (Ethereum)  |
| ORM (tùy chọn)       | SQLAlchemy                    |
| Môi trường phát triển| Docker (tuỳ chọn), Git        |

---

## ⚙️ Cài đặt

```bash
git clone https://github.com/yourname/agri-tracechain-2025
cd agri-tracechain-2025
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Cấu hình database trong .env hoặc config.py
# Chạy schema.sql để khởi tạo database

pip install -r requirements.txt
python init_db.py
python app.py

```

---

## 📦 Tính năng chính

### 🥬 Quản lý sản phẩm & nguồn gốc
- Thêm/sửa/xoá sản phẩm
- Quản lý nhà cung cấp, lô hàng, vận chuyển
- Gán mã QR riêng cho mỗi lô sản phẩm

### 🔍 Truy xuất nguồn gốc
- Tra cứu sản phẩm qua QR code
- Hiển thị đầy đủ chuỗi cung ứng từ sản xuất → tiêu dùng

### 🔐 Tích hợp Blockchain
- Ghi log truy xuất nguồn gốc không thể chỉnh sửa
- Sử dụng Ethereum local (Ganache) + Web3.py

### 🛒 Sàn giao dịch nông sản
- Danh sách sản phẩm
- Đặt mua, quản lý đơn hàng

---

## 📄 CSDL

Xem file [`database.md`](./database.md) hoặc chạy [`schema.sql`](./schema.sql) để tạo bảng.
