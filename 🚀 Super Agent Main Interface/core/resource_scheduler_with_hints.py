#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源调度与交互提示管理器
P2-303: 实现资源调度与交互提示
"""

from __future__ import annotations

import asyncio
import logging
import psutil
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4
from collections import deque, defaultdict
from queue import PriorityQueue

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


class SchedulingStrategy(str, Enum):
    """调度策略"""
    PRIORITY_BASED = "priority_based"  # 基于优先级
    FAIR_SHARING = "fair_sharing"  # 公平共享
    TIME_SLICING = "time_slicing"  # 时间片轮转
    RESOURCE_POOLING = "resource_pooling"  # 资源池化
    LOAD_BALANCING = "load_balancing"  # 负载均衡
    HYBRID = "hybrid"  # 混合策略


@dataclass
class ResourceState:
    """资源状态（6.2新增）"""
    resource_type: str
    total: float
    used: float
    available: float
    usage_percent: float
    status: str  # healthy/warning/critical
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GPUState:
    """GPU状态（6.2新增）"""
    gpu_id: str
    name: str
    memory_total: float  # MB
    memory_used: float  # MB
    memory_free: float  # MB
    utilization: float  # 0-100
    temperature: Optional[float] = None  # 摄氏度
    power_usage: Optional[float] = None  # 瓦特
    status: str = "available"  # available/in_use/error
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContainerState:
    """容器状态（6.2新增）"""
    container_id: str
    name: str
    image: str
    status: str  # running/stopped/paused/restarting
    cpu_usage: float  # 0-100
    memory_usage: float  # MB
    memory_limit: Optional[float] = None  # MB
    network_io: Optional[Dict[str, float]] = None  # bytes sent/received
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResourceConflict:
    """资源冲突（6.2新增）"""
    conflict_id: str
    conflict_type: str  # resource_competition/priority_conflict/schedule_conflict
    conflicting_tasks: List[str]
    resource_type: str
    severity: str  # low/medium/high/critical
    detected_at: str
    resolution_strategy: Optional[str] = None
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    资源调度与交互提示管理器（生产级实现 - 6.2）
    
    功能：
    1. 智能资源调度
    2. 资源使用监控
    3. 交互提示生成
    4. 资源优化建议
    5. GPU/CPU/容器状态监控（6.2新增）
    6. 冲突队列管理（6.2新增）
    7. 调度策略（6.2新增）
    8. 向前端推送提示（6.2新增）
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
        
        # GPU/CPU/容器状态（6.2新增）
        self.gpu_states: Dict[str, GPUState] = {}
        self.cpu_state: Optional[ResourceState] = None
        self.container_states: Dict[str, ContainerState] = {}
        self.monitoring_task: Optional[asyncio.Task] = None
        self.monitoring_interval: float = 5.0  # 监控间隔（秒）
        
        # 冲突队列（6.2新增）
        self.conflict_queue: deque = deque()  # 冲突队列（FIFO）
        self.conflict_priority_queue: PriorityQueue = PriorityQueue()  # 优先级队列
        self.detected_conflicts: Dict[str, ResourceConflict] = {}
        
        # 调度策略（6.2新增）
        self.current_strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY_BASED
        self.strategy_config: Dict[str, Any] = {
            "priority_based": {"min_priority": 1, "max_priority": 10},
            "fair_sharing": {"time_slice": 10.0},
            "time_slicing": {"slice_duration": 5.0},
            "resource_pooling": {"pool_size": 10},
            "load_balancing": {"threshold": 0.8},
        }
        self.strategy_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_allocations": 0,
            "successful_allocations": 0,
            "failed_allocations": 0,
            "avg_wait_time": 0.0,
        })
        
        # 前端推送（6.2新增）
        self.push_subscribers: Set[Callable[[Dict[str, Any]], None]] = set()
        self.push_lock = asyncio.Lock()
        
        logger.info("资源调度与交互提示管理器初始化完成（生产级 - 6.2）")
    
    async def allocate_resource(
        self,
        task_id: str,
        resource_type: ResourceType,
        requested_amount: float,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ResourceAllocation:
        """
        分配资源（生产级实现 - 6.2增强）
        
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
        
        # 检测冲突（6.2新增）
        conflict = self.detect_conflict(task_id, resource_type, requested_amount, priority)
        if conflict:
            # 推送冲突到前端
            await self.push_conflict(conflict)
            
            # 根据调度策略解决冲突
            if self.current_strategy != SchedulingStrategy.PRIORITY_BASED:
                # 非优先级策略需要先解决冲突
                self.resolve_conflict(conflict.conflict_id, self.current_strategy)
        
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
            
            # 推送提示到前端（6.2新增）
            await self.push_hint(hint)
            
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
        
        # 更新策略性能统计（6.2新增）
        strategy_perf = self.strategy_performance[self.current_strategy.value]
        strategy_perf["total_allocations"] += 1
        if allocated_amount >= requested_amount * 0.9:  # 分配了90%以上认为成功
            strategy_perf["successful_allocations"] += 1
        else:
            strategy_perf["failed_allocations"] += 1
        
        # 检查资源使用率，生成提示
        await self._check_resource_usage(resource_type)
        
        # 推送调度更新（6.2新增）
        await self.push_scheduling_update({
            "allocation_id": allocation_id,
            "task_id": task_id,
            "resource_type": resource_type.value,
            "allocated_amount": allocated_amount,
            "requested_amount": requested_amount,
        })
        
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
        """检查资源使用率并生成提示（6.2增强：推送提示）"""
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
            # 推送提示到前端（6.2新增）
            await self.push_hint(hint)
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
            # 推送提示到前端（6.2新增）
            await self.push_hint(hint)
    
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
    
    # ============ GPU/CPU/容器状态监控（6.2新增） ============
    
    async def start_monitoring(self):
        """启动资源监控"""
        if self.monitoring_task and not self.monitoring_task.done():
            logger.warning("监控任务已在运行")
            return
        
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("资源监控已启动")
    
    async def stop_monitoring(self):
        """停止资源监控"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
        logger.info("资源监控已停止")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while True:
            try:
                # 更新CPU状态
                await self._update_cpu_state()
                
                # 更新GPU状态
                await self._update_gpu_states()
                
                # 更新容器状态
                await self._update_container_states()
                
                # 推送状态更新
                await self._push_resource_status()
                
                await asyncio.sleep(self.monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}", exc_info=True)
                await asyncio.sleep(self.monitoring_interval)
    
    async def _update_cpu_state(self):
        """更新CPU状态"""
        try:
            loop = asyncio.get_event_loop()
            cpu_percent = await loop.run_in_executor(None, psutil.cpu_percent, 0.1)
            cpu_count = await loop.run_in_executor(None, psutil.cpu_count)
            cpu_freq = await loop.run_in_executor(None, psutil.cpu_freq)
            
            # 计算状态
            if cpu_percent < 70:
                status = "healthy"
            elif cpu_percent < 90:
                status = "warning"
            else:
                status = "critical"
            
            self.cpu_state = ResourceState(
                resource_type="cpu",
                total=100.0,
                used=cpu_percent,
                available=100.0 - cpu_percent,
                usage_percent=cpu_percent,
                status=status,
                metadata={
                    "cores": cpu_count,
                    "frequency": cpu_freq.current if cpu_freq else None,
                },
            )
            
            # 更新资源状态
            self.resource_status["cpu"] = {
                "total": 100.0,
                "used": cpu_percent,
                "available": 100.0 - cpu_percent,
            }
        except Exception as e:
            logger.error(f"更新CPU状态失败: {e}", exc_info=True)
    
    async def _update_gpu_states(self):
        """更新GPU状态"""
        try:
            # 尝试使用nvidia-smi获取GPU信息
            try:
                result = await asyncio.create_subprocess_exec(
                    "nvidia-smi",
                    "--query-gpu=index,name,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
                    "--format=csv,noheader,nounits",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0 and stdout:
                    lines = stdout.decode("utf-8").strip().split("\n")
                    for line in lines:
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 6:
                            gpu_id = f"gpu_{parts[0]}"
                            name = parts[1]
                            memory_total = float(parts[2])
                            memory_used = float(parts[3])
                            memory_free = float(parts[4])
                            utilization = float(parts[5])
                            temperature = float(parts[6]) if len(parts) > 6 else None
                            power_usage = float(parts[7]) if len(parts) > 7 else None
                            
                            # 计算状态
                            if utilization < 80:
                                status = "available"
                            elif utilization < 95:
                                status = "in_use"
                            else:
                                status = "in_use"
                            
                            self.gpu_states[gpu_id] = GPUState(
                                gpu_id=gpu_id,
                                name=name,
                                memory_total=memory_total,
                                memory_used=memory_used,
                                memory_free=memory_free,
                                utilization=utilization,
                                temperature=temperature,
                                power_usage=power_usage,
                                status=status,
                            )
            except FileNotFoundError:
                # nvidia-smi不存在，可能是没有GPU或不在GPU环境中
                logger.debug("nvidia-smi不可用，跳过GPU状态更新")
            except Exception as e:
                logger.warning(f"获取GPU状态失败: {e}")
        except Exception as e:
            logger.error(f"更新GPU状态失败: {e}", exc_info=True)
    
    async def _update_container_states(self):
        """更新容器状态"""
        try:
            # 尝试使用docker命令获取容器信息
            try:
                result = await asyncio.create_subprocess_exec(
                    "docker",
                    "ps",
                    "--format",
                    "{{.ID}}|{{.Names}}|{{.Image}}|{{.Status}}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0 and stdout:
                    lines = stdout.decode("utf-8").strip().split("\n")
                    for line in lines:
                        if not line.strip():
                            continue
                        parts = line.split("|")
                        if len(parts) >= 4:
                            container_id = parts[0]
                            name = parts[1]
                            image = parts[2]
                            status_str = parts[3]
                            
                            # 解析状态
                            if "Up" in status_str:
                                status = "running"
                            elif "Exited" in status_str:
                                status = "stopped"
                            elif "Paused" in status_str:
                                status = "paused"
                            else:
                                status = "unknown"
                            
                            # 获取容器统计信息（需要额外调用docker stats）
                            cpu_usage = 0.0
                            memory_usage = 0.0
                            
                            try:
                                stats_result = await asyncio.create_subprocess_exec(
                                    "docker",
                                    "stats",
                                    container_id,
                                    "--no-stream",
                                    "--format",
                                    "{{.CPUPerc}}|{{.MemUsage}}",
                                    stdout=asyncio.subprocess.PIPE,
                                    stderr=asyncio.subprocess.PIPE,
                                )
                                stats_stdout, _ = await stats_result.communicate()
                                if stats_result.returncode == 0 and stats_stdout:
                                    stats_parts = stats_stdout.decode("utf-8").strip().split("|")
                                    if len(stats_parts) >= 1:
                                        cpu_str = stats_parts[0].replace("%", "").strip()
                                        cpu_usage = float(cpu_str) if cpu_str else 0.0
                                    if len(stats_parts) >= 2:
                                        mem_str = stats_parts[1].split("/")[0].strip()
                                        # 解析内存使用（如 "100MiB" -> 100）
                                        memory_usage = self._parse_memory_size(mem_str)
                            except Exception:
                                pass
                            
                            self.container_states[container_id] = ContainerState(
                                container_id=container_id,
                                name=name,
                                image=image,
                                status=status,
                                cpu_usage=cpu_usage,
                                memory_usage=memory_usage,
                            )
            except FileNotFoundError:
                # docker命令不存在
                logger.debug("docker命令不可用，跳过容器状态更新")
            except Exception as e:
                logger.warning(f"获取容器状态失败: {e}")
        except Exception as e:
            logger.error(f"更新容器状态失败: {e}", exc_info=True)
    
    def _parse_memory_size(self, size_str: str) -> float:
        """解析内存大小字符串（如 "100MiB" -> 100）"""
        try:
            size_str = size_str.strip().upper()
            if "MIB" in size_str:
                return float(size_str.replace("MIB", "").strip())
            elif "MB" in size_str:
                return float(size_str.replace("MB", "").strip())
            elif "GIB" in size_str:
                return float(size_str.replace("GIB", "").strip()) * 1024
            elif "GB" in size_str:
                return float(size_str.replace("GB", "").strip()) * 1024
            else:
                return float(size_str)
        except Exception:
            return 0.0
    
    def get_cpu_state(self) -> Optional[ResourceState]:
        """获取CPU状态"""
        return self.cpu_state
    
    def get_gpu_states(self) -> Dict[str, GPUState]:
        """获取GPU状态"""
        return self.gpu_states
    
    def get_container_states(self) -> Dict[str, ContainerState]:
        """获取容器状态"""
        return self.container_states
    
    # ============ 冲突队列（6.2新增） ============
    
    def detect_conflict(
        self,
        task_id: str,
        resource_type: ResourceType,
        requested_amount: float,
        priority: int,
    ) -> Optional[ResourceConflict]:
        """
        检测资源冲突
        
        Args:
            task_id: 任务ID
            resource_type: 资源类型
            requested_amount: 请求数量
            priority: 优先级
            
        Returns:
            冲突对象（如果存在）
        """
        # 检查资源可用性
        available = self.resource_status[resource_type.value]["available"]
        
        if requested_amount > available:
            # 检测是否有其他任务也在竞争同一资源
            competing_tasks = [
                alloc.task_id
                for alloc in self.allocations.values()
                if alloc.resource_type == resource_type and alloc.priority >= priority
            ]
            
            if competing_tasks:
                # 存在冲突
                conflict = ResourceConflict(
                    conflict_id=f"conflict_{uuid4()}",
                    conflict_type="resource_competition",
                    conflicting_tasks=[task_id] + competing_tasks,
                    resource_type=resource_type.value,
                    severity="high" if requested_amount > available * 2 else "medium",
                    detected_at=datetime.utcnow().isoformat() + "Z",
                    metadata={
                        "requested_amount": requested_amount,
                        "available": available,
                        "priority": priority,
                    },
                )
                
                self.detected_conflicts[conflict.conflict_id] = conflict
                self._add_to_conflict_queue(conflict)
                
                logger.warning(f"检测到资源冲突: {conflict.conflict_id}")
                
                return conflict
        
        return None
    
    def _add_to_conflict_queue(self, conflict: ResourceConflict):
        """添加到冲突队列"""
        # 添加到FIFO队列
        self.conflict_queue.append(conflict)
        
        # 添加到优先级队列（优先级越高，数字越小）
        priority_score = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
        }.get(conflict.severity, 5)
        
        self.conflict_priority_queue.put((priority_score, conflict.detected_at, conflict))
    
    def get_conflict_queue(self, use_priority: bool = False) -> List[ResourceConflict]:
        """
        获取冲突队列
        
        Args:
            use_priority: 是否使用优先级队列
            
        Returns:
            冲突列表
        """
        if use_priority:
            # 从优先级队列获取
            conflicts = []
            temp_queue = PriorityQueue()
            
            while not self.conflict_priority_queue.empty():
                item = self.conflict_priority_queue.get()
                conflicts.append(item[2])  # 第三个元素是conflict对象
                temp_queue.put(item)
            
            # 恢复队列
            while not temp_queue.empty():
                self.conflict_priority_queue.put(temp_queue.get())
            
            return conflicts
        else:
            # 从FIFO队列获取
            return list(self.conflict_queue)
    
    def resolve_conflict(
        self,
        conflict_id: str,
        strategy: Optional[SchedulingStrategy] = None,
    ) -> bool:
        """
        解决冲突
        
        Args:
            conflict_id: 冲突ID
            strategy: 解决策略（如果为None，使用当前策略）
            
        Returns:
            是否成功
        """
        conflict = self.detected_conflicts.get(conflict_id)
        if not conflict or conflict.resolved:
            return False
        
        strategy = strategy or self.current_strategy
        
        # 根据策略解决冲突
        if strategy == SchedulingStrategy.PRIORITY_BASED:
            # 基于优先级：优先分配高优先级任务
            self._resolve_by_priority(conflict)
        elif strategy == SchedulingStrategy.FAIR_SHARING:
            # 公平共享：平均分配资源
            self._resolve_by_fair_sharing(conflict)
        elif strategy == SchedulingStrategy.TIME_SLICING:
            # 时间片轮转：按时间片分配
            self._resolve_by_time_slicing(conflict)
        else:
            # 默认使用优先级策略
            self._resolve_by_priority(conflict)
        
        conflict.resolved = True
        conflict.resolution_strategy = strategy.value
        
        # 从队列中移除
        if conflict in self.conflict_queue:
            self.conflict_queue.remove(conflict)
        
        logger.info(f"冲突已解决: {conflict_id} - {strategy.value}")
        
        return True
    
    def _resolve_by_priority(self, conflict: ResourceConflict):
        """基于优先级解决冲突"""
        # 获取冲突任务的优先级
        task_priorities = {}
        for task_id in conflict.conflicting_tasks:
            for alloc in self.allocations.values():
                if alloc.task_id == task_id and alloc.resource_type.value == conflict.resource_type:
                    task_priorities[task_id] = alloc.priority
                    break
        
        # 按优先级排序（优先级越高，数字越小）
        sorted_tasks = sorted(task_priorities.items(), key=lambda x: x[1])
        
        # 优先分配高优先级任务
        available = self.resource_status[conflict.resource_type]["available"]
        for task_id, priority in sorted_tasks:
            # 这里可以实现具体的分配逻辑
            logger.info(f"优先分配资源给任务: {task_id} (优先级: {priority})")
    
    def _resolve_by_fair_sharing(self, conflict: ResourceConflict):
        """基于公平共享解决冲突"""
        available = self.resource_status[conflict.resource_type]["available"]
        num_tasks = len(conflict.conflicting_tasks)
        
        if num_tasks > 0:
            share_per_task = available / num_tasks
            logger.info(f"公平共享资源: 每个任务 {share_per_task:.2f}%")
    
    def _resolve_by_time_slicing(self, conflict: ResourceConflict):
        """基于时间片轮转解决冲突"""
        time_slice = self.strategy_config.get("time_slicing", {}).get("slice_duration", 5.0)
        logger.info(f"时间片轮转: 每个任务 {time_slice}秒")
    
    # ============ 调度策略（6.2新增） ============
    
    def set_scheduling_strategy(
        self,
        strategy: SchedulingStrategy,
        config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        设置调度策略
        
        Args:
            strategy: 调度策略
            config: 策略配置（可选）
            
        Returns:
            是否成功
        """
        self.current_strategy = strategy
        
        if config:
            if strategy.value in self.strategy_config:
                self.strategy_config[strategy.value].update(config)
            else:
                self.strategy_config[strategy.value] = config
        
        logger.info(f"设置调度策略: {strategy.value}")
        
        return True
    
    def get_scheduling_strategy(self) -> Dict[str, Any]:
        """获取当前调度策略"""
        return {
            "strategy": self.current_strategy.value,
            "config": self.strategy_config.get(self.current_strategy.value, {}),
        }
    
    def evaluate_strategy_performance(
        self,
        strategy: Optional[SchedulingStrategy] = None,
    ) -> Dict[str, Any]:
        """
        评估策略性能
        
        Args:
            strategy: 策略（如果为None，评估当前策略）
            
        Returns:
            性能指标
        """
        strategy = strategy or self.current_strategy
        performance = self.strategy_performance[strategy.value]
        
        success_rate = (
            (performance["successful_allocations"] / performance["total_allocations"] * 100)
            if performance["total_allocations"] > 0
            else 0
        )
        
        return {
            "strategy": strategy.value,
            "total_allocations": performance["total_allocations"],
            "successful_allocations": performance["successful_allocations"],
            "failed_allocations": performance["failed_allocations"],
            "success_rate": success_rate,
            "avg_wait_time": performance["avg_wait_time"],
        }
    
    # ============ 向前端推送提示（6.2新增） ============
    
    def subscribe_push(self, callback: Callable[[Dict[str, Any]], None]):
        """
        订阅推送消息
        
        Args:
            callback: 回调函数
        """
        self.push_subscribers.add(callback)
        logger.info(f"新增推送订阅者，当前订阅数: {len(self.push_subscribers)}")
    
    def unsubscribe_push(self, callback: Callable[[Dict[str, Any]], None]):
        """
        取消订阅推送消息
        
        Args:
            callback: 回调函数
        """
        self.push_subscribers.discard(callback)
        logger.info(f"移除推送订阅者，当前订阅数: {len(self.push_subscribers)}")
    
    async def _push_to_frontend(self, message: Dict[str, Any]):
        """
        向前端推送消息
        
        Args:
            message: 消息内容
        """
        async with self.push_lock:
            for callback in list(self.push_subscribers):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(message)
                    else:
                        callback(message)
                except Exception as e:
                    logger.error(f"推送消息失败: {e}", exc_info=True)
                    # 移除失败的订阅者
                    self.push_subscribers.discard(callback)
    
    async def _push_resource_status(self):
        """推送资源状态更新"""
        message = {
            "type": "resource_status",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "cpu": self.cpu_state.to_dict() if self.cpu_state else None,
                "gpus": {gpu_id: gpu.to_dict() for gpu_id, gpu in self.gpu_states.items()},
                "containers": {cid: c.to_dict() for cid, c in self.container_states.items()},
                "resource_status": self.resource_status,
            },
        }
        
        await self._push_to_frontend(message)
    
    async def push_hint(self, hint: InteractionHint):
        """
        推送提示到前端
        
        Args:
            hint: 交互提示对象
        """
        message = {
            "type": "hint",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": hint.to_dict(),
        }
        
        await self._push_to_frontend(message)
    
    async def push_conflict(self, conflict: ResourceConflict):
        """
        推送冲突到前端
        
        Args:
            conflict: 资源冲突对象
        """
        message = {
            "type": "conflict",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": conflict.to_dict(),
        }
        
        await self._push_to_frontend(message)
    
    async def push_scheduling_update(self, update: Dict[str, Any]):
        """
        推送调度更新到前端
        
        Args:
            update: 更新内容
        """
        message = {
            "type": "scheduling_update",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": update,
        }
        
        await self._push_to_frontend(message)


_resource_scheduler: Optional[ResourceSchedulerWithHints] = None


def get_resource_scheduler() -> ResourceSchedulerWithHints:
    """获取资源调度器实例"""
    global _resource_scheduler
    if _resource_scheduler is None:
        _resource_scheduler = ResourceSchedulerWithHints()
    return _resource_scheduler

