#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双线闭环工作流验证测试框架

验证目标：确保RAG→Expert→Module→Expert→RAG完整链路正常工作
验证标准：
1. 所有6个步骤都能正确执行
2. 2次RAG检索都能返回有效结果
3. 专家路由能正确选择专家
4. 模块执行能完成具体功能
5. 响应时间<2秒
6. 完整的可观测性追踪
"""

from __future__ import annotations

import asyncio
import json
import logging
import pytest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.dual_loop_workflow_engine import (
    DualLoopWorkflowEngine,
    WorkflowType,
    WorkflowExecutionResult,
    WorkflowStepType,
)
from core.workflow_orchestrator import WorkflowOrchestrator
from core.rag_service_adapter import RAGServiceAdapter
from core.expert_router import ExpertRouter
from core.module_executor import ModuleExecutor
from core.workflow_observability import get_workflow_observability

logger = logging.getLogger(__name__)


class DualLoopWorkflowValidator:
    """双线闭环工作流验证器"""
    
    def __init__(self):
        self.engine: Optional[DualLoopWorkflowEngine] = None
        self.validation_results: List[Dict[str, Any]] = []
        self.test_cases: List[Dict[str, Any]] = [
            {
                "name": "ERP订单查询",
                "user_input": "查询最近10个ERP订单状态",
                "expected_steps": 6,
                "expected_rag_calls": 2,
                "timeout": 5.0,
            },
            {
                "name": "内容创作建议",
                "user_input": "为抖音创作一个关于AI技术的短视频脚本",
                "expected_steps": 6,
                "expected_rag_calls": 2,
                "timeout": 5.0,
            },
            {
                "name": "股票趋势分析",
                "user_input": "分析苹果公司最近一个月的股票走势",
                "expected_steps": 6,
                "expected_rag_calls": 2,
                "timeout": 5.0,
            },
        ]
    
    async def setup(self):
        """设置验证环境"""
        logger.info("设置双线闭环工作流验证环境...")
        
        # 初始化工作流引擎
        orchestrator = WorkflowOrchestrator()
        rag_service = RAGServiceAdapter()
        expert_router = ExpertRouter()
        module_executor = ModuleExecutor()
        observability = get_workflow_observability()
        
        self.engine = DualLoopWorkflowEngine(
            workflow_orchestrator=orchestrator,
            rag_service=rag_service,
            expert_router=expert_router,
            module_executor=module_executor,
            workflow_observability=observability,
        )
        
        logger.info("双线闭环工作流验证环境设置完成")
    
    async def validate_workflow_complete_chain(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """验证工作流完整链路"""
        logger.info(f"开始验证测试用例: {test_case['name']}")
        
        start_time = datetime.now()
        
        try:
            # 执行智能工作流
            result: WorkflowExecutionResult = await self.engine.execute_intelligent_workflow(
                user_input=test_case["user_input"],
                context={}
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证结果
            validations = self._validate_workflow_result(result, test_case, duration)
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            validation_result = {
                "test_case": test_case["name"],
                "user_input": test_case["user_input"],
                "success": result.success and pass_rate >= 90,
                "duration_seconds": duration,
                "pass_rate": pass_rate,
                "validations": validations,
                "workflow_id": result.workflow_id,
                "trace_id": result.trace_id,
                "steps_count": len(result.steps),
                "steps_detail": self._get_steps_detail(result.steps),
                "timestamp": datetime.now().isoformat(),
            }
            
            self.validation_results.append(validation_result)
            
            logger.info(f"验证结果: {'通过' if validation_result['success'] else '失败'}")
            logger.info(f"响应时间: {duration:.3f}秒")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"验证失败: {e}", exc_info=True)
            return {
                "test_case": test_case["name"],
                "user_input": test_case["user_input"],
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    def _validate_workflow_result(self, result: WorkflowExecutionResult, 
                                 test_case: Dict[str, Any], duration: float) -> Dict[str, bool]:
        """验证工作流结果"""
        validations = {}
        
        # 基础验证
        validations["workflow_id_exists"] = result.workflow_id is not None
        validations["workflow_type_correct"] = result.workflow_type == WorkflowType.INTELLIGENT
        validations["has_trace_id"] = result.trace_id is not None
        validations["success_status"] = result.success
        
        # 步骤数量验证
        validations["steps_count_ok"] = len(result.steps) >= test_case["expected_steps"]
        
        # 响应时间验证
        validations["response_time_ok"] = duration < 2.0
        
        # 步骤完整性验证
        step_types = [step.step_type for step in result.steps]
        validations["has_rag_retrieval_1"] = WorkflowStepType.RAG_RETRIEVAL_1 in step_types
        validations["has_expert_routing_1"] = WorkflowStepType.EXPERT_ROUTING_1 in step_types
        validations["has_module_execution"] = WorkflowStepType.MODULE_EXECUTION in step_types
        validations["has_expert_routing_2"] = WorkflowStepType.EXPERT_ROUTING_2 in step_types
        validations["has_rag_retrieval_2"] = WorkflowStepType.RAG_RETRIEVAL_2 in step_types
        validations["has_response_generation"] = WorkflowStepType.RESPONSE_GENERATION in step_types
        
        # 步骤可追踪性验证
        all_steps_trackable = all(
            step.started_at is not None and step.completed_at is not None
            for step in result.steps
        )
        validations["all_steps_trackable"] = all_steps_trackable
        
        # RAG调用次数验证
        rag_calls = sum(1 for step in result.steps 
                       if step.step_type in [WorkflowStepType.RAG_RETRIEVAL_1, 
                                           WorkflowStepType.RAG_RETRIEVAL_2])
        validations["rag_calls_ok"] = rag_calls >= test_case["expected_rag_calls"]
        
        # 步骤成功率验证
        successful_steps = sum(1 for step in result.steps if step.success)
        validations["steps_success_rate_ok"] = (successful_steps / len(result.steps)) >= 0.8
        
        return validations
    
    def _get_steps_detail(self, steps: List[Any]) -> List[Dict[str, Any]]:
        """获取步骤详情"""
        return [
            {
                "step_type": step.step_type.value,
                "success": step.success,
                "duration": step.duration,
                "started_at": step.started_at,
                "completed_at": step.completed_at,
            }
            for step in steps
        ]
    
    async def run_all_validations(self) -> Dict[str, Any]:
        """运行所有验证"""
        logger.info("开始运行双线闭环工作流完整验证...")
        
        results = []
        for test_case in self.test_cases:
            result = await self.validate_workflow_complete_chain(test_case)
            results.append(result)
        
        # 计算总体通过率
        total_passed = sum(1 for r in results if r["success"])
        total_cases = len(results)
        overall_pass_rate = total_passed / total_cases * 100
        
        summary = {
            "total_cases": total_cases,
            "passed_cases": total_passed,
            "overall_pass_rate": overall_pass_rate,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"验证完成: {total_passed}/{total_cases} 通过 ({overall_pass_rate:.1f}%)")
        
        return summary
    
    def generate_validation_report(self, summary: Dict[str, Any]) -> str:
        """生成验证报告"""
        report = f"""
# 双线闭环工作流验证报告

## 验证摘要
- 验证时间: {summary['timestamp']}
- 测试用例总数: {summary['total_cases']}
- 通过用例数: {summary['passed_cases']}
- 总体通过率: {summary['overall_pass_rate']:.1f}%

## 详细结果
"""
        
        for i, result in enumerate(summary["results"], 1):
            report += f"""
### 测试用例 {i}: {result['test_case']}
- 用户输入: {result['user_input']}
- 验证结果: {'✅ 通过' if result['success'] else '❌ 失败'}
- 响应时间: {result.get('duration_seconds', 0):.3f}秒
- 通过率: {result.get('pass_rate', 0):.1f}%
- 工作流ID: {result.get('workflow_id', 'N/A')}
- Trace ID: {result.get('trace_id', 'N/A')}

**验证详情:**
"""
            
            if "validations" in result:
                for key, value in result["validations"].items():
                    status = "✅" if value else "❌"
                    report += f"- {status} {key}\n"
            
            if "error" in result:
                report += f"\n**错误信息:** {result['error']}\n"
        
        return report


# 测试函数
@pytest.mark.asyncio
async def test_dual_loop_workflow_complete_chain():
    """测试双线闭环工作流完整链路"""
    validator = DualLoopWorkflowValidator()
    await validator.setup()
    
    summary = await validator.run_all_validations()
    
    # 验证总体通过率
    assert summary["overall_pass_rate"] >= 80.0, f"总体通过率不足80%: {summary['overall_pass_rate']:.1f}%"
    
    # 验证每个测试用例
    for result in summary["results"]:
        assert result["success"], f"测试用例 {result['test_case']} 失败"
        
        # 验证响应时间
        if "duration_seconds" in result:
            assert result["duration_seconds"] < 2.0, f"响应时间超过2秒: {result['duration_seconds']:.3f}秒"


if __name__ == "__main__":
    # 直接运行验证
    async def main():
        validator = DualLoopWorkflowValidator()
        await validator.setup()
        
        summary = await validator.run_all_validations()
        
        # 生成并打印报告
        report = validator.generate_validation_report(summary)
        print(report)
        
        # 保存报告到文件
        report_file = Path("dual_loop_workflow_validation_report.md")
        report_file.write_text(report, encoding="utf-8")
        print(f"验证报告已保存到: {report_file.absolute()}")
    
    asyncio.run(main())