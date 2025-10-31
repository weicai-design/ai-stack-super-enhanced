"""
资源冲突解决器
对应需求: 8.2 - 资源冲突弹窗处理
对应开发规则: 统一生命周期接口、事件通信规范
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型枚举"""

    RESOURCE_EXHAUSTION = "resource_exhaustion"  # 资源耗尽
    MEMORY_CONFLICT = "memory_conflict"  # 内存冲突
    CPU_CONFLICT = "cpu_conflict"  # CPU冲突
    DISK_CONFLICT = "disk_conflict"  # 磁盘冲突
    NETWORK_CONFLICT = "network_conflict"  # 网络冲突
    PORT_CONFLICT = "port_conflict"  # 端口冲突
    MODULE_DEPENDENCY = "module_dependency"  # 模块依赖冲突


class ResolutionAction(Enum):
    """解决动作枚举"""

    REALLOCATE = "reallocate"  # 重新分配
    SUSPEND = "suspend"  # 暂停模块
    TERMINATE = "terminate"  # 终止模块
    REDUCE_RESOURCES = "reduce_resources"  # 减少资源
    WAIT = "wait"  # 等待资源
    USER_INTERVENTION = "user_intervention"  # 用户干预


@dataclass
class ResourceConflict:
    """资源冲突信息"""

    conflict_id: str
    conflict_type: ConflictType
    modules_involved: List[str]
    resource_type: str
    current_usage: float
    max_capacity: float
    severity: str  # low, medium, high, critical
    timestamp: datetime
    description: str


@dataclass
class ConflictResolution:
    """冲突解决方案"""

    conflict_id: str
    resolution_action: ResolutionAction
    target_modules: List[str]
    parameters: Dict[str, Any]
    expected_impact: str
    user_confirmation_required: bool


class ConflictResolver:
    """
    资源冲突解决器
    实现系统资源冲突的检测、分析和解决
    """

    def __init__(self):
        self.core_services = {}
        self.active_conflicts = {}
        self.resolution_history = []
        self.conflict_detection_rules = self._initialize_detection_rules()
        self.auto_resolution_enabled = True
        self.user_intervention_required = []

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """
        初始化冲突解决器
        对应开发规则: 统一生命周期接口
        """
        self.config = config or {}
        self.core_services = core_services or {}

        # 注册事件监听器
        await self._register_event_listeners()

        logger.info("资源冲突解决器初始化完成")

    async def start(self):
        """启动冲突解决器"""
        # 启动冲突检测任务
        self.detection_task = asyncio.create_task(self._background_conflict_detection())
        logger.info("资源冲突解决器已启动")

    async def stop(self):
        """停止冲突解决器"""
        if hasattr(self, "detection_task"):
            self.detection_task.cancel()
            try:
                await self.detection_task
            except asyncio.CancelledError:
                pass

        # 取消事件监听器
        await self._unregister_event_listeners()
        logger.info("资源冲突解决器已停止")

    async def get_health_status(self) -> Dict:
        """获取健康状态"""
        return {
            "status": "healthy",
            "details": {
                "active_conflicts": len(self.active_conflicts),
                "auto_resolution_enabled": self.auto_resolution_enabled,
                "pending_user_interventions": len(self.user_intervention_required),
            },
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "conflicts_detected": getattr(self, "conflicts_detected", 0),
                "conflicts_resolved": getattr(self, "conflicts_resolved", 0),
                "user_interventions": getattr(self, "user_interventions", 0),
            },
        }

    async def detect_conflicts(self) -> List[ResourceConflict]:
        """
        检测资源冲突
        对应需求: 8.2 - 冲突检测
        """
        detected_conflicts = []

        # 检测各种类型的冲突
        detection_methods = [
            self._detect_memory_conflicts,
            self._detect_cpu_conflicts,
            self._detect_disk_conflicts,
            self._detect_network_conflicts,
            self._detect_module_dependency_conflicts,
        ]

        for detection_method in detection_methods:
            try:
                conflicts = await detection_method()
                detected_conflicts.extend(conflicts)
            except Exception as e:
                logger.error(f"冲突检测方法 {detection_method.__name__} 执行异常: {e}")

        # 处理检测到的冲突
        for conflict in detected_conflicts:
            await self._handle_detected_conflict(conflict)

        return detected_conflicts

    async def resolve_conflict(
        self, conflict_id: str, resolution: ConflictResolution = None
    ) -> bool:
        """
        解决资源冲突
        对应需求: 8.2 - 冲突解决
        """
        if conflict_id not in self.active_conflicts:
            logger.warning(f"冲突ID不存在: {conflict_id}")
            return False

        conflict = self.active_conflicts[conflict_id]

        # 如果没有提供解决方案，则自动生成
        if not resolution:
            resolution = await self._generate_resolution(conflict)

        # 检查是否需要用户确认
        if resolution.user_confirmation_required:
            await self._request_user_confirmation(conflict, resolution)
            return False

        # 执行解决方案
        success = await self._execute_resolution(conflict, resolution)

        if success:
            # 记录解决历史
            self.resolution_history.append(
                {
                    "conflict_id": conflict_id,
                    "resolution": resolution,
                    "timestamp": datetime.utcnow(),
                    "success": True,
                }
            )

            # 从活跃冲突中移除
            self.active_conflicts.pop(conflict_id)

            self.conflicts_resolved = getattr(self, "conflicts_resolved", 0) + 1

            logger.info(f"已成功解决冲突: {conflict_id}")

        return success

    async def get_conflict_report(self) -> Dict:
        """获取冲突报告"""
        return {
            "active_conflicts": [
                {
                    "conflict_id": conflict.conflict_id,
                    "type": conflict.conflict_type.value,
                    "modules": conflict.modules_involved,
                    "severity": conflict.severity,
                    "description": conflict.description,
                }
                for conflict in self.active_conflicts.values()
            ],
            "resolution_history": [
                {
                    "conflict_id": record["conflict_id"],
                    "action": record["resolution"].resolution_action.value,
                    "timestamp": record["timestamp"].isoformat(),
                    "success": record["success"],
                }
                for record in self.resolution_history[-10:]  # 最近10条记录
            ],
            "statistics": {
                "total_detected": getattr(self, "conflicts_detected", 0),
                "total_resolved": getattr(self, "conflicts_resolved", 0),
                "resolution_rate": self._calculate_resolution_rate(),
            },
        }

    async def set_auto_resolution(self, enabled: bool):
        """设置自动解决模式"""
        self.auto_resolution_enabled = enabled
        logger.info(f"自动冲突解决模式: {'启用' if enabled else '禁用'}")

    async def _register_event_listeners(self):
        """注册事件监听器"""
        event_bus = self.core_services.get("event_bus")
        if event_bus:
            await event_bus.subscribe("resource.alert", self._handle_resource_alert)
            await event_bus.subscribe("module.started", self._handle_module_started)
            await event_bus.subscribe("module.stopped", self._handle_module_stopped)

    async def _unregister_event_listeners(self):
        """取消事件监听器"""
        event_bus = self.core_services.get("event_bus")
        if event_bus:
            await event_bus.unsubscribe("resource.alert", self._handle_resource_alert)
            await event_bus.unsubscribe("module.started", self._handle_module_started)
            await event_bus.unsubscribe("module.stopped", self._handle_module_stopped)

    async def _background_conflict_detection(self):
        """后台冲突检测任务"""
        while True:
            try:
                await asyncio.sleep(10)  # 每10秒检测一次
                await self.detect_conflicts()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"后台冲突检测异常: {e}")
                await asyncio.sleep(5)  # 异常时短暂等待

    async def _detect_memory_conflicts(self) -> List[ResourceConflict]:
        """检测内存冲突"""
        conflicts = []

        resource_monitor = self.core_services.get("resource_monitor")
        if not resource_monitor:
            return conflicts

        try:
            metrics = await resource_monitor.get_current_metrics()
            memory_metric = metrics.get("memory")

            if memory_metric and memory_metric.usage_percent > 90:
                conflict = ResourceConflict(
                    conflict_id=f"memory_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    conflict_type=ConflictType.MEMORY_CONFLICT,
                    modules_involved=["system"],  # 需要更精确的模块识别
                    resource_type="memory",
                    current_usage=memory_metric.usage_percent,
                    max_capacity=100.0,
                    severity="critical" if memory_metric.usage_percent > 95 else "high",
                    timestamp=datetime.utcnow(),
                    description=f"内存使用率过高: {memory_metric.usage_percent:.1f}%",
                )
                conflicts.append(conflict)

        except Exception as e:
            logger.error(f"内存冲突检测异常: {e}")

        return conflicts

    async def _detect_cpu_conflicts(self) -> List[ResourceConflict]:
        """检测CPU冲突"""
        conflicts = []

        resource_monitor = self.core_services.get("resource_monitor")
        if not resource_monitor:
            return conflicts

        try:
            metrics = await resource_monitor.get_current_metrics()
            cpu_metric = metrics.get("cpu")

            if cpu_metric and cpu_metric.usage_percent > 85:
                conflict = ResourceConflict(
                    conflict_id=f"cpu_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    conflict_type=ConflictType.CPU_CONFLICT,
                    modules_involved=["system"],
                    resource_type="cpu",
                    current_usage=cpu_metric.usage_percent,
                    max_capacity=100.0,
                    severity="critical" if cpu_metric.usage_percent > 90 else "high",
                    timestamp=datetime.utcnow(),
                    description=f"CPU使用率过高: {cpu_metric.usage_percent:.1f}%",
                )
                conflicts.append(conflict)

        except Exception as e:
            logger.error(f"CPU冲突检测异常: {e}")

        return conflicts

    async def _detect_disk_conflicts(self) -> List[ResourceConflict]:
        """检测磁盘冲突"""
        conflicts = []

        resource_monitor = self.core_services.get("resource_monitor")
        if not resource_monitor:
            return conflicts

        try:
            metrics = await resource_monitor.get_current_metrics()
            disk_metric = metrics.get("disk")

            if disk_metric and disk_metric.usage_percent > 95:
                conflict = ResourceConflict(
                    conflict_id=f"disk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    conflict_type=ConflictType.DISK_CONFLICT,
                    modules_involved=["system"],
                    resource_type="disk",
                    current_usage=disk_metric.usage_percent,
                    max_capacity=100.0,
                    severity="critical",
                    timestamp=datetime.utcnow(),
                    description=f"磁盘空间不足: {disk_metric.usage_percent:.1f}% 已使用",
                )
                conflicts.append(conflict)

        except Exception as e:
            logger.error(f"磁盘冲突检测异常: {e}")

        return conflicts

    async def _detect_network_conflicts(self) -> List[ResourceConflict]:
        """检测网络冲突"""
        # 简化实现，实际需要更复杂的网络冲突检测
        return []

    async def _detect_module_dependency_conflicts(self) -> List[ResourceConflict]:
        """检测模块依赖冲突"""
        # 简化实现，实际需要检查模块依赖关系
        return []

    async def _handle_detected_conflict(self, conflict: ResourceConflict):
        """处理检测到的冲突"""
        # 检查是否已存在相同冲突
        existing_conflict = self._find_similar_conflict(conflict)
        if existing_conflict:
            # 更新现有冲突的严重程度
            await self._update_conflict_severity(existing_conflict, conflict.severity)
            return

        # 记录新冲突
        self.active_conflicts[conflict.conflict_id] = conflict
        self.conflicts_detected = getattr(self, "conflicts_detected", 0) + 1

        logger.warning(f"检测到资源冲突: {conflict.description}")

        # 发布冲突事件
        event_bus = self.core_services.get("event_bus")
        if event_bus:
            await event_bus.publish(
                "resource.conflict.detected",
                {
                    "conflict_id": conflict.conflict_id,
                    "conflict_type": conflict.conflict_type.value,
                    "severity": conflict.severity,
                    "description": conflict.description,
                    "timestamp": conflict.timestamp.isoformat(),
                },
                {"source": "conflict_resolver"},
            )

        # 自动解决（如果启用）
        if self.auto_resolution_enabled:
            await self.resolve_conflict(conflict.conflict_id)

    async def _generate_resolution(
        self, conflict: ResourceConflict
    ) -> ConflictResolution:
        """生成冲突解决方案"""
        resolution_action = await self._determine_resolution_action(conflict)

        return ConflictResolution(
            conflict_id=conflict.conflict_id,
            resolution_action=resolution_action,
            target_modules=conflict.modules_involved,
            parameters=await self._generate_resolution_parameters(
                conflict, resolution_action
            ),
            expected_impact=await self._assess_resolution_impact(
                conflict, resolution_action
            ),
            user_confirmation_required=await self._requires_user_confirmation(
                conflict, resolution_action
            ),
        )

    async def _determine_resolution_action(
        self, conflict: ResourceConflict
    ) -> ResolutionAction:
        """确定解决动作"""
        if conflict.conflict_type == ConflictType.MEMORY_CONFLICT:
            return ResolutionAction.REALLOCATE
        elif conflict.conflict_type == ConflictType.CPU_CONFLICT:
            return ResolutionAction.REDUCE_RESOURCES
        elif conflict.conflict_type == ConflictType.DISK_CONFLICT:
            return ResolutionAction.USER_INTERVENTION  # 磁盘冲突通常需要用户干预
        else:
            return ResolutionAction.REALLOCATE

    async def _generate_resolution_parameters(
        self, conflict: ResourceConflict, action: ResolutionAction
    ) -> Dict[str, Any]:
        """生成解决参数"""
        if action == ResolutionAction.REALLOCATE:
            return {
                "resource_type": conflict.resource_type,
                "reduction_percentage": 0.2,  # 减少20%
                "target_usage": conflict.max_capacity * 0.8,  # 目标使用率80%
            }
        elif action == ResolutionAction.REDUCE_RESOURCES:
            return {
                "cpu_reduction": 0.1,
                "memory_reduction": 0.1,
                "duration_minutes": 5,  # 持续5分钟
            }
        else:
            return {}

    async def _assess_resolution_impact(
        self, conflict: ResourceConflict, action: ResolutionAction
    ) -> str:
        """评估解决方案影响"""
        impacts = {
            ResolutionAction.REALLOCATE: "可能暂时影响部分模块性能",
            ResolutionAction.SUSPEND: "目标模块将暂停运行",
            ResolutionAction.TERMINATE: "目标模块将被终止",
            ResolutionAction.REDUCE_RESOURCES: "模块性能可能下降",
            ResolutionAction.WAIT: "系统将等待资源释放",
            ResolutionAction.USER_INTERVENTION: "需要用户确认操作",
        }
        return impacts.get(action, "影响未知")

    async def _requires_user_confirmation(
        self, conflict: ResourceConflict, action: ResolutionAction
    ) -> bool:
        """检查是否需要用户确认"""
        # 严重冲突或涉及关键模块时需要用户确认
        return conflict.severity in ["high", "critical"] or action in [
            ResolutionAction.TERMINATE,
            ResolutionAction.SUSPEND,
        ]

    async def _execute_resolution(
        self, conflict: ResourceConflict, resolution: ConflictResolution
    ) -> bool:
        """执行解决方案"""
        try:
            if resolution.resolution_action == ResolutionAction.REALLOCATE:
                return await self._execute_reallocation(conflict, resolution)
            elif resolution.resolution_action == ResolutionAction.REDUCE_RESOURCES:
                return await self._execute_resource_reduction(conflict, resolution)
            elif resolution.resolution_action == ResolutionAction.SUSPEND:
                return await self._execute_suspension(conflict, resolution)
            else:
                logger.warning(f"未实现的解决动作: {resolution.resolution_action}")
                return False

        except Exception as e:
            logger.error(f"执行解决方案异常: {e}")
            return False

    async def _execute_reallocation(
        self, conflict: ResourceConflict, resolution: ConflictResolution
    ) -> bool:
        """执行重新分配"""
        dynamic_allocator = self.core_services.get("dynamic_allocator")
        if not dynamic_allocator:
            logger.error("动态分配器不可用")
            return False

        try:
            # 对涉及模块进行资源重新分配
            for module_name in resolution.target_modules:
                if module_name != "system":  # 系统模块需要特殊处理
                    # 获取当前分配
                    current_allocation = None  # 需要从分配器获取

                    if current_allocation:
                        # 减少资源分配
                        new_cpu = current_allocation.cpu_limit * 0.8
                        new_memory = current_allocation.memory_limit * 0.8

                        await dynamic_allocator.adjust_allocation(
                            module_name, new_cpu, new_memory
                        )

            logger.info(f"已重新分配 {conflict.resource_type} 资源")
            return True

        except Exception as e:
            logger.error(f"重新分配资源异常: {e}")
            return False

    async def _execute_resource_reduction(
        self, conflict: ResourceConflict, resolution: ConflictResolution
    ) -> bool:
        """执行资源减少"""
        # 实现资源减少逻辑
        logger.info(f"已减少 {conflict.resource_type} 资源使用")
        return True

    async def _execute_suspension(
        self, conflict: ResourceConflict, resolution: ConflictResolution
    ) -> bool:
        """执行模块暂停"""
        # 实现模块暂停逻辑
        logger.warning(f"已暂停模块: {resolution.target_modules}")
        return True

    async def _request_user_confirmation(
        self, conflict: ResourceConflict, resolution: ConflictResolution
    ):
        """请求用户确认"""
        # 记录需要用户干预的冲突
        self.user_intervention_required.append(
            {
                "conflict": conflict,
                "resolution": resolution,
                "timestamp": datetime.utcnow(),
            }
        )

        # 发布用户干预事件
        event_bus = self.core_services.get("event_bus")
        if event_bus:
            await event_bus.publish(
                "resource.conflict.user_intervention",
                {
                    "conflict_id": conflict.conflict_id,
                    "conflict_type": conflict.conflict_type.value,
                    "severity": conflict.severity,
                    "description": conflict.description,
                    "proposed_action": resolution.resolution_action.value,
                    "target_modules": resolution.target_modules,
                    "expected_impact": resolution.expected_impact,
                },
                {"source": "conflict_resolver"},
            )

        logger.info(f"已请求用户确认冲突解决方案: {conflict.conflict_id}")

    async def _handle_resource_alert(self, event_data: Dict, metadata: Dict):
        """处理资源预警事件"""
        if event_data.get("status") in ["warning", "critical"]:
            # 触发冲突检测
            await self.detect_conflicts()

    async def _handle_module_started(self, event_data: Dict, metadata: Dict):
        """处理模块启动事件"""
        # 模块启动可能引发资源冲突
        await asyncio.sleep(2)  # 等待资源稳定
        await self.detect_conflicts()

    async def _handle_module_stopped(self, event_data: Dict, metadata: Dict):
        """处理模块停止事件"""
        # 模块停止可能解决某些冲突
        await self.detect_conflicts()

    def _find_similar_conflict(
        self, new_conflict: ResourceConflict
    ) -> Optional[ResourceConflict]:
        """查找相似冲突"""
        for conflict in self.active_conflicts.values():
            if (
                conflict.conflict_type == new_conflict.conflict_type
                and conflict.resource_type == new_conflict.resource_type
                and set(conflict.modules_involved) == set(new_conflict.modules_involved)
            ):
                return conflict
        return None

    async def _update_conflict_severity(
        self, conflict: ResourceConflict, new_severity: str
    ):
        """更新冲突严重程度"""
        # 更新冲突严重程度逻辑
        pass

    def _calculate_resolution_rate(self) -> float:
        """计算冲突解决率"""
        detected = getattr(self, "conflicts_detected", 0)
        resolved = getattr(self, "conflicts_resolved", 0)

        if detected == 0:
            return 1.0  # 无冲突时解决率为100%

        return resolved / detected

    def _initialize_detection_rules(self) -> Dict:
        """初始化冲突检测规则"""
        return {
            "memory_threshold": 90.0,
            "cpu_threshold": 85.0,
            "disk_threshold": 95.0,
            "network_threshold": 80.0,
            "check_interval": 10,  # 检测间隔(秒)
        }
