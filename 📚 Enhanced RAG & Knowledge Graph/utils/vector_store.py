from __future__ import annotations

import json
from typing import List, Optional, Tuple

try:
    import numpy as np
except Exception:
    np = None


class HybridVectorStore:
    """
    轻量向量库：
    - 优先用 numpy 做内存向量检索（内积相似度）
    - 无 numpy 时用纯 Python 退化实现
    - 提供 add_documents / search / save / load
    """

    def __init__(self, dim: Optional[int] = None):
        self.dim = dim
        self._ids: List[str] = []
        self._vecs: List[List[float]] = []

    def add_documents(self, vectors: List[List[float]], ids: List[str]) -> None:
        if len(vectors) != len(ids):
            raise ValueError("vectors 和 ids 长度不一致")
        if self.dim is None and vectors:
            self.dim = len(vectors[0])
        for v in vectors:
            if self.dim is not None and len(v) != self.dim:
                raise ValueError("向量维度不一致")
        self._ids.extend(ids)
        self._vecs.extend(vectors)

    def _scores_py(self, q: List[float]) -> List[float]:
        # 纯 Python 内积
        scores: List[float] = []
        for v in self._vecs:
            s = sum(a * b for a, b in zip(q, v))
            scores.append(s)
        return scores

    def search(self, query_vec: List[float], top_k: int = 5) -> List[Tuple[str, float]]:
        if not self._ids:
            return []
        if np is not None:
            Q = np.array(query_vec, dtype="float32")
            M = np.array(self._vecs, dtype="float32")
            scores = (M @ Q).tolist()
        else:
            scores = self._scores_py(query_vec)
        top = sorted(zip(self._ids, scores), key=lambda x: x[1], reverse=True)[:top_k]
        return top

    def save(self, path: str) -> None:
        data = {"dim": self.dim, "ids": self._ids, "vecs": self._vecs}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, path: str) -> "HybridVectorStore":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        inst = cls(dim=data.get("dim"))
        inst._ids = list(data.get("ids") or [])
        inst._vecs = list(data.get("vecs") or [])
        return inst

    def remove_prefix(self, prefix: str) -> int:
        """删除所有以 prefix 开头的 ids，返回删除数量"""
        keep_vecs, keep_ids = [], []
        removed = 0
        for v, _id in zip(self._vecs, self._ids):
            if not _id.startswith(prefix):
                keep_vecs.append(v)
                keep_ids.append(_id)
            else:
                removed += 1
        self._vecs, self._ids = keep_vecs, keep_ids
        return removed

    def remove_contains(self, substring: str) -> int:
        """删除所有包含指定子串的 ids，返回删除数量"""
        keep_vecs, keep_ids = [], []
        removed = 0
        for v, _id in zip(self._vecs, self._ids):
            if substring not in _id:
                keep_vecs.append(v)
                keep_ids.append(_id)
            else:
                removed += 1
        self._vecs, self._ids = keep_vecs, keep_ids
        return removed

    def list_ids(self) -> List[str]:
        return list(self._ids)

    def clear(self) -> int:
        """清空所有向量与ID，返回清空数量"""
        n = len(self._ids)
        self._ids = []
        self._vecs = []
        self.dim = None
        return n

    # 便捷：返回当前条目数量与维度
    @property
    def size(self) -> int:
        return len(self._ids)

    @property
    def dimension(self) -> int:
        return int(self.dim or 0)
