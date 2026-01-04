import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from contextlib import contextmanager

# 建立 Base 模型類別
Base = declarative_base()

# 全域變數
_engine = None
_SessionFactory = None


def init_database():
    """初始化資料庫連線"""
    global _engine, _SessionFactory
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL 環境變數未設定")
    
    print(f"🗄️  連接資料庫...")
    
    # 處理 IPv6 問題：強制使用 IPv4
    # Supabase 支援 IPv4 和 IPv6，但某些環境（如 Railway）可能不支援 IPv6
    import re
    
    # 檢查是否為 Supabase 連線且需要強制 IPv4
    if "supabase.co" in database_url:
        # 在 connect_args 中加入 hostaddr 來強制解析 IPv4
        print("🔧 檢測到 Supabase，配置 IPv4 優先連線...")
        
        # 解析主機名稱
        match = re.search(r'@([^:]+):', database_url)
        if match:
            hostname = match.group(1)
            print(f"🌐 主機名稱: {hostname}")
            
            # 嘗試解析 IPv4 地址
            try:
                import socket
                # 強制使用 IPv4
                ipv4_addr = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
                print(f"✅ 解析到 IPv4: {ipv4_addr}")
                
                connect_args = {
                    "connect_timeout": 10,
                    "application_name": "linebot_member_system",
                    "hostaddr": ipv4_addr  # 強制使用 IPv4 地址
                }
            except Exception as e:
                print(f"⚠️  IPv4 解析失敗: {e}，使用預設連線")
                connect_args = {
                    "connect_timeout": 10,
                    "application_name": "linebot_member_system"
                }
        else:
            connect_args = {
                "connect_timeout": 10,
                "application_name": "linebot_member_system"
            }
    else:
        connect_args = {
            "connect_timeout": 10,
            "application_name": "linebot_member_system"
        }
    
    # 建立 engine，優化連線設定
    _engine = create_engine(
        database_url,
        pool_size=3,  # 減少連線池大小
        max_overflow=5,  # 減少最大溢出連線
        pool_pre_ping=True,  # 確保連線有效
        pool_recycle=3600,  # 連線回收時間（1小時）
        connect_args=connect_args,
        echo=False  # 設為 True 可以看到 SQL 語句（開發用）
    )
    
    # 建立 Session factory
    _SessionFactory = sessionmaker(bind=_engine)
    
    print("✅ 資料庫連線初始化完成")
    
    return _engine


def create_tables():
    """建立所有資料表"""
    if _engine is None:
        raise RuntimeError("資料庫尚未初始化，請先呼叫 init_database()")
    
    print("📊 建立資料表...")
    
    # 添加重試機制
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # 測試連線是否有效
            with _engine.connect() as conn:
                # 執行簡單查詢測試連線
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            
            # 建立資料表
            Base.metadata.create_all(_engine)
            print("✅ 資料表建立完成")
            return
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠️  建立資料表失敗，重試中... (嘗試 {attempt + 1}/{max_retries})")
                import time
                time.sleep(2)  # 等待 2 秒後重試
            else:
                print(f"❌ 建立資料表失敗，已重試 {max_retries} 次")
                raise e


@contextmanager
def get_session():
    """取得資料庫 session（使用 context manager）"""
    if _SessionFactory is None:
        raise RuntimeError("資料庫尚未初始化，請先呼叫 init_database()")
    
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_engine():
    """取得 engine（用於測試或特殊用途）"""
    return _engine

