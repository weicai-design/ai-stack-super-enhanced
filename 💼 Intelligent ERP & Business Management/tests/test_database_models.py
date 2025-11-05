"""
Test Database Models
测试数据库模型

验证所有数据库模型的创建和基本操作
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import (
    Base,
    FinancialData,
    FinancialReport,
    BusinessProcess,
    ProcessInstance,
    ProcessTracking,
    Customer,
    Order,
    OrderItem,
    Project,
    FinancialCategory,
    PeriodType,
    ProcessStatus,
)


# 创建测试数据库（SQLite内存数据库）
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_financial_data_model(db_session):
    """测试财务数据模型"""
    financial_data = FinancialData(
        date=date.today(),
        period_type=PeriodType.DAILY,
        category=FinancialCategory.REVENUE,
        amount=Decimal("100000.00"),
        description="测试收入",
    )
    
    db_session.add(financial_data)
    db_session.commit()
    
    assert financial_data.id is not None
    assert financial_data.date == date.today()
    assert financial_data.category == FinancialCategory.REVENUE
    assert float(financial_data.amount) == 100000.00


def test_customer_model(db_session):
    """测试客户模型"""
    customer = Customer(
        name="测试客户",
        code="CUST001",
        category="A类客户",
        contact_person="张三",
        contact_phone="13800138000",
        contact_email="test@example.com",
    )
    
    db_session.add(customer)
    db_session.commit()
    
    assert customer.id is not None
    assert customer.name == "测试客户"
    assert customer.code == "CUST001"


def test_order_model(db_session):
    """测试订单模型"""
    # 先创建客户
    customer = Customer(
        name="测试客户",
        code="CUST001",
    )
    db_session.add(customer)
    db_session.flush()
    
    # 创建订单
    order = Order(
        order_number="ORD001",
        customer_id=customer.id,
        order_date=date.today(),
        total_amount=Decimal("50000.00"),
        status="pending",
    )
    
    db_session.add(order)
    db_session.commit()
    
    assert order.id is not None
    assert order.order_number == "ORD001"
    assert order.customer_id == customer.id
    assert order.customer.name == "测试客户"


def test_order_item_model(db_session):
    """测试订单明细模型"""
    # 创建客户和订单
    customer = Customer(name="测试客户", code="CUST001")
    db_session.add(customer)
    db_session.flush()
    
    order = Order(
        order_number="ORD001",
        customer_id=customer.id,
        order_date=date.today(),
        total_amount=Decimal("50000.00"),
    )
    db_session.add(order)
    db_session.flush()
    
    # 创建订单明细
    order_item = OrderItem(
        order_id=order.id,
        product_name="测试产品",
        product_code="PROD001",
        quantity=Decimal("10.00"),
        unit_price=Decimal("5000.00"),
        total_price=Decimal("50000.00"),
    )
    
    db_session.add(order_item)
    db_session.commit()
    
    assert order_item.id is not None
    assert order_item.order_id == order.id
    assert order_item.product_name == "测试产品"
    assert float(order_item.total_price) == 50000.00


def test_business_process_model(db_session):
    """测试业务流程模型"""
    process = BusinessProcess(
        name="测试流程",
        description="这是一个测试流程",
        process_type="生产流程",
        stages=[
            {"name": "阶段1", "order": 1},
            {"name": "阶段2", "order": 2},
        ],
        kpi_metrics={"completion_rate": 95},
    )
    
    db_session.add(process)
    db_session.commit()
    
    assert process.id is not None
    assert process.name == "测试流程"
    assert len(process.stages) == 2


def test_process_instance_model(db_session):
    """测试流程实例模型"""
    # 创建流程定义
    process = BusinessProcess(
        name="测试流程",
        stages=[{"name": "初始", "order": 1}],
    )
    db_session.add(process)
    db_session.flush()
    
    # 创建流程实例
    instance = ProcessInstance(
        process_id=process.id,
        instance_name="测试实例",
        status=ProcessStatus.PENDING,
        current_stage="初始",
        started_at=datetime.utcnow(),
    )
    
    db_session.add(instance)
    db_session.commit()
    
    assert instance.id is not None
    assert instance.process_id == process.id
    assert instance.status == ProcessStatus.PENDING


def test_process_tracking_model(db_session):
    """测试流程跟踪模型"""
    # 创建流程和实例
    process = BusinessProcess(name="测试流程", stages=[{"name": "阶段1", "order": 1}])
    db_session.add(process)
    db_session.flush()
    
    instance = ProcessInstance(
        process_id=process.id,
        status=ProcessStatus.IN_PROGRESS,
        current_stage="阶段1",
    )
    db_session.add(instance)
    db_session.flush()
    
    # 创建跟踪记录
    tracking = ProcessTracking(
        instance_id=instance.id,
        stage="阶段1",
        status="completed",
        action="完成任务",
        operator="张三",
    )
    
    db_session.add(tracking)
    db_session.commit()
    
    assert tracking.id is not None
    assert tracking.instance_id == instance.id
    assert tracking.stage == "阶段1"


def test_relationships(db_session):
    """测试模型关系"""
    # 创建客户
    customer = Customer(name="测试客户", code="CUST001")
    db_session.add(customer)
    db_session.flush()
    
    # 创建订单
    order = Order(
        order_number="ORD001",
        customer_id=customer.id,
        order_date=date.today(),
        total_amount=Decimal("10000.00"),
    )
    db_session.add(order)
    db_session.flush()
    
    # 创建订单明细
    item1 = OrderItem(
        order_id=order.id,
        product_name="产品1",
        quantity=Decimal("5.00"),
        unit_price=Decimal("1000.00"),
        total_price=Decimal("5000.00"),
    )
    item2 = OrderItem(
        order_id=order.id,
        product_name="产品2",
        quantity=Decimal("5.00"),
        unit_price=Decimal("1000.00"),
        total_price=Decimal("5000.00"),
    )
    db_session.add(item1)
    db_session.add(item2)
    db_session.commit()
    
    # 验证关系
    assert len(order.items) == 2
    assert order.customer.name == "测试客户"
    assert item1.order.order_number == "ORD001"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

