import os
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException

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


# 汇总导出
router = APIRouter()
router.include_router(readyz_router)
router.include_router(experts_router)
router.include_router(groups_router)
router.include_router(kg_router)
