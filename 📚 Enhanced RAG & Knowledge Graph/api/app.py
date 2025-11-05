from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(
    os.getenv("LOCAL_ST_MODEL_PATH", ROOT.parent / "models" / "all-MiniLM-L6-v2")
)
INDEX_DIR = ROOT / "data"
INDEX_DOCS = INDEX_DIR / "docs.json"
INDEX_VECS = INDEX_DIR / "vectors.npy"
KG_FILE = INDEX_DIR / "kg.json"

app = FastAPI(title="RAG&KG API (minimal)")
# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册专家API路由（将RAG功能提升到100%）
_expert_registered = False
try:
    import importlib.util
    expert_api_path = Path(__file__).parent / "expert_api.py"
    if expert_api_path.exists():
        # 确保PYTHONPATH包含父目录，以便模块能导入core等
        parent_dir = str(ROOT)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        try:
            spec = importlib.util.spec_from_file_location("api.expert_api", expert_api_path)
            expert_api_module = importlib.util.module_from_spec(spec)
            expert_api_module.__package__ = "api"
            expert_api_module.__file__ = str(expert_api_path)
            sys.modules["api.expert_api"] = expert_api_module
            sys.modules["expert_api"] = expert_api_module
            spec.loader.exec_module(expert_api_module)
            
            if hasattr(expert_api_module, 'router'):
                app.include_router(expert_api_module.router)
                logger.info("✅ 专家API路由已注册")
                _expert_registered = True
        except Exception as import_err:
            logger.warning(f"专家API模块导入失败: {type(import_err).__name__}: {import_err}")
    else:
        logger.warning("专家API模块文件不存在")
except Exception as e:
    logger.warning(f"专家API路由注册过程出错: {type(e).__name__}: {e}")

if not _expert_registered:
    # 创建降级router
    from fastapi import APIRouter as FastAPIRouter
    fallback_router = FastAPIRouter(prefix="/expert", tags=["Expert RAG API"])
    @fallback_router.post("/query")
    async def expert_query_fallback():
        raise HTTPException(status_code=503, detail="专家系统功能暂未完全实现")
    app.include_router(fallback_router)
    logger.info("✅ 专家API降级路由已注册")

# 注册知识图谱批量API路由（将知识图谱功能提升到100%）
_kg_batch_registered = False
try:
    import importlib.util
    kg_batch_api_path = Path(__file__).parent / "kg_batch_api.py"
    if kg_batch_api_path.exists():
        parent_dir = str(ROOT)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        spec = importlib.util.spec_from_file_location("api.kg_batch_api", kg_batch_api_path)
        kg_batch_api_module = importlib.util.module_from_spec(spec)
        kg_batch_api_module.__package__ = "api"
        kg_batch_api_module.__file__ = str(kg_batch_api_path)
        sys.modules["api.kg_batch_api"] = kg_batch_api_module
        sys.modules["kg_batch_api"] = kg_batch_api_module
        spec.loader.exec_module(kg_batch_api_module)
        if hasattr(kg_batch_api_module, 'router'):
            app.include_router(kg_batch_api_module.router)
            logger.info("✅ 知识图谱批量API路由已注册")
            _kg_batch_registered = True
        else:
            logger.warning("知识图谱批量API模块缺少router属性")
except Exception as e:
    logger.warning(f"知识图谱批量API模块导入失败: {type(e).__name__}: {e}")

if not _kg_batch_registered:
    # 创建降级router
    from fastapi import APIRouter as FastAPIRouter
    fallback_router = FastAPIRouter(prefix="/kg/batch", tags=["Knowledge Graph Batch API"])
    @fallback_router.post("/query")
    async def kg_batch_query_fallback():
        raise HTTPException(status_code=503, detail="知识图谱批量功能暂未完全实现")
    app.include_router(fallback_router)
    logger.info("✅ 知识图谱批量API降级路由已注册")

# 注册Self-RAG API路由（差距2：自适应学习能力）
_self_rag_registered = False
try:
    import importlib.util
    self_rag_api_path = Path(__file__).parent / "self_rag_api.py"
    if self_rag_api_path.exists():
        parent_dir = str(ROOT)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        spec = importlib.util.spec_from_file_location("api.self_rag_api", self_rag_api_path)
        self_rag_api_module = importlib.util.module_from_spec(spec)
        self_rag_api_module.__package__ = "api"
        self_rag_api_module.__file__ = str(self_rag_api_path)
        sys.modules["api.self_rag_api"] = self_rag_api_module
        sys.modules["self_rag_api"] = self_rag_api_module
        spec.loader.exec_module(self_rag_api_module)
        if hasattr(self_rag_api_module, 'router'):
            app.include_router(self_rag_api_module.router)
            logger.info("✅ Self-RAG API路由已注册")
            _self_rag_registered = True
        else:
            logger.warning("Self-RAG API模块缺少router属性")
except Exception as e:
    logger.warning(f"Self-RAG API模块导入失败: {type(e).__name__}: {e}")

if not _self_rag_registered:
    # 创建降级router
    from fastapi import APIRouter as FastAPIRouter
    fallback_router = FastAPIRouter(prefix="/self-rag", tags=["Self-RAG API"])
    @fallback_router.post("/retrieve")
    async def self_rag_retrieve_fallback():
        raise HTTPException(status_code=503, detail="Self-RAG功能暂未完全实现")
    app.include_router(fallback_router)
    logger.info("✅ Self-RAG API降级路由已注册")

# 注册Agentic RAG API路由（差距7：自主规划）
_agentic_rag_registered = False
try:
    import importlib.util
    agentic_rag_api_path = Path(__file__).parent / "agentic_rag_api.py"
    if agentic_rag_api_path.exists():
        parent_dir = str(ROOT)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        spec = importlib.util.spec_from_file_location("api.agentic_rag_api", agentic_rag_api_path)
        agentic_rag_api_module = importlib.util.module_from_spec(spec)
        agentic_rag_api_module.__package__ = "api"
        agentic_rag_api_module.__file__ = str(agentic_rag_api_path)
        sys.modules["api.agentic_rag_api"] = agentic_rag_api_module
        sys.modules["agentic_rag_api"] = agentic_rag_api_module
        spec.loader.exec_module(agentic_rag_api_module)
        if hasattr(agentic_rag_api_module, 'router'):
            app.include_router(agentic_rag_api_module.router)
            logger.info("✅ Agentic RAG API路由已注册")
            _agentic_rag_registered = True
        else:
            logger.warning("Agentic RAG API模块缺少router属性")
except Exception as e:
    logger.warning(f"Agentic RAG API模块导入失败: {type(e).__name__}: {e}")

if not _agentic_rag_registered:
    # 创建降级router
    from fastapi import APIRouter as FastAPIRouter
    fallback_router = FastAPIRouter(prefix="/agentic-rag", tags=["Agentic RAG API"])
    @fallback_router.post("/execute")
    async def agentic_execute_fallback():
        raise HTTPException(status_code=503, detail="Agentic RAG功能暂未完全实现")
    app.include_router(fallback_router)
    logger.info("✅ Agentic RAG API降级路由已注册")

# 注册图数据库API路由（差距5：图数据库集成）
_graph_db_registered = False
try:
    import importlib.util
    graph_db_api_path = Path(__file__).parent / "graph_db_api.py"
    if graph_db_api_path.exists():
        parent_dir = str(ROOT)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        spec = importlib.util.spec_from_file_location("api.graph_db_api", graph_db_api_path)
        graph_db_api_module = importlib.util.module_from_spec(spec)
        graph_db_api_module.__package__ = "api"
        graph_db_api_module.__file__ = str(graph_db_api_path)
        sys.modules["api.graph_db_api"] = graph_db_api_module
        sys.modules["graph_db_api"] = graph_db_api_module
        spec.loader.exec_module(graph_db_api_module)
        if hasattr(graph_db_api_module, 'router'):
            app.include_router(graph_db_api_module.router)
            logger.info("✅ 图数据库API路由已注册")
            _graph_db_registered = True
        else:
            logger.warning("图数据库API模块缺少router属性")
except Exception as e:
    logger.warning(f"图数据库API模块导入失败: {type(e).__name__}: {e}")

if not _graph_db_registered:
    # 创建降级router（至少注册stats端点）
    from fastapi import APIRouter as FastAPIRouter
    fallback_router = FastAPIRouter(prefix="/graph-db", tags=["Graph Database API"])
    @fallback_router.get("/stats")
    async def graph_db_stats_fallback():
        raise HTTPException(status_code=503, detail="图数据库功能暂未完全实现")
    @fallback_router.post("/node")
    async def graph_db_node_fallback():
        raise HTTPException(status_code=503, detail="图数据库功能暂未完全实现")
    app.include_router(fallback_router)
    logger.info("✅ 图数据库API降级路由已注册")

# 可选鉴权：设置环境变量 RAG_API_KEY 后才生效
API_KEY = os.getenv("RAG_API_KEY", "").strip()


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> bool:
    """
    API密钥验证依赖函数
    
    如果设置了RAG_API_KEY环境变量，则要求请求头中包含匹配的X-API-Key。
    
    Args:
        x_api_key: 从请求头X-API-Key获取的API密钥
        
    Returns:
        bool: 验证通过返回True
        
    Raises:
        HTTPException: 如果API密钥不匹配或未提供（当设置了API_KEY时）
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


# 全局状态：最小内存向量索引
class Doc(BaseModel):
    id: str
    text: str
    path: Optional[str] = None


_docs: List[Doc] = []
_vecs: List[np.ndarray] = []

# ---- 简易 KG 内存结构与工具 ----
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://\S+")

_kg_nodes: Dict[str, Dict[str, Any]] = {}  # node_id -> node
_kg_edges: List[Dict[str, str]] = []  # {src, dst, type}


def _kg_node_id(ntype: str, value: str) -> str:
    """
    生成知识图谱节点ID
    
    Args:
        ntype: 节点类型（如"doc", "email", "url"）
        value: 节点值
        
    Returns:
        str: 格式化的节点ID（格式: "type:value"）
    """
    return f"{ntype}:{value}"


# 全局锁
INDEX_LOCK = threading.RLock()
KG_LOCK = threading.RLock()


# 原子写辅助
def _atomic_write_json(path: Path, obj: Any) -> None:
    """
    原子性地写入JSON文件
    
    使用临时文件+原子替换的方式，确保写入操作的原子性。
    即使写入过程中发生错误，也不会破坏原有文件。
    
    Args:
        path: 目标文件路径
        obj: 要序列化的Python对象
        
    Raises:
        OSError: 如果文件写入失败
        json.JSONEncodeError: 如果对象无法序列化为JSON
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"{path}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _atomic_save_npy(path: Path, arr: np.ndarray) -> None:
    """
    原子性地保存NumPy数组到文件
    
    使用临时文件+原子替换的方式，确保写入操作的原子性。
    即使写入过程中发生错误，也不会破坏原有文件。
    
    Args:
        path: 目标文件路径（应包含.npy扩展名）
        arr: 要保存的NumPy数组
        
    Raises:
        OSError: 如果文件写入失败
        ValueError: 如果数组无法保存
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"{path}.tmp")  # 保持与目标同目录
    # 用二进制句柄写入，避免 np.save 自动追加 .npy
    with open(tmp, "wb") as f:
        np.save(f, arr)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _kg_remove_doc(doc_id: str) -> Dict[str, Any]:
    """
    从知识图谱中移除文档及其关联的边和实体
    
    Args:
        doc_id: 要移除的文档ID
        
    Returns:
        Dict包含移除的边数和实体数
    """
    with KG_LOCK:
        dnid = _kg_node_id("doc", doc_id)
        if dnid not in _kg_nodes:
            return {"removed_edges": 0, "removed_entities": 0}
        removed_edges = []
        keep_edges = []
        for e in _kg_edges:
            if e.get("src") == dnid:
                removed_edges.append(e)
            else:
                keep_edges.append(e)
        _kg_edges[:] = keep_edges
        removed_entities = 0
        # 回退实体计数并清理为0的 email/url 节点
        for e in removed_edges:
            dst = e.get("dst")
            node = _kg_nodes.get(dst)
            if node and node.get("type") in {"email", "url"}:
                node["count"] = max(0, int(node.get("count", 0)) - 1)
                if node["count"] == 0:
                    _kg_nodes.pop(dst, None)
                    removed_entities += 1
        # 移除文档节点
        _kg_nodes.pop(dnid, None)
        return {
            "removed_edges": len(removed_edges),
            "removed_entities": removed_entities,
        }


def _kg_add(doc_id: str, text: str, src_path: Optional[str]) -> None:
    """
    将文档添加到知识图谱，提取其中的实体（邮箱和URL）并建立关系
    
    Args:
        doc_id: 文档ID
        text: 文档文本内容
        src_path: 源文件路径（可选）
    """
    with KG_LOCK:
        dnid = _kg_node_id("doc", doc_id)
        if dnid not in _kg_nodes:
            _kg_nodes[dnid] = {
                "id": dnid,
                "type": "doc",
                "value": doc_id,
                "path": src_path,
            }
        emails = set(EMAIL_RE.findall(text or ""))
        urls = set(URL_RE.findall(text or ""))

        def _edge_exists(src: str, dst: str, et: str) -> bool:
            return any(
                e
                for e in _kg_edges
                if e.get("src") == src and e.get("dst") == dst and e.get("type") == et
            )

        for em in emails:
            nid = _kg_node_id("email", em)
            if nid not in _kg_nodes:
                _kg_nodes[nid] = {"id": nid, "type": "email", "value": em, "count": 0}
            if not _edge_exists(dnid, nid, "mentions"):
                _kg_nodes[nid]["count"] = _kg_nodes[nid].get("count", 0) + 1
                _kg_edges.append({"src": dnid, "dst": nid, "type": "mentions"})
        for u in urls:
            nid = _kg_node_id("url", u)
            if nid not in _kg_nodes:
                _kg_nodes[nid] = {"id": nid, "type": "url", "value": u, "count": 0}
            if not _edge_exists(dnid, nid, "links"):
                _kg_nodes[nid]["count"] = _kg_nodes[nid].get("count", 0) + 1
                _kg_edges.append({"src": dnid, "dst": nid, "type": "links"})


def _kg_save(out_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    保存知识图谱到文件
    
    Args:
        out_path: 输出路径（如果不提供，使用默认路径）
        
    Returns:
        Dict包含保存状态、路径、节点数和边数
        
    Raises:
        OSError: 如果文件写入失败
    """
    with KG_LOCK:
        p = Path(out_path) if out_path else KG_FILE
        _atomic_write_json(p, {"nodes": list(_kg_nodes.values()), "edges": _kg_edges})
        return {
            "success": True,
            "path": str(p),
            "nodes": len(_kg_nodes),
            "edges": len(_kg_edges),
        }


def _kg_clear(remove_file: bool = True) -> Dict[str, Any]:
    """
    清空知识图谱
    
    Args:
        remove_file: 是否删除磁盘上的知识图谱文件
        
    Returns:
        Dict包含清理状态和清理的节点/边数量
    """
    with KG_LOCK:
        n, e = len(_kg_nodes), len(_kg_edges)
        _kg_nodes.clear()
        _kg_edges.clear()
        if remove_file and KG_FILE.exists():
            try:
                KG_FILE.unlink()
            except Exception:
                pass
        return {"success": True, "cleared_nodes": n, "cleared_edges": e}


def _kg_load(in_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    从文件加载知识图谱
    
    Args:
        in_path: 输入路径（如果不提供，使用默认路径）
        
    Returns:
        Dict包含加载状态、路径、节点数和边数
        
    Raises:
        FileNotFoundError: 如果文件不存在
        json.JSONDecodeError: 如果JSON解析失败
    """
    p = Path(in_path) if in_path else KG_FILE
    if not p.exists():
        return {"success": False, "reason": "no_kg_on_disk", "path": str(p)}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        with KG_LOCK:
            _kg_nodes.clear()
            _kg_edges.clear()
            for n in data.get("nodes", []):
                _kg_nodes[n["id"]] = n
            _kg_edges.extend(data.get("edges", []))
        return {
            "success": True,
            "path": str(p),
            "nodes": len(_kg_nodes),
            "edges": len(_kg_edges),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(p)}


# ---- 简易 KG 结束 ----


def _save_index() -> Dict[str, Any]:
    """
    保存索引到磁盘
    
    Returns:
        Dict包含保存状态、路径、大小和维度信息
        
    Raises:
        OSError: 如果磁盘写入失败
    """
    try:
        with INDEX_LOCK:
            INDEX_DIR.mkdir(parents=True, exist_ok=True)
            X = _index_matrix()
            _atomic_save_npy(INDEX_VECS, X)
            _atomic_write_json(INDEX_DOCS, [d.model_dump() for d in _docs])
            return {
                "saved": True,
                "path": str(INDEX_DIR),
                "size": _index_size(),
                "dimension": _DIM,
            }
    except OSError as e:
        return {
            "saved": False,
            "error": f"Failed to save index: {str(e)}",
            "path": str(INDEX_DIR),
        }


def _load_index() -> Dict[str, Any]:
    """
    从磁盘加载索引
    
    Returns:
        Dict包含加载状态、索引大小和维度信息
        
    Raises:
        json.JSONDecodeError: 如果JSON解析失败
        ValueError: 如果向量维度不匹配
    """
    if not INDEX_DOCS.exists() or not INDEX_VECS.exists():
        return {"loaded": False, "reason": "no_index_on_disk"}
    try:
        with INDEX_LOCK:
            docs = json.loads(INDEX_DOCS.read_text(encoding="utf-8"))
            X = np.load(str(INDEX_VECS))
            if X.ndim != 2 or X.shape[1] != _DIM:
                return {
                    "loaded": False,
                    "reason": "dim_mismatch",
                    "file_dim": int(X.shape[1]) if X.ndim == 2 else None,
                    "model_dim": _DIM,
                }
            _docs.clear()
            _vecs.clear()
            for i, d in enumerate(docs):
                _docs.append(Doc(**d))
                _vecs.append(np.asarray(X[i], dtype=np.float32))
            return {"loaded": True, "size": _index_size(), "dimension": _DIM}
    except json.JSONDecodeError as e:
        return {"loaded": False, "reason": "json_decode_error", "error": str(e)}
    except ValueError as e:
        return {"loaded": False, "reason": "value_error", "error": str(e)}
    except Exception as e:
        return {"loaded": False, "reason": "unknown_error", "error": str(e)}


def _delete_by_id(doc_id: str) -> bool:
    """
    根据文档ID从索引中删除文档
    
    同时从向量索引和知识图谱中移除文档及其关联信息。
    
    Args:
        doc_id: 要删除的文档ID
        
    Returns:
        bool: 如果文档存在并成功删除返回True，否则返回False
    """
    with INDEX_LOCK:
        idx = next((i for i, d in enumerate(_docs) if d.id == doc_id), None)
        if idx is None:
            return False
        _docs.pop(idx)
        _vecs.pop(idx)
    _kg_remove_doc(doc_id)
    return True


def _load_model() -> SentenceTransformer:
    """
    加载句子嵌入模型
    
    优先尝试从本地路径加载模型，如果本地不存在则从HuggingFace下载。
    
    Returns:
        SentenceTransformer: 加载的模型实例
        
    Raises:
        RuntimeError: 如果模型加载失败
    """
    try:
        # 确保使用HuggingFace国内镜像（无VPN环境）
        try:
            from utils.huggingface_mirror import ensure_mirror_configured
            ensure_mirror_configured()
        except ImportError:
            # 如果镜像工具不可用，手动设置
            import os
            if "HF_ENDPOINT" not in os.environ:
                mirror_config = Path(__file__).parent.parent.parent / ".config" / "china_mirrors.env"
                if mirror_config.exists():
                    try:
                        with open(mirror_config, 'r') as f:
                            for line in f:
                                if line.startswith("export HF_ENDPOINT="):
                                    os.environ["HF_ENDPOINT"] = line.split("=", 1)[1].strip().strip('"')
                                    logger.info(f"从配置文件加载镜像: {os.environ['HF_ENDPOINT']}")
                                    break
                    except Exception:
                        pass
                if "HF_ENDPOINT" not in os.environ:
                    os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                    logger.info("使用默认HuggingFace国内镜像: https://hf-mirror.com")
        
        if MODEL_DIR.exists():
            return SentenceTransformer(str(MODEL_DIR), device="cpu")
        # 回退到在线模型（使用配置的镜像）
        logger.info("从HuggingFace下载模型（使用镜像: %s）", os.environ.get("HF_ENDPOINT", "默认"))
        return SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    except Exception as e:
        logger.error(f"模型加载失败: {e}")
        logger.info("提示：如果是网络问题，请运行 'bash scripts/setup_china_mirrors.sh' 配置国内镜像")
        logger.info("然后运行 'bash scripts/download_model.sh' 下载模型到本地")
        raise RuntimeError(f"load model failed (local={MODEL_DIR}): {e}")


_model = _load_model()
_DIM = int(getattr(_model, "get_sentence_embedding_dimension", lambda: 384)())
# 启动时尝试加载磁盘索引（若存在）
try:
    _load_index()
except Exception:
    pass


def _embed_texts(texts: List[str]) -> np.ndarray:
    """
    将文本列表编码为向量嵌入
    
    使用已加载的句子嵌入模型对文本进行编码，并归一化结果。
    归一化后的向量可以直接使用点积计算余弦相似度。
    
    Args:
        texts: 要编码的文本列表
        
    Returns:
        np.ndarray: 形状为 (len(texts), embedding_dim) 的归一化向量数组
        
    Raises:
        RuntimeError: 如果模型未加载或编码失败
    """
    # 归一化，便于点积=cosine
    return _model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def _index_size() -> int:
    """
    获取当前索引中的文档数量
    
    Returns:
        int: 索引中的文档数量
    """
    return len(_docs)


def _index_matrix() -> np.ndarray:
    """
    获取索引的完整向量矩阵
    
    将所有文档的向量组合成一个矩阵，用于批量相似度计算。
    
    Returns:
        np.ndarray: 形状为 (n_docs, embedding_dim) 的归一化向量矩阵
        
    Raises:
        ValueError: 如果索引为空或向量维度不一致
    """
    if not _vecs:
        return np.zeros((0, _DIM), dtype=np.float32)
    return np.vstack(_vecs).astype(np.float32)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "RAG & Knowledge Graph", "version": "1.0.0"}

@app.get("/readyz")
def readyz() -> Dict[str, Any]:
    # 模型可用性
    model_ok = bool(_model)
    dim_ok = isinstance(_DIM, int) and _DIM > 0

    # 索引可用性
    try:
        n_docs = _index_size()
        mat_ok = True
        if n_docs > 0:
            _ = _index_matrix()
    except Exception:
        mat_ok = False
        n_docs = -1

    # KG 快照文件存在性（可选）
    kg_file_exists = KG_FILE.exists()

    return {
        "model_ok": model_ok,
        "dim_ok": dim_ok,
        "index_docs": max(0, n_docs),
        "index_matrix_ok": mat_ok,
        "kg_file_exists": kg_file_exists,
        "ts": time.time(),
    }


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """功能界面主页"""
    dashboard_path = Path(__file__).parent.parent / "web" / "enhanced_dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    else:
        # 如果文件不存在，返回简单的界面
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Stack Super Enhanced - 功能界面</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 12px; }
                h1 { color: #667eea; }
                .link { display: block; padding: 15px; margin: 10px 0; background: #667eea; color: white; text-decoration: none; border-radius: 8px; }
                .link:hover { background: #764ba2; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 AI Stack Super Enhanced</h1>
                <p>功能界面文件未找到，请访问以下链接：</p>
                <a href="/docs" class="link">📚 API文档 (Swagger)</a>
                <a href="/redoc" class="link">📖 API文档 (ReDoc)</a>
                <a href="/readyz" class="link">💚 健康检查</a>
                <a href="/kg/snapshot" class="link">🕸️ 知识图谱快照</a>
                <a href="/index/info" class="link">📊 索引信息</a>
            </div>
        </body>
        </html>
        """)


@app.get("/", response_class=HTMLResponse)
def root():
    """根路径重定向到功能界面"""
    return dashboard()


class IngestReq(BaseModel):
    path: Optional[str] = None
    text: Optional[str] = None
    doc_id: Optional[str] = None
    save_index: Optional[bool] = True
    chunk_size: Optional[int] = None
    chunk_overlap: int = 0
    upsert: bool = False


def _ingest_text(
    text: str,
    *,
    src_path: Optional[str],
    doc_id: Optional[str],
    verify_truth: bool = True,
    enable_semantic_dedup: bool = False,
    use_semantic_segmentation: bool = True,
) -> str:
    """
    将文本摄入到索引并添加到知识图谱
    
    根据需求1.3：所有进入RAG库的信息都会进行去伪的处理，保证信息知识数据等的真实性和准确性
    根据差距3：使用语义分割优化（SAGE风格）提升检索相关性
    
    Args:
        text: 要摄入的文本内容
        src_path: 源文件路径（可选）
        doc_id: 文档ID（可选，如果不提供则自动生成）
        verify_truth: 是否进行真实性验证（默认True）
        enable_semantic_dedup: 是否启用语义去重
        use_semantic_segmentation: 是否使用语义分割优化（差距3）
        
    Returns:
        生成的文档ID
        
    Raises:
        ValueError: 如果文本为空或验证失败
    """
    if not text or not text.strip():
        raise ValueError("文本内容不能为空")
    
    # 语义分割优化（差距3：SAGE风格语义分割）
    if use_semantic_segmentation and len(text) > 500:
        try:
            from ..core.semantic_segmentation import get_semantic_segmentation_optimizer
            
            optimizer = get_semantic_segmentation_optimizer(embedding_model=_model)
            
            # 异步调用需要在同步函数中处理
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            chunks = loop.run_until_complete(
                optimizer.segment_text(text, doc_id=doc_id)
            )
            
            # 如果有多个语义分块，分别摄入
            if chunks and len(chunks) > 1:
                doc_ids = []
                for chunk in chunks:
                    chunk_id = f"{doc_id or str(uuid.uuid4())}-chunk-{chunk.id}"
                    # 递归调用（跳过分割，避免循环）
                    _ingest_text_single(
                        chunk.content,
                        src_path=src_path,
                        doc_id=chunk_id,
                        verify_truth=verify_truth,
                        enable_semantic_dedup=enable_semantic_dedup,
                        use_semantic_segmentation=False,  # 避免重复分割
                    )
                    doc_ids.append(chunk_id)
                
                # 返回主文档ID
                return doc_ids[0] if doc_ids else doc_id or str(uuid.uuid4())
            elif chunks:
                # 只有一个分块，使用分块内容
                text = chunks[0].content
        except Exception as e:
            logger.warning(f"语义分割优化失败，使用原始文本: {e}")
    
    # 调用单次摄入函数
    return _ingest_text_single(
        text,
        src_path=src_path,
        doc_id=doc_id,
        verify_truth=verify_truth,
        enable_semantic_dedup=enable_semantic_dedup,
        use_semantic_segmentation=False,
    )


def _ingest_text_single(
    text: str,
    *,
    src_path: Optional[str],
    doc_id: Optional[str],
    verify_truth: bool = True,
    enable_semantic_dedup: bool = False,
    use_semantic_segmentation: bool = False,
) -> str:
    """
    单次文本摄入（内部函数，避免递归）
    """
    if not text or not text.strip():
        raise ValueError("文本内容不能为空")
    
    # 真实性验证（需求1.3）
    if verify_truth:
        try:
            # 延迟导入避免循环依赖
            from ..pipelines.truth_verification_integration import get_truth_verification_integration
            
            verifier = get_truth_verification_integration(
                min_credibility=0.65,  # 可配置
                auto_filter=True,       # 自动过滤低可信度内容
            )
            
            # 获取已有文档用于一致性检查（采样）
            existing_texts = [doc.text for doc in _docs[:10]]  # 取前10个文档
            
            verification_result = verifier.verify_before_ingest(
                text=text,
                source=src_path,
                metadata={"doc_id": doc_id} if doc_id else None,
                existing_docs=existing_texts,
            )
            
            if not verification_result.get("verified", True):
                credibility = verification_result.get("credibility_score", 0.0)
                reason = verification_result.get("reason", "可信度不足")
                logger.warning(
                    f"文档真实性验证未通过: credibility={credibility:.3f}, reason={reason}"
                )
                # 根据配置决定是否拒绝
                # 当前配置为自动过滤，所以拒绝
                raise ValueError(
                    f"真实性验证未通过: {reason} (可信度: {credibility:.3f})"
                )
            
            logger.debug(
                f"文档真实性验证通过: credibility={verification_result.get('credibility_score', 0.0):.3f}"
            )
            
        except ImportError:
            # 如果模块未安装，记录警告但继续处理
            logger.warning("真实性验证模块未找到，跳过验证")
        except Exception as e:
            # 验证过程出错，根据配置决定
            logger.error(f"真实性验证过程出错: {e}")
            # 默认继续处理（可根据配置修改）
            if verify_truth:
                # 如果要求验证，验证失败则拒绝
                raise ValueError(f"真实性验证失败: {str(e)}")
    
    vec = _embed_texts([text])[0]
    did = doc_id or str(uuid.uuid4())
    with INDEX_LOCK:
        _docs.append(Doc(id=did, text=text, path=src_path))
        _vecs.append(vec)
    _kg_add(did, text, src_path)
    return did


@app.post("/rag/ingest")
def rag_ingest(req: IngestReq, _: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    摄入文本或文件到RAG索引
    
    Args:
        req: 摄入请求，包含path或text
        _: API密钥验证（通过Depends自动处理）
        
    Returns:
        Dict包含成功状态、插入数量、文档ID列表和索引大小
        
    Raises:
        HTTPException: 如果路径或文本无效、文件不存在或读取失败
    """
    if not req.path and not req.text:
        raise HTTPException(
            status_code=400,
            detail="必须提供'path'或'text'参数"
        )
    text = req.text
    if req.path:
        p = Path(req.path).expanduser()
        if not p.exists():
            raise HTTPException(
                status_code=404,
                detail=f"文件不存在: {p}"
            )
        if not p.is_file():
            raise HTTPException(
                status_code=400,
                detail=f"路径不是文件: {p}"
            )
        try:
            # 纯文本读取
            text = p.read_text(encoding="utf-8", errors="ignore")
        except PermissionError as e:
            raise HTTPException(
                status_code=403,
                detail=f"无权限读取文件: {str(e)}"
            )
        except OSError as e:
            raise HTTPException(
                status_code=400,
                detail=f"读取文件失败: {str(e)}"
            )
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="文本内容为空"
        )

    inserted = 0
    doc_ids: List[str] = []

    def add_one(_txt: str, _id: Optional[str] = None):
        nonlocal inserted
        if req.upsert and _id:
            _delete_by_id(_id)  # 覆盖同 id
        did = _ingest_text(_txt, src_path=req.path, doc_id=_id)
        inserted += 1
        doc_ids.append(did)

    # 可选字符级分片
    if req.chunk_size and req.chunk_size > 0:
        s = text
        k = req.chunk_size
        ov = max(0, req.chunk_overlap or 0)
        i = 0
        part = 0
        while i < len(s):
            chunk = s[i : i + k]
            if chunk.strip():
                cid = f"{req.doc_id or Path(req.path or 'doc').stem}-chunk-{part}"
                add_one(chunk, cid)
                part += 1
            i += max(1, k - ov)
    else:
        add_one(text, req.doc_id)

    if req.save_index:
        _save_index()
    return {
        "success": True,
        "inserted": inserted,
        "ids": doc_ids,
        "size": _index_size(),
    }


@app.post("/rag/ingest_file")
async def rag_ingest_file(
    file: UploadFile = File(...),
    save_index: bool = True,
    doc_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = 0,
    upsert: bool = False,
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    上传文件并摄入到RAG索引
    
    Args:
        file: 上传的文件
        save_index: 是否保存索引到磁盘
        doc_id: 可选的文档ID
        chunk_size: 分块大小（字符数）
        chunk_overlap: 分块重叠大小
        upsert: 如果文档ID已存在，是否更新
        
    Returns:
        Dict包含成功状态、插入数量、文档ID列表和索引大小
        
    Raises:
        HTTPException: 如果文件读取失败或文本为空
    """
    try:
        data = await file.read()
        text = data.decode("utf-8", errors="ignore")
    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail=f"文件编码错误，无法解码为UTF-8: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"读取上传文件失败: {str(e)}"
        )

    inserted = 0
    ids: List[str] = []

    def add_one(_txt: str, _id: Optional[str] = None):
        nonlocal inserted
        if upsert and _id:
            _delete_by_id(_id)
        did = _ingest_text(_txt, src_path=file.filename, doc_id=_id)
        ids.append(did)
        inserted += 1

    if chunk_size and chunk_size > 0:
        s = text
        k = chunk_size
        ov = max(0, chunk_overlap or 0)
        i = 0
        part = 0
        while i < len(s):
            chunk = s[i : i + k]
            if chunk.strip():
                cid = f"{(doc_id or Path(file.filename or 'doc').stem)}-chunk-{part}"
                add_one(chunk, cid)
                part += 1
            i += max(1, k - ov)
    else:
        add_one(text, doc_id)

    if save_index:
        _save_index()
    return {"success": True, "inserted": inserted, "ids": ids, "size": _index_size()}


@app.post("/rag/ingest_dir")
def rag_ingest_dir(
    dir_path: str = Query(..., min_length=1),
    glob: str = Query(default="**/*.txt"),
    save_index: bool = True,
    limit: Optional[int] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = 0,
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    批量摄入目录中的文件到RAG索引
    
    Args:
        dir_path: 目录路径
        glob: 文件匹配模式
        save_index: 是否保存索引到磁盘
        limit: 最大处理文件数
        chunk_size: 分块大小（字符数）
        chunk_overlap: 分块重叠大小
        
    Returns:
        Dict包含成功状态、插入数量、索引大小和文档ID数量
        
    Raises:
        HTTPException: 如果目录不存在或无法访问
    """
    p = Path(dir_path).expanduser()
    if not p.exists():
        raise HTTPException(
            status_code=404,
            detail=f"目录不存在: {p}"
        )
    if not p.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"路径不是目录: {p}"
        )
    inserted = 0
    ids: List[str] = []
    for i, f in enumerate(p.glob(glob)):
        if limit and i >= limit:
            break
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if chunk_size and chunk_size > 0:
            s = text
            k = chunk_size
            ov = max(0, chunk_overlap or 0)
            j = 0
            part = 0
            while j < len(s):
                ch = s[j : j + k]
                if ch.strip():
                    cid = f"{f.stem}-chunk-{part}"
                    did = _ingest_text(ch, src_path=str(f), doc_id=cid)
                    ids.append(did)
                    inserted += 1
                    part += 1
                j += max(1, k - ov)
        else:
            did = _ingest_text(text, src_path=str(f), doc_id=f.stem)
            ids.append(did)
            inserted += 1
    if save_index:
        _save_index()
    return {
        "success": True,
        "inserted": inserted,
        "size": _index_size(),
        "count_ids": len(ids),
    }


@app.get("/index/info")
def index_info() -> Dict[str, Any]:
    """
    获取索引信息
    
    Returns:
        Dict包含索引大小、维度和后端类型
    """
    return {"size": _index_size(), "dimension": _DIM, "backend": "InMemory"}


@app.get("/index/ids")
def index_ids() -> Dict[str, List[str]]:
    """
    获取所有文档ID列表
    
    Returns:
        Dict包含所有文档ID列表
    """
    return {"ids": [d.id for d in _docs]}


@app.delete("/index/clear")
def index_clear(
    remove_file: bool = Query(default=True, description="是否删除磁盘上的索引文件"),
    clear_kg: bool = Query(default=True, description="是否同时清空知识图谱"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    清空索引和可选的知识图谱
    
    Args:
        remove_file: 是否删除磁盘上的索引文件
        clear_kg: 是否同时清空知识图谱
        _: API密钥验证
        
    Returns:
        Dict包含清空前的大小、清空后的大小和KG清理结果
    """
    before = _index_size()
    _docs.clear()
    _vecs.clear()
    if remove_file:
        try:
            if INDEX_DOCS.exists():
                INDEX_DOCS.unlink()
            if INDEX_VECS.exists():
                INDEX_VECS.unlink()
        except OSError as e:
            # 记录错误但不中断清理过程
            pass
    # 同时处理 KG 清理（内存与可选文件）
    kg = {}
    if clear_kg:
        kg = _kg_clear(remove_file=remove_file)
    return {"cleared": before, "before": before, "kg": kg if clear_kg else None}


@app.post("/index/save")
def index_save(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    保存索引到磁盘
    
    Returns:
        Dict包含保存状态、路径、大小和维度信息
    """
    return _save_index()


@app.post("/index/load")
def index_load(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    从磁盘加载索引
    
    Returns:
        Dict包含加载状态、索引大小和维度信息
    """
    return _load_index()


@app.delete("/index/delete")
def index_delete(
    doc_id: str = Query(..., min_length=1, description="要删除的文档ID"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    根据ID删除文档
    
    Args:
        doc_id: 要删除的文档ID
        _: API密钥验证
        
    Returns:
        Dict包含删除数量和当前索引大小
        
    Raises:
        HTTPException: 如果文档ID不存在
    """
    ok = _delete_by_id(doc_id)
    if not ok:
        raise HTTPException(
            status_code=404,
            detail=f"文档ID不存在: {doc_id}"
        )
    return {"deleted": 1, "size": _index_size()}


class SearchItem(BaseModel):
    id: str
    score: float
    snippet: str
    path: Optional[str] = None


class SearchResp(BaseModel):
    items: List[SearchItem]


@app.get("/rag/search", response_model=SearchResp)
def rag_search(
    query: str = Query(..., min_length=1, description="搜索查询文本"),
    top_k: int = Query(5, ge=1, le=50, description="返回结果数量"),
    modality: Optional[str] = Query("text", description="检索模态: text, image, audio, multimodal"),
    fusion_strategy: Optional[str] = Query("weighted", description="融合策略: weighted, rank_fusion, simple"),
    use_kg_infused: Optional[bool] = Query(False, description="是否使用KG-Infused RAG（差距4）"),
    _: bool = Depends(require_api_key),
) -> SearchResp:
    """
    语义搜索RAG索引中的文档（支持多模态检索和KG-Infused RAG）
    
    根据需求1.5：支持多模态检索（文本、图像、音频）
    根据差距4：支持KG-Infused RAG（知识图谱深度融合）
    
    Args:
        query: 搜索查询文本
        top_k: 返回结果数量（1-50）
        modality: 检索模态
            - text: 仅文本检索（默认）
            - image: 仅图像检索
            - audio: 仅音频检索
            - multimodal: 混合模态检索（文本+图像+音频）
        fusion_strategy: 融合策略（仅用于multimodal）
            - weighted: 加权融合（默认）
            - rank_fusion: 排序融合（RRF）
            - simple: 简单合并
        use_kg_infused: 是否使用KG-Infused RAG（知识图谱深度融合）
            
    Returns:
        SearchResp包含搜索结果列表
        
    Raises:
        HTTPException: 如果搜索过程中发生错误
    """
    if _index_size() == 0:
        return SearchResp(items=[])
    
    try:
        # KG-Infused RAG（差距4：知识图谱深度融合）
        if use_kg_infused:
            try:
                from ..core.kg_infused_rag import get_kg_infused_rag
                
                # 创建简单的RAG检索器适配器
                class SimpleRAGRetriever:
                    async def search(self, query: str, top_k: int):
                        q = _embed_texts([query])[0].astype(np.float32)
                        X = _index_matrix()
                        scores = (X @ q).tolist()
                        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                        items = []
                        for i in order:
                            d = _docs[i]
                            items.append({
                                "id": d.id,
                                "document_id": d.id,
                                "content": d.text,
                                "snippet": d.text[:200],
                                "score": float(scores[i]),
                                "metadata": {"path": d.path},
                            })
                        return {"items": items}
                
                # 获取KG查询引擎
                kg_query_engine = None
                try:
                    from ..knowledge_graph.enhanced_kg_query import get_kg_query_engine
                    if _kg_nodes and _kg_edges:
                        kg_query_engine = get_kg_query_engine(_kg_nodes, _kg_edges)
                except Exception:
                    pass
                
                # 创建KG-Infused RAG实例
                rag_retriever = SimpleRAGRetriever()
                kg_infused_rag = get_kg_infused_rag(
                    rag_retriever=rag_retriever,
                    kg_query_engine=kg_query_engine,
                )
                
                # 执行KG增强检索（异步需要特殊处理）
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(
                    kg_infused_rag.retrieve_with_kg(query, top_k=top_k)
                )
                
                # 转换为SearchItem格式
                items = []
                for doc in result.get("documents", []):
                    items.append(
                        SearchItem(
                            id=doc.get("id") or doc.get("document_id", ""),
                            score=doc.get("score", doc.get("kg_enhanced_score", 0.0)),
                            snippet=doc.get("snippet", doc.get("content", ""))[:200],
                            path=doc.get("metadata", {}).get("path", ""),
                        )
                    )
                
                logger.info(f"KG-Infused RAG检索完成：{len(items)} 个结果，KG上下文：{len(result.get('kg_context', ''))} 字符")
                return SearchResp(items=items)
                
            except (ImportError, Exception) as e:
                logger.warning(f"KG-Infused RAG失败，回退到标准检索: {e}")
                # 继续使用标准检索
                pass
        
        # 如果是多模态检索，尝试使用多模态检索器
        if modality and modality.lower() in ["multimodal", "image", "audio"]:
            try:
                from ..core.multimodal_retrieval import get_multimodal_retriever
                
                multimodal_retriever = get_multimodal_retriever()
                
                # 确定要检索的模态
                if modality.lower() == "multimodal":
                    modalities = ["text", "image", "audio"]
                elif modality.lower() == "image":
                    modalities = ["image"]
                elif modality.lower() == "audio":
                    modalities = ["audio"]
                else:
                    modalities = ["text"]
                
                # 执行多模态检索（异步需要特殊处理）
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                results = loop.run_until_complete(
                    multimodal_retriever.hybrid_retrieve(
                        query=query,
                        modalities=modalities,
                        top_k=top_k,
                        fusion_strategy=fusion_strategy or "weighted",
                    )
                )
                
                # 转换为SearchItem格式
                items = []
                for result in results:
                    items.append(
                        SearchItem(
                            id=result.document_id,
                            score=result.similarity_score,
                            snippet=result.content[:200] if result.content else "",
                            path=result.source,
                        )
                    )
                
                return SearchResp(items=items)
                
            except (ImportError, Exception) as e:
                logger.warning(f"多模态检索失败，回退到文本检索: {e}")
                # 回退到文本检索
                pass
        
        # 默认文本检索（原有逻辑）
        q = _embed_texts([query])[0].astype(np.float32)
        X = _index_matrix()  # 已归一化，点积=cos
        scores = (X @ q).tolist()
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        items = []
        for i in order:
            d = _docs[i]
            items.append(
                SearchItem(
                    id=d.id,
                    score=float(scores[i]),
                    snippet=d.text[:200],
                    path=d.path,
                )
            )
        return SearchResp(items=items)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@app.get("/rag/groups")
def rag_groups(
    k: int = Query(3, ge=1, le=50, description="分组数量"),
    max_items: int = Query(100, ge=1, le=1000, description="最大处理文档数"),
) -> Dict[str, Any]:
    """
    对索引中的文档进行语义分组
    
    Args:
        k: 分组数量（1-50）
        max_items: 最大处理文档数（1-1000）
        
    Returns:
        Dict包含分组结果、分组数量和总数
    """
    n = _index_size()
    if n == 0:
        return {"success": True, "k": 0, "total": 0, "groups": []}
    idx = list(range(min(n, max_items)))
    k = min(k, len(idx))
    # 选择前k个作为中心，按最大余弦相似度分配
    X = _index_matrix()[idx]
    ids = [_docs[i].id for i in idx]
    centers = X[:k]
    assigns: List[List[int]] = [[] for _ in range(k)]
    for i, vec in enumerate(X):
        if k == 0:
            break
        sims = (centers @ vec).tolist()
        c = int(np.argmax(sims))
        assigns[c].append(i)
    groups = []
    for ci, members in enumerate(assigns):
        gids = [ids[m] for m in members]
        groups.append(
            {
                "center": ids[ci] if ci < len(ids) else None,
                "size": len(gids),
                "ids": gids,
            }
        )
    return {"success": True, "k": k, "total": len(idx), "groups": groups}


@app.get("/kg/snapshot")
def kg_snapshot() -> Dict[str, Any]:
    """
    获取知识图谱快照
    
    Returns:
        Dict包含知识图谱的实体、节点和边的信息，以及示例数据
    """
    # 提供简要统计、实体列表与少量示例
    entities = [
        {
            "id": n["id"],
            "type": n.get("type"),
            "value": n.get("value"),
            "count": n.get("count", 0),
        }
        for n in _kg_nodes.values()
        if n.get("type") in {"email", "url"}
    ]
    emails = [e["value"] for e in entities if e["type"] == "email"][:10]
    urls = [e["value"] for e in entities if e["type"] == "url"][:10]
    return {
        "success": True,
        "nodes": len(_kg_nodes),
        "edges": len(_kg_edges),
        "entities": entities,
        "sample": {"emails": emails, "urls": urls},
    }


@app.post("/kg/save")
def kg_save(
    path: Optional[str] = Query(default=None, description="保存路径（可选）"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    保存知识图谱到文件
    
    Args:
        path: 保存路径（如果不提供，使用默认路径）
        _: API密钥验证
        
    Returns:
        Dict包含保存状态、路径、节点数和边数
    """
    return _kg_save(Path(path) if path else None)


@app.delete("/kg/clear")
def kg_clear(
    remove_file: bool = Query(True, description="是否删除磁盘文件"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    清空知识图谱
    
    Args:
        remove_file: 是否删除磁盘上的知识图谱文件
        _: API密钥验证
        
    Returns:
        Dict包含清理状态和清理的节点/边数量
    """
    return _kg_clear(remove_file=remove_file)


@app.post("/kg/load")
def kg_load(
    path: Optional[str] = Query(default=None, description="加载路径（可选）"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    从文件加载知识图谱
    
    Args:
        path: 加载路径（如果不提供，使用默认路径）
        _: API密钥验证
        
    Returns:
        Dict包含加载状态、路径、节点数和边数
        
    Raises:
        HTTPException: 如果文件不存在或读取失败
    """
    return _kg_load(Path(path) if path else None)


# 已有占位
@app.get("/kg/stats")
def kg_stats() -> Dict[str, Any]:
    """
    获取知识图谱统计信息
    
    Returns:
        Dict包含节点数、边数和状态信息
    """
    return {"nodes": len(_kg_nodes), "edges": len(_kg_edges), "ok": True}


@app.post("/index/rebuild")
def index_rebuild(
    reload_docs: bool = Query(True, description="是否从磁盘重新加载文档"),
    batch: int = Query(256, ge=1, le=4096, description="批处理大小"),
    save_index: bool = Query(True, description="重建后是否保存索引"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    重建索引（重新计算所有向量）
    
    用于在模型更新或索引损坏时重新构建整个索引。
    可以批量处理大量文档，避免内存溢出。
    
    Args:
        reload_docs: 是否从磁盘重新加载文档列表
        batch: 批处理大小（1-4096），控制每次处理的文档数
        save_index: 重建后是否保存索引到磁盘
        _: API密钥验证
        
    Returns:
        Dict包含重建的文档数量、维度和保存状态
        
    Raises:
        HTTPException: 如果重建过程中发生错误
    """
    try:
        # 可选从磁盘重新加载 docs
        if reload_docs and INDEX_DOCS.exists():
            docs = json.loads(INDEX_DOCS.read_text(encoding="utf-8"))
            with INDEX_LOCK:
                _docs.clear()
                _docs.extend(Doc(**d) for d in docs)
        # 重新计算全部向量
        with INDEX_LOCK:
            _vecs.clear()
        texts = [d.text for d in _docs]
        new_vecs: List[np.ndarray] = []
        for i in range(0, len(texts), batch):
            new_vecs.append(_embed_texts(texts[i : i + batch]))
        with INDEX_LOCK:
            if new_vecs:
                _vecs.extend(v.astype(np.float32) for v in np.vstack(new_vecs))
        if save_index:
            _save_index()
        return {"rebuilt": _index_size(), "dimension": _DIM, "saved": bool(save_index)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"索引重建失败: {str(e)}"
        )


@app.get("/kg/query")
def kg_query(
    query_type: str = Query("entities", description="查询类型：entities, relations, path, subgraph, statistics"),
    type: Optional[str] = Query(None, description="实体类型（email、url等）"),
    value: Optional[str] = Query(None, description="实体值"),
    value_pattern: Optional[str] = Query(None, description="实体值模式（正则表达式）"),
    source: Optional[str] = Query(None, description="源实体ID（用于关系或路径查询）"),
    target: Optional[str] = Query(None, description="目标实体ID（用于关系或路径查询）"),
    relation_type: Optional[str] = Query(None, description="关系类型"),
    max_depth: int = Query(2, ge=1, le=5, description="最大深度（用于路径和子图查询）"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
) -> Dict[str, Any]:
    """
    增强的知识图谱查询（需求1.8）
    
    支持多种查询方式：
    - entities: 查询实体
    - relations: 查询关系
    - path: 查询两个实体之间的路径
    - subgraph: 查询子图（以某个实体为中心）
    - statistics: 查询统计信息
    
    Args:
        query_type: 查询类型
        type: 实体类型（可选）
        value: 实体值（可选）
        value_pattern: 实体值模式（正则表达式，可选）
        source: 源实体ID（可选）
        target: 目标实体ID（可选）
        relation_type: 关系类型（可选）
        max_depth: 最大深度（1-5）
        limit: 返回数量限制（1-1000）
        
    Returns:
        查询结果字典，格式根据查询类型而定
    """
    try:
        # 导入增强查询引擎
        from ..knowledge_graph.enhanced_kg_query import get_kg_query_engine
        
        # 创建查询引擎
        query_engine = get_kg_query_engine(_kg_nodes, _kg_edges)
        
        if query_type == "entities":
            # 实体查询
            results = query_engine.query_entities(
                entity_type=type,
                value_pattern=value_pattern or (f".*{value}.*" if value else None),
                limit=limit,
            )
            return {
                "success": True,
                "query_type": "entities",
                "results": results,
                "count": len(results),
            }
        
        elif query_type == "relations":
            # 关系查询
            source_entity = source or (_kg_node_id(type, value) if type and value else None)
            results = query_engine.query_relations(
                source_entity=source_entity,
                target_entity=target,
                relation_type=relation_type,
                limit=limit,
            )
            return {
                "success": True,
                "query_type": "relations",
                "results": results,
                "count": len(results),
            }
        
        elif query_type == "path":
            # 路径查询
            if not source or not target:
                # 兼容旧的查询方式：type + value 作为 source
                if type and value:
                    source_entity = _kg_node_id(type, value)
                else:
                    return {"success": False, "error": "需要提供source和target参数"}
            else:
                source_entity = source
            
            path = query_engine.query_path(
                source_entity=source_entity,
                target_entity=target,
                max_depth=max_depth,
            )
            
            if path:
                return {
                    "success": True,
                    "query_type": "path",
                    "path": path,
                    "path_length": len(path) - 1,
                }
            else:
                return {
                    "success": True,
                    "query_type": "path",
                    "path": None,
                    "message": "未找到路径",
                }
        
        elif query_type == "subgraph":
            # 子图查询
            center = source or (_kg_node_id(type, value) if type and value else None)
            if not center:
                return {"success": False, "error": "需要提供center实体（通过source或type+value）"}
            
            subgraph = query_engine.query_subgraph(
                center_entity=center,
                max_depth=max_depth,
                max_nodes=limit,
            )
            return {
                "success": True,
                "query_type": "subgraph",
                "subgraph": subgraph,
            }
        
        elif query_type == "statistics":
            # 统计查询
            stats = query_engine.query_statistics()
            return {
                "success": True,
                "query_type": "statistics",
                "statistics": stats,
            }
        
        else:
            # 兼容旧的查询方式（按type和value查询文档）
            if type and value:
                nid = _kg_node_id(type, value)
                if nid not in _kg_nodes:
                    return {"success": True, "docs": [], "count": 0}
                dnids = [e["src"] for e in _kg_edges if e.get("dst") == nid]
                ids = [n.split(":", 1)[1] for n in dnids if n.startswith("doc:")]
                # 映射到现存文档（可能已被删除）
                existing = {d.id for d in _docs}
                ids = [i for i in ids if i in existing]
                return {"success": True, "docs": ids, "count": len(ids)}
            else:
                return {"success": False, "error": f"未知的查询类型: {query_type}"}
    
    except Exception as e:
        logger.error(f"知识图谱查询失败: {e}")
        return {"success": False, "error": str(e)}
