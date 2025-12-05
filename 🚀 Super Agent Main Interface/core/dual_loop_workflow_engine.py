"""
双线闭环工作流引擎
实现"RAG→专家→模块→专家→RAG"的完整闭环流程

功能：
1. 智能线：RAG检索 → 专家路由 → 模块执行 → 专家后处理 → RAG整合
2. 直接操作线：直接模块执行（跳过RAG和专家路由）
3. 完整的状态管理和追踪
4. 可观测性支持（trace_id、span_id）
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowType,
    WorkflowState,
    IntelligentWorkflowData,
    DirectWorkflowData,
)
from .rag_service_adapter import RAGServiceAdapter
from .expert_router import ExpertRouter
from .module_executor import ModuleExecutor
from .workflow_observability import (
    WorkflowObservability,
    get_workflow_observability,
)
# 尝试导入RAG专家系统（如果可用）
try:
    import sys
    from pathlib import Path
    # 添加RAG模块路径
    rag_path = Path(__file__).parent.parent.parent / "📚 Enhanced RAG & Knowledge Graph"
    if rag_path.exists():
        sys.path.insert(0, str(rag_path))
    from core.rag_expert_system import RAGExpertSystem, get_rag_expert_system
except ImportError:
    # 如果导入失败，使用None（可选依赖）
    RAGExpertSystem = None
    def get_rag_expert_system(*args, **kwargs):
        return None

logger = logging.getLogger(__name__)


class WorkflowStepType(str, Enum):
    """工作流步骤类型"""
    RAG_RETRIEVAL_1 = "rag_retrieval_1"  # 第一次RAG检索
    EXPERT_ROUTING_1 = "expert_routing_1"  # 第一次专家路由
    MODULE_EXECUTION = "module_execution"  # 模块执行
    EXPERT_ROUTING_2 = "expert_routing_2"  # 第二次专家路由（后处理）
    RAG_RETRIEVAL_2 = "rag_retrieval_2"  # 第二次RAG检索（整合经验）
    RESPONSE_GENERATION = "response_generation"  # 响应生成


@dataclass
class WorkflowStepResult:
    """工作流步骤结果"""
    step_type: WorkflowStepType
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration: float = 0.0
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    completed_at: Optional[str] = None


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果"""
    workflow_id: str
    workflow_type: WorkflowType
    success: bool
    response: str
    steps: List[WorkflowStepResult] = field(default_factory=list)
    total_duration: float = 0.0
    trace_id: Optional[str] = None
    error: Optional[str] = None


class DualLoopWorkflowEngine:
    """
    双线闭环工作流引擎
    
    实现完整的"RAG→专家→模块→专家→RAG"闭环流程
    """
    
    def __init__(
        self,
        workflow_orchestrator: Optional[WorkflowOrchestrator] = None,
        rag_service: Optional[RAGServiceAdapter] = None,
        expert_router: Optional[ExpertRouter] = None,
        module_executor: Optional[ModuleExecutor] = None,
        expert_system: Optional[Any] = None,
        workflow_observability: Optional[WorkflowObservability] = None,
    ):
        """
        初始化工作流引擎
        
        Args:
            workflow_orchestrator: 工作流编排器
            rag_service: RAG服务适配器
            expert_router: 专家路由器
            module_executor: 模块执行器
            expert_system: 专家系统
        """
        self.orchestrator = workflow_orchestrator or WorkflowOrchestrator()
        self.rag_service = rag_service or RAGServiceAdapter()
        self.expert_router = expert_router or ExpertRouter()
        self.module_executor = module_executor or ModuleExecutor()
        self.expert_system = expert_system or get_rag_expert_system()
        self.observability = workflow_observability or get_workflow_observability()
        
        # 执行历史
        self.execution_history: Dict[str, WorkflowExecutionResult] = {}
    
    async def execute_intelligent_workflow(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> WorkflowExecutionResult:
        """
        执行智能线工作流（RAG→专家→模块→专家→RAG）
        
        完整流程：
        1. RAG检索（理解需求）
        2. 专家路由（选择专家和模块）
        3. 模块执行（执行具体功能）
        4. 专家后处理（专家系统处理结果）
        5. RAG检索（整合历史经验和最佳实践）
        6. 响应生成（综合所有信息生成最终响应）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            trace_id: Trace ID（可选）
            parent_span_id: 父 Span ID（可选）
            
        Returns:
            工作流执行结果
        """
        start_time = datetime.utcnow()
        workflow_id = await self.orchestrator.create_intelligent_workflow(
            user_input=user_input,
            context=context,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        workflow_snapshot = await self.orchestrator.get_workflow(workflow_id)
        workflow_trace_id = None
        if workflow_snapshot:
            workflow_trace_id = workflow_snapshot.get("trace_id") or trace_id
        else:
            workflow_trace_id = trace_id
        
        # 开始可观测性追踪
        obs_context = self.observability.start_workflow_trace(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.INTELLIGENT.value,
            user_input=user_input,
            context=context or {},
            trace_id=workflow_trace_id,
        )
        
        steps: List[WorkflowStepResult] = []
        workflow_data: Optional[IntelligentWorkflowData] = None
        current_span_id: Optional[str] = None
        
        try:
            # 获取工作流数据
            workflow_dict = await self.orchestrator.get_workflow(workflow_id)
            if workflow_dict:
                workflow_data = IntelligentWorkflowData(**workflow_dict)
            
            # 步骤1: 第一次RAG检索（理解需求）
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.RAG_RETRIEVAL_1,
            )
            
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="rag_retrieval_1",
                step_type="rag_retrieval",
                parent_span_id=current_span_id,
                input_data={"user_input": user_input},
            )
            if step_span:
                current_span_id = step_span.span_id
            
            rag_result_1 = await self._execute_rag_retrieval_1(
                user_input,
                context or {},
                workflow_id,
            )
            steps.append(rag_result_1)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="rag_retrieval_1",
                span_id=current_span_id,
                success=rag_result_1.success,
                duration=rag_result_1.duration,
                output_data=rag_result_1.data,
                error=rag_result_1.error,
            )
            
            if not rag_result_1.success:
                raise Exception(f"RAG检索失败: {rag_result_1.error}")
            
            # 步骤2: 第一次专家路由（选择专家和模块）
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.EXPERT_ROUTING,
                step_data={
                    "output_data": rag_result_1.data,
                },
            )
            
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="expert_routing_1",
                step_type="expert_routing",
                parent_span_id=current_span_id,
                input_data={"rag_result": rag_result_1.data},
            )
            if step_span:
                current_span_id = step_span.span_id
            
            expert_routing_1 = await self._execute_expert_routing_1(
                user_input,
                rag_result_1.data,
                workflow_id,
            )
            steps.append(expert_routing_1)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="expert_routing_1",
                span_id=current_span_id,
                success=expert_routing_1.success,
                duration=expert_routing_1.duration,
                output_data=expert_routing_1.data,
                error=expert_routing_1.error,
            )
            
            if not expert_routing_1.success:
                raise Exception(f"专家路由失败: {expert_routing_1.error}")
            
            # 步骤3: 模块执行
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.MODULE_EXECUTION,
                step_data={
                    "output_data": expert_routing_1.data,
                },
            )
            
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="module_execution",
                step_type="module_execution",
                parent_span_id=current_span_id,
                input_data={"expert_info": expert_routing_1.data},
            )
            if step_span:
                current_span_id = step_span.span_id
            
            module_execution = await self._execute_module_execution(
                user_input,
                expert_routing_1.data,
                rag_result_1.data,
                workflow_id,
            )
            steps.append(module_execution)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="module_execution",
                span_id=current_span_id,
                success=module_execution.success,
                duration=module_execution.duration,
                output_data=module_execution.data,
                error=module_execution.error,
            )
            
            if not module_execution.success:
                raise Exception(f"模块执行失败: {module_execution.error}")
            
            # 步骤4: 第二次专家路由（后处理）
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="expert_routing_2",
                step_type="expert_routing",
                parent_span_id=current_span_id,
                input_data={"module_result": module_execution.data},
            )
            if step_span:
                current_span_id = step_span.span_id
            
            expert_routing_2 = await self._execute_expert_routing_2(
                user_input,
                module_execution.data,
                expert_routing_1.data,
                workflow_id,
            )
            steps.append(expert_routing_2)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="expert_routing_2",
                span_id=current_span_id,
                success=expert_routing_2.success,
                duration=expert_routing_2.duration,
                output_data=expert_routing_2.data,
                error=expert_routing_2.error,
            )
            
            # 步骤5: 第二次RAG检索（整合历史经验和最佳实践）
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.RAG_RETRIEVAL_2,
                step_data={
                    "output_data": module_execution.data,
                },
            )
            
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="rag_retrieval_2",
                step_type="rag_retrieval",
                parent_span_id=current_span_id,
                input_data={"module_result": module_execution.data},
            )
            if step_span:
                current_span_id = step_span.span_id
            
            rag_result_2 = await self._execute_rag_retrieval_2(
                user_input,
                module_execution.data,
                expert_routing_1.data,
                workflow_id,
            )
            steps.append(rag_result_2)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="rag_retrieval_2",
                span_id=current_span_id,
                success=rag_result_2.success,
                duration=rag_result_2.duration,
                output_data=rag_result_2.data,
                error=rag_result_2.error,
            )
            
            # 步骤6: 响应生成
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.RESPONSE_GENERATION,
                step_data={
                    "output_data": rag_result_2.data if rag_result_2.success else {},
                },
            )
            
            # 开始步骤追踪
            step_span = self.observability.start_workflow_step(
                workflow_id=workflow_id,
                step_name="response_generation",
                step_type="response_generation",
                parent_span_id=current_span_id,
                input_data={
                    "rag_result_2": rag_result_2.data if rag_result_2.success else None,
                },
            )
            if step_span:
                current_span_id = step_span.span_id
            
            response_generation = await self._execute_response_generation(
                user_input,
                rag_result_1.data,
                expert_routing_1.data,
                module_execution.data,
                expert_routing_2.data if expert_routing_2.success else None,
                rag_result_2.data if rag_result_2.success else None,
                workflow_id,
            )
            steps.append(response_generation)
            
            # 完成步骤追踪
            self.observability.complete_workflow_step(
                workflow_id=workflow_id,
                step_name="response_generation",
                span_id=current_span_id,
                success=response_generation.success,
                duration=response_generation.duration,
                output_data=response_generation.data,
                error=response_generation.error,
            )
            
            if not response_generation.success:
                raise Exception(f"响应生成失败: {response_generation.error}")
            
            # 完成工作流
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.COMPLETED,
                step_data={
                    "output_data": {"response": response_generation.data.get("response", "")},
                },
            )
            
            # 计算总时长
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            # 构建执行结果
            result = WorkflowExecutionResult(
                workflow_id=workflow_id,
                workflow_type=WorkflowType.INTELLIGENT,
                success=True,
                response=response_generation.data.get("response", ""),
                steps=steps,
                total_duration=total_duration,
                trace_id=workflow_data.trace_id if workflow_data else None,
            )
            
            self.execution_history[workflow_id] = result
            return result
            
        except Exception as e:
            logger.error(f"智能线工作流执行失败: {e}", exc_info=True)
            
            # 标记为失败
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.FAILED,
                error=str(e),
            )
            
            # 完成可观测性追踪（失败）
            total_duration = (datetime.utcnow() - start_time).total_seconds()
            self.observability.complete_workflow_trace(
                workflow_id=workflow_id,
                success=False,
                total_duration=total_duration,
                error=str(e),
            )
            
            # 构建失败结果
            result = WorkflowExecutionResult(
                workflow_id=workflow_id,
                workflow_type=WorkflowType.INTELLIGENT,
                success=False,
                response="",
                steps=steps,
                total_duration=total_duration,
                trace_id=obs_context.trace_id,
                error=str(e),
            )
            
            self.execution_history[workflow_id] = result
            return result
    
    async def execute_direct_workflow(
        self,
        user_input: Optional[str] = None,
        target_module: Optional[str] = None,
        *,
        module: Optional[str] = None,
        action: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
    ) -> WorkflowExecutionResult:
        """
        执行直接操作线工作流（跳过RAG和专家路由）
        
        流程：
        1. 模块执行
        2. 响应生成
        
        Args:
            user_input: 用户输入
            target_module: 目标模块
            context: 上下文信息
            trace_id: Trace ID（可选）
            parent_span_id: 父 Span ID（可选）
            
        Returns:
            工作流执行结果
        """
        params = params or {}
        context = dict(context) if context else {}
        target_module = target_module or module or context.get("target_module") or "general"
        action_name = action or context.get("action") or "execute"
        context.setdefault("params", params)
        context.setdefault("action", action_name)
        context.setdefault("target_module", target_module)
        effective_input = user_input or self._build_direct_user_input(target_module, action_name, params)
        metadata = {"action": action_name, "params": params}
        start_time = datetime.utcnow()
        workflow_id = await self.orchestrator.create_direct_workflow(
            user_input=effective_input,
            target_module=target_module,
            context=context,
            metadata=metadata,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        
        steps: List[WorkflowStepResult] = []
        workflow_data: Optional[DirectWorkflowData] = None
        
        try:
            # 获取工作流数据
            workflow_dict = await self.orchestrator.get_workflow(workflow_id)
            if workflow_dict:
                workflow_data = DirectWorkflowData(**workflow_dict)
            
            # 步骤1: 模块执行
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.MODULE_EXECUTION,
            )
            
            module_execution = await self._execute_direct_module_execution(
                effective_input,
                target_module,
                context,
                workflow_id,
            )
            steps.append(module_execution)
            
            if not module_execution.success:
                raise Exception(f"模块执行失败: {module_execution.error}")
            
            # 步骤2: 响应生成
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.RESPONSE_GENERATION,
                step_data={
                    "output_data": module_execution.data,
                },
            )
            
            response_generation = await self._execute_direct_response_generation(
                user_input,
                module_execution.data,
                workflow_id,
            )
            steps.append(response_generation)
            
            if not response_generation.success:
                raise Exception(f"响应生成失败: {response_generation.error}")
            
            # 完成工作流
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.COMPLETED,
                step_data={
                    "output_data": {"response": response_generation.data.get("response", "")},
                },
            )
            
            # 计算总时长
            end_time = datetime.utcnow()
            total_duration = (end_time - start_time).total_seconds()
            
            # 构建执行结果
            result = WorkflowExecutionResult(
                workflow_id=workflow_id,
                workflow_type=WorkflowType.DIRECT,
                success=True,
                response=response_generation.data.get("response", ""),
                steps=steps,
                total_duration=total_duration,
                trace_id=workflow_data.trace_id if workflow_data else None,
            )
            
            self.execution_history[workflow_id] = result
            return result
            
        except Exception as e:
            logger.error(f"直接操作线工作流执行失败: {e}", exc_info=True)
            
            # 标记为失败
            await self.orchestrator.transition_state(
                workflow_id,
                WorkflowState.FAILED,
                error=str(e),
            )
            
            # 构建失败结果
            result = WorkflowExecutionResult(
                workflow_id=workflow_id,
                workflow_type=WorkflowType.DIRECT,
                success=False,
                response="",
                steps=steps,
                total_duration=(datetime.utcnow() - start_time).total_seconds(),
                trace_id=workflow_data.trace_id if workflow_data else None,
                error=str(e),
            )
            
            self.execution_history[workflow_id] = result
            return result

    @staticmethod
    def _build_direct_user_input(
        target_module: str,
        action: Optional[str],
        params: Dict[str, Any],
    ) -> str:
        """根据模块、动作和参数生成可追踪的直接工作流输入描述"""
        action_part = action or "execute"
        if params:
            param_kv = ", ".join(f"{k}={v}" for k, v in params.items())
            return f"[Direct] module={target_module}, action={action_part}, params={{ {param_kv} }}"
        return f"[Direct] module={target_module}, action={action_part}, params={{}}"
    
    # ============ 智能线步骤实现 ============
    
    async def _execute_rag_retrieval_1(
        self,
        user_input: str,
        context: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行第一次RAG检索（理解需求）"""
        step_start = datetime.utcnow()
        
        try:
            # 调用RAG服务检索
            knowledge_items = await self.rag_service.retrieve(
                query=user_input,
                top_k=5,
                context=context,
            )
            
            # 理解用户意图
            intent_understanding = await self.rag_service.understand_intent(user_input)
            
            retrieval_input = {
                "query": user_input,
                "top_k": 5,
                "context_keys": list((context or {}).keys()),
                "workflow_id": workflow_id,
            }
            source_summary = {
                "total_results": len(knowledge_items),
                "sources": list(
                    {
                        item.get("source", "unknown")
                        for item in knowledge_items or []
                    }
                ),
            }
            result_data = {
                "knowledge_items": knowledge_items,
                "intent_understanding": intent_understanding,
                "retrieval_input": retrieval_input,
                "retrieval_stats": source_summary,
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RAG_RETRIEVAL_1,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"第一次RAG检索失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RAG_RETRIEVAL_1,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_expert_routing_1(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行第一次专家路由（选择专家和模块）"""
        step_start = datetime.utcnow()
        
        try:
            # 构建RAG结果格式
            rag_result_formatted = {
                "knowledge": rag_result.get("knowledge_items", []),
                "understanding": rag_result.get("intent_understanding", {}),
            }
            
            # 调用专家路由器
            expert_info = await self.expert_router.route(
                user_input=user_input,
                rag_result=rag_result_formatted,
            )
            
            result_data = {
                "expert": expert_info.get("expert"),
                "domain": expert_info.get("domain"),
                "module": expert_info.get("module"),
                "confidence": expert_info.get("confidence"),
                "intent": expert_info.get("intent"),
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.EXPERT_ROUTING_1,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"第一次专家路由失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.EXPERT_ROUTING_1,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_module_execution(
        self,
        user_input: str,
        expert_info: Dict[str, Any],
        rag_result: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行模块功能"""
        step_start = datetime.utcnow()
        
        try:
            # 构建上下文（包含RAG检索结果）
            context = {
                "rag_result": rag_result,
                "expert_info": expert_info,
                "workflow_id": workflow_id,
            }
            
            # 调用模块执行器
            execution_result = await self.module_executor.execute(
                expert=expert_info,
                input=user_input,
                context=context,
            )
            
            result_data = {
                "module": execution_result.get("module"),
                "expert": execution_result.get("expert"),
                "result": execution_result.get("result"),
                "success": execution_result.get("success", False),
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.MODULE_EXECUTION,
                success=execution_result.get("success", False),
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"模块执行失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.MODULE_EXECUTION,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_expert_routing_2(
        self,
        user_input: str,
        module_result: Dict[str, Any],
        expert_info: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行第二次专家路由（后处理）"""
        step_start = datetime.utcnow()
        
        try:
            # 使用专家系统对模块执行结果进行后处理
            if self.expert_system:
                # 构建查询（基于用户输入和模块结果）
                query = f"{user_input} 执行结果: {module_result.get('result', {})}"
                
                # 分析查询
                analysis = self.expert_system.analyze_query(query)
                
                # 生成专家级答案（包含后处理建议）
                expert_answer = await self.expert_system.generate_expert_answer(
                    query=query,
                    analysis=analysis,
                    context=[module_result.get("result", {})],
                )
                
                result_data = {
                    "expert_analysis": {
                        "domain": analysis.domain.value,
                        "complexity": analysis.complexity,
                        "confidence": analysis.confidence,
                    },
                    "expert_answer": {
                        "answer": expert_answer.answer,
                        "confidence": expert_answer.confidence,
                        "recommendations": expert_answer.recommendations,
                        "related_concepts": expert_answer.related_concepts,
                    },
                }
            else:
                # 如果没有专家系统，返回简单结果
                result_data = {
                    "expert_analysis": {
                        "domain": expert_info.get("domain", "general"),
                        "complexity": 0.5,
                        "confidence": 0.7,
                    },
                    "expert_answer": {
                        "answer": "模块执行完成",
                        "confidence": 0.7,
                        "recommendations": [],
                        "related_concepts": [],
                    },
                }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.EXPERT_ROUTING_2,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"第二次专家路由失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.EXPERT_ROUTING_2,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_rag_retrieval_2(
        self,
        user_input: str,
        module_result: Dict[str, Any],
        expert_info: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行第二次RAG检索（整合历史经验和最佳实践）⭐T002增强"""
        step_start = datetime.utcnow()
        
        try:
            # 构建执行结果（用于第2次RAG检索）
            execution_result = {
                "module": module_result.get("module"),
                "type": module_result.get("result", {}).get("type", "unknown"),
                "result": module_result.get("result", {}),
                "success": module_result.get("success", False),
            }
            
            # 使用新的 retrieve_for_integration 方法（T002增强）
            # 该方法会同时查找类似案例和最佳实践
            integration_knowledge = await self.rag_service.retrieve_for_integration(
                execution_result=execution_result,
                top_k=5,
                context={
                    "user_input": user_input,
                    "expert_domain": expert_info.get("domain", "general"),
                },
                filter_type="experience",
            )
            
            # 分离类似案例和最佳实践
            similar_cases = [
                item for item in integration_knowledge
                if item.get("type") == "similar_case"
            ]
            best_practices = [
                item for item in integration_knowledge
                if item.get("type") == "best_practice"
            ]
            
            result_data = {
                "similar_cases": similar_cases,
                "best_practices": best_practices,
                "integration_knowledge": integration_knowledge,  # 完整结果
                "module_result": module_result,
                "retrieval_method": "retrieve_for_integration",  # 标记使用的方法
                "retrieval_input": {
                    "execution_result_snapshot": execution_result,
                    "context": {
                        "user_input": user_input,
                        "expert_domain": expert_info.get("domain", "general"),
                    },
                    "filters": ["experience"],
                },
                "retrieval_stats": {
                    "total_results": len(integration_knowledge),
                    "similar_case_count": len(similar_cases),
                    "best_practice_count": len(best_practices),
                },
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RAG_RETRIEVAL_2,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"第二次RAG检索失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RAG_RETRIEVAL_2,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_response_generation(
        self,
        user_input: str,
        rag_result_1: Dict[str, Any],
        expert_info: Dict[str, Any],
        module_result: Dict[str, Any],
        expert_routing_2: Optional[Dict[str, Any]],
        rag_result_2: Optional[Dict[str, Any]],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """生成最终响应"""
        step_start = datetime.utcnow()
        
        try:
            # 综合所有信息生成响应
            response_parts = []
            
            # 1. 模块执行结果
            module_response = module_result.get("result", {})
            if isinstance(module_response, dict):
                message = module_response.get("message", "执行完成")
                response_parts.append(f"**执行结果**: {message}")
                
                # 添加数据（如果有）
                if "data" in module_response:
                    response_parts.append(f"\n**数据**: {module_response['data']}")
                elif "knowledge" in module_response:
                    knowledge = module_response["knowledge"]
                    if knowledge:
                        response_parts.append(f"\n**相关知识**: {len(knowledge)}条")
            else:
                response_parts.append(f"**执行结果**: {str(module_response)}")
            
            # 2. 专家建议（如果有）
            if expert_routing_2:
                expert_answer = expert_routing_2.get("expert_answer", {})
                recommendations = expert_answer.get("recommendations", [])
                if recommendations:
                    response_parts.append(f"\n**专家建议**:")
                    for rec in recommendations:
                        response_parts.append(f"- {rec}")
            
            # 3. 历史案例和最佳实践（如果有）
            if rag_result_2:
                similar_cases = rag_result_2.get("similar_cases", [])
                best_practices = rag_result_2.get("best_practices", [])
                
                if similar_cases:
                    response_parts.append(f"\n**类似案例**: 找到{len(similar_cases)}个历史案例")
                
                if best_practices:
                    response_parts.append(f"\n**最佳实践**: 找到{len(best_practices)}条相关经验")
            
            # 组合响应
            response = "\n".join(response_parts) if response_parts else "执行完成"
            
            result_data = {
                "response": response,
                "components": {
                    "module_result": module_result,
                    "expert_routing_2": expert_routing_2,
                    "rag_result_2": rag_result_2,
                },
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RESPONSE_GENERATION,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"响应生成失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RESPONSE_GENERATION,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    # ============ 直接操作线步骤实现 ============
    
    async def _execute_direct_module_execution(
        self,
        user_input: str,
        target_module: str,
        context: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """执行直接模块执行"""
        step_start = datetime.utcnow()
        
        try:
            # 构建专家信息（基于目标模块）
            expert_info = {
                "expert": f"{target_module}_expert",
                "module": target_module,
                "domain": target_module,
            }
            
            # 调用模块执行器
            execution_result = await self.module_executor.execute(
                expert=expert_info,
                input=user_input,
                context=context,
            )
            
            result_data = {
                "module": execution_result.get("module"),
                "expert": execution_result.get("expert"),
                "result": execution_result.get("result"),
                "success": execution_result.get("success", False),
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.MODULE_EXECUTION,
                success=execution_result.get("success", False),
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"直接模块执行失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.MODULE_EXECUTION,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    async def _execute_direct_response_generation(
        self,
        user_input: str,
        module_result: Dict[str, Any],
        workflow_id: str,
    ) -> WorkflowStepResult:
        """生成直接操作线的响应"""
        step_start = datetime.utcnow()
        
        try:
            # 从模块结果生成响应
            module_response = module_result.get("result", {})
            if isinstance(module_response, dict):
                message = module_response.get("message", "执行完成")
                response = f"**执行结果**: {message}"
                
                # 添加数据（如果有）
                if "data" in module_response:
                    response += f"\n**数据**: {module_response['data']}"
            else:
                response = f"**执行结果**: {str(module_response)}"
            
            result_data = {
                "response": response,
                "module_result": module_result,
            }
            
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RESPONSE_GENERATION,
                success=True,
                data=result_data,
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
            
        except Exception as e:
            logger.error(f"直接响应生成失败: {e}", exc_info=True)
            duration = (datetime.utcnow() - step_start).total_seconds()
            
            return WorkflowStepResult(
                step_type=WorkflowStepType.RESPONSE_GENERATION,
                success=False,
                error=str(e),
                duration=duration,
                completed_at=datetime.utcnow().isoformat() + "Z",
            )
    
    # ============ 辅助方法 ============
    
    async def get_execution_history(
        self,
        workflow_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[WorkflowExecutionResult]:
        """获取执行历史"""
        if workflow_id:
            result = self.execution_history.get(workflow_id)
            return [result] if result else []
        
        # 返回最近的执行历史
        results = list(self.execution_history.values())
        results.sort(key=lambda x: x.total_duration, reverse=True)
        return results[:limit]
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        return await self.orchestrator.get_workflow(workflow_id)


# 单例模式
_workflow_engine: Optional[DualLoopWorkflowEngine] = None


def get_dual_loop_workflow_engine(
    workflow_orchestrator: Optional[WorkflowOrchestrator] = None,
    rag_service: Optional[RAGServiceAdapter] = None,
    expert_router: Optional[ExpertRouter] = None,
    module_executor: Optional[ModuleExecutor] = None,
    expert_system: Optional[Any] = None,
    workflow_observability: Optional[WorkflowObservability] = None,
) -> DualLoopWorkflowEngine:
    """获取双线闭环工作流引擎单例"""
    global _workflow_engine
    if _workflow_engine is None:
        _workflow_engine = DualLoopWorkflowEngine(
            workflow_orchestrator=workflow_orchestrator,
            rag_service=rag_service,
            expert_router=expert_router,
            module_executor=module_executor,
            expert_system=expert_system,
            workflow_observability=workflow_observability,
        )
    return _workflow_engine

