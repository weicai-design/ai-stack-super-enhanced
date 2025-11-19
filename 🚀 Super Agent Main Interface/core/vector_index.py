"""
轻量向量索引

提供：
- 增量向量写入（自动单位化）
- 余弦相似度检索
- 查询缓存（Top-K）
"""
from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Optional, Tuple

import numpy as np


class FastVectorIndex:
    def __init__(self, dim: int = 384, cache_size: int = 64):
        self.dim = dim
        self.cache_size = cache_size
        self._vectors = np.zeros((0, dim), dtype="float32")
        self._ids: List[str] = []
        self._doc_store: Dict[str, Dict] = {}
        self._cache: "OrderedDict[Tuple, List[Dict]]" = OrderedDict()

    def add_documents(
        self,
        vectors: List[List[float]],
        ids: List[str],
        metadatas: Optional[List[Dict]] = None,
    ):
        if not vectors:
            return
        arr = np.array(vectors, dtype="float32")
        if arr.ndim == 1:
            arr = arr.reshape(1, -1)
        if arr.shape[1] != self.dim:
            raise ValueError(f"向量维度不匹配，期望 {self.dim}，得到 {arr.shape[1]}")

        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0] = 1e-12
        arr = arr / norms

        if self._vectors.size == 0:
            self._vectors = arr
        else:
            self._vectors = np.vstack([self._vectors, arr])

        self._ids.extend(ids)
        if metadatas:
            for idx, doc_id in enumerate(ids):
                self._doc_store[doc_id] = metadatas[idx] if idx < len(metadatas) else {}

        self._cache.clear()

    def retrieve(
        self,
        query: str = None,
        vector: Optional[List[float]] = None,
        filters: Optional[Dict] = None,
        top_k: int = 10,
    ):
        if vector is None or self._vectors.size == 0:
            return []
        q = np.array(vector, dtype="float32")
        if q.ndim == 1:
            q = q.reshape(1, -1)
        if q.shape[1] != self.dim:
            raise ValueError(f"查询向量维度不匹配，期望 {self.dim}，得到 {q.shape[1]}")
        q_norm = np.linalg.norm(q, axis=1, keepdims=True)
        q_norm[q_norm == 0] = 1e-12
        q = q / q_norm

        cache_key = tuple(np.round(q[0][:32], 4))
        if cache_key in self._cache:
            results = self._cache[cache_key]
            self._cache.move_to_end(cache_key)
            return results[:top_k]

        sims = np.dot(self._vectors, q[0])
        idxs = sims.argsort()[::-1][:top_k]
        results = []
        for idx in idxs:
            doc_id = self._ids[idx] if idx < len(self._ids) else str(idx)
            payload = self._doc_store.get(doc_id, {})
            results.append(
                {
                    "document_id": doc_id,
                    "score": float(sims[idx]),
                    "metadata": payload,
                    "source": payload.get("source", "fast_vector_index"),
                }
            )

        self._cache[cache_key] = results
        if len(self._cache) > self.cache_size:
            self._cache.popitem(last=False)
        return results


__all__ = ["FastVectorIndex"]

