from models.database import get_session
from models.user_state import UserState
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any


class UserStateManager:
    """用戶狀態管理器，使用資料庫儲存狀態"""
    
    def __init__(self):
        """初始化狀態管理器"""
        pass
    
    def set_state(self, user_id: str, state: Dict[str, Any]):
        """設定用戶狀態"""
        try:
            with get_session() as session:
                # 檢查是否已存在狀態
                existing_state = session.query(UserState).filter_by(user_id=user_id).first()
                
                if existing_state:
                    # 更新現有狀態
                    existing_state.feature = state.get("feature")
                    existing_state.state = state.get("state")
                    existing_state.set_data(state.get("data"))
                    print(f"用戶 {user_id} 狀態已更新: {state}")
                else:
                    # 建立新狀態
                    new_state = UserState.create_state(
                        user_id=user_id,
                        feature=state.get("feature"),
                        state=state.get("state"),
                        data=state.get("data")
                    )
                    session.add(new_state)
                    print(f"用戶 {user_id} 狀態已建立: {state}")
                
                session.commit()
        except Exception as e:
            print(f"設定用戶狀態失敗: {str(e)}")
            raise e
    
    def get_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        """獲取用戶狀態"""
        try:
            with get_session() as session:
                user_state = session.query(UserState).filter_by(user_id=user_id).first()
                
                if user_state:
                    return {
                        "feature": user_state.feature,
                        "state": user_state.state,
                        "data": user_state.get_data()
                    }
                return None
        except Exception as e:
            print(f"獲取用戶狀態失敗: {str(e)}")
            return None
    
    def clear_state(self, user_id: str):
        """清除用戶狀態"""
        try:
            with get_session() as session:
                user_state = session.query(UserState).filter_by(user_id=user_id).first()
                
                if user_state:
                    old_state = {
                        "feature": user_state.feature,
                        "state": user_state.state,
                        "data": user_state.get_data()
                    }
                    session.delete(user_state)
                    session.commit()
                    print(f"用戶 {user_id} 狀態已清除 (原狀態: {old_state})")
                else:
                    print(f"用戶 {user_id} 沒有狀態需要清除")
        except Exception as e:
            print(f"清除用戶狀態失敗: {str(e)}")
            raise e
    
    def is_waiting_for_colorize(self, user_id: str) -> bool:
        """檢查用戶是否在等待彩色化確認（向後相容）"""
        state = self.get_state(user_id)
        if state:
            return (state.get("feature") == "colorize" and 
                    state.get("state") == "waiting")
        return False
    
    def is_colorizing(self, user_id: str) -> bool:
        """檢查用戶是否正在進行彩色化處理（向後相容）"""
        state = self.get_state(user_id)
        if state:
            return (state.get("feature") == "colorize" and 
                    state.get("state") == "processing")
        return False
    
    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """獲取所有用戶狀態（用於管理或除錯）"""
        try:
            with get_session() as session:
                states = session.query(UserState).all()
                return {
                    state.user_id: {
                        "feature": state.feature,
                        "state": state.state,
                        "data": state.get_data()
                    }
                    for state in states
                }
        except Exception as e:
            print(f"獲取所有狀態失敗: {str(e)}")
            return {}
    
    def cleanup_old_states(self, hours: int = 24):
        """清理超過指定小時的舊狀態"""
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import delete
            
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            with get_session() as session:
                result = session.execute(
                    delete(UserState).where(UserState.updated_at < cutoff_time)
                )
                session.commit()
                
                print(f"已清理 {result.rowcount} 個超過 {hours} 小時的舊狀態")
                return result.rowcount
        except Exception as e:
            print(f"清理舊狀態失敗: {str(e)}")
            return 0
