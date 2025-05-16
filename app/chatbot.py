import os
import openai
from app.models.product import Product
from flask import current_app, jsonify
import re
import unicodedata
from datetime import datetime, timedelta

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

                # Sử dụng regex không dấu
                match_mon_an = re.search(r'(?:cac )?mon(?: an)? tu ([\\w\\s\\-]+)', user_input_norm)
                if match_mon_an:
                    ten_sp = match_mon_an.group(1).strip()
                    ten_sp_norm = strip_accents(ten_sp).replace(' ', '-')
                    print("DEBUG: ten_sp_norm =", ten_sp_norm)
                    found = None
                    for p in products:
                        p_name_norm = strip_accents(p.name).replace(' ', '-')
                        print("DEBUG: so sánh", p_name_norm, "với", ten_sp_norm)
                        if p_name_norm == ten_sp_norm:
                            found = p
                            break
                    # Nếu không khớp tuyệt đối, thử khớp gần đúng
                    if not found:
                        for p in products:
                            if ten_sp_norm in strip_accents(p.name):
                                found = p
                                break
                    if found:
                        mon_an = []
                        name_norm = normalize_name(found.name)
                        print("DEBUG: name_norm =", name_norm)
                        if 'cachua' in name_norm:
                            mon_an = [
                                'Canh cà chua trứng',
                                'Sốt cà chua',
                                'Salad cà chua',
                                'Cà chua nhồi thịt',
                                'Nước ép cà chua'
                            ]
                        elif 'dautay' in name_norm:
                            mon_an = [
                                'Sinh tố dâu tây',
                                'Bánh mousse dâu tây',
                                'Mứt dâu tây',
                                'Sữa chua dâu tây',
                                'Dâu tây chấm sữa đặc'
                            ]
                        print("DEBUG: mon_an =", mon_an)
                        if mon_an:
                            print("DEBUG: Trả về gợi ý món ăn cho", found.name)
                            return jsonify({
                                "type": "text",
                                "response": f"Một số món ăn từ {found.name} bạn có thể tham khảo: " + ', '.join(mon_an)
                            })
                        else:
                            return jsonify({
                                "type": "text",
                                "response": f"Bạn có thể chế biến nhiều món ăn từ {found.name} như: xào, luộc, nấu canh, làm salad..."
                            })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": f"Không tìm thấy sản phẩm '{ten_sp}' để gợi ý món ăn."
                        })

                print("DEBUG: user_input_norm =", user_input_norm)

                # Xử lý lọc theo loại hàng
                categories = ['trai-cay', 'thit-ca', 'rau-cu']
                found_category = None
                for cat in categories:
                    if cat in user_input_norm:
                        found_category = cat
                        break

                # --- Bổ sung nhận diện tên sản phẩm + (trên/dưới/từ) + giá ---
                # Ghi chú: Chatbot vẫn hiểu được tên sản phẩm ngay cả khi không có từ khóa 'sản phẩm' trong câu hỏi.
                found_product = None
                user_words = user_input_norm.split('-')
                for p in products:
                    name_norm = strip_accents(p.name)
                    print("DEBUG: product name =", p.name, "->", name_norm)
                    # Ưu tiên khớp chính xác
                    if name_norm == user_input_norm:
                        found_product = p
                        break
                # Nếu không khớp chính xác, thử khớp gần đúng: input là một từ trong tên sản phẩm
                if not found_product:
                    for p in products:
                        name_norm = strip_accents(p.name)
                        if any(word for word in user_words if word and word in name_norm):
                            found_product = p
                            break

                # --- Bổ sung câu trả lời linh động trước khi đưa ra card sản phẩm ---
                if found_product:
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
                            "price": p.price,
                            "description": p.description,
                            "image_url": p.image_url,
                            "status": "Còn hàng" if available_quantity > 0 else "Hết hàng",
                            "available_quantity": available_quantity,
                            "category": p.category
                        })
                    if filtered:
                        return jsonify({
                            "type": "products",
                            "response": response,
                            "products": filtered
                        })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": f"Không tìm thấy sản phẩm {found_product.name} phù hợp với yêu cầu giá."
                        })

                # Nếu có tên sản phẩm trong câu hỏi nhưng không có từ khóa giá, chỉ lọc theo tên sản phẩm
                if found_product and not any(x in user_input_norm for x in ['tren', 'duoi', 'tu', 'gia']):
                    filtered = []
                    for p in products:
                        if strip_accents(p.name) != strip_accents(found_product.name):
                            continue
                        available_quantity = p.get_available_quantity()
                        filtered.append({
                            "id": p.id,
                            "name": p.name,
                            "price": p.price,
                            "description": p.description,
                            "image_url": p.image_url,
                            "status": "Còn hàng" if available_quantity > 0 else "Hết hàng",
                            "available_quantity": available_quantity,
                            "category": p.category
                        })
                    if filtered:
                        return jsonify({
                            "type": "products",
                            "response": f"Kết quả cho sản phẩm {found_product.name}:",
                            "products": filtered
                        })
                    else:
                        return jsonify({
                            "type": "text",
                            "response": f"Không tìm thấy sản phẩm {found_product.name}."
                        })

                # Xử lý lọc theo khoảng giá (linh hoạt)
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

                # Lọc sản phẩm
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
                        "price": p.price,
                        "description": p.description,
                        "image_url": p.image_url,
                        "status": "Còn hàng" if available_quantity > 0 else "Hết hàng",
                        "available_quantity": available_quantity,
                        "category": p.category
                    })

            # --- Bổ sung xử lý câu hỏi linh động theo vấn đề ---
            # Kiểm tra các từ khóa liên quan đến vấn đề người dùng hỏi
            if 'thanh toan' in user_input_norm:
                return jsonify({
                    "type": "text",
                    "response": "Bạn có thể thanh toán bằng tiền mặt khi nhận hàng (COD), chuyển khoản ngân hàng hoặc qua cổng thanh toán VNPay."
                })
            elif 'doi tra' in user_input_norm:
                return jsonify({
                    "type": "text",
                    "response": "Chúng tôi chấp nhận đổi trả sản phẩm trong vòng 7 ngày kể từ ngày nhận hàng, với điều kiện sản phẩm còn nguyên vẹn và chưa sử dụng."
                })
            elif 'giao hang' in user_input_norm:
                return jsonify({
                    "type": "text",
                    "response": "Thời gian giao hàng dự kiến từ 1-3 ngày làm việc, tùy thuộc vào địa chỉ giao hàng của bạn."
                })
            # Nếu không có từ khóa nào khớp, tiếp tục xử lý theo logic hiện tại

            # Nếu có kết quả, trả về card sản phẩm
            if product_list:
                return jsonify({
                    "type": "products",
                    "response": "Các sản phẩm bạn có thể quan tâm là:",
                    "products": product_list
                })
            # Nếu không có, trả về text
            else:
                return jsonify({
                    "type": "text",
                    "response": "Không tìm thấy sản phẩm phù hợp với yêu cầu của bạn."
                })

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