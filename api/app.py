from fastapi import FastAPI

app = FastAPI(title="AI Stack Super Enhanced - Lite API", version="0.1.0")

# 复用 src 的统一路由（包含 /readyz 与 /experts/*，以及我们下面补充的 /groups 与 /kg）
try:
    from src.services.api_gateway import router as api_router

    app.include_router(api_router)
except Exception as e:
    # 保底路由
    @app.get("/readyz")
    def readyz():
        return {"ok": True, "reason": f"router load failed: {e}"}
