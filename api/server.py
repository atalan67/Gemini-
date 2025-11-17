from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# 🔑 ضع مفاتيحك هنا بين علامتي التنصيص
GEMINI_API_KEY = "مفتاح_gemini_هنا"
PAGE_ACCESS_TOKEN = "مفتاح_الفيسبوك_هنا" 
VERIFY_TOKEN = "hello123"

# ✅ هذا للتحقق من الاتصال
@app.route('/webhook', methods=['GET'])
def verify_webhook():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    if mode and token == VERIFY_TOKEN:
        print('✅ تم التحقق من Webhook')
        return challenge
    else:
        print('❌ فشل التحقق')
        return 'Verification failed', 403

# 📩 هذا لاستقبال الرسائل
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.get_json()
    print('📩 استلمنا رسالة:', data)

    if data.get('object') == 'page':
        for entry in data['entry']:
            messaging_events = entry.get('messaging', [])
            for event in messaging_events:
                sender_id = event['sender']['id']
                if 'message' in event:
                    handle_message(sender_id, event['message'])
        
        return 'EVENT_RECEIVED', 200
    else:
        return 'Not Found', 404

# 🧠 هذا للاتصال بـ Gemini
def call_gemini_api(user_message):
    try:
        print('🧠 إرسال لـ Gemini:', user_message)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [{
                "parts": [{
                    "text": user_message
                }]
            }]
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']
        print('✅ رد Gemini:', answer)
        return answer
        
    except Exception as error:
        print('❌ خطأ في Gemini:', str(error))
        return "عذراً، حدث خطأ في المعالجة. حاول مرة أخرى."

# 💬 هذا لمعالجة الرسائل
def handle_message(sender_id, message):
    if 'text' not in message:
        print('❌ رسالة بدون نص')
        return
    
    user_text = message['text']
    print('👤 مستخدم يرسل:', user_text)
    
    # 👆 إظهار "يكتب..." للمستخدم
    send_typing_indicator(sender_id)
    
    # 🧠 الحصول على رد من Gemini
    gemini_response = call_gemini_api(user_text)
    
    # 👇 إرسال الرد للمستخدم
    send_message(sender_id, gemini_response)

# ⏳ إظهار "يكتب..."
def send_typing_indicator(sender_id):
    payload = {
        "recipient": {"id": sender_id},
        "sender_action": "typing_on"
    }
    call_send_api(payload)

# 📤 هذا لإرسال الرد للفيسبوك
def send_message(sender_id, text):
    payload = {
        "recipient": {"id": sender_id},
        "message": {"text": text}
    }
    call_send_api(payload)

def call_send_api(payload):
    try:
        print('📤 إرسال رد للفيسبوك:', payload)
        
        url = f"https://graph.facebook.com/v18.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        print('✅ تم إرسال الرد بنجاح')
        
    except Exception as error:
        print('❌ خطأ في الإرسال:', str(error))

# 🚀 تشغيل الخادم
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    print(f'🎉 الخادم يعمل على port {port}')
    app.run(host='0.0.0.0', port=port)
