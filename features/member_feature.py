from features.base_feature import BaseFeature
from datetime import datetime


class MemberFeature(BaseFeature):
    """會員功能 - 提供點數查詢、交易記錄等功能"""
    
    @property
    def name(self) -> str:
        return "member"
    
    def can_handle(self, message: str, user_id: str) -> bool:
        """判斷是否能處理此訊息"""
        commands = ["點數", "歷史", "會員資訊", "會員"]
        return message.strip() in commands
    
    def handle_text(self, event: dict) -> dict:
        """處理文字訊息"""
        user_id = self.get_user_id(event)
        reply_token = self.get_reply_token(event)
        message = self.get_message_text(event).strip()
        user_name = self.get_user_name(user_id)
        
        if message == "點數":
            return self._handle_points_query(user_id, user_name, reply_token, event)
        elif message == "歷史":
            return self._handle_history_query(user_id, user_name, reply_token, event)
        elif message in ["會員資訊", "會員"]:
            return self._handle_member_info(user_id, user_name, reply_token, event)
        
        return None
    
    def _handle_points_query(self, user_id: str, user_name: str, reply_token: str, event: dict):
        """處理點數查詢"""
        try:
            from models.database import get_session
            from models.member import Member
            
            with get_session() as session:
                # 直接在當前 session 中查詢或創建會員
                member = session.query(Member).filter_by(user_id=user_id).first()
                
                if not member:
                    # 建立新會員（初始點數 0）
                    member = Member(
                        user_id=user_id,
                        display_name=user_name or "使用者",
                        points=0,
                        status='normal'
                    )
                    session.add(member)
                    session.commit()
                    print(f"✅ 新會員已建立: {user_id} ({user_name})")
                else:
                    # 會員已存在，更新顯示名稱（如果有提供）
                    if user_name and member.display_name != user_name:
                        member.display_name = user_name
                        session.commit()
                        print(f"✅ 會員資訊已更新: {user_id}")
                
                # 在 session 內提取所需的屬性值
                display_name = member.display_name
                points = member.points
                status = member.status
            
            # 狀態顯示
            status_map = {
                'normal': '正常',
                'vip': 'VIP',
                'suspended': '停用',
                'banned': '黑名單'
            }
            status_text = status_map.get(status, status)
            
            # 狀態表情符號
            status_emoji = {
                'normal': '✅',
                'vip': '⭐',
                'suspended': '⚠️',
                'banned': '🚫'
            }
            emoji = status_emoji.get(status, '❓')
            
            response = f"""💰 點數查詢

👤 {display_name}
💎 剩餘點數：{points} 點
{emoji} 會員狀態：{status_text}

輸入「歷史」查看交易記錄
輸入「會員資訊」查看完整資料"""
            
            self.publisher.reply_text(reply_token, response, user_id, event)
            return "OK"
            
        except Exception as e:
            print(f"❌ 查詢點數失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            self.publisher.reply_text(reply_token, "❌ 查詢失敗，請稍後再試", user_id, event)
            return "OK"
    
    def _handle_history_query(self, user_id: str, user_name: str, reply_token: str, event: dict):
        """處理交易記錄查詢"""
        try:
            from models.database import get_session
            from models.member import Member
            
            with get_session() as session:
                # 直接在當前 session 中查詢或創建會員
                member = session.query(Member).filter_by(user_id=user_id).first()
                
                if not member:
                    # 建立新會員（初始點數 0）
                    member = Member(
                        user_id=user_id,
                        display_name=user_name or "使用者",
                        points=0,
                        status='normal'
                    )
                    session.add(member)
                    session.commit()
                    print(f"✅ 新會員已建立: {user_id} ({user_name})")
                else:
                    # 會員已存在，更新顯示名稱（如果有提供）
                    if user_name and member.display_name != user_name:
                        member.display_name = user_name
                        session.commit()
                        print(f"✅ 會員資訊已更新: {user_id}")
                
                # 在 session 內提取點數
                current_points = member.points
            
            # 查詢交易記錄
            transactions = self.member_service.get_point_history(user_id, limit=10)
            
            if not transactions:
                response = f"""📊 交易記錄

目前沒有任何交易記錄

💎 目前點數：{current_points} 點"""
                self.publisher.reply_text(reply_token, response, user_id, event)
                return "OK"
            
            # 組合回應訊息
            response_lines = ["📊 交易記錄（最近 10 筆）\n"]
            
            for trans in transactions:
                # 格式化時間
                created_at = datetime.fromisoformat(trans['created_at'])
                time_str = created_at.strftime("%m/%d %H:%M")
                
                # 交易類型顯示
                type_map = {
                    'earn': '🎁 獲得',
                    'spend': '💳 消費',
                    'admin_add': '➕ 管理員增加',
                    'admin_deduct': '➖ 管理員扣除',
                    'expire': '⏰ 過期'
                }
                type_str = type_map.get(trans['transaction_type'], trans['transaction_type'])
                
                # 點數顯示（正數顯示 +，負數自動有 -）
                points = trans['points']
                points_str = f"+{points}" if points > 0 else str(points)
                
                # 描述
                desc = trans['description'] or "無說明"
                
                line = f"{time_str} {type_str}\n{points_str} 點 → 餘額 {trans['balance_after']} 點\n說明：{desc}\n"
                response_lines.append(line)
            
            response_lines.append(f"\n💎 目前點數：{current_points} 點")
            response = "\n".join(response_lines)
            
            self.publisher.reply_text(reply_token, response, user_id, event)
            return "OK"
            
        except Exception as e:
            print(f"❌ 查詢交易記錄失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            self.publisher.reply_text(reply_token, "❌ 查詢失敗，請稍後再試", user_id, event)
            return "OK"
    
    def _handle_member_info(self, user_id: str, user_name: str, reply_token: str, event: dict):
        """處理會員資訊查詢"""
        try:
            from models.database import get_session
            from models.member import Member
            
            with get_session() as session:
                # 直接在當前 session 中查詢或創建會員
                member = session.query(Member).filter_by(user_id=user_id).first()
                
                if not member:
                    # 建立新會員（初始點數 0）
                    member = Member(
                        user_id=user_id,
                        display_name=user_name or "使用者",
                        points=0,
                        status='normal'
                    )
                    session.add(member)
                    session.commit()
                    print(f"✅ 新會員已建立: {user_id} ({user_name})")
                else:
                    # 會員已存在，更新顯示名稱（如果有提供）
                    if user_name and member.display_name != user_name:
                        member.display_name = user_name
                        session.commit()
                        print(f"✅ 會員資訊已更新: {user_id}")
                
                # 在 session 內提取所需的屬性值
                display_name = member.display_name
                points = member.points
                status = member.status
                created_at = member.created_at
            
            # 狀態顯示
            status_map = {
                'normal': '正常',
                'vip': 'VIP',
                'suspended': '停用',
                'banned': '黑名單'
            }
            status_text = status_map.get(status, status)
            
            # 格式化日期
            created_at_str = created_at.strftime("%Y/%m/%d %H:%M") if created_at else "未知"
            
            response = f"""👤 會員資訊

📝 姓名：{display_name}
🆔 ID：{user_id[:8]}...
💎 剩餘點數：{points} 點
📊 會員狀態：{status_text}
📅 註冊日期：{created_at_str}

輸入「點數」查看點數
輸入「歷史」查看交易記錄"""
            
            self.publisher.reply_text(reply_token, response, user_id, event)
            return "OK"
            
        except Exception as e:
            print(f"❌ 查詢會員資訊失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            self.publisher.reply_text(reply_token, "❌ 查詢失敗，請稍後再試", user_id, event)
            return "OK"

