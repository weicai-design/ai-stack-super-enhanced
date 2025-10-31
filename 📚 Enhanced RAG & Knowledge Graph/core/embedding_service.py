from __future__ import annotations

import os
from pathlib import Path
from typing import List


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        backend_pref = os.getenv("EMBEDDING_BACKEND", "stub").lower()
        offline = os.getenv("HF_HUB_OFFLINE", "0") == "1"
        allow_download = os.getenv("EMBEDDING_ALLOW_DOWNLOAD", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        override_model = os.getenv("EMBEDDING_MODEL_NAME")

        # 默认候选：优先环境变量；否则尝试 ./models/all-MiniLM-L6-v2
        local_candidates = []
        if override_model:
            local_candidates.append(Path(override_model))
        local_candidates.append(Path.cwd() / "models" / "all-MiniLM-L6-v2")

        self.backend = "stub"
        self.model = None
        self.dim = 384

        # 离线/禁止下载/显式 stub：仅当本地目录存在才尝试加载，否则直接 stub
        if backend_pref in {"stub", "none"} or offline or not allow_download:
            for ld in local_candidates:
                if ld.exists():
                    try:
                        from sentence_transformers import (
                            SentenceTransformer,
                        )  # type: ignore

                        self.model = SentenceTransformer(str(ld), device="cpu")
                        self.dim = int(
                            getattr(
                                self.model,
                                "get_sentence_embedding_dimension",
                                lambda: 384,
                            )()
                        )
                        self.backend = "sentence-transformers"
                        return
                    except Exception:
                        self.model = None
                        self.backend = "stub"
                        break
            return

        # 允许下载时，尝试在线加载；失败则回退 stub
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self.model = SentenceTransformer(override_model or model_name, device="cpu")
            self.dim = int(
                getattr(self.model, "get_sentence_embedding_dimension", lambda: 384)()
            )
            self.backend = "sentence-transformers"
        except Exception:
            self.model = None
            self.backend = "stub"

    def encode(self, texts: List[str]) -> List[List[float]]:
        if self.model is None:
            return [[0.0] * self.dim for _ in texts]
        vecs = self.model.encode(
            texts, batch_size=16, convert_to_numpy=False, normalize_embeddings=True
        )
        return [list(map(float, v)) for v in vecs]

    def encode_one(self, text: str) -> List[float]:
        return self.encode([text])[0]

    @property
    def dimension(self) -> int:
        return self.dim
