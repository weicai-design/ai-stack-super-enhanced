#!/usr/bin/env python3
"""
简化的订单管理与项目管理模块集成测试
暂时禁用复杂装饰器以排除日志配置冲突
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from datetime import datetime, timedelta
from mock_database import MockSession, MockOrder, MockCustomer, MockProject

# 导入模块时禁用复杂装饰器
import modules.order.order_manager as order_module
import modules.project.project_manager as project_module

# 简化装饰器 - 直接返回原函数
def simple_decorator(func):
    return func

# 替换复杂装饰器
# 订单管理器中没有ErrorHandlingStrategies，只替换其他装饰器
order_module.circuit_breaker = simple_decorator
order_module.rate_limit = simple_decorator
if hasattr(order_module, 'audit_decorators'):
    order_module.audit_decorators.order_create = simple_decorator

project_module.circuit_breaker = simple_decorator
project_module.rate_limit = simple_decorator
if hasattr(project_module, 'ErrorHandlingStrategies'):
    project_module.ErrorHandlingStrategies.business_logic = simple_decorator
if hasattr(project_module, 'audit_decorators'):
    project_module.audit_decorators.project_create = simple_decorator
if hasattr(project_module, 'monitor_project_creation'):
    project_module.monitor_project_creation = simple_decorator

from modules.order.order_manager import OrderManager
from modules.project.project_manager import ProjectManager

class SimpleIntegrationTest:
    def __init__(self):
        self.test_results = []
        # 创建模拟数据库会话
        self.db_session = MockSession()
        # 添加模拟客户数据
        self._setup_mock_data()
        # 创建订单管理器和项目管理器实例
        self.order_manager = OrderManager(self.db_session)
        self.project_manager = ProjectManager()
    
    def _setup_mock_data(self):
        """设置模拟数据"""
        # 添加模拟客户
        customer = MockCustomer(
            id=1,
            name="测试客户",
            code="TEST-CUST-001",
            category="企业客户",
            contact_person="张经理",
            contact_phone="13800138000",
            contact_email="test@example.com",
            address="北京市朝阳区测试地址"
        )
        self.db_session.add(customer)
    
    def log_test_result(self, test_name, success, message=""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {message}")
    
    def test_basic_order_creation(self):
        """测试基础订单创建"""
        try:
            # 创建测试订单数据
            order_data = {
                "customer_id": 1,
                "order_number": "SIMPLE-TEST-001",
                "order_date": datetime.now().isoformat(),
                "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "total_amount": 500.0,
                "order_type": "短期",
                "status": "待确认",
                "items": [
                    {
                        "product_name": "简单测试产品",
                        "product_code": "SIMPLE-PRODUCT-001",
                        "quantity": 5,
                        "unit_price": 100.0,
                        "total_price": 500.0
                    }
                ]
            }
            
            order_result = self.order_manager.create_order(order_data)
            
            if not order_result["success"]:
                self.log_test_result("基础订单创建", False, f"订单创建失败: {order_result.get('error', '未知错误')}")
                return False
            
            # 验证返回结果
            order = order_result["order"]
            required_fields = ["order_id", "order_number", "total_amount", "status"]
            
            for field in required_fields:
                if field not in order:
                    self.log_test_result("基础订单创建", False, f"缺少字段: {field}")
                    return False
            
            self.log_test_result("基础订单创建", True, f"订单创建成功: {order['order_number']}")
            return True
            
        except Exception as e:
            self.log_test_result("基础订单创建", False, f"异常: {str(e)}")
            return False
    
    def test_basic_project_creation(self):
        """测试基础项目创建"""
        try:
            # 创建项目数据
            project_data = {
                "name": "简单测试项目",
                "code": "SIMPLE-PROJ-001",  # 添加必需的code字段
                "description": "这是一个简单的测试项目",
                "start_date": datetime.now().isoformat(),
                "estimated_completion_date": (datetime.now() + timedelta(days=20)).isoformat(),
                "budget": 1000.0,
                "priority": "medium"
            }
            
            project_result = self.project_manager.create_project(project_data)
            
            if not project_result["success"]:
                self.log_test_result("基础项目创建", False, f"项目创建失败: {project_result.get('error', '未知错误')}")
                return False
            
            # 验证返回结果
            project = project_result["project"]
            required_fields = ["project_id", "name", "budget", "status"]
            
            for field in required_fields:
                if field not in project:
                    self.log_test_result("基础项目创建", False, f"缺少字段: {field}")
                    return False
            
            self.log_test_result("基础项目创建", True, f"项目创建成功: {project['name']}")
            return True
            
        except Exception as e:
            self.log_test_result("基础项目创建", False, f"异常: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有简化测试"""
        print("🚀 开始简化集成测试（禁用复杂装饰器）")
        print("=" * 60)
        
        tests = [
            self.test_basic_order_creation,
            self.test_basic_project_creation
        ]
        
        for test in tests:
            test()
        
        print("=" * 60)
        
        # 统计测试结果
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"📊 测试结果统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过数: {passed_tests}")
        print(f"   失败数: {failed_tests}")
        print(f"   成功率: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 简化测试通过！基本功能正常")
        else:
            print("⚠️  简化测试存在问题，需要进一步排查")
        
        return self.test_results

if __name__ == "__main__":
    test_suite = SimpleIntegrationTest()
    results = test_suite.run_all_tests()