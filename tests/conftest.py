"""
Pytest配置文件
提供全局fixtures和测试工具
"""

import pytest
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ==================== 基础Fixtures ====================

@pytest.fixture(scope="session")
def project_root_path():
    """项目根目录路径"""
    return project_root


@pytest.fixture(scope="session")
def test_data_dir(project_root_path):
    """测试数据目录"""
    test_data = project_root_path / "tests" / "test_data"
    test_data.mkdir(exist_ok=True)
    return test_data


@pytest.fixture
def temp_dir(tmp_path):
    """临时测试目录"""
    return tmp_path


# ==================== API测试Fixtures ====================

@pytest.fixture
def api_client():
    """API测试客户端"""
    from fastapi.testclient import TestClient
    # 这里将在具体测试中导入实际的app
    return TestClient


@pytest.fixture
def api_headers():
    """API请求头"""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


@pytest.fixture
def api_key():
    """测试API Key"""
    return "test_api_key_12345"


# ==================== 数据库Fixtures ====================

@pytest.fixture(scope="function")
def db_session():
    """数据库会话（每个测试函数独立）"""
    # 这里将在具体测试中实现数据库连接
    pass


@pytest.fixture(scope="function")
def clean_db(db_session):
    """清空数据库"""
    # 在测试前清空，测试后恢复
    yield
    # 清理逻辑


# ==================== Mock数据Fixtures ====================

@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        "user_id": "test_user_001",
        "username": "testuser",
        "email": "test@example.com",
        "role": "admin"
    }


@pytest.fixture
def sample_document():
    """示例文档数据"""
    return {
        "id": "doc_001",
        "title": "测试文档",
        "content": "这是一个测试文档的内容",
        "metadata": {
            "author": "测试用户",
            "created_at": "2025-11-07T10:00:00"
        }
    }


@pytest.fixture
def sample_customer():
    """示例客户数据（ERP）"""
    return {
        "name": "测试客户",
        "contact": "张三",
        "phone": "13800138000",
        "email": "customer@test.com",
        "address": "测试地址123号",
        "level": "VIP"
    }


@pytest.fixture
def sample_order():
    """示例订单数据（ERP）"""
    return {
        "order_number": "ORD20251107001",
        "customer_id": 1,
        "product": "测试产品",
        "quantity": 100,
        "unit_price": 99.99,
        "total_price": 9999.00,
        "status": "pending"
    }


# ==================== 环境变量Fixtures ====================

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """设置测试环境变量（自动应用到所有测试）"""
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("DEBUG", "1")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///test.db")
    

# ==================== 性能测试Fixtures ====================

@pytest.fixture
def timer():
    """计时器fixture"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# ==================== 日志Fixtures ====================

@pytest.fixture(autouse=True)
def setup_test_logging(caplog):
    """设置测试日志级别"""
    import logging
    caplog.set_level(logging.DEBUG)


# ==================== Pytest钩子 ====================

def pytest_configure(config):
    """Pytest配置钩子"""
    # 设置测试标记
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    for item in items:
        # 自动添加标记
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)


# ==================== 测试报告 ====================

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告"""
    outcome = yield
    report = outcome.get_result()
    
    # 添加额外的测试信息
    if report.when == "call":
        # 可以在这里添加自定义报告信息
        pass
