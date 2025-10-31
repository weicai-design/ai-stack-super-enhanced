from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Stack Super Enhanced", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    from src.services.api_gateway import router as api_router

    app.include_router(api_router)
except Exception:
    pass


@app.get("/")
def root():
    return {"ok": True}
