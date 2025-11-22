"""任务数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Any
from pydantic import BaseModel, Field
import uuid

class Task(BaseModel):
    """任务"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    description: str = ""
    status: str = "pending"
    priority: str = "medium"
    assignee: str | None = None
    due_date: datetime | None = None
    created_at: datetime = Field(default_factory=datetime.now)

class TaskPlan(BaseModel):
    """任务计划"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    name: str
    tasks: List[str] = Field(default_factory=list)
    schedule: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)

class TaskExecution(BaseModel):
    """任务执行"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    status: str
    result: Any = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: datetime | None = None


































