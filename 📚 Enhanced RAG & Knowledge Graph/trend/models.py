"""趋势分析数据模型"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List
from pydantic import BaseModel, Field
import uuid

class TrendData(BaseModel):
    """趋势数据"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    source: str
    category: str
    title: str
    content: str
    url: str = ""
    collected_at: datetime = Field(default_factory=datetime.now)

class Analysis(BaseModel):
    """分析结果"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    topic: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    created_at: datetime = Field(default_factory=datetime.now)

class Report(BaseModel):
    """分析报告"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    title: str
    content: str
    report_type: str
    generated_at: datetime = Field(default_factory=datetime.now)


































