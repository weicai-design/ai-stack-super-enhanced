#!/usr/bin/env python3
"""
订单管理与项目管理模块集成测试
验证两个模块的协同工作能力和数据一致性
"""

import sys
import os

# 添加模块路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'modules'))

from modules.order.order_manager import OrderManager
from modules.project.project_manager import ProjectManager
from datetime import datetime, timedelta
from mock_database import MockSession, MockOrder, MockCustomer, MockProject

class IntegrationTest:
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
        
        # 添加更多模拟客户
        customer2 = MockCustomer(
            id=2,
            name="示例客户",
            code="SAMPLE-CUST-002",
            category="个人客户",
            contact_person="李女士",
            contact_phone="13900139000",
            contact_email="sample@example.com",
            address="上海市浦东新区示例地址"
        )
        self.db_session.add(customer2)
    
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
    
    def test_order_project_creation_integration(self):
        """测试订单与项目创建集成"""
        try:
            # 创建测试订单数据
            order_data = {
                "customer_id": 1,
                "order_number": "TEST-INTEGRATION-001",
                "order_date": datetime.now().isoformat(),
                "delivery_date": (datetime.now() + timedelta(days=30)).isoformat(),
                "total_amount": 1000.0,
                "order_type": "短期",
                "status": "待确认",
                "items": [
                    {
                        "product_name": "集成测试产品",
                        "product_code": "TEST-PRODUCT-001",
                        "quantity": 10,
                        "unit_price": 100.0,
                        "total_price": 1000.0
                    }
                ]
            }
            
            order_result = self.order_manager.create_order(order_data)
            
            if not order_result["success"]:
                self.log_test_result("订单创建", False, f"订单创建失败: {order_result.get('error', '未知错误')}")
                return
            
            order_id = order_result["order"]["order_id"]
            
            # 基于订单创建项目
            project_data = {
                "name": f"项目-{order_result['order']['order_number']}",
                "description": f"基于订单 {order_result['order']['order_number']} 创建的项目",
                "code": f"PROJ-{order_result['order']['order_number']}",
                "start_date": datetime.now().isoformat(),
                "estimated_completion_date": (datetime.now() + timedelta(days=25)).isoformat(),
                "budget": order_result["order"]["total_amount"],
                "priority": "high"
            }
            
            project_result = self.project_manager.create_project(project_data)
            
            if not project_result["success"]:
                self.log_test_result("项目创建", False, f"项目创建失败: {project_result.get('error', '未知错误')}")
                return
            
            project_id = project_result["project"]["project_id"]
            
            # 关联订单与项目
            integration_result = self.project_manager.integrate_with_order_management(
                project_id,
                {"orders": [order_result["order"]]}
            )
            
            if not integration_result["success"]:
                self.log_test_result("订单项目关联", False, f"关联失败: {integration_result.get('error', '未知错误')}")
                return
            
            self.log_test_result("订单项目创建集成", True, 
                               f"订单 {order_id} 与项目 {project_id} 成功关联")
            
            return order_id, project_id
            
        except Exception as e:
            self.log_test_result("订单项目创建集成", False, f"异常: {str(e)}")
    
    def test_project_milestone_tracking(self):
        """测试项目里程碑跟踪与订单状态同步"""
        try:
            # 创建测试订单和项目
            result = self.test_order_project_creation_integration()
            if not result:
                return
            
            order_id, project_id = result
            
            # 为项目添加里程碑
            milestone_data = {
                "name": "设计阶段完成",
                "description": "完成产品设计和技术方案",
                "due_date": (datetime.now() + timedelta(days=10)).isoformat(),
                "weight": 30
            }
            
            milestone_result = self.project_manager.create_milestone(project_id, milestone_data)
            
            if not milestone_result["success"]:
                self.log_test_result("里程碑创建", False, f"里程碑创建失败: {milestone_result.get('error', '未知错误')}")
                return
            
            # 完成里程碑
            complete_result = self.project_manager.complete_milestone(project_id, milestone_result["milestone"]["milestone_id"])
            
            if not complete_result["success"]:
                self.log_test_result("里程碑完成", False, f"里程碑完成失败: {complete_result.get('error', '未知错误')}")
                return
            
            # 检查项目进度
            project_info = self.project_manager._get_project(project_id)
            progress = project_info.get("progress", 0)
            
            if progress >= 30:
                self.log_test_result("项目进度跟踪", True, f"项目进度更新为 {progress}%")
            else:
                self.log_test_result("项目进度跟踪", False, f"项目进度异常: {progress}%")
            
            # 检查订单状态是否同步
            order_info = self.order_manager._get_order(order_id)
            order_status = order_info.get("status", "unknown")
            
            # 订单状态应该反映项目进度
            if progress > 0 and order_status != "pending":
                self.log_test_result("订单状态同步", True, f"订单状态已更新为 {order_status}")
            else:
                self.log_test_result("订单状态同步", False, f"订单状态未同步: {order_status}")
                
        except Exception as e:
            self.log_test_result("项目里程碑跟踪", False, f"异常: {str(e)}")
    
    def test_budget_cost_integration(self):
        """测试预算与成本集成"""
        try:
            # 创建测试订单和项目
            result = self.test_order_project_creation_integration()
            if not result:
                return
            
            order_id, project_id = result
            
            # 获取订单金额
            order_info = self.order_manager._get_order(order_id)
            order_amount = order_info.get("total_amount", 0)
            
            # 设置项目预算
            budget_data = {
                "total_budget": order_amount,
                "allocated_budget": order_amount * 0.8,
                "actual_spent": order_amount * 0.3
            }
            
            budget_result = self.project_manager.update_project_budget(project_id, budget_data)
            
            if not budget_result["success"]:
                self.log_test_result("预算设置", False, f"预算设置失败: {budget_result.get('error', '未知错误')}")
                return
            
            # 分析预算偏差
            variance_result = self.project_manager.analyze_budget_variance(project_id)
            
            if not variance_result["success"]:
                self.log_test_result("预算分析", False, f"预算分析失败: {variance_result.get('error', '未知错误')}")
                return
            
            variance = variance_result["variance_analysis"]["variance_percentage"]
            
            if abs(variance) < 50:  # 允许一定偏差
                self.log_test_result("预算成本集成", True, f"预算偏差分析正常: {variance}%")
            else:
                self.log_test_result("预算成本集成", False, f"预算偏差过大: {variance}%")
                
        except Exception as e:
            self.log_test_result("预算成本集成", False, f"异常: {str(e)}")
    
    def test_risk_management_integration(self):
        """测试风险管理集成"""
        try:
            # 创建测试订单和项目
            result = self.test_order_project_creation_integration()
            if not result:
                return
            
            order_id, project_id = result
            
            # 添加项目风险
            risk_data = {
                "description": "供应链延迟风险",
                "category": "supply_chain",
                "probability": "medium",
                "impact": "high",
                "mitigation_plan": "建立备用供应商"
            }
            
            risk_result = self.project_manager.add_project_risk(project_id, risk_data)
            
            if not risk_result["success"]:
                self.log_test_result("风险添加", False, f"风险添加失败: {risk_result.get('error', '未知错误')}")
                return
            
            # 进行风险评估
            assessment_result = self.project_manager.project_risk_assessment(project_id)
            
            if not assessment_result["success"]:
                self.log_test_result("风险评估", False, f"风险评估失败: {assessment_result.get('error', '未知错误')}")
                return
            
            risk_level = assessment_result["risk_assessment"]["overall_risk_level"]
            
            if risk_level in ["low", "medium", "high"]:
                self.log_test_result("风险管理集成", True, f"风险评估完成: {risk_level}")
            else:
                self.log_test_result("风险管理集成", False, f"风险评估异常: {risk_level}")
                
        except Exception as e:
            self.log_test_result("风险管理集成", False, f"异常: {str(e)}")
    
    def test_resource_allocation_integration(self):
        """测试资源分配集成"""
        try:
            # 创建测试订单和项目
            result = self.test_order_project_creation_integration()
            if not result:
                return
            
            order_id, project_id = result
            
            # 分配项目资源
            resources_data = {
                "resources": [
                    {
                        "type": "human",
                        "name": "项目经理",
                        "quantity": 1,
                        "cost_per_unit": 5000
                    },
                    {
                        "type": "equipment",
                        "name": "开发服务器",
                        "quantity": 2,
                        "cost_per_unit": 1000
                    }
                ]
            }
            
            resource_result = self.project_manager.allocate_project_resources(project_id, resources_data["resources"])
            
            if not resource_result["success"]:
                self.log_test_result("资源分配", False, f"资源分配失败: {resource_result.get('error', '未知错误')}")
                return
            
            # 优化资源分配
            optimization_result = self.project_manager.optimize_resource_allocation(project_id)
            
            if not optimization_result["success"]:
                self.log_test_result("资源优化", False, f"资源优化失败: {optimization_result.get('error', '未知错误')}")
                return
            
            optimization_score = optimization_result["optimization_score"]
            
            if optimization_score >= 0:
                self.log_test_result("资源分配集成", True, f"资源优化完成，得分: {optimization_score}")
            else:
                self.log_test_result("资源分配集成", False, f"资源优化异常，得分: {optimization_score}")
                
        except Exception as e:
            self.log_test_result("资源分配集成", False, f"异常: {str(e)}")
    
    def test_report_generation_integration(self):
        """测试报告生成集成"""
        try:
            # 创建测试订单和项目
            result = self.test_order_project_creation_integration()
            if not result:
                return
            
            order_id, project_id = result
            
            # 生成项目报告
            report_result = self.project_manager.generate_project_report(project_id, "comprehensive")
            
            if not report_result["success"]:
                self.log_test_result("报告生成", False, f"报告生成失败: {report_result.get('error', '未知错误')}")
                return
            
            report_data = report_result["report"]
            
            if (report_data.get("executive_summary") and 
                report_data.get("progress_analysis") and 
                report_data.get("financial_overview")):
                self.log_test_result("报告生成集成", True, "综合报告生成成功")
            else:
                self.log_test_result("报告生成集成", False, "报告内容不完整")
                
        except Exception as e:
            self.log_test_result("报告生成集成", False, f"异常: {str(e)}")
    
    def run_all_tests(self):
        """运行所有集成测试"""
        print("🚀 开始订单管理与项目管理模块集成测试")
        print("=" * 60)
        
        tests = [
            self.test_order_project_creation_integration,
            self.test_project_milestone_tracking,
            self.test_budget_cost_integration,
            self.test_risk_management_integration,
            self.test_resource_allocation_integration,
            self.test_report_generation_integration
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
            print("🎉 集成测试通过！模块集成良好")
        else:
            print("⚠️  集成测试存在一些问题，需要优化")
        
        return self.test_results

if __name__ == "__main__":
    test_suite = IntegrationTest()
    results = test_suite.run_all_tests()