"""
RAG API模块初始化文件
对应需求: 1.7 RAG后端与各功能关联调用
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/api/112. __init__.py
"""

# 兼容加载器：动态在 package 上下文中加载 hyphenated 源文件（file-api.py, kg-api.py, rag-api.py）
import importlib.util
import os
import sys
from typing import Dict, List, Optional

__version__ = "1.0.0"
__author__ = "AI Stack Super Enhanced Team"
__description__ = "Enhanced RAG API Module (compat loader)"

_here = os.path.dirname(__file__)


def _load_router_from(filename: str, module_name: str):
    """Load a source file as a module under package 'web.api' and return its `router` attr if present."""
    path = os.path.join(_here, filename)
    if not os.path.exists(path):
        return None
    # Ensure the package directory is on sys.path so relative imports succeed
    pkg_dir = os.path.dirname(_here)
    if pkg_dir not in sys.path:
        sys.path.insert(0, pkg_dir)

    fullname = f"web.api.{module_name}"
    # Ensure 'web' and 'web.api' package placeholders exist in sys.modules with __path__ set
    if "web" not in sys.modules:
        web_pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("web", loader=None)
        )
        web_pkg.__path__ = [os.path.dirname(__file__)]
        sys.modules["web"] = web_pkg

    if "web.api" not in sys.modules:
        api_pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("web.api", loader=None)
        )
        api_pkg.__path__ = [_here]
        sys.modules["web.api"] = api_pkg
    # Create a placeholder package/module entry to support intra-package relative imports
    if fullname not in sys.modules:
        module = importlib.util.module_from_spec(
            importlib.util.spec_from_loader(fullname, loader=None)
        )
        module.__package__ = "web.api"
        sys.modules[fullname] = module

    spec = importlib.util.spec_from_file_location(fullname, path)
    module = importlib.util.module_from_spec(spec)
    # set correct package before executing
    module.__package__ = "web.api"
    sys.modules[fullname] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        # If loading fails, remove from sys.modules to avoid inconsistent state
        sys.modules.pop(fullname, None)
        raise

    return getattr(module, "router", None)


# load routers
try:
    file_router = _load_router_from("file_api.py", "file_api")
    kg_router = _load_router_from("kg_api.py", "kg_api")
    rag_router = _load_router_from("rag_api.py", "rag_api")
except Exception:
    # fallback: use a small shim that's more robust in different import contexts
    try:
        from . import _loader_shim as _shim

        file_router = getattr(_shim, "file_router", None)
        kg_router = getattr(_shim, "kg_router", None)
        rag_router = getattr(_shim, "rag_router", None)
    except Exception:
        file_router = None
        kg_router = None
        rag_router = None


def get_api_routers() -> List:
    """Return a list of available routers (in preferred order)."""
    routers = []
    if rag_router is not None:
        routers.append(rag_router)
    if kg_router is not None:
        routers.append(kg_router)
    if file_router is not None:
        routers.append(file_router)
    return routers


# API配置 (kept for compatibility)
API_CONFIG = {
    "prefix": "/api/v1",
    "tags": ["RAG System"],
    "dependencies": [],
    "responses": {
        200: {"description": "Success"},
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    },
}


class RAGAPIError(Exception):
    """RAG API异常基类"""

    def __init__(
        self, message: str, code: str = "RAG_API_ERROR", details: Optional[Dict] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(RAGAPIError):
    """文件处理异常"""

    pass


class KnowledgeGraphError(RAGAPIError):
    """知识图谱异常"""

    pass


class RetrievalError(RAGAPIError):
    """检索异常"""

    pass


# 模块初始化状态
_MODULE_INITIALIZED = False


def initialize_module():
    """
    初始化API模块

    Raises:
        RAGAPIError: 初始化失败时抛出
    """
    global _MODULE_INITIALIZED
    try:
        # 这里可以添加模块初始化逻辑
        _MODULE_INITIALIZED = True
    except Exception as e:
        raise RAGAPIError(f"Failed to initialize RAG API module: {str(e)}")


def is_initialized() -> bool:
    """
    检查模块是否已初始化

    Returns:
        bool: 初始化状态
    """
    return _MODULE_INITIALIZED


# 自动初始化模块
try:
    initialize_module()
except RAGAPIError as e:
    print(f"Warning: RAG API module initialization failed: {e}")
