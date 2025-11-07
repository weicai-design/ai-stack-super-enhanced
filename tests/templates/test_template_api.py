"""
API测试用例模板
复制此文件并修改为实际的测试
"""

import pytest
from fastapi.testclient import TestClient
from tests.test_utils import test_helper, APITestHelper


# ==================== 测试类模板 ====================

class TestAPITemplate:
    """API测试模板类
    
    使用方法：
    1. 复制此文件
    2. 修改类名和测试名称
    3. 实现具体的测试逻辑
    """
    
    @pytest.fixture(scope="class")
    def client(self):
        """创建测试客户端"""
        # TODO: 导入实际的FastAPI应用
        # from your_module import app
        # return TestClient(app)
        pass
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        """创建API测试辅助对象"""
        return APITestHelper(client, base_url="/api")
    
    # ==================== 健康检查测试 ====================
    
    @pytest.mark.fast
    @pytest.mark.smoke
    def test_health_check(self, api_helper):
        """测试：健康检查端点"""
        response = api_helper.get("/health")
        data = test_helper.assert_response_success(response)
        
        assert "status" in data
        assert data["status"] == "ok"
    
    # ==================== CRUD操作测试 ====================
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_create_resource(self, api_helper):
        """测试：创建资源"""
        # 准备测试数据
        test_data = {
            "name": "测试资源",
            "description": "这是一个测试资源"
        }
        
        # 发送请求
        response = api_helper.post("/resources", json_data=test_data)
        
        # 验证响应
        data = test_helper.assert_response_success(response, 201)
        assert "id" in data
        assert data["name"] == test_data["name"]
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_resource(self, api_helper):
        """测试：获取资源"""
        resource_id = 1
        
        response = api_helper.get(f"/resources/{resource_id}")
        data = test_helper.assert_response_success(response)
        
        assert data["id"] == resource_id
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_update_resource(self, api_helper):
        """测试：更新资源"""
        resource_id = 1
        update_data = {
            "name": "更新后的名称"
        }
        
        response = api_helper.put(f"/resources/{resource_id}", json_data=update_data)
        data = test_helper.assert_response_success(response)
        
        assert data["name"] == update_data["name"]
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_resource(self, api_helper):
        """测试：删除资源"""
        resource_id = 1
        
        response = api_helper.delete(f"/resources/{resource_id}")
        test_helper.assert_response_success(response, 204)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_list_resources(self, api_helper):
        """测试：列出资源"""
        response = api_helper.get("/resources")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list) or "items" in data
    
    # ==================== 错误处理测试 ====================
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_nonexistent_resource(self, api_helper):
        """测试：获取不存在的资源"""
        response = api_helper.get("/resources/99999")
        test_helper.assert_response_error(response, 404)
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_create_resource_invalid_data(self, api_helper):
        """测试：创建资源时数据无效"""
        invalid_data = {
            # 缺少必需字段或数据格式错误
        }
        
        response = api_helper.post("/resources", json_data=invalid_data)
        test_helper.assert_response_error(response, 422)
    
    # ==================== 权限测试 ====================
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    def test_unauthorized_access(self, client):
        """测试：未授权访问"""
        # 不提供认证信息
        response = client.get("/api/admin/resources")
        assert response.status_code == 401
    
    # ==================== 性能测试 ====================
    
    @pytest.mark.performance
    @pytest.mark.slow
    def test_api_response_time(self, api_helper, timer):
        """测试：API响应时间"""
        timer.start()
        response = api_helper.get("/resources")
        timer.stop()
        
        test_helper.assert_response_success(response)
        assert timer.elapsed < 1.0, f"响应时间过长: {timer.elapsed}s"
    
    # ==================== 并发测试 ====================
    
    @pytest.mark.integration
    @pytest.mark.slow
    def test_concurrent_requests(self, api_helper):
        """测试：并发请求"""
        import concurrent.futures
        
        def make_request():
            response = api_helper.get("/resources")
            return response.status_code == 200
        
        # 并发10个请求
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 所有请求都应成功
        assert all(results), "部分并发请求失败"


# ==================== 参数化测试示例 ====================

class TestParameterizedAPI:
    """参数化测试示例"""
    
    @pytest.mark.parametrize("input_data,expected", [
        ({"name": "test1"}, 201),
        ({"name": "test2"}, 201),
        ({}, 422),  # 缺少必需字段
    ])
    def test_create_with_various_inputs(self, client, input_data, expected):
        """测试：使用各种输入创建资源"""
        response = client.post("/api/resources", json=input_data)
        assert response.status_code == expected

