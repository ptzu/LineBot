from sqlalchemy import Column, String, Integer, DateTime, func
from models.database import Base


class Member(Base):
    """會員模型"""
    __tablename__ = 'members'
    
    user_id = Column(String(50), primary_key=True, comment='LINE user ID')
    display_name = Column(String(100), nullable=False, comment='顯示名稱')
    picture_url = Column(String(500), nullable=True, comment='頭像 URL')
    email = Column(String(255), nullable=True, comment='信箱')
    points = Column(Integer, default=0, nullable=False, comment='剩餘點數')
    status = Column(String(20), default='normal', nullable=False, comment='會員狀態')
    created_at = Column(DateTime, server_default=func.now(), nullable=False, comment='建立時間')
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新時間')
    
    def __repr__(self):
        return f"<Member(user_id='{self.user_id}', name='{self.display_name}', points={self.points}, status='{self.status}')>"
    
    def to_dict(self):
        """轉換為字典格式"""
        return {
            'user_id': self.user_id,
            'display_name': self.display_name,
            'picture_url': self.picture_url,
            'email': self.email,
            'points': self.points,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

