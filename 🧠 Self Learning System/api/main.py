"""
自我学习系统 - FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# 导入API路由
from api import learning_api

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="自我学习系统API",
    description="功能分析、问题检测、优化建议、用户习惯学习",
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
app.include_router(learning_api.router)


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "自我学习系统",
        "version": "1.0.0",
        "description": "AI驱动的系统自我学习和进化",
        "api_docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "self-learning-system",
        "version": "1.0.0"
    }


@app.get("/readyz")
async def ready_check():
    """就绪检查"""
    return {
        "status": "ready",
        "message": "自我学习系统已就绪"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("启动自我学习系统...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8019,
        reload=True,
        log_level="info"
    )

