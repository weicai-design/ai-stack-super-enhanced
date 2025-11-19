"""
任务管理器
世界级任务管理功能
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    """任务状态"""
    CAPTURED = "captured"
    CLASSIFIED = "classified"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    COMPLETED = "completed"
    REVIEW_PENDING = "review_pending"
    REVIEWED = "reviewed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class TaskManager:
    """
    任务管理器
    
    功能：
    1. 任务CRUD操作
    2. 任务分类和标签
    3. 任务依赖关系
    4. 任务历史记录
    """
    
    def __init__(self):
        self.tasks = []
        self.task_counter = 0
        self.lifecycle_log: Dict[int, List[Dict[str, Any]]] = {}
        
    def create_task(
        self,
        title: str,
        description: str,
        source: str = "user",  # user, agent, memo
        priority: TaskPriority = TaskPriority.MEDIUM,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建任务"""
        self.task_counter += 1
        task = {
            "id": self.task_counter,
            "title": title,
            "description": description,
            "source": source,
            "priority": priority.value,
            "tags": tags or [],
            "dependencies": dependencies or [],
            "status": TaskStatus.CAPTURED.value,
            "needs_confirmation": source == "agent",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "metadata": metadata.copy() if metadata else {}
        }
        self.lifecycle_log[task["id"]] = [{
            "stage": TaskStatus.CAPTURED.value,
            "timestamp": task["created_at"],
            "note": "任务捕获"
        }]
        self.tasks.append(task)
        return task
    
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务"""
        return next((t for t in self.tasks if t["id"] == task_id), None)
    
    def update_task(self, task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新任务"""
        task = self.get_task(task_id)
        if task:
            updates_copy = updates.copy()
            metadata_updates = updates_copy.pop("metadata", None)
            if metadata_updates:
                merged_meta = task.get("metadata", {}).copy()
                merged_meta.update(metadata_updates)
                task["metadata"] = merged_meta
            task.update(updates_copy)
            task["updated_at"] = datetime.now().isoformat()
            if "status" in updates:
                self._log_lifecycle(task_id, updates["status"], updates.get("note"))
            return task
        return None

    def _log_lifecycle(self, task_id: int, stage: str, note: Optional[str] = None):
        log = self.lifecycle_log.setdefault(task_id, [])
        log.append({
            "stage": stage,
            "timestamp": datetime.now().isoformat(),
            "note": note
        })
    
    def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                self.tasks.pop(i)
                return True
        return False
    
    def get_tasks(
        self,
        status: Optional[str] = None,
        source: Optional[str] = None,
        priority: Optional[int] = None,
        needs_confirmation: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """获取任务列表"""
        filtered = self.tasks
        
        if status:
            filtered = [t for t in filtered if t.get("status") == status]
        
        if source:
            filtered = [t for t in filtered if t.get("source") == source]
        
        if priority:
            filtered = [t for t in filtered if t.get("priority") >= priority]
        
        if needs_confirmation is not None:
            filtered = [t for t in filtered if t.get("needs_confirmation") == needs_confirmation]
        
        # 按优先级和创建时间排序
        filtered.sort(key=lambda x: (-x.get("priority", 0), x.get("created_at", "")))
        
        return filtered
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total": len(self.tasks),
            "by_status": {
                status.value: len([t for t in self.tasks if t.get("status") == status.value])
                for status in TaskStatus
            },
            "by_source": {
                source: len([t for t in self.tasks if t.get("source") == source])
                for source in ["user", "agent", "memo"]
            },
            "needs_confirmation": len([t for t in self.tasks if t.get("needs_confirmation")]),
            "by_priority": {
                priority.value: len([t for t in self.tasks if t.get("priority") == priority.value])
                for priority in TaskPriority
            }
        }

