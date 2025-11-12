"""
运营财务模块主应用
独立的前后端模块，与ERP数据监听系统集成
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import sys
import os

# 添加模块路径
operations_path = os.path.join(os.path.dirname(__file__), "..", "operations")
finance_path = os.path.join(os.path.dirname(__file__), "..", "finance")
sys.path.insert(0, operations_path)
sys.path.insert(0, finance_path)

from api.operations_api import router as operations_router
from api.finance_api import router as finance_router

# 导入ERP连接器
from core.erp_connector import ERPConnector

# 全局ERP连接器
erp_connector = ERPConnector(connection_type="both")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 正在启动运营财务模块...")
    
    # 启动ERP数据监听
    print("🔔 正在连接ERP数据监听系统...")
    await erp_connector.start_listening()
    print("✅ ERP数据监听已启动")
    
    yield
    
    # 关闭时的清理工作
    print("🔔 正在停止ERP数据监听...")
    erp_connector.stop_listening()
    print("👋 关闭运营财务模块")


# 创建FastAPI应用
app = FastAPI(
    title="Operations & Finance Management API",
    description="运营财务管理模块 - 独立前后端，与ERP数据监听系统集成",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8014",
        "http://127.0.0.1:8014",
        "http://localhost:8012",
        "http://127.0.0.1:8012",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(operations_router)
app.include_router(finance_router)

# 静态文件服务（前端）
static_dir = os.path.join(os.path.dirname(__file__), "web")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


# ERP事件接收端点（供ERP监听系统调用）
@app.post("/api/operations/erp-events")
async def receive_erp_event(event: dict):
    """接收ERP事件（Webhook）"""
    try:
        await erp_connector._handle_erp_event(event)
        return {"success": True, "message": "事件已处理"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# 根路径
@app.get("/")
def root():
    """API根路径"""
    return {
        "message": "Operations & Finance Management API",
        "status": "running",
        "version": "1.0.0",
        "modules": {
            "operations": "运营管理",
            "finance": "财务管理"
        },
        "erp_integration": {
            "type": "事件驱动架构",
            "listening": erp_connector.listening,
            "connection_type": erp_connector.connection_type
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "operations": "/api/operations/*",
            "finance": "/api/finance/*"
        }
    }


# 健康检查
@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "modules": {
            "operations": "active",
            "finance": "active"
        },
        "erp_connection": {
            "listening": erp_connector.listening,
            "cached_data": len(erp_connector.synced_data_cache) > 0
        }
    }


# 数据同步端点
@app.post("/api/sync/erp")
async def sync_erp_data():
    """同步ERP数据"""
    data = await erp_connector.sync_data()
    return {
        "success": True,
        "data": data,
        "timestamp": data.get("timestamp")
    }


@app.get("/api/sync/status")
async def get_sync_status():
    """获取同步状态"""
    return {
        "success": True,
        "listening": erp_connector.listening,
        "connection_type": erp_connector.connection_type,
        "cached_data_keys": list(erp_connector.synced_data_cache.keys()),
        "event_handlers": list(erp_connector.event_handlers.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8014,
        reload=True,
        log_level="info"
    )

