from flask import Flask, request, abort
import json
import requests
import os
import hashlib
import hmac
import base64

app = Flask(__name__)

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

# LINE API 端點
LINE_API_REPLY = 'https://api.line.me/v2/bot/message/reply'

def verify_signature(body, signature):
    """驗證 LINE webhook 簽名"""
    if not CHANNEL_SECRET:
        return False
    
    hash_value = hmac.new(
        CHANNEL_SECRET.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    expected_signature = base64.b64encode(hash_value).decode('utf-8')
    return hmac.compare_digest(signature, expected_signature)

def send_reply_message(reply_token, message_text):
    """發送回覆訊息到 LINE"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CHANNEL_ACCESS_TOKEN}'
    }
    
    data = {
        'replyToken': reply_token,
        'messages': [
            {
                'type': 'text',
                'text': message_text
            }
        ]
    }
    
    response = requests.post(LINE_API_REPLY, headers=headers, json=data)
    return response.status_code == 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """處理 LINE webhook 事件"""
    # 取得請求標頭和內容
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    # 驗證簽名
    if not verify_signature(body, signature):
        abort(400)
    
    try:
        # 解析 JSON 資料
        events = json.loads(body)['events']
        
        for event in events:
            # 只處理文字訊息事件
            if event['type'] == 'message' and event['message']['type'] == 'text':
                reply_token = event['replyToken']
                message_text = event['message']['text']
                
                # 回傳相同的訊息
                send_reply_message(reply_token, message_text)
        
        return 'OK', 200
        
    except Exception as e:
        print(f'Error processing webhook: {e}')
        abort(500)

@app.route('/')
def health_check():
    """健康檢查端點"""
    return 'LineBot Flask Server is running!'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
