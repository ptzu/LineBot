import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from message_publisher import MessagePublisher
from user_state_manager import UserStateManager
from features.feature_registry import FeatureRegistry
from features.menu_feature import MenuFeature
from features.colorize_feature import ColorizeFeature

# 全域變數
app = Flask(__name__)
line_bot_api = None
handler = None
publisher = None
user_state_manager = None
feature_registry = None

def init():
    """初始化所有 LINE Bot 相關組件"""
    global app, line_bot_api, handler, publisher, user_state_manager, feature_registry
    
    print("🚀 正在初始化 LINE Bot...")
    
    # 1. 驗證環境變數
    print("📋 檢查環境變數...")
    if not os.getenv("CHANNEL_ACCESS_TOKEN"):
        raise ValueError("CHANNEL_ACCESS_TOKEN 環境變數未設定")
    if not os.getenv("CHANNEL_SECRET"):
        raise ValueError("CHANNEL_SECRET 環境變數未設定")
    if not os.getenv("REPLICATE_API_TOKEN"):
        raise ValueError("REPLICATE_API_TOKEN 環境變數未設定")
    print("✅ 環境變數檢查完成")
    
    # 2. Flask 應用程式已在模組層級初始化
    print("🌐 Flask 應用程式已準備就緒")
    print("✅ Flask 應用程式初始化完成")
    
    # 3. 初始化 LINE Bot API
    print("🤖 初始化 LINE Bot API...")
    line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
    handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
    print("✅ LINE Bot API 初始化完成")
    
    # 4. 創建統一的訊息發送器
    print("📤 初始化訊息發送器...")
    publisher = MessagePublisher(line_bot_api)
    print("✅ 訊息發送器初始化完成")
    
    # 5. 創建用戶狀態管理器
    print("👤 初始化用戶狀態管理器...")
    user_state_manager = UserStateManager()
    print("✅ 用戶狀態管理器初始化完成")
    
    # 6. 創建功能註冊表
    print("📝 初始化功能註冊表...")
    feature_registry = FeatureRegistry()
    print("✅ 功能註冊表初始化完成")
    
    # 7. 註冊所有功能
    print("🔧 註冊功能模組...")
    menu_feature = MenuFeature(line_bot_api, publisher, user_state_manager)
    colorize_feature = ColorizeFeature(line_bot_api, publisher, user_state_manager)
    
    feature_registry.register(menu_feature)
    feature_registry.register(colorize_feature)
    
    print(f"✅ 已註冊 {len(feature_registry.get_all_features())} 個功能:")
    for feature in feature_registry.get_all_features():
        print(f"   - {feature.name}")
    
    print("🎉 LINE Bot 初始化完成！")

def main():
    """主程式入口點"""
    print("=" * 50)
    print("🚀 啟動 LINE Bot 服務")
    print("=" * 50)
    
    # 初始化所有組件
    init()
    
    # 啟動 Flask 應用程式
    print("🌐 啟動 Flask 伺服器...")
    port = int(os.getenv("PORT", 5000))
    print(f"📍 服務運行在: http://0.0.0.0:{port}")
    print("=" * 50)
    
    app.run(host="0.0.0.0", port=port)

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        # 驗證簽名
        handler.parser.parse(body, signature)
        
        # 解析請求內容
        import json
        events = json.loads(body).get('events', [])
        
        for event in events:
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                # 處理文字訊息
                result = handle_text_message(event)
                if result:  # 如果有 JSON 回應，直接回傳
                    return result
            elif event.get('type') == 'message' and event.get('message', {}).get('type') == 'image':
                # 處理圖片訊息
                result = handle_image_message(event)
                if result:  # 如果有 JSON 回應，直接回傳
                    return result
        
        return "OK"
    except InvalidSignatureError:
        print("❌ Invalid signature error")
        abort(400)
    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        import traceback
        traceback.print_exc()
        abort(500)

def handle_text_message(event):
    """處理文字訊息，委託給 FeatureRegistry"""
    try:
        result = feature_registry.route_text_message(event)
        return result
    except Exception as e:
        print(f"❌ handle_text_message error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def handle_image_message(event):
    """處理圖片訊息，委託給 FeatureRegistry"""
    try:
        result = feature_registry.route_image_message(event)
        return result
    except Exception as e:
        print(f"❌ handle_image_message error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
