"""
测试工具函数
提供测试中常用的辅助函数
"""

import json
import time
from typing import Any, Dict, List, Optional
from pathlib import Path


class TestHelper:
    """测试辅助类"""
    
    @staticmethod
    def load_test_data(filename: str) -> Dict:
        """加载测试数据文件"""
        test_data_dir = Path(__file__).parent / "test_data"
        file_path = test_data_dir / filename
        
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    @staticmethod
    def save_test_data(filename: str, data: Dict):
        """保存测试数据到文件"""
        test_data_dir = Path(__file__).parent / "test_data"
        test_data_dir.mkdir(exist_ok=True)
        file_path = test_data_dir / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def assert_response_success(response, status_code: int = 200):
        """断言API响应成功"""
        assert response.status_code == status_code, \
            f"期望状态码 {status_code}，实际 {response.status_code}"
        
        data = response.json()
        assert "error" not in data or data["error"] is None, \
            f"响应包含错误: {data.get('error')}"
        
        return data
    
    @staticmethod
    def assert_response_error(response, status_code: int = 400):
        """断言API响应错误"""
        assert response.status_code == status_code, \
            f"期望状态码 {status_code}，实际 {response.status_code}"
        
        data = response.json()
        assert "error" in data, "错误响应应包含error字段"
        
        return data
    
    @staticmethod
    def assert_dict_contains(actual: Dict, expected: Dict):
        """断言字典包含期望的键值对"""
        for key, value in expected.items():
            assert key in actual, f"缺少键: {key}"
            assert actual[key] == value, \
                f"键 {key} 的值不匹配。期望: {value}, 实际: {actual[key]}"
    
    @staticmethod
    def assert_list_contains(actual: List, expected_item: Any):
        """断言列表包含期望的元素"""
        assert expected_item in actual, \
            f"列表中不包含期望元素: {expected_item}"
    
    @staticmethod
    def wait_for_condition(
        condition_func,
        timeout: int = 10,
        interval: float = 0.5,
        error_message: str = "条件未满足"
    ):
        """等待条件满足"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if condition_func():
                return True
            time.sleep(interval)
        
        raise TimeoutError(error_message)
    
    @staticmethod
    def create_mock_response(
        status_code: int = 200,
        data: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """创建Mock响应对象"""
        class MockResponse:
            def __init__(self, status_code, data, error):
                self.status_code = status_code
                self._data = data or {}
                if error:
                    self._data["error"] = error
            
            def json(self):
                return self._data
        
        return MockResponse(status_code, data, error)


class APITestHelper:
    """API测试辅助类"""
    
    def __init__(self, client, base_url: str = ""):
        self.client = client
        self.base_url = base_url
    
    def get(self, endpoint: str, **kwargs):
        """GET请求"""
        url = f"{self.base_url}{endpoint}"
        return self.client.get(url, **kwargs)
    
    def post(self, endpoint: str, json_data: Dict = None, **kwargs):
        """POST请求"""
        url = f"{self.base_url}{endpoint}"
        return self.client.post(url, json=json_data, **kwargs)
    
    def put(self, endpoint: str, json_data: Dict = None, **kwargs):
        """PUT请求"""
        url = f"{self.base_url}{endpoint}"
        return self.client.put(url, json=json_data, **kwargs)
    
    def delete(self, endpoint: str, **kwargs):
        """DELETE请求"""
        url = f"{self.base_url}{endpoint}"
        return self.client.delete(url, **kwargs)
    
    def assert_endpoint_accessible(self, endpoint: str, method: str = "GET"):
        """断言端点可访问"""
        if method == "GET":
            response = self.get(endpoint)
        elif method == "POST":
            response = self.post(endpoint, {})
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        assert response.status_code in [200, 201, 400, 422], \
            f"端点 {endpoint} 不可访问，状态码: {response.status_code}"


class DBTestHelper:
    """数据库测试辅助类"""
    
    @staticmethod
    def create_test_record(session, model, **kwargs):
        """创建测试记录"""
        record = model(**kwargs)
        session.add(record)
        session.commit()
        return record
    
    @staticmethod
    def delete_test_record(session, record):
        """删除测试记录"""
        session.delete(record)
        session.commit()
    
    @staticmethod
    def count_records(session, model):
        """统计记录数"""
        return session.query(model).count()


class PerformanceTestHelper:
    """性能测试辅助类"""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """测量函数执行时间"""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def assert_execution_time(func, max_time: float, *args, **kwargs):
        """断言函数执行时间不超过最大时间"""
        _, execution_time = PerformanceTestHelper.measure_execution_time(
            func, *args, **kwargs
        )
        
        assert execution_time <= max_time, \
            f"执行时间 {execution_time:.2f}s 超过最大时间 {max_time}s"
        
        return execution_time


# 便捷函数
test_helper = TestHelper()

