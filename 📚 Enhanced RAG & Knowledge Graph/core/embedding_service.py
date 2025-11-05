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
                                        break
                        except Exception:
                            pass
                    if "HF_ENDPOINT" not in os.environ:
                        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

            self.model = SentenceTransformer(override_model or model_name, device="cpu")
            self.dim = int(
                getattr(self.model, "get_sentence_embedding_dimension", lambda: 384)()
            )
            self.backend = "sentence-transformers"
        except Exception as e:
            # 记录错误，但继续使用stub模式
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"模型下载失败，使用stub模式: {e}")
            logger.info("提示：运行 'bash scripts/setup_china_mirrors.sh' 配置国内镜像，然后使用 'bash scripts/download_model.sh' 下载模型")
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
