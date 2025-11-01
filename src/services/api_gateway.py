import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query

API_KEY = os.getenv("RAG_API_KEY", "").strip()


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


# experts + readyz
experts_router = APIRouter(prefix="/experts", tags=["experts"])
try:
    from src.core.module_registry import get_expert
    from src.experts.finance_expert import FinanceExpert  # noqa: F401
    from src.experts.trend_expert import TrendExpert  # noqa: F401
except Exception:
    get_expert = None


@experts_router.post("/{name}/predict")
def experts_predict(
    name: str, payload: Dict[str, Any] = Body(...), _: bool = Depends(require_api_key)
):
    if not get_expert:
        raise HTTPException(status_code=500, detail="experts registry unavailable")
    expert = get_expert(name)
    return expert.predict(payload)


readyz_router = APIRouter(tags=["health"])


@readyz_router.get("/readyz")
def readyz():
    return {"ok": True, "ts": time.time()}


# groups（内存回环）
_groups_state: List[Dict[str, Any]] = []
groups_router = APIRouter(prefix="/groups", tags=["groups"])


@groups_router.get("")
def list_groups():
    return {"groups": list(_groups_state)}


@groups_router.post("")
def create_group(payload: Dict[str, Any] = Body(...)):
    item = {"name": payload.get("name"), "data": payload}
    _groups_state.append(item)
    return {"ok": True, "group": item, "count": len(_groups_state)}


@groups_router.delete("")
def clear_groups():
    _groups_state.clear()
    return {"ok": True, "count": 0}


# kg（save/clear/load 回环）
_KG_SNAPSHOT: Dict[str, Any] = {"nodes": [], "edges": []}
kg_router = APIRouter(prefix="/kg", tags=["kg"])


@kg_router.post("/save")
def kg_save(payload: Dict[str, Any] = Body(...)):
    global _KG_SNAPSHOT
    _KG_SNAPSHOT = {
        "nodes": payload.get("nodes", []),
        "edges": payload.get("edges", []),
    }
    return {
        "ok": True,
        "saved": True,
        "nodes": len(_KG_SNAPSHOT["nodes"]),
        "edges": len(_KG_SNAPSHOT["edges"]),
    }


@kg_router.get("/snapshot")
def kg_snapshot():
    return {
        "ok": True,
        "nodes": _KG_SNAPSHOT.get("nodes", []),
        "edges": _KG_SNAPSHOT.get("edges", []),
    }


@kg_router.post("/clear")
@kg_router.delete("/clear")
def kg_clear():
    global _KG_SNAPSHOT
    _KG_SNAPSHOT = {"nodes": [], "edges": []}
    return {"ok": True, "cleared": True}


@kg_router.get("/load")
@kg_router.post("/load")
def kg_load():
    return {"ok": True, "snapshot": _KG_SNAPSHOT}


# ====== /rag 最小实现（含 ingest 与 groups）======
_RAG_INDEX: List[Dict[str, Any]] = []


def _chunk_text(text: str, max_len: int = 400) -> List[str]:
    parts: List[str] = []
    buf = ""
    for seg in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        for sent in seg.split("."):
            sent = sent.strip()
            if not sent:
                continue
            if len(buf) + len(sent) + 1 > max_len:
                parts.append(buf.strip())
                buf = sent
            else:
                buf = (buf + " " + sent).strip() if buf else sent
    if buf:
        parts.append(buf.strip())
    return parts or ([text[:max_len]] if text else [])


rag_router = APIRouter(prefix="/rag", tags=["rag"])


@rag_router.post("/ingest")
def rag_ingest(payload: Dict[str, Any] = Body(...)):
    path = payload.get("path")
    save_index = bool(payload.get("save_index", True))
    if not path:
        raise HTTPException(status_code=400, detail="path required")
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=400, detail=f"file not found: {path}")
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"read failed: {e}")
    chunks = _chunk_text(text)
    doc = {"path": str(p), "chunks": chunks, "size": len(text)}
    if save_index:
        _RAG_INDEX.append(doc)
    return {"success": True, "chunks": len(chunks), "indexed": save_index}


@rag_router.get("/groups")
def rag_groups(
    k: int = Query(3, ge=1, le=50), max_items: int = Query(100, ge=1, le=10000)
):
    # 简化：将已索引的 chunk 扁平化，按 round-robin 分配到 k 组
    items: List[Dict[str, Any]] = []
    for doc in _RAG_INDEX:
        for ch in doc.get("chunks", []):
            items.append({"text": ch, "path": doc.get("path")})
            if len(items) >= max_items:
                break
        if len(items) >= max_items:
            break
    groups = [{"id": i, "items": []} for i in range(k)]
    for idx, it in enumerate(items):
        groups[idx % k]["items"].append(it)
    return {"ok": True, "k": k, "total": len(items), "groups": groups}


@rag_router.post("/clear")
def rag_clear():
    _RAG_INDEX.clear()
    return {"ok": True, "count": 0}


# ====== 汇总导出 ======
router = APIRouter()
router.include_router(readyz_router)
router.include_router(experts_router)
router.include_router(groups_router)
router.include_router(kg_router)
router.include_router(rag_router)
