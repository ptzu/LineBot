"""
簡化版本地端測試
快速測試單一功能
"""

import os
from unittest.mock import patch
from mock_events import MockTextEvent, MockImageEvent

# 設定環境變數
os.environ["CHANNEL_ACCESS_TOKEN"] = "test_token"
os.environ["CHANNEL_SECRET"] = "test_secret"
os.environ["REPLICATE_API_TOKEN"] = "test_replicate_token"

# 匯入 app.py 中的函數
from app import handle_text, handle_image

class SimpleMockAPI:
    """簡化的模擬 API"""
    def __init__(self):
        self.replies = []
        self.pushes = []
    
    def reply_message(self, reply_token, message):
        self.replies.append(message)
        print(f"📤 回覆: {message.text if hasattr(message, 'text') else '圖片'}")
    
    def push_message(self, user_id, message):
        self.pushes.append(message)
        print(f"📤 推送給 {user_id}: {message.text if hasattr(message, 'text') else '圖片'}")
    
    def get_message_content(self, message_id):
        """模擬取得訊息內容"""
        from unittest.mock import Mock
        mock_content = Mock()
        mock_content.iter_content.return_value = [b'fake_image_data']
        return mock_content

def test_single_text(text):
    """測試單一文字訊息"""
    print(f"\n🧪 測試文字: {text}")
    
    event = MockTextEvent(text)
    mock_api = SimpleMockAPI()
    
    with patch('app.line_bot_api', mock_api):
        handle_text(event)
    
    print(f"✅ 測試完成 - 回覆數: {len(mock_api.replies)}")

def test_function_menu():
    """測試功能選單 - 模擬 user 發送 "!功能" 訊息"""
    print("\n🧪 測試功能選單")
    print("📝 模擬 user 發送: !功能")
    
    # 模擬 user 發送 "!功能" 訊息
    event = MockTextEvent("!功能")
    mock_api = SimpleMockAPI()
    
    with patch('app.line_bot_api', mock_api):
        handle_text(event)
    
    # 驗證 bot 是否有回覆
    if len(mock_api.replies) > 0:
        print(f"✅ Bot 有回覆 - 回覆數: {len(mock_api.replies)}")
        
        # 檢查回覆內容（這裡可以根據實際的快速選單格式進行更詳細的驗證）
        for i, reply in enumerate(mock_api.replies):
            print(f"   📤 回覆 {i+1}: {type(reply).__name__}")
            if hasattr(reply, 'text'):
                print(f"      內容: {reply.text[:50]}...")
    else:
        print("❌ Bot 沒有回覆")
    
    print("✅ 功能選單測試完成")

def test_quick_replies():
    """測試快速回覆選項 - 模擬 user 點擊快速選單"""
    print("\n🧪 測試快速回覆選項")
    print("📝 模擬 user 點擊快速選單中的各個選項")
    
    quick_reply_texts = [
        "📸 圖片彩色化",
        "💬 文字回覆", 
        "❓ 使用說明",
        "🔧 其他功能"
    ]
    
    for text in quick_reply_texts:
        print(f"\n   🔘 測試選項: {text}")
        test_single_text(text)
    
    print("\n✅ 快速回覆選項測試完成")

def test_image_processing():
    """測試圖片處理"""
    print("\n🧪 測試圖片處理")
    
    event = MockImageEvent()
    mock_api = SimpleMockAPI()
    
    with patch('app.line_bot_api', mock_api):
        with patch('app.replicate') as mock_replicate:
            mock_replicate.run.return_value = "https://example.com/colorized_image.jpg"
            handle_image(event)
    
    print(f"✅ 圖片處理測試完成 - 回覆數: {len(mock_api.replies)}")

if __name__ == "__main__":
    print("🚀 簡化版 Line Bot 測試")
    print("=" * 30)
    
    # 測試功能選單
    test_function_menu()
    
    # 測試快速回覆
    test_quick_replies()
    
    # 測試圖片處理
    test_image_processing()
    
    print("\n✅ 所有測試完成！")
