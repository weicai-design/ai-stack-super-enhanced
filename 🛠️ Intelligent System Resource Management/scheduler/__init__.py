"""
智能服务调度系统 - 模块初始化
负责服务依赖管理、启动顺序控制、健康检查和自动恢复
对应需求: 8.3/8.4/8.5/8.6 - 系统启动顺序、资源冲突解决、自动恢复
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    FAILED = "failed"


class DependencyType(Enum):
    """依赖类型枚举"""

    REQUIRED = "required"  # 必需依赖
    OPTIONAL = "optional"  # 可选依赖
    WEAK = "weak"  # 弱依赖


@dataclass
class ServiceDependency:
    """服务依赖定义"""

    service_name: str
    dependency_type: DependencyType
    health_required: bool = True
    timeout_seconds: int = 30


@dataclass
class ServiceInfo:
    """服务信息"""

    name: str
    version: str
    description: str
    dependencies: List[ServiceDependency]
    startup_timeout: int = 60
    health_check_interval: int = 30
    auto_restart: bool = True
    max_restart_attempts: int = 3
    resource_requirements: Dict[str, Any] = None


class ServiceSchedulerError(Exception):
    """服务调度异常基类"""

    pass


class DependencyResolutionError(ServiceSchedulerError):
    """依赖解析异常"""

    pass


class ServiceStartupError(ServiceSchedulerError):
    """服务启动异常"""

    pass


class ServiceHealthError(ServiceSchedulerError):
    """服务健康异常"""

    pass


# 导出公共接口
__all__ = [
    "ServiceStatus",
    "DependencyType",
    "ServiceDependency",
    "ServiceInfo",
    "ServiceSchedulerError",
    "DependencyResolutionError",
    "ServiceStartupError",
    "ServiceHealthError",
    "logger",
]

logger.info("智能服务调度系统模块初始化完成")
