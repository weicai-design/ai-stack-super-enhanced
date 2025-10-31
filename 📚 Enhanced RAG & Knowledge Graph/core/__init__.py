# ai-stack-super-enhanced/Enhanced RAG & Knowledge Graph/core/73. __init__.py
"""
Enhanced RAG & Knowledge Graph Core Module
超级增强版RAG与知识图谱核心模块初始化文件

功能特性：
1. 提供混合RAG引擎的统一接口
2. 管理多模态向量存储的组件注册
3. 协调语义检索引擎的协同工作
4. 支持动态知识图谱的构建与查询
5. 实现跨模块的数据交换和事件通信

版本: 1.0.0
兼容性: AI Stack Super Enhanced v1.0
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

# 配置模块级日志
logger = logging.getLogger(__name__)


class RAGModuleStatus(Enum):
    """RAG模块状态枚举"""

    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class RAGConfig:
    """RAG配置数据类"""

    chunk_size: int = 512
    chunk_overlap: int = 50
    embedding_model: str = "text-embedding-3-large"
    vector_store_type: str = "chroma"
    max_retrieval_docs: int = 10
    similarity_threshold: float = 0.7
    enable_hybrid_search: bool = True
    enable_reranking: bool = True


class RAGCoreComponents:
    """RAG核心组件容器类"""

    def __init__(self):
        self.hybrid_engine = None
        self.vector_store = None
        self.retrieval_engine = None
        self.knowledge_graph = None
        self.config = RAGConfig()

    def validate_components(self) -> bool:
        """验证所有核心组件是否就绪"""
        components = [self.hybrid_engine, self.vector_store, self.retrieval_engine]
        return all(comp is not None for comp in components)


# 全局组件实例
_components = RAGCoreComponents()


def get_rag_components() -> RAGCoreComponents:
    """获取RAG核心组件实例"""
    return _components


def initialize_rag_module(config: Optional[Dict[str, Any]] = None) -> bool:
    """
    初始化RAG模块

    Args:
        config: 配置字典，可选

    Returns:
        bool: 初始化是否成功
    """
    try:
        logger.info("开始初始化RAG核心模块...")

        # 应用配置
        if config:
            _apply_config(config)

        # 验证依赖组件
        if not _validate_dependencies():
            logger.error("RAG模块依赖组件验证失败")
            return False

        logger.info("RAG核心模块初始化完成")
        return True

    except Exception as e:
        logger.error(f"RAG模块初始化失败: {str(e)}")
        return False


def _apply_config(config: Dict[str, Any]) -> None:
    """应用配置到组件"""
    for key, value in config.items():
        if hasattr(_components.config, key):
            setattr(_components.config, key, value)
            logger.debug(f"更新配置: {key} = {value}")


def _validate_dependencies() -> bool:
    """验证模块依赖"""
    try:
        # 检查必要的Python包
        required_packages = [
            "numpy",
            "pandas",
            "chromadb",
            "sentence_transformers",
            "networkx",
            "spacy",
            "PIL",
            "pydub",
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"可选依赖包 {package} 未安装，部分功能可能受限")

        if missing_packages:
            logger.warning(f"以下可选依赖包未安装: {missing_packages}")

        return True

    except Exception as e:
        logger.error(f"依赖验证失败: {str(e)}")
        return False


def register_hybrid_engine(engine) -> bool:
    """
    注册混合RAG引擎

    Args:
        engine: 混合RAG引擎实例

    Returns:
        bool: 注册是否成功
    """
    try:
        if engine is None:
            logger.error("混合RAG引擎实例为空")
            return False

        _components.hybrid_engine = engine
        logger.info("混合RAG引擎注册成功")
        return True

    except Exception as e:
        logger.error(f"混合RAG引擎注册失败: {str(e)}")
        return False


def register_vector_store(vector_store) -> bool:
    """
    注册向量存储

    Args:
        vector_store: 向量存储实例

    Returns:
        bool: 注册是否成功
    """
    try:
        if vector_store is None:
            logger.error("向量存储实例为空")
            return False

        _components.vector_store = vector_store
        logger.info("向量存储注册成功")
        return True

    except Exception as e:
        logger.error(f"向量存储注册失败: {str(e)}")
        return False


def register_retrieval_engine(retrieval_engine) -> bool:
    """
    注册检索引擎

    Args:
        retrieval_engine: 检索引擎实例

    Returns:
        bool: 注册是否成功
    """
    try:
        if retrieval_engine is None:
            logger.error("检索引擎实例为空")
            return False

        _components.retrieval_engine = retrieval_engine
        logger.info("检索引擎注册成功")
        return True

    except Exception as e:
        logger.error(f"检索引擎注册失败: {str(e)}")
        return False


def register_knowledge_graph(knowledge_graph) -> bool:
    """
    注册知识图谱

    Args:
        knowledge_graph: 知识图谱实例

    Returns:
        bool: 注册是否成功
    """
    try:
        if knowledge_graph is None:
            logger.error("知识图谱实例为空")
            return False

        _components.knowledge_graph = knowledge_graph
        logger.info("知识图谱注册成功")
        return True

    except Exception as e:
        logger.error(f"知识图谱注册失败: {str(e)}")
        return False


def get_module_status() -> Dict[str, Any]:
    """
    获取模块状态

    Returns:
        Dict[str, Any]: 模块状态信息
    """
    return {
        "components_initialized": _components.validate_components(),
        "hybrid_engine_ready": _components.hybrid_engine is not None,
        "vector_store_ready": _components.vector_store is not None,
        "retrieval_engine_ready": _components.retrieval_engine is not None,
        "knowledge_graph_ready": _components.knowledge_graph is not None,
        "config": _components.config.__dict__,
    }


def cleanup_rag_module() -> bool:
    """
    清理RAG模块资源

    Returns:
        bool: 清理是否成功
    """
    try:
        logger.info("开始清理RAG模块资源...")

        # 清理各个组件
        if _components.hybrid_engine and hasattr(_components.hybrid_engine, "cleanup"):
            _components.hybrid_engine.cleanup()

        if _components.vector_store and hasattr(_components.vector_store, "cleanup"):
            _components.vector_store.cleanup()

        if _components.retrieval_engine and hasattr(
            _components.retrieval_engine, "cleanup"
        ):
            _components.retrieval_engine.cleanup()

        if _components.knowledge_graph and hasattr(
            _components.knowledge_graph, "cleanup"
        ):
            _components.knowledge_graph.cleanup()

        # 重置组件实例
        _components.hybrid_engine = None
        _components.vector_store = None
        _components.retrieval_engine = None
        _components.knowledge_graph = None

        logger.info("RAG模块资源清理完成")
        return True

    except Exception as e:
        logger.error(f"RAG模块资源清理失败: {str(e)}")
        return False


# 导出公共接口
__all__ = [
    "RAGModuleStatus",
    "RAGConfig",
    "RAGCoreComponents",
    "get_rag_components",
    "initialize_rag_module",
    "register_hybrid_engine",
    "register_vector_store",
    "register_retrieval_engine",
    "register_knowledge_graph",
    "get_module_status",
    "cleanup_rag_module",
]

# 模块版本信息
__version__ = "1.0.0"
__author__ = "AI Stack Super Enhanced Team"
__description__ = "Enhanced RAG and Knowledge Graph Core Module"
