"""
任务编排器模块
"""

from typing import Dict, Any, List
from enum import Enum


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskOrchestrator:
    """任务编排器"""
    
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, task_data: Dict[str, Any]) -> str:
        """创建任务"""
        task_id = f"task_{len(self.tasks) + 1}"
        self.tasks[task_id] = {
            "id": task_id,
            "data": task_data,
            "status": TaskStatus.PENDING
        }
        return task_id
    
    def get_task_status(self, task_id: str) -> TaskStatus:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        return task.get("status", TaskStatus.FAILED) if task else TaskStatus.FAILED