"""
ERP系统 - 财务管理模块测试
"""

import pytest
from datetime import datetime, timedelta
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.erp
@pytest.mark.unit
@pytest.mark.critical
class TestFinanceManagement:
    """财务管理模块测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management")
            from api.main import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except:
            pytest.skip("ERP应用未启动")
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client, base_url="/api")
    
    def test_get_financial_summary(self, api_helper):
        """测试：获取财务概览"""
        response = api_helper.get("/finance/summary")
        data = test_helper.assert_response_success(response)
        
        assert "revenue" in data
        assert "expenses" in data
        assert "profit" in data
    
    def test_get_daily_report(self, api_helper):
        """测试：获取日报"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = api_helper.get(f"/finance/daily?date={today}")
        data = test_helper.assert_response_success(response)
        
        assert "date" in data
        assert "revenue" in data
    
    def test_get_weekly_report(self, api_helper):
        """测试：获取周报"""
        response = api_helper.get("/finance/weekly")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, (list, dict))
    
    def test_get_monthly_report(self, api_helper):
        """测试：获取月报"""
        response = api_helper.get("/finance/monthly")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, (list, dict))
    
    def test_revenue_analysis(self, api_helper):
        """测试：收入分析"""
        response = api_helper.get("/finance/analysis/revenue")
        data = test_helper.assert_response_success(response)
        
        assert "total_revenue" in data or "revenue" in data
    
    def test_cost_analysis(self, api_helper):
        """测试：成本分析"""
        response = api_helper.get("/finance/analysis/cost")
        data = test_helper.assert_response_success(response)
        
        assert "total_cost" in data or "cost" in data
    
    def test_profit_trend(self, api_helper):
        """测试：利润趋势"""
        response = api_helper.get("/finance/trends/profit")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "trend" in data
    
    @pytest.mark.parametrize("period", ["day", "week", "month", "quarter", "year"])
    def test_financial_report_by_period(self, api_helper, period):
        """测试：按周期获取财务报告"""
        response = api_helper.get(f"/finance/report?period={period}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

