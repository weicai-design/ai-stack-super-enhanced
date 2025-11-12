"""
数据库模型和持久化
使用SQLAlchemy实现数据持久化
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

# 创建基类
Base = declarative_base()


# ==================== 数据模型 ====================

class ChatSession(Base):
    """聊天会话"""
    __tablename__ = 'chat_sessions'
    
    id = Column(String(50), primary_key=True)
    user_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    messages = Column(Text)  # JSON格式存储消息列表
    total_tokens = Column(Integer, default=0)
    context_summary = Column(Text, nullable=True)


class MemoItem(Base):
    """备忘录"""
    __tablename__ = 'memos'
    
    id = Column(String(50), primary_key=True)
    content = Column(Text, nullable=False)
    importance = Column(Integer, default=1)
    source = Column(String(20), default="user")  # user/agent/system
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(String(50), nullable=True)


class TaskItem(Base):
    """任务"""
    __tablename__ = 'tasks'
    
    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending/confirmed/executing/completed/rejected
    source = Column(String(30), default="user_defined")  # agent_identified/user_defined
    priority = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    estimated_duration = Column(Integer, nullable=True)  # 分钟
    required_modules = Column(Text, nullable=True)  # JSON格式
    user_id = Column(String(50), nullable=True)


class LearningRecord(Base):
    """学习记录"""
    __tablename__ = 'learning_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_type = Column(String(50), nullable=False)  # workflow_monitoring/issue/optimization
    content = Column(Text, nullable=False)  # JSON格式
    created_at = Column(DateTime, default=datetime.now)
    confidence = Column(Float, default=0.0)


class ERPCustomer(Base):
    """ERP客户"""
    __tablename__ = 'erp_customers'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(100), nullable=True)
    address = Column(Text, nullable=True)
    industry = Column(String(100), nullable=True)
    level = Column(String(20), default="normal")  # vip/normal/potential
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    extra_data = Column(Text, nullable=True)  # JSON格式（避免使用metadata保留字）


class ERPOrder(Base):
    """ERP订单"""
    __tablename__ = 'erp_orders'
    
    id = Column(String(50), primary_key=True)
    order_no = Column(String(50), unique=True, nullable=False)
    customer_id = Column(String(50), nullable=False)
    customer_name = Column(String(200), nullable=True)
    items = Column(Text, nullable=False)  # JSON格式存储订单项
    total_amount = Column(Float, default=0.0)
    status = Column(String(20), default="pending")  # pending/confirmed/producing/shipped/completed/cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    delivery_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class ERPProject(Base):
    """ERP项目"""
    __tablename__ = 'erp_projects'
    
    id = Column(String(50), primary_key=True)
    project_no = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    customer_id = Column(String(50), nullable=True)
    order_id = Column(String(50), nullable=True)
    status = Column(String(20), default="planning")  # planning/executing/completed/closed
    progress = Column(Float, default=0.0)
    budget = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class FinanceRecord(Base):
    """财务记录"""
    __tablename__ = 'finance_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    record_type = Column(String(20), nullable=False)  # income/expense/cost
    category = Column(String(100), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="CNY")
    date = Column(DateTime, nullable=False)
    order_id = Column(String(50), nullable=True)
    project_id = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class StockPosition(Base):
    """股票持仓"""
    __tablename__ = 'stock_positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=True)
    shares = Column(Float, nullable=False)
    avg_cost = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class StockTrade(Base):
    """股票交易记录"""
    __tablename__ = 'stock_trades'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    trade_type = Column(String(10), nullable=False)  # buy/sell
    shares = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    trade_time = Column(DateTime, default=datetime.now)
    strategy_name = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)


class ContentPost(Base):
    """内容发布记录"""
    __tablename__ = 'content_posts'
    
    id = Column(String(50), primary_key=True)
    title = Column(String(300), nullable=False)
    content = Column(Text, nullable=False)
    platform = Column(String(50), nullable=False)  # xiaohongshu/douyin/zhihu等
    status = Column(String(20), default="draft")  # draft/published/deleted
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==================== 数据库管理 ====================

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "aistack.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        # 确保数据目录存在
        db_dir = Path(db_path).parent
        if db_dir and str(db_dir) != ".":
            db_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建引擎
        self.engine = create_engine(f'sqlite:///{db_path}', echo=False)
        
        # 创建所有表
        Base.metadata.create_all(self.engine)
        
        # 创建Session工厂
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    def init_sample_data(self):
        """初始化示例数据"""
        session = self.get_session()
        
        try:
            # 检查是否已有数据
            if session.query(ERPCustomer).count() > 0:
                return
            
            # 添加示例客户
            customers = [
                ERPCustomer(
                    id="C001",
                    name="华为技术有限公司",
                    contact="张经理",
                    phone="13800138000",
                    email="zhang@huawei.com",
                    industry="科技",
                    level="vip"
                ),
                ERPCustomer(
                    id="C002",
                    name="小米集团",
                    contact="李经理",
                    phone="13900139000",
                    email="li@xiaomi.com",
                    industry="科技",
                    level="vip"
                )
            ]
            
            for customer in customers:
                session.add(customer)
            
            # 添加示例订单
            orders = [
                ERPOrder(
                    id="O001",
                    order_no="ORD-2025-001",
                    customer_id="C001",
                    customer_name="华为技术有限公司",
                    items='[{"product":"产品A","quantity":100,"price":245.0}]',
                    total_amount=24500.0,
                    status="confirmed"
                )
            ]
            
            for order in orders:
                session.add(order)
            
            session.commit()
            print("✅ 示例数据初始化完成")
        
        except Exception as e:
            session.rollback()
            print(f"⚠️  初始化示例数据失败: {e}")
        
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, int]:
        """获取数据库统计"""
        session = self.get_session()
        
        try:
            return {
                "chat_sessions": session.query(ChatSession).count(),
                "memos": session.query(MemoItem).count(),
                "tasks": session.query(TaskItem).count(),
                "learning_records": session.query(LearningRecord).count(),
                "customers": session.query(ERPCustomer).count(),
                "orders": session.query(ERPOrder).count(),
                "projects": session.query(ERPProject).count(),
                "finance_records": session.query(FinanceRecord).count(),
                "stock_positions": session.query(StockPosition).count(),
                "stock_trades": session.query(StockTrade).count(),
                "content_posts": session.query(ContentPost).count()
            }
        finally:
            session.close()


# 全局数据库实例
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_manager
    if _db_manager is None:
        db_path = os.getenv("DB_PATH", "data/aistack.db")
        _db_manager = DatabaseManager(db_path)
        # 初始化示例数据
        _db_manager.init_sample_data()
    return _db_manager


def get_db_session() -> Session:
    """获取数据库会话（用于依赖注入）"""
    db = get_db_manager()
    return db.get_session()


# 使用示例
if __name__ == "__main__":
    db = get_db_manager()
    
    print("✅ 数据库已初始化")
    print(f"📊 数据统计: {db.get_stats()}")
    
    # 测试添加数据
    session = db.get_session()
    
    try:
        # 添加备忘录
        memo = MemoItem(
            id=f"memo_{int(datetime.now().timestamp())}",
            content="测试备忘录",
            importance=3,
            source="test"
        )
        session.add(memo)
        session.commit()
        
        print("✅ 测试数据添加成功")
        print(f"📊 更新后统计: {db.get_stats()}")
    
    except Exception as e:
        session.rollback()
        print(f"❌ 测试失败: {e}")
    
    finally:
        session.close()

