import os
import openai
from app.models.product import Product
from flask import current_app, jsonify, request
import re
import unicodedata
from datetime import datetime, timedelta

RECIPE_MAP = {
    'mutdautay': "Nguyên liệu: 1kg dâu tây, 600g đường, 1 quả chanh.\nCách làm: Rửa sạch dâu tây, cắt cuống, để ráo. Ướp dâu với đường trong 3-4 tiếng cho tan đường. Bắc lên bếp đun nhỏ lửa, vớt bọt, đảo nhẹ tay. Khi dâu trong, nước sánh lại thì vắt nước cốt chanh vào, đun thêm 5 phút rồi tắt bếp. Để nguội, cho vào hũ kín bảo quản trong tủ lạnh.",
    'canhcachuatrung': "Nguyên liệu: 2 quả cà chua, 2 quả trứng, hành lá, gia vị.\nCách làm: Phi thơm hành, cho cà chua vào xào mềm, thêm nước đun sôi. Đập trứng vào bát, đánh tan rồi đổ từ từ vào nồi, khuấy nhẹ. Nêm nếm vừa ăn, rắc hành lá rồi tắt bếp.",
    'sotcachua': "Nguyên liệu: 3 quả cà chua, 1 củ tỏi, dầu ăn, gia vị.\nCách làm: Phi thơm tỏi, cho cà chua vào xào nhuyễn, nêm nếm vừa ăn. Đun nhỏ lửa đến khi sốt sánh lại, dùng làm sốt cho các món xào, rán.",
    'saladcachua': "Nguyên liệu: 2 quả cà chua, 1 quả dưa leo, rau xà lách, dầu oliu, muối, tiêu.\nCách làm: Cà chua, dưa leo rửa sạch, cắt lát. Trộn đều với rau xà lách, rưới dầu oliu, nêm muối tiêu vừa ăn.",
    'pizza_cachua': "Nguyên liệu: Đế pizza, 2 quả cà chua, phô mai mozzarella, sốt cà chua, lá oregano, dầu oliu.\nCách làm: Phết sốt cà chua lên đế pizza, xếp cà chua cắt lát và phô mai lên trên, rắc lá oregano, rưới chút dầu oliu. Nướng ở 200°C trong 10-12 phút cho phô mai chảy và đế giòn. Lấy ra cắt miếng và thưởng thức.",
    'nuocepcachua': "Nguyên liệu: 3 quả cà chua, 2 thìa đường, đá viên.\nCách làm: Cà chua rửa sạch, cắt miếng, cho vào máy xay sinh tố cùng đường và đá, xay nhuyễn, lọc lấy nước uống mát lạnh.",
    'sinhtodautay': "Nguyên liệu: 200g dâu tây, 100ml sữa tươi, 2 thìa sữa đặc, đá viên.\nCách làm: Dâu tây rửa sạch, cắt nhỏ, cho vào máy xay cùng sữa tươi, sữa đặc và đá. Xay nhuyễn, rót ra ly và thưởng thức.",
    'banhmoussedautay': "Nguyên liệu: Dâu tây, kem tươi, gelatin, đường, bánh quy.\nCách làm: Dâu tây xay nhuyễn, trộn với gelatin đã ngâm nở, kem tươi và đường. Đổ hỗn hợp lên đế bánh quy, để lạnh cho đông lại.",
    'suachuadautay': "Nguyên liệu: Dâu tây, sữa chua, đường.\nCách làm: Dâu tây rửa sạch, cắt nhỏ, trộn với sữa chua và đường, để lạnh rồi ăn.",
    'kemdautay': "Nguyên liệu: 300g dâu tây, 200ml kem tươi, 100ml sữa đặc, 50g đường.\nCách làm: Dâu tây rửa sạch, xay nhuyễn với đường. Đánh bông kem tươi, trộn đều với sữa đặc và dâu tây xay. Đổ vào khuôn, để ngăn đá 4-6 tiếng là dùng được.",
    # ... Thêm các món khác ...
}

def strip_accents(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn').lower().replace(' ', '-')

def normalize_name(name):
    return strip_accents(name).replace('-', '').replace(' ', '').lower()

class Chatbot:
    def __init__(self):
        # Khởi tạo client với API key
        self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        print("DEBUG - OPENAI_API_KEY:", os.getenv('OPENAI_API_KEY'))
        self.conversation_history = []
        self.last_clear_time = datetime.now()
        self.last_product_name = None
        self.last_recipe_list = []
        self.last_recipe_index = 0

    def is_dish_name(self, text):
        """Kiểm tra xem text có phải là tên món ăn không"""
        # Chuẩn hóa text
        text_norm = normalize_name(text)
        
        # Danh sách các từ khóa thường xuất hiện trong tên món ăn
        dish_keywords = [
            'canh', 'xao', 'luoc', 'nuong', 'ran', 'kho', 'hap', 'sot', 
            'salad', 'soup', 'pizza', 'banh', 'kem', 'sinh-to', 'nuoc-ep',
            'mut', 'mam', 'dip', 'sauce', 'soup', 'stew', 'curry', 'stir-fry'
        ]
        
        # Kiểm tra xem text có chứa từ khóa món ăn không
        return any(keyword in text_norm for keyword in dish_keywords)

    def get_chat_response(self, user_message):
        try:
            # Thêm câu hỏi của người dùng vào lịch sử
            self.conversation_history.append({"role": "user", "content": user_message})
            
            # Giới hạn lịch sử hội thoại để tránh token quá lớn
            if len(self.conversation_history) > 10:
                self.conversation_history = self.conversation_history[-10:]
            
            # Gọi API OpenAI để lấy câu trả lời
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý thân thiện của cửa hàng thực phẩm. Bạn có thể trả lời các câu hỏi về sản phẩm, chính sách cửa hàng và các vấn đề khác. Hãy trả lời ngắn gọn, thân thiện và hữu ích."},
                    *self.conversation_history
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            # Lấy câu trả lời từ API
            assistant_response = response.choices[0].message.content
            
            # Thêm câu trả lời vào lịch sử
            self.conversation_history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
            
        except Exception as e:
            print("OpenAI API error:", e)
            return "Xin lỗi, tôi đang gặp một số vấn đề kỹ thuật. Vui lòng thử lại sau."

    def get_response(self, user_message):
        try:
            # Kiểm tra và xóa lịch sử nếu đã qua 15 phút
            current_time = datetime.now()
            if current_time - self.last_clear_time > timedelta(minutes=15):
                self.clear_history()
                print("DEBUG: Đã xóa lịch sử chat sau 15 phút")

            with current_app.app_context():
                products = Product.query.all()
                product_list = []

                # Chuẩn hóa user input
                user_input_norm = strip_accents(user_message)
                print("DEBUG: user_input_norm =", user_input_norm)

                # 1. Xử lý chào hỏi
                if any(greet in user_input_norm for greet in ['xin-chao', 'hello']):
                    return jsonify({
                        "type": "text",
                        "response": "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
                    })

                # 2. Xử lý 'công thức khác' (ưu tiên kiểm tra trước)
                if user_input_norm in ['cong-thuc-khac', 'cong-thuc-khac-nua', 'cong-thuc-khac-di']:
                    if self.last_recipe_list:
                        self.last_recipe_index += 1
                        if self.last_recipe_index < len(self.last_recipe_list):
                            recipe = self.last_recipe_list[self.last_recipe_index]
                            return jsonify({
                                "type": "text",
                                "response": recipe
                            })
                        else:
                            return jsonify({
                                "type": "text",
                                "response": "Đã hết công thức gợi ý cho sản phẩm này!"
                            })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": "Bạn hãy hỏi về một sản phẩm trước nhé!"
                        })

                # Nếu user nhắn 'có' và vừa hỏi sản phẩm:
                if user_input_norm in ['co', 'có']:
                    product_name = None
                    if request.json and 'product_name' in request.json:
                        product_name = request.json['product_name']
                    if not product_name:
                        product_name = self.last_product_name
                    if product_name:
                        name_norm = normalize_name(product_name)
                        # Ưu tiên lấy danh sách công thức nếu có
                        mon_an = []
                        if 'cachua' in name_norm:
                            mon_an = [
                                RECIPE_MAP['canhcachuatrung'],
                                RECIPE_MAP['sotcachua'],
                                RECIPE_MAP['saladcachua'],
                                RECIPE_MAP['pizza_cachua'],
                                RECIPE_MAP['nuocepcachua']
                            ]
                        # ... các sản phẩm khác ...
                        if mon_an:
                            self.last_recipe_list = mon_an
                            self.last_recipe_index = 0
                            return jsonify({
                                "type": "text",
                                "response": mon_an[0]
                            })
                        # Nếu không có danh sách thì fallback như cũ
                        recipe_key = None
                        for key in RECIPE_MAP:
                            if key in name_norm:
                                recipe_key = key
                                break
                        if recipe_key:
                            recipe = RECIPE_MAP[recipe_key]
                        else:
                            prompt = f"Hãy viết công thức chi tiết cho món ăn từ '{product_name}' bằng tiếng Việt, gồm nguyên liệu và các bước thực hiện."
                            recipe = self.get_chat_response(prompt)
                        self.last_product_name = None
                        return jsonify({
                            "type": "text",
                            "response": recipe
                        })

                # Nếu user nhắn tên món ăn (không cần kiểm tra RECIPE_MAP nữa)
                if self.is_dish_name(user_message):
                    prompt = f"Hãy viết công thức chi tiết cho món ăn '{user_message}' bằng tiếng Việt, gồm nguyên liệu và các bước thực hiện."
                    ai_recipe = self.get_chat_response(prompt)
                    return jsonify({
                        "type": "text",
                        "response": ai_recipe
                    })
                # Xử lý lọc theo loại hàng
                categories = ['trai-cay', 'thit-ca', 'rau-cu']
                found_category = None
                for cat in categories:
                    if cat in user_input_norm:
                        found_category = cat
                        break

                # Tìm kiếm sản phẩm theo tên
                found_product = None
                user_words = user_input_norm.split('-')
                for p in products:
                    name_norm = strip_accents(p.name)
                    print("DEBUG: product name =", p.name, "->", name_norm)
                    # Ưu tiên khớp chính xác
                    if name_norm == user_input_norm:
                        found_product = p
                        break
                # Nếu không khớp chính xác, thử khớp gần đúng
                if not found_product:
                    for p in products:
                        name_norm = strip_accents(p.name)
                        if any(word for word in user_words if word and word in name_norm):
                            found_product = p
                            break

                # Xử lý câu hỏi về sản phẩm
                if found_product:
                    self.last_product_name = found_product.name
                    name_norm = normalize_name(found_product.name)
                    response = f"Kết quả cho sản phẩm {found_product.name}:"
                    # Tìm 'công thức' cho sản phẩm
                    mon_an = []
                    if 'cachua' in name_norm:
                        mon_an = [
                            RECIPE_MAP['canhcachuatrung'],
                            RECIPE_MAP['sotcachua'],
                            RECIPE_MAP['saladcachua'],
                            RECIPE_MAP['pizza_cachua'],
                            RECIPE_MAP['nuocepcachua']
                        ]
                    # ... các sản phẩm khác ...
                    if mon_an:
                        self.last_recipe_list = mon_an
                        self.last_recipe_index = 0
                        return jsonify({
                            "type": "text",
                            "response": mon_an[0]
                        })
                    # Nếu không có danh sách thì fallback như cũ
                    # ... giữ nguyên các xử lý lọc sản phẩm, giá ...

        except Exception as e:
            import traceback
            print("Chatbot error:", e)
            traceback.print_exc()
            return jsonify({
                "type": "text",
                "response": "Xin lỗi, tôi đang gặp một số vấn đề kỹ thuật. Vui lòng thử lại sau."
            })

    def clear_history(self):
        self.conversation_history = []
        self.last_clear_time = datetime.now()