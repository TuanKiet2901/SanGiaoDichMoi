-- Bảng người dùng
CREATE TABLE users (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL CHECK (role IN ('admin', 'farmer', 'buyer')),
    phone VARCHAR(20),
    address NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE()
);

-- Bảng sản phẩm
CREATE TABLE products (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description NVARCHAR(MAX),
    price DECIMAL(10,2),
    category VARCHAR(100),
    image_url VARCHAR(255),
    user_id INT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_products_users FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng lô hàng
CREATE TABLE batches (
    id INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT NULL,
    qr_code VARCHAR(255),
    harvest_date DATE,
    expiry_date DATE,
    quantity INT,
    location VARCHAR(255),
    status VARCHAR(20) DEFAULT 'harvested' CHECK (status IN ('harvested', 'processing', 'shipping', 'delivered')),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_batches_products FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Bảng nhật ký truy xuất
CREATE TABLE trace_logs (
    id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id INT NULL,
    action NVARCHAR(MAX),
    [timestamp] DATETIME DEFAULT GETDATE(),
    blockchain_tx VARCHAR(255),
    CONSTRAINT FK_trace_logs_batches FOREIGN KEY (batch_id) REFERENCES batches(id)
);

-- Bảng các bước chuỗi cung ứng
CREATE TABLE supply_chain_steps (
    id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id INT NULL,
    step_name VARCHAR(100) NOT NULL,
    description NVARCHAR(MAX),
    location VARCHAR(255),
    [timestamp] DATETIME DEFAULT GETDATE(),
    handler_id INT NULL,
    blockchain_tx VARCHAR(255),
    CONSTRAINT FK_supply_chain_steps_batches FOREIGN KEY (batch_id) REFERENCES batches(id),
    CONSTRAINT FK_supply_chain_steps_users FOREIGN KEY (handler_id) REFERENCES users(id)
);

-- Bảng đơn hàng
CREATE TABLE orders (
    id INT IDENTITY(1,1) PRIMARY KEY,
    buyer_id INT NULL,
    batch_id INT NULL,
    quantity INT,
    total_price DECIMAL(10,2),
    order_date DATETIME DEFAULT GETDATE(),
    delivery_date DATETIME NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered', 'cancelled')),
    CONSTRAINT FK_orders_users FOREIGN KEY (buyer_id) REFERENCES users(id),
    CONSTRAINT FK_orders_batches FOREIGN KEY (batch_id) REFERENCES batches(id)
);

-- Bảng chi tiết đơn hàng
CREATE TABLE order_items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    batch_id INT NULL,
    quantity INT NOT NULL DEFAULT 1,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_order_items_orders FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT FK_order_items_products FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT FK_order_items_batches FOREIGN KEY (batch_id) REFERENCES batches(id)
);

-- Bảng đánh giá
CREATE TABLE reviews (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NULL,
    user_id INT NULL,
    product_id INT NOT NULL,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment NVARCHAR(MAX),
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_reviews_orders FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT FK_reviews_users FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT FK_reviews_products FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Bảng thanh toán
CREATE TABLE payments (
    id INT IDENTITY(1,1) PRIMARY KEY,
    order_id INT NOT NULL,
    user_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    message NVARCHAR(MAX),
    bank_name VARCHAR(100),
    bank_account VARCHAR(50),
    bank_account_name VARCHAR(100),
    payment_proof VARCHAR(255),
    payment_date DATETIME NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_payments_orders FOREIGN KEY (order_id) REFERENCES orders(id),
    CONSTRAINT FK_payments_users FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng lưu trữ giao dịch blockchain
CREATE TABLE blockchain_transactions (
    id INT IDENTITY(1,1) PRIMARY KEY,
    tx_hash VARCHAR(255) NOT NULL,
    related_entity VARCHAR(50) NOT NULL,
    entity_id INT NOT NULL,
    data NVARCHAR(MAX),
    [timestamp] DATETIME DEFAULT GETDATE()
);

-- Bảng giỏ hàng
CREATE TABLE carts (
    id INT IDENTITY(1,1) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_carts_users FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Bảng sản phẩm trong giỏ hàng
CREATE TABLE cart_items (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cart_id INT NOT NULL,
    product_id INT NOT NULL,
    batch_id INT NULL,
    quantity INT NOT NULL DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_cart_items_carts FOREIGN KEY (cart_id) REFERENCES carts(id),
    CONSTRAINT FK_cart_items_products FOREIGN KEY (product_id) REFERENCES products(id),
    CONSTRAINT FK_cart_items_batches FOREIGN KEY (batch_id) REFERENCES batches(id)
);
