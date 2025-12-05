"""
订单管理集成测试

测试范围：
1. 订单API端点安全验证
2. 订单管理器业务逻辑
3. 安全防护功能验证
4. 集成功能测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 添加Super Agent Main Interface路径到sys.path
super_agent_path = os.path.join(project_root, "🚀 Super Agent Main Interface")
sys.path.insert(0, super_agent_path)

# 添加ERP Business Management路径到sys.path
erp_path = os.path.join(project_root, "💼 Intelligent ERP & Business Management")
sys.path.insert(0, erp_path)

# 确保正确的core模块被导入（Super Agent Main Interface的core）
# 首先移除ERP Business Management的core路径（如果有）
core_paths_to_remove = []
for path in sys.path:
    if "💼 Intelligent ERP & Business Management" in path and "core" in path:
        core_paths_to_remove.append(path)

for path in core_paths_to_remove:
    sys.path.remove(path)

# 然后添加Super Agent Main Interface的core路径
super_agent_core_path = os.path.join(super_agent_path, "core")
if super_agent_core_path not in sys.path:
    sys.path.insert(0, super_agent_core_path)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# 使用绝对导入避免pytest模块解析问题
import sys
import os
# 动态添加api路径到sys.path
api_path = os.path.join(super_agent_path, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)

from orders_api import router, OrderCreateRequest, OrderStatusUpdateRequest
from modules.order.order_manager import OrderManager
from core.database_models import Base, Order, Customer, OrderItem


class TestOrderIntegration:
    """订单管理集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup_database(self):
        """设置测试数据库"""
        # 创建内存数据库
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)
        
        # 创建会话
        SessionLocal = sessionmaker(autocreate=False, autocommit=False, autoflush=False, bind=self.engine)
        self.db_session = SessionLocal()
        
        # 创建测试客户
        self.test_customer = Customer(
            name="测试客户",
            code="TEST001",
            category="VIP",
            contact_person="张三",
            contact_phone="13800138000",
            contact_email="test@example.com",
            address="测试地址"
        )
        self.db_session.add(self.test_customer)
        self.db_session.commit()
        
        yield
        
        # 清理
        self.db_session.close()
        Base.metadata.drop_all(self.engine)
    
    @pytest.fixture
    def order_manager(self):
        """创建订单管理器实例"""
        return OrderManager(self.db_session)
    
    @pytest.fixture
    def test_client(self):
        """创建测试客户端"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        return TestClient(app)
    
    def test_create_order_success(self, order_manager):
        """测试成功创建订单"""
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-001",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": [
                {
                    "name": "测试产品A",
                    "quantity": 10,
                    "unit_price": 1000.0,
                    "code": "PROD-A-001"
                }
            ]
        }
        
        result = order_manager.create_order(order_data)
        
        assert result["success"] == True
        assert "order_id" in result
        assert result["order"]["order_number"] == "TEST-ORDER-001"
    
    def test_create_order_with_sql_injection_attempt(self, order_manager):
        """测试SQL注入攻击防护"""
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST'; DROP TABLE orders; --",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        result = order_manager.create_order(order_data)
        
        # 应该成功创建，但订单编号会被清理
        assert result["success"] == True
        assert "DROP" not in result["order"]["order_number"]
    
    def test_create_order_with_xss_attempt(self, order_manager):
        """测试XSS攻击防护"""
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-XSS",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "<script>alert('xss')</script>",
            "status": "待确认",
            "items": []
        }
        
        result = order_manager.create_order(order_data)
        
        # 应该成功创建，但订单类型会被清理
        assert result["success"] == True
        assert "<script>" not in result["order"]["order_type"]
    
    def test_create_order_invalid_customer_id(self, order_manager):
        """测试无效客户ID"""
        order_data = {
            "customer_id": -1,  # 无效ID
            "order_number": "TEST-ORDER-001",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        result = order_manager.create_order(order_data)
        
        assert result["success"] == False
        assert "客户ID格式不正确" in result["error"]
    
    def test_list_orders_with_filters(self, order_manager):
        """测试订单列表查询与筛选"""
        # 先创建几个测试订单
        order_data1 = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-001",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        order_data2 = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-002",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=60),
            "order_amount": 20000.0,
            "order_type": "长期",
            "status": "已确认",
            "items": []
        }
        
        order_manager.create_order(order_data1)
        order_manager.create_order(order_data2)
        
        # 测试按状态筛选
        result = order_manager.list_orders(status="待确认")
        assert result["success"] == True
        assert len(result["orders"]) == 1
        assert result["orders"][0]["status"] == "待确认"
        
        # 测试按客户筛选
        result = order_manager.list_orders(customer_id=self.test_customer.id)
        assert result["success"] == True
        assert len(result["orders"]) == 2
    
    def test_update_order_status(self, order_manager):
        """测试订单状态更新"""
        # 创建测试订单
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-001",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        create_result = order_manager.create_order(order_data)
        order_id = create_result["order_id"]
        
        # 更新状态
        update_result = order_manager.update_order_status(
            order_id=order_id,
            new_status="已确认",
            note="测试状态更新"
        )
        
        assert update_result["success"] == True
        assert update_result["order"]["status"] == "已确认"
    
    def test_update_order_status_invalid_id(self, order_manager):
        """测试无效订单ID的状态更新"""
        result = order_manager.update_order_status(
            order_id=999999,  # 不存在的ID
            new_status="已确认",
            note="测试"
        )
        
        assert result["success"] == False
        assert "订单不存在" in result["error"]
    
    def test_update_order_status_invalid_status(self, order_manager):
        """测试无效状态更新"""
        # 创建测试订单
        order_data = {
            "customer_id": self.test_customer.id,
            "order_number": "TEST-ORDER-001",
            "order_date": datetime.now(),
            "delivery_date": datetime.now() + timedelta(days=30),
            "order_amount": 10000.0,
            "order_type": "短期",
            "status": "待确认",
            "items": []
        }
        
        create_result = order_manager.create_order(order_data)
        order_id = create_result["order_id"]
        
        # 尝试更新为无效状态
        result = order_manager.update_order_status(
            order_id=order_id,
            new_status="无效状态",
            note="测试"
        )
        
        assert result["success"] == False
        assert "订单状态格式不正确" in result["error"]
    
    def test_analyze_order_trends(self, order_manager):
        """测试订单趋势分析"""
        # 创建不同状态的测试订单
        for i in range(5):
            order_data = {
                "customer_id": self.test_customer.id,
                "order_number": f"TEST-ORDER-{i:03d}",
                "order_date": datetime.now() - timedelta(days=i),
                "delivery_date": datetime.now() + timedelta(days=30 - i),
                "order_amount": 10000.0 + i * 1000,
                "order_type": "短期" if i % 2 == 0 else "长期",
                "status": ["待确认", "已确认", "生产中", "已完成", "已取消"][i % 5],
                "items": []
            }
            order_manager.create_order(order_data)
        
        result = order_manager.analyze_order_trends()
        
        assert result["success"] == True
        assert "analysis" in result
        assert isinstance(result["analysis"], list)
    
    def test_api_create_order_endpoint(self, test_client):
        """测试API创建订单端点"""
        order_data = {
            "customer": "测试客户",
            "industry": "制造业",
            "value": 10000.0,
            "currency": "CNY",
            "priority": "normal",
            "status": "confirming",
            "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "items": [
                {
                    "name": "测试产品",
                    "quantity": 10,
                    "unit_price": 1000.0,
                    "code": "TEST-PROD-001"
                }
            ]
        }
        
        response = test_client.post("/api/orders/create", json=order_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "order_id" in data
    
    def test_api_create_order_sql_injection_protection(self, test_client):
        """测试API端点的SQL注入防护"""
        order_data = {
            "customer": "测试'; DROP TABLE customers; --",
            "industry": "制造业",
            "value": 10000.0,
            "currency": "CNY",
            "priority": "normal",
            "status": "confirming",
            "items": [
                {
                    "name": "测试产品",
                    "quantity": 10,
                    "unit_price": 1000.0,
                    "code": "TEST-PROD-001"
                }
            ]
        }
        
        response = test_client.post("/api/orders/create", json=order_data)
        
        # 应该成功创建，但客户名称会被清理
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "DROP" not in data.get("order", {}).get("customer", "")
    
    def test_api_list_orders_endpoint(self, test_client):
        """测试API订单列表端点"""
        response = test_client.get("/api/orders/list")
        
        assert response.status_code == 200
        data = response.json()
        assert "orders" in data
        assert isinstance(data["orders"], list)
    
    def test_api_get_order_detail_endpoint(self, test_client):
        """测试API获取订单详情端点"""
        # 先创建订单
        order_data = {
            "customer": "测试客户",
            "industry": "制造业",
            "value": 10000.0,
            "currency": "CNY",
            "priority": "normal",
            "status": "confirming",
            "items": [
                {
                    "name": "测试产品",
                    "quantity": 10,
                    "unit_price": 1000.0,
                    "code": "TEST-PROD-001"
                }
            ]
        }
        
        create_response = test_client.post("/api/orders/create", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # 获取详情
        response = test_client.get(f"/api/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "order" in data
    
    def test_api_update_order_status_endpoint(self, test_client):
        """测试API更新订单状态端点"""
        # 先创建订单
        order_data = {
            "customer": "测试客户",
            "industry": "制造业",
            "value": 10000.0,
            "currency": "CNY",
            "priority": "normal",
            "status": "confirming",
            "items": [
                {
                    "name": "测试产品",
                    "quantity": 10,
                    "unit_price": 1000.0,
                    "code": "TEST-PROD-001"
                }
            ]
        }
        
        create_response = test_client.post("/api/orders/create", json=order_data)
        order_id = create_response.json()["order_id"]
        
        # 更新状态
        update_data = {
            "status": "approved",
            "stage": "评估阶段",
            "risk": "无风险",
            "note": "测试状态更新"
        }
        
        response = test_client.put(f"/api/orders/{order_id}/status", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["order"]["status"] == "approved"


class TestOrderSecurity:
    """订单安全防护测试类"""
    
    def test_sql_injection_protection(self):
        """测试SQL注入防护函数"""
        from api.orders_api import _sanitize_sql_input
        
        # 测试各种SQL注入攻击
        test_cases = [
            ("SELECT * FROM orders", " FROM orders"),
            ("'; DROP TABLE users; --", ""),
            ("OR 1=1", "1=1"),
            ("UNION SELECT password", " SELECT password"),
            ("admin' OR '1'='1", "admin OR 11"),
        ]
        
        for input_str, expected_contains in test_cases:
            result = _sanitize_sql_input(input_str)
            # 确保危险关键词被移除
            for keyword in ['SELECT', 'DROP', 'UNION', 'OR']:
                assert keyword not in result.upper()
    
    def test_xss_protection(self):
        """测试XSS防护函数"""
        from api.orders_api import _sanitize_html_input
        
        # 测试各种XSS攻击
        test_cases = [
            ("<script>alert('xss')</script>", "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
            ("<img src=x onerror=alert(1)>", "&lt;img src=x onerror=alert(1)&gt;"),
            ("javascript:alert('XSS')", "javascript:alert(&#x27;XSS&#x27;)"),
        ]
        
        for input_str, expected in test_cases:
            result = _sanitize_html_input(input_str)
            assert result == expected
    
    def test_input_validation_functions(self):
        """测试输入验证函数"""
        from api.orders_api import _validate_numeric_input, _validate_string_length
        
        # 测试数值验证
        assert _validate_numeric_input("100", min_val=1, max_val=1000) == True
        assert _validate_numeric_input("-1", min_val=0) == False
        assert _validate_numeric_input("abc") == False
        
        # 测试字符串长度验证
        assert _validate_string_length("test", max_length=10) == True
        assert _validate_string_length("a" * 11, max_length=10) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])