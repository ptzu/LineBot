import os
import base64
import tempfile
import requests
import replicate
import threading
import time
from .base_feature import BaseFeature
from linebot.models import TextSendMessage, ImageSendMessage, QuickReply, QuickReplyButton, MessageAction, Sender


class ColorizeFeature(BaseFeature):
    """圖片彩色化功能處理器"""
    
    def __init__(self, line_bot_api, publisher, state_manager):
        super().__init__(line_bot_api, publisher, state_manager)
        # 設定 Replicate API token
        os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
        self.replicate_model = "flux-kontext-apps/restore-image"
    
    @property
    def name(self) -> str:
        return "colorize"
    
    def can_handle(self, message: str, user_id: str) -> bool:
        """判斷是否能處理此訊息"""
        # 處理彩色化相關的訊息
        if message == "圖片彩色化":
            return True
        
        # 檢查用戶是否在彩色化狀態中
        user_state = self.get_user_state(user_id)
        if user_state and user_state.get("feature") == self.name:
            return True
        
        return False
    
    def handle_text(self, event: dict) -> dict:
        """處理文字訊息"""
        user_id = self.get_user_id(event)
        reply_token = self.get_reply_token(event)
        message = self.get_message_text(event)
        user_name = self.get_user_name(user_id)
        
        try:
            if message == "圖片彩色化":
                return self._handle_colorize_request(reply_token, user_name, user_id)
                
        except Exception as e:
            print(f"❌ ColorizeFeature handle_text error: {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def handle_image(self, event: dict) -> dict:
        """處理圖片訊息"""
        user_id = self.get_user_id(event)
        reply_token = self.get_reply_token(event)
        message_id = self.get_message_id(event)
        user_name = self.get_user_name(user_id)
        
        print(f"收到圖片訊息，用戶 ID：{user_id}")
        
        # 檢查用戶是否在等待彩色化狀態
        if not self.is_user_in_state(user_id, "waiting"):
            # 用戶沒有確認彩色化，靜默處理，不發送任何回覆
            print(f"用戶 {user_id} 上傳圖片但未確認彩色化功能，靜默處理")
            return None
        
        try:
            # 設定狀態為正在彩色化
            self.set_user_state(user_id, "processing")
            
            # 1. 從 LINE 下載圖片
            message_content = self.line_bot_api.get_message_content(message_id)
            image_bytes = b''.join(chunk for chunk in message_content.iter_content())

            # 2. 先回覆用戶已收到圖片
            result = self.publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"{user_name}，我已經收到您的珍貴照片了！✨ 正在為您精心處理中，請稍候片刻 🌟"),
                user_id
            )
            if result:  # 如果回傳錯誤 JSON
                return result
            
            # 3. 發送載入動畫
            try:
                self._start_loading_animation(user_id)
            except Exception as e:
                print(f"發送載入動畫失敗: {str(e)}")

            # 4. 在背景執行彩色化處理
            def process_image_async():
                try:
                    output_url = self._colorize_image(image_bytes)
                    
                    # 回傳彩色圖片（載入動畫會自動停止）
                    error_result = self.publisher.process_push_message(
                        user_id,
                        ImageSendMessage(
                            original_content_url=output_url,
                            preview_image_url=output_url
                        )
                    )
                    if error_result:
                        print(f"背景處理時用戶無效，JSON 回應: {error_result}")
                        
                except Exception as e:
                    # 回傳錯誤訊息（載入動畫會自動停止）
                    error_result = self.publisher.process_push_message(
                        user_id,
                        TextSendMessage(text=f"處理圖片時發生錯誤: {str(e)}")
                    )
                    if error_result:
                        print(f"背景處理時用戶無效，JSON 回應: {error_result}")
                finally:
                    # 處理完成後清除用戶狀態
                    self.clear_user_state(user_id)
                    print(f"用戶 {user_id} 彩色化處理完成，狀態已重置")

            # 啟動背景執行緒
            thread = threading.Thread(target=process_image_async)
            thread.start()

        except Exception as e:
            # 發生錯誤時也要清除狀態
            self.clear_user_state(user_id)
            
            result = self.publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"發生錯誤: {str(e)}"),
                user_id
            )
            return result
        
        return None
    
    def _handle_colorize_request(self, reply_token: str, user_name: str, user_id: str) -> dict:
        """處理彩色化請求"""
        # 設定用戶狀態為等待圖片
        self.set_user_state(user_id, "waiting")
        
        result = self.publisher.process_reply_message(
            reply_token,
            TextSendMessage(
                text=f"{user_name} 你好！✨\n🎨 圖片彩色化功能\n\n💎 此功能會消耗 1 點點數，讓您的珍貴回憶重現色彩！\n\n請上傳一張黑白照片，我將為您進行彩色化處理，讓回憶重新綻放光彩 🌈"
            ),
            user_id
        )
        return result
    
    def _start_loading_animation(self, user_id: str):
        """開始載入動畫"""
        try:
            # 使用 LINE Bot API 的載入動畫功能
            import requests
            
            # 構建請求 URL
            url = "https://api.line.me/v2/bot/chat/loading/start"
            
            # 設定 headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("CHANNEL_ACCESS_TOKEN")}'
            }
            
            # 設定載入動畫參數（5-60秒）
            data = {
                "chatId": user_id,
                "loadingSeconds": 30  # 設定為30秒，通常足夠處理圖片
            }
            
            # 發送請求
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"載入動畫已啟動，用戶: {user_id}")
            else:
                print(f"載入動畫啟動失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"啟動載入動畫時發生錯誤: {str(e)}")
    
    def _colorize_image(self, image_bytes: bytes) -> str:
        """呼叫 Replicate 彩色化 API"""
        try:
            # 將 bytes 轉換為 base64 格式
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            image_data_url = f"data:image/jpeg;base64,{image_b64}"
            
            # 使用 Replicate Python SDK
            output = replicate.run(
                self.replicate_model,
                input={
                    "input_image": image_data_url,
                }
            )
            
            if output:
                # 如果 output 是字串（URL），直接回傳
                if isinstance(output, str):
                    return output
                # 如果 output 是列表，回傳第一個元素
                elif isinstance(output, list) and len(output) > 0:
                    return output[0]
                # 如果 output 是 FileOutput 物件，轉換為字串
                else:
                    return str(output)
            else:
                raise Exception("API 沒有回傳結果")
                
        except Exception as e:
            print(f"Replicate API 錯誤: {str(e)}")
            if "Insufficient credit" in str(e):
                raise Exception("Replicate 點數不足，請前往 https://replicate.com/account/billing#billing 購買點數")
            else:
                raise Exception(f"彩色化處理失敗: {str(e)}")
