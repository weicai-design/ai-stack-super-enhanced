#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强工作流监控系统
P0-002: 详细监控双RAG检索、专家路由、模块执行等完整AI工作流
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class WorkflowStepType(str, Enum):
    """工作流步骤类型"""
    USER_INPUT = "user_input"
    RAG_RETRIEVAL_1 = "rag_retrieval_1"
    EXPERT_ROUTING = "expert_routing"
    MODULE_EXECUTION = "module_execution"
    RAG_RETRIEVAL_2 = "rag_retrieval_2"
    RESPONSE_GENERATION = "response_generation"
    USER_RESPONSE = "user_response"


@dataclass
class EnhancedWorkflowStep:
    """增强工作流步骤"""
    step_id: str
    step_name: str
    step_type: WorkflowStepType
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_type": self.step_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "data": self.data,
            "metadata": self.metadata,
        }


class EnhancedWorkflowMonitor:
    """
    增强工作流监控系统
    
    监控完整AI工作流：
    1. 用户输入
    2. 第1次RAG检索（理解需求）
    3. 专家路由
    4. 模块执行
    5. 第2次RAG检索（整合经验知识）
    6. 响应生成
    7. 返回用户
    """
    
    def __init__(
        self,
        rag_service=None,
        resource_manager=None,
        causal_analyzer=None,
        max_workflows: int = 1000,
    ):
        self.rag_service = rag_service
        self.resource_manager = resource_manager
        self.causal_analyzer = causal_analyzer
        self.max_workflows = max_workflows
        
        # 工作流存储
        self.workflows: List[Dict[str, Any]] = []
        self.current_workflow: Optional[Dict[str, Any]] = None
        
        # 统计
        self.stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "avg_response_time": 0.0,
            "step_times": {},
            "step_success_rates": {},
        }
    
    async def start_workflow(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        开始监控一个工作流
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            workflow_id: 工作流ID
        """
        workflow_id = f"wf_{uuid4()}"
        self.current_workflow = {
            "workflow_id": workflow_id,
            "user_input": user_input,
            "context": context or {},
            "start_time": time.time(),
            "steps": [],
            "status": "running",
            "rag1_result": None,
            "rag2_result": None,
            "expert_routing": None,
            "module_execution": None,
        }
        
        # 记录用户输入步骤
        await self.record_step(
            step_name="user_input",
            step_type=WorkflowStepType.USER_INPUT,
            data={"input": user_input, "context": context},
        )
        
        return workflow_id
    
    async def record_step(
        self,
        step_name: str,
        step_type: WorkflowStepType,
        success: bool = True,
        error: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        记录工作流步骤
        
        Args:
            step_name: 步骤名称
            step_type: 步骤类型
            success: 是否成功
            error: 错误信息
            data: 步骤数据
            metadata: 元数据
            
        Returns:
            step_id: 步骤ID
        """
        if not self.current_workflow:
            return ""
        
        step_id = f"step_{uuid4()}"
        step = EnhancedWorkflowStep(
            step_id=step_id,
            step_name=step_name,
            step_type=step_type,
            start_time=time.time(),
            success=success,
            error=error,
            data=data or {},
            metadata=metadata or {},
        )
        
        self.current_workflow["steps"].append(step)
        
        # 特殊处理：保存关键步骤的结果
        if step_type == WorkflowStepType.RAG_RETRIEVAL_1:
            self.current_workflow["rag1_result"] = data
        elif step_type == WorkflowStepType.RAG_RETRIEVAL_2:
            self.current_workflow["rag2_result"] = data
        elif step_type == WorkflowStepType.EXPERT_ROUTING:
            self.current_workflow["expert_routing"] = data
        elif step_type == WorkflowStepType.MODULE_EXECUTION:
            self.current_workflow["module_execution"] = data
        
        return step_id
    
    async def complete_step(
        self,
        step_name: str,
        success: bool = True,
        result: Optional[Any] = None,
        error: Optional[str] = None,
    ):
        """
        完成工作流步骤
        
        Args:
            step_name: 步骤名称
            success: 是否成功
            result: 步骤结果
            error: 错误信息
        """
        if not self.current_workflow:
            return
        
        # 找到最后一个匹配的步骤
        for step in reversed(self.current_workflow["steps"]):
            if step.step_name == step_name and step.end_time is None:
                step.end_time = time.time()
                step.duration = step.end_time - step.start_time
                step.success = success
                step.error = error
                
                if result:
                    step.data["result"] = result
                
                # 更新统计
                self._update_step_stats(step)
                
                break
    
    async def complete_workflow(
        self,
        response: str,
        response_time: float,
    ) -> Dict[str, Any]:
        """
        完成工作流
        
        Args:
            response: 最终响应
            response_time: 响应时间
            
        Returns:
            工作流记录
        """
        if not self.current_workflow:
            return {}
        
        self.current_workflow["end_time"] = time.time()
        self.current_workflow["total_duration"] = (
            self.current_workflow["end_time"] - self.current_workflow["start_time"]
        )
        self.current_workflow["response"] = response
        self.current_workflow["response_time"] = response_time
        self.current_workflow["status"] = "completed"
        
        # 分析工作流
        analysis = await self._analyze_workflow(self.current_workflow)
        self.current_workflow["analysis"] = analysis
        
        # 保存工作流
        workflow_record = {
            **self.current_workflow,
            "steps": [step.to_dict() for step in self.current_workflow["steps"]],
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        self.workflows.append(workflow_record)
        
        # 限制工作流数量
        if len(self.workflows) > self.max_workflows:
            self.workflows = self.workflows[-self.max_workflows:]
        
        # 更新统计
        self._update_workflow_stats(workflow_record)
        
        # 集成因果分析器（如果有）
        if self.causal_analyzer:
            try:
                await self.causal_analyzer.record_workflow_trace(
                    workflow_id=workflow_record.get("workflow_id"),
                    steps=workflow_record.get("steps", []),
                    metrics={
                        "total_duration": workflow_record.get("total_duration", 0),
                        "success": workflow_record.get("status") == "completed",
                        "bottlenecks": analysis.get("bottlenecks", []),
                        "errors": [
                            s for s in workflow_record.get("steps", [])
                            if not s.get("success", True)
                        ],
                    },
                )
            except Exception as e:
                logger.warning(f"因果分析器记录失败: {e}")
        
        result = workflow_record.copy()
        self.current_workflow = None
        
        return result
    
    async def _analyze_workflow(self, workflow: Dict) -> Dict[str, Any]:
        """分析工作流性能"""
        steps = workflow.get("steps", [])
        total_time = workflow.get("total_duration", 0)
        
        # 分析各步骤耗时
        step_analysis = {}
        for step in steps:
            if isinstance(step, EnhancedWorkflowStep):
                step_type = step.step_type.value
                duration = step.duration or 0
            else:
                step_type = step.get("step_type", "unknown")
                duration = step.get("duration", 0)
            
            if step_type not in step_analysis:
                step_analysis[step_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float("inf"),
                    "success_rate": 0,
                    "success_count": 0,
                }
            
            stats = step_analysis[step_type]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["max_time"] = max(stats["max_time"], duration)
            stats["min_time"] = min(stats["min_time"], duration)
            
            success = (
                step.success
                if isinstance(step, EnhancedWorkflowStep)
                else step.get("success", True)
            )
            if success:
                stats["success_count"] += 1
            stats["success_rate"] = stats["success_count"] / stats["count"] * 100
        
        # 识别瓶颈
        bottlenecks = []
        for step_type, stats in step_analysis.items():
            if total_time > 0:
                percentage = (stats["total_time"] / total_time) * 100
                if percentage > 30:  # 超过30%的步骤视为瓶颈
                    bottlenecks.append({
                        "step_type": step_type,
                        "percentage": round(percentage, 2),
                        "avg_time": round(stats["avg_time"], 3),
                        "max_time": round(stats["max_time"], 3),
                    })
        
        # 计算总体指标
        success_steps = sum(
            1
            for step in steps
            if (
                step.success
                if isinstance(step, EnhancedWorkflowStep)
                else step.get("success", True)
            )
        )
        total_steps = len(steps)
        overall_success_rate = (
            (success_steps / total_steps * 100) if total_steps > 0 else 0
        )
        
        # 双RAG检索分析
        rag_analysis = self._analyze_dual_rag(workflow)
        
        return {
            "step_analysis": step_analysis,
            "bottlenecks": bottlenecks,
            "overall_success_rate": round(overall_success_rate, 2),
            "total_steps": total_steps,
            "successful_steps": success_steps,
            "total_duration": round(total_time, 3),
            "performance_score": self._calculate_performance_score(
                workflow, step_analysis
            ),
            "rag_analysis": rag_analysis,
        }
    
    def _analyze_dual_rag(self, workflow: Dict) -> Dict[str, Any]:
        """分析双RAG检索"""
        rag1_result = workflow.get("rag1_result")
        rag2_result = workflow.get("rag2_result")
        
        rag1_knowledge_count = 0
        rag2_knowledge_count = 0
        
        if rag1_result:
            if isinstance(rag1_result, dict):
                knowledge = rag1_result.get("knowledge", [])
                if not knowledge:
                    knowledge = rag1_result.get("knowledge_items", [])
                rag1_knowledge_count = len(knowledge)
        
        if rag2_result:
            if isinstance(rag2_result, dict):
                experience = rag2_result.get("experience", [])
                similar_cases = rag2_result.get("similar_cases", [])
                best_practices = rag2_result.get("best_practices", [])
                rag2_knowledge_count = (
                    len(experience) + len(similar_cases) + len(best_practices)
                )
        
        return {
            "rag1_knowledge_count": rag1_knowledge_count,
            "rag2_knowledge_count": rag2_knowledge_count,
            "rag1_success": rag1_result is not None,
            "rag2_success": rag2_result is not None,
        }
    
    def _calculate_performance_score(
        self, workflow: Dict, step_analysis: Dict
    ) -> float:
        """计算性能评分（0-100）"""
        total_time = workflow.get("total_duration", 0)
        target_time = 2.0  # 2秒目标
        
        # 时间评分（60%权重）
        if total_time <= target_time:
            time_score = 100
        elif total_time <= target_time * 2:
            time_score = 100 - ((total_time - target_time) / target_time * 30)
        else:
            time_score = max(
                0, 70 - ((total_time - target_time * 2) / target_time * 20)
            )
        
        # 成功率评分（40%权重）
        success_rate = (
            sum(stats["success_rate"] for stats in step_analysis.values())
            / len(step_analysis)
            if step_analysis
            else 100
        )
        
        # 综合评分
        performance_score = time_score * 0.6 + success_rate * 0.4
        
        return round(performance_score, 2)
    
    def _update_step_stats(self, step: EnhancedWorkflowStep):
        """更新步骤统计"""
        step_type = step.step_type.value
        
        if step_type not in self.stats["step_times"]:
            self.stats["step_times"][step_type] = []
        self.stats["step_times"][step_type].append(step.duration or 0)
        
        if step_type not in self.stats["step_success_rates"]:
            self.stats["step_success_rates"][step_type] = {"success": 0, "total": 0}
        
        stats = self.stats["step_success_rates"][step_type]
        stats["total"] += 1
        if step.success:
            stats["success"] += 1
    
    def _update_workflow_stats(self, workflow: Dict):
        """更新工作流统计"""
        self.stats["total_workflows"] += 1
        
        if workflow.get("status") == "completed":
            self.stats["successful_workflows"] += 1
        else:
            self.stats["failed_workflows"] += 1
        
        response_time = workflow.get("response_time", 0)
        total = self.stats["total_workflows"]
        current_avg = self.stats["avg_response_time"]
        self.stats["avg_response_time"] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        recent_workflows = self.workflows[-100:] if self.workflows else []
        
        # 计算成功率
        success_rate = (
            (self.stats["successful_workflows"] / self.stats["total_workflows"] * 100)
            if self.stats["total_workflows"] > 0
            else 0
        )
        
        # 计算步骤平均时间
        step_avg_times = {}
        for step_type, times in self.stats["step_times"].items():
            if times:
                step_avg_times[step_type] = round(sum(times) / len(times), 3)
        
        # 计算步骤成功率
        step_success_rates = {}
        for step_type, rates in self.stats["step_success_rates"].items():
            if rates["total"] > 0:
                step_success_rates[step_type] = round(
                    rates["success"] / rates["total"] * 100, 2
                )
        
        return {
            "total_workflows": self.stats["total_workflows"],
            "successful_workflows": self.stats["successful_workflows"],
            "failed_workflows": self.stats["failed_workflows"],
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(self.stats["avg_response_time"], 3),
            "step_avg_times": step_avg_times,
            "step_success_rates": step_success_rates,
            "recent_workflows_count": len(recent_workflows),
        }
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict]:
        """获取最近的工作流记录"""
        return self.workflows[-limit:] if self.workflows else []

