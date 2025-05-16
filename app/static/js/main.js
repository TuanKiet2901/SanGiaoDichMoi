// Main JavaScript file for Agri TraceChain

// Custom Alert Function
function showAlert(message, type = 'info', duration = 5000) {
    // Remove any existing alerts
    const existingAlerts = document.querySelectorAll('.custom-alert');
    existingAlerts.forEach(alert => {
        alert.remove();
    });

    // Create alert container
    const alertElement = document.createElement('div');
    alertElement.className = `custom-alert custom-alert-${type}`;

    // Set icon based on type
    let icon = '&#8505;'; // info icon
    if (type === 'success') icon = '&#10004;'; // checkmark
    if (type === 'error') icon = '&#10060;'; // x mark

    // Create alert content
    alertElement.innerHTML = `
        <div class="custom-alert-icon">${icon}</div>
        <div class="custom-alert-content">${message}</div>
        <button class="custom-alert-close">&times;</button>
    `;

    // Add to document
    document.body.appendChild(alertElement);

    // Show the alert (with animation)
    setTimeout(() => {
        alertElement.classList.add('show');
    }, 10);

    // Add close button functionality
    const closeButton = alertElement.querySelector('.custom-alert-close');
    closeButton.addEventListener('click', () => {
        alertElement.classList.remove('show');
        setTimeout(() => {
            alertElement.remove();
        }, 300);
    });

    // Auto dismiss
    if (duration > 0) {
        setTimeout(() => {
            if (alertElement) {
                alertElement.classList.remove('show');
                setTimeout(() => {
                    alertElement.remove();
                }, 300);
            }
        }, duration);
    }

    return alertElement;
}

// Function to update cart count
function updateCartCount() {
    // Check if user is logged in and cart count element exists
    const cartCountElement = document.getElementById('cart-count');
    if (!cartCountElement) return;

    // Fetch cart count from server
    fetch('/marketplace/cart/count')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update cart count
                cartCountElement.textContent = data.count;

                // Hide count if zero
                if (data.count === 0) {
                    cartCountElement.classList.add('hidden');
                } else {
                    cartCountElement.classList.remove('hidden');
                }
            }
        })
        .catch(error => {
            console.error('Error fetching cart count:', error);
        });
}

// Hàm cập nhật trạng thái đơn hàng
function updateOrderStatus(orderId, status) {
    fetch(`/marketplace/orders/${orderId}/update-status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.message || 'Có lỗi xảy ra khi cập nhật trạng thái đơn hàng.', 'error');
        }
    })
    .catch(error => {
        showAlert('Có lỗi xảy ra khi cập nhật trạng thái đơn hàng.', 'error');
    });
}

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
}

document.addEventListener('DOMContentLoaded', function() {
    // Update cart count when page loads
    updateCartCount();

    // Mobile menu toggle
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // Dropdown menu
    const dropdowns = document.querySelectorAll('.dropdown');

    dropdowns.forEach(function(dropdown) {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');

        if (toggle && menu) {
            // Show menu on toggle click
            toggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                menu.classList.toggle('hidden');
            });

            // Hide menu when clicking outside
            document.addEventListener('click', function(e) {
                if (!dropdown.contains(e.target)) {
                    menu.classList.add('hidden');
                }
            });
        }
    });

    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.flash-message');

    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });

    // QR Code scanner (if on scan page)
    const qrScanner = document.getElementById('qr-scanner');

    if (qrScanner) {
        // This would be replaced with actual QR scanning library implementation
        console.log('QR scanner initialized');
    }

    // Blockchain verification
    const verifyButtons = document.querySelectorAll('.verify-blockchain');

    verifyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const txHash = this.dataset.txHash;

            // Show loading state
            this.innerHTML = 'Đang xác thực...';

            // Call verification API
            fetch(`/trace/api/verify/${txHash}`)
                .then(response => response.json())
                .then(data => {
                    if (data.verified) {
                        this.innerHTML = 'Đã xác thực ✓';
                        this.classList.add('bg-green-600');
                        this.classList.remove('bg-yellow-500');
                    } else {
                        this.innerHTML = 'Không xác thực ✗';
                        this.classList.add('bg-red-600');
                        this.classList.remove('bg-yellow-500');
                    }
                })
                .catch(error => {
                    console.error('Error verifying blockchain transaction:', error);
                    this.innerHTML = 'Lỗi xác thực';
                    this.classList.add('bg-red-600');
                    this.classList.remove('bg-yellow-500');
                });
        });
    });

    // Shopping cart functionality
    const addToCartButtons = document.querySelectorAll('.add-to-cart');

    addToCartButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const productId = this.dataset.productId;
            const batchId = this.dataset.batchId;
            const quantity = document.querySelector(`#quantity-${productId}`)?.value || 1;

            // Add to cart API call
            fetch('/marketplace/cart/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    product_id: productId,
                    batch_id: batchId,
                    quantity: quantity
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showAlert(data.message, 'success');
                    updateCartCount();

                    // Cập nhật số lượng còn lại trên giao diện
                    const qtySpan = document.getElementById(`product-qty-${productId}`);
                    if (qtySpan) {
                        // Lấy số lượng hiện tại từ text, trừ đi số lượng vừa thêm
                        let match = qtySpan.textContent.match(/\((\d+)\)/);
                        if (match) {
                            let currentQty = parseInt(match[1]);
                            let newQty = currentQty - parseInt(quantity);
                            newQty = newQty < 0 ? 0 : newQty;
                            // Cập nhật text
                            qtySpan.textContent = (newQty === 0 ? 'Hết hàng' : 'Còn hàng') + ` (${newQty})`;
                            // Đổi màu badge
                            qtySpan.classList.remove('bg-green-100', 'text-green-800', 'bg-red-100', 'text-red-800');
                            if (newQty === 0) {
                                qtySpan.classList.add('bg-red-100', 'text-red-800');
                            } else {
                                qtySpan.classList.add('bg-green-100', 'text-green-800');
                            }
                        }
                    }
                } else {
                    showAlert(data.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng.', 'error');
                }
            })
            .catch(error => {
                console.error('Error adding to cart:', error);
                showAlert('Có lỗi xảy ra khi thêm vào giỏ hàng.', 'error');
            });
        });
    });

    // Gắn cho nút xác nhận đơn hàng
    const confirmOrderBtn = document.getElementById('confirm-order-btn');
    if (confirmOrderBtn) {
        confirmOrderBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            if (confirm('Bạn có chắc chắn muốn xác nhận đơn hàng này?')) {
                updateOrderStatus(orderId, 'confirmed');
            }
        });
    }
    // Gắn cho nút hủy đơn hàng
    const cancelOrderBtn = document.getElementById('cancel-order-btn');
    if (cancelOrderBtn) {
        cancelOrderBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            if (confirm('Bạn có chắc chắn muốn hủy đơn hàng này?')) {
                updateOrderStatus(orderId, 'cancelled');
            }
        });
    }
    // Gắn cho nút bắt đầu giao hàng
    const shipOrderBtn = document.getElementById('ship-order-btn');
    if (shipOrderBtn) {
        shipOrderBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            if (confirm('Bạn có chắc chắn muốn bắt đầu giao hàng cho đơn hàng này?')) {
                updateOrderStatus(orderId, 'shipped');
            }
        });
    }
    // Gắn cho nút xác nhận đã giao hàng
    const deliverOrderBtn = document.getElementById('deliver-order-btn');
    if (deliverOrderBtn) {
        deliverOrderBtn.addEventListener('click', function() {
            const orderId = this.getAttribute('data-order-id');
            if (confirm('Bạn có chắc chắn đơn hàng này đã được giao thành công?')) {
                updateOrderStatus(orderId, 'delivered');
            }
        });
    }
});

// ==== Chatbot Floating Widget Functions ====
function toggleChatbot() {
  const box = document.getElementById('chatbot-box');
  box.style.display = (box.style.display === 'none' || box.style.display === '') ? 'flex' : 'none';
}

function addMessage(message, isUser) {
  const messagesDiv = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
  messageDiv.textContent = message;
  messagesDiv.appendChild(messageDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, true);
    input.value = '';
    try {
      const response = await fetch('/chat/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
      });
      const data = await response.json();
      if (response.ok) {
        addMessage(data.response, false);
      } else {
        addMessage('Có lỗi xảy ra khi gửi tin nhắn', false);
      }
    } catch (error) {
      addMessage('Có lỗi xảy ra khi gửi tin nhắn', false);
    }
  }
// ==== End Chatbot Floating Widget Functions ====
