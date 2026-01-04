from sqlalchemy import Column, String, Text, DateTime, func, Index
from models.database import Base
import json


class UserState(Base):
    """用戶狀態模型"""
    __tablename__ = 'user_states'
    
    user_id = Column(String(50), primary_key=True, comment='LINE user ID')
    feature = Column(String(50), nullable=False, comment='功能名稱')
    state = Column(String(50), nullable=False, comment='狀態名稱')
    data = Column(Text, nullable=True, comment='額外數據（JSON格式）')
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment='建立時間')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新時間')
    
    # 建立索引以提升查詢效能
    __table_args__ = (
        Index('idx_user_feature', 'user_id', 'feature'),
        Index('idx_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<UserState(user_id='{self.user_id}', feature='{self.feature}', state='{self.state}')>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'user_id': self.user_id,
            'feature': self.feature,
            'state': self.state,
            'data': self.get_data(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def get_data(self):
        """獲取解析後的數據"""
        if self.data:
            try:
                return json.loads(self.data)
            except json.JSONDecodeError:
                return None
        return None
    
    def set_data(self, data):
        """設定數據"""
        if data is None:
            self.data = None
        else:
            self.data = json.dumps(data, ensure_ascii=False)
    
    @classmethod
    def create_state(cls, user_id, feature, state, data=None):
        """建立新的狀態記錄"""
        user_state = cls(
            user_id=user_id,
            feature=feature,
            state=state
        )
        user_state.set_data(data)
        return user_state
