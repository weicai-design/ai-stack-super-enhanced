#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP专家模块测试脚本
测试1~4小项开发成果：质量专家、成本专家、交期专家、安全专家
"""

import asyncio
import sys
import os

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from erp_experts import (
    ERPDataConnector, QualityExpert, CostExpert, 
    DeliveryExpert, SafetyExpert, ERPDimension
)


class ERPExpertsTestSuite:
    """ERP专家测试套件"""
    
    def __init__(self):
        self.data_connector = ERPDataConnector({"test_mode": True})
        self.quality_expert = QualityExpert(self.data_connector)
        self.cost_expert = CostExpert(self.data_connector)
        self.delivery_expert = DeliveryExpert(self.data_connector)
        self.safety_expert = SafetyExpert(self.data_connector)
        self.results = {}
    
    def print_header(self, title: str):
        """打印测试标题"""
        print(f"\n{'='*60}")
        print(f"测试: {title}")
        print(f"{'='*60}")
    
    async def test_quality_expert(self):
        """测试质量专家"""
        self.print_header("质量专家测试")
        
        # 测试数据
        quality_data = {
            "defect_rate": 2.5,
            "total_produced": 10000,
            "total_defects": 250,
            "cpk": 1.45,
            "customer_ppm": 3500,
            "audit_findings": 3,
            "inspection_coverage": 85.5,
            "improvement_projects": 5,
            "historical_defects": [280, 260, 240, 230, 250],
            "defect_types": {"外观": 120, "功能": 80, "尺寸": 50}
        }
        
        try:
            # 分析质量
            analysis = await self.quality_expert.analyze_quality(
                quality_data, {"system_type": "sap", "period": "monthly"}
            )
            
            print(f"✓ 质量分析完成 - 得分: {analysis.score:.1f}")
            print(f"  置信度: {analysis.confidence}")
            print(f"  维度: {analysis.dimension}")
            
            # 测试仪表板
            dashboard = self.quality_expert.get_quality_dashboard()
            print(f"✓ 质量仪表板获取成功")
            print(f"  不良率: {dashboard['defect_rate']}%")
            print(f"  风险等级: {dashboard['risk_level']}")
            
            # 测试实时监控
            monitoring_started = await self.quality_expert.start_real_time_monitoring()
            print(f"✓ 实时监控: {'启动成功' if monitoring_started else '启动失败'}")
            
            # 测试参数优化
            optimization = await self.quality_expert.optimize_quality_parameters(quality_data)
            print(f"✓ 参数优化完成 - 置信度: {optimization['confidence']}")
            
            self.results["quality_expert"] = {
                "status": "通过",
                "score": analysis.score,
                "confidence": analysis.confidence,
                "dashboard": dashboard is not None,
                "monitoring": monitoring_started,
                "optimization": optimization is not None
            }
            
        except Exception as e:
            print(f"✗ 质量专家测试失败: {e}")
            self.results["quality_expert"] = {"status": "失败", "error": str(e)}
    
    async def test_cost_expert(self):
        """测试成本专家"""
        self.print_header("成本专家测试")
        
        # 测试数据
        cost_data = {
            "material_cost": 500000,
            "labor_cost": 200000,
            "overhead_cost": 100000,
            "total_spend": 800000,
            "savings_pipeline": 50000,
            "realized_savings": 25000,
            "spend_under_management": 600000,
            "supplier_concentration": 45.2,
            "avg_payment_terms": 45,
            "historical_costs": [850000, 820000, 800000, 780000, 800000],
            "cost_breakdown": {"原材料": 500000, "人工": 200000, "制造费用": 100000}
        }
        
        try:
            # 分析成本
            analysis = await self.cost_expert.analyze_cost(
                cost_data, {"system_type": "oracle", "period": "monthly"}
            )
            
            print(f"✓ 成本分析完成 - 得分: {analysis.score:.1f}")
            print(f"  置信度: {analysis.confidence}")
            print(f"  维度: {analysis.dimension}")
            
            # 测试仪表板
            dashboard = self.cost_expert.get_cost_dashboard()
            print(f"✓ 成本仪表板获取成功")
            print(f"  总成本: {dashboard['overview']['total_cost']}")
            print(f"  成本结构: {dashboard['structure_analysis']}")
            
            # 测试实时监控
            monitoring_started = await self.cost_expert.start_real_time_monitoring()
            print(f"✓ 实时监控: {'启动成功' if monitoring_started else '启动失败'}")
            
            # 测试参数优化
            optimization = await self.cost_expert.optimize_cost_parameters(cost_data)
            print(f"✓ 参数优化完成 - 置信度: {optimization['confidence']}")
            
            self.results["cost_expert"] = {
                "status": "通过",
                "score": analysis.score,
                "confidence": analysis.confidence,
                "dashboard": dashboard is not None,
                "monitoring": monitoring_started,
                "optimization": optimization is not None
            }
            
        except Exception as e:
            print(f"✗ 成本专家测试失败: {e}")
            self.results["cost_expert"] = {"status": "失败", "error": str(e)}
    
    async def test_delivery_expert(self):
        """测试交期专家"""
        self.print_header("交期专家测试")
        
        # 测试数据
        delivery_data = {
            "on_time_delivery": 920,
            "total_orders": 1000,
            "avg_delivery_days": 15.2,
            "supply_risk_index": 0.3,
            "backup_capacity": 0.2,
            "expedite_dependency": 0.15,
            "historical_otd": [890, 900, 910, 920, 920],
            "delivery_breakdown": {"准时": 920, "延迟": 80}
        }
        
        try:
            # 分析交期
            analysis = await self.delivery_expert.analyze_delivery(
                delivery_data, {"system_type": "sap", "period": "monthly"}
            )
            
            print(f"✓ 交期分析完成 - 得分: {analysis.score:.1f}")
            print(f"  置信度: {analysis.confidence}")
            print(f"  维度: {analysis.dimension}")
            
            # 测试仪表板
            dashboard = self.delivery_expert.get_delivery_dashboard()
            print(f"✓ 交期仪表板获取成功")
            print(f"  交期达成率: {dashboard['overview']['delivery_rate']:.1f}%")
            print(f"  平均交期: {dashboard['overview']['avg_delivery_days']}天")
            
            # 测试实时监控
            monitoring_started = await self.delivery_expert.start_real_time_monitoring()
            print(f"✓ 实时监控: {'启动成功' if monitoring_started else '启动失败'}")
            
            # 测试参数优化
            optimization = await self.delivery_expert.optimize_delivery_parameters(delivery_data)
            print(f"✓ 参数优化完成 - 置信度: {optimization['confidence']}")
            
            self.results["delivery_expert"] = {
                "status": "通过",
                "score": analysis.score,
                "confidence": analysis.confidence,
                "dashboard": dashboard is not None,
                "monitoring": monitoring_started,
                "optimization": optimization is not None
            }
            
        except Exception as e:
            print(f"✗ 交期专家测试失败: {e}")
            self.results["delivery_expert"] = {"status": "失败", "error": str(e)}
    
    async def test_safety_expert(self):
        """测试安全专家"""
        self.print_header("安全专家测试")
        
        # 测试数据
        safety_data = {
            "accidents": 2,
            "total_work_hours": 200000,
            "severe_accidents": 0,
            "hazards": 8,
            "resolved_hazards": 7,
            "pending_hazards": 1,
            "audit_score": 88.5,
            "training_completion": 92.0,
            "ppe_compliance": 95.5,
            "regulatory_findings": 1,
            "emergency_drills": 4,
            "drill_participation": 85.0,
            "emergency_equipment": 92.0,
            "historical_accidents": [3, 2, 1, 2, 2],
            "historical_hazards": [10, 9, 8, 8, 8],
            "hazard_types": {"电气": 3, "机械": 2, "化学品": 2, "其他": 1}
        }
        
        try:
            # 分析安全
            analysis = await self.safety_expert.analyze_safety(
                safety_data, {"system_type": "oracle", "period": "monthly"}
            )
            
            print(f"✓ 安全分析完成 - 得分: {analysis.score:.1f}")
            print(f"  置信度: {analysis.confidence}")
            print(f"  维度: {analysis.dimension}")
            
            # 测试仪表板
            dashboard = self.safety_expert.get_safety_dashboard()
            print(f"✓ 安全仪表板获取成功")
            print(f"  事故率: {dashboard['overview']['accident_rate']:.2f}")
            print(f"  隐患数量: {dashboard['overview']['hazards_count']}")
            
            # 测试实时监控
            monitoring_started = await self.safety_expert.start_real_time_monitoring()
            print(f"✓ 实时监控: {'启动成功' if monitoring_started else '启动失败'}")
            
            # 测试参数优化
            optimization = await self.safety_expert.optimize_safety_parameters(safety_data)
            print(f"✓ 参数优化完成 - 置信度: {optimization['confidence']}")
            
            self.results["safety_expert"] = {
                "status": "通过",
                "score": analysis.score,
                "confidence": analysis.confidence,
                "dashboard": dashboard is not None,
                "monitoring": monitoring_started,
                "optimization": optimization is not None
            }
            
        except Exception as e:
            print(f"✗ 安全专家测试失败: {e}")
            self.results["safety_expert"] = {"status": "失败", "error": str(e)}
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("开始ERP专家模块测试...")
        print(f"测试时间: {asyncio.get_event_loop().time()}")
        
        # 运行所有测试
        await self.test_quality_expert()
        await self.test_cost_expert()
        await self.test_delivery_expert()
        await self.test_safety_expert()
        
        # 生成测试报告
        self.generate_test_report()
    
    def generate_test_report(self):
        """生成测试报告"""
        print(f"\n{'='*60}")
        print("测试报告")
        print(f"{'='*60}")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get("status") == "通过")
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"失败数: {failed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        print(f"\n详细结果:")
        for expert_name, result in self.results.items():
            status = result.get("status", "未知")
            if status == "通过":
                print(f"  ✓ {expert_name}: {status}")
                print(f"    得分: {result.get('score', 'N/A'):.1f}")
                print(f"    置信度: {result.get('confidence', 'N/A')}")
            else:
                print(f"  ✗ {expert_name}: {status}")
                if "error" in result:
                    print(f"    错误: {result['error']}")
        
        if failed_tests == 0:
            print(f"\n🎉 所有测试通过！ERP专家模块1~4小项开发完成！")
        else:
            print(f"\n⚠️  有{failed_tests}个测试失败，请检查代码实现。")


async def main():
    """主函数"""
    test_suite = ERPExpertsTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())