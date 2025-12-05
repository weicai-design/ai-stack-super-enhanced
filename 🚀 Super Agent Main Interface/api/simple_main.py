"""
简化版API服务器 - 解决依赖问题
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="AI-STACK 简化版API",
    description="企业级AI智能系统 - 简化版API",
    version="5.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "status": "running",
        "message": "AI-STACK API服务器正在运行",
        "version": "5.0.0"
    }

@app.get("/api/experts")
async def get_experts():
    """获取专家列表"""
    return {
        "experts": [
            {"id": "rag_expert", "name": "RAG专家", "status": "active"},
            {"id": "erp_expert", "name": "ERP专家", "status": "active"},
            {"id": "content_expert", "name": "内容创作专家", "status": "active"},
            {"id": "trend_expert", "name": "趋势分析专家", "status": "active"},
            {"id": "stock_expert", "name": "股票分析专家", "status": "active"},
            {"id": "operations_finance_expert", "name": "运营财务专家", "status": "active"}
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "5.0.0",
        "services": {
            "api_server": True,
            "simplified_mode": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8001"))
    
    logger.info(f"🚀 启动简化版API服务器: {host}:{port}")
    
    uvicorn.run(
        "simple_main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )