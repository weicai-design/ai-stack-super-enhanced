from __future__ import annotations

import html
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_WORD_RE = re.compile(r"[A-Za-z0-9_]+", re.UNICODE)


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in _WORD_RE.findall(text or "")]


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    s = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    c = s / (na * nb)
    return float(0.0 if c < 0 else (1.0 if c > 1 else c))


def _is_valid_st_dir(p: Path) -> bool:
    if not p.exists() or not p.is_dir():
        return False
    if (p / "modules.json").exists():
        return True
    if (p / "config.json").exists() and (
        (p / "pytorch_model.bin").exists() or any(p.glob("*.safetensors"))
    ):
        return True
    if (p / "0_Transformer").exists() or (p / "1_Pooling").exists():
        return True
    return False


_ST = None  # 延迟加载的 SentenceTransformer
_ST_ERR: Optional[str] = None  # 记录最近一次加载错误


def _load_st_model() -> Optional[Any]:
    global _ST
    global _ST_ERR
    if _ST is not None:
        return _ST
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception as e:
        _ST = None
        _ST_ERR = f"import_error: {e}"
        return _ST
    override = os.getenv("EMBEDDING_MODEL_NAME") or os.getenv("LOCAL_ST_MODEL_PATH")
    candidates: List[Path] = []
    if override:
        candidates.append(Path(override))
    candidates.append(Path.cwd() / "models" / "all-MiniLM-L6-v2")
    last_err: Optional[Exception] = None
    for c in candidates:
        if _is_valid_st_dir(c):
            try:
                _ST = SentenceTransformer(str(c), device="cpu")
                _ST_ERR = None
                return _ST
            except Exception as e:
                last_err = e
                continue
    _ST = None
    _ST_ERR = f"not_loaded: {last_err}" if last_err else "model_not_found"
    return _ST


def st_available() -> bool:
    return _load_st_model() is not None


def st_status() -> Dict[str, Any]:
    """返回模型加载诊断信息"""
    return {
        "available": st_available(),
        "error": _ST_ERR,
        "env_path": os.getenv("LOCAL_ST_MODEL_PATH")
        or os.getenv("EMBEDDING_MODEL_NAME"),
    }


def _embed_many(texts: List[str]) -> Optional[List[List[float]]]:
    st = _load_st_model()
    if st is None:
        return None
    try:
        vecs = st.encode(texts, normalize_embeddings=True, convert_to_numpy=False)
        return [list(map(float, v)) for v in vecs]
    except Exception:
        return None


def _read_doc(doc_meta: Dict[str, Any], max_chars: int = 4000) -> Tuple[str, str]:
    doc_id = str(doc_meta.get("id") or "")
    text = ""
    if isinstance(doc_meta.get("text"), str) and doc_meta["text"].strip():
        text = doc_meta["text"]
    else:
        p = doc_meta.get("path")
        if isinstance(p, str) and p:
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(max_chars + 1024)
            except Exception:
                text = ""
    if len(text) > max_chars:
        text = text[:max_chars]
    return doc_id, text


def _bm25_scores(
    docs_tokens: List[List[str]], q_tokens: List[str], k1: float = 1.5, b: float = 0.75
) -> List[float]:
    if not docs_tokens or not q_tokens:
        return [0.0] * len(docs_tokens)
    N = len(docs_tokens)
    q_vocab = list(dict.fromkeys([t for t in q_tokens if t]))
    df = {t: 0 for t in q_vocab}
    doc_len = [len(dt) for dt in docs_tokens]
    avgdl = sum(doc_len) / max(1, N)
    for dt in docs_tokens:
        present = set(dt)
        for t in q_vocab:
            if t in present:
                df[t] += 1
    idf = {t: math.log((N - df[t] + 0.5) / (df[t] + 0.5) + 1.0) for t in q_vocab}
    scores: List[float] = []
    for i, dt in enumerate(docs_tokens):
        tf: Dict[str, int] = {}
        for t in dt:
            if t in idf:
                tf[t] = tf.get(t, 0) + 1
        s = 0.0
        denom_len = (1 - b) + b * (doc_len[i] / max(1e-9, avgdl))
        for t in q_vocab:
            f = tf.get(t, 0)
            if f == 0:
                continue
            s += idf[t] * ((f * (k1 + 1)) / (f + k1 * denom_len))
        scores.append(float(max(0.0, s)))
    mx = max(scores) if scores else 0.0
    return [s / mx if mx > 0 else 0.0 for s in scores]


def _find_offsets(
    text: str, q_tokens: List[str], max_hits: int = 16
) -> List[Dict[str, int | str]]:
    hits: List[Dict[str, int | str]] = []
    if not text or not q_tokens:
        return hits
    lowered = text.lower()
    toks = [t for t in dict.fromkeys(q_tokens) if t]
    for t in toks:
        start = 0
        tl = t.lower()
        while True:
            i = lowered.find(tl, start)
            if i == -1:
                break
            hits.append({"term": t, "start": i, "end": i + len(t)})
            if len(hits) >= max_hits:
                return hits
            start = i + len(tl)
    hits.sort(key=lambda h: int(h["start"]))
    return hits


def _best_window(
    text: str, hits: List[Dict[str, int | str]], win: int = 160
) -> Tuple[int, str, str]:
    if not text:
        return 0, "", ""
    if not hits:
        raw = text[:win]
        return 0, raw, html.escape(raw)
    best_s, best_cnt = 0, -1
    for h in hits:
        s = max(0, int(h["start"]) - win // 4)
        e = s + win
        cnt = sum(1 for hh in hits if s <= int(hh["start"]) < e)
        if cnt > best_cnt:
            best_cnt, best_s = cnt, s
    s = best_s
    e = min(len(text), s + win)
    raw = text[s:e]
    esc = html.escape(raw)
    for t in sorted({str(h["term"]) for h in hits}, key=len, reverse=True):
        esc = re.compile(r"(" + re.escape(t) + r")", re.IGNORECASE).sub(
            lambda m: f"<em>{html.escape(m.group(0))}</em>", esc
        )
    return s, raw, esc


def hybrid_search(
    query: str,
    kg: Any,
    top_k: int = 5,
    alpha: float = 0.5,
    max_docs: int = 2000,
    max_chars: int = 4000,
    offset: int = 0,
    use_faiss: bool = True,
    return_highlight: bool = True,
) -> Dict[str, Any]:
    q = (query or "").strip()
    if not q:
        return {
            "query": query,
            "mode": "hybrid",
            "items": [],
            "total": 0,
            "offset": offset,
            "top_k": top_k,
        }

    docs_meta = getattr(kg, "docs", {}) or {}
    docs: List[Dict[str, Any]] = []
    for i, (doc_id, meta) in enumerate(docs_meta.items()):
        if i >= max_docs:
            break
        m = {"id": doc_id, **(meta or {})}
        did, text = _read_doc(m, max_chars=max_chars)
        if not text.strip():
            continue
        docs.append({"id": did or doc_id, "path": m.get("path"), "text": text})
    N = len(docs)
    if N == 0:
        return {
            "query": query,
            "mode": "hybrid",
            "items": [],
            "total": 0,
            "offset": offset,
            "top_k": top_k,
        }

    q_tokens = _tokenize(q)
    docs_tokens = [_tokenize(d["text"]) for d in docs]
    kw_scores = _bm25_scores(docs_tokens, q_tokens)

    vec_scores = [0.0] * N
    embeddings = _embed_many([q] + [d["text"] for d in docs])
    if embeddings:
        qv = embeddings[0]
        doc_vecs = embeddings[1:]
        try:
            import faiss  # type: ignore
            import numpy as np  # type: ignore

            dim = len(qv)
            index = faiss.IndexFlatIP(dim)
            mat = np.asarray(doc_vecs, dtype="float32")
            index.add(mat)
            pre_k = min(N, max(offset + top_k, 200))
            D, I = index.search(np.asarray([qv], dtype="float32"), pre_k)
            idx2score = {
                int(idx): float(max(0.0, score))
                for idx, score in zip(I[0].tolist(), D[0].tolist())
                if int(idx) >= 0
            }
            for i, sc in idx2score.items():
                if 0 <= i < N:
                    vec_scores[i] = sc
        except Exception:
            for i, dv in enumerate(doc_vecs):
                vec_scores[i] = _cosine(qv, dv)

    items = []
    for i, d in enumerate(docs):
        kw = kw_scores[i]
        vec = vec_scores[i]
        score = alpha * kw + (1.0 - alpha) * vec
        hits = _find_offsets(d["text"], q_tokens, max_hits=16)
        win_start, preview_raw, preview_h = _best_window(d["text"], hits, win=160)
        item: Dict[str, Any] = {
            "doc_id": d["id"],
            "path": d.get("path"),
            "score": round(score, 6),
            "keyword_score": round(kw, 6),
            "vector_score": round(vec, 6),
            "preview": preview_raw.replace("\n", " "),
            "preview_start": int(win_start),
            "matches": hits,
        }
        if return_highlight:
            item["preview_highlighted"] = preview_h.replace("\n", " ")
        items.append(item)

    items.sort(key=lambda x: x["score"], reverse=True)
    total = len(items)
    start = max(0, int(offset))
    end = min(total, start + max(1, int(top_k)))
    return {
        "query": query,
        "mode": "hybrid",
        "alpha": alpha,
        "total": total,
        "offset": start,
        "top_k": end - start,
        "items": items[start:end],
    }
