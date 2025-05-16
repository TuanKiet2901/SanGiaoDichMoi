import os
print("DEBUG - Đường dẫn file chat.py:", os.path.abspath(__file__))
from flask import Blueprint, request, jsonify, render_template
from app.chatbot import Chatbot

chat_bp = Blueprint('chat', __name__)
chatbot = Chatbot()

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    print("DEBUG - headers:", request.headers)
    print("DEBUG - data raw:", request.data)
    data = request.get_json(silent=True)
    print("DEBUG - data nhận được từ frontend:", data)
    user_message = data['message'] if data and 'message' in data else ''
    
    if not user_message:
        print("DEBUG - Không có tin nhắn được gửi")
        return jsonify({'error': 'Không có tin nhắn được gửi'}), 400
        #-------------------------
    return chatbot.get_response(user_message)

@chat_bp.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    chatbot.clear_history()
    return jsonify({'message': 'Đã xóa lịch sử chat'})

@chat_bp.route('/api/test', methods=['GET', 'POST'])
def test():
    print("DEBUG - Đã gọi vào route /api/test")
    return jsonify({'msg': 'ok'})