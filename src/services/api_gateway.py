import os
import time
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, Header, HTTPException

API_KEY = os.getenv("RAG_API_KEY", "").strip()


def require_api_key(x_api_key: str | None = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


experts_router = APIRouter(prefix="/experts", tags=["experts"])

try:
    # 导入以触发 register() 侧效应
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


# 就绪检查（模型/索引/KG按需补充内部探针）
readyz_router = APIRouter(tags=["health"])


@readyz_router.get("/readyz")
def readyz():
    # 最小探针；若有 _model/_index 可扩展为真实状态探测
    return {"ok": True, "ts": time.time()}


# 如果此文件有全局 app，则直接挂载；否则导出 router 给上层 include
try:
    app.include_router(experts_router)  # type: ignore[name-defined]
    app.include_router(readyz_router)  # type: ignore[name-defined]
except Exception:
    router = APIRouter()
    router.include_router(experts_router)
    router.include_router(readyz_router)
