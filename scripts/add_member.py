#!/usr/bin/env python3
"""
新增會員腳本
用於手動新增第一個會員或測試會員
"""

import os
import sys

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from models.database import init_database
from services.member_service import MemberService

def add_member():
    """新增會員"""
    print("=" * 50)
    print("👤 新增會員腳本")
    print("=" * 50)
    
    # 載入環境變數
    load_dotenv()
    
    try:
        # 初始化資料庫
        print("🔌 初始化資料庫連線...")
        init_database()
        print("✅ 資料庫連線成功")
        
        # 建立會員服務
        member_service = MemberService()
        
        # 取得用戶輸入
        print("\n請輸入會員資訊：")
        user_id = input("LINE User ID (例如: U1234567890abcdef): ").strip()
        if not user_id:
            print("❌ User ID 不能為空")
            return
        
        display_name = input("顯示名稱 (例如: 測試用戶): ").strip()
        if not display_name:
            display_name = "使用者"
        
        picture_url = input("頭像 URL (可選): ").strip()
        if not picture_url:
            picture_url = None
        
        email = input("電子郵件 (可選): ").strip()
        if not email:
            email = None
        
        # 新增會員
        print(f"\n📝 正在新增會員...")
        print(f"   User ID: {user_id}")
        print(f"   顯示名稱: {display_name}")
        print(f"   頭像: {picture_url or '無'}")
        print(f"   信箱: {email or '無'}")
        
        member = member_service.get_or_create_member(
            user_id=user_id,
            display_name=display_name,
            picture_url=picture_url,
            email=email
        )
        
        if member:
            print(f"\n✅ 會員新增成功！")
            print(f"   ID: {member.user_id}")
            print(f"   姓名: {member.display_name}")
            print(f"   點數: {member.points}")
            print(f"   狀態: {member.status}")
            print(f"   建立時間: {member.created_at}")
            
            # 詢問是否要增加點數
            add_points = input("\n是否要為此會員增加點數？(y/n): ").strip().lower()
            if add_points in ['y', 'yes', '是']:
                try:
                    points = int(input("請輸入要增加的點數: "))
                    if points > 0:
                        success = member_service.add_points(
                            user_id=user_id,
                            points=points,
                            transaction_type='admin_add',
                            description='管理員手動增加'
                        )
                        if success:
                            print(f"✅ 已為 {display_name} 增加 {points} 點")
                        else:
                            print("❌ 增加點數失敗")
                    else:
                        print("❌ 點數必須大於 0")
                except ValueError:
                    print("❌ 請輸入有效的數字")
            
            print("\n" + "=" * 50)
            print("🎉 會員新增完成！")
            print("=" * 50)
            
        else:
            print("❌ 會員新增失敗")
            
    except Exception as e:
        print(f"\n❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

def list_members():
    """列出所有會員"""
    print("=" * 50)
    print("📋 會員列表")
    print("=" * 50)
    
    try:
        # 初始化資料庫
        init_database()
        
        # 查詢所有會員
        from models.database import get_session
        from models.member import Member
        
        with get_session() as session:
            members = session.query(Member).all()
            
            if not members:
                print("📭 目前沒有任何會員")
                return
            
            print(f"📊 共 {len(members)} 位會員：\n")
            
            for i, member in enumerate(members, 1):
                print(f"{i}. {member.display_name}")
                print(f"   ID: {member.user_id}")
                print(f"   點數: {member.points}")
                print(f"   狀態: {member.status}")
                print(f"   建立時間: {member.created_at}")
                print()

    except Exception as e:
        print(f"❌ 查詢失敗: {str(e)}")

if __name__ == "__main__":
    print("選擇操作：")
    print("1. 新增會員")
    print("2. 查看會員列表")
    
    choice = input("請選擇 (1/2): ").strip()
    
    if choice == "1":
        add_member()
    elif choice == "2":
        list_members()
    else:
        print("❌ 無效的選擇")
