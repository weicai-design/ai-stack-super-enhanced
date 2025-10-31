"""
Enhanced RAG Text Processors Module
版本: 1.0.0
功能: 文本处理器模块初始化文件
描述: 统一管理文本处理器的注册、发现和依赖注入
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# 配置模块日志
logger = logging.getLogger("text_processors")


class ProcessingLevel(Enum):
    """文本处理级别枚举"""

    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    INTELLIGENT = "intelligent"


class ChunkingStrategy(Enum):
    """分块策略枚举"""

    SEMANTIC = "semantic"
    FIXED = "fixed"
    DYNAMIC = "dynamic"
    ADAPTIVE = "adaptive"


@dataclass
class TextProcessingConfig:
    """文本处理配置数据类"""

    chunk_size: int = 512
    chunk_overlap: int = 50
    min_chunk_size: int = 100
    max_chunk_size: int = 1024
    processing_level: ProcessingLevel = ProcessingLevel.INTELLIGENT
    chunking_strategy: ChunkingStrategy = ChunkingStrategy.ADAPTIVE
    enable_semantic_cleaning: bool = True
    enable_entity_extraction: bool = True
    enable_quality_validation: bool = True
    language: str = "zh-CN"


@dataclass
class ProcessedTextChunk:
    """处理后的文本块数据类"""

    content: str
    chunk_id: str
    start_position: int
    end_position: int
    semantic_score: float
    quality_score: float
    entities: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class TextProcessorBase:
    """文本处理器基类"""

    def __init__(self, config: TextProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(f"text_processor.{self.__class__.__name__}")
        self._initialized = False

    async def initialize(self):
        """初始化处理器"""
        try:
            await self._initialize_components()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} 初始化成功")
        except Exception as e:
            self.logger.error(f"{self.__class__.__name__} 初始化失败: {str(e)}")
            raise

    async def _initialize_components(self):
        """初始化组件 - 子类实现"""
        pass

    async def process(self, text: str, metadata: Dict[str, Any] = None) -> Any:
        """处理文本 - 子类实现"""
        if not self._initialized:
            raise RuntimeError("处理器未初始化，请先调用initialize()")
        return await self._process_impl(text, metadata or {})

    async def _process_impl(self, text: str, metadata: Dict[str, Any]) -> Any:
        """处理实现 - 子类重写"""
        raise NotImplementedError("子类必须实现_process_impl方法")

    async def cleanup(self):
        """清理资源"""
        self._initialized = False


# 处理器注册表
_TEXT_PROCESSOR_REGISTRY = {}


def register_processor(name: str, processor_class):
    """注册文本处理器"""
    if not issubclass(processor_class, TextProcessorBase):
        raise TypeError(f"处理器类必须继承自 TextProcessorBase: {processor_class}")
    _TEXT_PROCESSOR_REGISTRY[name] = processor_class
    logger.info(f"文本处理器注册成功: {name} -> {processor_class.__name__}")


def get_processor(name: str) -> Optional[type]:
    """获取文本处理器类"""
    return _TEXT_PROCESSOR_REGISTRY.get(name)


def list_processors() -> List[str]:
    """列出所有注册的处理器"""
    return list(_TEXT_PROCESSOR_REGISTRY.keys())


def create_processor(name: str, config: TextProcessingConfig) -> TextProcessorBase:
    """创建处理器实例"""
    processor_class = get_processor(name)
    if not processor_class:
        raise ValueError(f"未找到文本处理器: {name}")
    return processor_class(config)


# 导出公共接口
__all__ = [
    "TextProcessorBase",
    "TextProcessingConfig",
    "ProcessedTextChunk",
    "ProcessingLevel",
    "ChunkingStrategy",
    "register_processor",
    "get_processor",
    "list_processors",
    "create_processor",
]

logger.info("文本处理器模块初始化完成")
