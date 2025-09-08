import os
import base64
import tempfile
import requests
import replicate
import threading
import time
import re
from unittest.mock import patch, MagicMock
from flask import Flask, request, abort, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage,
    TextSendMessage, ImageSendMessage, QuickReply, QuickReplyButton, MessageAction
)

class UserStateManager:
    """用戶狀態管理器，追蹤每個用戶的當前狀態"""
    
    def __init__(self):
        # 用戶狀態字典：{user_id: state}
        # 狀態類型：
        # - None: 無特殊狀態
        # - "waiting_for_colorize": 等待彩色化確認
        # - "colorizing": 正在進行彩色化處理
        self.user_states = {}
    
    def set_state(self, user_id, state):
        """設定用戶狀態"""
        self.user_states[user_id] = state
        print(f"用戶 {user_id} 狀態設為: {state}")
    
    def get_state(self, user_id):
        """獲取用戶狀態"""
        return self.user_states.get(user_id, None)
    
    def clear_state(self, user_id):
        """清除用戶狀態"""
        if user_id in self.user_states:
            old_state = self.user_states[user_id]
            del self.user_states[user_id]
            print(f"用戶 {user_id} 狀態已清除 (原狀態: {old_state})")
    
    def is_waiting_for_colorize(self, user_id):
        """檢查用戶是否在等待彩色化確認"""
        return self.get_state(user_id) == "waiting_for_colorize"
    
    def is_colorizing(self, user_id):
        """檢查用戶是否正在進行彩色化處理"""
        return self.get_state(user_id) == "colorizing"

class MessagePublisher:
    """統一的訊息發送器，負責用戶驗證和訊息發送"""
    
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
    
    def _is_valid_user(self, user_id):
        """
        驗證 LINE userId 是否有效
        
        Args:
            user_id (str): 要驗證的 LINE userId
        
        Returns:
            dict: 驗證結果，包含以下欄位：
                - is_valid (bool): userId 是否有效
                - reason (str): 驗證結果的原因說明
                - error_code (str): 錯誤代碼（如果有錯誤）
                - user_info (dict, optional): 用戶資訊（如果驗證成功且能獲取）
        """
        
        # 1. 基本參數檢查
        if not user_id:
            return {
                "is_valid": False,
                "reason": "userId 不能為空",
                "error_code": "EMPTY_USER_ID"
            }
        
        if not isinstance(user_id, str):
            return {
                "is_valid": False,
                "reason": "userId 必須是字串格式",
                "error_code": "INVALID_TYPE"
            }

        if not self.line_bot_api:
            return {
                "is_valid": False,
                "reason": "LINE Bot API 實例未初始化",
                "error_code": "API_NOT_INITIALIZED"
            }
        try:
            # 使用 get_profile 方法驗證用戶是否存在且已加為好友
            profile = self.line_bot_api.get_profile(user_id)
            
            # 如果成功獲取到 profile，表示 userId 有效且用戶已加 Bot 為好友
            user_info = {
                "userId": profile.user_id,
                "displayName": profile.display_name,
                "language": getattr(profile, 'language', None),
                "pictureUrl": getattr(profile, 'picture_url', None),
                "statusMessage": getattr(profile, 'status_message', None)
            }
            
            return {
                "is_valid": True,
                "reason": "用戶驗證成功，已加為好友",
                "error_code": None,
                "user_info": user_info
            }
            
        except LineBotApiError as e:
            # 根據不同的錯誤碼提供不同的回應
            error_message = str(e)
            status_code = getattr(e, 'status_code', None)
            
            if status_code == 404:
                return {
                    "is_valid": False,
                    "reason": "用戶不存在或尚未加 Bot 為好友",
                    "error_code": "USER_NOT_FOUND_OR_NOT_FRIEND"
                }
            elif status_code == 403:
                return {
                    "is_valid": False,
                    "reason": "無權限獲取用戶資訊，可能是 Bot 未被用戶加為好友",
                    "error_code": "PERMISSION_DENIED"
                }
            elif status_code == 429:
                return {
                    "is_valid": False,
                    "reason": "API 呼叫頻率過高，請稍後再試",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            else:
                return {
                    "is_valid": False,
                    "reason": f"LINE API 錯誤：{error_message}",
                    "error_code": f"LINE_API_ERROR_{status_code}"
                }
        
        except requests.exceptions.RequestException as e:
            return {
                "is_valid": False,
                "reason": f"網路連接錯誤：{str(e)}",
                "error_code": "NETWORK_ERROR"
            }
        
        except Exception as e:
            return {
                "is_valid": False,
                "reason": f"未預期的錯誤：{str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
    
    def _serialize_message(self, messages):
        """將 LINE 訊息物件序列化為 JSON 格式"""
        if not isinstance(messages, list):
            messages = [messages]
        
        serialized_messages = []
        for message in messages:
            if hasattr(message, 'type'):
                message_data = {"type": message.type}
                
                # 處理文字訊息
                if message.type == 'text':
                    message_data["text"] = message.text
                    # 處理快速回覆
                    if hasattr(message, 'quick_reply') and message.quick_reply:
                        quick_reply_items = []
                        for item in message.quick_reply.items:
                            quick_reply_items.append({
                                "type": item.action.type,
                                "label": item.action.label,
                                "text": getattr(item.action, 'text', None)
                            })
                        message_data["quick_reply"] = {"items": quick_reply_items}
                
                # 處理圖片訊息
                elif message.type == 'image':
                    message_data["original_content_url"] = message.original_content_url
                    message_data["preview_image_url"] = message.preview_image_url
                
                serialized_messages.append(message_data)
            else:
                # 如果不是標準 LINE 訊息物件，嘗試直接序列化
                serialized_messages.append(str(message))
        
        return serialized_messages[0] if len(serialized_messages) == 1 else serialized_messages
    
    def _create_json_response(self, user_id, original_messages):
        """建立純訊息的回應 JSON（用於 unit test）"""
        return {
            "status": "success",
            "data": self._serialize_message(original_messages),
            "user_id": user_id,
            "timestamp": time.time()
        }
    
    # def reply_message(self, reply_token, messages, user_id=None):
    #     """
    #     發送回覆訊息，包含用戶驗證
        
    #     Args:
    #         reply_token: LINE 回覆 token
    #         messages: 要發送的訊息
    #         user_id: 用戶 ID（用於驗證）
        
    #     Returns:
    #         dict or None: 如果用戶無效回傳純訊息 JSON，否則回傳 None
    #     """
    #     if user_id:
    #         validation_result = self._is_valid_user(user_id)
    #         print(f"驗證結果: {validation_result}")
    #         if not validation_result['is_valid']:
    #             # invalid user (unit test)：回傳純訊息 JSON
    #             return self._create_json_response(user_id, messages)
        
    #     # valid user：直接使用 LINE Bot API
    #     return self.line_bot_api.reply_message(reply_token, messages)
    
    # def push_message(self, user_id, messages):
    #     """
    #     發送推送訊息，包含用戶驗證
        
    #     Args:
    #         user_id: 用戶 ID
    #         messages: 要發送的訊息
        
    #     Returns:
    #         dict or None: 如果用戶無效回傳純訊息 JSON，否則回傳 None
    #     """
    #     validation_result = self._is_valid_user(user_id)
    #     if not validation_result['is_valid']:
    #         # invalid user (unit test)：回傳純訊息 JSON
    #         return self._create_json_response(user_id, messages)
        
    #     # valid user：直接使用 LINE Bot API
    #     return self.line_bot_api.push_message(user_id, messages)
    
    def process_reply_message(self, reply_token, messages, user_id):
        """
        處理回覆訊息，包含用戶驗證和 Flask 回應
        
        Args:
            reply_token: LINE 回覆 token
            messages: 要發送的訊息
            user_id: 用戶 ID
        
        Returns:
            Flask Response: 包含純訊息的 JSON 回應或 None（表示正常處理）
        """
        validation_result = self._is_valid_user(user_id)
        print(f"驗證結果: {validation_result}")
        if not validation_result['is_valid']:
            # invalid user (unit test)：回傳純訊息 JSON
            json_response = self._create_json_response(user_id, messages)
            print(f"回傳純訊息 JSON: {json_response}")
            return jsonify(json_response)
        
        # valid user：直接使用 LINE Bot API
        self.line_bot_api.reply_message(reply_token, messages)
        return None  # 表示正常處理，不需要特殊回應
    
    def process_push_message(self, user_id, messages):
        """
        處理推送訊息，包含用戶驗證和 Flask 回應
        
        Args:
            user_id: 用戶 ID
            messages: 要發送的訊息
        
        Returns:
            Flask Response: 包含純訊息的 JSON 回應或 None（表示正常處理）
        """
        validation_result = self._is_valid_user(user_id)
        if not validation_result['is_valid']:
            # invalid user (unit test)：回傳純訊息 JSON
            json_response = self._create_json_response(user_id, messages)
            return jsonify(json_response)
        
        # valid user：直接使用 LINE Bot API
        self.line_bot_api.push_message(user_id, messages)
        return None  # 表示正常處理，不需要特殊回應


app = Flask(__name__)

# 驗證環境變數
if not os.getenv("CHANNEL_ACCESS_TOKEN"):
    raise ValueError("CHANNEL_ACCESS_TOKEN 環境變數未設定")
if not os.getenv("CHANNEL_SECRET"):
    raise ValueError("CHANNEL_SECRET 環境變數未設定")
if not os.getenv("REPLICATE_API_TOKEN"):
    raise ValueError("REPLICATE_API_TOKEN 環境變數未設定")

line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

# 創建統一的訊息發送器
publisher = MessagePublisher(line_bot_api)

# 創建用戶狀態管理器
user_state_manager = UserStateManager()

# 設定 Replicate API token
os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")

REPLICATE_MODEL = "flux-kontext-apps/restore-image"  # flux-kontext-apps/restore-image

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
    user_message = event.get('message', {}).get('text', '')
    user_id = event.get('source', {}).get('userId', '')
    reply_token = event.get('replyToken', '')
    print(f"收到訊息：{user_message}")
    print(f"用戶 ID：{user_id}")
    
    # 獲取使用者名稱
    user_name = "使用者"  # 預設名稱
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
        print(f"用戶名稱：{user_name}")
    except Exception as e:
        print(f"無法獲取用戶名稱：{str(e)}")
    
    try:
        # 處理功能選單命令
        if user_message == "!功能" or user_message == "功能" or user_message == "！功能":
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label="📸 圖片彩色化", text="圖片彩色化")),
                QuickReplyButton(action=MessageAction(label="❓ 使用說明", text="使用說明")),
            ]
            
            quick_reply = QuickReply(items=quick_reply_buttons)
            
            result = publisher.process_reply_message(
                reply_token,
                TextSendMessage(
                    text=f"{user_name} 你好\n🤖 請選擇您想要的功能：",
                    quick_reply=quick_reply
                ),
                user_id
            )
            if result:  # 如果回傳 JSON
                return result
                
        elif user_message == "圖片彩色化":
            # 設定用戶狀態為等待彩色化確認
            user_state_manager.set_state(user_id, "waiting_for_colorize")
            
            # 提供確認選項
            quick_reply_buttons = [
                QuickReplyButton(action=MessageAction(label="✅ 確認彩色化", text="確認彩色化")),
                QuickReplyButton(action=MessageAction(label="❌ 取消", text="取消彩色化")),
            ]
            
            quick_reply = QuickReply(items=quick_reply_buttons)
            
            result = publisher.process_reply_message(
                reply_token,
                TextSendMessage(
                    text=f"{user_name} 你好\n📸 圖片彩色化功能\n\n請確認是否要進行彩色化處理？\n\n⚠️ 注意：彩色化處理需要消耗 API 點數，請確認後再上傳圖片。",
                    quick_reply=quick_reply
                ),
                user_id
            )
            if result:  # 如果回傳 JSON
                return result
                
        elif user_message == "確認彩色化":
            # 檢查用戶是否在等待彩色化狀態
            if user_state_manager.is_waiting_for_colorize(user_id):
                result = publisher.process_reply_message(
                    reply_token,
                    TextSendMessage(text=f"{user_name} 你好\n✅ 已確認彩色化功能\n\n請上傳一張黑白照片，我將為您進行彩色化處理。\n\n💡 提示：處理完成後狀態會自動重置。"),
                    user_id
                )
                if result:  # 如果回傳 JSON
                    return result
            else:
                result = publisher.process_reply_message(
                    reply_token,
                    TextSendMessage(text=f"{user_name} 你好\n❌ 您目前沒有等待確認的彩色化請求\n\n請先輸入「圖片彩色化」來啟動功能。"),
                    user_id
                )
                if result:  # 如果回傳 JSON
                    return result
                    
        elif user_message == "取消彩色化":
            # 清除用戶狀態
            user_state_manager.clear_state(user_id)
            
            result = publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"{user_name} 你好\n❌ 已取消彩色化功能\n\n如需使用其他功能，請輸入「!功能」查看選單。"),
                user_id
            )
            if result:  # 如果回傳 JSON
                return result
                
        elif user_message == "使用說明":
            help_message = f"""{user_name} 你好
❓ 使用說明

🤖 這個 LINE Bot 提供以下功能：

📸 圖片彩色化：
- 上傳黑白照片
- 自動進行彩色化處理
- 支援 JPEG 格式

💡 指令說明：
- 輸入 "!功能" 開啟功能選單
- 上傳圖片自動進行彩色化處理"""
            
            result = publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=help_message),
                user_id
            )
            if result:  # 如果回傳 JSON
                return result
                
        elif user_message == "其他功能":
            result = publisher.process_reply_message(
                reply_token,
                TextSendMessage(text=f"{user_name} 你好\n🔧 其他功能\n\n更多功能正在開發中，敬請期待！\n\n目前可用的功能：\n• 圖片彩色化\n• 文字對話\n• 使用說明"),
                user_id
            )
            if result:  # 如果回傳 JSON
                return result
                
        # else:
        #     # 處理一般文字訊息
        #     result = publisher.process_reply_message(
        #         reply_token,
        #         TextSendMessage(text=f"{user_name} 你好\n收到您的訊息：{user_message}"),
        #         user_id
        #     )
        #     if result:  # 如果回傳 JSON
        #         return result
                
    except Exception as e:
        print(f"❌ handle_text error: {str(e)}")
        import traceback
        traceback.print_exc()

def handle_image_message(event):
    user_id = event.get('source', {}).get('userId', '')
    reply_token = event.get('replyToken', '')
    message_id = event.get('message', {}).get('id', '')
    print(f"收到圖片訊息，用戶 ID：{user_id}")
    
    # 獲取使用者名稱
    user_name = "使用者"  # 預設名稱
    try:
        profile = line_bot_api.get_profile(user_id)
        user_name = profile.display_name
        print(f"用戶名稱：{user_name}")
    except Exception as e:
        print(f"無法獲取用戶名稱：{str(e)}")
    
    # 檢查用戶狀態，只有確認彩色化後才處理圖片
    if not user_state_manager.is_waiting_for_colorize(user_id):
        # 用戶沒有確認彩色化，靜默處理，不發送任何回覆
        print(f"用戶 {user_id} 上傳圖片但未確認彩色化功能，靜默處理")
        return  # 不處理圖片，不發送回覆，直接結束
    
    try:
        # 設定狀態為正在彩色化
        user_state_manager.set_state(user_id, "colorizing")
        
        # 1. 從 LINE 下載圖片
        message_content = line_bot_api.get_message_content(message_id)
        image_bytes = b''.join(chunk for chunk in message_content.iter_content())

        # 2. 先回覆用戶正在處理（包含用戶驗證）
        result = publisher.process_reply_message(
            reply_token,
            TextSendMessage(text=f"{user_name} 你好\n正在處理您的圖片，請稍候..."),
            user_id
        )
        if result:  # 如果回傳錯誤 JSON
            return result

        # 3. 在背景執行彩色化處理
        def process_image_async():
            try:
                output_url = colorize_image(image_bytes)
                # 回傳彩色圖片（包含用戶驗證）
                error_result = publisher.process_push_message(
                    user_id,
                    ImageSendMessage(
                        original_content_url=output_url,
                        preview_image_url=output_url
                    )
                )
                # 注意：背景處理中如果用戶無效，只能記錄 JSON 結果
                if error_result:
                    print(f"背景處理時用戶無效，JSON 回應: {error_result}")
                    
            except Exception as e:
                # 回傳錯誤訊息（包含用戶驗證）
                error_result = publisher.process_push_message(
                    user_id,
                    TextSendMessage(text=f"處理圖片時發生錯誤: {str(e)}")
                )
                # 注意：背景處理中如果用戶無效，只能記錄 JSON 結果
                if error_result:
                    print(f"背景處理時用戶無效，JSON 回應: {error_result}")
            finally:
                # 處理完成後清除用戶狀態
                user_state_manager.clear_state(user_id)
                print(f"用戶 {user_id} 彩色化處理完成，狀態已重置")

        # 啟動背景執行緒
        thread = threading.Thread(target=process_image_async)
        thread.start()

    except Exception as e:
        # 發生錯誤時也要清除狀態
        user_state_manager.clear_state(user_id)
        
        result = publisher.process_reply_message(
            reply_token,
            TextSendMessage(text=f"發生錯誤: {str(e)}"),
            user_id
        )
        if result:  # 如果回傳錯誤 JSON
            return result

def colorize_image(image_bytes):
    """呼叫 Replicate 彩色化 API"""
    try:
        # 將 bytes 轉換為 base64 格式
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        image_data_url = f"data:image/jpeg;base64,{image_b64}"
        
        # 使用 Replicate Python SDK
        output = replicate.run(
            REPLICATE_MODEL,
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
