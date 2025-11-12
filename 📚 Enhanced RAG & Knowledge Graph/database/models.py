"""
AI-STACK V5.7 数据库模型
定义所有表结构
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import json

Base = declarative_base()


class FinanceRecord(Base):
    """财务记录表"""
    __tablename__ = 'finance_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period = Column(String(20), nullable=False)  # 2025-11
    revenue = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    profit = Column(Float)
    profit_margin = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'period': self.period,
            'revenue': self.revenue,
            'cost': self.cost,
            'profit': self.profit,
            'profit_margin': self.profit_margin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ERPCustomer(Base):
    """ERP客户表"""
    __tablename__ = 'erp_customers'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    contact = Column(String(100))
    phone = Column(String(50))
    email = Column(String(100))
    level = Column(String(20), default='normal')  # vip/normal/potential
    orders = Column(Integer, default=0)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact': self.contact,
            'phone': self.phone,
            'email': self.email,
            'level': self.level,
            'orders': self.orders,
            'amount': self.amount,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Task(Base):
    """任务表"""
    __tablename__ = 'tasks'
    
    id = Column(String(50), primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    priority = Column(String(20), default='medium')  # high/medium/low
    status = Column(String(20), default='pending')   # pending/in_progress/completed/cancelled
    progress = Column(Integer, default=0)
    assignee = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    completed_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'progress': self.progress,
            'assignee': self.assignee,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Content(Base):
    """内容表"""
    __tablename__ = 'contents'
    
    id = Column(String(50), primary_key=True)
    content = Column(Text, nullable=False)
    prompt = Column(String(500))
    style = Column(String(50))
    word_count = Column(Integer)
    quality_score = Column(Float)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'prompt': self.prompt,
            'style': self.style,
            'word_count': self.word_count,
            'quality_score': self.quality_score,
            'published': self.published,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StockPosition(Base):
    """股票持仓表"""
    __tablename__ = 'stock_positions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    profit = Column(Float)
    profit_rate = Column(Float)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'quantity': self.quantity,
            'cost': self.cost,
            'current': self.current,
            'profit': self.profit,
            'profit_rate': self.profit_rate,
            'market_value': self.current * self.quantity,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ERPOrder(Base):
    """ERP订单表"""
    __tablename__ = 'erp_orders'
    
    id = Column(String(50), primary_key=True)
    customer_id = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String(20), default='draft')  # draft/confirmed/in_production/shipped/completed
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_amount': self.total_amount,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TrendTopic(Base):
    """趋势话题表"""
    __tablename__ = 'trend_topics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(200), nullable=False)
    growth = Column(Float, default=0)
    heat = Column(Float, default=0)
    articles = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'growth': self.growth,
            'heat': self.heat,
            'articles': self.articles,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UserAccount(Base):
    """用户账户表"""
    __tablename__ = 'user_accounts'
    
    id = Column(String(50), primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True)
    password_hash = Column(String(200))
    role = Column(String(20), default='user')  # admin/user/guest
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class APILog(Base):
    """API调用日志表"""
    __tablename__ = 'api_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    user_id = Column(String(50))
    status_code = Column(Integer)
    response_time = Column(Float)  # 毫秒
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'method': self.method,
            'user_id': self.user_id,
            'status_code': self.status_code,
            'response_time': self.response_time,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = 'system_configs'
    
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(String(500))
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Workflow(Base):
    """工作流表"""
    __tablename__ = 'workflows'
    
    id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    definition = Column(Text)  # JSON格式
    status = Column(String(20), default='draft')  # draft/active/inactive
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'definition': json.loads(self.definition) if self.definition else {},
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Notification(Base):
    """通知表"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(50), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    type = Column(String(20), default='info')  # info/warning/error/success
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'type': self.type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


print("✅ 数据库模型已加载（13个表）")

