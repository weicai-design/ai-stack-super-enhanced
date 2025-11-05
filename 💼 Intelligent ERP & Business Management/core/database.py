"""
Database Configuration
数据库配置模块

管理数据库连接和会话
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 数据库配置
# 优先使用PostgreSQL，如果不可用则使用SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # 默认使用SQLite（开发测试）
    "sqlite:///./erp_data.db"
    # PostgreSQL（生产环境）
    # "postgresql://erp_user:erp_password_2025@localhost:5432/erp_db"
)

# 根据数据库类型设置参数
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    print("📝 使用SQLite数据库（开发模式）")
else:
    print("🐘 使用PostgreSQL数据库（生产模式）")

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # 连接前检查
    echo=False,          # 不打印SQL
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    初始化数据库
    
    创建所有表结构
    """
    from core.database_models import Base
    
    print("📦 正在创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def drop_all_tables() -> None:
    """
    删除所有表（危险操作，仅用于开发测试）
    """
    from core.database_models import Base
    
    print("⚠️  警告：正在删除所有表...")
    Base.metadata.drop_all(bind=engine)
    print("🗑️  所有表已删除")


def reset_db() -> None:
    """
    重置数据库（删除后重新创建）
    """
    drop_all_tables()
    init_db()
    print("🔄 数据库已重置")


if __name__ == "__main__":
    # 测试数据库连接
    print("🔍 测试数据库连接...")
    try:
        with engine.connect() as conn:
            print("✅ 数据库连接成功！")
            print(f"📍 连接地址: {DATABASE_URL}")
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
