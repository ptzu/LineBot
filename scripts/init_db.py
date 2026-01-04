"""
資料庫初始化腳本
用於建立所有必要的資料表

使用方式:
    python scripts/init_db.py
"""

import os
import sys

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from models.database import init_database, create_tables

def main():
    """主程式"""
    print("=" * 50)
    print("🗄️  資料庫初始化腳本")
    print("=" * 50)
    
    # 載入環境變數
    load_dotenv()
    
    # 檢查 DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ 錯誤：未設定 DATABASE_URL 環境變數")
        print("請在 .env 檔案中設定 DATABASE_URL")
        print("\n範例：")
        print("DATABASE_URL=postgresql://user:password@host:port/dbname")
        print("\nSupabase 範例：")
        print("DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-ID].supabase.co:5432/postgres")
        sys.exit(1)
    
    print(f"📍 資料庫位置：{database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    print()
    
    try:
        # 初始化資料庫連線
        print("🔌 正在連接資料庫...")
        engine = init_database()
        print("✅ 資料庫連線成功")
        print()
        
        # 測試連線穩定性
        print("🔍 測試連線穩定性...")
        try:
            with engine.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                print(f"✅ 資料庫版本：{version[:50]}...")
        except Exception as e:
            print(f"⚠️  連線測試失敗：{str(e)}")
            print("繼續嘗試建立資料表...")
        print()
        
        # 建立所有資料表
        print("📊 正在建立資料表...")
        create_tables()
        print("✅ 資料表建立完成")
        print()
        
        # 顯示建立的資料表
        from models.member import Member
        from models.point_transaction import PointTransaction
        from models.user_state import UserState
        
        print("已建立以下資料表：")
        print("  1. members - 會員表")
        print("     - user_id (主鍵)")
        print("     - display_name")
        print("     - picture_url")
        print("     - email")
        print("     - points (預設 0)")
        print("     - status (預設 'normal')")
        print("     - created_at, updated_at")
        print()
        print("  2. point_transactions - 點數交易記錄表")
        print("     - id (主鍵)")
        print("     - user_id (外鍵)")
        print("     - transaction_type")
        print("     - points")
        print("     - balance_after")
        print("     - description")
        print("     - created_at")
        print()
        print("  3. user_states - 用戶狀態表")
        print("     - user_id (主鍵)")
        print("     - feature (功能名稱)")
        print("     - state (狀態名稱)")
        print("     - data (額外數據，JSON格式)")
        print("     - created_at, updated_at")
        print()
        
        print("=" * 50)
        print("🎉 資料庫初始化完成！")
        print("=" * 50)
        print()
        print("💡 提示：")
        print("  - LINE Bot 啟動時會自動連接資料庫")
        print("  - 會員首次使用時會自動建立（初始點數 0）")
        print("  - 可以透過管理功能手動增加會員點數")
        print()
        
    except Exception as e:
        print()
        print("=" * 50)
        print("❌ 資料庫初始化失敗")
        print("=" * 50)
        print(f"錯誤訊息：{str(e)}")
        print()
        print("常見問題排查：")
        print("  1. 檢查 DATABASE_URL 格式是否正確")
        print("  2. 確認資料庫伺服器是否運行中")
        print("  3. 檢查帳號密碼是否正確")
        print("  4. 確認網路連線正常")
        print("  5. 檢查資料庫是否允許遠端連接")
        print()
        print("Supabase 特定問題：")
        print("  - 檢查 Supabase 專案是否暫停（免費版 7 天不使用會暫停）")
        print("  - 確認密碼中沒有特殊字元需要 URL 編碼")
        print("  - 檢查 Supabase 專案狀態：https://supabase.com/dashboard")
        print("  - 嘗試重設資料庫密碼")
        print()
        print("診斷資訊：")
        print(f"  - DATABASE_URL 前綴：{database_url.split('@')[0].split('://')[0] if '://' in database_url else 'N/A'}")
        print(f"  - 主機位址：{database_url.split('@')[1].split(':')[0] if '@' in database_url else 'N/A'}")
        print(f"  - 連接埠：{database_url.split(':')[-1].split('/')[0] if ':' in database_url else 'N/A'}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

