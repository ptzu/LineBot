import os
import base64
import tempfile
import requests
import replicate
import threading
import time
from .base_feature import BaseFeature
from linebot.models import TextSendMessage, ImageSendMessage, QuickReply, QuickReplyButton, MessageAction, Sender


class EditFeature(BaseFeature):
    """圖片編輯功能處理器"""
    
    def __init__(self, line_bot_api, publisher, state_manager):
        super().__init__(line_bot_api, publisher, state_manager)
        # 設定 Replicate API token
        os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")
        self.replicate_model = "google/nano-banana"
    
    @property
    def name(self) -> str:
        return "edit"
    
    def can_handle(self, message: str, user_id: str) -> bool:
        """判斷是否能處理此訊息"""
        # 處理圖片編輯相關的訊息
        if message == "圖片編輯":
            return True
        
        # 檢查用戶是否在圖片編輯狀態中
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
            if message == "圖片編輯":
                return self._handle_edit_request(reply_token, user_name, user_id)
            
            # 檢查用戶是否在等待編輯描述狀態
            if self.is_user_in_state(user_id, "waiting_description"):
                return self._handle_description_input(reply_token, user_name, user_id, message)
                
        except Exception as e:
            print(f"❌ EditFeature handle_text error: {str(e)}")
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
        
        # 檢查用戶是否在等待圖片狀態
        if not self.is_user_in_state(user_id, "waiting_image"):
            # 用戶沒有確認圖片編輯，靜默處理，不發送任何回覆
            print(f"用戶 {user_id} 上傳圖片但未確認圖片編輯功能，靜默處理")
            return None
        
        try:
            # 1. 從 LINE 下載圖片並暫存
            message_content = self.line_bot_api.get_message_content(message_id)
            image_bytes = b''.join(chunk for chunk in message_content.iter_content())
            
            # 2. 設定狀態為等待編輯描述，同時保存圖片數據
            self.state_manager.set_state(user_id, {
                "feature": self.name,
                "state": "waiting_description",
                "image_data": base64.b64encode(image_bytes).decode('utf-8')
            })
            
            # 3. 回覆用戶已收到圖片，請輸入編輯描述
            result = self.publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"{user_name}，我已經收到您的圖片了！📷✨\n\n請告訴我您希望如何編輯這張圖片？例如：\n• 將背景改成海灘\n• 把天空變成夕陽\n• 添加彩虹效果\n• 讓人物穿上紅色衣服\n\n請輸入您的編輯描述："),
                user_id
            )
            return result

        except Exception as e:
            # 發生錯誤時清除狀態
            self.clear_user_state(user_id)
            
            result = self.publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"處理圖片時發生錯誤: {str(e)}"),
                user_id
            )
            return result
        
        return None
    
    def _handle_edit_request(self, reply_token: str, user_name: str, user_id: str) -> dict:
        """處理圖片編輯請求"""
        # 設定用戶狀態為等待圖片
        self.set_user_state(user_id, "waiting_image")
        
        result = self.publisher.process_reply_message(
            reply_token,
            TextSendMessage(
                text=f"{user_name} 你好！✨\n🎨 圖片編輯功能\n\n💎 此功能會消耗 1 點點數，讓您的圖片煥然一新！\n\n請先上傳一張您想要編輯的圖片，然後我會請您描述想要的編輯效果 🖼️"
            ),
            user_id
        )
        return result
    
    def _handle_description_input(self, reply_token: str, user_name: str, user_id: str, description: str) -> dict:
        """處理編輯描述輸入"""
        try:
            # 獲取暫存的圖片數據
            user_state = self.get_user_state(user_id)
            image_data = user_state.get("image_data")
            
            if not image_data:
                self.clear_user_state(user_id)
                return self.publisher.process_reply_message(
                    reply_token,
                    TextSendMessage(text="找不到您上傳的圖片，請重新開始圖片編輯流程。"),
                    user_id
                )
            
            # 設定狀態為正在處理，保留圖片數據和描述
            self.state_manager.set_state(user_id, {
                "feature": self.name,
                "state": "processing",
                "image_data": image_data,
                "description": description
            })
            
            # 1. 先回覆用戶已收到描述
            result = self.publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"{user_name}，我已經收到您的編輯需求！🎨\n\n編輯描述：「{description}」\n\n正在為您精心處理中，請稍候片刻 ✨"),
                user_id
            )
            if result:  # 如果回傳錯誤 JSON
                return result
            
            # 2. 發送載入動畫
            try:
                self._start_loading_animation(user_id)
            except Exception as e:
                print(f"發送載入動畫失敗: {str(e)}")

            # 3. 在背景執行圖片編輯處理
            def process_image_async():
                try:
                    # 重新獲取狀態以確保數據完整
                    current_state = self.get_user_state(user_id)
                    if not current_state:
                        print(f"用戶 {user_id} 狀態已清除，停止處理")
                        return
                    
                    image_data = current_state.get("image_data")
                    description = current_state.get("description")
                    
                    if not image_data or not description:
                        error_result = self.publisher.process_push_message(
                            user_id,
                            TextSendMessage(text="處理過程中遺失了圖片或描述資料，請重新開始。")
                        )
                        if error_result:
                            print(f"背景處理時用戶無效，JSON 回應: {error_result}")
                        return
                    
                    # 將 base64 轉回 bytes
                    image_bytes = base64.b64decode(image_data)
                    
                    # 使用 Replicate API 處理圖片
                    output_url = self._edit_image(image_bytes, description)
                    
                    # 回傳編輯後的圖片（載入動畫會自動停止）
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
                    print(f"用戶 {user_id} 圖片編輯處理完成，狀態已重置")

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
                "loadingSeconds": 45  # 圖片編輯可能需要更長時間
            }
            
            # 發送請求
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                print(f"載入動畫已啟動，用戶: {user_id}")
            else:
                print(f"載入動畫啟動失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"啟動載入動畫時發生錯誤: {str(e)}")
    
    def _edit_image(self, image_bytes: bytes, description: str) -> str:
        """呼叫 Replicate 圖片編輯 API"""
        try:
            print(f"🔍 開始處理圖片編輯...")
            print(f"📊 圖片大小: {len(image_bytes)} bytes")
            print(f"📝 編輯描述: {description}")
            
            # 將 bytes 轉換為 base64 格式
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            image_data_url = f"data:image/jpeg;base64,{image_b64}"
            
            print(f"🤖 呼叫模型: {self.replicate_model}")
            print("📡 正在發送請求到 Replicate API...")
            
            # 使用 Replicate Python SDK 呼叫 google/nano-banana 模型
            # 根據官方範例使用正確的參數格式
            output = replicate.run(
                self.replicate_model,
                input={
                    "prompt": description,
                    "image_input": [image_data_url],  # 使用 image_input 而不是 image
                    "output_format": "jpg"
                }
            )
            
            print(f"✅ API 回應類型: {type(output)}")
            print(f"📄 API 回應內容: {output}")
            
            if output:
                # 處理 FileOutput 物件，獲取 URL 字串
                try:
                    # 嘗試不同的方式獲取 URL
                    if hasattr(output, 'url'):
                        if callable(getattr(output, 'url')):
                            result_url = output.url()
                            print(f"🎯 回傳 URL (使用 .url()): {result_url}")
                            return result_url
                        else:
                            result_url = output.url
                            print(f"🎯 回傳 URL (使用 .url 屬性): {result_url}")
                            return result_url
                    elif isinstance(output, str):
                        print(f"🎯 回傳字串 URL: {output}")
                        return output
                    elif isinstance(output, list) and len(output) > 0:
                        first_item = output[0]
                        if hasattr(first_item, 'url'):
                            if callable(getattr(first_item, 'url')):
                                result_url = first_item.url()
                            else:
                                result_url = first_item.url
                            print(f"🎯 回傳列表第一個元素的 URL: {result_url}")
                            return result_url
                        else:
                            print(f"🎯 回傳列表第一個元素 (轉字串): {str(first_item)}")
                            return str(first_item)
                    else:
                        # 嘗試轉換為字串
                        result_str = str(output)
                        print(f"🎯 回傳轉換後字串: {result_str}")
                        return result_str
                except Exception as url_error:
                    print(f"❌ 獲取 URL 失敗: {url_error}")
                    # 備用方案：轉換為字串
                    result_str = str(output)
                    print(f"🔄 備用方案，回傳字串: {result_str}")
                    return result_str
            else:
                print("❌ API 沒有回傳任何結果")
                raise Exception("API 沒有回傳結果")
                
        except Exception as e:
            print(f"❌ Replicate API 錯誤詳細信息: {str(e)}")
            print(f"❌ 錯誤類型: {type(e)}")
            
            if "Insufficient credit" in str(e):
                raise Exception("Replicate 點數不足，請前往 https://replicate.com/account/billing#billing 購買點數")
            elif "Model not found" in str(e) or "does not exist" in str(e):
                raise Exception("找不到 google/nano-banana 模型，請檢查模型名稱是否正確")
            elif "Invalid input" in str(e):
                raise Exception("輸入參數格式錯誤，請檢查圖片和描述格式")
            else:
                raise Exception(f"圖片編輯處理失敗: {str(e)}")
    
    def _convert_base64_to_url(self, image_base64: str) -> str:
        """將 Base64 圖片數據轉換為可訪問的 URL"""
        try:
            import uuid
            import tempfile
            import os
            
            # 生成唯一的圖片 ID
            image_id = str(uuid.uuid4())
            
            # 將 Base64 轉回 bytes
            image_bytes = base64.b64decode(image_base64)
            
            # 創建臨時文件
            temp_dir = tempfile.gettempdir()
            temp_filename = f"linebot_image_{image_id}.jpg"
            temp_filepath = os.path.join(temp_dir, temp_filename)
            
            # 寫入圖片文件
            with open(temp_filepath, 'wb') as f:
                f.write(image_bytes)
            
            print(f"📁 臨時圖片已保存: {temp_filepath}")
            
            # 返回可訪問的 URL（需要配置 web server 提供靜態文件服務）
            # 這裡暫時返回 file:// URL 用於測試
            file_url = f"file://{temp_filepath}"
            
            # 實際部署時應該返回 HTTP URL，例如：
            # server_url = os.getenv("SERVER_URL", "https://your-app.herokuapp.com")
            # return f"{server_url}/temp/{temp_filename}"
            
            print(f"🔗 生成的圖片 URL: {file_url}")
            return file_url
            
        except Exception as e:
            print(f"❌ Base64 轉 URL 失敗: {str(e)}")
            raise Exception(f"圖片 URL 轉換失敗: {str(e)}")
