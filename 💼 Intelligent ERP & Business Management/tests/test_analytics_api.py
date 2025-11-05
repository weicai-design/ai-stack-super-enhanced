"""
Test Analytics API
测试经营分析API

验证开源分析、成本分析、产出效益分析
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path
erp_dir = Path(__file__).parent.parent
sys.path.insert(0, str(erp_dir))

from core.database_models import (
    Base,
    Customer,
    Order,
    OrderItem,
    FinancialData,
    PeriodType,
    FinancialCategory,
)
from core.database import get_db
from api.analytics_api import router
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)

# 创建测试数据库
test_engine = create_engine("sqlite:///:memory:", echo=False)
Base.metadata.create_all(test_engine)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """覆盖get_db依赖"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试前设置数据库"""
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_revenue_analysis():
    """测试开源分析"""
    # 创建测试数据
    db = next(override_get_db())
    today = date.today()
    
    # 创建客户
    customer1 = Customer(name="客户A", code="CUST001", category="A类")
    customer2 = Customer(name="客户B", code="CUST002", category="B类")
    db.add(customer1)
    db.add(customer2)
    db.flush()
    
    # 创建订单
    order1 = Order(
        order_number="ORD001",
        customer_id=customer1.id,
        order_date=today,
        total_amount=Decimal("50000.00"),
    )
    order2 = Order(
        order_number="ORD002",
        customer_id=customer2.id,
        order_date=today,
        total_amount=Decimal("30000.00"),
    )
    db.add(order1)
    db.add(order2)
    db.flush()
    
    # 创建订单明细
    item1 = OrderItem(
        order_id=order1.id,
        product_name="产品1",
        product_code="PROD001",
        quantity=Decimal("10.00"),
        unit_price=Decimal("5000.00"),
        total_price=Decimal("50000.00"),
    )
    db.add(item1)
    db.commit()
    db.close()
    
    # 测试开源分析
    response = client.get("/analytics/revenue?period_type=daily")
    
    assert response.status_code == 200
    result = response.json()
    assert result["total_revenue"] == 80000.0
    assert "A类" in result["customer_category_stats"] or len(result["customer_category_stats"]) > 0
    assert result["order_stats"]["total_orders"] == 2


def test_cost_analysis():
    """测试成本分析"""
    # 创建测试数据
    db = next(override_get_db())
    today = date.today()
    
    # 创建成本数据
    sales_cost = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.EXPENSE,
        subcategory="sales",
        amount=Decimal("10000.00"),
    )
    management_cost = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.EXPENSE,
        subcategory="management",
        amount=Decimal("5000.00"),
    )
    db.add(sales_cost)
    db.add(management_cost)
    
    # 创建收入数据
    revenue = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.REVENUE,
        amount=Decimal("50000.00"),
    )
    db.add(revenue)
    db.commit()
    db.close()
    
    # 测试成本分析
    response = client.get("/analytics/cost?period_type=daily")
    
    assert response.status_code == 200
    result = response.json()
    assert result["total_cost"] == 15000.0
    assert "sales" in result["cost_by_category"] or len(result["cost_by_category"]) > 0
    assert "break_even_analysis" in result
    assert result["break_even_analysis"]["profit"] == 35000.0


def test_efficiency_analysis():
    """测试产出效益分析"""
    # 创建测试数据
    db = next(override_get_db())
    today = date.today()
    
    # 创建投入数据
    investment = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.INVESTMENT,
        amount=Decimal("100000.00"),
    )
    db.add(investment)
    
    # 创建产出数据
    output = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.REVENUE,
        amount=Decimal("150000.00"),
    )
    db.add(output)
    db.commit()
    db.close()
    
    # 测试产出效益分析
    response = client.get("/analytics/efficiency?period_type=daily")
    
    assert response.status_code == 200
    result = response.json()
    assert result["input_output_ratio"] == 1.5  # 150000 / 100000
    assert result["efficiency_metrics"]["investment"] == 100000.0
    assert result["efficiency_metrics"]["output"] == 150000.0
    assert result["efficiency_metrics"]["roi"] == 50.0  # (150000-100000)/100000 * 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

