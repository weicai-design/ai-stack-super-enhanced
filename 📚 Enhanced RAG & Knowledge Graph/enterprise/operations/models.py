"""
运营管理数据模型
Operations Management Models

版本: v1.0.0
"""

from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class ProcessStatus(str, Enum):
    """流程状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class WorkflowStep(BaseModel):
    """工作流步骤"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="步骤名称")
    description: str = Field("", description="步骤描述")
    order: int = Field(..., description="执行顺序")
    owner: Optional[str] = Field(None, description="负责人")
    duration_hours: float = Field(0, description="预计时长")
    status: ProcessStatus = Field(ProcessStatus.PENDING)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Workflow(BaseModel):
    """工作流程"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="租户ID")
    name: str = Field(..., description="流程名称")
    description: str = Field("", description="流程描述")
    steps: List[WorkflowStep] = Field(default_factory=list)
    kpis: Dict[str, Any] = Field(default_factory=dict, description="KPI指标")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class BusinessProcess(BaseModel):
    """业务流程实例"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="租户ID")
    workflow_id: str = Field(..., description="工作流ID")
    name: str = Field(..., description="流程名称")
    current_step: int = Field(0, description="当前步骤")
    status: ProcessStatus = Field(ProcessStatus.PENDING)
    data: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)


class Issue(BaseModel):
    """问题记录"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(..., description="租户ID")
    process_id: str = Field(..., description="流程ID")
    title: str = Field(..., description="问题标题")
    description: str = Field("", description="问题描述")
    severity: str = Field("medium", description="严重程度")
    status: str = Field("open", description="状态")
    resolution: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


class Dashboard(BaseModel):
    """运营看板"""
    tenant_id: str
    active_processes: int = 0
    completed_today: int = 0
    blocked_processes: int = 0
    open_issues: int = 0
    kpi_metrics: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)












