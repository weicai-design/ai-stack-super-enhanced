"""
ERP系统 - 客户管理模块测试
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.erp
@pytest.mark.unit
class TestCustomerManagement:
    """客户管理模块测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        """创建测试客户端"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management")
            from api.main import app
            return TestClient(app)
        except:
            pytest.skip("ERP应用未启动")
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client, base_url="/api")
    
    def test_create_customer(self, api_helper, sample_customer):
        """测试：创建客户"""
        response = api_helper.post("/customers", json_data=sample_customer)
        data = test_helper.assert_response_success(response, 201)
        
        assert "id" in data
        assert data["name"] == sample_customer["name"]
        assert data["contact"] == sample_customer["contact"]
    
    def test_get_customer(self, api_helper):
        """测试：获取客户信息"""
        customer_id = 1
        response = api_helper.get(f"/customers/{customer_id}")
        data = test_helper.assert_response_success(response)
        
        assert data["id"] == customer_id
        assert "name" in data
    
    def test_list_customers(self, api_helper):
        """测试：列出所有客户"""
        response = api_helper.get("/customers")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    def test_update_customer(self, api_helper):
        """测试：更新客户信息"""
        customer_id = 1
        update_data = {
            "phone": "13900139000",
            "level": "SVIP"
        }
        
        response = api_helper.put(f"/customers/{customer_id}", json_data=update_data)
        data = test_helper.assert_response_success(response)
        
        assert data["phone"] == update_data["phone"]
    
    def test_delete_customer(self, api_helper):
        """测试：删除客户"""
        customer_id = 999
        response = api_helper.delete(f"/customers/{customer_id}")
        # 可能返回204或404
        assert response.status_code in [204, 404]
    
    @pytest.mark.parametrize("level", ["VIP", "SVIP", "普通"])
    def test_filter_customers_by_level(self, api_helper, level):
        """测试：按级别筛选客户"""
        response = api_helper.get(f"/customers?level={level}")
        data = test_helper.assert_response_success(response)
        
        if isinstance(data, list):
            assert all(c.get("level") == level for c in data)
    
    def test_search_customers(self, api_helper):
        """测试：搜索客户"""
        response = api_helper.get("/customers/search?q=测试")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    def test_customer_statistics(self, api_helper):
        """测试：客户统计"""
        response = api_helper.get("/customers/statistics")
        data = test_helper.assert_response_success(response)
        
        assert "total" in data
        assert "by_level" in data

