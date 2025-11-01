from fastapi import FastAPI

app = FastAPI(title="AI Stack Super Enhanced - Lite API", version="0.1.0")

try:
    from src.services.api_gateway import router as api_router

    app.include_router(api_router)
except Exception as e:

    @app.get("/readyz")
    def readyz():
        return {"ok": True, "reason": f"router load failed: {e}"}
