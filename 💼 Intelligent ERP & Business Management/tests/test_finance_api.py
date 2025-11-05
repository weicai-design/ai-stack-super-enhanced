"""
Test Finance API
测试财务API

验证财务API的功能
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

from core.database_models import Base, FinancialData, PeriodType, FinancialCategory
from core.database import get_db
from api.finance_api import router
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


def test_create_financial_data():
    """测试创建财务数据"""
    data = {
        "date": "2025-11-02",
        "period_type": "daily",
        "category": "revenue",
        "amount": 100000.00,
        "description": "测试收入",
    }
    
    response = client.post("/finance/data", json=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["category"] == "revenue"
    assert result["amount"] == 100000.00


def test_get_finance_dashboard():
    """测试获取财务看板"""
    # 先创建一些测试数据
    db = next(override_get_db())
    today = date.today()
    
    # 创建收入数据
    revenue = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.REVENUE,
        amount=Decimal("100000.00"),
    )
    db.add(revenue)
    
    # 创建支出数据
    expense = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.EXPENSE,
        amount=Decimal("60000.00"),
    )
    db.add(expense)
    
    db.commit()
    db.close()
    
    # 获取看板
    response = client.get("/finance/dashboard?period_type=daily")
    
    assert response.status_code == 200
    result = response.json()
    assert "revenue" in result
    assert "expense" in result
    assert "profit" in result
    assert result["revenue"] == 100000.0
    assert result["expense"] == 60000.0
    assert result["profit"] == 40000.0


def test_get_financial_data():
    """测试查询财务数据"""
    # 创建测试数据
    db = next(override_get_db())
    today = date.today()
    
    financial_data = FinancialData(
        date=today,
        period_type=PeriodType.DAILY,
        category=FinancialCategory.REVENUE,
        amount=Decimal("50000.00"),
    )
    db.add(financial_data)
    db.commit()
    db.close()
    
    # 查询数据
    response = client.get(f"/finance/data?start_date={today.isoformat()}")
    
    assert response.status_code == 200
    results = response.json()
    assert len(results) > 0
    assert results[0]["category"] == "revenue"


def test_get_finance_dashboard_monthly():
    """测试月度财务看板"""
    # 创建月度数据
    db = next(override_get_db())
    today = date.today()
    month_start = today.replace(day=1)
    
    # 创建多天的数据
    for i in range(5):
        data_date = month_start + timedelta(days=i)
        revenue = FinancialData(
            date=data_date,
            period_type=PeriodType.DAILY,
            category=FinancialCategory.REVENUE,
            amount=Decimal("20000.00"),
        )
        db.add(revenue)
    
    db.commit()
    db.close()
    
    # 获取月度看板
    response = client.get("/finance/dashboard?period_type=monthly")
    
    assert response.status_code == 200
    result = response.json()
    assert result["period_type"] == "monthly"
    assert result["revenue"] >= 100000.0  # 5天 × 20000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

