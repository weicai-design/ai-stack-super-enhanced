"""
Content Creation API Main Application
内容创作API主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.content_api import router as content_router

# 创建FastAPI应用
app = FastAPI(
    title="Content Creation API",
    description="智能内容创作系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8016",  # 内容创作前端
        "http://localhost:3000",  # OpenWebUI
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(content_router, prefix="/api")

@app.get("/")
def root():
    """API根路径"""
    return {
        "name": "Content Creation API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8016,
        reload=True
    )

