import json
import os
import re
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


# ====== /rag 最小实现（含 ingest 与 groups）======
_RAG_INDEX: List[Dict[str, Any]] = []

# 简单 KG 实体缓存
_KG_SNAPSHOT: Dict[str, Any] = {"nodes": [], "edges": []}
_KG_ENTITIES: List[Dict[str, Any]] = []

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL_RE = re.compile(r"https?://[^\s)]+", re.IGNORECASE)


def _extract_entities(text: str) -> List[Dict[str, Any]]:
    ents: List[Dict[str, Any]] = []
    for m in _EMAIL_RE.findall(text):
        ents.append({"type": "email", "value": m})
    for m in _URL_RE.findall(text):
        ents.append({"type": "url", "value": m})
    return ents


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
    # 简单实体抽取并写入 KG 快照
    ents = _extract_entities(text)
    if ents:
        # 记录文档实体
        doc_ent = {"type": "document", "value": str(p)}
        _KG_ENTITIES.append(doc_ent)
        for e in ents:
            _KG_ENTITIES.append(e)
        # 同步 nodes（去重）
        seen = set()
        nodes = []
        for e in _KG_ENTITIES:
            key = (e.get("type"), e.get("value"))
            if key in seen:
                continue
            seen.add(key)
            nodes.append(
                {
                    "id": f"{e['type']}:{e['value']}",
                    "label": e["value"],
                    "type": e["type"],
                }
            )
        _KG_SNAPSHOT["nodes"] = nodes
        # 简单边：document -> entity
        edges = []
        for e in ents:
            edges.append(
                {
                    "source": f"document:{p}",
                    "target": f"{e['type']}:{e['value']}",
                    "type": "contains",
                }
            )
        _KG_SNAPSHOT["edges"] = edges
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
    # 同步清空 KG
    _KG_SNAPSHOT["nodes"].clear()
    _KG_SNAPSHOT["edges"].clear()
    _KG_ENTITIES.clear()
    return {"ok": True, "count": 0}


# ====== /kg（含 snapshot/save/clear/load）======
kg_router = APIRouter(prefix="/kg", tags=["kg"])


@kg_router.post("/save")
def kg_save(
    path: Optional[str] = Query(default=None),
    payload: Optional[Dict[str, Any]] = Body(default=None),
    _: bool = Depends(require_api_key),
):
    global _KG_SNAPSHOT
    data = payload or _KG_SNAPSHOT
    # 规范化快照结构
    snap = {"nodes": data.get("nodes", []), "edges": data.get("edges", [])}

    # 若提供路径，则写入文件
    if path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        return {
            "ok": True,
            "saved": True,
            "path": str(p),
            "nodes": len(snap["nodes"]),
            "edges": len(snap["edges"]),
        }

    # 否则更新内存快照
    _KG_SNAPSHOT = snap
    _KG_ENTITIES.clear()
    for n in snap["nodes"]:
        t = n.get("type") or (
            n.get("id", "").split(":", 1)[0] if isinstance(n.get("id"), str) else "node"
        )
        _KG_ENTITIES.append({"type": t, "value": n.get("label") or n.get("id")})
    return {
        "ok": True,
        "saved": True,
        "nodes": len(snap["nodes"]),
        "edges": len(snap["edges"]),
    }


@kg_router.get("/snapshot")
def kg_snapshot():
    return {
        "ok": True,
        "entities": list(_KG_ENTITIES),
        "nodes": _KG_SNAPSHOT.get("nodes", []),
        "edges": _KG_SNAPSHOT.get("edges", []),
    }


@kg_router.post("/clear")
@kg_router.delete("/clear")
def kg_clear():
    _KG_SNAPSHOT["nodes"].clear()
    _KG_SNAPSHOT["edges"].clear()
    _KG_ENTITIES.clear()
    return {"ok": True, "cleared": True}


@kg_router.get("/load")
@kg_router.post("/load")
def kg_load(path: Optional[str] = Query(default=None)):
    global _KG_SNAPSHOT
    if path:
        p = Path(path)
        if not p.exists():
            raise HTTPException(status_code=400, detail=f"kg file not found: {path}")
        try:
            snap = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"kg read failed: {e}")
        _KG_SNAPSHOT = {"nodes": snap.get("nodes", []), "edges": snap.get("edges", [])}
        _KG_ENTITIES.clear()
        for n in _KG_SNAPSHOT["nodes"]:
            t = n.get("type") or (
                n.get("id", "").split(":", 1)[0]
                if isinstance(n.get("id"), str)
                else "node"
            )
            _KG_ENTITIES.append({"type": t, "value": n.get("label") or n.get("id")})
        return {
            "ok": True,
            "loaded": True,
            "nodes": len(_KG_SNAPSHOT["nodes"]),
            "edges": len(_KG_SNAPSHOT["edges"]),
            "path": str(p),
        }
    return {"ok": True, "snapshot": _KG_SNAPSHOT}


# ====== 汇总导出 ======
router = APIRouter()
router.include_router(readyz_router)
router.include_router(experts_router)
router.include_router(groups_router)
router.include_router(kg_router)
router.include_router(rag_router)
