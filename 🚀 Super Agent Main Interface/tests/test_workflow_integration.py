#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流集成测试（T001）
验证RAG→Expert→Module→Expert→RAG完整链路

验收标准：
1. 所有工作流步骤可追踪
2. 有完整日志
3. 响应时间<2秒
"""

from __future__ import annotations

import asyncio
import pytest
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys
from dataclasses import dataclass, field, asdict

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class WorkflowIntegrationTest:
    """
    工作流集成测试类（T001）
    
    验证双线闭环工作流的完整链路
    """
    
    def __init__(self):
        self.engine: Optional[DualLoopWorkflowEngine] = None
        self.test_results: List[Dict[str, Any]] = []
        
    async def setup(self):
        """设置测试环境"""
        logger.info("设置工作流集成测试环境...")
        
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
        
        logger.info("工作流集成测试环境设置完成")
    
    async def test_intelligent_workflow_complete_chain(self) -> Dict[str, Any]:
        """
        测试智能工作流完整链路
        
        验证：用户输入 → RAG1 → 专家1 → 模块 → 专家2 → RAG2 → 响应生成
        """
        logger.info("="*60)
        logger.info("测试1: 智能工作流完整链路")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 执行智能工作流
            result: WorkflowExecutionResult = await self.engine.execute_intelligent_workflow(
                user_input="查询ERP订单状态",
                context={}
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证结果
            validations = {
                "workflow_id_exists": result.workflow_id is not None,
                "workflow_type_correct": result.workflow_type == WorkflowType.INTELLIGENT,
                "has_trace_id": result.trace_id is not None,
                "all_steps_present": len(result.steps) >= 6,  # 至少6个步骤
                "response_time_ok": duration < 2.0,  # 响应时间<2秒
                "success": result.success,
            }
            
            # 验证步骤完整性
            step_types = [step.step_type for step in result.steps]
            validations["has_rag_retrieval_1"] = WorkflowStepType.RAG_RETRIEVAL_1 in step_types
            validations["has_expert_routing_1"] = WorkflowStepType.EXPERT_ROUTING_1 in step_types
            validations["has_module_execution"] = WorkflowStepType.MODULE_EXECUTION in step_types
            validations["has_expert_routing_2"] = WorkflowStepType.EXPERT_ROUTING_2 in step_types
            validations["has_rag_retrieval_2"] = WorkflowStepType.RAG_RETRIEVAL_2 in step_types
            validations["has_response_generation"] = WorkflowStepType.RESPONSE_GENERATION in step_types
            
            # 验证步骤可追踪性
            all_steps_trackable = all(
                step.started_at is not None and step.completed_at is not None
                for step in result.steps
            )
            validations["all_steps_trackable"] = all_steps_trackable
            
            # 验证日志完整性
            log_file = Path("logs/workflow") / f"workflow_{datetime.now().strftime('%Y%m%d')}.log"
            has_logs = log_file.exists()
            validations["has_logs"] = has_logs
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "智能工作流完整链路",
                "success": result.success and pass_rate >= 90,
                "duration_seconds": duration,
                "response_time_ok": duration < 2.0,
                "validations": validations,
                "pass_rate": pass_rate,
                "workflow_id": result.workflow_id,
                "trace_id": result.trace_id,
                "steps_count": len(result.steps),
                "steps_detail": [
                    {
                        "step_type": step.step_type.value,
                        "success": step.success,
                        "duration": step.duration,
                        "started_at": step.started_at,
                        "completed_at": step.completed_at,
                    }
                    for step in result.steps
                ],
                "error": result.error,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"响应时间: {duration:.3f}秒 ({'✓' if duration < 2.0 else '✗'})")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "智能工作流完整链路",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def test_direct_workflow_complete_chain(self) -> Dict[str, Any]:
        """
        测试直接工作流完整链路
        
        验证：用户输入 → 模块执行 → 响应生成
        """
        logger.info("="*60)
        logger.info("测试2: 直接工作流完整链路")
        logger.info("="*60)
        
        start_time = datetime.now()
        
        try:
            # 执行直接工作流
            result: WorkflowExecutionResult = await self.engine.execute_direct_workflow(
                module="erp",
                action="get_orders",
                params={"limit": 10}
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 验证结果
            validations = {
                "workflow_id_exists": result.workflow_id is not None,
                "workflow_type_correct": result.workflow_type == WorkflowType.DIRECT,
                "has_trace_id": result.trace_id is not None,
                "has_module_execution": any(
                    step.step_type == WorkflowStepType.MODULE_EXECUTION
                    for step in result.steps
                ),
                "response_time_ok": duration < 2.0,
                "success": result.success,
            }
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "直接工作流完整链路",
                "success": result.success and pass_rate >= 90,
                "duration_seconds": duration,
                "response_time_ok": duration < 2.0,
                "validations": validations,
                "pass_rate": pass_rate,
                "workflow_id": result.workflow_id,
                "trace_id": result.trace_id,
                "steps_count": len(result.steps),
                "error": result.error,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"响应时间: {duration:.3f}秒 ({'✓' if duration < 2.0 else '✗'})")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "直接工作流完整链路",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def test_workflow_traceability(self) -> Dict[str, Any]:
        """
        测试工作流可追踪性
        
        验证：所有步骤都有trace_id、span_id，可以完整追踪
        """
        logger.info("="*60)
        logger.info("测试3: 工作流可追踪性")
        logger.info("="*60)
        
        try:
            # 执行工作流
            result: WorkflowExecutionResult = await self.engine.execute_intelligent_workflow(
                user_input="生成内容创作计划",
                context={}
            )
            
            # 验证可追踪性
            validations = {
                "has_trace_id": result.trace_id is not None,
                "all_steps_have_timestamps": all(
                    step.started_at and step.completed_at
                    for step in result.steps
                ),
                "all_steps_have_duration": all(
                    step.duration > 0
                    for step in result.steps
                ),
            }
            
            # 检查可观测性数据
            if result.trace_id:
                observability = get_workflow_observability()
                trace = observability.get_workflow_trace(result.trace_id)
                validations["trace_exists"] = trace is not None
                
                if trace:
                    spans = observability.get_workflow_spans(result.trace_id)
                    validations["has_spans"] = len(spans) > 0
                    validations["spans_match_steps"] = len(spans) == len(result.steps)
            
            # 计算通过率
            passed = sum(1 for v in validations.values() if v)
            total = len(validations)
            pass_rate = passed / total * 100
            
            test_result = {
                "test_name": "工作流可追踪性",
                "success": pass_rate >= 90,
                "validations": validations,
                "pass_rate": pass_rate,
                "trace_id": result.trace_id,
                "spans_count": len(spans) if validations.get("has_spans") else 0,
                "timestamp": datetime.now().isoformat(),
            }
            
            self.test_results.append(test_result)
            
            logger.info(f"测试结果: {'通过' if test_result['success'] else '失败'}")
            logger.info(f"通过率: {pass_rate:.1f}%")
            
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {e}", exc_info=True)
            return {
                "test_name": "工作流可追踪性",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    def generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.get("success", False))
        pass_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        # 计算平均响应时间
        response_times = [
            r.get("duration_seconds", 0)
            for r in self.test_results
            if "duration_seconds" in r
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # 检查2秒SLO
        slo_compliant = all(
            r.get("response_time_ok", False)
            for r in self.test_results
            if "response_time_ok" in r
        )
        
        report = {
            "test_suite": "工作流集成测试（T001）",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "pass_rate": pass_rate,
                "avg_response_time_seconds": avg_response_time,
                "slo_2s_compliant": slo_compliant,
            },
            "test_results": self.test_results,
        }
        
        return report


@pytest.mark.asyncio
async def test_intelligent_workflow_integration():
    """Pytest测试用例：智能工作流集成"""
    test = WorkflowIntegrationTest()
    await test.setup()
    result = await test.test_intelligent_workflow_complete_chain()
    assert result["success"], f"测试失败: {result.get('error', '未知错误')}"


@pytest.mark.asyncio
async def test_direct_workflow_integration():
    """Pytest测试用例：直接工作流集成"""
    test = WorkflowIntegrationTest()
    await test.setup()
    result = await test.test_direct_workflow_complete_chain()
    assert result["success"], f"测试失败: {result.get('error', '未知错误')}"


@pytest.mark.asyncio
async def test_workflow_traceability():
    """Pytest测试用例：工作流可追踪性"""
    test = WorkflowIntegrationTest()
    await test.setup()
    result = await test.test_workflow_traceability()
    assert result["success"], f"测试失败: {result.get('error', '未知错误')}"


async def main():
    """主函数：运行所有集成测试"""
    test = WorkflowIntegrationTest()
    await test.setup()
    
    # 运行所有测试
    await test.test_intelligent_workflow_complete_chain()
    await test.test_direct_workflow_complete_chain()
    await test.test_workflow_traceability()
    
    # 生成报告
    report = test.generate_report()
    
    # 保存报告
    report_file = Path("logs/workflow") / f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    logger.info("="*60)
    logger.info("工作流集成测试报告")
    logger.info("="*60)
    logger.info(f"总测试数: {report['summary']['total_tests']}")
    logger.info(f"通过数: {report['summary']['passed_tests']}")
    logger.info(f"通过率: {report['summary']['pass_rate']:.1f}%")
    logger.info(f"平均响应时间: {report['summary']['avg_response_time_seconds']:.3f}秒")
    logger.info(f"2秒SLO合规: {'是' if report['summary']['slo_2s_compliant'] else '否'}")
    logger.info(f"报告已保存: {report_file}")
    
    return report


if __name__ == "__main__":
    asyncio.run(main())

