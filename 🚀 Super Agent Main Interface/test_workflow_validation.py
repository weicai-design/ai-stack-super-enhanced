#!/usr/bin/env python3
"""
工作流验证器测试脚本
测试双线闭环工作流验证机制的生产水平功能
"""

import asyncio
import sys
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.workflow_enhanced_validator import (
    WorkflowEnhancedValidator,
    ValidationStatus,
    ValidationLevel,
    WorkflowValidationReport
)


class WorkflowValidationTest:
    """工作流验证器测试类"""
    
    def __init__(self):
        self.results = {}
        self.test_count = 0
        self.passed_count = 0
        self.validator = None
    
    async def setup(self):
        """测试设置"""
        print("\n🔧 设置工作流验证器测试环境...")
        
        # 创建验证器实例
        self.validator = WorkflowEnhancedValidator()
        
        # 添加错误处理器
        def error_handler(validation_id: str, error: Exception):
            print(f"错误处理: {validation_id}, {error}")
        
        self.validator.add_error_handler(error_handler)
        
        # 添加监控回调
        async def monitoring_callback(event_type: str, data: Dict[str, Any]):
            print(f"监控事件: {event_type}, 数据: {data}")
        
        self.validator.add_monitoring_callback(monitoring_callback)
        
        print("✅ 测试环境设置完成")
    
    async def test_basic_validation(self):
        """测试基础验证功能"""
        print("\n🧪 测试基础验证功能...")
        
        try:
            # 测试智能工作流验证
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_workflow_001",
                workflow_type="intelligent",
                user_input="测试智能工作流验证",
                context={"test": True}
            )
            
            assert validation_id is not None, "验证ID为空"
            assert validation_id.startswith("val_"), "验证ID格式错误"
            
            # 等待验证完成
            await asyncio.sleep(1)
            
            # 检查验证报告
            report = self.validator.validation_reports.get(validation_id)
            assert report is not None, "验证报告不存在"
            assert isinstance(report, WorkflowValidationReport), "验证报告类型错误"
            
            # 检查验证结果
            assert len(report.validation_results) >= 6, "验证结果数量不足"
            assert report.overall_status in [ValidationStatus.PASSED, ValidationStatus.FAILED], "验证状态无效"
            
            self.results["basic_validation"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 基础验证功能测试通过")
            
        except Exception as e:
            self.results["basic_validation"] = f"❌ 失败: {str(e)}"
            print(f"❌ 基础验证功能测试失败: {e}")
    
    async def test_dual_loop_validation(self):
        """测试双线闭环验证"""
        print("\n🔄 测试双线闭环验证...")
        
        try:
            # 测试智能工作流的双线闭环验证
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_dual_loop_001",
                workflow_type="intelligent",
                user_input="测试双线闭环验证",
                context={"dual_loop": True}
            )
            
            await asyncio.sleep(1)
            
            report = self.validator.validation_reports.get(validation_id)
            assert report is not None, "双线闭环验证报告不存在"
            
            # 查找双线闭环验证结果
            dual_loop_result = None
            for result in report.validation_results:
                if result.name == "dual_loop_integrity":
                    dual_loop_result = result
                    break
            
            assert dual_loop_result is not None, "双线闭环验证结果不存在"
            assert dual_loop_result.level == ValidationLevel.CRITICAL, "验证级别错误"
            
            # 检查验证详情
            assert "loop_complete" in dual_loop_result.details, "缺少闭环完整性信息"
            assert "rag_phase" in dual_loop_result.details, "缺少RAG阶段信息"
            assert "expert_phase" in dual_loop_result.details, "缺少专家阶段信息"
            
            self.results["dual_loop_validation"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 双线闭环验证测试通过")
            
        except Exception as e:
            self.results["dual_loop_validation"] = f"❌ 失败: {str(e)}"
            print(f"❌ 双线闭环验证测试失败: {e}")
    
    async def test_error_handling(self):
        """测试错误处理机制"""
        print("\n⚠️ 测试错误处理机制...")
        
        try:
            # 测试无效参数的错误处理
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="",  # 空工作流ID
                workflow_type="intelligent",
                user_input="测试错误处理",
                context={}
            )
            
            await asyncio.sleep(1)
            
            report = self.validator.validation_reports.get(validation_id)
            assert report is not None, "错误处理验证报告不存在"
            
            # 检查是否有错误结果
            has_error = any(result.status == ValidationStatus.FAILED 
                          for result in report.validation_results)
            
            assert has_error, "错误处理机制未正确工作"
            
            self.results["error_handling"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 错误处理机制测试通过")
            
        except Exception as e:
            self.results["error_handling"] = f"❌ 失败: {str(e)}"
            print(f"❌ 错误处理机制测试失败: {e}")
    
    async def test_performance_monitoring(self):
        """测试性能监控"""
        print("\n📊 测试性能监控...")
        
        try:
            # 检查性能监控数据
            health_status = await self.validator._check_health_status()
            
            assert "timestamp" in health_status, "缺少时间戳"
            assert "concurrent_validations" in health_status, "缺少并发验证数"
            assert "success_rate" in health_status, "缺少成功率"
            assert "status" in health_status, "缺少健康状态"
            
            # 验证健康状态计算
            is_healthy = self.validator._is_healthy()
            assert isinstance(is_healthy, bool), "健康状态类型错误"
            
            # 验证成功率计算
            success_rate = self.validator._calculate_success_rate()
            assert 0 <= success_rate <= 1, "成功率范围错误"
            
            self.results["performance_monitoring"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 性能监控测试通过")
            
        except Exception as e:
            self.results["performance_monitoring"] = f"❌ 失败: {str(e)}"
            print(f"❌ 性能监控测试失败: {e}")
    
    async def test_report_generation(self):
        """测试报告生成"""
        print("\n📋 测试报告生成...")
        
        try:
            # 创建临时目录用于测试报告生成
            with tempfile.TemporaryDirectory() as temp_dir:
                # 修改配置以使用临时目录
                self.validator.config["reporting"]["save_directory"] = temp_dir
                
                # 执行验证
                validation_id = await self.validator.start_workflow_validation(
                    workflow_id="test_report_001",
                    workflow_type="intelligent",
                    user_input="测试报告生成",
                    context={"report_test": True}
                )
                
                await asyncio.sleep(1)
                
                # 检查报告文件是否生成
                report_files = list(Path(temp_dir).glob("*.json"))
                assert len(report_files) > 0, "报告文件未生成"
                
                # 验证报告内容
                report_file = report_files[0]
                with open(report_file, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                assert "workflow_id" in report_data, "报告缺少工作流ID"
                assert "validation_results" in report_data, "报告缺少验证结果"
                assert "overall_status" in report_data, "报告缺少整体状态"
                
                self.results["report_generation"] = "✅ 通过"
                self.passed_count += 1
                print("✅ 报告生成测试通过")
                
        except Exception as e:
            self.results["report_generation"] = f"❌ 失败: {str(e)}"
            print(f"❌ 报告生成测试失败: {e}")
    
    async def test_concurrent_validation(self):
        """测试并发验证"""
        print("\n⚡ 测试并发验证...")
        
        try:
            # 并发执行多个验证
            validation_tasks = []
            for i in range(5):
                task = self.validator.start_workflow_validation(
                    workflow_id=f"concurrent_test_{i}",
                    workflow_type="intelligent",
                    user_input=f"并发测试 {i}",
                    context={"concurrent": True}
                )
                validation_tasks.append(task)
            
            # 等待所有验证完成
            validation_ids = await asyncio.gather(*validation_tasks)
            
            await asyncio.sleep(2)  # 等待所有验证完成
            
            # 检查并发验证结果
            for validation_id in validation_ids:
                report = self.validator.validation_reports.get(validation_id)
                assert report is not None, f"并发验证报告不存在: {validation_id}"
                assert report.overall_status in [ValidationStatus.PASSED, ValidationStatus.FAILED], "验证状态无效"
            
            # 检查并发数统计
            assert self.validator.stats["concurrent_validations"] >= 5, "并发验证统计错误"
            
            self.results["concurrent_validation"] = "✅ 通过"
            self.passed_count += 1
            print("✅ 并发验证测试通过")
            
        except Exception as e:
            self.results["concurrent_validation"] = f"❌ 失败: {str(e)}"
            print(f"❌ 并发验证测试失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始工作流验证器生产水平测试...")
        
        await self.setup()
        
        # 执行所有测试
        test_methods = [
            self.test_basic_validation,
            self.test_dual_loop_validation,
            self.test_error_handling,
            self.test_performance_monitoring,
            self.test_report_generation,
            self.test_concurrent_validation,
        ]
        
        self.test_count = len(test_methods)
        
        for test_method in test_methods:
            await test_method()
        
        # 输出测试结果
        print("\n" + "="*60)
        print("📊 工作流验证器测试结果")
        print("="*60)
        
        for test_name, result in self.results.items():
            print(f"{test_name}: {result}")
        
        print(f"\n测试总数: {self.test_count}")
        print(f"通过数: {self.passed_count}")
        print(f"失败数: {self.test_count - self.passed_count}")
        print(f"成功率: {self.passed_count/self.test_count*100:.1f}%")
        
        if self.passed_count == self.test_count:
            print("\n🎉 所有测试通过！工作流验证器已达到生产水平！")
        else:
            print(f"\n⚠️  {self.test_count - self.passed_count} 个测试失败，需要进一步优化")


async def main():
    """主函数"""
    tester = WorkflowValidationTest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())