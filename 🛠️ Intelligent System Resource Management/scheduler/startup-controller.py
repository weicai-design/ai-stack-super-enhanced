"""
启动控制器
负责系统启动流程控制、阶段管理、启动策略执行和异常处理
对应需求: 8.3/8.4/8.6 - 启动顺序控制、资源冲突解决、自动恢复
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from . import ServiceStartupError, ServiceStatus, logger


@dataclass
class StartupPhase:
    """启动阶段定义"""

    name: str
    description: str
    services: List[str]
    dependencies: List[str]  # 依赖的前置阶段
    timeout: int = 300  # 阶段超时时间（秒）
    retry_policy: Dict[str, Any] = None  # 重试策略


@dataclass
class StartupConfig:
    """启动配置"""

    phases: List[StartupPhase]
    global_timeout: int = 1800  # 全局超时时间（秒）
    parallel_phase_limit: int = 2  # 并行阶段限制
    health_check_delay: int = 5  # 健康检查延迟（秒）
    failure_strategy: str = "stop_all"  # 失败策略: stop_all, continue_healthy, rollback


@dataclass
class StartupProgress:
    """启动进度"""

    current_phase: str
    completed_phases: List[str]
    pending_phases: List[str]
    phase_progress: Dict[str, float]  # 各阶段进度 0-1
    overall_progress: float
    estimated_remaining_time: int  # 预估剩余时间（秒）
    started_at: float
    status: str  # running, paused, completed, failed


class StartupController:
    """
    启动控制器
    管理系统的分阶段启动、进度跟踪、异常恢复和回滚
    """

    def __init__(
        self, service_scheduler, dependency_intelligence, resource_manager=None
    ):
        self.service_scheduler = service_scheduler
        self.dependency_intelligence = dependency_intelligence
        self.resource_manager = resource_manager

        self.startup_config: Optional[StartupConfig] = None
        self.current_progress: Optional[StartupProgress] = None
        self.phase_handlers: Dict[str, Callable] = {}
        self.phase_timeouts: Dict[str, asyncio.Task] = {}

        self.is_starting = False
        self.is_rolling_back = False
        self.pause_event = asyncio.Event()
        self.resume_event = asyncio.Event()
        self.shutdown_event = asyncio.Event()

        self.phase_start_times: Dict[str, float] = {}
        self.phase_metrics: Dict[str, Dict[str, Any]] = {}

        # 启动策略
        self.startup_strategies = {
            "conservative": self._conservative_startup,
            "balanced": self._balanced_startup,
            "aggressive": self._aggressive_startup,
        }

        # 失败处理策略
        self.failure_handlers = {
            "stop_all": self._stop_all_on_failure,
            "continue_healthy": self._continue_healthy_on_failure,
            "rollback": self._rollback_on_failure,
        }

        logger.info("启动控制器初始化完成")

    async def initialize_startup_plan(
        self, strategy: str = "balanced", custom_config: Optional[StartupConfig] = None
    ) -> StartupConfig:
        """
        初始化启动计划

        Args:
            strategy: 启动策略
            custom_config: 自定义配置

        Returns:
            StartupConfig: 启动配置
        """
        try:
            if custom_config:
                self.startup_config = custom_config
            else:
                # 自动生成启动计划
                self.startup_config = await self._generate_startup_plan(strategy)

            # 注册阶段处理器
            await self._register_phase_handlers()

            logger.info(f"启动计划初始化完成: {len(self.startup_config.phases)} 个阶段")
            return self.startup_config

        except Exception as e:
            logger.error(f"启动计划初始化失败: {str(e)}")
            raise ServiceStartupError(f"启动计划初始化失败: {str(e)}")

    async def execute_startup(self) -> Dict[str, Any]:
        """
        执行系统启动

        Returns:
            Dict[str, Any]: 启动结果
        """
        if not self.startup_config:
            raise ServiceStartupError("启动计划未初始化")

        if self.is_starting:
            raise ServiceStartupError("启动流程已在执行中")

        self.is_starting = True
        self.shutdown_event.clear()
        start_time = time.time()

        try:
            # 初始化启动进度跟踪
            await self._initialize_progress_tracking()

            logger.info("开始执行系统启动流程")

            # 执行启动策略
            strategy = self.startup_config.failure_strategy
            startup_result = await self.startup_strategies["balanced"]()

            # 记录启动指标
            total_time = time.time() - start_time
            await self._record_startup_metrics(total_time, startup_result)

            logger.info(f"系统启动完成，总耗时: {total_time:.2f} 秒")
            return {
                "success": True,
                "total_time": total_time,
                "phases_completed": len(self.current_progress.completed_phases),
                "services_started": await self._count_running_services(),
                "metrics": self.phase_metrics,
            }

        except Exception as e:
            logger.error(f"系统启动失败: {str(e)}")

            # 执行失败处理
            await self.failure_handlers[self.startup_config.failure_strategy](str(e))

            return {
                "success": False,
                "error": str(e),
                "completed_phases": (
                    self.current_progress.completed_phases
                    if self.current_progress
                    else []
                ),
                "current_phase": (
                    self.current_progress.current_phase
                    if self.current_progress
                    else None
                ),
            }

        finally:
            self.is_starting = False

    async def pause_startup(self) -> bool:
        """
        暂停启动流程

        Returns:
            bool: 暂停是否成功
        """
        if not self.is_starting:
            logger.warning("启动流程未运行，无法暂停")
            return False

        self.pause_event.set()
        logger.info("启动流程暂停")
        return True

    async def resume_startup(self) -> bool:
        """
        恢复启动流程

        Returns:
            bool: 恢复是否成功
        """
        if not self.pause_event.is_set():
            logger.warning("启动流程未暂停，无需恢复")
            return False

        self.pause_event.clear()
        self.resume_event.set()
        logger.info("启动流程恢复")
        return True

    async def rollback_startup(self, reason: str = "") -> Dict[str, Any]:
        """
        回滚启动流程

        Args:
            reason: 回滚原因

        Returns:
            Dict[str, Any]: 回滚结果
        """
        if self.is_rolling_back:
            logger.warning("回滚流程已在执行中")
            return {"success": False, "error": "回滚流程已在执行中"}

        self.is_rolling_back = True
        rollback_start_time = time.time()

        try:
            logger.info(f"开始启动回滚: {reason}")

            # 按阶段逆序停止服务
            completed_phases = self.current_progress.completed_phases.copy()
            completed_phases.reverse()

            rollback_results = {}
            for phase_name in completed_phases:
                phase = next(
                    p for p in self.startup_config.phases if p.name == phase_name
                )
                phase_result = await self._rollback_phase(phase)
                rollback_results[phase_name] = phase_result

            total_time = time.time() - rollback_start_time
            logger.info(f"启动回滚完成，耗时: {total_time:.2f} 秒")

            return {
                "success": True,
                "total_time": total_time,
                "rollback_results": rollback_results,
                "phases_rolled_back": completed_phases,
            }

        except Exception as e:
            logger.error(f"启动回滚失败: {str(e)}")
            return {"success": False, "error": str(e), "partial_rollback": True}

        finally:
            self.is_rolling_back = False

    async def get_startup_progress(self) -> StartupProgress:
        """
        获取启动进度

        Returns:
            StartupProgress: 启动进度信息
        """
        if not self.current_progress:
            raise ServiceStartupError("启动进度未初始化")

        # 更新进度信息
        await self._update_progress()
        return self.current_progress

    async def validate_startup_readiness(self) -> Dict[str, Any]:
        """
        验证启动就绪状态

        Returns:
            Dict[str, Any]: 就绪状态检查结果
        """
        checks = {}

        try:
            # 检查服务调度器
            checks["service_scheduler"] = await self._check_service_scheduler()

            # 检查依赖分析器
            checks["dependency_intelligence"] = (
                await self._check_dependency_intelligence()
            )

            # 检查资源管理器
            if self.resource_manager:
                checks["resource_manager"] = await self._check_resource_manager()

            # 检查服务注册状态
            checks["service_registration"] = await self._check_service_registration()

            # 检查依赖关系
            checks["dependency_health"] = await self._check_dependency_health()

            # 总体就绪状态
            all_passed = all(check.get("ready", False) for check in checks.values())
            checks["overall_ready"] = all_passed

            logger.info(f"启动就绪检查完成: {'通过' if all_passed else '未通过'}")
            return checks

        except Exception as e:
            logger.error(f"启动就绪检查失败: {str(e)}")
            checks["overall_ready"] = False
            checks["error"] = str(e)
            return checks

    # ========== 启动策略实现 ==========

    async def _conservative_startup(self) -> Dict[str, Any]:
        """保守启动策略"""
        logger.info("执行保守启动策略")

        results = {}
        for phase in self.startup_config.phases:
            # 等待暂停信号
            if self.pause_event.is_set():
                await self.resume_event.wait()
                self.resume_event.clear()

            # 检查停止信号
            if self.shutdown_event.is_set():
                raise ServiceStartupError("启动流程被中止")

            phase_result = await self._execute_phase_conservative(phase)
            results[phase.name] = phase_result

            if not phase_result["success"]:
                raise ServiceStartupError(
                    f"阶段 {phase.name} 启动失败: {phase_result['error']}"
                )

        return results

    async def _balanced_startup(self) -> Dict[str, Any]:
        """平衡启动策略"""
        logger.info("执行平衡启动策略")

        # 识别可以并行执行的阶段
        parallel_groups = await self._identify_parallel_phases()
        results = {}

        for group in parallel_groups:
            # 等待暂停信号
            if self.pause_event.is_set():
                await self.resume_event.wait()
                self.resume_event.clear()

            # 检查停止信号
            if self.shutdown_event.is_set():
                raise ServiceStartupError("启动流程被中止")

            # 并行执行阶段组
            group_results = await self._execute_phase_group_parallel(group)
            results.update(group_results)

            # 检查组内失败
            failed_phases = [
                name for name, result in group_results.items() if not result["success"]
            ]
            if failed_phases:
                raise ServiceStartupError(f"并行阶段组启动失败: {failed_phases}")

        return results

    async def _aggressive_startup(self) -> Dict[str, Any]:
        """激进启动策略"""
        logger.info("执行激进启动策略")

        # 最大并行度执行
        all_phases = [phase.name for phase in self.startup_config.phases]
        phase_groups = [
            all_phases[i : i + self.startup_config.parallel_phase_limit]
            for i in range(0, len(all_phases), self.startup_config.parallel_phase_limit)
        ]

        results = {}
        for group in phase_groups:
            # 等待暂停信号
            if self.pause_event.is_set():
                await self.resume_event.wait()
                self.resume_event.clear()

            # 检查停止信号
            if self.shutdown_event.is_set():
                raise ServiceStartupError("启动流程被中止")

            # 并行执行阶段组
            group_results = await self._execute_phase_group_parallel(
                [
                    next(p for p in self.startup_config.phases if p.name == name)
                    for name in group
                ]
            )
            results.update(group_results)

            # 容忍部分失败，继续执行
            failed_phases = [
                name for name, result in group_results.items() if not result["success"]
            ]
            if failed_phases:
                logger.warning(f"阶段组内部分失败，继续执行: {failed_phases}")

        return results

    # ========== 阶段执行逻辑 ==========

    async def _execute_phase_conservative(self, phase: StartupPhase) -> Dict[str, Any]:
        """保守执行单个阶段"""
        logger.info(f"开始执行阶段: {phase.name}")

        self.current_progress.current_phase = phase.name
        self.phase_start_times[phase.name] = time.time()

        try:
            # 执行阶段前置检查
            if not await self._check_phase_prerequisites(phase):
                raise ServiceStartupError(f"阶段前置检查失败: {phase.name}")

            # 执行阶段处理器
            if phase.name in self.phase_handlers:
                phase_result = await self.phase_handlers[phase.name](phase)
            else:
                phase_result = await self._default_phase_handler(phase)

            # 验证阶段结果
            if not await self._validate_phase_completion(phase):
                raise ServiceStartupError(f"阶段完成验证失败: {phase.name}")

            # 记录阶段指标
            phase_time = time.time() - self.phase_start_times[phase.name]
            self.phase_metrics[phase.name] = {
                "success": True,
                "duration": phase_time,
                "services_started": len(phase.services),
                "completed_at": time.time(),
            }

            # 更新进度
            self.current_progress.completed_phases.append(phase.name)
            self.current_progress.pending_phases.remove(phase.name)

            logger.info(f"阶段执行完成: {phase.name}, 耗时: {phase_time:.2f} 秒")
            return {"success": True, "duration": phase_time}

        except Exception as e:
            # 记录失败指标
            phase_time = time.time() - self.phase_start_times[phase.name]
            self.phase_metrics[phase.name] = {
                "success": False,
                "duration": phase_time,
                "error": str(e),
                "failed_at": time.time(),
            }

            logger.error(f"阶段执行失败 {phase.name}: {str(e)}")
            return {"success": False, "error": str(e), "duration": phase_time}

    async def _execute_phase_group_parallel(
        self, phases: List[StartupPhase]
    ) -> Dict[str, Any]:
        """并行执行阶段组"""
        if not phases:
            return {}

        logger.info(f"开始并行执行阶段组: {[p.name for p in phases]}")

        # 设置阶段超时监控
        phase_tasks = {}
        for phase in phases:
            self.current_progress.current_phase = f"parallel_group_{phase.name}"
            self.phase_start_times[phase.name] = time.time()

            task = asyncio.create_task(self._execute_phase_with_timeout(phase))
            phase_tasks[phase.name] = task

        # 等待所有阶段完成或超时
        results = {}
        completed_tasks = await asyncio.gather(
            *phase_tasks.values(), return_exceptions=True
        )

        for phase_name, result in zip(phase_tasks.keys(), completed_tasks):
            if isinstance(result, Exception):
                results[phase_name] = {"success": False, "error": str(result)}
            else:
                results[phase_name] = result

            # 更新进度
            if results[phase_name].get("success", False):
                self.current_progress.completed_phases.append(phase_name)
                if phase_name in self.current_progress.pending_phases:
                    self.current_progress.pending_phases.remove(phase_name)

        logger.info(f"并行阶段组执行完成: {[p.name for p in phases]}")
        return results

    async def _execute_phase_with_timeout(self, phase: StartupPhase) -> Dict[str, Any]:
        """带超时监控的阶段执行"""
        try:
            # 设置阶段超时
            async with asyncio.timeout(phase.timeout):
                return await self._execute_phase_conservative(phase)

        except asyncio.TimeoutError:
            error_msg = f"阶段执行超时: {phase.name} (> {phase.timeout} 秒)"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            logger.error(f"阶段执行异常 {phase.name}: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _default_phase_handler(self, phase: StartupPhase) -> Dict[str, Any]:
        """默认阶段处理器"""
        logger.info(f"使用默认处理器执行阶段: {phase.name}")

        # 启动阶段内的所有服务
        start_results = {}
        for service_name in phase.services:
            try:
                success = await self.service_scheduler.start_service(service_name)
                start_results[service_name] = success

                if not success:
                    logger.warning(f"阶段 {phase.name} 中服务启动失败: {service_name}")

            except Exception as e:
                logger.error(
                    f"阶段 {phase.name} 中服务启动异常 {service_name}: {str(e)}"
                )
                start_results[service_name] = False

        # 检查阶段完成状态
        successful_starts = sum(1 for result in start_results.values() if result)
        success_rate = successful_starts / len(start_results) if start_results else 1.0

        return {
            "success": success_rate >= 0.8,  # 80%成功率即认为阶段成功
            "success_rate": success_rate,
            "service_results": start_results,
        }

    # ========== 失败处理策略 ==========

    async def _stop_all_on_failure(self, error: str):
        """失败时停止所有服务"""
        logger.info(f"执行停止所有服务策略: {error}")

        try:
            # 停止所有已启动的服务
            for service_name in self.service_scheduler.services:
                await self.service_scheduler.stop_service(service_name, force=True)

            logger.info("所有服务已停止")

        except Exception as e:
            logger.error(f"停止所有服务失败: {str(e)}")

    async def _continue_healthy_on_failure(self, error: str):
        """失败时继续运行健康服务"""
        logger.info(f"执行继续健康服务策略: {error}")

        try:
            # 只停止失败阶段的服务
            current_phase = self.current_progress.current_phase
            if current_phase:
                phase = next(
                    p for p in self.startup_config.phases if p.name == current_phase
                )
                for service_name in phase.services:
                    await self.service_scheduler.stop_service(service_name, force=True)

            logger.info("失败阶段服务已停止，健康服务继续运行")

        except Exception as e:
            logger.error(f"停止失败阶段服务失败: {str(e)}")

    async def _rollback_on_failure(self, error: str):
        """失败时回滚到上一个稳定状态"""
        logger.info(f"执行回滚策略: {error}")
        await self.rollback_startup(f"启动失败: {error}")

    # ========== 阶段管理和规划 ==========

    async def _generate_startup_plan(self, strategy: str) -> StartupConfig:
        """生成启动计划"""
        logger.info(f"生成启动计划，策略: {strategy}")

        # 获取最优启动顺序
        optimal_sequence = (
            await self.dependency_intelligence.find_optimal_startup_sequence()
        )

        # 根据策略分组阶段
        if strategy == "conservative":
            phases = await self._create_conservative_phases(optimal_sequence)
        elif strategy == "aggressive":
            phases = await self._create_aggressive_phases(optimal_sequence)
        else:  # balanced
            phases = await self._create_balanced_phases(optimal_sequence)

        config = StartupConfig(
            phases=phases,
            global_timeout=1800,
            parallel_phase_limit=2,
            failure_strategy=(
                "rollback" if strategy != "aggressive" else "continue_healthy"
            ),
        )

        logger.info(f"启动计划生成完成: {len(phases)} 个阶段")
        return config

    async def _create_conservative_phases(
        self, service_sequence: List[str]
    ) -> List[StartupPhase]:
        """创建保守阶段划分"""
        phases = []
        current_phase_services = []

        for service_name in service_sequence:
            current_phase_services.append(service_name)

            # 保守策略：每个服务一个阶段
            phase = StartupPhase(
                name=f"phase_{service_name}",
                description=f"启动服务 {service_name}",
                services=[service_name],
                dependencies=phases[-1].name if phases else [],
                timeout=60,
            )
            phases.append(phase)
            current_phase_services = []

        return phases

    async def _create_balanced_phases(
        self, service_sequence: List[str]
    ) -> List[StartupPhase]:
        """创建平衡阶段划分"""
        phases = []
        current_group = []

        # 基于依赖关系分组
        for service_name in service_sequence:
            current_group.append(service_name)

            # 检查是否可以结束当前组
            if len(current_group) >= 3:  # 每组最多3个服务
                phase = StartupPhase(
                    name=f"phase_{len(phases)+1}",
                    description=f"启动服务组 {len(phases)+1}",
                    services=current_group.copy(),
                    dependencies=phases[-1].name if phases else [],
                    timeout=120,
                )
                phases.append(phase)
                current_group = []

        # 处理剩余服务
        if current_group:
            phase = StartupPhase(
                name=f"phase_{len(phases)+1}",
                description=f"启动最终服务组",
                services=current_group,
                dependencies=phases[-1].name if phases else [],
                timeout=120,
            )
            phases.append(phase)

        return phases

    async def _create_aggressive_phases(
        self, service_sequence: List[str]
    ) -> List[StartupPhase]:
        """创建激进阶段划分"""
        # 激进策略：最少阶段数
        return [
            StartupPhase(
                name="phase_aggressive",
                description="激进启动所有服务",
                services=service_sequence,
                dependencies=[],
                timeout=300,
            )
        ]

    async def _identify_parallel_phases(self) -> List[List[StartupPhase]]:
        """识别可以并行执行的阶段"""
        parallel_groups = []
        remaining_phases = self.startup_config.phases.copy()

        while remaining_phases:
            # 找到没有前置依赖或前置依赖已完成的阶段
            executable_phases = []
            for phase in remaining_phases:
                if not phase.dependencies or all(
                    dep in [p.name for p in self.current_progress.completed_phases]
                    for dep in phase.dependencies
                ):
                    executable_phases.append(phase)

            if not executable_phases:
                break

            # 分组并行执行
            group = executable_phases[: self.startup_config.parallel_phase_limit]
            parallel_groups.append(group)

            # 移除已分组的阶段
            for phase in group:
                remaining_phases.remove(phase)

        return parallel_groups

    # ========== 进度跟踪和管理 ==========

    async def _initialize_progress_tracking(self):
        """初始化进度跟踪"""
        self.current_progress = StartupProgress(
            current_phase="",
            completed_phases=[],
            pending_phases=[phase.name for phase in self.startup_config.phases],
            phase_progress={phase.name: 0.0 for phase in self.startup_config.phases},
            overall_progress=0.0,
            estimated_remaining_time=0,
            started_at=time.time(),
            status="running",
        )

        self.phase_metrics = {}
        self.phase_start_times = {}

    async def _update_progress(self):
        """更新进度信息"""
        if not self.current_progress:
            return

        # 计算总体进度
        total_phases = len(self.startup_config.phases)
        completed_phases = len(self.current_progress.completed_phases)
        self.current_progress.overall_progress = (
            completed_phases / total_phases if total_phases > 0 else 0.0
        )

        # 估算剩余时间
        if completed_phases > 0:
            elapsed_time = time.time() - self.current_progress.started_at
            avg_time_per_phase = elapsed_time / completed_phases
            remaining_phases = total_phases - completed_phases
            self.current_progress.estimated_remaining_time = int(
                avg_time_per_phase * remaining_phases
            )

        # 更新阶段进度
        for phase in self.startup_config.phases:
            if phase.name in self.current_progress.completed_phases:
                self.current_progress.phase_progress[phase.name] = 1.0
            elif phase.name == self.current_progress.current_phase:
                # 基于已启动服务比例估算当前阶段进度
                phase_services = phase.services
                running_services = sum(
                    1
                    for service_name in phase_services
                    if self.service_scheduler.services.get(service_name, {}).get(
                        "status"
                    )
                    == ServiceStatus.RUNNING
                )
                self.current_progress.phase_progress[phase.name] = (
                    running_services / len(phase_services) if phase_services else 0.0
                )

    # ========== 辅助方法和检查 ==========

    async def _register_phase_handlers(self):
        """注册阶段处理器"""
        # 这里可以注册自定义阶段处理器
        # 目前使用默认处理器
        pass

    async def _check_phase_prerequisites(self, phase: StartupPhase) -> bool:
        """检查阶段前置条件"""
        try:
            # 检查依赖阶段是否完成
            for dep_phase_name in phase.dependencies:
                if dep_phase_name not in self.current_progress.completed_phases:
                    logger.warning(f"阶段前置依赖未完成: {dep_phase_name}")
                    return False

            # 检查资源可用性
            if self.resource_manager:
                resource_status = await self.resource_manager.get_detailed_status()
                if (
                    resource_status["cpu"]["usage_fraction"] > 0.9
                    or resource_status["memory"]["usage_fraction"] > 0.9
                ):
                    logger.warning("系统资源紧张，暂缓阶段执行")
                    return False

            return True

        except Exception as e:
            logger.error(f"阶段前置检查异常: {str(e)}")
            return False

    async def _validate_phase_completion(self, phase: StartupPhase) -> bool:
        """验证阶段完成状态"""
        try:
            # 检查阶段内服务是否正常启动
            running_services = 0
            for service_name in phase.services:
                service = self.service_scheduler.services.get(service_name)
                if service and service.status == ServiceStatus.RUNNING:
                    running_services += 1

            success_rate = running_services / len(phase.services)

            # 等待健康检查
            await asyncio.sleep(self.startup_config.health_check_delay)

            return success_rate >= 0.8  # 80%服务运行即认为阶段完成

        except Exception as e:
            logger.error(f"阶段完成验证异常: {str(e)}")
            return False

    async def _rollback_phase(self, phase: StartupPhase) -> Dict[str, Any]:
        """回滚阶段"""
        logger.info(f"回滚阶段: {phase.name}")

        stop_results = {}
        for service_name in phase.services:
            try:
                success = await self.service_scheduler.stop_service(
                    service_name, force=True
                )
                stop_results[service_name] = success
            except Exception as e:
                logger.error(f"回滚阶段服务停止失败 {service_name}: {str(e)}")
                stop_results[service_name] = False

        successful_stops = sum(1 for result in stop_results.values() if result)
        success_rate = successful_stops / len(stop_results) if stop_results else 1.0

        return {
            "success": success_rate >= 0.8,
            "success_rate": success_rate,
            "service_results": stop_results,
        }

    async def _count_running_services(self) -> int:
        """统计运行中服务数量"""
        return sum(
            1
            for service in self.service_scheduler.services.values()
            if service.status == ServiceStatus.RUNNING
        )

    async def _record_startup_metrics(
        self, total_time: float, startup_result: Dict[str, Any]
    ):
        """记录启动指标"""
        self.phase_metrics["startup_overall"] = {
            "total_time": total_time,
            "success": startup_result.get("success", False),
            "phases_completed": len(self.current_progress.completed_phases),
            "services_started": await self._count_running_services(),
            "completed_at": time.time(),
        }

    async def _check_service_scheduler(self) -> Dict[str, Any]:
        """检查服务调度器"""
        try:
            metrics = await self.service_scheduler.get_scheduling_metrics()
            return {
                "ready": True,
                "total_services": metrics.get("total_services", 0),
                "running_services": metrics.get("running_services", 0),
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def _check_dependency_intelligence(self) -> Dict[str, Any]:
        """检查依赖分析器"""
        try:
            metrics = await self.dependency_intelligence.analyze_global_dependencies()
            return {
                "ready": True,
                "total_services": metrics.total_services,
                "cyclic_dependencies": len(metrics.cyclic_dependencies),
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def _check_resource_manager(self) -> Dict[str, Any]:
        """检查资源管理器"""
        try:
            status = await self.resource_manager.get_detailed_status()
            return {
                "ready": status["cpu"]["usage_fraction"] < 0.9
                and status["memory"]["usage_fraction"] < 0.9,
                "cpu_usage": status["cpu"]["usage_fraction"],
                "memory_usage": status["memory"]["usage_fraction"],
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def _check_service_registration(self) -> Dict[str, Any]:
        """检查服务注册状态"""
        try:
            total_services = len(self.service_scheduler.services)
            return {"ready": total_services > 0, "registered_services": total_services}
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def _check_dependency_health(self) -> Dict[str, Any]:
        """检查依赖关系健康度"""
        try:
            metrics = await self.dependency_intelligence.analyze_global_dependencies()
            return {
                "ready": len(metrics.cyclic_dependencies) == 0,
                "cyclic_dependencies": len(metrics.cyclic_dependencies),
                "max_dependency_depth": metrics.max_dependency_depth,
            }
        except Exception as e:
            return {"ready": False, "error": str(e)}

    async def shutdown(self):
        """关闭启动控制器"""
        logger.info("开始关闭启动控制器")
        self.shutdown_event.set()

        if self.is_starting:
            await self.pause_startup()

        logger.info("启动控制器关闭完成")


# 导出启动控制器类
__all__ = ["StartupController", "StartupPhase", "StartupConfig", "StartupProgress"]
