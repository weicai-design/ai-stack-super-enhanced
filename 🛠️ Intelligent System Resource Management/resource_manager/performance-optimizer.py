#!/usr/bin/env python3
"""
智能性能优化器
功能：基于实时性能数据和历史模式，动态优化系统性能配置
对应需求：8.1/8.5/9.1 - 资源动态调配、自适应调整、自我学习
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List

import numpy as np
import psutil

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """优化策略类型"""

    RESOURCE_ALLOCATION = "resource_allocation"
    MEMORY_MANAGEMENT = "memory_management"
    CPU_SCHEDULING = "cpu_scheduling"
    CACHE_OPTIMIZATION = "cache_optimization"
    NETWORK_OPTIMIZATION = "network_optimization"


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_io: float
    network_io: float
    response_time: float
    throughput: float
    error_rate: float


@dataclass
class OptimizationAction:
    """优化动作"""

    strategy: OptimizationStrategy
    module: str
    parameter: str
    value: Any
    confidence: float
    expected_improvement: float


class PerformanceOptimizer:
    """
    智能性能优化器
    基于实时性能数据和历史模式，动态优化系统性能配置
    """

    def __init__(self, resource_manager=None, event_bus=None):
        self.resource_manager = resource_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(__name__)

        # 性能数据存储
        self.performance_history = {}
        self.optimization_history = []

        # 优化配置
        self.optimization_config = {
            "cpu_threshold_high": 0.8,
            "cpu_threshold_low": 0.3,
            "memory_threshold_high": 0.85,
            "memory_threshold_low": 0.4,
            "response_time_threshold": 2.0,  # 秒
            "throughput_threshold": 100,  # 请求/秒
            "learning_window": 3600,  # 学习窗口（秒）
            "optimization_interval": 60,  # 优化间隔（秒）
        }

        # 机器学习模型参数（简化版）
        self.performance_patterns = {}
        self.optimization_models = {}

        self.initialized = False
        self.optimization_enabled = True

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化性能优化器"""
        try:
            self.logger.info("初始化智能性能优化器...")

            if core_services:
                self.resource_manager = core_services.get("resource_manager")
                self.event_bus = core_services.get("event_bus")

            # 加载配置
            if config:
                self._load_optimization_config(config)

            # 初始化性能基准
            await self._initialize_performance_baseline()

            # 启动优化监控循环
            asyncio.create_task(self._optimization_loop())

            self.initialized = True
            self.logger.info("智能性能优化器初始化完成")

        except Exception as e:
            self.logger.error(f"性能优化器初始化失败: {e}", exc_info=True)
            raise

    def _load_optimization_config(self, config: Dict):
        """加载优化配置"""
        opt_config = config.get("performance_optimizer", {})
        self.optimization_config.update(opt_config)

        # 模块特定配置
        self.module_configs = config.get("module_optimizations", {})

    async def _initialize_performance_baseline(self):
        """初始化性能基准"""
        self.logger.info("初始化性能基准...")

        # 初始性能基准
        self.performance_baseline = {
            "cpu_usage": 0.3,
            "memory_usage": 0.4,
            "response_time": 1.0,
            "throughput": 50,
            "error_rate": 0.01,
        }

        # 为每个模块初始化性能历史
        initial_modules = [
            "rag_engine",
            "erp_core",
            "stock_trading",
            "content_creation",
            "trend_analysis",
            "task_agent",
            "openwebui",
        ]

        for module in initial_modules:
            self.performance_history[module] = []

    async def collect_performance_metrics(self, module_name: str) -> PerformanceMetrics:
        """收集模块性能指标"""
        try:
            # 获取系统级指标
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # 模拟模块特定指标（实际实现中应从模块获取）
            response_time = await self._measure_response_time(module_name)
            throughput = await self._measure_throughput(module_name)
            error_rate = await self._measure_error_rate(module_name)

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage=cpu_percent / 100.0,
                memory_usage=memory.percent / 100.0,
                disk_io=0.0,  # 简化实现
                network_io=0.0,  # 简化实现
                response_time=response_time,
                throughput=throughput,
                error_rate=error_rate,
            )

            # 存储性能数据
            if module_name not in self.performance_history:
                self.performance_history[module_name] = []

            self.performance_history[module_name].append(metrics)

            # 保持历史数据在时间窗口内
            self._cleanup_old_metrics(module_name)

            return metrics

        except Exception as e:
            self.logger.error(f"收集性能指标失败 {module_name}: {e}")
            # 返回默认指标
            return PerformanceMetrics(
                timestamp=datetime.now(),
                cpu_usage=0.5,
                memory_usage=0.5,
                disk_io=0.0,
                network_io=0.0,
                response_time=1.0,
                throughput=50.0,
                error_rate=0.05,
            )

    async def _measure_response_time(self, module_name: str) -> float:
        """测量响应时间"""
        # 模拟实现 - 实际应从模块API获取
        base_times = {
            "rag_engine": 0.8,
            "erp_core": 1.2,
            "stock_trading": 0.5,
            "content_creation": 2.0,
            "trend_analysis": 1.5,
            "task_agent": 0.7,
            "openwebui": 0.3,
        }
        return base_times.get(module_name, 1.0) * (0.8 + 0.4 * np.random.random())

    async def _measure_throughput(self, module_name: str) -> float:
        """测量吞吐量"""
        # 模拟实现
        base_throughput = {
            "rag_engine": 80,
            "erp_core": 60,
            "stock_trading": 100,
            "content_creation": 40,
            "trend_analysis": 50,
            "task_agent": 70,
            "openwebui": 120,
        }
        return base_throughput.get(module_name, 50) * (0.8 + 0.4 * np.random.random())

    async def _measure_error_rate(self, module_name: str) -> float:
        """测量错误率"""
        # 模拟实现
        base_rates = {
            "rag_engine": 0.02,
            "erp_core": 0.01,
            "stock_trading": 0.03,
            "content_creation": 0.04,
            "trend_analysis": 0.025,
            "task_agent": 0.015,
            "openwebui": 0.005,
        }
        return base_rates.get(module_name, 0.02) * (0.5 + np.random.random())

    def _cleanup_old_metrics(self, module_name: str):
        """清理过期性能指标"""
        if module_name not in self.performance_history:
            return

        window_seconds = self.optimization_config["learning_window"]
        cutoff_time = datetime.now() - timedelta(seconds=window_seconds)

        self.performance_history[module_name] = [
            metrics
            for metrics in self.performance_history[module_name]
            if metrics.timestamp > cutoff_time
        ]

    async def analyze_performance(self, module_name: str) -> Dict[str, Any]:
        """分析模块性能"""
        try:
            if module_name not in self.performance_history:
                await self.collect_performance_metrics(module_name)

            metrics_list = self.performance_history.get(module_name, [])
            if not metrics_list:
                return {"status": "no_data", "module": module_name}

            # 计算性能统计
            recent_metrics = metrics_list[-10:]  # 最近10个数据点

            avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
            avg_memory = np.mean([m.memory_usage for m in recent_metrics])
            avg_response = np.mean([m.response_time for m in recent_metrics])
            avg_throughput = np.mean([m.throughput for m in recent_metrics])
            avg_error = np.mean([m.error_rate for m in recent_metrics])

            # 性能评估
            performance_score = self._calculate_performance_score(
                avg_cpu, avg_memory, avg_response, avg_throughput, avg_error
            )

            # 识别性能问题
            issues = await self._identify_performance_issues(
                module_name,
                avg_cpu,
                avg_memory,
                avg_response,
                avg_throughput,
                avg_error,
            )

            # 生成优化建议
            recommendations = await self._generate_optimization_recommendations(
                module_name, issues, performance_score
            )

            analysis_result = {
                "module": module_name,
                "performance_score": performance_score,
                "metrics": {
                    "cpu_usage": avg_cpu,
                    "memory_usage": avg_memory,
                    "response_time": avg_response,
                    "throughput": avg_throughput,
                    "error_rate": avg_error,
                },
                "issues": issues,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat(),
            }

            # 发布性能分析事件
            if self.event_bus:
                await self.event_bus.publish("performance.analyzed", analysis_result)

            return analysis_result

        except Exception as e:
            self.logger.error(f"性能分析失败 {module_name}: {e}")
            return {
                "module": module_name,
                "performance_score": 0.5,
                "metrics": {},
                "issues": ["analysis_failed"],
                "recommendations": [],
                "timestamp": datetime.now().isoformat(),
            }

    def _calculate_performance_score(
        self,
        cpu: float,
        memory: float,
        response: float,
        throughput: float,
        error: float,
    ) -> float:
        """计算综合性能分数"""
        # 权重配置
        weights = {
            "cpu": 0.2,
            "memory": 0.2,
            "response_time": 0.25,
            "throughput": 0.25,
            "error_rate": 0.1,
        }

        # 归一化并计算分数
        cpu_score = 1.0 - min(cpu, 1.0)
        memory_score = 1.0 - min(memory, 1.0)
        response_score = 1.0 - min(response / 5.0, 1.0)  # 假设5秒为最大可接受响应时间
        throughput_score = min(throughput / 200.0, 1.0)  # 假设200为理想吞吐量
        error_score = 1.0 - min(error * 10, 1.0)  # 错误率放大处理

        total_score = (
            cpu_score * weights["cpu"]
            + memory_score * weights["memory"]
            + response_score * weights["response_time"]
            + throughput_score * weights["throughput"]
            + error_score * weights["error_rate"]
        )

        return total_score

    async def _identify_performance_issues(
        self,
        module_name: str,
        cpu: float,
        memory: float,
        response: float,
        throughput: float,
        error: float,
    ) -> List[str]:
        """识别性能问题"""
        issues = []
        config = self.optimization_config

        if cpu > config["cpu_threshold_high"]:
            issues.append("high_cpu_usage")
        elif cpu < config["cpu_threshold_low"]:
            issues.append("low_cpu_utilization")

        if memory > config["memory_threshold_high"]:
            issues.append("high_memory_usage")
        elif memory < config["memory_threshold_low"]:
            issues.append("low_memory_utilization")

        if response > config["response_time_threshold"]:
            issues.append("slow_response")

        if throughput < config["throughput_threshold"]:
            issues.append("low_throughput")

        if error > 0.05:  # 5%错误率阈值
            issues.append("high_error_rate")

        # 模块特定问题检测
        module_issues = await self._detect_module_specific_issues(module_name, issues)
        issues.extend(module_issues)

        return issues

    async def _detect_module_specific_issues(
        self, module_name: str, base_issues: List[str]
    ) -> List[str]:
        """检测模块特定问题"""
        specific_issues = []

        if module_name == "rag_engine" and "high_memory_usage" in base_issues:
            specific_issues.append("rag_memory_leak_suspected")

        if module_name == "stock_trading" and "slow_response" in base_issues:
            specific_issues.append("trading_latency_issue")

        if module_name == "content_creation" and "low_throughput" in base_issues:
            specific_issues.append("content_generation_bottleneck")

        return specific_issues

    async def _generate_optimization_recommendations(
        self, module_name: str, issues: List[str], performance_score: float
    ) -> List[OptimizationAction]:
        """生成优化建议"""
        recommendations = []

        # 基于问题生成建议
        for issue in issues:
            if issue == "high_cpu_usage":
                action = OptimizationAction(
                    strategy=OptimizationStrategy.CPU_SCHEDULING,
                    module=module_name,
                    parameter="cpu_quota",
                    value=0.8,  # 限制CPU使用
                    confidence=0.7,
                    expected_improvement=0.15,
                )
                recommendations.append(action)

            elif issue == "high_memory_usage":
                action = OptimizationAction(
                    strategy=OptimizationStrategy.MEMORY_MANAGEMENT,
                    module=module_name,
                    parameter="memory_limit",
                    value="512MB",  # 设置内存限制
                    confidence=0.6,
                    expected_improvement=0.2,
                )
                recommendations.append(action)

            elif issue == "slow_response":
                action = OptimizationAction(
                    strategy=OptimizationStrategy.CACHE_OPTIMIZATION,
                    module=module_name,
                    parameter="cache_size",
                    value="256MB",  # 增加缓存
                    confidence=0.5,
                    expected_improvement=0.1,
                )
                recommendations.append(action)

            elif issue == "low_throughput":
                action = OptimizationAction(
                    strategy=OptimizationStrategy.RESOURCE_ALLOCATION,
                    module=module_name,
                    parameter="worker_count",
                    value=4,  # 增加工作线程
                    confidence=0.6,
                    expected_improvement=0.25,
                )
                recommendations.append(action)

        # 基于性能分数生成通用建议
        if performance_score < 0.6:
            action = OptimizationAction(
                strategy=OptimizationStrategy.RESOURCE_ALLOCATION,
                module=module_name,
                parameter="priority_boost",
                value=True,
                confidence=0.4,
                expected_improvement=0.1,
            )
            recommendations.append(action)

        return recommendations

    async def apply_optimization(self, action: OptimizationAction) -> Dict[str, Any]:
        """应用优化动作"""
        try:
            self.logger.info(f"应用优化: {action.strategy.value} for {action.module}")

            # 记录优化动作
            optimization_record = {
                "action": action,
                "timestamp": datetime.now(),
                "applied": False,
                "result": {},
            }

            # 执行优化（模拟实现）
            if action.strategy == OptimizationStrategy.RESOURCE_ALLOCATION:
                result = await self._apply_resource_optimization(action)
            elif action.strategy == OptimizationStrategy.MEMORY_MANAGEMENT:
                result = await self._apply_memory_optimization(action)
            elif action.strategy == OptimizationStrategy.CPU_SCHEDULING:
                result = await self._apply_cpu_optimization(action)
            else:
                result = {"success": False, "reason": "strategy_not_implemented"}

            optimization_record["applied"] = result.get("success", False)
            optimization_record["result"] = result

            # 记录优化历史
            self.optimization_history.append(optimization_record)

            # 发布优化事件
            if self.event_bus:
                await self.event_bus.publish(
                    "optimization.applied",
                    {
                        "action": self._action_to_dict(action),
                        "result": result,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

            return result

        except Exception as e:
            self.logger.error(f"应用优化失败: {e}")
            return {"success": False, "error": str(e)}

    async def _apply_resource_optimization(
        self, action: OptimizationAction
    ) -> Dict[str, Any]:
        """应用资源分配优化"""
        # 模拟实现 - 实际应调用资源管理器
        return {
            "success": True,
            "message": f"资源分配优化已应用: {action.parameter}={action.value}",
            "module": action.module,
        }

    async def _apply_memory_optimization(
        self, action: OptimizationAction
    ) -> Dict[str, Any]:
        """应用内存管理优化"""
        # 模拟实现
        return {
            "success": True,
            "message": f"内存优化已应用: {action.parameter}={action.value}",
            "module": action.module,
        }

    async def _apply_cpu_optimization(
        self, action: OptimizationAction
    ) -> Dict[str, Any]:
        """应用CPU调度优化"""
        # 模拟实现
        return {
            "success": True,
            "message": f"CPU优化已应用: {action.parameter}={action.value}",
            "module": action.module,
        }

    async def _optimization_loop(self):
        """优化监控循环"""
        while self.optimization_enabled:
            try:
                # 检查所有模块性能
                for module_name in list(self.performance_history.keys()):
                    analysis = await self.analyze_performance(module_name)

                    # 如果发现性能问题，生成并应用优化
                    if analysis.get("performance_score", 0) < 0.7 and analysis.get(
                        "recommendations"
                    ):
                        for recommendation in analysis["recommendations"]:
                            if recommendation.confidence > 0.5:  # 只应用高置信度建议
                                await self.apply_optimization(recommendation)
                                break  # 一次只应用一个优化

                # 等待下一次优化检查
                interval = self.optimization_config["optimization_interval"]
                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"优化循环错误: {e}")
                await asyncio.sleep(10)  # 出错时短暂等待

    def _action_to_dict(self, action: OptimizationAction) -> Dict[str, Any]:
        """将优化动作转换为字典"""
        return {
            "strategy": action.strategy.value,
            "module": action.module,
            "parameter": action.parameter,
            "value": action.value,
            "confidence": action.confidence,
            "expected_improvement": action.expected_improvement,
        }

    async def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        successful_optimizations = [
            record
            for record in self.optimization_history
            if record["applied"] and record["result"].get("success", False)
        ]

        failed_optimizations = [
            record
            for record in self.optimization_history
            if not record["applied"] or not record["result"].get("success", False)
        ]

        return {
            "total_optimizations_applied": len(successful_optimizations),
            "success_rate": len(successful_optimizations)
            / max(len(self.optimization_history), 1),
            "recent_actions": [
                {
                    "action": self._action_to_dict(record["action"]),
                    "timestamp": record["timestamp"].isoformat(),
                    "success": record["applied"],
                }
                for record in self.optimization_history[-10:]  # 最近10个动作
            ],
            "performance_trends": await self._calculate_performance_trends(),
            "recommendations": await self._generate_system_optimization_recommendations(),
        }

    async def _calculate_performance_trends(self) -> Dict[str, float]:
        """计算性能趋势"""
        # 模拟实现
        return {
            "overall_trend": 0.05,  # 5%提升
            "cpu_efficiency": 0.08,
            "memory_efficiency": 0.03,
            "response_improvement": 0.12,
            "throughput_growth": 0.06,
        }

    async def _generate_system_optimization_recommendations(
        self,
    ) -> List[Dict[str, Any]]:
        """生成系统级优化建议"""
        return [
            {
                "type": "resource_rebalancing",
                "priority": "high",
                "description": "重新平衡RAG引擎和交易模块的资源分配",
                "expected_impact": 0.15,
            },
            {
                "type": "cache_strategy",
                "priority": "medium",
                "description": "优化内容创建模块的缓存策略",
                "expected_impact": 0.08,
            },
        ]

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy" if self.initialized else "initializing",
            "optimization_enabled": self.optimization_enabled,
            "modules_monitored": len(self.performance_history),
            "optimizations_applied": len(
                [r for r in self.optimization_history if r["applied"]]
            ),
            "average_performance_score": await self._calculate_average_performance_score(),
            "last_optimization": (
                self.optimization_history[-1]["timestamp"].isoformat()
                if self.optimization_history
                else None
            ),
        }

    async def _calculate_average_performance_score(self) -> float:
        """计算平均性能分数"""
        if not self.performance_history:
            return 0.0

        total_score = 0.0
        count = 0

        for module_name, metrics_list in self.performance_history.items():
            if metrics_list:
                recent_metrics = metrics_list[-5:]  # 最近5个数据点
                score = self._calculate_performance_score(
                    np.mean([m.cpu_usage for m in recent_metrics]),
                    np.mean([m.memory_usage for m in recent_metrics]),
                    np.mean([m.response_time for m in recent_metrics]),
                    np.mean([m.throughput for m in recent_metrics]),
                    np.mean([m.error_rate for m in recent_metrics]),
                )
                total_score += score
                count += 1

        return total_score / count if count > 0 else 0.0

    async def stop(self):
        """停止性能优化器"""
        self.logger.info("停止智能性能优化器")
        self.optimization_enabled = False
        self.initialized = False
