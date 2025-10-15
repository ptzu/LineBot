from datetime import datetime
from models.database import get_session
from models.member import Member
from models.point_transaction import PointTransaction


class MemberService:
    """會員服務層 - 處理所有會員相關的業務邏輯"""
    
    def get_or_create_member(self, user_id, display_name=None, picture_url=None, email=None):
        """
        取得或建立會員
        
        Args:
            user_id: LINE user ID
            display_name: 顯示名稱
            picture_url: 頭像 URL
            email: 信箱
            
        Returns:
            Member: 會員物件
        """
        with get_session() as session:
            member = session.query(Member).filter_by(user_id=user_id).first()
            
            if member:
                # 會員已存在，更新資訊（如果有提供）
                updated = False
                if display_name and member.display_name != display_name:
                    member.display_name = display_name
                    updated = True
                if picture_url and member.picture_url != picture_url:
                    member.picture_url = picture_url
                    updated = True
                if email and member.email != email:
                    member.email = email
                    updated = True
                
                if updated:
                    session.commit()
                    print(f"✅ 會員資訊已更新: {user_id}")
                
                # 重新查詢以取得最新資料
                session.expire(member)
                return session.query(Member).filter_by(user_id=user_id).first()
            else:
                # 建立新會員（初始點數 0）
                new_member = Member(
                    user_id=user_id,
                    display_name=display_name or "使用者",
                    picture_url=picture_url,
                    email=email,
                    points=0,
                    status='normal'
                )
                session.add(new_member)
                session.commit()
                print(f"✅ 新會員已建立: {user_id} ({display_name})")
                
                # 重新查詢以取得完整資料
                return session.query(Member).filter_by(user_id=user_id).first()
    
    def get_member_info(self, user_id):
        """
        查詢會員完整資訊
        
        Args:
            user_id: LINE user ID
            
        Returns:
            Member: 會員物件，不存在則返回 None
        """
        with get_session() as session:
            return session.query(Member).filter_by(user_id=user_id).first()
    
    def get_member_points(self, user_id):
        """
        查詢會員點數
        
        Args:
            user_id: LINE user ID
            
        Returns:
            int: 點數，會員不存在則返回 None
        """
        with get_session() as session:
            member = session.query(Member).filter_by(user_id=user_id).first()
            return member.points if member else None
    
    def add_points(self, user_id, points, transaction_type='earn', description=None):
        """
        增加點數並記錄交易
        
        Args:
            user_id: LINE user ID
            points: 要增加的點數（正數）
            transaction_type: 交易類型 (earn, admin_add)
            description: 交易說明
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        if points <= 0:
            print(f"❌ 點數必須為正數: {points}")
            return False
        
        with get_session() as session:
            try:
                # 查詢會員
                member = session.query(Member).filter_by(user_id=user_id).with_for_update().first()
                if not member:
                    print(f"❌ 會員不存在: {user_id}")
                    return False
                
                # 增加點數
                member.points += points
                new_balance = member.points
                
                # 記錄交易
                transaction = PointTransaction(
                    user_id=user_id,
                    transaction_type=transaction_type,
                    points=points,
                    balance_after=new_balance,
                    description=description
                )
                session.add(transaction)
                
                session.commit()
                print(f"✅ 點數已增加: {user_id} (+{points}), 餘額: {new_balance}")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ 增加點數失敗: {str(e)}")
                return False
    
    def deduct_points(self, user_id, points, description=None):
        """
        扣除點數並記錄交易
        
        Args:
            user_id: LINE user ID
            points: 要扣除的點數（正數）
            description: 交易說明
            
        Returns:
            bool: 成功返回 True，餘額不足或失敗返回 False
        """
        if points <= 0:
            print(f"❌ 點數必須為正數: {points}")
            return False
        
        with get_session() as session:
            try:
                # 查詢會員並鎖定（避免並發問題）
                member = session.query(Member).filter_by(user_id=user_id).with_for_update().first()
                if not member:
                    print(f"❌ 會員不存在: {user_id}")
                    return False
                
                # 檢查餘額
                if member.points < points:
                    print(f"❌ 點數不足: {user_id}, 需要 {points}, 目前 {member.points}")
                    return False
                
                # 扣除點數
                member.points -= points
                new_balance = member.points
                
                # 記錄交易（點數變動記為負數）
                transaction = PointTransaction(
                    user_id=user_id,
                    transaction_type='spend',
                    points=-points,
                    balance_after=new_balance,
                    description=description
                )
                session.add(transaction)
                
                session.commit()
                print(f"✅ 點數已扣除: {user_id} (-{points}), 餘額: {new_balance}")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ 扣除點數失敗: {str(e)}")
                return False
    
    def get_point_history(self, user_id, limit=10):
        """
        查詢交易記錄
        
        Args:
            user_id: LINE user ID
            limit: 返回筆數（預設 10）
            
        Returns:
            list: 交易記錄列表（從新到舊）
        """
        with get_session() as session:
            transactions = session.query(PointTransaction)\
                .filter_by(user_id=user_id)\
                .order_by(PointTransaction.created_at.desc())\
                .limit(limit)\
                .all()
            
            return [t.to_dict() for t in transactions]
    
    def update_member_status(self, user_id, status):
        """
        更新會員狀態
        
        Args:
            user_id: LINE user ID
            status: 新狀態 (normal, vip, suspended, banned)
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        valid_statuses = ['normal', 'vip', 'suspended', 'banned']
        if status not in valid_statuses:
            print(f"❌ 無效的狀態: {status}")
            return False
        
        with get_session() as session:
            try:
                member = session.query(Member).filter_by(user_id=user_id).first()
                if not member:
                    print(f"❌ 會員不存在: {user_id}")
                    return False
                
                old_status = member.status
                member.status = status
                session.commit()
                
                print(f"✅ 會員狀態已更新: {user_id} ({old_status} → {status})")
                return True
                
            except Exception as e:
                session.rollback()
                print(f"❌ 更新狀態失敗: {str(e)}")
                return False

