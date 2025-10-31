"""
Intelligent System Resource Management - Resource Manager Package
对应需求: 8.1/8.2/8.5 - 资源监控、冲突弹窗、动态调度、健康自适应
"""

from .conflict_resolver import ConflictResolver
from .dynamic_allocator import DynamicAllocator
from .intelligent_resource_monitor import IntelligentResourceMonitor

__all__ = ["IntelligentResourceMonitor", "DynamicAllocator", "ConflictResolver"]

# 版本信息
__version__ = "1.0.0"
__author__ = "AI-STACK Super Enhanced Team"
__description__ = "智能系统资源管理模块 - 资源监控、动态分配、冲突解决"


# 模块初始化函数
async def initialize_resource_manager(core_services: dict = None):
    """
    资源管理器初始化函数
    对应开发规则: 统一生命周期接口规范
    """
    from ..scheduler.intelligent_service_scheduler import IntelligentServiceScheduler

    resource_monitor = IntelligentResourceMonitor()
    dynamic_allocator = DynamicAllocator()
    conflict_resolver = ConflictResolver()

    # 注入核心服务
    if core_services:
        await resource_monitor.initialize(core_services=core_services)
        await dynamic_allocator.initialize(core_services=core_services)
        await conflict_resolver.initialize(core_services=core_services)

    return {
        "resource_monitor": resource_monitor,
        "dynamic_allocator": dynamic_allocator,
        "conflict_resolver": conflict_resolver,
    }
