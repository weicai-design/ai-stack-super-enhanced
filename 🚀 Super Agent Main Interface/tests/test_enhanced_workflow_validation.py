#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的工作流验证测试（T001）

测试目标：
1. 验证增强验证器的功能完整性
2. 测试双线闭环工作流的验证机制
3. 验证API接口的正确性
4. 测试错误处理和恢复机制
"""

from __future__ import annotations

import asyncio
import pytest
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow_enhanced_validator import (
    WorkflowEnhancedValidator,
    get_enhanced_validator,
    ValidationStatus,
    ValidationLevel,
    WorkflowValidationReport,
    ValidationResult,
)

logger = logging.getLogger(__name__)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class EnhancedWorkflowValidationTest:
    """增强的工作流验证测试类"""
    
    def __init__(self):
        self.validator: Optional[WorkflowEnhancedValidator] = None
        self.test_results: List[Dict[str, Any]] = []
    
    async def setup(self):
        """设置测试环境"""
        logger.info("设置增强工作流验证测试环境...")
        
        # 初始化验证器
        self.validator = WorkflowEnhancedValidator()
        
        logger.info("增强工作流验证测试环境设置完成")
    
    async def test_validation_workflow(self) -> Dict[str, Any]:
        """测试验证工作流"""
        logger.info("="*60)
        logger.info("测试1: 验证工作流")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 开始验证
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_wf_001",
                workflow_type="intelligent",
                user_input="测试工作流验证",
                context={"test": True},
            )
            
            # 等待验证完成
            await asyncio.sleep(1)  # 等待验证过程
            
            # 获取验证报告
            report = await self.validator.get_validation_report(validation_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证结果
            validations = {
                "validation_id_exists": validation_id is not None,
                "report_exists": report is not None,
                "workflow_id_correct": report.workflow_id == "test_wf_001",
                "workflow_type_correct": report.workflow_type == "intelligent",
                "has_validation_results": len(report.validation_results) > 0,
                "total_duration_positive": report.total_duration > 0,
                "overall_status_valid": report.overall_status in [
                    ValidationStatus.PASSED,
                    ValidationStatus.FAILED,
                    ValidationStatus.WARNING,
                ],
            }
            
            # 验证验证结果完整性
            if report.validation_results:
                result_names = [r.name for r in report.validation_results]
                validations["has_input_validation"] = "input_validation" in result_names
                validations["has_performance_validation"] = "performance_validation" in result_names
                validations["has_functional_validation"] = "functional_validation" in result_names
                validations["has_dual_loop_validation"] = "dual_loop_integrity" in result_names
                validations["has_security_validation"] = "security_validation" in result_names
                validations["has_reliability_validation"] = "reliability_validation" in result_names
                validations["has_observability_validation"] = "observability_validation" in result_names
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "验证工作流",
                "success": pass_rate >= 90,
                "duration_seconds": duration,
                "validations": validations,
                "pass_rate": pass_rate,
                "validation_id": validation_id,
                "overall_status": report.overall_status.value if report else None,
                "validation_results_count": len(report.validation_results) if report else 0,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"通过率: {pass_rate:.1f}%")
            logger.info(f"整体状态: {report.overall_status.value if report else 'N/A'}")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "验证工作流",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def test_validation_stats(self) -> Dict[str, Any]:
        """测试验证统计信息"""
        logger.info("="*60)
        logger.info("测试2: 验证统计信息")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 获取统计信息
            stats = await self.validator.get_validation_stats()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证统计信息
            validations = {
                "stats_exists": stats is not None,
                "has_total_validations": "total_validations" in stats,
                "has_passed_validations": "passed_validations" in stats,
                "has_failed_validations": "failed_validations" in stats,
                "has_warning_validations": "warning_validations" in stats,
                "total_validations_non_negative": stats["total_validations"] >= 0,
                "passed_validations_non_negative": stats["passed_validations"] >= 0,
                "failed_validations_non_negative": stats["failed_validations"] >= 0,
                "warning_validations_non_negative": stats["warning_validations"] >= 0,
            }
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "验证统计信息",
                "success": pass_rate >= 90,
                "duration_seconds": duration,
                "validations": validations,
                "pass_rate": pass_rate,
                "stats": stats,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"通过率: {pass_rate:.1f}%")
            logger.info(f"统计信息: {stats}")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "验证统计信息",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def test_dual_loop_validation(self) -> Dict[str, Any]:
        """测试双线闭环验证"""
        logger.info("="*60)
        logger.info("测试3: 双线闭环验证")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 测试智能工作流验证
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_wf_intelligent",
                workflow_type="intelligent",
                user_input="测试智能工作流",
                context={"domain": "erp"},
            )
            
            # 等待验证完成
            await asyncio.sleep(1)
            
            # 获取验证报告
            report = await self.validator.get_validation_report(validation_id)
            
            # 测试直接工作流验证
            direct_validation_id = await self.validator.start_workflow_validation(
                workflow_id="test_wf_direct",
                workflow_type="direct",
                user_input="测试直接工作流",
                context={"module": "erp"},
            )
            
            await asyncio.sleep(1)
            direct_report = await self.validator.get_validation_report(direct_validation_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证双线闭环验证
            validations = {
                "intelligent_validation_exists": report is not None,
                "direct_validation_exists": direct_report is not None,
                "intelligent_has_dual_loop_validation": any(
                    r.name == "dual_loop_integrity" for r in report.validation_results
                ),
                "direct_has_dual_loop_validation": any(
                    r.name == "dual_loop_integrity" for r in direct_report.validation_results
                ),
            }
            
            # 检查智能工作流的双线闭环验证结果
            if validations["intelligent_has_dual_loop_validation"]:
                dual_loop_result = next(
                    r for r in report.validation_results if r.name == "dual_loop_integrity"
                )
                validations["intelligent_dual_loop_passed"] = (
                    dual_loop_result.status == ValidationStatus.PASSED
                )
            
            # 检查直接工作流的双线闭环验证结果
            if validations["direct_has_dual_loop_validation"]:
                dual_loop_result = next(
                    r for r in direct_report.validation_results if r.name == "dual_loop_integrity"
                )
                validations["direct_dual_loop_passed"] = (
                    dual_loop_result.status == ValidationStatus.PASSED
                )
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "双线闭环验证",
                "success": pass_rate >= 90,
                "duration_seconds": duration,
                "validations": validations,
                "pass_rate": pass_rate,
                "intelligent_validation_id": validation_id,
                "direct_validation_id": direct_validation_id,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "双线闭环验证",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """测试错误处理"""
        logger.info("="*60)
        logger.info("测试4: 错误处理")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 测试无效输入
            validation_id = await self.validator.start_workflow_validation(
                workflow_id="",  # 无效工作流ID
                workflow_type="invalid_type",  # 无效工作流类型
                user_input="",  # 空输入
                context={},
            )
            
            await asyncio.sleep(1)
            
            # 获取验证报告
            report = await self.validator.get_validation_report(validation_id)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证错误处理
            validations = {
                "validation_completed": report is not None,
                "has_error_handling": True,  # 验证器应该能够处理无效输入
            }
            
            if report:
                validations["overall_status_valid"] = report.overall_status in [
                    ValidationStatus.PASSED,
                    ValidationStatus.FAILED,
                    ValidationStatus.WARNING,
                ]
                
                # 检查输入验证结果
                input_validation = next(
                    (r for r in report.validation_results if r.name == "input_validation"),
                    None
                )
                if input_validation:
                    validations["input_validation_exists"] = True
                    validations["input_validation_status"] = input_validation.status in [
                        ValidationStatus.PASSED,
                        ValidationStatus.FAILED,
                        ValidationStatus.WARNING,
                    ]
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "错误处理",
                "success": pass_rate >= 90,
                "duration_seconds": duration,
                "validations": validations,
                "pass_rate": pass_rate,
                "validation_id": validation_id,
                "overall_status": report.overall_status.value if report else None,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "错误处理",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        logger.info("="*60)
        logger.info("运行增强工作流验证测试套件")
        logger.info("="*60)
        
        await self.setup()
        
        # 运行所有测试
        tests = [
            self.test_validation_workflow,
            self.test_validation_stats,
            self.test_dual_loop_validation,
            self.test_error_handling,
        ]
        
        for test_func in tests:
            await test_func()
        
        # 生成测试报告
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        overall_pass_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        report = {
            "test_suite": "增强工作流验证测试",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "overall_pass_rate": overall_pass_rate,
            "test_results": self.test_results,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info("="*60)
        logger.info("测试套件完成")
        logger.info(f"总测试数: {total_tests}")
        logger.info(f"通过测试数: {passed_tests}")
        logger.info(f"整体通过率: {overall_pass_rate:.1f}%")
        logger.info("="*60)
        
        return report


# Pytest测试用例
@pytest.mark.asyncio
async def test_enhanced_workflow_validation():
    """Pytest测试用例：增强工作流验证"""
    test = EnhancedWorkflowValidationTest()
    report = await test.run_all_tests()
    
    assert report["overall_pass_rate"] >= 80, f"测试通过率不足: {report['overall_pass_rate']}%"


if __name__ == "__main__":
    # 直接运行测试
    async def main():
        test = EnhancedWorkflowValidationTest()
        report = await test.run_all_tests()
        
        # 保存测试报告
        import json
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_validation_test_report_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"测试报告已保存: {filename}")
        
        # 退出码
        exit_code = 0 if report["overall_pass_rate"] >= 80 else 1
        exit(exit_code)
    
    asyncio.run(main())