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
    
    # 建立 engine
    _engine = create_engine(
        database_url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # 確保連線有效
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
    Base.metadata.create_all(_engine)
    print("✅ 資料表建立完成")


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

