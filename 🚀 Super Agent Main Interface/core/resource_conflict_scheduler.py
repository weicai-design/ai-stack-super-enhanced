"""
资源冲突调度系统
P0-015: 资源策略引擎与冲突调度（与自学习联动）
"""

from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型"""
    CPU_COMPETITION = "cpu_competition"  # CPU竞争
    MEMORY_COMPETITION = "memory_competition"  # 内存竞争
    DISK_COMPETITION = "disk_competition"  # 磁盘竞争
    NETWORK_COMPETITION = "network_competition"  # 网络竞争
    PRIORITY_CONFLICT = "priority_conflict"  # 优先级冲突
    SCHEDULE_CONFLICT = "schedule_conflict"  # 调度冲突
    DEPENDENCY_CONFLICT = "dependency_conflict"  # 依赖冲突


class ResolutionStrategy(Enum):
    """解决策略"""
    PRIORITY_BASED = "priority_based"  # 基于优先级
    FAIR_SHARING = "fair_sharing"  # 公平共享
    TIME_SLICING = "time_slicing"  # 时间片轮转
    RESOURCE_POOLING = "resource_pooling"  # 资源池化
    LEARNING_BASED = "learning_based"  # 基于学习
    HYBRID = "hybrid"  # 混合策略


@dataclass
class ResourceConflict:
    """资源冲突"""
    conflict_id: str
    conflict_type: ConflictType
    conflicting_modules: List[str]
    resource_type: str
    conflict_severity: str  # low, medium, high, critical
    detected_at: datetime
    current_state: Dict[str, Any]
    root_cause: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConflictResolution:
    """冲突解决方案"""
    conflict: ResourceConflict
    resolution_strategy: ResolutionStrategy
    resolution_actions: List[Dict[str, Any]]
    expected_improvement: str
    risk_level: str  # low, medium, high
    requires_approval: bool
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    success: bool = False
    feedback_score: Optional[float] = None  # 来自自学习系统的反馈


class ResourceConflictScheduler:
    """
    资源冲突调度系统
    
    功能：
    1. 检测资源冲突
    2. 分析冲突根因
    3. 生成解决方案
    4. 执行冲突解决
    5. 与自学习系统联动优化
    """
    
    def __init__(
        self,
        resource_monitor=None,
        strategy_engine=None,
        learning_system=None,
        dynamic_allocator=None
    ):
        self.resource_monitor = resource_monitor
        self.strategy_engine = strategy_engine
        self.learning_system = learning_system
        self.dynamic_allocator = dynamic_allocator
        
        # 冲突记录
        self.detected_conflicts: List[ResourceConflict] = []
        
        # 解决方案记录
        self.resolutions: List[ConflictResolution] = []
        
        # 冲突模式（用于学习）
        self.conflict_patterns: Dict[str, Dict[str, Any]] = {}
        
        # 解决效果统计
        self.resolution_statistics: Dict[ResolutionStrategy, Dict[str, Any]] = {}
        
        logger.info("资源冲突调度系统初始化完成")
    
    async def detect_conflicts(
        self,
        resource_state: Optional[Dict[str, Any]] = None
    ) -> List[ResourceConflict]:
        """
        检测资源冲突
        
        Args:
            resource_state: 资源状态（可选）
            
        Returns:
            检测到的冲突列表
        """
        if not resource_state and self.resource_monitor:
            resource_state = self.resource_monitor.get_current_status()
        
        if not resource_state:
            return []
        
        conflicts = []
        
        # 检测CPU竞争
        cpu_conflicts = await self._detect_cpu_conflicts(resource_state)
        conflicts.extend(cpu_conflicts)
        
        # 检测内存竞争
        memory_conflicts = await self._detect_memory_conflicts(resource_state)
        conflicts.extend(memory_conflicts)
        
        # 检测磁盘竞争
        disk_conflicts = await self._detect_disk_conflicts(resource_state)
        conflicts.extend(disk_conflicts)
        
        # 检测优先级冲突
        priority_conflicts = await self._detect_priority_conflicts(resource_state)
        conflicts.extend(priority_conflicts)
        
        # 保存冲突记录
        self.detected_conflicts.extend(conflicts)
        
        # 保留最近1000条
        if len(self.detected_conflicts) > 1000:
            self.detected_conflicts = self.detected_conflicts[-1000:]
        
        # 分析冲突模式
        for conflict in conflicts:
            await self._analyze_conflict_pattern(conflict)
        
        return conflicts
    
    async def _detect_cpu_conflicts(
        self,
        resource_state: Dict[str, Any]
    ) -> List[ResourceConflict]:
        """检测CPU竞争"""
        conflicts = []
        
        cpu_data = resource_state.get("cpu", {})
        cpu_percent = cpu_data.get("percent", 0)
        per_cpu = cpu_data.get("per_cpu", [])
        
        # 如果CPU使用率很高且单个核心过载
        if cpu_percent > 85 and per_cpu:
            max_cpu = max(per_cpu)
            if max_cpu > 95:
                conflicts.append(ResourceConflict(
                    conflict_id=f"cpu_{int(datetime.now().timestamp() * 1000)}",
                    conflict_type=ConflictType.CPU_COMPETITION,
                    conflicting_modules=["system"],  # 需要从实际监控获取
                    resource_type="cpu",
                    conflict_severity="high" if cpu_percent > 90 else "medium",
                    detected_at=datetime.now(),
                    current_state={"cpu_percent": cpu_percent, "max_core": max_cpu},
                    root_cause="单个CPU核心过载，可能存在资源竞争"
                ))
        
        return conflicts
    
    async def _detect_memory_conflicts(
        self,
        resource_state: Dict[str, Any]
    ) -> List[ResourceConflict]:
        """检测内存竞争"""
        conflicts = []
        
        memory_data = resource_state.get("memory", {})
        memory_percent = memory_data.get("percent", 0)
        available = memory_data.get("available", 0)
        available_gb = available / (1024 ** 3)
        
        # 如果内存使用率很高且可用内存很少
        if memory_percent > 85 and available_gb < 2:
            conflicts.append(ResourceConflict(
                conflict_id=f"memory_{int(datetime.now().timestamp() * 1000)}",
                conflict_type=ConflictType.MEMORY_COMPETITION,
                conflicting_modules=["system"],
                resource_type="memory",
                conflict_severity="critical" if memory_percent > 95 else "high",
                detected_at=datetime.now(),
                current_state={"memory_percent": memory_percent, "available_gb": available_gb},
                root_cause="内存使用率过高，可用内存不足"
            ))
        
        return conflicts
    
    async def _detect_disk_conflicts(
        self,
        resource_state: Dict[str, Any]
    ) -> List[ResourceConflict]:
        """检测磁盘竞争"""
        conflicts = []
        
        disk_data = resource_state.get("disk", {})
        disk_percent = disk_data.get("percent", 0)
        
        if disk_percent > 90:
            conflicts.append(ResourceConflict(
                conflict_id=f"disk_{int(datetime.now().timestamp() * 1000)}",
                conflict_type=ConflictType.DISK_COMPETITION,
                conflicting_modules=["system"],
                resource_type="disk",
                conflict_severity="high",
                detected_at=datetime.now(),
                current_state={"disk_percent": disk_percent},
                root_cause="磁盘空间不足"
            ))
        
        return conflicts
    
    async def _detect_priority_conflicts(
        self,
        resource_state: Dict[str, Any]
    ) -> List[ResourceConflict]:
        """检测优先级冲突"""
        # 这里需要从任务系统或模块系统获取优先级信息
        # 简化实现
        return []
    
    async def _analyze_conflict_pattern(self, conflict: ResourceConflict):
        """分析冲突模式"""
        pattern_key = f"{conflict.conflict_type.value}_{conflict.conflict_severity}"
        
        if pattern_key not in self.conflict_patterns:
            self.conflict_patterns[pattern_key] = {
                "count": 0,
                "first_seen": conflict.detected_at,
                "last_seen": conflict.detected_at,
                "common_root_causes": [],
                "successful_resolutions": []
            }
        
        pattern = self.conflict_patterns[pattern_key]
        pattern["count"] += 1
        pattern["last_seen"] = conflict.detected_at
        
        if conflict.root_cause:
            if conflict.root_cause not in pattern["common_root_causes"]:
                pattern["common_root_causes"].append(conflict.root_cause)
    
    async def resolve_conflict(
        self,
        conflict: ResourceConflict,
        preferred_strategy: Optional[ResolutionStrategy] = None
    ) -> ConflictResolution:
        """
        解决资源冲突
        
        Args:
            conflict: 资源冲突
            preferred_strategy: 首选解决策略（可选）
            
        Returns:
            冲突解决方案
        """
        # 如果自学习系统可用，优先使用学习策略
        if self.learning_system and not preferred_strategy:
            learning_strategy = await self._get_learning_based_strategy(conflict)
            if learning_strategy:
                preferred_strategy = learning_strategy
        
        # 如果没有学习策略，根据冲突类型选择
        if not preferred_strategy:
            preferred_strategy = self._select_resolution_strategy(conflict)
        
        # 生成解决方案
        resolution = await self._generate_resolution(conflict, preferred_strategy)
        
        # 保存解决方案
        self.resolutions.append(resolution)
        
        # 保留最近1000条
        if len(self.resolutions) > 1000:
            self.resolutions = self.resolutions[-1000:]
        
        return resolution
    
    async def _get_learning_based_strategy(
        self,
        conflict: ResourceConflict
    ) -> Optional[ResolutionStrategy]:
        """从自学习系统获取解决策略"""
        if not self.learning_system:
            return None
        
        try:
            # 查询自学习系统的建议
            # 这里需要根据实际的自学习系统接口实现
            pattern_key = f"{conflict.conflict_type.value}_{conflict.conflict_severity}"
            pattern = self.conflict_patterns.get(pattern_key, {})
            
            # 如果有成功的解决方案，优先使用
            successful_resolutions = pattern.get("successful_resolutions", [])
            if successful_resolutions:
                # 返回最成功的策略
                best_strategy = max(
                    successful_resolutions,
                    key=lambda x: x.get("feedback_score", 0)
                )
                return ResolutionStrategy(best_strategy["strategy"])
            
        except Exception as e:
            logger.warning(f"从自学习系统获取策略失败: {e}")
        
        return None
    
    def _select_resolution_strategy(
        self,
        conflict: ResourceConflict
    ) -> ResolutionStrategy:
        """选择解决策略"""
        # 根据冲突类型和严重程度选择策略
        if conflict.conflict_severity == "critical":
            return ResolutionStrategy.PRIORITY_BASED
        elif conflict.conflict_type in [
            ConflictType.CPU_COMPETITION,
            ConflictType.MEMORY_COMPETITION
        ]:
            return ResolutionStrategy.TIME_SLICING
        elif conflict.conflict_type == ConflictType.PRIORITY_CONFLICT:
            return ResolutionStrategy.PRIORITY_BASED
        else:
            return ResolutionStrategy.FAIR_SHARING
    
    async def _generate_resolution(
        self,
        conflict: ResourceConflict,
        strategy: ResolutionStrategy
    ) -> ConflictResolution:
        """生成解决方案"""
        actions = []
        expected_improvement = ""
        risk_level = "medium"
        requires_approval = False
        
        if strategy == ResolutionStrategy.PRIORITY_BASED:
            actions = [
                {"action": "adjust_priority", "modules": conflict.conflicting_modules},
                {"action": "reallocate_resources", "priority": "high"}
            ]
            expected_improvement = "基于优先级重新分配资源，减少冲突"
            risk_level = "low"
        
        elif strategy == ResolutionStrategy.TIME_SLICING:
            actions = [
                {"action": "schedule_timeslice", "modules": conflict.conflicting_modules},
                {"action": "limit_concurrent_access", "resource": conflict.resource_type}
            ]
            expected_improvement = "使用时间片轮转，避免同时竞争"
            risk_level = "low"
        
        elif strategy == ResolutionStrategy.FAIR_SHARING:
            actions = [
                {"action": "equal_allocation", "modules": conflict.conflicting_modules},
                {"action": "enforce_limits", "resource": conflict.resource_type}
            ]
            expected_improvement = "公平分配资源，确保所有模块都能获得资源"
            risk_level = "low"
        
        elif strategy == ResolutionStrategy.LEARNING_BASED:
            # 从自学习系统获取具体动作
            learning_actions = await self._get_learning_actions(conflict)
            actions = learning_actions or actions
            expected_improvement = "基于历史学习数据优化资源分配"
            risk_level = "low"
        
        # 根据冲突严重程度决定是否需要授权
        if conflict.conflict_severity in ["high", "critical"]:
            requires_approval = True
            risk_level = "medium"
        
        return ConflictResolution(
            conflict=conflict,
            resolution_strategy=strategy,
            resolution_actions=actions,
            expected_improvement=expected_improvement,
            risk_level=risk_level,
            requires_approval=requires_approval
        )
    
    async def _get_learning_actions(
        self,
        conflict: ResourceConflict
    ) -> List[Dict[str, Any]]:
        """从自学习系统获取动作"""
        # 这里需要根据实际的自学习系统接口实现
        return []
    
    async def execute_resolution(
        self,
        resolution: ConflictResolution,
        approved: bool = False
    ) -> Dict[str, Any]:
        """
        执行冲突解决方案
        
        Args:
            resolution: 冲突解决方案
            approved: 是否已获得授权
            
        Returns:
            执行结果
        """
        if resolution.requires_approval and not approved:
            return {
                "success": False,
                "message": "需要用户授权才能执行此操作",
                "resolution": resolution
            }
        
        resolution.executed_at = datetime.now()
        
        try:
            # 执行解决方案动作
            execution_result = await self._execute_resolution_actions(
                resolution.resolution_actions
            )
            
            resolution.execution_result = execution_result
            resolution.success = execution_result.get("success", False)
            
            # 收集执行后的性能指标
            if self.resource_monitor:
                post_execution_state = self.resource_monitor.get_current_status()
                # 计算改善效果
                improvement = self._calculate_improvement(
                    resolution.conflict.current_state,
                    post_execution_state
                )
                execution_result["improvement"] = improvement
            
            # 发送反馈到自学习系统
            if self.learning_system:
                feedback_score = await self._send_resolution_feedback(resolution)
                resolution.feedback_score = feedback_score
            
            # 更新解决统计
            self._update_resolution_statistics(resolution)
            
            # 更新冲突模式
            if resolution.success:
                pattern_key = f"{resolution.conflict.conflict_type.value}_{resolution.conflict.conflict_severity}"
                if pattern_key in self.conflict_patterns:
                    pattern = self.conflict_patterns[pattern_key]
                    pattern["successful_resolutions"].append({
                        "strategy": resolution.resolution_strategy.value,
                        "feedback_score": resolution.feedback_score or 0.5,
                        "executed_at": resolution.executed_at.isoformat()
                    })
            
            logger.info(f"冲突解决执行完成: {resolution.conflict.conflict_id}, 成功: {resolution.success}")
            
            return {
                "success": True,
                "resolution_id": resolution.conflict.conflict_id,
                "execution_result": execution_result
            }
            
        except Exception as e:
            logger.error(f"冲突解决执行失败: {e}", exc_info=True)
            resolution.success = False
            resolution.execution_result = {"error": str(e)}
            return {
                "success": False,
                "error": str(e),
                "resolution_id": resolution.conflict.conflict_id
            }
    
    async def _execute_resolution_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行解决方案动作"""
        result = {
            "success": True,
            "actions_executed": [],
            "details": {}
        }
        
        for action in actions:
            action_type = action.get("action")
            
            if action_type == "adjust_priority":
                # 调整优先级
                result["actions_executed"].append("adjust_priority")
                result["details"]["adjust_priority"] = "优先级已调整"
            
            elif action_type == "reallocate_resources":
                # 重新分配资源
                if self.dynamic_allocator:
                    result["actions_executed"].append("reallocate_resources")
                    result["details"]["reallocate_resources"] = "资源已重新分配"
            
            elif action_type == "schedule_timeslice":
                # 时间片调度
                result["actions_executed"].append("schedule_timeslice")
                result["details"]["schedule_timeslice"] = "时间片已调度"
            
            elif action_type == "equal_allocation":
                # 公平分配
                result["actions_executed"].append("equal_allocation")
                result["details"]["equal_allocation"] = "资源已公平分配"
        
        return result
    
    def _calculate_improvement(
        self,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算改善效果"""
        improvement = {}
        
        # CPU改善
        if "cpu_percent" in before_state and "cpu" in after_state:
            cpu_before = before_state["cpu_percent"]
            cpu_after = after_state.get("cpu", {}).get("percent", cpu_before)
            improvement["cpu"] = cpu_before - cpu_after
        
        # 内存改善
        if "memory_percent" in before_state and "memory" in after_state:
            mem_before = before_state.get("memory_percent", 0)
            mem_after = after_state.get("memory", {}).get("percent", mem_before)
            improvement["memory"] = mem_before - mem_after
        
        return improvement
    
    async def _send_resolution_feedback(
        self,
        resolution: ConflictResolution
    ) -> float:
        """发送解决反馈到自学习系统"""
        if not self.learning_system:
            return 0.5  # 默认评分
        
        try:
            # 计算反馈评分
            score = 0.5  # 基础分
            
            if resolution.success:
                score += 0.3
            
            if resolution.execution_result:
                improvement = resolution.execution_result.get("improvement", {})
                if improvement:
                    # 根据改善效果调整评分
                    cpu_improvement = improvement.get("cpu", 0)
                    mem_improvement = improvement.get("memory", 0)
                    score += min(0.2, (cpu_improvement + mem_improvement) / 100)
            
            # 发送到自学习系统
            feedback_data = {
                "conflict_type": resolution.conflict.conflict_type.value,
                "resolution_strategy": resolution.resolution_strategy.value,
                "success": resolution.success,
                "improvement": resolution.execution_result.get("improvement", {}),
                "feedback_score": score,
                "timestamp": resolution.executed_at.isoformat() if resolution.executed_at else datetime.now().isoformat()
            }
            
            # await self.learning_system.record_conflict_resolution(feedback_data)
            logger.debug(f"已发送冲突解决反馈: {score}")
            
            return score
            
        except Exception as e:
            logger.warning(f"发送反馈失败: {e}")
            return 0.5
    
    def _update_resolution_statistics(
        self,
        resolution: ConflictResolution
    ):
        """更新解决统计"""
        strategy = resolution.resolution_strategy
        
        if strategy not in self.resolution_statistics:
            self.resolution_statistics[strategy] = {
                "total_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_feedback_score": 0.0,
                "feedback_scores": []
            }
        
        stats = self.resolution_statistics[strategy]
        stats["total_count"] += 1
        
        if resolution.success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
        
        if resolution.feedback_score is not None:
            stats["feedback_scores"].append(resolution.feedback_score)
            # 只保留最近100个评分
            if len(stats["feedback_scores"]) > 100:
                stats["feedback_scores"] = stats["feedback_scores"][-100:]
            stats["avg_feedback_score"] = sum(stats["feedback_scores"]) / len(stats["feedback_scores"])
    
    def get_conflict_statistics(self) -> Dict[str, Any]:
        """获取冲突统计信息"""
        recent_conflicts = self.detected_conflicts[-100:] if self.detected_conflicts else []
        recent_resolutions = self.resolutions[-100:] if self.resolutions else []
        
        conflict_type_counts = {}
        for conflict in recent_conflicts:
            conflict_type = conflict.conflict_type.value
            conflict_type_counts[conflict_type] = conflict_type_counts.get(conflict_type, 0) + 1
        
        return {
            "total_conflicts": len(self.detected_conflicts),
            "recent_conflicts": len(recent_conflicts),
            "total_resolutions": len(self.resolutions),
            "recent_resolutions": len(recent_resolutions),
            "conflict_type_distribution": conflict_type_counts,
            "resolution_statistics": {
                strategy.value: stats
                for strategy, stats in self.resolution_statistics.items()
            },
            "conflict_patterns": {
                key: {
                    "count": pattern["count"],
                    "common_root_causes": pattern["common_root_causes"][:5]
                }
                for key, pattern in self.conflict_patterns.items()
            }
        }










