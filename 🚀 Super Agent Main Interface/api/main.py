"""
超级Agent主界面 - FastAPI主应用
主应用入口，注册所有路由
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import os

# 导入API路由
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.super_agent_api import router as super_agent_router, observability_system
from core.observability_middleware import ObservabilityMiddleware
from core.security.middleware import SecurityMiddleware
from core.security.audit import get_audit_logger

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 正在启动超级Agent主界面...")
    
    # 初始化服务（服务已在super_agent_api.py中初始化）
    logger.info("✅ 服务初始化完成")
    
    yield
    
    # 关闭时的清理工作
    logger.info("👋 正在关闭超级Agent主界面...")


# 创建FastAPI应用
app = FastAPI(
    title="AI-STACK 超级Agent主界面",
    description="企业级AI智能系统 - 超级Agent主界面API",
    version="5.0.0",
    lifespan=lifespan
)

# 安全审计中间件应最先执行
app.add_middleware(
    SecurityMiddleware,
    audit_logger=get_audit_logger()
)

# P0-018: 添加可观测性中间件（必须在CORS之前）
if observability_system:
    app.add_middleware(
        ObservabilityMiddleware,
        observability_system=observability_system
    )

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",  # OpenWebUI
        "http://127.0.0.1:3000",
        "http://localhost:8011",  # RAG系统
        "http://localhost:8012",  # ERP前端
        "http://localhost:8013",  # ERP后端
        "http://localhost:8014",  # 股票系统
        "http://localhost:8015",  # 趋势分析
        "http://localhost:8016",  # 内容创作
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(super_agent_router)

# 静态文件服务
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    # 静态文件（CSS/JS/图片）
    static_dir = web_dir / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # CSS文件
    css_dir = web_dir / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    
    # JS文件
    js_dir = web_dir / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回主界面"""
    index_file = web_dir / "index.html"
    
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    else:
        return """
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <title>AI-STACK 超级Agent</title>
        </head>
        <body>
            <h1>AI-STACK 超级Agent主界面</h1>
            <p>API文档: <a href="/docs">/docs</a></p>
            <p>健康检查: <a href="/health">/health</a></p>
        </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查关键服务
        from core.llm_service import get_llm_service
        
        llm_service = get_llm_service()
        
        return {
            "status": "healthy",
            "version": "5.0.0",
            "services": {
                "super_agent": True,
                "llm_service": llm_service is not None,
                "llm_provider": llm_service.provider.value if llm_service else None
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    
    # 从环境变量读取配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )

