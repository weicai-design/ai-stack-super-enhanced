from __future__ import annotations

import json
import os
import re
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import Depends, FastAPI, File, Header, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = Path(
    os.getenv("LOCAL_ST_MODEL_PATH", ROOT.parent / "models" / "all-MiniLM-L6-v2")
)
INDEX_DIR = ROOT / "data"
INDEX_DOCS = INDEX_DIR / "docs.json"
INDEX_VECS = INDEX_DIR / "vectors.npy"
KG_FILE = INDEX_DIR / "kg.json"

app = FastAPI(title="RAG&KG API (minimal)")
# 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 可选鉴权：设置环境变量 RAG_API_KEY 后才生效
API_KEY = os.getenv("RAG_API_KEY", "").strip()


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(401, "unauthorized")
    return True


# 全局状态：最小内存向量索引
class Doc(BaseModel):
    id: str
    text: str
    path: Optional[str] = None


_docs: List[Doc] = []
_vecs: List[np.ndarray] = []

# ---- 简易 KG 内存结构与工具 ----
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL_RE = re.compile(r"https?://\S+")

_kg_nodes: Dict[str, Dict[str, Any]] = {}  # node_id -> node
_kg_edges: List[Dict[str, str]] = []  # {src, dst, type}


def _kg_node_id(ntype: str, value: str) -> str:
    return f"{ntype}:{value}"


# 全局锁
INDEX_LOCK = threading.RLock()
KG_LOCK = threading.RLock()


# 原子写辅助
def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"{path}.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _atomic_save_npy(path: Path, arr: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(f"{path}.tmp")  # 保持与目标同目录
    # 用二进制句柄写入，避免 np.save 自动追加 .npy
    with open(tmp, "wb") as f:
        np.save(f, arr)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _kg_remove_doc(doc_id: str) -> Dict[str, Any]:
    with KG_LOCK:
        dnid = _kg_node_id("doc", doc_id)
        if dnid not in _kg_nodes:
            return {"removed_edges": 0, "removed_entities": 0}
        removed_edges = []
        keep_edges = []
        for e in _kg_edges:
            if e.get("src") == dnid:
                removed_edges.append(e)
            else:
                keep_edges.append(e)
        _kg_edges[:] = keep_edges
        removed_entities = 0
        # 回退实体计数并清理为0的 email/url 节点
        for e in removed_edges:
            dst = e.get("dst")
            node = _kg_nodes.get(dst)
            if node and node.get("type") in {"email", "url"}:
                node["count"] = max(0, int(node.get("count", 0)) - 1)
                if node["count"] == 0:
                    _kg_nodes.pop(dst, None)
                    removed_entities += 1
        # 移除文档节点
        _kg_nodes.pop(dnid, None)
        return {
            "removed_edges": len(removed_edges),
            "removed_entities": removed_entities,
        }


def _kg_add(doc_id: str, text: str, src_path: Optional[str]) -> None:
    with KG_LOCK:
        dnid = _kg_node_id("doc", doc_id)
        if dnid not in _kg_nodes:
            _kg_nodes[dnid] = {
                "id": dnid,
                "type": "doc",
                "value": doc_id,
                "path": src_path,
            }
        emails = set(EMAIL_RE.findall(text or ""))
        urls = set(URL_RE.findall(text or ""))

        def _edge_exists(src: str, dst: str, et: str) -> bool:
            return any(
                e
                for e in _kg_edges
                if e.get("src") == src and e.get("dst") == dst and e.get("type") == et
            )

        for em in emails:
            nid = _kg_node_id("email", em)
            if nid not in _kg_nodes:
                _kg_nodes[nid] = {"id": nid, "type": "email", "value": em, "count": 0}
            if not _edge_exists(dnid, nid, "mentions"):
                _kg_nodes[nid]["count"] = _kg_nodes[nid].get("count", 0) + 1
                _kg_edges.append({"src": dnid, "dst": nid, "type": "mentions"})
        for u in urls:
            nid = _kg_node_id("url", u)
            if nid not in _kg_nodes:
                _kg_nodes[nid] = {"id": nid, "type": "url", "value": u, "count": 0}
            if not _edge_exists(dnid, nid, "links"):
                _kg_nodes[nid]["count"] = _kg_nodes[nid].get("count", 0) + 1
                _kg_edges.append({"src": dnid, "dst": nid, "type": "links"})


def _kg_save(out_path: Optional[Path] = None) -> Dict[str, Any]:
    with KG_LOCK:
        p = Path(out_path) if out_path else KG_FILE
        _atomic_write_json(p, {"nodes": list(_kg_nodes.values()), "edges": _kg_edges})
        return {
            "success": True,
            "path": str(p),
            "nodes": len(_kg_nodes),
            "edges": len(_kg_edges),
        }


def _kg_clear(remove_file: bool = True) -> Dict[str, Any]:
    with KG_LOCK:
        n, e = len(_kg_nodes), len(_kg_edges)
        _kg_nodes.clear()
        _kg_edges.clear()
        if remove_file and KG_FILE.exists():
            try:
                KG_FILE.unlink()
            except Exception:
                pass
        return {"success": True, "cleared_nodes": n, "cleared_edges": e}


def _kg_load(in_path: Optional[Path] = None) -> Dict[str, Any]:
    p = Path(in_path) if in_path else KG_FILE
    if not p.exists():
        return {"success": False, "reason": "no_kg_on_disk", "path": str(p)}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        with KG_LOCK:
            _kg_nodes.clear()
            _kg_edges.clear()
            for n in data.get("nodes", []):
                _kg_nodes[n["id"]] = n
            _kg_edges.extend(data.get("edges", []))
        return {
            "success": True,
            "path": str(p),
            "nodes": len(_kg_nodes),
            "edges": len(_kg_edges),
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": str(p)}


# ---- 简易 KG 结束 ----


def _save_index() -> Dict[str, Any]:
    with INDEX_LOCK:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        X = _index_matrix()
        _atomic_save_npy(INDEX_VECS, X)
        _atomic_write_json(INDEX_DOCS, [d.model_dump() for d in _docs])
        return {
            "saved": True,
            "path": str(INDEX_DIR),
            "size": _index_size(),
            "dimension": _DIM,
        }


def _load_index() -> Dict[str, Any]:
    if not INDEX_DOCS.exists() or not INDEX_VECS.exists():
        return {"loaded": False, "reason": "no_index_on_disk"}
    with INDEX_LOCK:
        docs = json.loads(INDEX_DOCS.read_text(encoding="utf-8"))
        X = np.load(str(INDEX_VECS))
        if X.ndim != 2 or X.shape[1] != _DIM:
            return {
                "loaded": False,
                "reason": "dim_mismatch",
                "file_dim": int(X.shape[1]) if X.ndim == 2 else None,
                "model_dim": _DIM,
            }
        _docs.clear()
        _vecs.clear()
        for i, d in enumerate(docs):
            _docs.append(Doc(**d))
            _vecs.append(np.asarray(X[i], dtype=np.float32))
        return {"loaded": True, "size": _index_size(), "dimension": _DIM}


def _delete_by_id(doc_id: str) -> bool:
    with INDEX_LOCK:
        idx = next((i for i, d in enumerate(_docs) if d.id == doc_id), None)
        if idx is None:
            return False
        _docs.pop(idx)
        _vecs.pop(idx)
    _kg_remove_doc(doc_id)
    return True


def _load_model() -> SentenceTransformer:
    try:
        if MODEL_DIR.exists():
            return SentenceTransformer(str(MODEL_DIR), device="cpu")
        # 回退到在线模型（使用本地缓存目录）
        return SentenceTransformer("all-MiniLM-L6-v2", device="cpu")
    except Exception as e:
        raise RuntimeError(f"load model failed (local={MODEL_DIR}): {e}")


_model = _load_model()
_DIM = int(getattr(_model, "get_sentence_embedding_dimension", lambda: 384)())
# 启动时尝试加载磁盘索引（若存在）
try:
    _load_index()
except Exception:
    pass


def _embed_texts(texts: List[str]) -> np.ndarray:
    # 归一化，便于点积=cosine
    return _model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)


def _index_size() -> int:
    return len(_docs)


def _index_matrix() -> np.ndarray:
    if not _vecs:
        return np.zeros((0, _DIM), dtype=np.float32)
    return np.vstack(_vecs).astype(np.float32)


@app.get("/readyz")
def readyz() -> Dict[str, Any]:
    return {
        "ready": True,
        "st_model": True,
        "st_status": {"available": True, "error": None, "env_path": str(MODEL_DIR)},
        "deps": {"sentence_transformers": True},
        "cwd": str(Path.cwd()),
        "vector_index": {
            "size": _index_size(),
            "dimension": _DIM,
            "backend": "InMemory",
        },
    }


class IngestReq(BaseModel):
    path: Optional[str] = None
    text: Optional[str] = None
    doc_id: Optional[str] = None
    save_index: Optional[bool] = True
    chunk_size: Optional[int] = None
    chunk_overlap: int = 0
    upsert: bool = False


def _ingest_text(text: str, *, src_path: Optional[str], doc_id: Optional[str]) -> str:
    vec = _embed_texts([text])[0]
    did = doc_id or str(uuid.uuid4())
    with INDEX_LOCK:
        _docs.append(Doc(id=did, text=text, path=src_path))
        _vecs.append(vec)
    _kg_add(did, text, src_path)
    return did


@app.post("/rag/ingest")
def rag_ingest(req: IngestReq, _: bool = Depends(require_api_key)):
    if not req.path and not req.text:
        raise HTTPException(400, "provide 'path' or 'text'")
    text = req.text
    if req.path:
        p = Path(req.path).expanduser()
        if not p.exists():
            raise HTTPException(404, f"path not found: {p}")
        try:
            # 纯文本读取
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(400, f"read path failed: {e}")
    if not text or not text.strip():
        raise HTTPException(400, "empty text")

    inserted = 0
    doc_ids: List[str] = []

    def add_one(_txt: str, _id: Optional[str] = None):
        nonlocal inserted
        if req.upsert and _id:
            _delete_by_id(_id)  # 覆盖同 id
        did = _ingest_text(_txt, src_path=req.path, doc_id=_id)
        inserted += 1
        doc_ids.append(did)

    # 可选字符级分片
    if req.chunk_size and req.chunk_size > 0:
        s = text
        k = req.chunk_size
        ov = max(0, req.chunk_overlap or 0)
        i = 0
        part = 0
        while i < len(s):
            chunk = s[i : i + k]
            if chunk.strip():
                cid = f"{req.doc_id or Path(req.path or 'doc').stem}-chunk-{part}"
                add_one(chunk, cid)
                part += 1
            i += max(1, k - ov)
    else:
        add_one(text, req.doc_id)

    if req.save_index:
        _save_index()
    return {
        "success": True,
        "inserted": inserted,
        "ids": doc_ids,
        "size": _index_size(),
    }


@app.post("/rag/ingest_file")
async def rag_ingest_file(
    file: UploadFile = File(...),
    save_index: bool = True,
    doc_id: Optional[str] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = 0,
    upsert: bool = False,
    _: bool = Depends(require_api_key),
):
    try:
        data = await file.read()
        text = data.decode("utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(400, f"read upload failed: {e}")

    inserted = 0
    ids: List[str] = []

    def add_one(_txt: str, _id: Optional[str] = None):
        nonlocal inserted
        if upsert and _id:
            _delete_by_id(_id)
        did = _ingest_text(_txt, src_path=file.filename, doc_id=_id)
        ids.append(did)
        inserted += 1

    if chunk_size and chunk_size > 0:
        s = text
        k = chunk_size
        ov = max(0, chunk_overlap or 0)
        i = 0
        part = 0
        while i < len(s):
            chunk = s[i : i + k]
            if chunk.strip():
                cid = f"{(doc_id or Path(file.filename or 'doc').stem)}-chunk-{part}"
                add_one(chunk, cid)
                part += 1
            i += max(1, k - ov)
    else:
        add_one(text, doc_id)

    if save_index:
        _save_index()
    return {"success": True, "inserted": inserted, "ids": ids, "size": _index_size()}


@app.post("/rag/ingest_dir")
def rag_ingest_dir(
    dir_path: str = Query(..., min_length=1),
    glob: str = Query(default="**/*.txt"),
    save_index: bool = True,
    limit: Optional[int] = None,
    chunk_size: Optional[int] = None,
    chunk_overlap: int = 0,
    _: bool = Depends(require_api_key),
):
    p = Path(dir_path).expanduser()
    if not p.exists() or not p.is_dir():
        raise HTTPException(404, f"dir not found: {p}")
    inserted = 0
    ids: List[str] = []
    for i, f in enumerate(p.glob(glob)):
        if limit and i >= limit:
            break
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if chunk_size and chunk_size > 0:
            s = text
            k = chunk_size
            ov = max(0, chunk_overlap or 0)
            j = 0
            part = 0
            while j < len(s):
                ch = s[j : j + k]
                if ch.strip():
                    cid = f"{f.stem}-chunk-{part}"
                    did = _ingest_text(ch, src_path=str(f), doc_id=cid)
                    ids.append(did)
                    inserted += 1
                    part += 1
                j += max(1, k - ov)
        else:
            did = _ingest_text(text, src_path=str(f), doc_id=f.stem)
            ids.append(did)
            inserted += 1
    if save_index:
        _save_index()
    return {
        "success": True,
        "inserted": inserted,
        "size": _index_size(),
        "count_ids": len(ids),
    }


@app.get("/index/info")
def index_info():
    return {"size": _index_size(), "dimension": _DIM, "backend": "InMemory"}


@app.get("/index/ids")
def index_ids():
    return {"ids": [d.id for d in _docs]}


@app.delete("/index/clear")
def index_clear(
    remove_file: bool = Query(default=True),
    clear_kg: bool = Query(default=True),
    _: bool = Depends(require_api_key),
):
    before = _index_size()
    _docs.clear()
    _vecs.clear()
    if remove_file:
        try:
            if INDEX_DOCS.exists():
                INDEX_DOCS.unlink()
            if INDEX_VECS.exists():
                INDEX_VECS.unlink()
        except Exception:
            pass
    # 同时处理 KG 清理（内存与可选文件）
    kg = {}
    if clear_kg:
        kg = _kg_clear(remove_file=remove_file)
    return {"cleared": before, "before": before, "kg": kg if clear_kg else None}


@app.post("/index/save")
def index_save(_: bool = Depends(require_api_key)):
    return _save_index()


@app.post("/index/load")
def index_load(_: bool = Depends(require_api_key)):
    return _load_index()


@app.delete("/index/delete")
def index_delete(
    doc_id: str = Query(..., min_length=1), _: bool = Depends(require_api_key)
):
    ok = _delete_by_id(doc_id)
    if not ok:
        raise HTTPException(404, f"id not found: {doc_id}")
    return {"deleted": 1, "size": _index_size()}


class SearchItem(BaseModel):
    id: str
    score: float
    snippet: str
    path: Optional[str] = None


class SearchResp(BaseModel):
    items: List[SearchItem]


@app.get("/rag/search", response_model=SearchResp)
def rag_search(
    query: str = Query(..., min_length=1),
    top_k: int = Query(5, ge=1, le=50),
):
    if _index_size() == 0:
        return {"items": []}
    q = _embed_texts([query])[0].astype(np.float32)
    X = _index_matrix()  # 已归一化，点积=cos
    scores = (X @ q).tolist()
    order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    items = []
    for i in order:
        d = _docs[i]
        items.append(
            {
                "id": d.id,
                "score": float(scores[i]),
                "snippet": d.text[:200],
                "path": d.path,
            }
        )
    return {"items": items}


@app.get("/rag/groups")
def rag_groups(
    k: int = Query(3, ge=1, le=50), max_items: int = Query(100, ge=1, le=1000)
):
    n = _index_size()
    if n == 0:
        return {"success": True, "k": 0, "total": 0, "groups": []}
    idx = list(range(min(n, max_items)))
    k = min(k, len(idx))
    # 选择前k个作为中心，按最大余弦相似度分配
    X = _index_matrix()[idx]
    ids = [_docs[i].id for i in idx]
    centers = X[:k]
    assigns: List[List[int]] = [[] for _ in range(k)]
    for i, vec in enumerate(X):
        if k == 0:
            break
        sims = (centers @ vec).tolist()
        c = int(np.argmax(sims))
        assigns[c].append(i)
    groups = []
    for ci, members in enumerate(assigns):
        gids = [ids[m] for m in members]
        groups.append(
            {
                "center": ids[ci] if ci < len(ids) else None,
                "size": len(gids),
                "ids": gids,
            }
        )
    return {"success": True, "k": k, "total": len(idx), "groups": groups}


@app.get("/kg/snapshot")
def kg_snapshot():
    # 提供简要统计、实体列表与少量示例
    entities = [
        {
            "id": n["id"],
            "type": n.get("type"),
            "value": n.get("value"),
            "count": n.get("count", 0),
        }
        for n in _kg_nodes.values()
        if n.get("type") in {"email", "url"}
    ]
    emails = [e["value"] for e in entities if e["type"] == "email"][:10]
    urls = [e["value"] for e in entities if e["type"] == "url"][:10]
    return {
        "success": True,
        "nodes": len(_kg_nodes),
        "edges": len(_kg_edges),
        "entities": entities,
        "sample": {"emails": emails, "urls": urls},
    }


@app.post("/kg/save")
def kg_save(
    path: Optional[str] = Query(default=None), _: bool = Depends(require_api_key)
):
    return _kg_save(Path(path) if path else None)


@app.delete("/kg/clear")
def kg_clear(remove_file: bool = Query(True), _: bool = Depends(require_api_key)):
    return _kg_clear(remove_file=remove_file)


@app.post("/kg/load")
def kg_load(
    path: Optional[str] = Query(default=None), _: bool = Depends(require_api_key)
):
    return _kg_load(Path(path) if path else None)


# 已有占位
@app.get("/kg/stats")
def kg_stats():
    return {"nodes": len(_kg_nodes), "edges": len(_kg_edges), "ok": True}


@app.post("/index/rebuild")
def index_rebuild(
    reload_docs: bool = Query(True),
    batch: int = Query(256, ge=1, le=4096),
    save_index: bool = Query(True),
    _: bool = Depends(require_api_key),
):
    # 可选从磁盘重新加载 docs
    if reload_docs and INDEX_DOCS.exists():
        docs = json.loads(INDEX_DOCS.read_text(encoding="utf-8"))
        with INDEX_LOCK:
            _docs.clear()
            _docs.extend(Doc(**d) for d in docs)
    # 重新计算全部向量
    with INDEX_LOCK:
        _vecs.clear()
    texts = [d.text for d in _docs]
    new_vecs: List[np.ndarray] = []
    for i in range(0, len(texts), batch):
        new_vecs.append(_embed_texts(texts[i : i + batch]))
    with INDEX_LOCK:
        if new_vecs:
            _vecs.extend(v.astype(np.float32) for v in np.vstack(new_vecs))
    if save_index:
        _save_index()
    return {"rebuilt": _index_size(), "dimension": _DIM, "saved": bool(save_index)}


@app.get("/kg/query")
def kg_query(
    type: str = Query(..., pattern="^(email|url)$"),
    value: str = Query(..., min_length=3),
):
    nid = _kg_node_id(type, value)
    if nid not in _kg_nodes:
        return {"success": True, "docs": [], "count": 0}
    dnids = [e["src"] for e in _kg_edges if e.get("dst") == nid]
    ids = [n.split(":", 1)[1] for n in dnids if n.startswith("doc:")]
    # 映射到现存文档（可能已被删除）
    existing = {d.id for d in _docs}
    ids = [i for i in ids if i in existing]
    return {"success": True, "docs": ids, "count": len(ids)}
