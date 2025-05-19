import os
import openai
from app.models.product import Product
from flask import current_app, jsonify, request, session
import re
import unicodedata
from datetime import datetime, timedelta
from flask import Blueprint
from flask_login import current_user, login_required
from app import db
from app.models.chat_history import ChatHistory
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Override the default JSON encoder
json.JSONEncoder = DecimalEncoder

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
        self.last_clear_time = datetime.now()


    def get_user_context(self, user_id):
        """Lấy context chat của user từ session"""
        if not user_id:
            return []
        return session.get(f'chat_history_{user_id}', [])

    def save_user_context(self, user_id, context):
        """Lưu context chat của user vào session"""
        if user_id:
            session[f'chat_history_{user_id}'] = context

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

    def get_chat_response(self, user_message, user_id):
        try:
            # Lấy context chat của user
            conversation_history = self.get_user_context(user_id)
            
            # Thêm câu hỏi của người dùng vào lịch sử
            conversation_history.append({"role": "user", "content": user_message})
            
            # Giới hạn lịch sử hội thoại để tránh token quá lớn
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]
            
            # Gọi API OpenAI để lấy câu trả lời
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là một trợ lý thân thiện của cửa hàng thực phẩm. Bạn có thể trả lời các câu hỏi về sản phẩm, chính sách cửa hàng và các vấn đề khác. Hãy trả lời ngắn gọn, thân thiện và hữu ích."},
                    *conversation_history
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            # Lấy câu trả lời từ API
            assistant_response = response.choices[0].message.content
            
            # Thêm câu trả lời vào lịch sử
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Lưu context mới vào session
            self.save_user_context(user_id, conversation_history)
            
            return assistant_response
            
        except Exception as e:
            print("OpenAI API error:", e)
            return "Xin lỗi, tôi đang gặp một số vấn đề kỹ thuật. Vui lòng thử lại sau."

    def get_response(self, user_message, user_id):
        try:
            # Kiểm tra và xóa lịch sử nếu đã qua 15 phút
            current_time = datetime.now()
            if current_time - self.last_clear_time > timedelta(minutes=15):
                self.clear_history(user_id)
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

                # 2. Xử lý "công thức khác" (ĐƯA LÊN TRƯỚC)
                if user_input_norm in ['cong-thuc-khac', 'cong-thuc-khac-nua', 'cong-thuc-khac-di']:
                    last_recipe_list = session.get(f'last_recipe_list_{user_id}', [])
                    last_recipe_index = session.get(f'last_recipe_index_{user_id}', 0) + 1
                    if last_recipe_index < len(last_recipe_list):
                        session[f'last_recipe_index_{user_id}'] = last_recipe_index
                        recipe = last_recipe_list[last_recipe_index]
                        return jsonify({
                            "type": "text",
                            "response": recipe
                        })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": "Đã hết công thức gợi ý cho sản phẩm này!"
                        })

                # Nếu user nhắn "có" và vừa hỏi sản phẩm:
                if user_input_norm in ['co', 'có']:
                    # Lấy tên sản phẩm từ request hoặc từ self.last_product_name
                    product_name = None
                    if request.json and 'product_name' in request.json:
                        product_name = request.json['product_name']
                    if not product_name:
                        product_name = session.get('last_product_name')
                    if product_name:
                        name_norm = normalize_name(product_name)
                        # Ưu tiên lấy công thức từ RECIPE_MAP
                        recipe_key = None
                        for key in RECIPE_MAP:
                            if key in name_norm:
                                recipe_key = key
                                break
                        if recipe_key:
                            recipe = RECIPE_MAP[recipe_key]
                        else:
                            prompt = f"Hãy viết công thức chi tiết cho món ăn từ '{product_name}' bằng tiếng Việt, gồm nguyên liệu và các bước thực hiện."
                            recipe = self.get_chat_response(prompt, user_id)
                        session['last_product_name'] = None
                        return jsonify({
                            "type": "text",
                            "response": recipe
                        })

                # Nếu user nhắn tên món ăn (không cần kiểm tra RECIPE_MAP nữa)
                if self.is_dish_name(user_message):
                    prompt = f"Hãy viết công thức chi tiết cho món ăn '{user_message}' bằng tiếng Việt, gồm nguyên liệu và các bước thực hiện."
                    ai_recipe = self.get_chat_response(prompt, user_id)
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
                    session['last_product_name'] = found_product.name
                    response = f"Kết quả cho sản phẩm {found_product.name}:"
                    # Tìm "trên", "dưới", "từ ... đến ..." liên quan giá
                    price_min, price_max = None, None
                    # từ ... đến ...
                    range_match = re.search(r'tu\s*(\d+)[^\d]+den[^\d]+(\d+)', user_input_norm)
                    if range_match:
                        price_min = int(range_match.group(1))
                        price_max = int(range_match.group(2))
                    else:
                        # trên
                        above_match = re.search(r'tren[^\d]*(\d+)', user_input_norm)
                        if above_match:
                            price_min = int(above_match.group(1))
                        # dưới
                        below_match = re.search(r'duoi[^\d]*(\d+)', user_input_norm)
                        if below_match:
                            price_max = int(below_match.group(1))
                        # giá ...
                        price_match = re.search(r'gia[^\d]*(\d+)', user_input_norm)
                        if price_match:
                            price_max = int(price_match.group(1))
                    
                    # Lọc sản phẩm theo tên và giá
                    filtered = []
                    for p in products:
                        if strip_accents(p.name) != strip_accents(found_product.name):
                            continue
                        if price_min and p.price < price_min:
                            continue
                        if price_max and p.price > price_max:
                            continue
                        available_quantity = p.get_available_quantity()
                        filtered.append({
                            "id": p.id,
                            "name": p.name,
                            "price": float(p.price) if p.price is not None else None,
                            "description": p.description,
                            "image_url": p.image_url,
                            "status": "Còn hàng" if available_quantity > 0 else "Hết hàng",
                            "available_quantity": available_quantity,
                            "category": p.category
                        })
                    if filtered:
                        # Lưu card sản phẩm vào chat_history
                        if user_id:
                            bot_history = ChatHistory(
                                user_id=user_id,
                                message=response,
                                is_user=False,
                                type="products",
                                data=json.dumps(filtered)
                            )
                            db.session.add(bot_history)
                            db.session.commit()
                        return jsonify({
                            "type": "products",
                            "response": response,
                            "products": filtered,
                            "follow_up": f"Bạn có muốn tham khảo một số món từ sản phẩm {found_product.name} không? (Trả lời 'có' để xem gợi ý món ăn)"
                        })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": f"Không tìm thấy sản phẩm {found_product.name} phù hợp với yêu cầu giá."
                        })

                # Xử lý lọc theo khoảng giá
                price_min, price_max = None, None
                range_match = re.search(r'(?:gia|tu)?\s*(\d+)[^\d]+(\d+)', user_input_norm)
                if range_match:
                    price_min = int(range_match.group(1))
                    price_max = int(range_match.group(2))
                else:
                    below_match = re.search(r'(?:gia)?[^\d]*duoi[^\d]*(\d+)', user_input_norm)
                    if below_match:
                        price_max = int(below_match.group(1))
                    else:
                        above_match = re.search(r'(?:gia)?[^\d]*tren[^\d]*(\d+)', user_input_norm)
                        if above_match:
                            price_min = int(above_match.group(1))
                        else:
                            price_match = re.search(r'(\d+)', user_input_norm)
                            if price_match:
                                price_max = int(price_match.group(1))

                # Lọc sản phẩm theo giá và danh mục
                for p in products:
                    available_quantity = p.get_available_quantity()
                    # Lọc theo loại hàng
                    if found_category and (not p.category or strip_accents(p.category) != found_category):
                        continue
                    # Lọc theo khoảng giá
                    if price_min and p.price < price_min:
                        continue
                    if price_max and p.price > price_max:
                        continue
                    product_list.append({
                        "id": p.id,
                        "name": p.name,
                        "price": float(p.price) if p.price is not None else None,
                        "description": p.description,
                        "image_url": p.image_url,
                        "status": "Còn hàng" if available_quantity > 0 else "Hết hàng",
                        "available_quantity": available_quantity,
                        "category": p.category
                    })

                # Trả về kết quả sản phẩm nếu có
                if product_list:
                    # Lưu card sản phẩm vào chat_history
                    if user_id:
                        bot_history = ChatHistory(
                            user_id=user_id,
                            message="Các sản phẩm bạn có thể quan tâm là:",
                            is_user=False,
                            type="products",
                            data=json.dumps(product_list)
                        )
                        db.session.add(bot_history)
                        db.session.commit()
                    return jsonify({
                        "type": "products",
                        "response": "Các sản phẩm bạn có thể quan tâm là:",
                        "products": product_list
                    })
                # Nếu không có kết quả sản phẩm và không phải câu hỏi thực tế về cửa hàng
                else:
                    # Sử dụng OpenAI để trả lời các câu hỏi chung
                    chat_response = self.get_chat_response(user_message, user_id)
                    return jsonify({
                        "type": "text",
                        "response": chat_response
                    })

                # Khi trả về công thức đầu tiên cho sản phẩm:
                if found_product:
                    # ... lấy danh sách công thức cho sản phẩm ...
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
                        session[f'last_recipe_list_{user_id}'] = mon_an
                        session[f'last_recipe_index_{user_id}'] = 0
                        return jsonify({
                            "type": "text",
                            "response": mon_an[0]
                        })

        except Exception as e:
            import traceback
            print("Chatbot error:", e)
            traceback.print_exc()
            return jsonify({
                "type": "text",
                "response": "Xin lỗi, tôi đang gặp một số vấn đề kỹ thuật. Vui lòng thử lại sau."
            })

    def clear_history(self, user_id):
        """Xóa lịch sử chat của user"""
        if user_id:
            session.pop(f'chat_history_{user_id}', None)
            session.pop(f'last_recipe_list_{user_id}', None)
            session.pop(f'last_recipe_index_{user_id}', None)
        self.last_clear_time = datetime.now()

chat_api = Blueprint('chat_api', __name__)

@chat_api.route('/api/history', methods=['GET'])
@login_required
def get_chat_history():
    try:
        user_id = current_user.id
        history = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.created_at.asc()).limit(50).all()
        result = []
        for msg in history:
            if msg.type == "products":
                result.append({
                    "type": "products",
                    "text": msg.message,
                    "products": json.loads(msg.data) if msg.data else []
                })
            else:
                result.append({
                    "type": "text",
                    "text": msg.message,
                    "isUser": msg.is_user
                })
        return jsonify({
            'success': True,
            'history': result
        })
    except Exception as e:
        print("Error getting chat history:", e)
        return jsonify({
            'success': False,
            'error': 'Không thể lấy lịch sử chat'
        })

@chat_api.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    if not user_message:
        return jsonify({'success': False, 'error': 'Tin nhắn không được để trống.'})

    user_id = current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None

    # Lưu tin nhắn của user vào database NẾU đã đăng nhập
    if user_id:
        user_history = ChatHistory(user_id=user_id, message=user_message, is_user=True)
        db.session.add(user_history)
        db.session.commit()

    # GỌI LOGIC XỬ LÝ CÂU HỎI ĐÃ SETUP SẴN
    chatbot = Chatbot()
    assistant_response = chatbot.get_response(user_message, user_id)

    # Nếu assistant_response là jsonify (tức là đã trả về đúng định dạng), thì lấy text để lưu vào db
    if hasattr(assistant_response, 'get_json'):
        try:
            data = assistant_response.get_json()
            text = data.get("response") or data.get("text") or str(data)
        except Exception:
            text = str(assistant_response)
        assistant_response_text = text
    else:
        assistant_response_text = assistant_response

    # Lưu tin nhắn của bot vào database NẾU đã đăng nhập
    if user_id:
        bot_history = ChatHistory(user_id=user_id, message=assistant_response_text, is_user=False)
        db.session.add(bot_history)
        db.session.commit()

    # Trả về đúng định dạng cho frontend
    if hasattr(assistant_response, 'get_json'):
        return assistant_response
    return jsonify({'success': True, 'response': assistant_response_text})