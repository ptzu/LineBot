"""
用戶狀態清理腳本
清理超過指定時間的舊用戶狀態

使用方式:
    python scripts/cleanup_user_states.py [小時數]
    
範例:
    python scripts/cleanup_user_states.py 24    # 清理超過 24 小時的狀態
    python scripts/cleanup_user_states.py 168   # 清理超過 7 天的狀態
"""

import os
import sys
import argparse

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from models.database import init_database
from user_state_manager import UserStateManager

def cleanup_user_states(hours=24):
    """清理用戶狀態"""
    print("=" * 50)
    print("🧹 用戶狀態清理腳本")
    print("=" * 50)
    
    # 載入環境變數
    load_dotenv()
    
    # 檢查 DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ 錯誤：未設定 DATABASE_URL 環境變數")
        print("請在 .env 檔案中設定 DATABASE_URL")
        return False
    
    try:
        # 初始化資料庫
        print("🔌 初始化資料庫...")
        init_database()
        print("✅ 資料庫初始化完成")
        
        # 建立 UserStateManager
        print("📝 建立 UserStateManager...")
        state_manager = UserStateManager()
        print("✅ UserStateManager 建立完成")
        
        # 檢查清理前的狀態數量
        print(f"\n🔍 檢查超過 {hours} 小時的舊狀態...")
        all_states = state_manager.get_all_states()
        print(f"📊 目前總共有 {len(all_states)} 個狀態")
        
        if all_states:
            print("現有狀態:")
            for user_id, state in all_states.items():
                print(f"  - {user_id}: {state.get('feature')} - {state.get('state')}")
        
        # 執行清理
        print(f"\n🧹 開始清理超過 {hours} 小時的舊狀態...")
        cleaned_count = state_manager.cleanup_old_states(hours=hours)
        
        # 檢查清理後的狀態
        remaining_states = state_manager.get_all_states()
        print(f"📊 清理後剩餘 {len(remaining_states)} 個狀態")
        
        if remaining_states:
            print("剩餘狀態:")
            for user_id, state in remaining_states.items():
                print(f"  - {user_id}: {state.get('feature')} - {state.get('state')}")
        
        print("\n" + "=" * 50)
        print("✅ 清理完成！")
        print("=" * 50)
        print(f"🧹 已清理 {cleaned_count} 個舊狀態")
        print(f"📊 剩餘 {len(remaining_states)} 個活躍狀態")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 清理失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='清理用戶狀態')
    parser.add_argument('hours', type=int, nargs='?', default=24,
                       help='清理超過指定小時數的狀態 (預設: 24)')
    
    args = parser.parse_args()
    
    if args.hours < 0:
        print("❌ 錯誤：小時數不能為負數")
        sys.exit(1)
    
    if args.hours == 0:
        print("⚠️  警告：將清理所有狀態！")
        confirm = input("確定要繼續嗎？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 已取消清理")
            sys.exit(0)
    
    success = cleanup_user_states(args.hours)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
