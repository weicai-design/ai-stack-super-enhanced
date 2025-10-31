#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable

from sentence_transformers import SentenceTransformer, models
from transformers import AutoConfig

ROOT = Path(__file__).resolve().parents[1]
SRC_CANDIDATES = [
    ROOT / "offline_bundle" / "models" / "all-MiniLM-L6-v2",
    ROOT / "models" / "all-MiniLM-L6-v2",
]


def find_src() -> Path:
    for c in SRC_CANDIDATES:
        if (c / "config.json").exists() and (
            list(c.glob("*.safetensors")) or (c / "pytorch_model.bin").exists()
        ):
            return c
    raise SystemExit(
        "未找到本地HF权重，请确认 offline_bundle/models/all-MiniLM-L6-v2 含 config.json + 权重"
    )


def copy_selected(src: Path, dst: Path, include: Iterable[str]) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for pat in include:
        for p in src.glob(pat):
            if p.is_file():
                shutil.copy2(p, dst / p.name)


def main():
    src = find_src()
    cfg = AutoConfig.from_pretrained(str(src), local_files_only=True)
    dim = int(getattr(cfg, "hidden_size", 384))
    print("source_dir =", src, "hidden_size =", dim)

    # 用本地HF权重构建 ST 并保存
    t = models.Transformer(str(src))  # 纯本地
    p = models.Pooling(word_embedding_dimension=dim, pooling_mode_mean_tokens=True)
    st = SentenceTransformer(modules=[t, p])

    dst = ROOT / "models" / "all-MiniLM-L6-v2"
    if dst.exists():
        shutil.rmtree(dst)
    st.save(str(dst))

    # 若 0_Transformer 未创建，手动补齐（从HF权重挑必要文件拷入）
    zt = dst / "0_Transformer"
    if not zt.exists():
        copy_selected(
            src,
            zt,
            include=[
                "config.json",
                "model.safetensors",
                "pytorch_model.bin",
                "tokenizer.json",
                "tokenizer_config.json",
                "special_tokens_map.json",
                "vocab.txt",
                "vocab.json",
                "merges.txt",
                "*.model",  # sentencepiece
            ],
        )

    ok = (
        zt.exists() and (dst / "1_Pooling").exists() and (dst / "modules.json").exists()
    )
    print("saved_to =", dst, "ok_structure =", ok)
    if not ok:
        raise SystemExit("重建后结构仍不完整，请贴出: ls -l models/all-MiniLM-L6-v2")

    # 自检：可加载并输出维度
    m = SentenceTransformer(str(dst), device="cpu")
    v = m.encode(["ok"])[0]
    print("selftest_dim =", len(v))


if __name__ == "__main__":
    main()
