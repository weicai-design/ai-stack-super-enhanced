#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源调度与交互提示管理器
P2-303: 实现资源调度与交互提示
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"


class HintType(str, Enum):
    """提示类型"""
    INFO = "info"  # 信息提示
    WARNING = "warning"  # 警告提示
    ERROR = "error"  # 错误提示
    SUCCESS = "success"  # 成功提示
    SUGGESTION = "suggestion"  # 建议提示


@dataclass
class ResourceAllocation:
    """资源分配"""
    allocation_id: str
    task_id: str
    resource_type: ResourceType
    allocated_amount: float
    requested_amount: float
    priority: int
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["resource_type"] = self.resource_type.value
        return data


@dataclass
class InteractionHint:
    """交互提示"""
    hint_id: str
    hint_type: HintType
    title: str
    message: str
    action: Optional[str] = None  # 建议的操作
    resource_context: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["hint_type"] = self.hint_type.value
        return data


class ResourceSchedulerWithHints:
    """
    资源调度与交互提示管理器
    
    功能：
    1. 智能资源调度
    2. 资源使用监控
    3. 交互提示生成
    4. 资源优化建议
    """
    
    def __init__(self):
        self.allocations: Dict[str, ResourceAllocation] = {}
        self.hints: List[InteractionHint] = []
        self.resource_status: Dict[str, Any] = {
            "cpu": {"total": 100.0, "used": 0.0, "available": 100.0},
            "memory": {"total": 100.0, "used": 0.0, "available": 100.0},
            "disk": {"total": 100.0, "used": 0.0, "available": 100.0},
            "network": {"total": 100.0, "used": 0.0, "available": 100.0},
        }
        
        logger.info("资源调度与交互提示管理器初始化完成")
    
    async def allocate_resource(
        self,
        task_id: str,
        resource_type: ResourceType,
        requested_amount: float,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ResourceAllocation:
        """
        分配资源
        
        Args:
            task_id: 任务ID
            resource_type: 资源类型
            requested_amount: 请求数量
            priority: 优先级 (1-10)
            metadata: 元数据
            
        Returns:
            资源分配对象
        """
        allocation_id = f"alloc_{uuid4()}"
        
        # 检查资源可用性
        available = self.resource_status[resource_type.value]["available"]
        
        if requested_amount > available:
            # 资源不足，生成提示
            hint = InteractionHint(
                hint_id=f"hint_{uuid4()}",
                hint_type=HintType.WARNING,
                title="资源不足",
                message=f"{resource_type.value.upper()}资源不足，请求{requested_amount}%，可用{available:.1f}%",
                action="建议降低资源需求或等待其他任务完成",
                resource_context={
                    "resource_type": resource_type.value,
                    "requested": requested_amount,
                    "available": available,
                },
            )
            self.hints.append(hint)
            
            # 尝试分配可用资源
            allocated_amount = min(requested_amount, available)
        else:
            allocated_amount = requested_amount
        
        # 创建分配记录
        allocation = ResourceAllocation(
            allocation_id=allocation_id,
            task_id=task_id,
            resource_type=resource_type,
            allocated_amount=allocated_amount,
            requested_amount=requested_amount,
            priority=priority,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {},
        )
        
        self.allocations[allocation_id] = allocation
        
        # 更新资源状态
        self.resource_status[resource_type.value]["used"] += allocated_amount
        self.resource_status[resource_type.value]["available"] -= allocated_amount
        
        # 检查资源使用率，生成提示
        await self._check_resource_usage(resource_type)
        
        logger.info(f"分配资源: {allocation_id} - {resource_type.value} {allocated_amount}%")
        
        return allocation
    
    async def release_resource(self, allocation_id: str) -> bool:
        """
        释放资源
        
        Args:
            allocation_id: 分配ID
            
        Returns:
            是否成功
        """
        if allocation_id not in self.allocations:
            return False
        
        allocation = self.allocations[allocation_id]
        resource_type = allocation.resource_type.value
        
        # 更新资源状态
        self.resource_status[resource_type]["used"] -= allocation.allocated_amount
        self.resource_status[resource_type]["available"] += allocation.allocated_amount
        
        # 删除分配记录
        del self.allocations[allocation_id]
        
        logger.info(f"释放资源: {allocation_id}")
        
        return True
    
    async def _check_resource_usage(self, resource_type: ResourceType):
        """检查资源使用率并生成提示"""
        status = self.resource_status[resource_type.value]
        usage_percent = (status["used"] / status["total"]) * 100
        
        if usage_percent > 90:
            # 资源使用率过高
            hint = InteractionHint(
                hint_id=f"hint_{uuid4()}",
                hint_type=HintType.WARNING,
                title=f"{resource_type.value.upper()}资源使用率过高",
                message=f"当前使用率{usage_percent:.1f}%，建议优化资源分配",
                action="考虑释放不必要的资源或扩展资源容量",
                resource_context={
                    "resource_type": resource_type.value,
                    "usage_percent": usage_percent,
                },
            )
            self.hints.append(hint)
        elif usage_percent < 20:
            # 资源使用率过低
            hint = InteractionHint(
                hint_id=f"hint_{uuid4()}",
                hint_type=HintType.SUGGESTION,
                title=f"{resource_type.value.upper()}资源使用率较低",
                message=f"当前使用率{usage_percent:.1f}%，资源充足",
                action="可以考虑增加任务负载以提高资源利用率",
                resource_context={
                    "resource_type": resource_type.value,
                    "usage_percent": usage_percent,
                },
            )
            self.hints.append(hint)
    
    def generate_hint(
        self,
        hint_type: HintType,
        title: str,
        message: str,
        action: Optional[str] = None,
        resource_context: Optional[Dict[str, Any]] = None,
    ) -> InteractionHint:
        """
        生成交互提示
        
        Args:
            hint_type: 提示类型
            title: 标题
            message: 消息
            action: 建议操作
            resource_context: 资源上下文
            
        Returns:
            交互提示对象
        """
        hint = InteractionHint(
            hint_id=f"hint_{uuid4()}",
            hint_type=hint_type,
            title=title,
            message=message,
            action=action,
            resource_context=resource_context,
        )
        
        self.hints.append(hint)
        
        logger.info(f"生成提示: {hint_type.value} - {title}")
        
        return hint
    
    def get_resource_status(self) -> Dict[str, Any]:
        """获取资源状态"""
        return {
            "status": self.resource_status,
            "total_allocations": len(self.allocations),
            "active_hints": len([h for h in self.hints if not h.acknowledged]),
        }
    
    def get_hints(
        self,
        hint_type: Optional[HintType] = None,
        unacknowledged_only: bool = False,
        limit: int = 50,
    ) -> List[InteractionHint]:
        """获取交互提示"""
        hints = list(self.hints)
        
        if hint_type:
            hints = [h for h in hints if h.hint_type == hint_type]
        if unacknowledged_only:
            hints = [h for h in hints if not h.acknowledged]
        
        # 按时间倒序
        hints.sort(key=lambda h: h.timestamp, reverse=True)
        
        return hints[:limit]
    
    def acknowledge_hint(self, hint_id: str) -> bool:
        """确认提示"""
        hint = next((h for h in self.hints if h.hint_id == hint_id), None)
        if hint:
            hint.acknowledged = True
            return True
        return False
    
    def get_scheduling_suggestions(self) -> List[Dict[str, Any]]:
        """获取调度建议"""
        suggestions = []
        
        # 分析资源使用情况
        for resource_type, status in self.resource_status.items():
            usage_percent = (status["used"] / status["total"]) * 100
            
            if usage_percent > 80:
                suggestions.append({
                    "type": "resource_optimization",
                    "resource": resource_type,
                    "message": f"{resource_type.upper()}资源使用率{usage_percent:.1f}%，建议优化",
                    "priority": "high",
                })
            elif usage_percent < 30:
                suggestions.append({
                    "type": "resource_utilization",
                    "resource": resource_type,
                    "message": f"{resource_type.upper()}资源使用率{usage_percent:.1f}%，可以增加负载",
                    "priority": "low",
                })
        
        return suggestions


_resource_scheduler: Optional[ResourceSchedulerWithHints] = None


def get_resource_scheduler() -> ResourceSchedulerWithHints:
    """获取资源调度器实例"""
    global _resource_scheduler
    if _resource_scheduler is None:
        _resource_scheduler = ResourceSchedulerWithHints()
    return _resource_scheduler

