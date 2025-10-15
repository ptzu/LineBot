from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, func
from models.database import Base


class PointTransaction(Base):
    """點數交易記錄模型"""
    __tablename__ = 'point_transactions'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='交易 ID')
    user_id = Column(String(50), ForeignKey('members.user_id'), nullable=False, index=True, comment='會員 ID')
    transaction_type = Column(String(20), nullable=False, comment='交易類型')
    points = Column(Integer, nullable=False, comment='點數變動')
    balance_after = Column(Integer, nullable=False, comment='交易後餘額')
    description = Column(Text, nullable=True, comment='交易說明')
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment='交易時間')
    
    def __repr__(self):
        return f"<PointTransaction(id={self.id}, user_id='{self.user_id}', type='{self.transaction_type}', points={self.points})>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'transaction_type': self.transaction_type,
            'points': self.points,
            'balance_after': self.balance_after,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

