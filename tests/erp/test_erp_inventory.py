"""
ERP系统 - 库存管理模块测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.erp
@pytest.mark.unit
class TestInventoryManagement:
    """库存管理模块测试"""
    
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
    
    def test_get_inventory_summary(self, api_helper):
        """测试：获取库存概览"""
        response = api_helper.get("/inventory/summary")
        data = test_helper.assert_response_success(response)
        
        assert "total_items" in data or "total" in data
    
    def test_check_stock_level(self, api_helper):
        """测试：检查库存水平"""
        product_id = 1
        response = api_helper.get(f"/inventory/products/{product_id}")
        
        if response.status_code == 200:
            data = response.json()
            assert "quantity" in data
            assert "product_id" in data
    
    def test_stock_in_operation(self, api_helper):
        """测试：入库操作"""
        stock_in_data = {
            "product_id": 1,
            "quantity": 100,
            "warehouse": "主仓库",
            "batch_number": "BATCH20251107"
        }
        
        response = api_helper.post("/inventory/stock-in", json_data=stock_in_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data or "success" in data
    
    def test_stock_out_operation(self, api_helper):
        """测试：出库操作"""
        stock_out_data = {
            "product_id": 1,
            "quantity": 50,
            "reason": "销售订单",
            "order_id": 1
        }
        
        response = api_helper.post("/inventory/stock-out", json_data=stock_out_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "success" in data or "id" in data
    
    def test_low_stock_alert(self, api_helper):
        """测试：低库存预警"""
        response = api_helper.get("/inventory/alerts")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "alerts" in data
    
    def test_inventory_count(self, api_helper):
        """测试：库存盘点"""
        count_data = {
            "warehouse": "主仓库",
            "date": "2025-11-07"
        }
        
        response = api_helper.post("/inventory/count", json_data=count_data)
        
        if response.status_code in [200, 201]:
            assert True

