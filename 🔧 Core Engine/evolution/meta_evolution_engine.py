# ai-stack-super-enhanced/🔧 Core Engine/evolution/meta_evolution_engine.py
"""
元进化引擎 - 负责系统级的自我学习和进化协调
对应开发计划：阶段1 - Core Engine 中的进化引擎基础
对应开发规则：9.1/9.2 自我学习和自我进化功能需求
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EvolutionState(Enum):
    """进化状态枚举"""

    INITIALIZING = "initializing"
    MONITORING = "monitoring"
    ANALYZING = "analyzing"
    EVOLVING = "evolving"
    ADAPTING = "adapting"
    PAUSED = "paused"
    STOPPED = "stopped"


class EvolutionStrategy(Enum):
    """进化策略枚举"""

    GRADUAL_ADAPTATION = "gradual_adaptation"
    RADICAL_INNOVATION = "radical_innovation"
    HYBRID_APPROACH = "hybrid_approach"
    CONSERVATIVE = "conservative"


class MetaEvolutionEngine:
    """
    元进化引擎 - 系统级自我学习和进化协调器

    核心功能：
    1. 监控系统整体性能和健康状态
    2. 协调各模块的进化过程
    3. 管理进化策略和适应度评估
    4. 处理跨模块的进化依赖关系
    5. 实现元学习能力（学习如何学习）
    """

    def __init__(
        self, performance_analyzer=None, feedback_processor=None, strategy_evolver=None
    ):
        self.performance_analyzer = performance_analyzer
        self.feedback_processor = feedback_processor
        self.strategy_evolver = strategy_evolver

        # 引擎状态
        self.state = EvolutionState.INITIALIZING
        self.engine_id = str(uuid.uuid4())
        self.start_time = None
        self.generation_count = 0

        # 进化配置
        self.config = {}
        self.evolution_history = []
        self.adaptation_log = []

        # 模块协调
        self.registered_modules = {}
        self.evolution_dependencies = {}
        self.coordination_queue = asyncio.Queue()

        # 性能指标
        self.performance_metrics = {
            "overall_fitness": 0.0,
            "adaptation_speed": 0.0,
            "learning_efficiency": 0.0,
            "stability_index": 0.0,
        }

        # 任务管理
        self.monitoring_task = None
        self.coordination_task = None
        self.running = False

        logger.info(f"元进化引擎实例创建: {self.engine_id}")

    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化元进化引擎

        Args:
            config: 进化配置参数

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始初始化元进化引擎")

            # 设置配置
            self.config = config or {}
            self.setup_default_config()

            # 验证依赖组件
            if not await self._validate_dependencies():
                raise RuntimeError("依赖组件验证失败")

            # 初始化状态
            self.state = EvolutionState.MONITORING
            self.start_time = datetime.utcnow()
            self.generation_count = 0

            # 启动后台任务
            self.running = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            self.coordination_task = asyncio.create_task(self._coordination_loop())

            logger.info("元进化引擎初始化完成")
            return True

        except Exception as e:
            logger.error(f"元进化引擎初始化失败: {str(e)}", exc_info=True)
            self.state = EvolutionState.STOPPED
            return False

    def setup_default_config(self):
        """设置默认配置"""
        default_config = {
            "monitoring_interval": 30,  # 监控间隔(秒)
            "analysis_depth": "comprehensive",  # 分析深度
            "evolution_trigger_threshold": 0.7,  # 进化触发阈值
            "max_parallel_evolutions": 3,  # 最大并行进化数
            "fitness_evaluation_interval": 300,  # 适应度评估间隔(秒)
            "meta_learning_enabled": True,  # 元学习启用
            "cross_module_coordination": True,  # 跨模块协调
            "emergency_adaptation": True,  # 紧急适应机制
        }

        # 合并配置
        for key, value in default_config.items():
            if key not in self.config:
                self.config[key] = value

    async def _validate_dependencies(self) -> bool:
        """验证依赖组件"""
        try:
            dependencies = [
                (self.performance_analyzer, "PerformanceAnalyzer"),
                (self.feedback_processor, "FeedbackProcessor"),
                (self.strategy_evolver, "StrategyEvolver"),
            ]

            for component, name in dependencies:
                if not component:
                    logger.error(f"依赖组件未提供: {name}")
                    return False

                if not hasattr(component, "initialize"):
                    logger.error(f"依赖组件缺少initialize方法: {name}")
                    return False

                if not hasattr(component, "get_health_status"):
                    logger.error(f"依赖组件缺少get_health_status方法: {name}")
                    return False

            logger.info("所有依赖组件验证通过")
            return True

        except Exception as e:
            logger.error(f"依赖组件验证异常: {str(e)}")
            return False

    async def _monitoring_loop(self):
        """监控循环 - 持续监控系统状态"""
        logger.info("启动进化监控循环")

        while self.running:
            try:
                # 监控系统性能
                await self._monitor_system_performance()

                # 检查进化触发条件
                await self._check_evolution_triggers()

                # 更新元学习模型
                if self.config.get("meta_learning_enabled", True):
                    await self._update_meta_learning()

                # 记录监控日志
                await self._log_monitoring_data()

                # 等待下一个监控周期
                interval = self.config.get("monitoring_interval", 30)
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("进化监控循环被取消")
                break
            except Exception as e:
                logger.error(f"进化监控循环异常: {str(e)}", exc_info=True)
                await asyncio.sleep(10)  # 异常后等待10秒

    async def _coordination_loop(self):
        """协调循环 - 处理进化协调任务"""
        logger.info("启动进化协调循环")

        while self.running:
            try:
                # 处理协调队列中的任务
                if not self.coordination_queue.empty():
                    task = await self.coordination_queue.get()
                    await self._process_coordination_task(task)
                    self.coordination_queue.task_done()
                else:
                    # 队列为空时进行协调检查
                    await self._check_coordination_needs()
                    await asyncio.sleep(5)  # 短暂等待

            except asyncio.CancelledError:
                logger.info("进化协调循环被取消")
                break
            except Exception as e:
                logger.error(f"进化协调循环异常: {str(e)}", exc_info=True)
                await asyncio.sleep(5)

    async def _monitor_system_performance(self):
        """监控系统性能"""
        try:
            # 获取性能分析
            performance_data = (
                await self.performance_analyzer.get_comprehensive_analysis()
            )

            # 计算整体适应度
            fitness_score = await self._calculate_overall_fitness(performance_data)
            self.performance_metrics["overall_fitness"] = fitness_score

            # 更新适应度历史
            fitness_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "fitness": fitness_score,
                "generation": self.generation_count,
                "performance_data": performance_data,
            }
            self.evolution_history.append(fitness_record)

            # 保持历史记录大小
            max_history = self.config.get("max_history_size", 1000)
            if len(self.evolution_history) > max_history:
                self.evolution_history = self.evolution_history[-max_history:]

            logger.debug(f"系统适应度更新: {fitness_score:.4f}")

        except Exception as e:
            logger.error(f"系统性能监控失败: {str(e)}", exc_info=True)

    async def _calculate_overall_fitness(
        self, performance_data: Dict[str, Any]
    ) -> float:
        """计算整体适应度分数"""
        try:
            weights = {
                "efficiency": 0.3,
                "accuracy": 0.25,
                "stability": 0.2,
                "adaptability": 0.15,
                "resource_usage": 0.1,
            }

            total_score = 0.0
            total_weight = 0.0

            for dimension, weight in weights.items():
                if dimension in performance_data:
                    dimension_score = performance_data[dimension].get("score", 0)
                    total_score += dimension_score * weight
                    total_weight += weight

            # 归一化到0-1范围
            fitness = total_score / total_weight if total_weight > 0 else 0.0
            return max(0.0, min(1.0, fitness))

        except Exception as e:
            logger.error(f"适应度计算失败: {str(e)}")
            return 0.0

    async def _check_evolution_triggers(self):
        """检查进化触发条件"""
        try:
            current_fitness = self.performance_metrics["overall_fitness"]
            trigger_threshold = self.config.get("evolution_trigger_threshold", 0.7)

            # 检查适应度是否低于阈值
            if current_fitness < trigger_threshold:
                logger.warning(
                    f"系统适应度({current_fitness:.4f})低于阈值({trigger_threshold}), 触发进化"
                )
                await self._initiate_evolution_cycle()

            # 检查性能下降趋势
            if await self._detect_performance_decline():
                logger.warning("检测到性能下降趋势，触发预防性进化")
                await self._initiate_evolution_cycle()

        except Exception as e:
            logger.error(f"进化触发检查失败: {str(e)}", exc_info=True)

    async def _detect_performance_decline(self) -> bool:
        """检测性能下降趋势"""
        try:
            if len(self.evolution_history) < 10:
                return False

            # 分析最近10个时间点的适应度趋势
            recent_fitness = [
                record["fitness"] for record in self.evolution_history[-10:]
            ]

            # 计算趋势（简单线性回归斜率）
            n = len(recent_fitness)
            x = list(range(n))
            y = recent_fitness

            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_x2 = sum(x_i * x_i for x_i in x)

            numerator = n * sum_xy - sum_x * sum_y
            denominator = n * sum_x2 - sum_x * sum_x

            if denominator == 0:
                return False

            slope = numerator / denominator

            # 如果斜率为负且绝对值较大，则认为有下降趋势
            return slope < -0.01

        except Exception as e:
            logger.error(f"性能下降趋势检测失败: {str(e)}")
            return False

    async def _initiate_evolution_cycle(self):
        """启动进化周期"""
        try:
            if self.state == EvolutionState.EVOLVING:
                logger.info("进化周期已在进行中，跳过新请求")
                return

            logger.info("启动新的进化周期")
            self.state = EvolutionState.EVOLVING

            # 分析当前问题
            problem_analysis = await self.performance_analyzer.identify_bottlenecks()

            # 处理反馈信息
            feedback_data = await self.feedback_processor.process_feedback(
                problem_analysis
            )

            # 进化策略
            new_strategies = await self.strategy_evolver.evolve_strategies(
                problem_analysis, feedback_data
            )

            # 协调模块进化
            coordination_tasks = await self._coordinate_module_evolutions(
                new_strategies
            )

            # 执行协调后的进化
            evolution_results = await self._execute_coordinated_evolutions(
                coordination_tasks
            )

            # 评估进化结果
            success = await self._evaluate_evolution_results(evolution_results)

            if success:
                self.generation_count += 1
                logger.info(f"进化周期完成 - 第{self.generation_count}代")
            else:
                logger.warning("进化周期完成但效果不佳")

            # 返回监控状态
            self.state = EvolutionState.MONITORING

        except Exception as e:
            logger.error(f"进化周期执行失败: {str(e)}", exc_info=True)
            self.state = EvolutionState.MONITORING

    async def _coordinate_module_evolutions(
        self, strategies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """协调模块进化"""
        coordination_plan = []

        try:
            # 分析策略依赖关系
            dependency_graph = await self._analyze_strategy_dependencies(strategies)

            # 生成协调计划
            for module_id, strategy in strategies.items():
                coordination_task = {
                    "task_id": str(uuid.uuid4()),
                    "module_id": module_id,
                    "strategy": strategy,
                    "dependencies": dependency_graph.get(module_id, []),
                    "priority": self._calculate_evolution_priority(module_id, strategy),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                coordination_plan.append(coordination_task)

            # 按优先级和依赖关系排序
            coordination_plan.sort(
                key=lambda x: (x["priority"], len(x["dependencies"]))
            )

            logger.info(f"生成进化协调计划，包含{len(coordination_plan)}个任务")
            return coordination_plan

        except Exception as e:
            logger.error(f"模块进化协调失败: {str(e)}", exc_info=True)
            return []

    async def _analyze_strategy_dependencies(
        self, strategies: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """分析策略依赖关系"""
        dependency_graph = {}

        try:
            for module_id, strategy in strategies.items():
                dependencies = []

                # 分析策略中的依赖声明
                if "dependencies" in strategy:
                    dependencies.extend(strategy["dependencies"])

                # 检查模块间依赖
                if module_id in self.evolution_dependencies:
                    dependencies.extend(self.evolution_dependencies[module_id])

                dependency_graph[module_id] = list(set(dependencies))  # 去重

            return dependency_graph

        except Exception as e:
            logger.error(f"策略依赖分析失败: {str(e)}")
            return {}

    def _calculate_evolution_priority(
        self, module_id: str, strategy: Dict[str, Any]
    ) -> int:
        """计算进化优先级"""
        priority_factors = {
            "criticality": strategy.get("criticality", 1),
            "impact_level": strategy.get("impact", 1),
            "urgency": strategy.get("urgency", 1),
        }

        # 简单加权计算
        priority = (
            priority_factors["criticality"] * 3
            + priority_factors["impact_level"] * 2
            + priority_factors["urgency"] * 1
        )

        return priority

    async def _execute_coordinated_evolutions(
        self, coordination_tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """执行协调后的进化"""
        results = {}

        try:
            # 限制并行进化数量
            max_parallel = self.config.get("max_parallel_evolutions", 3)
            semaphore = asyncio.Semaphore(max_parallel)

            async def execute_single_evolution(task):
                async with semaphore:
                    try:
                        # 等待依赖任务完成
                        await self._wait_for_dependencies(task, results)

                        # 执行进化
                        evolution_result = await self._execute_module_evolution(task)
                        results[task["task_id"]] = evolution_result

                        return evolution_result
                    except Exception as e:
                        logger.error(
                            f"模块进化执行失败: {task['module_id']} - {str(e)}"
                        )
                        return {"success": False, "error": str(e)}

            # 并行执行进化任务
            tasks = [execute_single_evolution(task) for task in coordination_tasks]
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(
                f"协调进化执行完成，成功: {sum(1 for r in results.values() if r.get('success', False))}"
            )
            return results

        except Exception as e:
            logger.error(f"协调进化执行失败: {str(e)}", exc_info=True)
            return {}

    async def _wait_for_dependencies(
        self, task: Dict[str, Any], completed_results: Dict[str, Any]
    ):
        """等待依赖任务完成"""
        dependencies = task.get("dependencies", [])

        for dep_module_id in dependencies:
            # 查找依赖任务的完成状态
            dep_task_id = None
            for task_id, result in completed_results.items():
                if result.get("module_id") == dep_module_id and result.get("success"):
                    dep_task_id = task_id
                    break

            if not dep_task_id:
                logger.warning(
                    f"任务{task['task_id']}等待未完成的依赖: {dep_module_id}"
                )
                # 这里可以实现更复杂的依赖等待逻辑
                await asyncio.sleep(1)

    async def _execute_module_evolution(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个模块进化"""
        try:
            module_id = task["module_id"]
            strategy = task["strategy"]

            logger.info(f"执行模块进化: {module_id}")

            # 这里调用具体模块的进化接口
            # 实际实现中会根据模块类型调用不同的进化方法

            evolution_result = {
                "task_id": task["task_id"],
                "module_id": module_id,
                "strategy_applied": strategy.get("type", "unknown"),
                "success": True,
                "timestamp": datetime.utcnow().isoformat(),
                "metrics": {
                    "improvement_score": 0.0,
                    "adaptation_time": 0.0,
                    "resource_impact": 0.0,
                },
            }

            # 模拟进化执行时间
            await asyncio.sleep(0.1)

            return evolution_result

        except Exception as e:
            logger.error(f"模块进化执行异常: {task['module_id']} - {str(e)}")
            return {
                "task_id": task["task_id"],
                "module_id": task["module_id"],
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _evaluate_evolution_results(
        self, evolution_results: Dict[str, Any]
    ) -> bool:
        """评估进化结果"""
        try:
            successful_evolutions = [
                result
                for result in evolution_results.values()
                if result.get("success", False)
            ]

            success_rate = (
                len(successful_evolutions) / len(evolution_results)
                if evolution_results
                else 0
            )

            # 计算整体改进分数
            total_improvement = sum(
                result.get("metrics", {}).get("improvement_score", 0)
                for result in successful_evolutions
            )
            avg_improvement = (
                total_improvement / len(successful_evolutions)
                if successful_evolutions
                else 0
            )

            evaluation_result = {
                "success_rate": success_rate,
                "average_improvement": avg_improvement,
                "total_evolutions": len(evolution_results),
                "successful_evolutions": len(successful_evolutions),
                "timestamp": datetime.utcnow().isoformat(),
            }

            # 记录评估结果
            self.adaptation_log.append(evaluation_result)

            # 判断进化是否成功（成功率高且有正向改进）
            is_successful = success_rate > 0.6 and avg_improvement > 0

            logger.info(
                f"进化评估结果: 成功率={success_rate:.2f}, 平均改进={avg_improvement:.4f}, 成功={is_successful}"
            )

            return is_successful

        except Exception as e:
            logger.error(f"进化结果评估失败: {str(e)}")
            return False

    async def _update_meta_learning(self):
        """更新元学习模型"""
        try:
            if len(self.evolution_history) < 5:
                return

            # 分析进化历史，学习进化模式
            recent_history = self.evolution_history[-20:]  # 最近20条记录

            # 计算学习效率趋势
            efficiency_trend = await self._calculate_learning_efficiency_trend(
                recent_history
            )
            self.performance_metrics["learning_efficiency"] = efficiency_trend

            # 计算适应速度
            adaptation_speed = await self._calculate_adaptation_speed(recent_history)
            self.performance_metrics["adaptation_speed"] = adaptation_speed

            # 计算稳定性指数
            stability_index = await self._calculate_stability_index(recent_history)
            self.performance_metrics["stability_index"] = stability_index

            logger.debug(
                f"元学习更新 - 效率: {efficiency_trend:.4f}, 速度: {adaptation_speed:.4f}, 稳定性: {stability_index:.4f}"
            )

        except Exception as e:
            logger.error(f"元学习更新失败: {str(e)}", exc_info=True)

    async def _calculate_learning_efficiency_trend(self, history: List[Dict]) -> float:
        """计算学习效率趋势"""
        try:
            if len(history) < 2:
                return 0.0

            improvements = []
            for i in range(1, len(history)):
                prev_fitness = history[i - 1]["fitness"]
                curr_fitness = history[i]["fitness"]
                improvement = curr_fitness - prev_fitness
                improvements.append(improvement)

            # 计算平均改进率
            avg_improvement = (
                sum(improvements) / len(improvements) if improvements else 0.0
            )
            return max(0.0, avg_improvement)

        except Exception as e:
            logger.error(f"学习效率计算失败: {str(e)}")
            return 0.0

    async def _calculate_adaptation_speed(self, history: List[Dict]) -> float:
        """计算适应速度"""
        try:
            if len(history) < 3:
                return 0.0

            # 分析适应度恢复速度
            recovery_speeds = []
            for i in range(2, len(history)):
                if (
                    history[i - 2]["fitness"]
                    < history[i - 1]["fitness"]
                    < history[i]["fitness"]
                ):
                    # 连续改进，计算改进速度
                    speed = (history[i]["fitness"] - history[i - 2]["fitness"]) / 2
                    recovery_speeds.append(speed)

            avg_speed = (
                sum(recovery_speeds) / len(recovery_speeds) if recovery_speeds else 0.0
            )
            return avg_speed

        except Exception as e:
            logger.error(f"适应速度计算失败: {str(e)}")
            return 0.0

    async def _calculate_stability_index(self, history: List[Dict]) -> float:
        """计算稳定性指数"""
        try:
            if len(history) < 5:
                return 1.0

            fitness_values = [record["fitness"] for record in history]

            # 计算变异系数（标准差/均值）
            mean_fitness = sum(fitness_values) / len(fitness_values)
            variance = sum((x - mean_fitness) ** 2 for x in fitness_values) / len(
                fitness_values
            )
            std_dev = variance**0.5

            if mean_fitness == 0:
                return 1.0

            coefficient_of_variation = std_dev / mean_fitness

            # 稳定性指数 = 1 - 变异系数（限制在0-1范围）
            stability = max(0.0, min(1.0, 1.0 - coefficient_of_variation))
            return stability

        except Exception as e:
            logger.error(f"稳定性指数计算失败: {str(e)}")
            return 1.0

    async def _check_coordination_needs(self):
        """检查协调需求"""
        # 这里可以检查是否需要主动协调模块间的进化
        # 例如：检测模块间冲突、资源竞争等
        pass

    async def _process_coordination_task(self, task: Dict[str, Any]):
        """处理协调任务"""
        try:
            task_type = task.get("type", "unknown")

            if task_type == "module_registration":
                await self._handle_module_registration(task)
            elif task_type == "conflict_resolution":
                await self._handle_conflict_resolution(task)
            elif task_type == "resource_coordination":
                await self._handle_resource_coordination(task)
            else:
                logger.warning(f"未知的协调任务类型: {task_type}")

        except Exception as e:
            logger.error(f"协调任务处理失败: {str(e)}", exc_info=True)

    async def _handle_module_registration(self, task: Dict[str, Any]):
        """处理模块注册"""
        module_id = task.get("module_id")
        if module_id:
            self.registered_modules[module_id] = task
            logger.info(f"模块注册完成: {module_id}")

    async def _handle_conflict_resolution(self, task: Dict[str, Any]):
        """处理冲突解决"""
        logger.info(f"处理进化冲突: {task.get('conflict_id', 'unknown')}")
        # 实现冲突解决逻辑

    async def _handle_resource_coordination(self, task: Dict[str, Any]):
        """处理资源协调"""
        logger.info(f"处理资源协调: {task.get('resource_type', 'unknown')}")
        # 实现资源协调逻辑

    async def _log_monitoring_data(self):
        """记录监控数据"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "engine_id": self.engine_id,
                "state": self.state.value,
                "generation": self.generation_count,
                "performance_metrics": self.performance_metrics.copy(),
                "registered_modules": len(self.registered_modules),
                "evolution_history_size": len(self.evolution_history),
            }

            # 这里可以将日志写入文件或发送到监控系统
            if self.generation_count % 10 == 0:  # 每10代记录一次详细日志
                logger.info(f"进化引擎监控快照: {json.dumps(log_entry, indent=2)}")

        except Exception as e:
            logger.error(f"监控数据记录失败: {str(e)}")

    async def register_module(
        self, module_id: str, module_info: Dict[str, Any]
    ) -> bool:
        """
        注册模块到进化引擎

        Args:
            module_id: 模块标识
            module_info: 模块信息

        Returns:
            bool: 注册是否成功
        """
        try:
            self.registered_modules[module_id] = module_info

            # 记录依赖关系
            if "dependencies" in module_info:
                self.evolution_dependencies[module_id] = module_info["dependencies"]

            # 发送注册任务到协调队列
            registration_task = {
                "type": "module_registration",
                "module_id": module_id,
                "module_info": module_info,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.coordination_queue.put(registration_task)

            logger.info(f"模块注册成功: {module_id}")
            return True

        except Exception as e:
            logger.error(f"模块注册失败: {module_id} - {str(e)}")
            return False

    async def request_emergency_adaptation(
        self, emergency_info: Dict[str, Any]
    ) -> bool:
        """
        请求紧急适应

        Args:
            emergency_info: 紧急情况信息

        Returns:
            bool: 请求是否被接受
        """
        try:
            if not self.config.get("emergency_adaptation", True):
                logger.warning("紧急适应功能被禁用")
                return False

            logger.warning(
                f"接收到紧急适应请求: {emergency_info.get('reason', 'unknown')}"
            )

            # 立即触发进化周期
            await self._initiate_evolution_cycle()

            return True

        except Exception as e:
            logger.error(f"紧急适应请求处理失败: {str(e)}")
            return False

    async def get_evolution_status(self) -> Dict[str, Any]:
        """获取进化状态"""
        return {
            "engine_id": self.engine_id,
            "state": self.state.value,
            "generation_count": self.generation_count,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "running": self.running,
            "performance_metrics": self.performance_metrics,
            "registered_modules_count": len(self.registered_modules),
            "evolution_history_size": len(self.evolution_history),
            "adaptation_log_size": len(self.adaptation_log),
        }

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            component_status = {
                "monitoring_task": self.monitoring_task is not None
                and not self.monitoring_task.done(),
                "coordination_task": self.coordination_task is not None
                and not self.coordination_task.done(),
                "performance_analyzer": await self.performance_analyzer.get_health_status(),
                "feedback_processor": await self.feedback_processor.get_health_status(),
                "strategy_evolver": await self.strategy_evolver.get_health_status(),
            }

            all_healthy = all(
                [
                    component_status["monitoring_task"],
                    component_status["coordination_task"],
                    component_status["performance_analyzer"].get("status") == "healthy",
                    component_status["feedback_processor"].get("status") == "healthy",
                    component_status["strategy_evolver"].get("status") == "healthy",
                ]
            )

            return {
                "status": "healthy" if all_healthy else "degraded",
                "message": (
                    "元进化引擎运行正常" if all_healthy else "元进化引擎运行异常"
                ),
                "components": component_status,
                "state": self.state.value,
                "generation": self.generation_count,
                "overall_fitness": self.performance_metrics["overall_fitness"],
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"健康检查失败: {str(e)}",
                "components": {},
                "state": self.state.value,
                "error": str(e),
            }

    async def stop(self):
        """停止进化引擎"""
        logger.info("正在停止元进化引擎...")

        self.running = False
        self.state = EvolutionState.STOPPED

        # 取消后台任务
        if self.monitoring_task:
            self.monitoring_task.cancel()
        if self.coordination_task:
            self.coordination_task.cancel()

        # 等待任务完成
        await asyncio.sleep(1)

        logger.info("元进化引擎已停止")

    def __del__(self):
        """析构函数"""
        if self.running:
            asyncio.create_task(self.stop())
