from .base_feature import BaseFeature
from linebot.models import TextSendMessage, QuickReply, QuickReplyButton, MessageAction


class MenuFeature(BaseFeature):
    """功能選單處理器"""
    
    @property
    def name(self) -> str:
        return "menu"
    
    def can_handle(self, message: str, user_id: str) -> bool:
        """處理功能選單相關的訊息"""
        menu_commands = ["!功能", "功能", "！功能", "使用說明", "其他功能"]
        return message in menu_commands
    
    def handle_text(self, event: dict) -> dict:
        """處理文字訊息"""
        user_id = self.get_user_id(event)
        reply_token = self.get_reply_token(event)
        message = self.get_message_text(event)
        user_name = self.get_user_name(user_id)
        
        try:
            if message in ["!功能", "功能", "！功能"]:
                return self._handle_main_menu(reply_token, user_name, user_id)
            elif message == "使用說明":
                return self._handle_help(reply_token, user_name, user_id)
            elif message == "其他功能":
                return self._handle_other_features(reply_token, user_name, user_id)
                
        except Exception as e:
            print(f"❌ MenuFeature handle_text error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def _handle_main_menu(self, reply_token: str, user_name: str, user_id: str) -> dict:
        """處理主功能選單"""
        quick_reply_buttons = [
            QuickReplyButton(action=MessageAction(label="📸 圖片彩色化", text="圖片彩色化")),
            QuickReplyButton(action=MessageAction(label="❓ 使用說明", text="使用說明")),
        ]
        
        quick_reply = QuickReply(items=quick_reply_buttons)
        
        result = self.publisher.process_reply_message(
            reply_token,
            TextSendMessage(
                text=f"{user_name} 你好！✨\n🤖 請選擇您想要的功能：",
                quick_reply=quick_reply
            ),
            user_id
        )
        return result
    
    def _handle_help(self, reply_token: str, user_name: str, user_id: str) -> dict:
        """處理使用說明"""
        help_message = f"""{user_name} 你好！✨
❓ 使用說明

🤖 這個 LINE Bot 為您提供以下貼心服務：

🎨 圖片彩色化：
- 上傳您的珍貴黑白照片
- 自動進行精心的彩色化處理
- 讓回憶重新綻放光彩 🌈
- 支援 JPEG 格式

💡 貼心提醒：
- 輸入 "!功能" 開啟功能選單
- 上傳圖片即可開始彩色化處理
- 每張照片會消耗 1 點點數 💎"""
        
        result = self.publisher.process_reply_message(
            reply_token,
            TextSendMessage(text=help_message),
            user_id
        )
        return result
    
    def _handle_other_features(self, reply_token: str, user_name: str, user_id: str) -> dict:
        """處理其他功能說明"""
        result = self.publisher.process_reply_message(
            reply_token,
            TextSendMessage(text=f"{user_name} 你好！✨\n🔧 其他功能\n\n更多貼心功能正在精心開發中，敬請期待！🌟\n\n目前為您提供的服務：\n• 🎨 圖片彩色化\n• 💬 文字對話\n• ❓ 使用說明"),
            user_id
        )
        return result
