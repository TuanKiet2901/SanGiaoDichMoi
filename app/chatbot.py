import os
import openai
from app.models.product import Product
from flask import current_app

class Chatbot:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("DEBUG - OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))
        self.conversation_history = []

    def get_products_info(self):
        with current_app.app_context():
            products = Product.query.all()
            info = "Danh sách tất cả sản phẩm:\n"
            for p in products:
                info += (
                    f"- {p.name}: {p.price} VNĐ. "
                    f"{p.description or ''} "
                    f"(Danh mục: {p.category or 'Không có'}) "
                    f"Ảnh: {p.image_url or 'Không có'}\n"
                )
            return info

    def get_batches_info(self):
        # Truy vấn bảng batches, trả về thông tin lô hàng
        pass

    def get_orders_info(self, user_id=None):
        # Truy vấn bảng orders, order_items, trả về đơn hàng của user
        pass

    def get_reviews_info(self, product_id=None):
        # Truy vấn bảng reviews, trả về đánh giá sản phẩm
        pass

    def get_product_by_name(self, name):
        with current_app.app_context():
            product = Product.query.filter(Product.name.ilike(f"%{name}%")).first()
            if product:
                info = (
                    f"Tên: {product.name}\n"
                    f"Giá: {product.price} VNĐ\n"
                    f"Mô tả: {product.description or 'Không có'}\n"
                    f"Danh mục: {product.category or 'Không có'}\n"
                    f"Ảnh: {product.image_url or 'Không có'}"
                )
                return info
            else:
                return "Không tìm thấy sản phẩm nào phù hợp với tên bạn nhập."

    def get_response(self, user_message):
        try:
            # Truy vấn sản phẩm theo tên nếu phát hiện từ khóa "sản phẩm" + tên
            if "sản phẩm" in user_message.lower():
                # Tìm tên sản phẩm trong câu hỏi (giả sử tên nằm sau từ "sản phẩm")
                parts = user_message.lower().split("sản phẩm")
                if len(parts) > 1 and parts[1].strip():
                    product_name = parts[1].strip()
                    info = self.get_product_by_name(product_name)
                    prompt = (
                        f"Người dùng hỏi: {user_message}\n"
                        f"Dưới đây là thông tin sản phẩm tìm được:\n{info}\n"
                        "Chỉ trả lời dựa trên dữ liệu này, không bịa thêm."
                    )
                else:
                    # Nếu không có tên, trả về tất cả sản phẩm như cũ
                    info = self.get_products_info()
                    prompt = (
                        f"Người dùng hỏi: {user_message}\n"
                        f"Dưới đây là danh sách sản phẩm thực tế trên website:\n{info}\n"
                        "Chỉ trả lời dựa trên dữ liệu này, không bịa thêm sản phẩm nào khác."
                    )
            elif "lô hàng" in user_message.lower():
                info = self.get_batches_info()
                prompt = f"{user_message}\nDữ liệu thực tế từ website: {info}"
            elif "đơn hàng" in user_message.lower():
                info = self.get_orders_info()
                prompt = f"{user_message}\nDữ liệu thực tế từ website: {info}"
            else:
                prompt = user_message

            print("DEBUG - prompt:", prompt)

            self.conversation_history.append({"role": "user", "content": prompt})
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=self.conversation_history,
                max_tokens=150,
                temperature=0.7
            )
            bot_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": bot_response})
            return bot_response
        except Exception as e:
            print("Chatbot error:", e)
            return "Xin lỗi, tôi đang gặp một số vấn đề kỹ thuật. Vui lòng thử lại sau."

    def clear_history(self):
        self.conversation_history = []