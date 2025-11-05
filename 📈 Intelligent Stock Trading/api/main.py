"""
Stock Trading API Main Application
股票交易API主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.stock_api import router as stock_router

# 创建FastAPI应用
app = FastAPI(
    title="Stock Trading API",
    description="智能股票交易系统API",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8014",  # 股票前端
        "http://localhost:3000",  # OpenWebUI
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(stock_router, prefix="/api")

@app.get("/")
def root():
    """API根路径"""
    return {
        "name": "Stock Trading API",
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
        port=8014,
        reload=True
    )

