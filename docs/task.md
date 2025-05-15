# Danh sách công việc cho đồ án Agri TraceChain

## 1. Thiết lập dự án

- [x] Tạo cấu trúc thư mục dự án
- [x] Thiết kế cơ sở dữ liệu
- [x] Cài đặt môi trường phát triển (Python, Flask, MySQL)
- [x] Tạo file requirements.txt với các thư viện cần thiết
- [x] Tạo file .env cho cấu hình môi trường
- [x] Khởi tạo cơ sở dữ liệu từ file schema SQL

## 2. Phát triển Backend

### 2.1. Cấu trúc và cài đặt cơ bản
- [x] Thiết lập cấu trúc Flask app
- [x] Cấu hình kết nối cơ sở dữ liệu
- [x] Tạo các models ORM với SQLAlchemy (nếu sử dụng)
- [x] Thiết lập hệ thống xác thực và phân quyền

### 2.2. Quản lý người dùng
- [x] API đăng ký tài khoản
- [x] API đăng nhập/đăng xuất
- [x] API quản lý thông tin cá nhân
- [x] Phân quyền theo vai trò (admin, farmer, buyer)

### 2.3. Quản lý sản phẩm
- [x] API thêm/sửa/xóa sản phẩm
- [x] API tìm kiếm và lọc sản phẩm
- [x] API upload và quản lý hình ảnh sản phẩm
- [x] API phân loại sản phẩm

### 2.4. Quản lý lô hàng
- [x] API tạo lô hàng mới
- [x] API cập nhật thông tin lô hàng
- [x] API tạo và quản lý mã QR cho lô hàng
- [x] API theo dõi trạng thái lô hàng

### 2.5. Chuỗi cung ứng
- [x] API thêm các bước trong chuỗi cung ứng
- [x] API cập nhật trạng thái chuỗi cung ứng
- [x] API truy xuất thông tin chuỗi cung ứng
- [x] API lưu trữ thông tin địa điểm và thời gian

### 2.6. Truy xuất nguồn gốc
- [x] API truy xuất thông tin từ mã QR
- [x] API ghi log truy xuất
- [x] API hiển thị lịch sử truy xuất
- [x] API tạo báo cáo truy xuất

### 2.7. Tích hợp Blockchain
- [x] Cài đặt và cấu hình Web3.py
- [x] Thiết lập kết nối với Ganache (Ethereum local)
- [x] Phát triển smart contract cho truy xuất nguồn gốc
- [x] API ghi dữ liệu lên blockchain
- [x] API đọc và xác thực dữ liệu từ blockchain

### 2.8. Sàn giao dịch
- [x] API danh sách sản phẩm đang bán
- [x] API tạo đơn hàng mới
- [x] API cập nhật trạng thái đơn hàng
- [x] API quản lý đơn hàng (cho người mua và người bán)

### 2.9. Thanh toán
- [x] API tạo giao dịch thanh toán
- [x] API cập nhật trạng thái thanh toán
- [x] API xem lịch sử thanh toán
- [x] API tạo báo cáo thanh toán

### 2.10. Đánh giá sản phẩm
- [ ] API thêm đánh giá và bình luận
- [ ] API hiển thị đánh giá sản phẩm
- [ ] API tính điểm đánh giá trung bình
- [ ] API quản lý đánh giá (xóa, ẩn)

## 3. Phát triển Frontend

### 3.1. Giao diện chung
- [ ] Thiết kế layout chung với TailwindCSS
- [ ] Tạo các components tái sử dụng
- [ ] Thiết kế responsive cho desktop và mobile
- [ ] Tạo trang chủ và navigation

### 3.2. Xác thực và quản lý tài khoản
- [x] Trang đăng ký
- [x] Trang đăng nhập
- [x] Trang quản lý thông tin cá nhân
- [ ] Trang quản lý quyền (cho admin)

### 3.3. Quản lý sản phẩm
- [x] Trang danh sách sản phẩm
- [x] Form thêm/sửa sản phẩm
- [x] Trang chi tiết sản phẩm
- [x] Trang tìm kiếm và lọc sản phẩm

### 3.4. Quản lý lô hàng
- [x] Trang danh sách lô hàng
- [x] Form tạo lô hàng mới
- [x] Trang chi tiết lô hàng
- [x] Trang tạo và quản lý mã QR

### 3.5. Chuỗi cung ứng
- [x] Trang theo dõi chuỗi cung ứng
- [x] Form thêm bước trong chuỗi cung ứng
- [x] Hiển thị trực quan chuỗi cung ứng
- [x] Trang quản lý chuỗi cung ứng

### 3.6. Truy xuất nguồn gốc
- [x] Trang quét mã QR
- [x] Trang hiển thị thông tin truy xuất
- [x] Hiển thị lịch sử truy xuất
- [x] Trang xác thực thông tin blockchain

### 3.7. Sàn giao dịch
- [x] Trang hiển thị sản phẩm đang bán
- [x] Trang giỏ hàng
- [x] Trang thanh toán
- [x] Trang quản lý đơn hàng

### 3.8. Đánh giá và phản hồi
- [ ] Form đánh giá sản phẩm
- [ ] Hiển thị đánh giá trên trang sản phẩm
- [ ] Trang quản lý đánh giá đã gửi
- [ ] Hiển thị xếp hạng sản phẩm

## 4. Tích hợp QR Code

- [x] Phát triển module tạo mã QR
- [x] Tích hợp thông tin lô hàng vào mã QR
- [x] Phát triển tính năng quét mã QR
- [x] Tạo trang landing cho người dùng quét QR

## 5. Tích hợp Blockchain

- [x] Phát triển smart contract cho truy xuất nguồn gốc
- [x] Triển khai smart contract trên Ganache
- [x] Tích hợp Web3.py với backend
- [x] Phát triển cơ chế xác thực thông tin trên blockchain
- [x] Hiển thị thông tin blockchain cho người dùng

## 6. Kiểm thử

- [ ] Viết unit tests cho các API
- [ ] Viết integration tests cho luồng nghiệp vụ
- [ ] Kiểm thử bảo mật
- [ ] Kiểm thử hiệu năng
- [ ] Kiểm thử trên các thiết bị khác nhau

## 7. Triển khai

- [ ] Chuẩn bị môi trường triển khai
- [ ] Cấu hình Docker (nếu sử dụng)
- [ ] Triển khai cơ sở dữ liệu
- [ ] Triển khai backend
- [ ] Triển khai frontend
- [ ] Cấu hình HTTPS
- [ ] Kiểm tra sau triển khai

## 8. Tài liệu

- [ ] Viết tài liệu API
- [ ] Viết tài liệu hướng dẫn sử dụng
- [ ] Viết tài liệu hướng dẫn triển khai
- [ ] Viết báo cáo đồ án
- [ ] Chuẩn bị slide thuyết trình

## 9. Tính năng bổ sung (nếu có thời gian)

- [ ] Tích hợp thông báo qua email
- [ ] Tích hợp thông báo qua SMS
- [ ] Phát triển ứng dụng di động
- [ ] Tích hợp bản đồ để theo dõi vị trí
- [ ] Phát triển dashboard phân tích dữ liệu
- [ ] Tích hợp thanh toán trực tuyến thực tế

## 10. Quản lý dự án

- [ ] Lập kế hoạch chi tiết
- [ ] Phân công nhiệm vụ
- [ ] Theo dõi tiến độ
- [ ] Quản lý phiên bản
- [ ] Họp nhóm định kỳ
- [ ] Chuẩn bị demo và thuyết trình

## Ghi chú

- Cập nhật lần cuối: 21/04/2024 (11:50)
- Đã hoàn thành mục 1 (Thiết lập dự án) và mục 2.1 (Cấu trúc và cài đặt cơ bản)
- Đã hoàn thành mục 2.2 (Quản lý người dùng) và mục 3.2 (Xác thực và quản lý tài khoản)
- Đã hoàn thành mục 2.3 (Quản lý sản phẩm) và mục 3.3 (Quản lý sản phẩm - UI)
- Đã hoàn thành mục 2.4 (Quản lý lô hàng) và mục 3.4 (Quản lý lô hàng - UI)
- Đã hoàn thành mục 2.5 (Chuỗi cung ứng) và mục 3.5 (Chuỗi cung ứng - UI)
- Đã hoàn thành mục 2.6 (Truy xuất nguồn gốc) và mục 3.6 (Truy xuất nguồn gốc - UI)
- Đã hoàn thành mục 4 (Tích hợp QR Code)
- Đã hoàn thành mục 2.7 (Tích hợp Blockchain) và mục 5 (Tích hợp Blockchain)
- Đã hoàn thành mục 2.8 (Sàn giao dịch) và mục 2.9 (Thanh toán) và mục 3.7 (Sàn giao dịch - UI)
- Đang thực hiện mục 2.10 (Đánh giá sản phẩm)
- Để đánh dấu một công việc đã hoàn thành, thay đổi `[ ]` thành `[x]`
- Thêm các công việc mới vào danh sách khi cần thiết
