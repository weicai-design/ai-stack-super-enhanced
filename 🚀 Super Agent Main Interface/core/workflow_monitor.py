"""
AI工作流完整监控系统
监控完整流程：用户→RAG→专家→模块→专家→RAG→用户
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4
from dataclasses import dataclass, field
from enum import Enum
import json

@dataclass
class WorkflowStep:
    """工作流步骤"""
    step_name: str
    step_type: str  # user_input, rag_retrieval, expert_routing, module_execution, expert_analysis, rag_integration, user_response
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class WorkflowMonitor:
    """
    AI工作流完整监控系统
    
    监控完整流程：
    1. 用户输入
    2. 第1次RAG检索（理解需求）
    3. AI专家路由和分析
    4. 调用模块执行
    5. 第2次RAG检索（整合知识）
    6. 专家综合生成回复
    7. 返回用户
    """
    
    def __init__(self, rag_service=None, resource_manager=None):
        self.rag_service = rag_service
        self.resource_manager = resource_manager
        self.workflows = []  # 完整工作流记录
        self.current_workflow = None
        self.step_times = {}  # 各步骤平均耗时统计
        self.system_events: List[Dict[str, Any]] = []  # 系统级事件（终端、安全等）
        
    async def start_workflow(self, user_input: str, context: Dict[str, Any] = None) -> str:
        """
        开始监控一个工作流
        
        Returns:
            workflow_id: 工作流ID
        """
        workflow_id = f"wf_{int(time.time() * 1000)}"
        self.current_workflow = {
            "workflow_id": workflow_id,
            "user_input": user_input,
            "context": context or {},
            "start_time": time.time(),
            "steps": [],
            "status": "running"
        }
        return workflow_id
    
    async def record_step(
        self,
        step_name: str,
        step_type: str,
        success: bool = True,
        error: Optional[str] = None,
        data: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """记录工作流步骤"""
        if not self.current_workflow:
            return
        
        step = WorkflowStep(
            step_name=step_name,
            step_type=step_type,
            start_time=time.time(),
            success=success,
            error=error,
            data=data or {},
            metadata=metadata or {}
        )
        
        self.current_workflow["steps"].append(step)
        
        # 记录步骤开始时间
        step_key = f"{step_type}_{step_name}"
        if step_key not in self.step_times:
            self.step_times[step_key] = []
    
    async def complete_step(self, step_name: str, success: bool = True, result: Any = None):
        """完成工作流步骤"""
        if not self.current_workflow:
            return
        
        # 找到最后一个匹配的步骤
        for step in reversed(self.current_workflow["steps"]):
            if step.step_name == step_name and step.end_time is None:
                step.end_time = time.time()
                step.duration = step.end_time - step.start_time
                step.success = success
                if result:
                    step.data["result"] = result
                
                # 更新统计
                step_key = f"{step.step_type}_{step_name}"
                if step_key not in self.step_times:
                    self.step_times[step_key] = []
                self.step_times[step_key].append(step.duration)
                
                break
    
    async def complete_workflow(self, response: str, response_time: float) -> Dict[str, Any]:
        """完成工作流"""
        if not self.current_workflow:
            return {}
        
        self.current_workflow["end_time"] = time.time()
        self.current_workflow["total_duration"] = self.current_workflow["end_time"] - self.current_workflow["start_time"]
        self.current_workflow["response"] = response
        self.current_workflow["response_time"] = response_time
        self.current_workflow["status"] = "completed"
        
        # 分析工作流
        analysis = await self._analyze_workflow(self.current_workflow)
        self.current_workflow["analysis"] = analysis
        
        # 保存工作流
        workflow_record = {
            **self.current_workflow,
            "steps": [
                {
                    "step_name": step.step_name,
                    "step_type": step.step_type,
                    "duration": step.duration,
                    "success": step.success,
                    "error": step.error,
                    "data": step.data,
                    "metadata": step.metadata
                }
                for step in self.current_workflow["steps"]
            ],
            "timestamp": datetime.now().isoformat()
        }
        
        self.workflows.append(workflow_record)
        
        # 如果工作流超过1000条，保留最近1000条
        if len(self.workflows) > 1000:
            self.workflows = self.workflows[-1000:]
        
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
            step_type = step.step_type
            duration = step.duration or 0
            
            if step_type not in step_analysis:
                step_analysis[step_type] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0,
                    "min_time": float('inf'),
                    "success_rate": 0,
                    "success_count": 0
                }
            
            stats = step_analysis[step_type]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["max_time"] = max(stats["max_time"], duration)
            stats["min_time"] = min(stats["min_time"], duration)
            
            if step.success:
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
                        "percentage": percentage,
                        "avg_time": stats["avg_time"],
                        "max_time": stats["max_time"]
                    })
        
        # 计算总体指标
        success_steps = sum(1 for step in steps if step.success)
        total_steps = len(steps)
        overall_success_rate = (success_steps / total_steps * 100) if total_steps > 0 else 0
        
        return {
            "step_analysis": step_analysis,
            "bottlenecks": bottlenecks,
            "overall_success_rate": overall_success_rate,
            "total_steps": total_steps,
            "successful_steps": success_steps,
            "total_duration": total_time,
            "performance_score": self._calculate_performance_score(workflow, step_analysis)
        }
    
    def _calculate_performance_score(self, workflow: Dict, step_analysis: Dict) -> float:
        """计算性能评分（0-100）"""
        total_time = workflow.get("total_duration", 0)
        target_time = 2.0  # 2秒目标
        
        # 时间评分（60%权重）
        if total_time <= target_time:
            time_score = 100
        elif total_time <= target_time * 2:
            time_score = 100 - ((total_time - target_time) / target_time * 30)
        else:
            time_score = max(0, 70 - ((total_time - target_time * 2) / target_time * 20))
        
        # 成功率评分（40%权重）
        success_rate = sum(
            stats["success_rate"] 
            for stats in step_analysis.values()
        ) / len(step_analysis) if step_analysis else 100
        
        # 综合评分
        performance_score = time_score * 0.6 + success_rate * 0.4
        
        return round(performance_score, 2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.workflows:
            return {
                "total_workflows": 0,
                "status": "idle"
            }
        
        recent_workflows = self.workflows[-100:]  # 最近100条
        
        # 计算平均响应时间
        avg_response_time = sum(
            w.get("response_time", 0) 
            for w in recent_workflows 
            if "response_time" in w
        ) / len(recent_workflows) if recent_workflows else 0
        
        # 计算成功率
        successful_workflows = sum(
            1 for w in recent_workflows 
            if w.get("status") == "completed" and w.get("analysis", {}).get("overall_success_rate", 0) > 80
        )
        success_rate = (successful_workflows / len(recent_workflows) * 100) if recent_workflows else 0
        
        # 获取主要瓶颈
        all_bottlenecks = []
        for w in recent_workflows:
            bottlenecks = w.get("analysis", {}).get("bottlenecks", [])
            all_bottlenecks.extend(bottlenecks)
        
        # 统计瓶颈频率
        bottleneck_freq = {}
        for b in all_bottlenecks:
            step_type = b.get("step_type", "unknown")
            bottleneck_freq[step_type] = bottleneck_freq.get(step_type, 0) + 1
        
        # 获取最常见的瓶颈
        top_bottlenecks = sorted(
            bottleneck_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "total_workflows": len(self.workflows),
            "recent_workflows": len(recent_workflows),
            "avg_response_time": round(avg_response_time, 3),
            "success_rate": round(success_rate, 2),
            "top_bottlenecks": [
                {"step_type": step_type, "frequency": freq}
                for step_type, freq in top_bottlenecks
            ],
            "status": "active",
            "last_update": datetime.now().isoformat()
        }
    
    def get_recent_workflows(self, limit: int = 10) -> List[Dict]:
        """获取最近的工作流记录"""
        return self.workflows[-limit:] if self.workflows else []

    async def record_system_event(
        self,
        event_type: str,
        source: str,
        severity: str = "info",
        success: bool = True,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """记录系统级事件（终端命令、安全告警等）"""
        event = {
            "event_id": f"evt_{uuid4()}",
            "event_type": event_type,
            "source": source,
            "severity": severity,
            "success": success,
            "data": data or {},
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.system_events.append(event)

        if len(self.system_events) > 500:
            self.system_events = self.system_events[-500:]

        return event

    def get_recent_system_events(
        self,
        limit: int = 50,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取系统级事件"""
        events = self.system_events
        if event_type:
            events = [event for event in events if event.get("event_type") == event_type]
        return events[-limit:][::-1]  # 返回按时间倒序排列

    def get_system_event_summary(
        self,
        event_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取系统级事件的汇总信息"""
        events = self.get_recent_system_events(limit=100, event_type=event_type)
        if not events:
            return {
                "total": 0,
                "success_rate": 100.0,
                "recent_event": None
            }

        success_count = sum(1 for event in events if event.get("success"))
        recent_event = events[0] if events else None
        return {
            "total": len(events),
            "success_rate": round(success_count / len(events) * 100, 2),
            "recent_event": recent_event
        }







