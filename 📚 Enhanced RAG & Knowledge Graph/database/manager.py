"""
AI-STACK V5.7 数据库管理器
提供统一的数据库操作接口
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
from .models import Base, FinanceRecord, ERPCustomer, Task, Content, StockPosition, ERPOrder, TrendTopic
from datetime import datetime, timedelta
import random

class DatabaseManager:
    """数据库管理器 - 单例模式"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if self._initialized:
            return
            
        if db_path is None:
            # 默认数据库路径
            db_dir = Path(__file__).parent.parent.parent / "data"
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / "ai_stack_v5_7.db"
        
        self.db_path = str(db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}', echo=False)
        
        # 创建所有表
        Base.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        
        self._initialized = True
        print(f"✅ 数据库已初始化: {self.db_path}")
    
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()
    
    # ==================== 财务管理 ====================
    
    def add_finance_record(self, period: str, revenue: float, cost: float) -> FinanceRecord:
        """添加财务记录"""
        session = self.get_session()
        try:
            profit = revenue - cost
            profit_margin = (profit / revenue * 100) if revenue > 0 else 0
            
            record = FinanceRecord(
                period=period,
                revenue=revenue,
                cost=cost,
                profit=profit,
                profit_margin=round(profit_margin, 2)
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        finally:
            session.close()
    
    def get_finance_records(self, limit: int = 10):
        """获取财务记录"""
        session = self.get_session()
        try:
            return session.query(FinanceRecord).order_by(FinanceRecord.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    # ==================== ERP客户管理 ====================
    
    def create_customer(self, id: str, name: str, **kwargs) -> ERPCustomer:
        """创建客户"""
        session = self.get_session()
        try:
            customer = ERPCustomer(id=id, name=name, **kwargs)
            session.add(customer)
            session.commit()
            session.refresh(customer)
            return customer
        finally:
            session.close()
    
    def get_customers(self, limit: int = 100):
        """获取客户列表"""
        session = self.get_session()
        try:
            return session.query(ERPCustomer).limit(limit).all()
        finally:
            session.close()
    
    def get_customer_by_id(self, customer_id: str):
        """根据ID获取客户"""
        session = self.get_session()
        try:
            return session.query(ERPCustomer).filter_by(id=customer_id).first()
        finally:
            session.close()
    
    def update_customer(self, customer_id: str, **kwargs) -> bool:
        """更新客户信息"""
        session = self.get_session()
        try:
            customer = session.query(ERPCustomer).filter_by(id=customer_id).first()
            if customer:
                for key, value in kwargs.items():
                    setattr(customer, key, value)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # ==================== 任务管理 ====================
    
    def create_task(self, id: str, title: str, **kwargs) -> Task:
        """创建任务"""
        session = self.get_session()
        try:
            task = Task(id=id, title=title, **kwargs)
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()
    
    def get_tasks(self, status: str = None, limit: int = 100):
        """获取任务列表"""
        session = self.get_session()
        try:
            query = session.query(Task)
            if status:
                query = query.filter_by(status=status)
            return query.order_by(Task.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    def update_task_status(self, task_id: str, status: str, progress: int = None) -> bool:
        """更新任务状态"""
        session = self.get_session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                task.status = status
                if progress is not None:
                    task.progress = progress
                if status == 'completed':
                    task.completed_at = datetime.now()
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # ==================== 内容管理 ====================
    
    def create_content(self, id: str, content: str, **kwargs) -> Content:
        """创建内容"""
        session = self.get_session()
        try:
            content_obj = Content(id=id, content=content, **kwargs)
            session.add(content_obj)
            session.commit()
            session.refresh(content_obj)
            return content_obj
        finally:
            session.close()
    
    def get_contents(self, limit: int = 50):
        """获取内容列表"""
        session = self.get_session()
        try:
            return session.query(Content).order_by(Content.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    # ==================== 股票持仓管理 ====================
    
    def add_position(self, symbol: str, name: str, quantity: int, cost: float, current: float) -> StockPosition:
        """添加持仓"""
        session = self.get_session()
        try:
            profit = (current - cost) * quantity
            profit_rate = (current - cost) / cost * 100
            
            position = StockPosition(
                symbol=symbol,
                name=name,
                quantity=quantity,
                cost=cost,
                current=current,
                profit=round(profit, 2),
                profit_rate=round(profit_rate, 2)
            )
            session.add(position)
            session.commit()
            session.refresh(position)
            return position
        finally:
            session.close()
    
    def get_positions(self):
        """获取所有持仓"""
        session = self.get_session()
        try:
            return session.query(StockPosition).all()
        finally:
            session.close()
    
    def update_position_price(self, symbol: str, current: float) -> bool:
        """更新持仓价格"""
        session = self.get_session()
        try:
            position = session.query(StockPosition).filter_by(symbol=symbol).first()
            if position:
                position.current = current
                position.profit = (current - position.cost) * position.quantity
                position.profit_rate = (current - position.cost) / position.cost * 100
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # ==================== ERP订单管理 ====================
    
    def create_order(self, id: str, customer_id: str, product_name: str, quantity: int, unit_price: float) -> ERPOrder:
        """创建订单"""
        session = self.get_session()
        try:
            total_amount = quantity * unit_price
            order = ERPOrder(
                id=id,
                customer_id=customer_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                total_amount=total_amount
            )
            session.add(order)
            session.commit()
            session.refresh(order)
            return order
        finally:
            session.close()
    
    def get_orders(self, status: str = None, limit: int = 100):
        """获取订单列表"""
        session = self.get_session()
        try:
            query = session.query(ERPOrder)
            if status:
                query = query.filter_by(status=status)
            return query.order_by(ERPOrder.created_at.desc()).limit(limit).all()
        finally:
            session.close()
    
    # ==================== 趋势话题管理 ====================
    
    def add_trend_topic(self, topic: str, growth: float, heat: float, articles: int) -> TrendTopic:
        """添加趋势话题"""
        session = self.get_session()
        try:
            trend = TrendTopic(
                topic=topic,
                growth=growth,
                heat=heat,
                articles=articles
            )
            session.add(trend)
            session.commit()
            session.refresh(trend)
            return trend
        finally:
            session.close()
    
    def get_trend_topics(self, limit: int = 10):
        """获取趋势话题"""
        session = self.get_session()
        try:
            return session.query(TrendTopic).order_by(TrendTopic.heat.desc()).limit(limit).all()
        finally:
            session.close()
    
    # ==================== 数据初始化 ====================
    
    def init_demo_data(self):
        """初始化演示数据"""
        print("🔄 初始化演示数据...")
        
        # 1. 财务记录
        for i in range(6):
            date = (datetime.now() - timedelta(days=30*(5-i))).strftime("%Y-%m")
            revenue = 950000 + i * 50000 + random.randint(-20000, 20000)
            cost = 680000 + i * 35000 + random.randint(-15000, 15000)
            self.add_finance_record(date, revenue, cost)
        
        # 2. ERP客户
        customers = [
            ("C001", "阿里巴巴集团", "张经理", "13800138001", "vip"),
            ("C002", "腾讯科技", "李总", "13800138002", "vip"),
            ("C003", "百度在线", "王主管", "13800138003", "normal"),
        ]
        for cid, name, contact, phone, level in customers:
            self.create_customer(cid, name, contact=contact, phone=phone, level=level)
        
        # 3. 任务
        tasks = [
            ("T001", "完成V5.7开发", "high", "in_progress", 85),
            ("T002", "测试所有功能", "high", "pending", 0),
            ("T003", "编写文档", "medium", "pending", 0),
        ]
        for tid, title, priority, status, progress in tasks:
            self.create_task(tid, title, priority=priority, status=status, progress=progress, description=f"任务{tid}的详细描述")
        
        # 4. 股票持仓
        positions = [
            ("600519", "贵州茅台", 100, 1680.5, 1725.3),
            ("000001", "平安银行", 500, 11.8, 12.5),
        ]
        for symbol, name, qty, cost, current in positions:
            self.add_position(symbol, name, qty, cost, current)
        
        # 5. 趋势话题
        topics = [
            ("AI技术突破", 235, 98, 12456),
            ("新能源革命", 128, 85, 8234),
            ("元宇宙应用", 89, 72, 5678),
        ]
        for topic, growth, heat, articles in topics:
            self.add_trend_topic(topic, growth, heat, articles)
        
        print("✅ 演示数据初始化完成")


# 全局数据库实例
_db_instance = None

def get_db() -> DatabaseManager:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
        # 初始化演示数据（仅首次）
        try:
            _db_instance.init_demo_data()
        except Exception as e:
            print(f"⚠️  演示数据已存在或初始化失败: {e}")
    return _db_instance


print("✅ 数据库管理器已加载")


