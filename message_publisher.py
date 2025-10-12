import time
import requests
from flask import jsonify
from linebot.exceptions import LineBotApiError


class MessagePublisher:
    """統一的訊息發送器，負責用戶驗證和訊息發送"""
    
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
    
    def _get_source_type(self, event):
        """
        檢測訊息來源類型
        
        Args:
            event: LINE webhook event
            
        Returns:
            str: 'user', 'group', 'room' 或 'unknown'
        """
        source = event.get('source', {})
        source_type = source.get('type', 'unknown')
        return source_type
    
    def _is_group_chat(self, event):
        """
        判斷是否為群組聊天
        
        Args:
            event: LINE webhook event
            
        Returns:
            bool: True 如果是群組聊天，False 如果是個人聊天
        """
        source_type = self._get_source_type(event)
        return source_type in ['group', 'room']
    
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
    
    def process_reply_message(self, reply_token, messages, user_id, event=None):
        """
        處理回覆訊息，包含用戶驗證和 Flask 回應
        
        Args:
            reply_token: LINE 回覆 token
            messages: 要發送的訊息
            user_id: 用戶 ID
            event: LINE webhook event（用於判斷是否為群組聊天）
        
        Returns:
            Flask Response: 包含純訊息的 JSON 回應或 None（表示正常處理）
        """
        # 如果是群組聊天，跳過用戶驗證
        if event and self._is_group_chat(event):
            print(f"群組聊天，跳過用戶驗證，直接回應")
            self.line_bot_api.reply_message(reply_token, messages)
            return None
        
        # 個人聊天才進行用戶驗證
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
    
    def _get_target_id(self, event):
        """
        獲取正確的目標ID（用於推送訊息）
        
        Args:
            event: LINE webhook event
            
        Returns:
            str: 群組ID（群組聊天）或用戶ID（個人聊天）
        """
        if not event:
            return None
            
        source = event.get('source', {})
        source_type = source.get('type', 'user')
        
        if source_type == 'group':
            return source.get('groupId', '')
        elif source_type == 'room':
            return source.get('roomId', '')
        else:  # source_type == 'user'
            return source.get('userId', '')
    
    def process_push_message(self, user_id, messages, event=None):
        """
        處理推送訊息，包含用戶驗證和 Flask 回應
        
        Args:
            user_id: 用戶 ID（個人聊天使用）
            messages: 要發送的訊息
            event: LINE webhook event（用於判斷是否為群組聊天）
        
        Returns:
            Flask Response: 包含純訊息的 JSON 回應或 None（表示正常處理）
        """
        # 如果是群組聊天，跳過用戶驗證，使用群組ID推送訊息
        if event and self._is_group_chat(event):
            target_id = self._get_target_id(event)
            print(f"群組聊天，跳過用戶驗證，直接推送訊息到: {target_id}")
            self.line_bot_api.push_message(target_id, messages)
            return None
        
        # 個人聊天才進行用戶驗證
        validation_result = self._is_valid_user(user_id)
        if not validation_result['is_valid']:
            # invalid user (unit test)：回傳純訊息 JSON
            json_response = self._create_json_response(user_id, messages)
            return jsonify(json_response)
        
        # valid user：直接使用 LINE Bot API
        self.line_bot_api.push_message(user_id, messages)
        return None  # 表示正常處理，不需要特殊回應
