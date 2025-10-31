#!/usr/bin/env python3
"""
智能优先级管理系统
功能：基于多维度因素动态计算和调整系统资源分配优先级
对应需求：8.1/8.2/8.5 - 资源动态调配、冲突解决、自适应调整
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class PriorityLevel(Enum):
    """优先级级别定义"""

    CRITICAL = 100  # 关键任务，系统核心功能
    HIGH = 75  # 高优先级，直接影响用户体验
    MEDIUM = 50  # 中等优先级，业务重要功能
    LOW = 25  # 低优先级，后台处理任务
    BACKGROUND = 10  # 后台任务，资源空闲时执行


@dataclass
class PriorityFactor:
    """优先级计算因子"""

    business_importance: float = 0.0  # 业务重要性 0-1
    user_impact: float = 0.0  # 用户影响度 0-1
    time_sensitivity: float = 0.0  # 时间敏感性 0-1
    resource_efficiency: float = 0.0  # 资源效率 0-1
    historical_performance: float = 0.0  # 历史性能 0-1
    dependency_level: float = 0.0  # 依赖级别 0-1


class PriorityIntelligence:
    """
    智能优先级管理器
    基于多维度因素动态计算和调整系统资源分配优先级
    """

    def __init__(self, resource_manager=None, event_bus=None):
        self.resource_manager = resource_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # 优先级配置
        self.priority_weights = {
            "business_importance": 0.25,
            "user_impact": 0.20,
            "time_sensitivity": 0.20,
            "resource_efficiency": 0.15,
            "historical_performance": 0.10,
            "dependency_level": 0.10,
        }

        # 模块优先级历史记录
        self.module_priority_history = {}

        # 实时优先级缓存
        self.current_priorities = {}

        # 自适应学习参数
        self.learning_rate = 0.1
        self.performance_threshold = 0.8

        self.initialized = False

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化优先级智能管理器"""
        try:
            self.logger.info("初始化智能优先级管理系统...")

            if core_services:
                self.resource_manager = core_services.get("resource_manager")
                self.event_bus = core_services.get("event_bus")

            # 加载配置
            if config:
                self._load_config(config)

            # 初始化模块优先级基准
            await self._initialize_module_priorities()

            # 启动优先级监控任务
            asyncio.create_task(self._priority_monitoring_loop())

            self.initialized = True
            self.logger.info("智能优先级管理系统初始化完成")

        except Exception as e:
            self.logger.error(f"优先级管理系统初始化失败: {e}", exc_info=True)
            raise

    def _load_config(self, config: Dict):
        """加载优先级配置"""
        priority_config = config.get("priority_intelligence", {})

        if "weights" in priority_config:
            self.priority_weights.update(priority_config["weights"])

        if "learning_rate" in priority_config:
            self.learning_rate = priority_config["learning_rate"]

        if "performance_threshold" in priority_config:
            self.performance_threshold = priority_config["performance_threshold"]

    async def _initialize_module_priorities(self):
        """初始化模块优先级基准"""
        base_priorities = {
            "rag_engine": PriorityFactor(0.9, 0.8, 0.7, 0.6, 0.8, 0.9),
            "erp_core": PriorityFactor(0.8, 0.7, 0.6, 0.5, 0.7, 0.8),
            "stock_trading": PriorityFactor(0.7, 0.6, 0.9, 0.4, 0.6, 0.7),
            "content_creation": PriorityFactor(0.6, 0.5, 0.5, 0.7, 0.5, 0.6),
            "trend_analysis": PriorityFactor(0.5, 0.4, 0.4, 0.8, 0.4, 0.5),
            "task_agent": PriorityFactor(0.7, 0.6, 0.8, 0.5, 0.6, 0.7),
            "openwebui": PriorityFactor(0.9, 0.9, 0.8, 0.6, 0.8, 0.9),
        }

        for module_name, factors in base_priorities.items():
            priority_score = self._calculate_priority_score(factors)
            priority_level = self._score_to_priority_level(priority_score)

            self.current_priorities[module_name] = {
                "score": priority_score,
                "level": priority_level,
                "factors": factors,
                "last_updated": datetime.now(),
            }

            self.module_priority_history[module_name] = [
                {
                    "timestamp": datetime.now(),
                    "score": priority_score,
                    "level": priority_level,
                    "factors": factors,
                }
            ]

    def _calculate_priority_score(self, factors: PriorityFactor) -> float:
        """计算优先级分数"""
        score = 0.0

        for factor_name, weight in self.priority_weights.items():
            factor_value = getattr(factors, factor_name, 0.0)
            score += factor_value * weight

        return min(max(score, 0.0), 1.0)

    def _score_to_priority_level(self, score: float) -> PriorityLevel:
        """将分数转换为优先级级别"""
        if score >= 0.9:
            return PriorityLevel.CRITICAL
        elif score >= 0.7:
            return PriorityLevel.HIGH
        elif score >= 0.5:
            return PriorityLevel.MEDIUM
        elif score >= 0.3:
            return PriorityLevel.LOW
        else:
            return PriorityLevel.BACKGROUND

    async def calculate_module_priority(
        self, module_name: str, current_factors: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        计算模块优先级
        """
        try:
            # 获取基础因子
            if module_name in self.current_priorities:
                base_factors = self.current_priorities[module_name]["factors"]
            else:
                base_factors = PriorityFactor()

            # 更新实时因子
            if current_factors:
                for factor_name, value in current_factors.items():
                    if hasattr(base_factors, factor_name):
                        setattr(base_factors, factor_name, value)

            # 考虑系统状态调整
            await self._adjust_factors_by_system_state(base_factors, module_name)

            # 计算最终分数和级别
            final_score = self._calculate_priority_score(base_factors)
            final_level = self._score_to_priority_level(final_score)

            # 记录历史
            history_entry = {
                "timestamp": datetime.now(),
                "score": final_score,
                "level": final_level,
                "factors": base_factors,
            }

            if module_name not in self.module_priority_history:
                self.module_priority_history[module_name] = []

            self.module_priority_history[module_name].append(history_entry)

            # 更新当前优先级
            self.current_priorities[module_name] = {
                "score": final_score,
                "level": final_level,
                "factors": base_factors,
                "last_updated": datetime.now(),
            }

            # 发布优先级更新事件
            if self.event_bus:
                await self.event_bus.publish(
                    "priority.updated",
                    {
                        "module": module_name,
                        "priority_score": final_score,
                        "priority_level": final_level.name,
                        "factors": self._factors_to_dict(base_factors),
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return {
                "module": module_name,
                "priority_score": final_score,
                "priority_level": final_level,
                "factors": base_factors,
                "resource_allocation": self._get_resource_allocation(final_level),
            }

        except Exception as e:
            self.logger.error(f"计算模块优先级失败 {module_name}: {e}")
            # 返回默认优先级
            return {
                "module": module_name,
                "priority_score": 0.5,
                "priority_level": PriorityLevel.MEDIUM,
                "factors": PriorityFactor(),
                "resource_allocation": self._get_resource_allocation(
                    PriorityLevel.MEDIUM
                ),
            }

    async def _adjust_factors_by_system_state(
        self, factors: PriorityFactor, module_name: str
    ):
        """根据系统状态调整因子"""
        if not self.resource_manager:
            return

        try:
            # 获取系统资源状态
            system_status = await self.resource_manager.get_detailed_status()

            # 根据CPU使用率调整资源效率因子
            cpu_usage = system_status["cpu"]["usage_fraction"]
            if cpu_usage > 0.8:  # 高负载时优先资源效率高的模块
                factors.resource_efficiency *= 1.2
            elif cpu_usage < 0.3:  # 低负载时放宽限制
                factors.resource_efficiency *= 0.8

            # 根据内存使用率调整
            memory_usage = system_status["memory"]["usage_fraction"]
            if memory_usage > 0.85:
                # 内存紧张时，降低内存密集型模块的优先级
                if module_name in ["rag_engine", "trend_analysis"]:
                    factors.resource_efficiency *= 0.7

            # 限制因子范围
            for field in factors.__dataclass_fields__:
                value = getattr(factors, field)
                setattr(factors, field, min(max(value, 0.0), 1.0))

        except Exception as e:
            self.logger.warning(f"系统状态调整因子失败: {e}")

    def _get_resource_allocation(
        self, priority_level: PriorityLevel
    ) -> Dict[str, float]:
        """根据优先级级别获取资源分配比例"""
        allocation_map = {
            PriorityLevel.CRITICAL: {"cpu": 0.3, "memory": 0.3, "gpu": 0.4},
            PriorityLevel.HIGH: {"cpu": 0.2, "memory": 0.2, "gpu": 0.3},
            PriorityLevel.MEDIUM: {"cpu": 0.15, "memory": 0.15, "gpu": 0.2},
            PriorityLevel.LOW: {"cpu": 0.1, "memory": 0.1, "gpu": 0.1},
            PriorityLevel.BACKGROUND: {"cpu": 0.05, "memory": 0.05, "gpu": 0.0},
        }
        return allocation_map.get(
            priority_level, {"cpu": 0.1, "memory": 0.1, "gpu": 0.1}
        )

    async def get_priority_recommendations(self) -> List[Dict[str, Any]]:
        """获取优先级调整建议"""
        recommendations = []

        for module_name, priority_data in self.current_priorities.items():
            current_score = priority_data["score"]
            factors = priority_data["factors"]

            # 分析性能提升潜力
            improvement_potential = self._calculate_improvement_potential(factors)

            if improvement_potential > 0.1:  # 有显著提升空间
                recommendations.append(
                    {
                        "module": module_name,
                        "current_priority": priority_data["level"].name,
                        "improvement_potential": improvement_potential,
                        "suggested_actions": self._get_suggested_actions(factors),
                        "expected_impact": (
                            "high" if improvement_potential > 0.3 else "medium"
                        ),
                    }
                )

        # 按提升潜力排序
        recommendations.sort(key=lambda x: x["improvement_potential"], reverse=True)
        return recommendations

    def _calculate_improvement_potential(self, factors: PriorityFactor) -> float:
        """计算改进潜力"""
        # 找出最低的因子，改进空间最大
        factor_values = [
            getattr(factors, field) for field in factors.__dataclass_fields__
        ]
        min_factor = min(factor_values)
        return 1.0 - min_factor

    def _get_suggested_actions(self, factors: PriorityFactor) -> List[str]:
        """获取改进建议"""
        actions = []
        low_threshold = 0.3

        if factors.business_importance < low_threshold:
            actions.append("提升业务逻辑重要性")
        if factors.user_impact < low_threshold:
            actions.append("优化用户体验设计")
        if factors.time_sensitivity < low_threshold:
            actions.append("改进任务调度及时性")
        if factors.resource_efficiency < low_threshold:
            actions.append("优化资源使用效率")
        if factors.historical_performance < low_threshold:
            actions.append("修复历史性能问题")
        if factors.dependency_level < low_threshold:
            actions.append("减少模块间依赖")

        return actions

    async def resolve_priority_conflict(
        self, conflicting_modules: List[str]
    ) -> Dict[str, Any]:
        """解决优先级冲突"""
        if len(conflicting_modules) < 2:
            return {"resolved": True, "decision": "无需解决"}

        # 获取各模块优先级信息
        module_priorities = {}
        for module in conflicting_modules:
            if module in self.current_priorities:
                module_priorities[module] = self.current_priorities[module]

        if not module_priorities:
            return {"resolved": False, "error": "无优先级信息"}

        # 按优先级分数排序
        sorted_modules = sorted(
            module_priorities.items(), key=lambda x: x[1]["score"], reverse=True
        )

        winner_module = sorted_modules[0][0]
        winner_score = sorted_modules[0][1]["score"]

        # 检查是否需要人工干预（分数接近时）
        needs_human_intervention = False
        if len(sorted_modules) >= 2:
            second_score = sorted_modules[1][1]["score"]
            if abs(winner_score - second_score) < 0.1:  # 分数差距小于0.1
                needs_human_intervention = True

        resolution = {
            "resolved": not needs_human_intervention,
            "winner_module": winner_module,
            "winner_priority_score": winner_score,
            "conflicting_modules": conflicting_modules,
            "needs_human_intervention": needs_human_intervention,
            "timestamp": datetime.now().isoformat(),
        }

        if needs_human_intervention:
            resolution["suggestion"] = (
                f"建议人工干预：{winner_module} 和 {sorted_modules[1][0]} 优先级接近"
            )

        # 发布冲突解决事件
        if self.event_bus:
            await self.event_bus.publish("priority.conflict_resolved", resolution)

        return resolution

    async def _priority_monitoring_loop(self):
        """优先级监控循环"""
        while True:
            try:
                # 每30秒更新一次优先级
                await asyncio.sleep(30)

                # 更新所有模块的优先级
                for module_name in list(self.current_priorities.keys()):
                    await self.calculate_module_priority(module_name)

                self.logger.debug("优先级监控循环完成")

            except Exception as e:
                self.logger.error(f"优先级监控循环错误: {e}")
                await asyncio.sleep(10)  # 出错时短暂等待

    def _factors_to_dict(self, factors: PriorityFactor) -> Dict[str, float]:
        """将因子对象转换为字典"""
        return {
            field: getattr(factors, field) for field in factors.__dataclass_fields__
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy" if self.initialized else "initializing",
            "modules_tracked": len(self.current_priorities),
            "last_updated": datetime.now().isoformat(),
            "performance_metrics": {
                "calculation_accuracy": 0.95,  # 模拟指标
                "conflict_resolution_rate": 0.92,
                "adaptation_speed": 0.88,
            },
        }

    async def stop(self):
        """停止优先级管理器"""
        self.logger.info("停止智能优先级管理系统")
        self.initialized = False
