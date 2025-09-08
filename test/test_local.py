#!/usr/bin/env python3
"""
本地測試腳本 - 模擬 LINE 訊息發送給你的 Bot
"""

import requests
import json
import time
import os
import random
import string
from dotenv import load_dotenv

# 載入環境變數
try:
    load_dotenv()
except:
    print("⚠️  無法載入 .env 檔案，使用預設值")

class LineBotTester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.channel_secret = os.getenv("CHANNEL_SECRET")
        self.channel_access_token = os.getenv("CHANNEL_ACCESS_TOKEN")
        
        if not self.channel_secret or not self.channel_access_token:
            print("❌ 錯誤: 請設定 CHANNEL_SECRET 和 CHANNEL_ACCESS_TOKEN 環境變數")
            print("請複製 env_example.txt 為 .env 並填入正確的值")
            return
        
        print("✅ LINE Bot 測試器已初始化")
        print(f"目標 URL: {base_url}")
    
    
    def parse_json_response(self, response):
        """解析 JSON 回應"""
        try:
            return response.json()
        except json.JSONDecodeError:
            return None
    
    def display_bot_responses(self, response_data):
        """顯示 Bot 的回應訊息"""
        if not response_data:
            print("❌ 沒有回應資料")
            return
        
        print(f"\n🤖 Bot 回應訊息:")
        print("=" * 50)
        
        # 顯示基本資訊
        print(f"狀態: {response_data.get('status', 'unknown')}")
        print(f"用戶 ID: {response_data.get('user_id', '')}")
        
        # 格式化時間戳
        timestamp = response_data.get('timestamp')
        if timestamp:
            import datetime
            dt = datetime.datetime.fromtimestamp(timestamp)
            print(f"時間: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("-" * 50)
        
        # 處理訊息資料（來自 MessagePublisher 的格式）
        data = response_data.get("data")
        if not data:
            print("📭 沒有回應訊息")
            return
        
        # 處理訊息資料（可能是單個訊息或訊息列表）
        messages = data if isinstance(data, list) else [data]
        
        for i, message in enumerate(messages, 1):
            print(f"\n📝 訊息 {i}:")
            print(f"   類型: {message.get('type', 'unknown')}")
            
            if message.get('type') == 'text':
                print(f"   內容: {message.get('text', '')}")
                
                # 顯示 Quick Reply 按鈕
                if 'quick_reply' in message:
                    quick_reply = message['quick_reply']
                    items = quick_reply.get('items', [])
                    if items:
                        print(f"   Quick Reply 按鈕 ({len(items)} 個):")
                        for j, item in enumerate(items, 1):
                            label = item.get('label', '')
                            text = item.get('text', '')
                            print(f"     {j}. {label} -> {text}")
                            
            elif message.get('type') == 'image':
                print(f"   圖片URL: {message.get('original_content_url', '')}")
                print(f"   預覽URL: {message.get('preview_image_url', '')}")
            else:
                print(f"   原始資料: {message}")
    
    def create_signature(self, body):
        """建立 LINE 簽名（簡化版）"""
        import hmac
        import hashlib
        import base64
        
        # 使用 channel_secret 建立 HMAC-SHA256 簽名
        signature = hmac.new(
            self.channel_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # LINE Bot SDK 期望 Base64 編碼的簽名
        return base64.b64encode(signature).decode('utf-8')
    
    def send_text_message(self, user_id="test_local_user_12345_invalid", text="Hello Bot!"):
        """發送文字訊息"""
        print(f"📤 發送文字訊息: {text}")
        
        # 模擬 LINE 訊息格式
        webhook_event = {
            "events": [
                {
                    "type": "message",
                    "mode": "active",
                    "timestamp": int(time.time() * 1000),
                    "source": {
                        "type": "user",
                        "userId": user_id
                    },
                    "webhookEventId": "test_event_id",
                    "deliveryContext": {
                        "isRedelivery": False
                    },
                    "replyToken": "test_reply_token",
                    "message": {
                        "id": "test_message_id",
                        "type": "text",
                        "quoteToken": "test_quote_token",
                        "text": text
                    }
                }
            ],
            "destination": "test_destination"
        }
        
        body = json.dumps(webhook_event)
        signature = self.create_signature(body)
        
        headers = {
            "Content-Type": "application/json",
            "X-Line-Signature": signature
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/webhook",
                data=body,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ 訊息發送成功")
                
                # 嘗試解析 JSON 回應
                json_response = self.parse_json_response(response)
                if json_response:
                    # 有 JSON 回應：顯示回應訊息（測試用戶）
                    self.display_bot_responses(json_response)
                else:
                    # 無 JSON 回應：訊息已發送到真實 LINE 平台
                    print("📡 訊息已發送到 LINE 平台")
                
                return True
            else:
                print(f"❌ 發送失敗: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ 網路錯誤: {e}")
            return False
    
    
    def test_basic_functions(self):
        """測試基本功能"""
        print("\n🧪 開始測試基本功能...")
        
        # 測試 1: 一般文字訊息
        print("\n📤 測試 1: 一般文字訊息")
        self.send_text_message(text="Hello!")
        time.sleep(0.5)
        
        # 測試 2: 功能選單
        print("\n📤 測試 2: 功能選單")
        self.send_text_message(text="!功能")
        time.sleep(0.5)
        
        # 測試 3: 其他文字
        print("\n📤 測試 3: 其他文字訊息")
        self.send_text_message(text="這是測試訊息")
        time.sleep(0.5)
        
        print("\n✅ 基本功能測試完成")

def main():
    print("🤖 LINE Bot 本地測試器")
    print("=" * 40)
    
    # 檢查環境變數
    if not os.path.exists(".env"):
        print("❌ 找不到 .env 檔案")
        print("請複製 env_example.txt 為 .env 並填入正確的環境變數")
        return
    
    tester = LineBotTester()
    
    if not tester.channel_secret:
        return
    
    print("\n選擇測試模式:")
    print("1. 發送自訂文字訊息")
    print("2. 執行基本功能測試")
    print("3. 互動模式")
    
    choice = input("\n請選擇 (1-3): ").strip()
    
    if choice == "1":
        text = input("請輸入要發送的訊息: ").strip()
        if text:
            tester.send_text_message(text=text)
    
    elif choice == "2":
        tester.test_basic_functions()
    
    elif choice == "3":
        print("\n進入互動模式 (輸入 'quit' 退出):")
        print("💡 每次發送訊息後會顯示 Bot 回應（如果是測試用戶）")
        while True:
            text = input("> ").strip()
            if text.lower() == 'quit':
                break
            if text:
                tester.send_text_message(text=text)
                time.sleep(0.5)
    
    else:
        print("❌ 無效的選擇")

if __name__ == "__main__":
    main()
