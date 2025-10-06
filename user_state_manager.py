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
