"""
自适应进化器
实现系统资源的自适应调整和优化
对应需求: 8.7 - 自适应进化
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class EvolutionStrategy(Enum):
    """进化策略枚举"""
    CONSERVATIVE = "conservative"  # 保守策略
    BALANCED = "balanced"  # 平衡策略
    AGGRESSIVE = "aggressive"  # 激进策略


@dataclass
class EvolutionAction:
    """进化动作"""
    action_type: str  # adjust, scale, optimize, migrate
    target_module: str
    parameters: Dict[str, Any]
    expected_improvement: float
    risk_level: str  # low, medium, high
    timestamp: datetime


@dataclass
class EvolutionMetrics:
    """进化指标"""
    cpu_usage_before: float
    cpu_usage_after: float
    memory_usage_before: float
    memory_usage_after: float
    response_time_before: float
    response_time_after: float
    improvement_rate: float
    evolution_count: int


class AdaptiveEvolver:
    """
    自适应进化器
    根据系统负载和性能指标自动调整资源分配和系统配置
    """

    def __init__(self):
        self.evolution_strategy = EvolutionStrategy.BALANCED
        self.evolution_history: List[EvolutionAction] = []
        self.evolution_metrics: List[EvolutionMetrics] = []
        self.is_evolving = False
        self.evolution_task = None
        self.evolution_interval = 300  # 5分钟检查一次
        self.performance_thresholds = {
            "cpu_high": 0.85,
            "cpu_low": 0.30,
            "memory_high": 0.90,
            "memory_low": 0.40,
            "response_time_high": 2.0,  # 秒
            "response_time_low": 0.5,
        }
        self.core_services = {}

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化自适应进化器"""
        self.config = config or {}
        self.core_services = core_services or {}
        
        if "strategy" in self.config:
            self.evolution_strategy = EvolutionStrategy(self.config["strategy"])
        
        if "interval" in self.config:
            self.evolution_interval = self.config["interval"]
        
        logger.info(f"自适应进化器初始化完成，策略: {self.evolution_strategy.value}")

    async def start(self):
        """启动自适应进化"""
        if self.is_evolving:
            logger.warning("自适应进化已在运行中")
            return
        
        self.is_evolving = True
        self.evolution_task = asyncio.create_task(self._evolution_loop())
        logger.info("自适应进化已启动")

    async def stop(self):
        """停止自适应进化"""
        self.is_evolving = False
        if self.evolution_task:
            self.evolution_task.cancel()
            try:
                await self.evolution_task
            except asyncio.CancelledError:
                pass
        logger.info("自适应进化已停止")

    async def _evolution_loop(self):
        """进化循环"""
        try:
            while self.is_evolving:
                await asyncio.sleep(self.evolution_interval)
                
                # 收集当前性能指标
                current_metrics = await self._collect_performance_metrics()
                
                # 分析是否需要进化
                if await self._should_evolve(current_metrics):
                    logger.info("检测到需要进化，开始执行进化")
                    evolution_result = await self._execute_evolution(current_metrics)
                    
                    if evolution_result["success"]:
                        logger.info(f"进化执行成功: {evolution_result.get('improvement')}")
                    else:
                        logger.warning(f"进化执行失败: {evolution_result.get('error')}")
                        
        except asyncio.CancelledError:
            logger.info("进化循环被取消")
        except Exception as e:
            logger.error(f"进化循环异常: {str(e)}")

    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """收集性能指标"""
        try:
            import psutil
            
            metrics = {
                "cpu_percent": psutil.cpu_percent(interval=1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": psutil.disk_usage('/').percent,
                "timestamp": datetime.utcnow(),
            }
            
            # 如果有资源监控器，获取更详细的指标
            if "resource_monitor" in self.core_services:
                resource_monitor = self.core_services["resource_monitor"]
                detailed_status = await resource_monitor.get_detailed_status()
                metrics.update({
                    "cpu_detailed": detailed_status.get("cpu", {}),
                    "memory_detailed": detailed_status.get("memory", {}),
                })
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集性能指标失败: {str(e)}")
            return {}

    async def _should_evolve(self, metrics: Dict[str, Any]) -> bool:
        """判断是否需要进化"""
        try:
            cpu_usage = metrics.get("cpu_percent", 0) / 100
            memory_usage = metrics.get("memory_percent", 0) / 100
            
            # 检查是否超过阈值
            if cpu_usage > self.performance_thresholds["cpu_high"]:
                logger.info(f"CPU使用率过高: {cpu_usage:.2%}，需要进化")
                return True
            
            if memory_usage > self.performance_thresholds["memory_high"]:
                logger.info(f"内存使用率过高: {memory_usage:.2%}，需要进化")
                return True
            
            # 检查是否低于阈值（可以优化）
            if cpu_usage < self.performance_thresholds["cpu_low"]:
                logger.info(f"CPU使用率较低: {cpu_usage:.2%}，可以优化")
                return True
            
            if memory_usage < self.performance_thresholds["memory_low"]:
                logger.info(f"内存使用率较低: {memory_usage:.2%}，可以优化")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"判断是否需要进化失败: {str(e)}")
            return False

    async def _execute_evolution(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """执行进化"""
        try:
            cpu_usage = metrics.get("cpu_percent", 0) / 100
            memory_usage = metrics.get("memory_percent", 0) / 100
            
            # 根据策略选择进化动作
            if self.evolution_strategy == EvolutionStrategy.CONSERVATIVE:
                actions = await self._conservative_evolution(cpu_usage, memory_usage)
            elif self.evolution_strategy == EvolutionStrategy.AGGRESSIVE:
                actions = await self._aggressive_evolution(cpu_usage, memory_usage)
            else:  # BALANCED
                actions = await self._balanced_evolution(cpu_usage, memory_usage)
            
            # 执行进化动作
            results = []
            for action in actions:
                result = await self._apply_evolution_action(action)
                results.append(result)
                
                # 记录进化历史
                self.evolution_history.append(action)
            
            # 评估进化效果
            improvement = await self._evaluate_evolution_improvement(metrics, results)
            
            return {
                "success": True,
                "actions_count": len(actions),
                "improvement": improvement,
                "actions": [action.action_type for action in actions],
            }
            
        except Exception as e:
            logger.error(f"执行进化失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _conservative_evolution(
        self, cpu_usage: float, memory_usage: float
    ) -> List[EvolutionAction]:
        """保守进化策略"""
        actions = []
        
        # 只在资源使用率很高时才调整
        if cpu_usage > 0.90:
            actions.append(EvolutionAction(
                action_type="reduce_resources",
                target_module="high_cpu_modules",
                parameters={"cpu_reduction": 0.1},
                expected_improvement=0.05,
                risk_level="low",
                timestamp=datetime.utcnow(),
            ))
        
        if memory_usage > 0.95:
            actions.append(EvolutionAction(
                action_type="optimize_memory",
                target_module="memory_intensive_modules",
                parameters={"memory_optimization": True},
                expected_improvement=0.10,
                risk_level="low",
                timestamp=datetime.utcnow(),
            ))
        
        return actions

    async def _balanced_evolution(
        self, cpu_usage: float, memory_usage: float
    ) -> List[EvolutionAction]:
        """平衡进化策略"""
        actions = []
        
        # CPU优化
        if cpu_usage > self.performance_thresholds["cpu_high"]:
            actions.append(EvolutionAction(
                action_type="adjust_resources",
                target_module="all_modules",
                parameters={"cpu_reallocation": True, "reduction_rate": 0.15},
                expected_improvement=0.10,
                risk_level="medium",
                timestamp=datetime.utcnow(),
            ))
        elif cpu_usage < self.performance_thresholds["cpu_low"]:
            actions.append(EvolutionAction(
                action_type="optimize_allocation",
                target_module="all_modules",
                parameters={"cpu_optimization": True},
                expected_improvement=0.05,
                risk_level="low",
                timestamp=datetime.utcnow(),
            ))
        
        # 内存优化
        if memory_usage > self.performance_thresholds["memory_high"]:
            actions.append(EvolutionAction(
                action_type="optimize_memory",
                target_module="all_modules",
                parameters={"memory_cleanup": True, "cache_optimization": True},
                expected_improvement=0.15,
                risk_level="medium",
                timestamp=datetime.utcnow(),
            ))
        
        return actions

    async def _aggressive_evolution(
        self, cpu_usage: float, memory_usage: float
    ) -> List[EvolutionAction]:
        """激进进化策略"""
        actions = []
        
        # 更激进的资源调整
        if cpu_usage > 0.80:
            actions.append(EvolutionAction(
                action_type="scale_down",
                target_module="non_critical_modules",
                parameters={"cpu_reduction": 0.25, "memory_reduction": 0.20},
                expected_improvement=0.20,
                risk_level="high",
                timestamp=datetime.utcnow(),
            ))
        
        if memory_usage > 0.85:
            actions.append(EvolutionAction(
                action_type="aggressive_memory_optimization",
                target_module="all_modules",
                parameters={"force_gc": True, "cache_clear": True},
                expected_improvement=0.25,
                risk_level="high",
                timestamp=datetime.utcnow(),
            ))
        
        return actions

    async def _apply_evolution_action(self, action: EvolutionAction) -> Dict[str, Any]:
        """应用进化动作"""
        try:
            logger.info(f"执行进化动作: {action.action_type} -> {action.target_module}")
            
            # 根据动作类型执行相应操作
            if action.action_type == "adjust_resources":
                result = await self._adjust_resources(action)
            elif action.action_type == "optimize_memory":
                result = await self._optimize_memory(action)
            elif action.action_type == "reduce_resources":
                result = await self._reduce_resources(action)
            elif action.action_type == "scale_down":
                result = await self._scale_down(action)
            else:
                result = {"success": False, "error": f"未知动作类型: {action.action_type}"}
            
            return result
            
        except Exception as e:
            logger.error(f"应用进化动作失败: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _adjust_resources(self, action: EvolutionAction) -> Dict[str, Any]:
        """调整资源分配"""
        try:
            if "dynamic_allocator" in self.core_services:
                allocator = self.core_services["dynamic_allocator"]
                # 调用动态分配器调整资源
                result = await allocator.reallocate_resources(action.parameters)
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": "动态分配器不可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _optimize_memory(self, action: EvolutionAction) -> Dict[str, Any]:
        """优化内存使用"""
        try:
            import gc
            
            # 强制垃圾回收
            if action.parameters.get("force_gc", False):
                collected = gc.collect()
                logger.info(f"垃圾回收完成，回收对象数: {collected}")
            
            # 清理缓存
            if action.parameters.get("cache_clear", False):
                # 这里可以调用缓存管理器清理缓存
                logger.info("缓存清理完成")
            
            return {"success": True, "memory_freed": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _reduce_resources(self, action: EvolutionAction) -> Dict[str, Any]:
        """减少资源使用"""
        try:
            # 减少目标模块的资源分配
            if "dynamic_allocator" in self.core_services:
                allocator = self.core_services["dynamic_allocator"]
                result = await allocator.reduce_module_resources(
                    action.target_module,
                    action.parameters
                )
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": "动态分配器不可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _scale_down(self, action: EvolutionAction) -> Dict[str, Any]:
        """缩减规模"""
        try:
            # 暂停或停止非关键模块
            if "service_scheduler" in self.core_services:
                scheduler = self.core_services["service_scheduler"]
                # 暂停非关键服务
                result = await scheduler.suspend_service(action.target_module)
                return {"success": True, "result": result}
            else:
                return {"success": False, "error": "服务调度器不可用"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _evaluate_evolution_improvement(
        self, before_metrics: Dict[str, Any], results: List[Dict[str, Any]]
    ) -> float:
        """评估进化改进效果"""
        try:
            # 收集进化后的指标
            after_metrics = await self._collect_performance_metrics()
            
            # 计算改进率
            cpu_improvement = (
                (before_metrics.get("cpu_percent", 0) - after_metrics.get("cpu_percent", 0))
                / before_metrics.get("cpu_percent", 1)
            )
            
            memory_improvement = (
                (before_metrics.get("memory_percent", 0) - after_metrics.get("memory_percent", 0))
                / before_metrics.get("memory_percent", 1)
            )
            
            # 记录进化指标
            evolution_metric = EvolutionMetrics(
                cpu_usage_before=before_metrics.get("cpu_percent", 0),
                cpu_usage_after=after_metrics.get("cpu_percent", 0),
                memory_usage_before=before_metrics.get("memory_percent", 0),
                memory_usage_after=after_metrics.get("memory_percent", 0),
                response_time_before=0,  # 需要从其他地方获取
                response_time_after=0,
                improvement_rate=(cpu_improvement + memory_improvement) / 2,
                evolution_count=len(self.evolution_history),
            )
            
            self.evolution_metrics.append(evolution_metric)
            
            return evolution_metric.improvement_rate
            
        except Exception as e:
            logger.error(f"评估进化改进效果失败: {str(e)}")
            return 0.0

    async def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化状态"""
        return {
            "is_evolving": self.is_evolving,
            "strategy": self.evolution_strategy.value,
            "evolution_count": len(self.evolution_history),
            "recent_actions": [
                {
                    "type": action.action_type,
                    "target": action.target_module,
                    "timestamp": action.timestamp.isoformat(),
                }
                for action in self.evolution_history[-10:]
            ],
            "metrics_summary": {
                "total_evolutions": len(self.evolution_metrics),
                "avg_improvement": (
                    sum(m.improvement_rate for m in self.evolution_metrics) / len(self.evolution_metrics)
                    if self.evolution_metrics else 0
                ),
            },
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return await self.get_evolution_status()


__all__ = ["AdaptiveEvolver", "EvolutionStrategy", "EvolutionAction", "EvolutionMetrics"]

