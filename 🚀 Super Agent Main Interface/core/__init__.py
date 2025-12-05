"""
超级Agent主界面核心模块
为避免在导入 `core` 时立即执行所有子模块的重型初始化（其中部分模块仍在迭代），
这里采用惰性加载策略：仅在实际访问具体类或函数时才导入对应模块。
这保证了 `from core import SuperAgent` 等写法仍然可用，同时不会因个别模块的语法问题
阻塞整个包的导入，使得测试环境能够顺利加载 `core.algorithms` 等子包。
"""

from importlib import import_module
from typing import Any, Dict, Tuple

_EXPORTS: Dict[str, Tuple[str, str]] = {
    "SuperAgent": ("core.super_agent", "SuperAgent"),
    "MemoSystem": ("core.memo_system", "MemoSystem"),
    "TaskPlanning": ("core.task_planning", "TaskPlanning"),
    "SelfLearningMonitor": ("core.self_learning", "SelfLearningMonitor"),
    "ResourceMonitor": ("core.resource_monitor", "ResourceMonitor"),
    "VoiceInteraction": ("core.voice_interaction", "VoiceInteraction"),
    "TranslationService": ("core.translation", "TranslationService"),
    "FileGenerationService": ("core.file_generation", "FileGenerationService"),
    "WebSearchService": ("core.web_search", "WebSearchService"),
    "RAGServiceAdapter": ("core.rag_service_adapter", "RAGServiceAdapter"),
    "ExpertRouter": ("core.expert_router", "ExpertRouter"),
    "ModuleExecutor": ("core.module_executor", "ModuleExecutor"),
    "WorkflowOrchestrator": ("core.workflow_orchestrator", "WorkflowOrchestrator"),
    "WorkflowType": ("core.workflow_orchestrator", "WorkflowType"),
    "WorkflowState": ("core.workflow_orchestrator", "WorkflowState"),
    "WorkflowEventType": ("core.workflow_orchestrator", "WorkflowEventType"),
    "IntelligentWorkflowData": ("core.workflow_orchestrator", "IntelligentWorkflowData"),
    "DirectWorkflowData": ("core.workflow_orchestrator", "DirectWorkflowData"),
    "WorkflowStep": ("core.workflow_orchestrator", "WorkflowStep"),
    "get_workflow_orchestrator": ("core.workflow_orchestrator", "get_workflow_orchestrator"),
    "ERPProcessService": ("core.erp_process_service", "ERPProcessService"),
    "BASE_STAGE_LIFECYCLES": ("core.erp_process_service", "BASE_STAGE_LIFECYCLES"),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module 'core' has no attribute '{name}'")

    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value  # cache for future access
    return value


def __dir__():
    return sorted(list(globals().keys()) + list(_EXPORTS.keys()))

