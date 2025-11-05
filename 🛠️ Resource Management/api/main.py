"""
资源管理 - FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 导入API路由
from api import resource_api

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="资源管理API",
    description="系统资源监控、调配、冲突检测和服务启动管理",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(resource_api.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "资源管理系统",
        "version": "1.0.0",
        "description": "系统资源监控、调配、冲突检测和服务启动管理",
        "api_docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "resource-management",
        "version": "1.0.0"
    }


@app.get("/readyz")
async def ready_check():
    """就绪检查"""
    return {
        "status": "ready",
        "message": "资源管理服务已就绪"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("启动资源管理服务...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8018,
        reload=True,
        log_level="info"
    )

