#!/usr/bin/env python3
"""
Enhanced RAG Core API
对应需求: 1.1 所有格式文件处理, 1.2 四项预处理, 1.3 去伪处理, 1.6 词义自主分组
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/api/rag_api.py
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# 导入核心模块
from core.hybrid_rag_engine import HybridRAGEngine
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pipelines.smart_ingestion_pipeline import SmartIngestionPipeline
from pydantic import BaseModel, Field

from processors.file_processors.universal_file_parser import UniversalFileParser

logger = logging.getLogger("rag_api")

# 创建路由
router = APIRouter(
    prefix="/rag", tags=["RAG Core API"], responses={404: {"description": "Not found"}}
)


# Pydantic模型定义
class SearchQuery(BaseModel):
    """搜索查询模型"""

    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(10, description="返回结果数量")
    threshold: float = Field(0.7, description="相似度阈值")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    include_metadata: bool = Field(True, description="是否包含元数据")


class SearchResponse(BaseModel):
    """搜索响应模型"""

    results: List[Dict[str, Any]]
    total_count: int
    query_time: float
    query_id: str


class DocumentChunk(BaseModel):
    """文档分块模型"""

    content: str
    metadata: Dict[str, Any]
    chunk_id: str
    document_id: str


class IngestionRequest(BaseModel):
    """文档注入请求模型"""

    documents: List[Dict[str, Any]]
    preprocess: bool = Field(True, description="是否预处理")
    verify_truth: bool = Field(True, description="是否验证真实性")
    group_semantically: bool = Field(True, description="是否语义分组")


class IngestionResponse(BaseModel):
    """文档注入响应模型"""

    success: bool
    processed_count: int
    failed_count: int
    failed_documents: List[Dict[str, Any]]
    ingestion_id: str


class GroupingRequest(BaseModel):
    """语义分组请求模型"""

    documents: List[Dict[str, Any]]
    grouping_strategy: str = Field("semantic", description="分组策略")
    max_groups: Optional[int] = Field(None, description="最大分组数")


class GroupingResponse(BaseModel):
    """语义分组响应模型"""

    groups: List[Dict[str, Any]]
    total_groups: int
    grouping_strategy: str


# 全局组件实例
_rag_engine = None
_file_parser = None
_ingestion_pipeline = None


# 依赖注入
async def get_rag_engine() -> HybridRAGEngine:
    """获取RAG引擎实例"""
    global _rag_engine
    if _rag_engine is None:
        try:
            # 创建本地 RAG 引擎实例，并注入本地向量存储与语义引擎（A1 方案）
            _rag_engine = HybridRAGEngine()

            # 延迟导入 heavy 依赖
            try:
                import faiss
                from sentence_transformers import SentenceTransformer
            except Exception:
                SentenceTransformer = None
                faiss = None

            # Lightweight FAISS wrapper
            class FAISSWrapper:
                def __init__(self, dim: int = 384):
                    self.dim = dim
                    self.index = None
                    self.id_map = []

                def initialize(self):
                    if faiss is None:
                        return False
                    # 使用 HNSW (更适合 CPU) 或 Flat 索引
                    try:
                        self.index = faiss.IndexHNSWFlat(self.dim, 32)
                        # 可选：设置 efSearch/efConstruction
                        return True
                    except Exception:
                        try:
                            self.index = faiss.IndexFlatL2(self.dim)
                            return True
                        except Exception:
                            return False

                def add_documents(self, vectors: List[List[float]], ids: List[str]):
                    if self.index is None:
                        raise RuntimeError("FAISS index not initialized")
                    import numpy as np

                    vecs = np.array(vectors).astype("float32")
                    self.index.add(vecs)
                    self.id_map.extend(ids)

                def save_index(self, path: str):
                    try:
                        if faiss is None or self.index is None:
                            return False
                        faiss.write_index(self.index, path)
                        # save id_map
                        import pickle

                        with open(path + ".ids.pkl", "wb") as f:
                            pickle.dump(self.id_map, f)
                        return True
                    except Exception:
                        return False

                def load_index(self, path: str):
                    try:
                        if faiss is None:
                            return False
                        self.index = faiss.read_index(path)
                        import pickle

                        with open(path + ".ids.pkl", "rb") as f:
                            self.id_map = pickle.load(f)
                        return True
                    except Exception:
                        return False

                def retrieve(
                    self,
                    query: str = None,
                    vector: List[float] = None,
                    filters=None,
                    top_k: int = 10,
                ):
                    # 支持基于 vector 的检索；如果提供 query 则上层应先 encode
                    if self.index is None:
                        return []
                    import numpy as np

                    if vector is None:
                        return []

                    vec = np.array([vector]).astype("float32")
                    D, idxs = self.index.search(vec, top_k)
                    results = []
                    for score, idx in zip(D[0], idxs[0]):
                        if idx < 0 or idx >= len(self.id_map):
                            continue
                        results.append(
                            {
                                "document_id": self.id_map[idx],
                                "content": "",
                                "score": float(score),
                                "metadata": {},
                                "source": "faiss",
                            }
                        )
                    return results

            # Lightweight local semantic engine using sentence-transformers
            # Supports loading from a local cache folder to avoid remote downloads
            class LocalSemanticEngine:
                def __init__(
                    self,
                    model_name: str = "all-MiniLM-L6-v2",
                    local_model_path: Optional[str] = "./models/all-MiniLM-L6-v2",
                ):
                    self.model_name = model_name
                    self.local_model_path = local_model_path
                    self.model = None
                    # will be set to FAISSWrapper instance after instantiation
                    self.vector_store = None

                def initialize(self):
                    """Initialize semantic model only from a local path.

                    In offline environments we must NOT attempt to download models
                    from the Internet. If the local_model_path exists, load it; otherwise
                    return False immediately so the system falls back to the
                    in-memory semantic/fallback behavior.
                    """
                    if SentenceTransformer is None:
                        return False
                    try:
                        import os

                        if self.local_model_path and os.path.exists(
                            self.local_model_path
                        ):
                            try:
                                # SentenceTransformer accepts a local folder path
                                self.model = SentenceTransformer(self.local_model_path)
                                return True
                            except Exception:
                                self.model = None
                                return False

                        # Do not attempt remote downloads in offline mode; return False
                        return False
                    except Exception:
                        self.model = None
                        return False

                def encode_query(self, query: str):
                    if not self.model:
                        return None
                    return self.model.encode(query).tolist()

                async def retrieve(self, query: str, filters=None, top_k: int = 10):
                    # For local engine, encode and then delegate to vector_store.retrieve
                    try:
                        vec = self.encode_query(query)
                        if vec is None or self.vector_store is None:
                            return []
                        # delegate to FAISS wrapper
                        results = self.vector_store.retrieve(
                            vector=vec, filters=filters, top_k=top_k
                        )
                        return results
                    except Exception:
                        return []

            # 实例化本地组件
            vector_store = FAISSWrapper(dim=384)
            # try to load existing index from disk to persist across restarts
            import os

            idx_path = os.path.join("./data", "faiss.index")
            if os.path.exists(idx_path):
                _ = vector_store.load_index(idx_path)
            else:
                # attempt initialize; if fails, HybridRAGEngine will fallback to in-memory store
                try:
                    _ = vector_store.initialize()
                except Exception:
                    _ = False

            # instantiate semantic engine and attach vector_store immediately so the
            # engine can perform fallback behaviors even before a heavyweight model
            # finishes loading in the background.
            import os as _os

            semantic_engine = LocalSemanticEngine(
                local_model_path=_os.environ.get(
                    "LOCAL_ST_MODEL_PATH", "./models/all-MiniLM-L6-v2"
                )
            )
            # In offline/local mode we do NOT attempt background model downloads or
            # initialization. The LocalSemanticEngine will only be initialized if a
            # local model path is present and a manual initialization is requested.
            # This avoids startup blocking in environments without Internet access.
            # (No-op here)
            pass

            # attach vector_store so semantic_engine.retrieve can call into it (even if
            # semantic model not yet loaded)
            try:
                semantic_engine.vector_store = vector_store
            except Exception:
                pass

            # 注入本地 DynamicKnowledgeGraph（带持久化配置）
            try:
                from core.dynamic_knowledge_graph import DynamicKnowledgeGraph

                kg = DynamicKnowledgeGraph(config={"storage_path": "./data"})
                await kg.initialize()
            except Exception:
                kg = None

            # Always provide vector_store and semantic_engine instances to the
            # RAG engine; HybridRAGEngine will perform its own validation and
            # potentially enable in-memory fallbacks.
            dependencies = {
                "file_parser": await get_file_parser(),
                "knowledge_graph": kg,
                "ingestion_pipeline": None,
                "vector_store": vector_store,
                "semantic_engine": semantic_engine,
                "config": {},
            }

            await _rag_engine.initialize(dependencies)

            # Ensure the ingestion pipeline (created elsewhere) is wired to the
            # engine's semantic engine and vector store so that background
            # ingestion writes embeddings into the same store the engine uses.
            try:
                try:
                    ingestion_pipeline_instance = await get_ingestion_pipeline()
                except Exception:
                    ingestion_pipeline_instance = None

                if ingestion_pipeline_instance is not None:
                    # set attributes directly to avoid reinitialization
                    try:
                        setattr(
                            ingestion_pipeline_instance,
                            "semantic_engine",
                            getattr(_rag_engine, "semantic_engine", None),
                        )
                        setattr(
                            ingestion_pipeline_instance,
                            "vector_store",
                            getattr(_rag_engine, "vector_store", None),
                        )
                        # also keep reference on the engine
                        _rag_engine.ingestion_pipeline = ingestion_pipeline_instance
                        logger.info(
                            "Wired ingestion pipeline with engine semantic_engine and vector_store"
                        )
                    except Exception as _e:
                        logger.warning(
                            f"Failed to attach core services to ingestion pipeline: {_e}"
                        )
            except Exception:
                # Non-fatal wiring failure; continue without blocking initialization
                logger.warning(
                    "Unable to wire ingestion pipeline to engine (non-fatal)"
                )
            # 底层诊断日志：记录运行时类来源和方法列表，帮助定位方法缺失问题
            try:
                logger.info(
                    f"RAG engine class: {_rag_engine.__class__}, module: {_rag_engine.__class__.__module__}"
                )
                logger.info(
                    f"RAG engine dir: {sorted([n for n in dir(_rag_engine) if not n.startswith('__')])}"
                )
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Failed to initialize RAG engine: {str(e)}")
            raise HTTPException(status_code=503, detail="RAG engine not initialized")
    return _rag_engine


async def get_file_parser() -> UniversalFileParser:
    """获取文件解析器实例"""
    global _file_parser
    if _file_parser is None:
        try:
            _file_parser = UniversalFileParser()
            # UniversalFileParser.initialize may be sync or async; handle both
            init = getattr(_file_parser, "initialize", None)
            if callable(init):
                import inspect

                if inspect.iscoroutinefunction(init):
                    await init()
                else:
                    init()
            else:
                logger.warning("UniversalFileParser has no initialize() method")
        except Exception as e:
            logger.error(f"Failed to initialize file parser: {str(e)}")
            raise HTTPException(status_code=503, detail="File parser not initialized")
    return _file_parser


async def get_ingestion_pipeline() -> SmartIngestionPipeline:
    """获取注入管道实例"""
    global _ingestion_pipeline
    if _ingestion_pipeline is None:
        try:
            # Prefer the registered pipeline implementation which provides process_document
            try:
                from pipelines.smart_ingestion_pipeline import (
                    RegisteredSmartIngestionPipeline,
                )

                _ingestion_pipeline = RegisteredSmartIngestionPipeline()
            except Exception:
                # fallback to base class if registered subclass is not importable
                _ingestion_pipeline = SmartIngestionPipeline()

            # initialize may be sync or async
            init = getattr(_ingestion_pipeline, "initialize", None)
            if callable(init):
                import inspect

                if inspect.iscoroutinefunction(init):
                    await init()
                else:
                    init()
            else:
                logger.warning("Ingestion pipeline has no initialize() method")
        except Exception as e:
            logger.error(f"Failed to initialize ingestion pipeline: {str(e)}")
            raise HTTPException(
                status_code=503, detail="Ingestion pipeline not initialized"
            )
    return _ingestion_pipeline


# API路由
@router.post("/search", response_model=SearchResponse)
async def semantic_search(
    query: SearchQuery, rag_engine: HybridRAGEngine = Depends(get_rag_engine)
):
    """
    语义搜索

    Args:
        query: 搜索查询
        rag_engine: RAG引擎

    Returns:
        SearchResponse: 搜索结果
    """
    try:
        start_time = datetime.now()

        # 执行搜索 - 兼容不同引擎实现
        if hasattr(rag_engine, "search") and callable(getattr(rag_engine, "search")):
            results = await rag_engine.search(
                query=query.query,
                top_k=query.top_k,
                threshold=query.threshold,
                filters=query.filters,
                include_metadata=query.include_metadata,
            )
        elif hasattr(rag_engine, "hybrid_retrieve") and callable(
            getattr(rag_engine, "hybrid_retrieve")
        ):
            # hybrid_retrieve 返回 RetrievalResult 对象列表；将其转换为 API 返回格式
            raw = await rag_engine.hybrid_retrieve(query=query.query)
            results = []
            for r in raw[: query.top_k]:
                # 支持 dataclass 或 dict 风格
                try:
                    doc_id = getattr(r, "document_id", None) or r.get("document_id")
                    content = getattr(r, "content", None) or r.get("content", "")
                    score = getattr(r, "similarity_score", None) or r.get("score", 0.0)
                    metadata = getattr(r, "metadata", None) or r.get("metadata", {})
                    source = getattr(r, "source", None) or r.get("source", "")
                except Exception:
                    # 最后回退：把对象转为字符串记录
                    doc_id = str(getattr(r, "document_id", ""))
                    content = str(getattr(r, "content", ""))
                    score = float(getattr(r, "similarity_score", 0.0) or 0.0)
                    metadata = {}
                    source = ""

                results.append(
                    {
                        "document_id": doc_id,
                        "content": content,
                        "score": float(score),
                        "metadata": metadata if query.include_metadata else {},
                        "source": source,
                    }
                )
        else:
            raise Exception("RAG engine does not provide search or hybrid_retrieve")

        query_time = (datetime.now() - start_time).total_seconds()
        query_id = str(uuid.uuid4())

        logger.info(
            f"Semantic search completed: query='{query.query}', results={len(results)}, time={query_time:.3f}s"
        )

        return SearchResponse(
            results=results,
            total_count=len(results),
            query_time=query_time,
            query_id=query_id,
        )

    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/ingest/documents", response_model=IngestionResponse)
async def ingest_documents(
    request: IngestionRequest,
    background_tasks: BackgroundTasks,
    ingestion_pipeline: SmartIngestionPipeline = Depends(get_ingestion_pipeline),
):
    """
    批量注入文档

    Args:
        request: 注入请求
        background_tasks: 后台任务
        ingestion_pipeline: 注入管道

    Returns:
        IngestionResponse: 注入响应
    """
    try:
        ingestion_id = str(uuid.uuid4())

        # 在后台执行文档注入
        background_tasks.add_task(
            process_documents_ingestion,
            request.documents,
            request.preprocess,
            request.verify_truth,
            request.group_semantically,
            ingestion_pipeline,
            ingestion_id,
        )

        logger.info(
            f"Document ingestion started: ingestion_id={ingestion_id}, document_count={len(request.documents)}"
        )

        return IngestionResponse(
            success=True,
            processed_count=0,  # 异步处理，初始为0
            failed_count=0,
            failed_documents=[],
            ingestion_id=ingestion_id,
        )

    except Exception as e:
        logger.error(f"Document ingestion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


async def process_documents_ingestion(
    documents: List[Dict[str, Any]],
    preprocess: bool,
    verify_truth: bool,
    group_semantically: bool,
    ingestion_pipeline: SmartIngestionPipeline,
    ingestion_id: str,
):
    """处理文档注入的后台任务"""
    try:
        processed_count = 0
        failed_count = 0
        failed_documents = []

        for doc in documents:
            try:
                # 执行文档注入
                await ingestion_pipeline.process_document(
                    document=doc,
                    preprocess=preprocess,
                    verify_truth=verify_truth,
                    group_semantically=group_semantically,
                )
                processed_count += 1

            except Exception as e:
                failed_count += 1
                failed_documents.append(
                    {"document": doc.get("id", "unknown"), "error": str(e)}
                )
                logger.warning(f"Failed to process document {doc.get('id')}: {str(e)}")

        logger.info(
            f"Document ingestion completed: ingestion_id={ingestion_id}, "
            f"processed={processed_count}, failed={failed_count}"
        )

    except Exception as e:
        logger.error(f"Background ingestion task failed: {str(e)}")


@router.post("/group/semantic", response_model=GroupingResponse)
async def semantic_grouping(
    request: GroupingRequest, rag_engine: HybridRAGEngine = Depends(get_rag_engine)
):
    """
    语义分组

    Args:
        request: 分组请求
        rag_engine: RAG引擎

    Returns:
        GroupingResponse: 分组响应
    """
    try:
        # 执行语义分组
        groups = await rag_engine.semantic_grouping(
            documents=request.documents,
            strategy=request.grouping_strategy,
            max_groups=request.max_groups,
        )

        logger.info(
            f"Semantic grouping completed: documents={len(request.documents)}, groups={len(groups)}"
        )

        return GroupingResponse(
            groups=groups,
            total_groups=len(groups),
            grouping_strategy=request.grouping_strategy,
        )

    except Exception as e:
        logger.error(f"Semantic grouping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Grouping failed: {str(e)}")


@router.get("/chunks/{document_id}")
async def get_document_chunks(
    document_id: str, rag_engine: HybridRAGEngine = Depends(get_rag_engine)
):
    """
    获取文档分块

    Args:
        document_id: 文档ID
        rag_engine: RAG引擎

    Returns:
        List[DocumentChunk]: 文档分块列表
    """
    try:
        chunks = await rag_engine.get_document_chunks(document_id)

        return [
            DocumentChunk(
                content=chunk["content"],
                metadata=chunk["metadata"],
                chunk_id=chunk["chunk_id"],
                document_id=chunk["document_id"],
            )
            for chunk in chunks
        ]

    except Exception as e:
        logger.error(f"Failed to get document chunks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get chunks: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str, rag_engine: HybridRAGEngine = Depends(get_rag_engine)
):
    """
    删除文档

    Args:
        document_id: 文档ID
        rag_engine: RAG引擎

    Returns:
        Dict: 删除结果
    """
    try:
        success = await rag_engine.delete_document(document_id)

        if success:
            logger.info(f"Document deleted: {document_id}")
            return {"success": True, "message": f"Document {document_id} deleted"}
        else:
            raise HTTPException(
                status_code=404, detail=f"Document {document_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/stats")
async def get_rag_stats(rag_engine: HybridRAGEngine = Depends(get_rag_engine)):
    """
    获取RAG系统统计信息

    Args:
        rag_engine: RAG引擎

    Returns:
        Dict: 统计信息
    """
    try:
        stats = await rag_engine.get_system_stats()
        return stats

    except Exception as e:
        logger.error(f"Failed to get RAG stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.post("/clear-cache")
async def clear_cache(rag_engine: HybridRAGEngine = Depends(get_rag_engine)):
    """
    清除缓存

    Args:
        rag_engine: RAG引擎

    Returns:
        Dict: 清除结果
    """
    try:
        await rag_engine.clear_cache()
        logger.info("RAG cache cleared")
        return {"success": True, "message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cache clearance failed: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查端点"""
    try:
        rag_engine = await get_rag_engine()
        file_parser = await get_file_parser()
        # Provide more detailed readiness info for observability
        semantic_engine_ready = False
        semantic_engine_loading = False
        vector_store_ready = False
        try:
            # rag_engine may expose semantic_engine and vector_store attributes
            if rag_engine is not None:
                se = getattr(rag_engine, "semantic_engine", None)
                vs = getattr(rag_engine, "vector_store", None)
                # If semantic engine has a loaded model attribute, consider it ready
                if se is not None:
                    semantic_engine_loading = getattr(se, "model", None) is None
                    semantic_engine_ready = getattr(se, "model", None) is not None
                vector_store_ready = vs is not None

        except Exception:
            pass

        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "rag_engine": rag_engine is not None,
                "file_parser": file_parser is not None,
                "ingestion_pipeline": _ingestion_pipeline is not None,
            },
            "readiness": {
                "semantic_engine_ready": semantic_engine_ready,
                "semantic_engine_loading": semantic_engine_loading,
                "vector_store_ready": vector_store_ready,
                "ingestion_pipeline_ready": _ingestion_pipeline is not None,
                "rag_engine_status": (
                    getattr(rag_engine, "status", None)
                    if rag_engine is not None
                    else None
                ),
            },
        }
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unhealthy")
