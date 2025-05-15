import multiprocessing

# Số lượng worker
workers = multiprocessing.cpu_count() * 2 + 1

# Thời gian timeout
timeout = 120

# Số lượng kết nối tối đa
worker_connections = 1000

# Loại worker
worker_class = 'sync'

# Thời gian chờ worker khởi động
graceful_timeout = 120

# Thời gian chờ worker kết thúc
keepalive = 5

# Log level
loglevel = 'info'

# Access log
accesslog = '-'

# Error log
errorlog = '-' 