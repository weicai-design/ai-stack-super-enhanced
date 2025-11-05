"""
智能任务代理 - FastAPI 主应用
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
from pathlib import Path

# 导入API路由
from web.api import task_api

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="智能任务代理API",
    description="AI驱动的任务规划、执行、监控系统",
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
app.include_router(task_api.router)

# 静态文件服务
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# 模板文件路径
templates_path = Path(__file__).parent.parent / "templates"


@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径 - 返回前端页面"""
    dashboard_file = templates_path / "dashboard.html"
    
    if dashboard_file.exists():
        return dashboard_file.read_text(encoding="utf-8")
    else:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>智能任务代理</title>
            <meta charset="utf-8">
        </head>
        <body>
            <h1>智能任务代理系统</h1>
            <p>API文档: <a href="/docs">/docs</a></p>
            <p>任务列表: <a href="/api/tasks/list">/api/tasks/list</a></p>
        </body>
        </html>
        """


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "intelligent-task-agent",
        "version": "1.0.0"
    }


@app.get("/readyz")
async def ready_check():
    """就绪检查"""
    return {
        "status": "ready",
        "message": "智能任务代理服务已就绪"
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info("启动智能任务代理服务...")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8017,
        reload=True,
        log_level="info"
    )

