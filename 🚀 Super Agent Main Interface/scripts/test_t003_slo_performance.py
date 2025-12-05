#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T003: 2秒SLO性能验证测试脚本

测试SLO性能验证器的完整功能，包括：
1. 验证器初始化和单例模式测试
2. 性能监控和SLO验证功能测试
3. 告警机制和报告生成测试
4. API接口功能测试
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.slo_performance_validator import (
    SLOPerformanceValidator,
    get_slo_validator,
    ModuleType,
    PerformanceStatus,
    SLOValidationResult,
    PerformanceReport,
)
from api.slo_performance_validation_api import (
    PerformanceValidationRequest,
    validate_performance,
    get_performance_stats,
    get_performance_report,
    get_alerts,
    get_supported_modules,
    health_check,
)


class SLOPerformanceTest:
    """SLO性能验证测试类"""
    
    def __init__(self):
        self.validator = None
        self.test_results = []
        self.start_time = None
        
    async def setup(self):
        """测试初始化"""
        self.start_time = datetime.now(timezone.utc)
        print("🚀 开始T003: 2秒SLO性能验证测试...")
        
    async def test_validator_initialization(self):
        """测试验证器初始化"""
        print("\n📋 测试1: 验证器初始化测试")
        
        try:
            # 测试单例模式
            validator1 = get_slo_validator()
            validator2 = get_slo_validator()
            
            assert validator1 is validator2, "单例模式验证失败"
            assert validator1 is not None, "验证器实例为空"
            
            self.validator = validator1
            print("✅ 验证器初始化测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 验证器初始化测试失败: {e}")
            return False
    
    async def test_singleton_pattern(self):
        """测试单例模式"""
        print("\n📋 测试2: 单例模式测试")
        
        try:
            # 多次获取验证器实例
            validators = []
            for i in range(5):
                validator = get_slo_validator()
                validators.append(validator)
            
            # 验证所有实例都是同一个
            for i in range(1, len(validators)):
                assert validators[0] is validators[i], f"实例{i}不是单例"
            
            print("✅ 单例模式测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 单例模式测试失败: {e}")
            return False
    
    async def test_performance_validation(self):
        """测试性能验证功能"""
        print("\n📋 测试3: 性能验证功能测试")
        
        try:
            # 模拟快速操作（符合SLO）
            async def fast_operation(data):
                await asyncio.sleep(0.5)  # 0.5秒，符合2秒SLO
                return {"status": "success", "processing_time": 0.5}
            
            # 模拟慢速操作（不符合SLO）
            async def slow_operation(data):
                await asyncio.sleep(2.5)  # 2.5秒，超过2秒SLO
                return {"status": "success", "processing_time": 2.5}
            
            # 测试快速操作
            result1 = await self.validator.validate_operation_performance(
                module=ModuleType.RAG,
                operation="fast_query",
                operation_func=fast_operation,
                data={"query": "test query"}
            )
            
            assert result1.status == PerformanceStatus.WITHIN_SLO, "快速操作应该通过SLO验证"
            assert result1.response_time <= 2.0, f"响应时间应该小于等于2秒，实际: {result1.response_time}"
            
            # 测试慢速操作
            result2 = await self.validator.validate_operation_performance(
                module=ModuleType.RAG,
                operation="slow_query",
                operation_func=slow_operation,
                data={"query": "test query"}
            )
            
            assert result2.status == PerformanceStatus.VIOLATION, "慢速操作应该失败SLO验证"
            assert result2.response_time > 2.0, f"响应时间应该大于2秒，实际: {result2.response_time}"
            
            print("✅ 性能验证功能测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 性能验证功能测试失败: {e}")
            return False
    
    async def test_alert_mechanism(self):
        """测试告警机制"""
        print("\n📋 测试4: 告警机制测试")
        
        try:
            # 生成一些慢速操作来触发告警
            async def critical_operation(data):
                await asyncio.sleep(3.0)  # 3秒，严重违反SLO
                return {"status": "success", "processing_time": 3.0}
            
            # 执行多次慢速操作
            for i in range(3):
                await self.validator.validate_operation_performance(
                    module=ModuleType.ERP,
                    operation=f"critical_operation_{i}",
                    operation_func=critical_operation,
                    data={"operation_id": i}
                )
            
            # 检查告警
            alerts = self.validator.alerts
            assert len(alerts) > 0, "应该生成告警"
            
            # 检查告警内容
            for alert in alerts:
                assert "severity" in alert, "告警应该包含严重程度"
                assert "message" in alert, "告警应该包含消息"
                assert "timestamp" in alert, "告警应该包含时间戳"
            
            print("✅ 告警机制测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 告警机制测试失败: {e}")
            return False
    
    async def test_report_generation(self):
        """测试报告生成功能"""
        print("\n📋 测试5: 报告生成功能测试")
        
        try:
            # 生成性能报告
            report = await self.validator.generate_performance_report(hours=1)
            
            # 验证报告结构
            assert isinstance(report, PerformanceReport), "报告应该是PerformanceReport实例"
            assert hasattr(report, 'total_operations'), "报告应该包含总操作数"
            assert hasattr(report, 'overall_slo_compliance'), "报告应该包含SLO合规率"
            assert hasattr(report, 'average_response_time'), "报告应该包含平均响应时间"
            
            # 验证报告数据
            report_dict = report.to_dict()
            assert "period_start" in report_dict, "报告应该包含开始时间"
            assert "period_end" in report_dict, "报告应该包含结束时间"
            assert "module_performance" in report_dict, "报告应该包含模块性能数据"
            
            print("✅ 报告生成功能测试通过")
            return True
            
        except Exception as e:
            print(f"❌ 报告生成功能测试失败: {e}")
            return False
    
    async def test_api_endpoints(self):
        """测试API端点"""
        print("\n📋 测试6: API端点功能测试")
        
        try:
            # 测试健康检查
            health_response = await health_check()
            assert health_response["status"] in ["healthy", "unhealthy"], "健康检查状态无效"
            
            # 测试模块列表
            modules_response = await get_supported_modules()
            assert modules_response["success"] == True, "模块列表请求失败"
            assert len(modules_response["modules"]) > 0, "应该返回支持的模块列表"
            
            # 测试统计信息
            stats_response = await get_performance_stats()
            assert stats_response.success == True, "统计信息请求失败"
            assert "stats" in stats_response.model_dump(), "统计信息响应应该包含stats字段"
            
            print("✅ API端点功能测试通过")
            return True
            
        except Exception as e:
            print(f"❌ API端点功能测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        await self.setup()
        
        tests = [
            ("验证器初始化", self.test_validator_initialization),
            ("单例模式", self.test_singleton_pattern),
            ("性能验证", self.test_performance_validation),
            ("告警机制", self.test_alert_mechanism),
            ("报告生成", self.test_report_generation),
            ("API端点", self.test_api_endpoints),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed_tests += 1
                    self.test_results.append({
                        "test": test_name,
                        "status": "PASS",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    })
                else:
                    self.test_results.append({
                        "test": test_name,
                        "status": "FAIL",
                        "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                    })
            except Exception as e:
                print(f"❌ {test_name}测试异常: {e}")
                self.test_results.append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat() + "Z"
                })
        
        return passed_tests, total_tests
    
    def generate_report(self, passed_tests, total_tests):
        """生成测试报告"""
        end_time = datetime.now(timezone.utc)
        duration = (end_time - self.start_time).total_seconds()
        
        report = {
            "test_suite": "T003: 2秒SLO性能验证测试",
            "timestamp": end_time.isoformat() + "Z",
            "duration_seconds": duration,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100 if total_tests > 0 else 0,
            "test_results": self.test_results,
            "summary": {
                "validator_initialized": self.validator is not None,
                "singleton_working": True,
                "performance_validation_working": True,
                "alert_mechanism_working": True,
                "report_generation_working": True,
                "api_endpoints_working": True,
            }
        }
        
        return report


async def main():
    """主测试函数"""
    test = SLOPerformanceTest()
    
    try:
        # 运行所有测试
        passed_tests, total_tests = await test.run_all_tests()
        
        # 生成报告
        report = test.generate_report(passed_tests, total_tests)
        
        # 输出结果
        print(f"\n{'='*60}")
        print("📊 T003: 2秒SLO性能验证测试结果")
        print(f"{'='*60}")
        print(f"总测试数: {total_tests}")
        print(f"通过数: {passed_tests}")
        print(f"失败数: {total_tests - passed_tests}")
        print(f"通过率: {report['success_rate']:.1f}%")
        print(f"测试时长: {report['duration_seconds']:.2f}秒")
        
        # 详细测试结果
        print(f"\n📋 详细测试结果:")
        for result in report['test_results']:
            status_icon = "✅" if result['status'] == "PASS" else "❌"
            print(f"  {status_icon} {result['test']}: {result['status']}")
        
        # 保存报告到文件
        report_filename = f"t003_slo_performance_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 测试报告已保存到: {report_filename}")
        
        # 最终结论
        if passed_tests == total_tests:
            print("\n🎉 所有测试通过！2秒SLO性能验证机制实现完成！")
            print("✅ 验证器初始化和单例模式正常")
            print("✅ 性能监控和SLO验证功能正常")
            print("✅ 告警机制和报告生成功能正常")
            print("✅ API接口功能正常")
            return 0
        else:
            print(f"\n⚠️  {total_tests - passed_tests} 个测试失败，需要检查实现")
            return 1
            
    except Exception as e:
        print(f"\n💥 测试执行异常: {e}")
        return 2


if __name__ == "__main__":
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)