"""
Optimized FAISS Vector Store
优化的FAISS向量存储

性能优化：
1. 使用HNSW索引替代Flat索引（大规模数据更快）
2. 添加缓存机制
3. 支持并行检索
4. 批量操作优化
"""

from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    """L2归一化向量"""
    if x.ndim == 1:
        n = np.linalg.norm(x) or 1.0
        return (x / n).astype("float32")
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (x / n).astype("float32")


class OptimizedFaissVectorStore:
    """
    优化的FAISS向量存储
    
    特性：
    1. 自动选择最优索引类型（HNSW vs Flat）
    2. 查询结果缓存
    3. 批量操作优化
    4. 线程安全
    """

    def __init__(
        self,
        dim: int | None = None,
        use_hnsw: bool = True,
        hnsw_m: int = 32,
        hnsw_ef_construction: int = 200,
        hnsw_ef_search: int = 128,
        enable_cache: bool = True,
        cache_size: int = 1000,
    ):
        """
        初始化优化的FAISS向量存储
        
        Args:
            dim: 向量维度
            use_hnsw: 是否使用HNSW索引（大规模数据推荐）
            hnsw_m: HNSW参数M（连接数）
            hnsw_ef_construction: HNSW构建参数
            hnsw_ef_search: HNSW搜索参数
            enable_cache: 是否启用缓存
            cache_size: 缓存大小
        """
        if not FAISS_AVAILABLE:
            raise RuntimeError("faiss_not_available")
        
        self.dim: int | None = dim
        self.use_hnsw = use_hnsw
        self.hnsw_m = hnsw_m
        self.hnsw_ef_construction = hnsw_ef_construction
        self.hnsw_ef_search = hnsw_ef_search
        self.enable_cache = enable_cache
        
        self._ids: List[str] = []
        self._vecs: np.ndarray | None = None
        self._index = None
        self._lock = threading.Lock()
        
        # 查询缓存（LRU）
        if enable_cache:
            self._cache = {}
            self._cache_hits = 0
            self._cache_misses = 0
            self._max_cache_size = cache_size
        else:
            self._cache = None

    def _ensure_index(self):
        """确保索引已创建"""
        if self._index is None:
            if not self.dim:
                raise ValueError("dimension_not_set")
            
            with self._lock:
                if self._index is None:
                    # 根据数据规模选择索引类型
                    if self.use_hnsw and len(self._ids) > 1000:
                        # 大规模数据使用HNSW
                        self._index = faiss.IndexHNSWFlat(self.dim, self.hnsw_m)
                        self._index.hnsw.efConstruction = self.hnsw_ef_construction
                        self._index.hnsw.efSearch = self.hnsw_ef_search
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"使用HNSW索引 (M={self.hnsw_m}, efConstruction={self.hnsw_ef_construction})")
                    else:
                        # 小规模数据使用Flat索引
                        self._index = faiss.IndexFlatIP(self.dim)
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"使用Flat索引（数据量: {len(self._ids)}）")

    def add_documents(self, vectors: List[List[float]], ids: List[str]) -> None:
        """批量添加文档（优化版）"""
        if not vectors:
            return
        
        X = np.asarray(vectors, dtype="float32")
        if self.dim is None:
            self.dim = int(X.shape[1])
        elif int(X.shape[1]) != int(self.dim):
            raise ValueError(f"dimension_mismatch: got {X.shape[1]} want {self.dim}")
        
        X = _l2_normalize(X)
        
        with self._lock:
            self._ensure_index()
            
            # 批量添加（更高效）
            if isinstance(self._index, faiss.IndexHNSWFlat):
                # HNSW索引需要逐个添加或使用IndexFlatL2作为量化器
                for vec in X:
                    self._index.add(vec.reshape(1, -1))
            else:
                # Flat索引可以直接批量添加
                self._index.add(X)
            
            self._ids.extend(ids)
            
            if self._vecs is None:
                self._vecs = X.copy()
            else:
                self._vecs = np.vstack([self._vecs, X])
            
            # 清空缓存（数据已变更）
            if self.enable_cache and self._cache:
                self._cache.clear()

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        use_cache: bool = True,
    ) -> List[Tuple[str, float]]:
        """
        搜索（优化版，支持缓存）
        
        Args:
            query_vector: 查询向量
            top_k: 返回Top K结果
            use_cache: 是否使用缓存
            
        Returns:
            搜索结果列表 [(id, score), ...]
        """
        if self._index is None or self._vecs is None or len(self._ids) == 0:
            return []
        
        # 检查缓存
        cache_key = None
        if self.enable_cache and use_cache and self._cache is not None:
            cache_key = (tuple(query_vector), top_k)
            if cache_key in self._cache:
                self._cache_hits += 1
                return self._cache[cache_key]
            self._cache_misses += 1
        
        q = np.asarray(query_vector, dtype="float32").reshape(1, -1)
        if q.shape[1] != int(self.dim or 0):
            return []
        
        q = _l2_normalize(q)
        
        with self._lock:
            # 设置HNSW搜索参数
            if isinstance(self._index, faiss.IndexHNSWFlat):
                self._index.hnsw.efSearch = self.hnsw_ef_search
            
            # 执行搜索
            D, I = self._index.search(q, min(top_k, len(self._ids)))
        
        hits: List[Tuple[str, float]] = []
        for idx, score in zip(I[0].tolist(), D[0].tolist()):
            if idx == -1:
                continue
            hits.append((self._ids[idx], float(score)))
        
        # 缓存结果
        if self.enable_cache and use_cache and cache_key and self._cache is not None:
            # LRU缓存：如果超过大小限制，删除最旧的
            if len(self._cache) >= self._max_cache_size:
                # 删除第一个（FIFO）
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            self._cache[cache_key] = hits
        
        return hits

    def batch_search(
        self,
        query_vectors: List[List[float]],
        top_k: int = 5,
    ) -> List[List[Tuple[str, float]]]:
        """
        批量搜索（并行优化）
        
        Args:
            query_vectors: 查询向量列表
            top_k: 每个查询返回Top K结果
            
        Returns:
            搜索结果列表的列表
        """
        if not query_vectors:
            return []
        
        Q = np.asarray(query_vectors, dtype="float32")
        if Q.shape[1] != int(self.dim or 0):
            return [[] for _ in query_vectors]
        
        Q = _l2_normalize(Q)
        
        with self._lock:
            if isinstance(self._index, faiss.IndexHNSWFlat):
                self._index.hnsw.efSearch = self.hnsw_ef_search
            
            D, I = self._index.search(Q, min(top_k, len(self._ids)))
        
        results = []
        for i in range(len(query_vectors)):
            hits = []
            for idx, score in zip(I[i].tolist(), D[i].tolist()):
                if idx == -1:
                    continue
                hits.append((self._ids[idx], float(score)))
            results.append(hits)
        
        return results

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        if not self.enable_cache:
            return {"enabled": False}
        
        total_queries = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        return {
            "enabled": True,
            "cache_size": len(self._cache) if self._cache else 0,
            "max_cache_size": self._max_cache_size,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }

    def clear_cache(self):
        """清空缓存"""
        if self._cache:
            self._cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0

    def remove_prefix(self, prefix: str) -> int:
        """删除指定前缀的文档"""
        return self._rebuild_keep(lambda _id: not _id.startswith(prefix))

    def remove_contains(self, substring: str) -> int:
        """删除包含指定子串的文档"""
        return self._rebuild_keep(lambda _id: substring not in _id)

    def _rebuild_keep(self, keep_fn) -> int:
        """重建索引（保留满足条件的文档）"""
        if self._vecs is None or self._index is None or not self._ids:
            return 0
        
        mask = np.array([keep_fn(_id) for _id in self._ids], dtype=bool)
        removed = int((~mask).sum())
        kept_vecs = self._vecs[mask]
        kept_ids = [i for i, m in zip(self._ids, mask) if m]
        
        with self._lock:
            # 重建索引
            self._index = None
            self._ids = kept_ids
            self._vecs = kept_vecs if kept_vecs.size > 0 else None
            if self._vecs is not None:
                self._ensure_index()
                if isinstance(self._index, faiss.IndexHNSWFlat):
                    for vec in self._vecs:
                        self._index.add(vec.reshape(1, -1))
                else:
                    self._index.add(self._vecs)
            
            # 清空缓存
            if self._cache:
                self._cache.clear()
        
        return removed

    def list_ids(self) -> List[str]:
        """列出所有文档ID"""
        return list(self._ids)

    def clear(self) -> int:
        """清空所有数据"""
        n = len(self._ids)
        with self._lock:
            self._ids = []
            self._vecs = None
            self._index = None
            if self._cache:
                self._cache.clear()
        return n

    def save(self, path: str) -> None:
        """保存索引到文件"""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存FAISS索引
        index_path = Path(str(p) + ".faiss")
        if self._index is not None:
            faiss.write_index(self._index, str(index_path))
        
        # 保存元数据
        data = {
            "backend": "faiss_optimized",
            "dim": int(self.dim or 0),
            "ids": self._ids,
            "use_hnsw": self.use_hnsw,
            "hnsw_m": self.hnsw_m,
            "hnsw_ef_construction": self.hnsw_ef_construction,
            "hnsw_ef_search": self.hnsw_ef_search,
        }
        
        # 只保存ID，不保存向量（向量在FAISS索引中）
        p.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: str) -> "OptimizedFaissVectorStore":
        """从文件加载索引"""
        p = Path(path)
        data = json.loads(p.read_text())
        
        dim = int(data.get("dim") or 0)
        use_hnsw = data.get("use_hnsw", True)
        hnsw_m = data.get("hnsw_m", 32)
        hnsw_ef_construction = data.get("hnsw_ef_construction", 200)
        hnsw_ef_search = data.get("hnsw_ef_search", 128)
        
        store = cls(
            dim=dim,
            use_hnsw=use_hnsw,
            hnsw_m=hnsw_m,
            hnsw_ef_construction=hnsw_ef_construction,
            hnsw_ef_search=hnsw_ef_search,
        )
        
        # 加载FAISS索引
        index_path = Path(str(p) + ".faiss")
        if index_path.exists():
            store._index = faiss.read_index(str(index_path))
            store._ids = list(data.get("ids") or [])
        
        return store

    @property
    def size(self) -> int:
        """返回文档数量"""
        return len(self._ids)

    @property
    def dimension(self) -> int:
        """返回向量维度"""
        return int(self.dim or 0)

