"""
模擬 Line Bot 事件資料結構
用於本地端測試
"""

class MockTextMessage:
    """模擬文字訊息"""
    def __init__(self, text):
        self.text = text
        self.type = "text"

class MockImageMessage:
    """模擬圖片訊息"""
    def __init__(self, image_path=None):
        self.type = "image"
        self.image_path = image_path
        self.id = "mock_image_message_id"

class MockUser:
    """模擬用戶"""
    def __init__(self, user_id="test_user_123"):
        self.user_id = user_id

class MockSource:
    """模擬訊息來源"""
    def __init__(self, user_id="test_user_123"):
        self.user_id = user_id
        self.type = "user"

class MockTextEvent:
    """模擬文字事件"""
    def __init__(self, text, user_id="test_user_123"):
        self.message = MockTextMessage(text)
        self.source = MockSource(user_id)
        self.reply_token = "test_reply_token_123"
        self.type = "message"

class MockImageEvent:
    """模擬圖片事件"""
    def __init__(self, image_path=None, user_id="test_user_123"):
        self.message = MockImageMessage(image_path)
        self.source = MockSource(user_id)
        self.reply_token = "test_reply_token_123"
        self.type = "message"

# 預設的測試事件
TEST_EVENTS = {
    "功能選單": MockTextEvent("!功能"),
    "一般文字": MockTextEvent("你好"),
    "使用說明": MockTextEvent("❓ 使用說明"),
    "圖片彩色化": MockTextEvent("📸 圖片彩色化"),
    "文字回覆": MockTextEvent("💬 文字回覆"),
    "其他功能": MockTextEvent("🔧 其他功能"),
}
