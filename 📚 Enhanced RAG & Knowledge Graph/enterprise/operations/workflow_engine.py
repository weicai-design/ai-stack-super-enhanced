"""
流程引擎
Workflow Engine

提供流程定义、执行、监控的核心引擎

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import Workflow, WorkflowStep, BusinessProcess, ProcessStatus

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """流程引擎"""
    
    def __init__(self):
        """初始化流程引擎"""
        logger.info("✅ 流程引擎已初始化")
    
    def execute_workflow(
        self,
        workflow: Workflow,
        process: BusinessProcess
    ) -> BusinessProcess:
        """
        执行工作流程
        
        Args:
            workflow: 工作流定义
            process: 业务流程实例
        
        Returns:
            更新后的流程实例
        """
        if not workflow.steps:
            raise ValueError("工作流没有步骤")
        
        # 开始执行
        process.status = ProcessStatus.IN_PROGRESS
        process.started_at = datetime.now()
        
        # 执行当前步骤
        current_step = workflow.steps[process.current_step]
        
        logger.info(f"执行流程 {workflow.name} 步骤 {current_step.name}")
        
        # 更新步骤状态
        current_step.status = ProcessStatus.IN_PROGRESS
        
        return process
    
    def complete_step(
        self,
        workflow: Workflow,
        process: BusinessProcess,
        step_result: Optional[Dict[str, Any]] = None
    ) -> BusinessProcess:
        """
        完成当前步骤
        
        Args:
            workflow: 工作流定义
            process: 业务流程实例
            step_result: 步骤执行结果
        
        Returns:
            更新后的流程实例
        """
        if process.current_step >= len(workflow.steps):
            raise ValueError("已经是最后一个步骤")
        
        # 标记当前步骤完成
        current_step = workflow.steps[process.current_step]
        current_step.status = ProcessStatus.COMPLETED
        
        # 保存结果
        if step_result:
            if "step_results" not in process.data:
                process.data["step_results"] = []
            process.data["step_results"].append({
                "step": current_step.name,
                "result": step_result,
                "completed_at": datetime.now().isoformat()
            })
        
        # 移动到下一步
        process.current_step += 1
        
        # 检查是否完成全部流程
        if process.current_step >= len(workflow.steps):
            process.status = ProcessStatus.COMPLETED
            process.completed_at = datetime.now()
            logger.info(f"流程 {workflow.name} 已完成")
        else:
            # 开始下一步
            next_step = workflow.steps[process.current_step]
            next_step.status = ProcessStatus.IN_PROGRESS
            logger.info(f"进入下一步: {next_step.name}")
        
        return process
    
    def block_process(
        self,
        process: BusinessProcess,
        reason: str
    ) -> BusinessProcess:
        """
        阻塞流程
        
        Args:
            process: 业务流程实例
            reason: 阻塞原因
        
        Returns:
            更新后的流程实例
        """
        process.status = ProcessStatus.BLOCKED
        process.data["blocked_reason"] = reason
        process.data["blocked_at"] = datetime.now().isoformat()
        
        logger.warning(f"流程 {process.id} 被阻塞: {reason}")
        
        return process
    
    def resume_process(
        self,
        process: BusinessProcess
    ) -> BusinessProcess:
        """
        恢复流程
        
        Args:
            process: 业务流程实例
        
        Returns:
            更新后的流程实例
        """
        if process.status != ProcessStatus.BLOCKED:
            raise ValueError("流程不是阻塞状态")
        
        process.status = ProcessStatus.IN_PROGRESS
        if "blocked_reason" in process.data:
            del process.data["blocked_reason"]
        if "blocked_at" in process.data:
            del process.data["blocked_at"]
        
        logger.info(f"流程 {process.id} 已恢复")
        
        return process
    
    def cancel_process(
        self,
        process: BusinessProcess,
        reason: str
    ) -> BusinessProcess:
        """
        取消流程
        
        Args:
            process: 业务流程实例
            reason: 取消原因
        
        Returns:
            更新后的流程实例
        """
        process.status = ProcessStatus.CANCELLED
        process.data["cancelled_reason"] = reason
        process.data["cancelled_at"] = datetime.now().isoformat()
        
        logger.info(f"流程 {process.id} 已取消: {reason}")
        
        return process
    
    def get_process_progress(
        self,
        workflow: Workflow,
        process: BusinessProcess
    ) -> Dict[str, Any]:
        """
        获取流程进度
        
        Args:
            workflow: 工作流定义
            process: 业务流程实例
        
        Returns:
            进度信息
        """
        total_steps = len(workflow.steps)
        completed_steps = process.current_step
        progress_percent = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # 当前步骤信息
        current_step = None
        if process.current_step < total_steps:
            step = workflow.steps[process.current_step]
            current_step = {
                "name": step.name,
                "description": step.description,
                "owner": step.owner,
                "status": step.status
            }
        
        return {
            "process_id": process.id,
            "workflow_name": workflow.name,
            "status": process.status,
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "current_step": process.current_step,
            "progress_percent": progress_percent,
            "current_step_info": current_step,
            "started_at": process.started_at.isoformat() if process.started_at else None,
            "completed_at": process.completed_at.isoformat() if process.completed_at else None
        }


# ==================== 导出 ====================

__all__ = [
    "WorkflowEngine"
]



























