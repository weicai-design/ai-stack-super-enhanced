"""
Enhanced RAG Pipelines Module
智能RAG管道系统初始化模块

功能概述：
1. 统一管理所有RAG数据处理管道
2. 提供管道注册和发现机制
3. 支持管道的动态组合和扩展

版本: 1.0.0
依赖: Core Engine, Configuration Center
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# 配置日志
logger = logging.getLogger(__name__)


class PipelineType(Enum):
    """管道类型枚举"""

    INGESTION = "smart_ingestion"
    PREPROCESSING = "multi_stage_preprocessing"
    TRUTH_VERIFICATION = "truth_verification"
    GROUPING = "adaptive_grouping"
    FUSION = "knowledge_fusion"


@dataclass
class PipelineConfig:
    """管道配置数据类"""

    name: str
    pipeline_type: PipelineType
    enabled: bool = True
    priority: int = 1
    timeout: int = 300
    max_retries: int = 3
    batch_size: int = 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "pipeline_type": self.pipeline_type.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "batch_size": self.batch_size,
        }


class PipelineRegistry:
    """管道注册表"""

    def __init__(self):
        self._pipelines: Dict[str, Any] = {}
        self._configs: Dict[str, PipelineConfig] = {}

    def register_pipeline(self, name: str, pipeline_class: Any, config: PipelineConfig):
        """注册管道"""
        if name in self._pipelines:
            logger.warning(f"Pipeline {name} already registered, overwriting")

        self._pipelines[name] = pipeline_class
        self._configs[name] = config
        logger.info(f"Registered pipeline: {name} with config {config}")

    def get_pipeline(self, name: str) -> Optional[Any]:
        """获取管道类"""
        return self._pipelines.get(name)

    def get_config(self, name: str) -> Optional[PipelineConfig]:
        """获取管道配置"""
        return self._configs.get(name)

    def list_pipelines(self) -> List[str]:
        """列出所有管道"""
        return list(self._pipelines.keys())

    def get_enabled_pipelines(self) -> List[str]:
        """获取启用的管道"""
        return [name for name, config in self._configs.items() if config.enabled]


# 全局管道注册表实例
pipeline_registry = PipelineRegistry()


def register_pipeline(name: str, config: PipelineConfig):
    """管道注册装饰器"""

    def decorator(cls):
        pipeline_registry.register_pipeline(name, cls, config)
        return cls

    return decorator


# make package

# 导出公共接口
__all__ = [
    "PipelineType",
    "PipelineConfig",
    "PipelineRegistry",
    "pipeline_registry",
    "register_pipeline",
]

logger.info("Enhanced RAG Pipelines module initialized successfully")
