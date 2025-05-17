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

// Hiện/ẩn khung chat
function toggleChatbot() {
  const box = document.getElementById('chatbot-box');
  if (box.style.display === 'none' || box.style.display === '') {
    box.style.display = 'flex';
    restoreChatHistory();
    const messagesDiv = document.getElementById('chat-messages');
    if (messagesDiv.childElementCount === 0) {
      addMessage('Xin chào! Tôi là Chatbot Agri TraceChain. Bạn cần hỗ trợ gì?', false);
    }
  } else {
    box.style.display = 'none';
  }
}

// Thêm bóng chat (text)
function addMessage(message, isUser, skipSave = false) {
  const messagesDiv = document.getElementById('chat-messages');
  const messageDiv = document.createElement('div');
  messageDiv.className = isUser ? 'flex justify-end' : 'flex justify-start';
  const bubble = document.createElement('div');
  bubble.className = 'message-bubble ' + (isUser ? 'user' : 'bot');

  // Nếu là gợi ý món ăn, tách từng món thành nút
  if (!isUser && message.startsWith('Một số món ăn từ')) {
    // Tìm đoạn sau dấu ':' là danh sách món
    const idx = message.indexOf(':');
    if (idx !== -1) {
      const intro = message.slice(0, idx + 1);
      const dishes = message.slice(idx + 1).split(',').map(s => s.trim());
      bubble.innerHTML = intro + '<br>' + dishes.map(mon =>
        `<button class="dish-btn" style="margin:2px 4px;padding:2px 8px;border-radius:8px;background:#f3f3f3;border:1px solid #ccc;cursor:pointer">${mon}</button>`
      ).join('');
    } else {
      bubble.textContent = message;
    }
  } else {
    bubble.textContent = message;
  }

  messageDiv.appendChild(bubble);
  messagesDiv.appendChild(messageDiv);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  if (!skipSave) saveChatHistory();

  // Gắn sự kiện click cho các nút món ăn
  if (!isUser && message.startsWith('Một số món ăn từ')) {
    setTimeout(() => {
      document.querySelectorAll('.dish-btn').forEach(btn => {
        btn.onclick = function() {
          // Gửi tên món lên như một tin nhắn user
          document.getElementById('user-input').value = btn.textContent;
          sendMessage();
        };
      });
    }, 100);
  }
}

// Gửi tin nhắn
async function sendMessage() {
  const input = document.getElementById('user-input');
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, true);
  input.value = '';

  // Hiện typing indicator
  document.getElementById('typing-indicator').classList.remove('hidden');

  try {
    const response = await fetch('/chat/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: message })
    });
    const data = await response.json();

    // Ẩn typing indicator
    document.getElementById('typing-indicator').classList.add('hidden');

    if (response.ok) {
      if (data.type === "products") {
        if (data.response) {
          addMessage(data.response, false);
        }
        addProductCards(data.products);
        if (data.follow_up) {
          addMessage(data.follow_up, false);
        }
      } else {
        addMessage(data.response, false);
      }
    } else {
      addMessage('Có lỗi xảy ra khi gửi tin nhắn', false);
    }
  } catch (error) {
    document.getElementById('typing-indicator').classList.add('hidden');
    addMessage('Có lỗi xảy ra khi gửi tin nhắn', false);
  }
}

// ==== End Chatbot Floating Widget Functions ====

function addProductCards(products, skipSave = false) {
  const messagesDiv = document.getElementById('chat-messages');
  const wrapper = document.createElement('div');
  wrapper.className = 'grid grid-cols-1 gap-4 w-full';
  products.forEach(product => {
    const cardLink = document.createElement('a');
    cardLink.href = `/products/${product.id}`;
    cardLink.className = 'block bg-white rounded-lg shadow-md overflow-hidden flex flex-col items-center p-3 mb-2 transition hover:shadow-lg hover:scale-105 cursor-pointer';
    cardLink.innerHTML = `
      <img src="${product.image_url || '/static/img/no-image.png'}" alt="${product.name}" class="w-32 h-24 object-cover rounded">
      <div class="font-bold text-lg mt-2 text-gray-800">${product.name}</div>
      <div class="text-green-600 font-bold">${Number(product.price).toLocaleString()} đ</div>
      <div class="my-1 text-sm text-gray-600">${product.description || ''}</div>
    `;
    wrapper.appendChild(cardLink);
  });
  messagesDiv.appendChild(wrapper);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
  if (!skipSave) saveChatHistory();
}

// Hàm thêm vào giỏ hàng từ chat
function addToCartFromChat(productId) {
  fetch('/marketplace/cart/add', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({
      product_id: productId,
      quantity: 1
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      showAlert('Đã thêm vào giỏ hàng!', 'success');
      updateCartCount();
    } else {
      showAlert(data.message || 'Có lỗi xảy ra khi thêm vào giỏ hàng.', 'error');
    }
  })
  .catch(error => {
    showAlert('Có lỗi xảy ra khi thêm vào giỏ hàng.', 'error');
  });
}

function saveChatHistory() {
  const messagesDiv = document.getElementById('chat-messages');
  const history = [];
  messagesDiv.childNodes.forEach(node => {
    // Nếu là bóng chat text
    const bubble = node.querySelector('.message-bubble');
    if (bubble) {
      history.push({
        type: 'text',
        text: bubble.textContent,
        isUser: bubble.classList.contains('user')
      });
    } else if (node.querySelector('a')) {
      // Nếu là card sản phẩm
      const products = [];
      node.querySelectorAll('a').forEach(card => {
        products.push({
          id: card.href.split('/products/')[1],
          name: card.querySelector('.font-bold.text-lg').textContent,
          price: card.querySelector('.text-green-600.font-bold').textContent.replace(' đ', '').replace(/,/g, ''),
          description: card.querySelector('.my-1.text-sm.text-gray-600').textContent,
          image_url: card.querySelector('img').src
        });
      });
      history.push({
        type: 'products',
        products: products
      });
    }
  });
  localStorage.setItem('chatbot_history', JSON.stringify(history));
}

function restoreChatHistory() {
  const history = JSON.parse(localStorage.getItem('chatbot_history') || '[]');
  const messagesDiv = document.getElementById('chat-messages');
  messagesDiv.innerHTML = '';
  history.forEach(msg => {
    if (msg.type === 'text') {
      addMessage(msg.text, msg.isUser, true);
    } else if (msg.type === 'products') {
      addProductCards(msg.products, true);
    }
  });
}
