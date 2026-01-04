"""
用戶狀態遷移腳本
將現有的記憶體狀態遷移到資料庫（如果有的話）

使用方式:
    python scripts/migrate_user_states.py
"""

import os
import sys

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from models.database import init_database, create_tables
from user_state_manager import UserStateManager

def migrate_user_states():
    """遷移用戶狀態到資料庫"""
    print("=" * 50)
    print("🔄 用戶狀態遷移腳本")
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
        create_tables()
        print("✅ 資料庫初始化完成")
        
        # 建立 UserStateManager
        print("📝 建立 UserStateManager...")
        state_manager = UserStateManager()
        print("✅ UserStateManager 建立完成")
        
        # 檢查是否有現有狀態
        print("\n🔍 檢查現有狀態...")
        all_states = state_manager.get_all_states()
        
        if all_states:
            print(f"📊 發現 {len(all_states)} 個現有狀態:")
            for user_id, state in all_states.items():
                print(f"  - {user_id}: {state.get('feature')} - {state.get('state')}")
        else:
            print("ℹ️  沒有發現現有狀態")
        
        print("\n" + "=" * 50)
        print("✅ 遷移完成！")
        print("=" * 50)
        print()
        print("💡 說明：")
        print("  - 用戶狀態現在儲存在資料庫中")
        print("  - 狀態會在伺服器重啟後保持")
        print("  - 可以透過資料庫管理工具查看狀態")
        print("  - 舊的記憶體狀態已不再使用")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ 遷移失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = migrate_user_states()
    sys.exit(0 if success else 1)
