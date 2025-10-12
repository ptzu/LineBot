from typing import List, Optional
from .base_feature import BaseFeature


class FeatureRegistry:
    """功能註冊表，負責路由訊息到對應的功能處理器"""
    
    def __init__(self):
        self.features: List[BaseFeature] = []
    
    def register(self, feature: BaseFeature):
        """註冊功能"""
        self.features.append(feature)
        print(f"已註冊功能: {feature.name}")
    
    def get_feature_by_name(self, name: str) -> Optional[BaseFeature]:
        """根據名稱獲取功能"""
        for feature in self.features:
            if feature.name == name:
                return feature
        return None
    
    def route_text_message(self, event: dict) -> dict:
        """
        路由文字訊息到對應的功能處理器
        
        Args:
            event: LINE webhook event
            
        Returns:
            dict: Flask 回應或 None
        """
        user_id = event.get('source', {}).get('userId', '')
        message = event.get('message', {}).get('text', '')
        
        # 1. 首先檢查用戶是否有特定功能的狀態
        user_state = self._get_user_state(user_id)
        if user_state and user_state.get("feature"):
            feature_name = user_state.get("feature")
            feature = self.get_feature_by_name(feature_name)
            if feature and feature.can_handle(message, user_id):
                print(f"根據用戶狀態路由到功能: {feature_name}")
                return feature.handle_text(event)
        
        # 2. 如果沒有狀態或狀態中的功能無法處理，則尋找能處理此訊息的功能
        for feature in self.features:
            if feature.can_handle(message, user_id):
                print(f"路由到功能: {feature.name}")
                return feature.handle_text(event)
        
        # 3. 沒有功能能處理此訊息
        print(f"沒有功能能處理訊息: {message}")
        return None
    
    def route_image_message(self, event: dict) -> dict:
        """
        路由圖片訊息到對應的功能處理器
        
        Args:
            event: LINE webhook event
            
        Returns:
            dict: Flask 回應或 None
        """
        user_id = event.get('source', {}).get('userId', '')
        
        # 1. 首先檢查用戶是否有特定功能的狀態
        user_state = self._get_user_state(user_id)
        if user_state and user_state.get("feature"):
            feature_name = user_state.get("feature")
            feature = self.get_feature_by_name(feature_name)
            if feature:
                print(f"根據用戶狀態路由圖片到功能: {feature_name}")
                return feature.handle_image(event)
        
        # 2. 如果沒有狀態，則尋找能處理圖片的功能
        for feature in self.features:
            if hasattr(feature, 'handle_image') and feature.handle_image(event) is not None:
                print(f"路由圖片到功能: {feature.name}")
                return feature.handle_image(event)
        
        # 3. 沒有功能能處理此圖片
        print(f"沒有功能能處理圖片訊息")
        return None
    
    def _get_user_state(self, user_id: str) -> dict:
        """獲取用戶狀態（需要從第一個功能中獲取 state_manager）"""
        if self.features:
            return self.features[0].get_user_state(user_id)
        return None
    
    def get_all_features(self) -> List[BaseFeature]:
        """獲取所有註冊的功能"""
        return self.features.copy()
    
    def get_feature_names(self) -> List[str]:
        """獲取所有功能名稱"""
        return [feature.name for feature in self.features]
