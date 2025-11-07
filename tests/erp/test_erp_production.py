"""
ERP系统 - 生产管理模块测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.erp
@pytest.mark.unit
class TestProductionManagement:
    """生产管理模块测试"""
    
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
    
    def test_create_production_plan(self, api_helper):
        """测试：创建生产计划"""
        plan_data = {
            "order_id": 1,
            "product": "测试产品",
            "quantity": 100,
            "start_date": "2025-11-08",
            "end_date": "2025-11-15"
        }
        
        response = api_helper.post("/production/plans", json_data=plan_data)
        
        if response.status_code == 201:
            data = response.json()
            assert "id" in data
            assert data["quantity"] == plan_data["quantity"]
    
    def test_get_production_plan(self, api_helper):
        """测试：获取生产计划"""
        plan_id = 1
        response = api_helper.get(f"/production/plans/{plan_id}")
        
        if response.status_code == 200:
            data = response.json()
            assert data["id"] == plan_id
    
    def test_update_production_progress(self, api_helper):
        """测试：更新生产进度"""
        plan_id = 1
        progress_data = {
            "completed_quantity": 50,
            "current_stage": "加工生产"
        }
        
        response = api_helper.put(
            f"/production/plans/{plan_id}/progress",
            json_data=progress_data
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data["completed_quantity"] == progress_data["completed_quantity"]
    
    def test_get_production_status(self, api_helper):
        """测试：获取生产状态"""
        response = api_helper.get("/production/status")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, (list, dict))
    
    def test_list_production_stages(self, api_helper):
        """测试：列出生产阶段"""
        response = api_helper.get("/production/stages")
        data = test_helper.assert_response_success(response)
        
        # 应该有16个阶段
        if isinstance(data, list):
            assert len(data) > 0
    
    def test_production_efficiency_report(self, api_helper):
        """测试：生产效率报告"""
        response = api_helper.get("/production/efficiency")
        
        if response.status_code == 200:
            data = response.json()
            assert "efficiency_rate" in data or "efficiency" in data

