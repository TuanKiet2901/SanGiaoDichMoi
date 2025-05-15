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
                info += f"- {p.name}: {p.price} VNĐ. {p.description}\n"
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

    def get_response(self, user_message):
        try:
            if "sản phẩm" in user_message.lower():
                info = self.get_products_info()
                prompt = f"{user_message}\nDữ liệu thực tế từ website: {info}"
            elif "lô hàng" in user_message.lower():
                info = self.get_batches_info()
                prompt = f"{user_message}\nDữ liệu thực tế từ website: {info}"
            elif "đơn hàng" in user_message.lower():
                info = self.get_orders_info()
                prompt = f"{user_message}\nDữ liệu thực tế từ website: {info}"
            else:
                prompt = user_message

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