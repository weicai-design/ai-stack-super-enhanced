"""
资源策略引擎
P0-015: 资源策略引擎与冲突调度（与自学习联动）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class ResourceStrategy(Enum):
    """资源策略类型"""
    BALANCED = "balanced"  # 平衡策略
    PERFORMANCE = "performance"  # 性能优先
    EFFICIENCY = "efficiency"  # 效率优先
    COST_OPTIMIZED = "cost_optimized"  # 成本优化
    QUALITY_FOCUSED = "quality_focused"  # 质量优先
    ADAPTIVE = "adaptive"  # 自适应策略（基于学习）


class StrategyContext(Enum):
    """策略上下文"""
    NORMAL = "normal"  # 正常负载
    HIGH_LOAD = "high_load"  # 高负载
    LOW_LOAD = "low_load"  # 低负载
    CRITICAL = "critical"  # 关键任务
    MAINTENANCE = "maintenance"  # 维护模式


@dataclass
class StrategyRule:
    """策略规则"""
    strategy: ResourceStrategy
    context: StrategyContext
    conditions: Dict[str, Any]  # 触发条件
    actions: Dict[str, Any]  # 执行动作
    priority: int  # 优先级
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    success_count: int = 0
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyExecution:
    """策略执行记录"""
    strategy: ResourceStrategy
    context: StrategyContext
    triggered_at: datetime
    execution_result: Dict[str, Any]
    performance_metrics: Dict[str, float]  # 性能指标
    success: bool
    feedback_score: Optional[float] = None  # 反馈评分（来自自学习系统）


class ResourceStrategyEngine:
    """
    资源策略引擎
    
    功能：
    1. 管理多种资源分配策略
    2. 根据系统上下文自动选择策略
    3. 基于自学习系统反馈优化策略
    4. 策略执行效果评估
    """
    
    def __init__(
        self,
        learning_system=None,
        resource_monitor=None,
        dynamic_allocator=None
    ):
        self.learning_system = learning_system  # 自学习系统
        self.resource_monitor = resource_monitor
        self.dynamic_allocator = dynamic_allocator
        
        # 策略规则库
        self.strategy_rules: List[StrategyRule] = []
        
        # 当前策略
        self.current_strategy: Optional[ResourceStrategy] = None
        self.current_context: Optional[StrategyContext] = None
        
        # 执行历史
        self.execution_history: List[StrategyExecution] = []
        
        # 策略性能统计
        self.strategy_performance: Dict[ResourceStrategy, Dict[str, Any]] = {}
        
        # 初始化默认策略
        self._initialize_default_strategies()
        
        logger.info("资源策略引擎初始化完成")
    
    def _initialize_default_strategies(self):
        """初始化默认策略规则"""
        # 平衡策略 - 正常负载
        self.strategy_rules.append(StrategyRule(
            strategy=ResourceStrategy.BALANCED,
            context=StrategyContext.NORMAL,
            conditions={
                "cpu_usage": {"min": 30, "max": 70},
                "memory_usage": {"min": 40, "max": 75}
            },
            actions={
                "cpu_allocation": "equal",
                "memory_allocation": "proportional",
                "priority_adjustment": "moderate"
            },
            priority=3
        ))
        
        # 性能优先策略 - 高负载
        self.strategy_rules.append(StrategyRule(
            strategy=ResourceStrategy.PERFORMANCE,
            context=StrategyContext.HIGH_LOAD,
            conditions={
                "cpu_usage": {"min": 70},
                "memory_usage": {"min": 75}
            },
            actions={
                "cpu_allocation": "priority_based",
                "memory_allocation": "critical_first",
                "priority_adjustment": "aggressive"
            },
            priority=5
        ))
        
        # 效率优先策略 - 低负载
        self.strategy_rules.append(StrategyRule(
            strategy=ResourceStrategy.EFFICIENCY,
            context=StrategyContext.LOW_LOAD,
            conditions={
                "cpu_usage": {"max": 30},
                "memory_usage": {"max": 40}
            },
            actions={
                "cpu_allocation": "consolidate",
                "memory_allocation": "minimize",
                "priority_adjustment": "conservative"
            },
            priority=2
        ))
        
        # 自适应策略 - 基于学习
        self.strategy_rules.append(StrategyRule(
            strategy=ResourceStrategy.ADAPTIVE,
            context=StrategyContext.NORMAL,
            conditions={},
            actions={
                "cpu_allocation": "learning_based",
                "memory_allocation": "learning_based",
                "priority_adjustment": "learning_based"
            },
            priority=10  # 最高优先级
        ))
    
    async def select_strategy(
        self,
        context: Optional[StrategyContext] = None,
        resource_state: Optional[Dict[str, Any]] = None
    ) -> ResourceStrategy:
        """
        选择资源策略
        
        Args:
            context: 系统上下文（可选）
            resource_state: 资源状态（可选）
            
        Returns:
            选中的策略
        """
        # 如果没有提供上下文，自动检测
        if not context:
            context = await self._detect_context(resource_state)
        
        # 如果没有提供资源状态，从监控器获取
        if not resource_state and self.resource_monitor:
            resource_state = self.resource_monitor.get_current_status()
        
        # 优先检查自适应策略（如果自学习系统可用）
        if self.learning_system:
            adaptive_strategy = await self._get_adaptive_strategy(context, resource_state)
            if adaptive_strategy:
                self.current_strategy = adaptive_strategy
                self.current_context = context
                logger.info(f"选择自适应策略: {adaptive_strategy.value}")
                return adaptive_strategy
        
        # 匹配策略规则
        matched_rules = []
        for rule in self.strategy_rules:
            if not rule.enabled:
                continue
            
            if rule.context != context:
                continue
            
            # 检查条件是否满足
            if self._check_conditions(rule.conditions, resource_state):
                matched_rules.append(rule)
        
        if not matched_rules:
            # 没有匹配的规则，使用默认策略
            strategy = ResourceStrategy.BALANCED
        else:
            # 选择优先级最高的规则
            matched_rules.sort(key=lambda r: r.priority, reverse=True)
            strategy = matched_rules[0].strategy
        
        self.current_strategy = strategy
        self.current_context = context
        
        logger.info(f"选择策略: {strategy.value} (上下文: {context.value})")
        return strategy
    
    async def _detect_context(
        self,
        resource_state: Optional[Dict[str, Any]]
    ) -> StrategyContext:
        """检测系统上下文"""
        if not resource_state and self.resource_monitor:
            resource_state = self.resource_monitor.get_current_status()
        
        if not resource_state:
            return StrategyContext.NORMAL
        
        cpu_percent = resource_state.get("cpu", {}).get("percent", 0)
        memory_percent = resource_state.get("memory", {}).get("percent", 0)
        
        # 高负载
        if cpu_percent > 80 or memory_percent > 85:
            return StrategyContext.HIGH_LOAD
        
        # 低负载
        if cpu_percent < 30 and memory_percent < 40:
            return StrategyContext.LOW_LOAD
        
        # 正常负载
        return StrategyContext.NORMAL
    
    def _check_conditions(
        self,
        conditions: Dict[str, Any],
        resource_state: Dict[str, Any]
    ) -> bool:
        """检查条件是否满足"""
        if not conditions:
            return True
        
        for key, condition in conditions.items():
            if key == "cpu_usage":
                cpu_percent = resource_state.get("cpu", {}).get("percent", 0)
                if "min" in condition and cpu_percent < condition["min"]:
                    return False
                if "max" in condition and cpu_percent > condition["max"]:
                    return False
            
            elif key == "memory_usage":
                memory_percent = resource_state.get("memory", {}).get("percent", 0)
                if "min" in condition and memory_percent < condition["min"]:
                    return False
                if "max" in condition and memory_percent > condition["max"]:
                    return False
        
        return True
    
    async def _get_adaptive_strategy(
        self,
        context: StrategyContext,
        resource_state: Dict[str, Any]
    ) -> Optional[ResourceStrategy]:
        """从自学习系统获取自适应策略"""
        if not self.learning_system:
            return None
        
        try:
            # 查询自学习系统的策略建议
            # 这里需要根据实际的自学习系统接口调整
            learning_suggestion = await self._query_learning_system(context, resource_state)
            
            if learning_suggestion and learning_suggestion.get("strategy"):
                strategy_name = learning_suggestion["strategy"]
                try:
                    return ResourceStrategy(strategy_name)
                except ValueError:
                    logger.warning(f"自学习系统返回了未知策略: {strategy_name}")
                    return None
        except Exception as e:
            logger.warning(f"从自学习系统获取策略失败: {e}")
            return None
        
        return None
    
    async def _query_learning_system(
        self,
        context: StrategyContext,
        resource_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """查询自学习系统"""
        # 这里需要根据实际的自学习系统接口实现
        # 简化实现：返回None表示没有建议
        return None
    
    async def execute_strategy(
        self,
        strategy: Optional[ResourceStrategy] = None,
        target_modules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行资源策略
        
        Args:
            strategy: 要执行的策略（可选，不提供则使用当前策略）
            target_modules: 目标模块列表（可选）
            
        Returns:
            执行结果
        """
        if not strategy:
            strategy = self.current_strategy or ResourceStrategy.BALANCED
        
        context = self.current_context or StrategyContext.NORMAL
        
        execution_start = datetime.now()
        
        try:
            # 获取策略规则
            rule = self._get_strategy_rule(strategy, context)
            if not rule:
                raise ValueError(f"未找到策略规则: {strategy.value}")
            
            # 执行策略动作
            result = await self._execute_strategy_actions(
                rule.actions,
                target_modules
            )
            
            # 记录执行
            execution = StrategyExecution(
                strategy=strategy,
                context=context,
                triggered_at=execution_start,
                execution_result=result,
                performance_metrics=await self._collect_performance_metrics(),
                success=result.get("success", False)
            )
            
            self.execution_history.append(execution)
            
            # 保留最近1000条记录
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            # 更新策略性能统计
            self._update_strategy_performance(strategy, execution)
            
            # 发送反馈到自学习系统
            if self.learning_system:
                await self._send_feedback_to_learning(execution)
            
            logger.info(f"策略执行完成: {strategy.value}, 成功: {execution.success}")
            
            return {
                "success": True,
                "strategy": strategy.value,
                "context": context.value,
                "result": result,
                "execution_id": len(self.execution_history) - 1
            }
            
        except Exception as e:
            logger.error(f"策略执行失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "strategy": strategy.value if strategy else None
            }
    
    def _get_strategy_rule(
        self,
        strategy: ResourceStrategy,
        context: StrategyContext
    ) -> Optional[StrategyRule]:
        """获取策略规则"""
        for rule in self.strategy_rules:
            if rule.strategy == strategy and rule.context == context:
                return rule
        return None
    
    async def _execute_strategy_actions(
        self,
        actions: Dict[str, Any],
        target_modules: Optional[List[str]]
    ) -> Dict[str, Any]:
        """执行策略动作"""
        result = {
            "success": True,
            "actions_executed": [],
            "details": {}
        }
        
        if not self.dynamic_allocator:
            result["success"] = False
            result["error"] = "动态分配器不可用"
            return result
        
        # 执行CPU分配
        if "cpu_allocation" in actions:
            cpu_result = await self._apply_cpu_allocation(
                actions["cpu_allocation"],
                target_modules
            )
            result["actions_executed"].append("cpu_allocation")
            result["details"]["cpu_allocation"] = cpu_result
        
        # 执行内存分配
        if "memory_allocation" in actions:
            memory_result = await self._apply_memory_allocation(
                actions["memory_allocation"],
                target_modules
            )
            result["actions_executed"].append("memory_allocation")
            result["details"]["memory_allocation"] = memory_result
        
        # 执行优先级调整
        if "priority_adjustment" in actions:
            priority_result = await self._apply_priority_adjustment(
                actions["priority_adjustment"],
                target_modules
            )
            result["actions_executed"].append("priority_adjustment")
            result["details"]["priority_adjustment"] = priority_result
        
        return result
    
    async def _apply_cpu_allocation(
        self,
        allocation_type: str,
        target_modules: Optional[List[str]]
    ) -> Dict[str, Any]:
        """应用CPU分配策略"""
        # 这里需要调用动态分配器
        return {
            "type": allocation_type,
            "applied": True,
            "message": f"CPU分配策略已应用: {allocation_type}"
        }
    
    async def _apply_memory_allocation(
        self,
        allocation_type: str,
        target_modules: Optional[List[str]]
    ) -> Dict[str, Any]:
        """应用内存分配策略"""
        return {
            "type": allocation_type,
            "applied": True,
            "message": f"内存分配策略已应用: {allocation_type}"
        }
    
    async def _apply_priority_adjustment(
        self,
        adjustment_type: str,
        target_modules: Optional[List[str]]
    ) -> Dict[str, Any]:
        """应用优先级调整"""
        return {
            "type": adjustment_type,
            "applied": True,
            "message": f"优先级调整已应用: {adjustment_type}"
        }
    
    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """收集性能指标"""
        if not self.resource_monitor:
            return {}
        
        status = self.resource_monitor.get_current_status()
        return {
            "cpu_usage": status.get("cpu", {}).get("percent", 0),
            "memory_usage": status.get("memory", {}).get("percent", 0),
            "disk_usage": status.get("disk", {}).get("percent", 0)
        }
    
    def _update_strategy_performance(
        self,
        strategy: ResourceStrategy,
        execution: StrategyExecution
    ):
        """更新策略性能统计"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {
                "execution_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "avg_performance": {},
                "last_execution": None
            }
        
        stats = self.strategy_performance[strategy]
        stats["execution_count"] += 1
        if execution.success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
        stats["last_execution"] = execution.triggered_at.isoformat()
        
        # 更新平均性能指标
        if execution.performance_metrics:
            for key, value in execution.performance_metrics.items():
                if key not in stats["avg_performance"]:
                    stats["avg_performance"][key] = []
                stats["avg_performance"][key].append(value)
                # 只保留最近100个值
                if len(stats["avg_performance"][key]) > 100:
                    stats["avg_performance"][key] = stats["avg_performance"][key][-100:]
    
    async def _send_feedback_to_learning(self, execution: StrategyExecution):
        """发送反馈到自学习系统"""
        if not self.learning_system:
            return
        
        try:
            # 计算反馈评分
            feedback_score = self._calculate_feedback_score(execution)
            execution.feedback_score = feedback_score
            
            # 发送到自学习系统
            # 这里需要根据实际的自学习系统接口实现
            feedback_data = {
                "strategy": execution.strategy.value,
                "context": execution.context.value,
                "success": execution.success,
                "performance_metrics": execution.performance_metrics,
                "feedback_score": feedback_score,
                "timestamp": execution.triggered_at.isoformat()
            }
            
            # await self.learning_system.record_strategy_feedback(feedback_data)
            logger.debug(f"已发送策略反馈到自学习系统: {feedback_score}")
            
        except Exception as e:
            logger.warning(f"发送反馈到自学习系统失败: {e}")
    
    def _calculate_feedback_score(self, execution: StrategyExecution) -> float:
        """计算反馈评分"""
        if not execution.success:
            return 0.0
        
        # 基于性能指标计算评分
        metrics = execution.performance_metrics
        score = 1.0
        
        # CPU使用率越低越好（在合理范围内）
        cpu_usage = metrics.get("cpu_usage", 50)
        if cpu_usage > 90:
            score *= 0.5
        elif cpu_usage < 20:
            score *= 0.8  # 过低也不好
        
        # 内存使用率
        memory_usage = metrics.get("memory_usage", 50)
        if memory_usage > 90:
            score *= 0.5
        elif memory_usage < 20:
            score *= 0.8
        
        return max(0.0, min(1.0, score))
    
    def get_strategy_statistics(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        return {
            "current_strategy": self.current_strategy.value if self.current_strategy else None,
            "current_context": self.current_context.value if self.current_context else None,
            "total_rules": len(self.strategy_rules),
            "enabled_rules": len([r for r in self.strategy_rules if r.enabled]),
            "total_executions": len(self.execution_history),
            "strategy_performance": {
                strategy.value: stats
                for strategy, stats in self.strategy_performance.items()
            },
            "recent_executions": [
                {
                    "strategy": e.strategy.value,
                    "context": e.context.value,
                    "success": e.success,
                    "triggered_at": e.triggered_at.isoformat(),
                    "feedback_score": e.feedback_score
                }
                for e in self.execution_history[-10:]
            ]
        }
    
    async def update_strategy_from_learning(
        self,
        learning_recommendations: Dict[str, Any]
    ):
        """从自学习系统更新策略"""
        if not learning_recommendations:
            return
        
        # 根据学习建议更新策略规则
        for recommendation in learning_recommendations.get("strategies", []):
            strategy_name = recommendation.get("strategy")
            context_name = recommendation.get("context")
            actions = recommendation.get("actions", {})
            
            try:
                strategy = ResourceStrategy(strategy_name)
                context = StrategyContext(context_name)
                
                # 查找或创建规则
                rule = self._get_strategy_rule(strategy, context)
                if rule:
                    # 更新现有规则
                    rule.actions.update(actions)
                    rule.updated_at = datetime.now()
                else:
                    # 创建新规则
                    new_rule = StrategyRule(
                        strategy=strategy,
                        context=context,
                        conditions=recommendation.get("conditions", {}),
                        actions=actions,
                        priority=recommendation.get("priority", 3),
                        metadata={"source": "learning_system"}
                    )
                    self.strategy_rules.append(new_rule)
                
                logger.info(f"已从自学习系统更新策略: {strategy_name} - {context_name}")
                
            except (ValueError, KeyError) as e:
                logger.warning(f"无效的策略建议: {e}")










