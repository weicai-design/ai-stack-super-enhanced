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

from api.super_agent_api import (
    router as super_agent_router,
    observability_system,
    resource_monitor,
    super_agent,
)
from core.security.audit_pipeline import get_audit_pipeline
from core.security.risk_engine import get_risk_engine
from core.security.permission_guard import get_permission_guard
from core.security.crawler_compliance import get_crawler_compliance_service
from api.orders_api import router as orders_router
from api.procurements_api import router as procurements_router
from api.inventory_api import router as inventory_router
from api.production_api import router as production_router
from api.quality_api import router as quality_router
from api.logistics_api import router as logistics_router
from api.after_sales_api import router as after_sales_router
from api.finance_settlement_api import router as finance_settlement_router
from api.workflow_api import router as workflow_router
from api.workflow_observability_api import router as workflow_observability_router
from api.workflow_orchestrator_metrics_api import router as workflow_orchestrator_metrics_router
from api.tenant_auth_api import router as tenant_auth_router
from api.crawler_compliance_api import router as crawler_compliance_router
from api.task_lifecycle_api import router as task_lifecycle_router
from api.learning_curve_api import router as learning_curve_router
from api.resource_scheduler_api import router as resource_scheduler_router
from api.task_integration_api import router as task_integration_router
from api.expert_api import router as expert_router
from core.observability_middleware import ObservabilityMiddleware
from core.security.middleware import SecurityMiddleware
from core.security.audit import get_audit_logger
from core.tenant_middleware import TenantContextMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    import asyncio
    
    # 启动时初始化
    logger.info("🚀 正在启动超级Agent主界面...")
    
    # 启动后台任务
    background_tasks = []
    
    # 启动资源监控器
    if resource_monitor:
        resource_monitor_task = asyncio.create_task(resource_monitor.start_monitoring())
        background_tasks.append(resource_monitor_task)
        logger.info("✅ 资源监控器后台任务已启动")
    
    # 启动ERP监听器
    if super_agent:
        try:
            from api.super_agent_api import _erp_listener
            erp_listener_task = asyncio.create_task(_erp_listener())
            background_tasks.append(erp_listener_task)
            logger.info("✅ ERP监听器后台任务已启动")
        except ImportError:
            logger.warning("⚠️ ERP监听器导入失败，跳过启动")
    
    # 初始化服务（服务已在super_agent_api.py中初始化）
    logger.info("✅ 服务初始化完成")
    
    yield
    
    # 关闭时的清理工作
    logger.info("👋 正在关闭超级Agent主界面...")
    
    # 取消所有后台任务
    for task in background_tasks:
        task.cancel()
    
    # 等待任务完成
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)
        logger.info("✅ 所有后台任务已停止")


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
    audit_logger=get_audit_logger(),
    audit_pipeline=get_audit_pipeline(),
    risk_engine=get_risk_engine(),
    permission_guard=get_permission_guard(),
    crawler_compliance=get_crawler_compliance_service(),
)

# 多租户上下文中间件
app.add_middleware(
    TenantContextMiddleware,
    header_name="X-Tenant-ID",
    default_tenant="global",
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
app.include_router(orders_router)  # 订单全生命周期（T012）
app.include_router(procurements_router)  # 采购全生命周期（T014）
app.include_router(inventory_router)  # 库存全生命周期（T015）
app.include_router(production_router)  # 生产全生命周期（T016）
app.include_router(quality_router)  # 质量管理（T017，集成在生产）
app.include_router(logistics_router)  # 物流全生命周期（T018）
app.include_router(after_sales_router)  # 售后全生命周期（T019）
app.include_router(finance_settlement_router)  # 财务结算全生命周期（T020）
app.include_router(workflow_router)  # 双线闭环工作流API
app.include_router(workflow_observability_router)  # 工作流可观测性API
app.include_router(workflow_orchestrator_metrics_router)  # 工作流编排器指标API
app.include_router(tenant_auth_router)  # 多租户认证API（5.1）
app.include_router(crawler_compliance_router)  # 爬虫合规API（5.2）
app.include_router(task_lifecycle_router)  # 任务生命周期API（6.1）
app.include_router(learning_curve_router)  # 学习曲线API（6.2）
app.include_router(resource_scheduler_router)  # 资源调度器API（6.2）
app.include_router(task_integration_router)  # 智能任务集成API（6.3）
app.include_router(expert_router)  # 专家系统API（T005）

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

