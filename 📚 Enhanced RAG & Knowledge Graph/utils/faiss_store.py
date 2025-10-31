from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except Exception as e:
    faiss = None  # 由调用方决定回退


def _l2_normalize(x: np.ndarray) -> np.ndarray:
    if x.ndim == 1:
        n = np.linalg.norm(x) or 1.0
        return (x / n).astype("float32")
    n = np.linalg.norm(x, axis=1, keepdims=True)
    n[n == 0] = 1.0
    return (x / n).astype("float32")


class FaissVectorStore:
    """
    使用 FAISS IndexFlatIP + L2 归一化实现余弦相似度搜索。
    支持：add/search/save/load/remove_prefix/remove_contains/list_ids/clear/size/dimension
    """

    def __init__(self, dim: int | None = None):
        if faiss is None:
            raise RuntimeError("faiss_not_available")
        self.dim: int | None = dim
        self._ids: List[str] = []
        self._vecs: np.ndarray | None = None  # 归一化后的向量
        self._index = None  # faiss.IndexFlatIP

    def _ensure_index(self):
        if self._index is None:
            if not self.dim:
                raise ValueError("dimension_not_set")
            self._index = faiss.IndexFlatIP(self.dim)

    def add_documents(self, vectors: List[List[float]], ids: List[str]) -> None:
        if not vectors:
            return
        X = np.asarray(vectors, dtype="float32")
        if self.dim is None:
            self.dim = int(X.shape[1])
        elif int(X.shape[1]) != int(self.dim):
            raise ValueError(f"dimension_mismatch: got {X.shape[1]} want {self.dim}")
        X = _l2_normalize(X)
        self._ensure_index()
        self._index.add(X)
        self._ids.extend(ids)
        if self._vecs is None:
            self._vecs = X.copy()
        else:
            self._vecs = np.vstack([self._vecs, X])

    def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[Tuple[str, float]]:
        if self._index is None or self._vecs is None or len(self._ids) == 0:
            return []
        q = np.asarray(query_vector, dtype="float32").reshape(1, -1)
        if q.shape[1] != int(self.dim or 0):
            return []
        q = _l2_normalize(q)
        D, I = self._index.search(q, min(top_k, len(self._ids)))
        hits: List[Tuple[str, float]] = []
        for idx, score in zip(I[0].tolist(), D[0].tolist()):
            if idx == -1:
                continue
            hits.append((self._ids[idx], float(score)))
        return hits

    def remove_prefix(self, prefix: str) -> int:
        return self._rebuild_keep(lambda _id: not _id.startswith(prefix))

    def remove_contains(self, substring: str) -> int:
        return self._rebuild_keep(lambda _id: substring not in _id)

    def _rebuild_keep(self, keep_fn) -> int:
        if self._vecs is None or self._index is None or not self._ids:
            return 0
        mask = np.array([keep_fn(_id) for _id in self._ids], dtype=bool)
        removed = int((~mask).sum())
        kept_vecs = self._vecs[mask]
        kept_ids = [i for i, m in zip(self._ids, mask) if m]
        # 重建索引
        self._index = faiss.IndexFlatIP(int(self.dim or kept_vecs.shape[1]))
        if len(kept_ids) > 0:
            self._index.add(kept_vecs)
            self._vecs = kept_vecs
        else:
            self._vecs = None
        self._ids = kept_ids
        return removed

    def list_ids(self) -> List[str]:
        return list(self._ids)

    def clear(self) -> int:
        n = len(self._ids)
        self._ids = []
        self._vecs = None
        self._index = None
        self.dim = None
        return n

    def save(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "backend": "faiss",
            "dim": int(self.dim or 0),
            "ids": self._ids,
            "vectors": (self._vecs.tolist() if self._vecs is not None else []),
        }
        p.write_text(json.dumps(data))

    @classmethod
    def load(cls, path: str) -> "FaissVectorStore":
        p = Path(path)
        data = json.loads(p.read_text())
        dim = int(data.get("dim") or 0)
        store = cls(dim=dim)
        ids = data.get("ids") or []
        vecs = np.asarray(data.get("vectors") or [], dtype="float32")
        if vecs.size > 0:
            store._ensure_index()
            store._index.add(vecs)
            store._vecs = vecs
            store._ids = list(ids)
        return store

    @property
    def size(self) -> int:
        return len(self._ids)

    @property
    def dimension(self) -> int:
        return int(self.dim or 0)
