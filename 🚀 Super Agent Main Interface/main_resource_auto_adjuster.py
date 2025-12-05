#!/usr/bin/env python3
"""
资源自动调节器主入口 - AI-STACK优化：集成监控、API和Web界面

功能特性：
1. 集成资源监控、问题分析和自动调节
2. 提供RESTful API接口
3. 支持Web可视化界面
4. 支持配置管理和统计报告

架构设计：
- 模块化架构，支持扩展
- 异步处理，高性能监控
- 统一配置管理
- 完整的错误处理
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

# FastAPI相关导入
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn

# 导入资源调节器组件
from core.resource_auto_adjuster import ResourceAutoAdjuster, ResourceConfig
from api.resource_auto_adjuster_api import router as adjuster_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resource_auto_adjuster.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ResourceAutoAdjusterApp:
    """资源自动调节器应用主类 - AI-STACK优化：集成应用管理"""
    
    def __init__(self):
        self.app = None
        self.adjuster = None
        self.monitoring_task = None
        self.is_running = False
        
    def initialize(self) -> None:
        """初始化应用"""
        try:
            # 创建FastAPI应用
            self.app = FastAPI(
                title="资源自动调节器",
                description="AI-STACK优化的智能资源监控与自动调节系统",
                version="1.0.0",
                docs_url="/api/docs",
                redoc_url="/api/redoc"
            )
            
            # 初始化资源调节器
            config = ResourceConfig()
            self.adjuster = ResourceAutoAdjuster(config=config)
            
            # 设置中间件和路由
            self._setup_middleware()
            self._setup_routes()
            self._setup_static_files()
            
            logger.info("资源自动调节器应用初始化完成")
            
        except Exception as e:
            logger.error(f"应用初始化失败: {e}")
            raise
    
    def _setup_middleware(self) -> None:
        """设置中间件"""
        
        @self.app.middleware("http")
        async def add_process_time_header(request: Request, call_next):
            """添加处理时间头"""
            import time
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            return response
        
        @self.app.middleware("http")
        async def catch_exceptions_middleware(request: Request, call_next):
            """全局异常处理中间件"""
            try:
                response = await call_next(request)
                return response
            except Exception as e:
                logger.error(f"请求处理异常: {e}")
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=500,
                    content={
                        "status": "error",
                        "message": f"服务器内部错误: {str(e)}",
                        "data": None
                    }
                )
    
    def _setup_routes(self) -> None:
        """设置路由"""
        
        # 包含API路由
        self.app.include_router(adjuster_router)
        
        # 根路由
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root(request: Request):
            """根路由，重定向到Web界面"""
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/web")
        
        # Web界面路由
        @self.app.get("/web", response_class=HTMLResponse)
        async def read_web_interface(request: Request):
            """Web界面路由"""
            templates = Jinja2Templates(directory="web")
            return templates.TemplateResponse(
                "resource_auto_adjuster.html",
                {"request": request}
            )
        
        # 健康检查路由
        @self.app.get("/health")
        async def health_check() -> Dict[str, Any]:
            """健康检查接口"""
            return {
                "status": "healthy",
                "service": "resource_auto_adjuster",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        
        # 系统信息路由
        @self.app.get("/api/system/info")
        async def get_system_info() -> Dict[str, Any]:
            """获取系统信息"""
            import platform
            import psutil
            
            return {
                "system": {
                    "platform": platform.platform(),
                    "python_version": platform.python_version(),
                    "hostname": platform.node()
                },
                "resources": {
                    "cpu_count": psutil.cpu_count(),
                    "total_memory": psutil.virtual_memory().total,
                    "total_disk": psutil.disk_usage('/').total
                },
                "service": {
                    "name": "Resource Auto Adjuster",
                    "version": "1.0.0",
                    "status": "running"
                }
            }
    
    def _setup_static_files(self) -> None:
        """设置静态文件服务"""
        # 创建静态文件目录（如果不存在）
        static_dir = Path("static")
        static_dir.mkdir(exist_ok=True)
        
        # 挂载静态文件
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
    
    async def start_monitoring(self) -> None:
        """启动资源监控任务"""
        if not self.adjuster:
            logger.error("调节器未初始化，无法启动监控")
            return
        
        self.is_running = True
        
        async def monitoring_loop():
            """监控循环"""
            while self.is_running:
                try:
                    # 执行资源监控
                    issues = await self.adjuster.monitor_resources()
                    
                    # 如果有问题，记录日志
                    if issues:
                        logger.info(f"检测到 {len(issues)} 个资源问题")
                        
                        # 如果启用自动调节，执行自动调节
                        if self.adjuster.config.get("monitoring.enable_auto_adjust", False):
                            await self._auto_adjust_issues(issues)
                    
                    # 等待下一个监控周期
                    interval = self.adjuster.config.get("monitoring.interval", 5)
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"监控循环异常: {e}")
                    await asyncio.sleep(5)  # 出错后等待5秒重试
        
        # 启动监控任务
        self.monitoring_task = asyncio.create_task(monitoring_loop())
        logger.info("资源监控任务已启动")
    
    async def _auto_adjust_issues(self, issues: list) -> None:
        """自动调节检测到的问题"""
        try:
            threshold = self.adjuster.config.get("monitoring.auto_adjust_threshold", "medium")
            
            for issue in issues:
                # 根据阈值决定是否自动调节
                should_adjust = False
                
                if threshold == "low" and issue.severity == "critical":
                    should_adjust = True
                elif threshold == "medium" and issue.severity in ["warning", "critical"]:
                    should_adjust = True
                elif threshold == "high":
                    should_adjust = True
                
                if should_adjust:
                    # 分析问题并获取建议
                    suggestions = await self.adjuster.analyze_issue(issue)
                    
                    if suggestions:
                        # 执行第一个建议（简化实现）
                        suggestion = suggestions[0]
                        
                        # 检查是否需要授权
                        requires_approval = self.adjuster.config.get(
                            "security.require_approval_for_critical", True
                        )
                        
                        approved = not (requires_approval and issue.severity == "critical")
                        
                        if approved:
                            result = await self.adjuster.execute_adjustment(suggestion, approved=True)
                            logger.info(f"自动调节执行: {suggestion.action.value}, 结果: {result}")
                        else:
                            logger.warning(f"需要授权才能执行调节: {suggestion.action.value}")
                            
        except Exception as e:
            logger.error(f"自动调节异常: {e}")
    
    async def stop_monitoring(self) -> None:
        """停止资源监控"""
        self.is_running = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            
        logger.info("资源监控任务已停止")
    
    async def run_server(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """运行服务器"""
        try:
            # 启动监控任务
            await self.start_monitoring()
            
            # 配置服务器
            config = uvicorn.Config(
                app=self.app,
                host=host,
                port=port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            logger.info(f"服务器启动在 http://{host}:{port}")
            logger.info(f"API文档: http://{host}:{port}/api/docs")
            logger.info(f"Web界面: http://{host}:{port}/web")
            
            # 运行服务器
            await server.serve()
            
        except Exception as e:
            logger.error(f"服务器运行异常: {e}")
            raise
        finally:
            # 确保监控任务停止
            await self.stop_monitoring()


def setup_signal_handlers(app_instance: ResourceAutoAdjusterApp) -> None:
    """设置信号处理器"""
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        logger.info(f"接收到信号 {signum}，正在关闭应用...")
        
        # 停止监控任务
        if app_instance.monitoring_task:
            app_instance.monitoring_task.cancel()
        
        # 退出应用
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """主函数"""
    try:
        # 创建应用实例
        app_instance = ResourceAutoAdjusterApp()
        
        # 初始化应用
        app_instance.initialize()
        
        # 设置信号处理器
        setup_signal_handlers(app_instance)
        
        # 运行服务器
        await app_instance.run_server()
        
    except KeyboardInterrupt:
        logger.info("用户中断应用")
    except Exception as e:
        logger.error(f"应用运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 检查依赖
    try:
        import fastapi
        import uvicorn
        import psutil
        import jinja2
    except ImportError as e:
        print(f"缺少依赖: {e}")
        print("请安装依赖: pip install fastapi uvicorn psutil jinja2")
        sys.exit(1)
    
    # 运行主函数
    asyncio.run(main())