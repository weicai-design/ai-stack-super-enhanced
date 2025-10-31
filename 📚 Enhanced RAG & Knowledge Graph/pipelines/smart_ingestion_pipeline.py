"""
Smart Ingestion Pipeline
智能数据注入管道

功能概述：
1. 支持多格式文件统一注入
2. 智能文件类型检测和路由
3. 自适应批处理和流量控制
4. 实时进度监控和错误恢复

版本: 1.0.0
依赖: File Processors, Core Engine
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from parsers.file_parsers import parse_file
from pipelines.multi_stage_preprocessor import MultiStagePreprocessor

from core.embedding_service import EmbeddingService

# 健壮导入向量后端
try:
    from utils.faiss_store import FaissVectorStore  # type: ignore
except Exception:
    FaissVectorStore = None  # type: ignore

try:
    from core.vector_store import HybridVectorStore  # type: ignore
except Exception:
    try:
        from utils.vector_store import HybridVectorStore  # type: ignore
    except Exception:
        HybridVectorStore = None  # type: ignore


class IngestResult:
    def __init__(self, success: bool, details: Optional[Dict] = None):
        self.success = success
        self.details = details or {}


def _ext(path: Path) -> str:
    return (path.suffix or "").lower()


def _preprocess_chunks(raw_items: List[Dict]) -> List[Dict]:
    # 二次分块并保留元数据
    from preprocessors.text_preprocessor import preprocess_text

    out: List[Dict] = []
    for it in raw_items:
        text = it.get("text") or ""
        meta = {k: v for k, v in it.items() if k != "text"}
        for ch in preprocess_text(text):
            m = dict(meta)
            m.update(ch.get("metadata") or {})
            out.append({"text": ch["text"], "metadata": m})
    return out


def _compute_doc_id(p: Path, raw_items: List[Dict]) -> str:
    """
    统一用 checksum 作为 doc_id，避免不同文件名产生重复。
    """
    checksum = None
    for it in raw_items or []:
        if isinstance(it, dict) and it.get("checksum"):
            checksum = str(it["checksum"])
            break
    if not checksum:
        try:
            h = hashlib.md5()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            checksum = h.hexdigest()
        except Exception:
            try:
                checksum = str(p.stat().st_mtime_ns)
            except Exception:
                checksum = "unknown"
    return checksum


class SmartIngestionPipeline:
    """
    稳健版 Ingestion 管道：
    - 按扩展名路由到 PDF/Office 解析器，失败则回退到纯文本读取
    - 统一预处理分块，生成向量，写入向量库，可选写入轻量KG
    - 不依赖 universal_file_parser，避免侧向依赖问题
    """

    def __init__(self, core_services: Optional[Dict[str, Any]] = None):
        core_services = core_services or {}
        self.semantic_engine = core_services.get("semantic_engine")
        self.vector_store = core_services.get("vector_store")
        self.kg_writer = core_services.get("kg_writer")

        self.index_path = Path(
            core_services.get("index_path") or (Path.cwd() / "data" / "index.json")
        )
        self.auto_save_index: bool = bool(core_services.get("auto_save_index", False))

        self.file_processor: Any = None
        self.preprocessor = MultiStagePreprocessor()
        self.embedder = core_services.get("embedder") or EmbeddingService()

        # 文本存储（便于分组/调试）
        self.doc_store_path = Path(
            core_services.get("doc_store_path") or (Path.cwd() / "data" / "docs.json")
        )
        self.doc_store: Dict[str, str] = {}
        self._load_doc_store()

        # 选择向量后端：优先 core_services 传入；否则按环境变量选择
        if self.vector_store is None:
            backend = os.getenv("VECTOR_BACKEND", "").lower()
            if backend == "faiss" and FaissVectorStore is not None:
                try:
                    self.vector_store = FaissVectorStore()
                except Exception:
                    self.vector_store = (
                        HybridVectorStore() if HybridVectorStore is not None else None
                    )
            else:
                self.vector_store = (
                    HybridVectorStore() if HybridVectorStore is not None else None
                )

    async def initialize(self) -> None:
        # 预留钩子；当前无外部依赖初始化
        await asyncio.sleep(0)
        # 如存在已保存索引，可在此选择加载（保持显式，默认不自动加载）
        # if self.index_path.is_file():
        #     self.load_index()

    # 新增：保存/加载索引
    def save_index(self) -> bool:
        try:
            if self.vector_store and hasattr(self.vector_store, "save"):
                self.index_path.parent.mkdir(parents=True, exist_ok=True)
                self.vector_store.save(str(self.index_path))
                return True
        except Exception:
            pass
        return False

    def load_index(self) -> bool:
        try:
            if not self.index_path.is_file():
                return False
            backend = None
            try:
                data = json.loads(self.index_path.read_text())
                backend = (data.get("backend") or data.get("_backend") or "").lower()
            except Exception:
                backend = None

            if backend == "faiss" and FaissVectorStore is not None:
                self.vector_store = FaissVectorStore.load(str(self.index_path))
                return True

            if HybridVectorStore is not None:
                # 兼容无 backend 字段或 hybrid
                self.vector_store = HybridVectorStore.load(str(self.index_path))
                return True

            if self.vector_store and hasattr(self.vector_store, "load"):
                self.vector_store.load(str(self.index_path))
                return True
        except Exception:
            pass
        return False

    # 新增：文本检索（需要语义引擎；否则返回空列表）
    def search(self, query: str, top_k: int = 5):
        if not (self.vector_store and hasattr(self.vector_store, "search")):
            return []
        if not (self.semantic_engine and hasattr(self.semantic_engine, "encode_query")):
            return []
        try:
            qv = self.semantic_engine.encode_query(query)
        except Exception:
            return []
        try:
            return self.vector_store.search(qv, top_k=top_k)
        except Exception:
            return []

    def _load_doc_store(self):
        try:
            if self.doc_store_path.is_file():
                self.doc_store = json.loads(
                    self.doc_store_path.read_text(encoding="utf-8")
                )
        except Exception:
            self.doc_store = {}

    def _save_doc_store(self):
        try:
            self.doc_store_path.parent.mkdir(parents=True, exist_ok=True)
            self.doc_store_path.write_text(
                json.dumps(self.doc_store, ensure_ascii=False, indent=0),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _doc_store_remove_prefix(self, prefix: str) -> int:
        keys = [k for k in self.doc_store.keys() if k.startswith(prefix)]
        for k in keys:
            self.doc_store.pop(k, None)
        return len(keys)

    async def ingest_single_file(self, path: str):
        p = Path(path)
        # 1) 解析为文本片段
        raw_items = parse_file(str(p))
        if not raw_items:
            return type(
                "Res",
                (),
                {"success": False, "details": {"reason": "empty_or_unreadable"}},
            )()

        # 2) 预处理（四阶段）
        chunks: List[Dict[str, Any]] = []
        for it in raw_items:
            out = self.preprocessor.run(
                {"text": it["text"], "meta": it.get("meta", {})}
            )
            if not out.get("quality", {}).get("ok", True):
                continue
            chunks.append(out)
        if not chunks:
            return type(
                "Res", (), {"success": False, "details": {"reason": "all_filtered"}}
            )()

        # 3) 计算统一 doc_id（checksum-only）
        def _compute_doc_id_from(chs: List[Dict[str, Any]]) -> str:
            # 取第一个片段 checksum 作为文档主id（亦可选文件全量hash）
            return str(chs[0].get("checksum") or chs[0]["meta"].get("checksum"))

        doc_id = _compute_doc_id_from(chunks)

        # 4) upsert 清理（索引与 doc_store 的历史）
        removed = 0
        try:
            if self.vector_store and hasattr(self.vector_store, "remove_prefix"):
                removed += self.vector_store.remove_prefix(f"{doc_id}#")
            if hasattr(self, "_doc_store_remove_prefix"):
                removed += self._doc_store_remove_prefix(f"{doc_id}#")
        except Exception:
            pass

        # 5) 嵌入
        texts = [c["text"] for c in chunks]
        try:
            vectors = self.embedder.encode(texts)
        except Exception:
            vectors = [
                [0.0] * int(getattr(self.embedder, "dimension", 384)) for _ in texts
            ]
        ids = [f"{doc_id}#{i}" for i in range(len(texts))]

        # 6) 入库
        try:
            if self.vector_store:
                self.vector_store.add_documents(vectors=vectors, ids=ids)
        except Exception:
            return type(
                "Res",
                (),
                {"success": False, "details": {"reason": "vector_store_failed"}},
            )()

        # 7) 保存文本快照（便于分组/调试）
        for _id, t in zip(ids, texts):
            self.doc_store[_id] = t
        self._save_doc_store()

        # 8) 可选：保存索引
        if getattr(self, "auto_save_index", False):
            try:
                self.save_index()
            except Exception:
                pass

        return type(
            "Res",
            (),
            {
                "success": True,
                "details": {
                    "doc_id": doc_id,
                    "replaced": removed,
                    "chunks": len(chunks),
                    "vectors": len(ids),
                },
            },
        )()
