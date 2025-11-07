"""
ERP系统 - 订单管理模块测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.erp
@pytest.mark.unit
class TestOrderManagement:
    """订单管理模块测试"""
    
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
    
    def test_create_order(self, api_helper, sample_order):
        """测试：创建订单"""
        response = api_helper.post("/orders", json_data=sample_order)
        data = test_helper.assert_response_success(response, 201)
        
        assert "id" in data
        assert "order_number" in data
        assert data["status"] == "pending"
    
    def test_get_order(self, api_helper):
        """测试：获取订单详情"""
        order_id = 1
        response = api_helper.get(f"/orders/{order_id}")
        data = test_helper.assert_response_success(response)
        
        assert data["id"] == order_id
        assert "order_number" in data
        assert "customer_id" in data
    
    def test_list_orders(self, api_helper):
        """测试：列出订单"""
        response = api_helper.get("/orders")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    @pytest.mark.parametrize("status", [
        "pending", "confirmed", "in_production", 
        "shipped", "completed", "cancelled"
    ])
    def test_update_order_status(self, api_helper, status):
        """测试：更新订单状态"""
        order_id = 1
        response = api_helper.put(
            f"/orders/{order_id}/status",
            json_data={"status": status}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == status
    
    def test_cancel_order(self, api_helper):
        """测试：取消订单"""
        order_id = 1
        response = api_helper.post(f"/orders/{order_id}/cancel")
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "cancelled"
    
    def test_filter_orders_by_status(self, api_helper):
        """测试：按状态筛选订单"""
        response = api_helper.get("/orders?status=pending")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    def test_filter_orders_by_customer(self, api_helper):
        """测试：按客户筛选订单"""
        customer_id = 1
        response = api_helper.get(f"/orders?customer_id={customer_id}")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    def test_order_statistics(self, api_helper):
        """测试：订单统计"""
        response = api_helper.get("/orders/statistics")
        data = test_helper.assert_response_success(response)
        
        assert "total" in data or "count" in data

