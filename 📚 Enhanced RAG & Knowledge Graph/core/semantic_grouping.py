from __future__ import annotations

from typing import Any, Dict, List

import numpy as np


class SemanticGrouper:
    def __init__(self, embed_fn):
        self.embed_fn = embed_fn

    def cluster(self, texts: List[str], k: int = 8) -> Dict[str, Any]:
        if not texts:
            return {"k": k, "groups": []}
        X = np.array([self.embed_fn(t or "") for t in texts], dtype=float)
        n = len(texts)
        if n <= k or X.size == 0:
            return {
                "k": min(k, n),
                "groups": [{"id": i, "items": [i]} for i in range(n)],
            }

        try:
            from sklearn.cluster import KMeans  # type: ignore

            km = KMeans(n_clusters=k, n_init=5, random_state=42)
            labels = km.fit_predict(X)
        except Exception:
            # 回退：hash 分桶
            labels = np.array([hash(t) % max(1, k) for t in texts])
        groups: Dict[int, List[int]] = {}
        for i, lb in enumerate(labels):
            groups.setdefault(int(lb), []).append(i)
        return {
            "k": k,
            "groups": [{"id": gid, "items": items} for gid, items in groups.items()],
        }
