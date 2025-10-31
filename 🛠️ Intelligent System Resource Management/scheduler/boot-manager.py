# ai-stack-super-enhanced/🛠️ Intelligent System Resource Management/scheduler/455. boot-manager.py

"""
系统启动管理器
负责系统启动流程管理、服务依赖解析和启动优化
"""

import asyncio
import inspect
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"


class BootPhase(Enum):
    """启动阶段枚举"""

    PRE_INIT = "pre_init"
    CORE_SERVICES = "core_services"
    SYSTEM_SERVICES = "system_services"
    APPLICATION_SERVICES = "application_services"
    POST_INIT = "post_init"
    READY = "ready"


@dataclass
class ServiceInfo:
    """服务信息数据类"""

    name: str
    module: Any
    dependencies: List[str]
    priority: int
    timeout: int
    retry_count: int
    status: ServiceStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class BootManager:
    """
    系统启动管理器
    负责管理系统的启动流程、服务依赖和启动优化
    """

    def __init__(self, system_manager=None):
        self.system_manager = system_manager
        self.services: Dict[str, ServiceInfo] = {}
        self.service_dependencies: Dict[str, Set[str]] = {}
        self.boot_phase: BootPhase = BootPhase.PRE_INIT
        self.boot_start_time: Optional[datetime] = None
        self.boot_end_time: Optional[datetime] = None

        # 启动配置
        self.boot_config = {
            "parallel_startup": True,
            "dependency_check": True,
            "health_check_enabled": True,
            "startup_timeout": 300,  # 5分钟
            "retry_delay": 5,  # 5秒
            "max_retries": 3,
        }

        # 启动事件监听器
        self.boot_listeners: Dict[str, List[callable]] = {}

        logger.info("系统启动管理器初始化完成")

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化启动管理器"""
        if config:
            self.boot_config.update(config)

        if core_services:
            self.system_manager = core_services.get("system_manager")

        # 注册核心服务
        await self._register_core_services()

        logger.info("系统启动管理器启动完成")

    async def _register_core_services(self):
        """注册核心服务"""
        # 这里可以预注册一些核心服务
        # 实际服务会在系统启动时动态注册
        pass

    async def register_service(
        self,
        name: str,
        module: Any,
        dependencies: List[str] = None,
        priority: int = 0,
        timeout: int = 30,
        retry_count: int = 3,
    ) -> bool:
        """
        注册服务到启动管理器

        Args:
            name: 服务名称
            module: 服务模块对象
            dependencies: 依赖服务列表
            priority: 启动优先级（数字越小优先级越高）
            timeout: 启动超时时间（秒）
            retry_count: 重试次数

        Returns:
            bool: 注册是否成功
        """
        try:
            if name in self.services:
                logger.warning(f"服务已存在: {name}")
                return False

            service_info = ServiceInfo(
                name=name,
                module=module,
                dependencies=dependencies or [],
                priority=priority,
                timeout=timeout,
                retry_count=retry_count,
                status=ServiceStatus.PENDING,
            )

            self.services[name] = service_info

            # 更新依赖关系
            for dep in service_info.dependencies:
                if dep not in self.service_dependencies:
                    self.service_dependencies[dep] = set()
                self.service_dependencies[dep].add(name)

            logger.info(
                f"服务注册成功: {name}, 优先级: {priority}, 依赖: {dependencies}"
            )
            return True

        except Exception as e:
            logger.error(f"服务注册失败: {name} - {str(e)}")
            return False

    async def unregister_service(self, name: str) -> bool:
        """取消注册服务"""
        try:
            if name not in self.services:
                return False

            # 移除依赖关系
            service_info = self.services[name]
            for dep in service_info.dependencies:
                if (
                    dep in self.service_dependencies
                    and name in self.service_dependencies[dep]
                ):
                    self.service_dependencies[dep].remove(name)

            # 移除服务
            del self.services[name]

            logger.info(f"服务取消注册: {name}")
            return True

        except Exception as e:
            logger.error(f"服务取消注册失败: {name} - {str(e)}")
            return False

    async def start_system(self) -> Dict[str, Any]:
        """
        启动整个系统
        按照依赖关系和优先级启动所有服务
        """
        self.boot_start_time = datetime.utcnow()
        self.boot_phase = BootPhase.PRE_INIT

        logger.info("开始系统启动流程")

        try:
            # 预启动检查
            precheck_result = await self._pre_startup_check()
            if not precheck_result["success"]:
                return await self._generate_boot_report(
                    False, precheck_result["errors"]
                )

            # 执行启动流程
            boot_result = await self._execute_boot_sequence()

            # 生成启动报告
            report = await self._generate_boot_report(
                boot_result["success"], boot_result.get("errors", [])
            )

            if boot_result["success"]:
                self.boot_phase = BootPhase.READY
                logger.info("系统启动完成")
            else:
                logger.error("系统启动失败")

            return report

        except Exception as e:
            logger.error(f"系统启动异常: {str(e)}", exc_info=True)
            return await self._generate_boot_report(False, [str(e)])

    async def _pre_startup_check(self) -> Dict[str, Any]:
        """预启动检查"""
        errors = []
        warnings = []

        logger.info("执行预启动检查")

        try:
            # 检查循环依赖
            cycle_detected = await self._detect_cyclic_dependencies()
            if cycle_detected:
                errors.append("检测到循环依赖")

            # 检查缺失依赖
            missing_deps = await self._check_missing_dependencies()
            if missing_deps:
                errors.extend([f"缺失依赖: {dep}" for dep in missing_deps])

            # 检查服务接口
            interface_issues = await self._check_service_interfaces()
            warnings.extend(interface_issues)

            # 检查资源限制
            resource_issues = await self._check_resource_limits()
            warnings.extend(resource_issues)

            return {"success": len(errors) == 0, "errors": errors, "warnings": warnings}

        except Exception as e:
            logger.error(f"预启动检查失败: {str(e)}")
            return {
                "success": False,
                "errors": [f"预启动检查异常: {str(e)}"],
                "warnings": warnings,
            }

    async def _detect_cyclic_dependencies(self) -> bool:
        """检测循环依赖"""
        try:
            visited = set()
            recursion_stack = set()

            def dfs(service_name):
                if service_name in recursion_stack:
                    return True
                if service_name in visited:
                    return False

                visited.add(service_name)
                recursion_stack.add(service_name)

                service_info = self.services.get(service_name)
                if service_info:
                    for dep in service_info.dependencies:
                        if dfs(dep):
                            return True

                recursion_stack.remove(service_name)
                return False

            for service_name in self.services:
                if dfs(service_name):
                    logger.error(f"检测到循环依赖，涉及服务: {service_name}")
                    return True

            return False

        except Exception as e:
            logger.error(f"循环依赖检测失败: {str(e)}")
            return False

    async def _check_missing_dependencies(self) -> List[str]:
        """检查缺失依赖"""
        missing_deps = []

        for service_name, service_info in self.services.items():
            for dep in service_info.dependencies:
                if dep not in self.services:
                    missing_deps.append(f"{service_name} -> {dep}")

        return missing_deps

    async def _check_service_interfaces(self) -> List[str]:
        """检查服务接口"""
        interface_issues = []

        for service_name, service_info in self.services.items():
            module = service_info.module

            # 检查必要的接口方法
            required_methods = ["initialize", "stop", "get_health_status"]
            for method in required_methods:
                if not hasattr(module, method) or not callable(getattr(module, method)):
                    interface_issues.append(
                        f"服务 {service_name} 缺少必要接口: {method}"
                    )

        return interface_issues

    async def _check_resource_limits(self) -> List[str]:
        """检查资源限制"""
        resource_issues = []

        try:
            import resource

            import psutil

            # 检查内存
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                resource_issues.append("系统内存使用率过高")

            # 检查文件描述符限制（仅Unix）
            if hasattr(resource, "getrlimit"):
                soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
                if soft_limit < 1024:
                    resource_issues.append(f"文件描述符限制较低: {soft_limit}")

        except ImportError:
            logger.warning("无法导入资源检查模块")
        except Exception as e:
            logger.error(f"资源检查失败: {str(e)}")

        return resource_issues

    async def _execute_boot_sequence(self) -> Dict[str, Any]:
        """执行启动序列"""
        boot_errors = []
        started_services = []

        logger.info("开始执行启动序列")

        try:
            # 获取拓扑排序的服务列表
            service_order = await self._get_service_start_order()

            if self.boot_config["parallel_startup"]:
                # 并行启动
                start_results = await self._start_services_parallel(service_order)
            else:
                # 串行启动
                start_results = await self._start_services_sequential(service_order)

            # 分析启动结果
            for service_name, result in start_results.items():
                if result["success"]:
                    started_services.append(service_name)
                else:
                    boot_errors.append(
                        f"服务 {service_name} 启动失败: {result.get('error', '未知错误')}"
                    )

            # 执行健康检查
            if self.boot_config["health_check_enabled"] and started_services:
                health_issues = await self._perform_health_checks(started_services)
                boot_errors.extend(health_issues)

            return {
                "success": len(boot_errors) == 0,
                "started_services": started_services,
                "errors": boot_errors,
                "start_results": start_results,
            }

        except Exception as e:
            logger.error(f"启动序列执行失败: {str(e)}")
            boot_errors.append(f"启动序列异常: {str(e)}")
            return {
                "success": False,
                "started_services": started_services,
                "errors": boot_errors,
            }

    async def _get_service_start_order(self) -> List[str]:
        """获取服务启动顺序（拓扑排序）"""
        try:
            # Kahn's 拓扑排序算法
            in_degree = {name: 0 for name in self.services}
            graph = {name: set() for name in self.services}

            # 构建图
            for service_name, service_info in self.services.items():
                for dep in service_info.dependencies:
                    if dep in self.services:
                        graph[dep].add(service_name)
                        in_degree[service_name] += 1

            # 初始化队列（按优先级排序）
            from collections import deque

            queue = deque()

            # 找到所有入度为0的节点，按优先级排序
            zero_degree_services = [
                name for name, degree in in_degree.items() if degree == 0
            ]
            zero_degree_services.sort(key=lambda x: self.services[x].priority)

            for service in zero_degree_services:
                queue.append(service)

            result = []
            while queue:
                service = queue.popleft()
                result.append(service)

                for neighbor in graph[service]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            # 检查是否所有服务都被处理
            if len(result) != len(self.services):
                logger.warning("存在循环依赖，部分服务可能无法启动")
                # 添加剩余的服务
                remaining_services = [
                    name for name in self.services if name not in result
                ]
                result.extend(remaining_services)

            logger.info(f"服务启动顺序: {result}")
            return result

        except Exception as e:
            logger.error(f"获取服务启动顺序失败: {str(e)}")
            # 返回按优先级排序的列表作为备选
            return sorted(self.services.keys(), key=lambda x: self.services[x].priority)

    async def _start_services_parallel(
        self, service_order: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """并行启动服务"""
        start_results = {}
        pending_services = set(service_order)

        # 创建任务字典
        tasks = {}
        for service_name in service_order:
            service_info = self.services[service_name]
            task = asyncio.create_task(self._start_service_with_retry(service_info))
            tasks[service_name] = task

        # 等待所有任务完成
        completed, _ = await asyncio.wait(
            tasks.values(),
            timeout=self.boot_config["startup_timeout"],
            return_when=asyncio.ALL_COMPLETED,
        )

        # 收集结果
        for service_name, task in tasks.items():
            if task in completed:
                try:
                    result = task.result()
                    start_results[service_name] = result

                    if result["success"]:
                        pending_services.discard(service_name)
                except Exception as e:
                    start_results[service_name] = {
                        "success": False,
                        "error": f"任务执行异常: {str(e)}",
                    }
            else:
                start_results[service_name] = {"success": False, "error": "启动超时"}

        return start_results

    async def _start_services_sequential(
        self, service_order: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """串行启动服务"""
        start_results = {}

        for service_name in service_order:
            service_info = self.services[service_name]

            # 检查依赖是否就绪
            deps_ready = await self._check_dependencies_ready(
                service_info, start_results
            )
            if not deps_ready:
                start_results[service_name] = {
                    "success": False,
                    "error": "依赖服务未就绪",
                }
                continue

            # 启动服务
            result = await self._start_service_with_retry(service_info)
            start_results[service_name] = result

            # 如果服务启动失败，可以选择继续或停止
            if not result["success"]:
                logger.error(
                    f"服务启动失败: {service_name}, 错误: {result.get('error')}"
                )
                # 这里可以根据配置决定是否继续启动其他服务

        return start_results

    async def _check_dependencies_ready(
        self, service_info: ServiceInfo, start_results: Dict[str, Any]
    ) -> bool:
        """检查服务依赖是否就绪"""
        for dep_name in service_info.dependencies:
            if dep_name not in start_results:
                return False
            if not start_results[dep_name].get("success", False):
                return False
        return True

    async def _start_service_with_retry(
        self, service_info: ServiceInfo
    ) -> Dict[str, Any]:
        """带重试机制的服务启动"""
        last_error = None

        for attempt in range(service_info.retry_count + 1):
            try:
                logger.info(
                    f"启动服务: {service_info.name} (尝试 {attempt + 1}/{service_info.retry_count + 1})"
                )

                service_info.status = ServiceStatus.STARTING
                service_info.start_time = datetime.utcnow()

                # 执行服务初始化
                result = await self._start_single_service(service_info)

                if result["success"]:
                    service_info.status = ServiceStatus.RUNNING
                    service_info.end_time = datetime.utcnow()
                    service_info.error_message = None

                    logger.info(f"服务启动成功: {service_info.name}")
                    return result
                else:
                    last_error = result.get("error", "未知错误")
                    service_info.error_message = last_error

                    if attempt < service_info.retry_count:
                        logger.warning(
                            f"服务启动失败，准备重试: {service_info.name}, 错误: {last_error}"
                        )
                        await asyncio.sleep(self.boot_config["retry_delay"])
                    else:
                        service_info.status = ServiceStatus.FAILED
                        logger.error(
                            f"服务启动最终失败: {service_info.name}, 错误: {last_error}"
                        )

            except Exception as e:
                last_error = str(e)
                service_info.error_message = last_error
                service_info.status = ServiceStatus.FAILED

                if attempt < service_info.retry_count:
                    logger.warning(
                        f"服务启动异常，准备重试: {service_info.name}, 异常: {last_error}"
                    )
                    await asyncio.sleep(self.boot_config["retry_delay"])
                else:
                    logger.error(
                        f"服务启动最终异常: {service_info.name}, 异常: {last_error}"
                    )

        return {
            "success": False,
            "error": last_error,
            "attempts": service_info.retry_count + 1,
        }

    async def _start_single_service(self, service_info: ServiceInfo) -> Dict[str, Any]:
        """启动单个服务"""
        try:
            module = service_info.module

            # 检查初始化方法
            if not hasattr(module, "initialize") or not callable(module.initialize):
                return {"success": False, "error": "服务缺少initialize方法"}

            # 执行初始化
            if inspect.iscoroutinefunction(module.initialize):
                # 异步初始化
                await asyncio.wait_for(
                    module.initialize(
                        core_services={"system_manager": self.system_manager}
                    ),
                    timeout=service_info.timeout,
                )
            else:
                # 同步初始化（在线程池中执行）
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(
                        None,
                        lambda: module.initialize(
                            core_services={"system_manager": self.system_manager}
                        ),
                    ),
                    timeout=service_info.timeout,
                )

            return {"success": True}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"启动超时 ({service_info.timeout}秒)"}
        except Exception as e:
            return {"success": False, "error": f"启动异常: {str(e)}"}

    async def _perform_health_checks(self, service_names: List[str]) -> List[str]:
        """执行健康检查"""
        health_issues = []

        for service_name in service_names:
            service_info = self.services.get(service_name)
            if not service_info:
                continue

            try:
                module = service_info.module

                if hasattr(module, "get_health_status") and callable(
                    module.get_health_status
                ):
                    if inspect.iscoroutinefunction(module.get_health_status):
                        health_status = await module.get_health_status()
                    else:
                        loop = asyncio.get_event_loop()
                        health_status = await loop.run_in_executor(
                            None, module.get_health_status
                        )

                    if health_status.get("status") not in ["healthy", "running"]:
                        health_issues.append(
                            f"服务 {service_name} 健康检查失败: {health_status}"
                        )

            except Exception as e:
                health_issues.append(f"服务 {service_name} 健康检查异常: {str(e)}")

        return health_issues

    async def _generate_boot_report(
        self, success: bool, errors: List[str]
    ) -> Dict[str, Any]:
        """生成启动报告"""
        self.boot_end_time = datetime.utcnow()

        boot_duration = 0
        if self.boot_start_time and self.boot_end_time:
            boot_duration = (self.boot_end_time - self.boot_start_time).total_seconds()

        # 统计服务状态
        service_stats = {
            "total": len(self.services),
            "running": len(
                [s for s in self.services.values() if s.status == ServiceStatus.RUNNING]
            ),
            "failed": len(
                [s for s in self.services.values() if s.status == ServiceStatus.FAILED]
            ),
            "pending": len(
                [s for s in self.services.values() if s.status == ServiceStatus.PENDING]
            ),
            "starting": len(
                [
                    s
                    for s in self.services.values()
                    if s.status == ServiceStatus.STARTING
                ]
            ),
        }

        report = {
            "success": success,
            "boot_phase": self.boot_phase.value,
            "boot_duration_seconds": boot_duration,
            "service_statistics": service_stats,
            "errors": errors,
            "boot_start_time": (
                self.boot_start_time.isoformat() if self.boot_start_time else None
            ),
            "boot_end_time": (
                self.boot_end_time.isoformat() if self.boot_end_time else None
            ),
            "services_detail": await self._get_services_detail(),
        }

        return report

    async def _get_services_detail(self) -> Dict[str, Any]:
        """获取服务详细信息"""
        services_detail = {}

        for service_name, service_info in self.services.items():
            services_detail[service_name] = {
                "status": service_info.status.value,
                "dependencies": service_info.dependencies,
                "priority": service_info.priority,
                "start_time": (
                    service_info.start_time.isoformat()
                    if service_info.start_time
                    else None
                ),
                "end_time": (
                    service_info.end_time.isoformat() if service_info.end_time else None
                ),
                "error_message": service_info.error_message,
            }

        return services_detail

    async def stop_system(self) -> Dict[str, Any]:
        """停止整个系统"""
        logger.info("开始系统停止流程")

        stop_errors = []
        stopped_services = []

        try:
            # 获取停止顺序（反向启动顺序）
            service_order = await self._get_service_start_order()
            stop_order = list(reversed(service_order))

            for service_name in stop_order:
                service_info = self.services.get(service_name)
                if not service_info or service_info.status != ServiceStatus.RUNNING:
                    continue

                try:
                    result = await self._stop_single_service(service_info)
                    if result["success"]:
                        stopped_services.append(service_name)
                        service_info.status = ServiceStatus.STOPPED
                    else:
                        stop_errors.append(
                            f"服务 {service_name} 停止失败: {result.get('error')}"
                        )

                except Exception as e:
                    stop_errors.append(f"服务 {service_name} 停止异常: {str(e)}")

            return {
                "success": len(stop_errors) == 0,
                "stopped_services": stopped_services,
                "errors": stop_errors,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"系统停止异常: {str(e)}")
            return {
                "success": False,
                "errors": [f"系统停止异常: {str(e)}"],
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _stop_single_service(self, service_info: ServiceInfo) -> Dict[str, Any]:
        """停止单个服务"""
        try:
            module = service_info.module

            if hasattr(module, "stop") and callable(module.stop):
                service_info.status = ServiceStatus.STOPPING

                if inspect.iscoroutinefunction(module.stop):
                    # 异步停止
                    await asyncio.wait_for(module.stop(), timeout=service_info.timeout)
                else:
                    # 同步停止（在线程池中执行）
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, module.stop),
                        timeout=service_info.timeout,
                    )

            return {"success": True}

        except asyncio.TimeoutError:
            return {"success": False, "error": f"停止超时 ({service_info.timeout}秒)"}
        except Exception as e:
            return {"success": False, "error": f"停止异常: {str(e)}"}

    async def get_service_status(self, service_name: str) -> Optional[Dict[str, Any]]:
        """获取服务状态"""
        service_info = self.services.get(service_name)
        if not service_info:
            return None

        return {
            "name": service_info.name,
            "status": service_info.status.value,
            "dependencies": service_info.dependencies,
            "priority": service_info.priority,
            "start_time": (
                service_info.start_time.isoformat() if service_info.start_time else None
            ),
            "end_time": (
                service_info.end_time.isoformat() if service_info.end_time else None
            ),
            "error_message": service_info.error_message,
        }

    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "boot_phase": self.boot_phase.value,
            "total_services": len(self.services),
            "services_status": await self._get_services_status_summary(),
            "boot_duration": await self._get_boot_duration(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def _get_services_status_summary(self) -> Dict[str, int]:
        """获取服务状态摘要"""
        summary = {}
        for status in ServiceStatus:
            summary[status.value] = 0

        for service_info in self.services.values():
            summary[service_info.status.value] += 1

        return summary

    async def _get_boot_duration(self) -> Optional[float]:
        """获取启动持续时间"""
        if not self.boot_start_time:
            return None

        end_time = self.boot_end_time or datetime.utcnow()
        return (end_time - self.boot_start_time).total_seconds()

    async def add_boot_listener(self, event_type: str, listener: callable):
        """添加启动事件监听器"""
        if event_type not in self.boot_listeners:
            self.boot_listeners[event_type] = []

        self.boot_listeners[event_type].append(listener)

    async def remove_boot_listener(self, event_type: str, listener: callable):
        """移除启动事件监听器"""
        if (
            event_type in self.boot_listeners
            and listener in self.boot_listeners[event_type]
        ):
            self.boot_listeners[event_type].remove(listener)

    async def stop(self):
        """停止启动管理器"""
        logger.info("系统启动管理器停止")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态（实现BaseModule接口）"""
        return await self.get_system_status()


# 模块导出
__all__ = ["BootManager", "ServiceStatus", "BootPhase", "ServiceInfo"]
