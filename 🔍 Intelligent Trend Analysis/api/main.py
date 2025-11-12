"""
Trend Analysis API Main Application
趋势分析API主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.trend_api import router as trend_router
from api.custom_trend_api import router as custom_trend_router

# 创建FastAPI应用
app = FastAPI(
    title="Trend Analysis API",
    description="智能趋势分析系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8015",  # 趋势分析前端
        "http://localhost:3000",  # OpenWebUI
        "http://localhost:8000",  # 主应用
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(trend_router, prefix="/api")
app.include_router(custom_trend_router, prefix="/api")

@app.get("/")
def root():
    """API根路径"""
    return {
        "name": "Trend Analysis API",
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
        port=8015,
        reload=True
    )

