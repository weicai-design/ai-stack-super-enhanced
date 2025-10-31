#!/usr/bin/env python3
"""
Enhanced RAG Web Application
对应需求: 1.7 RAG前端功能在open webui上实现，1.9 形成前端操作界面
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/111. app.py
"""

import logging
import os

# 导入RAG核心模块
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from core.dynamic_knowledge_graph import DynamicKnowledgeGraph
from core.hybrid_rag_engine import HybridRAGEngine
from pipelines.smart_ingestion_pipeline import SmartIngestionPipeline

from processors.file_processors.universal_file_parser import UniversalFileParser

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/Users/ywc/ai-stack-super-enhanced/logs/rag_web.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("rag_web_app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """生命周期管理器 - 替换已弃用的on_event"""
    # 启动时初始化
    await rag_web_app.initialize_components()
    yield
    # 关闭时清理
    logger.info("Shutting down RAG Web Application...")


class RAGWebApp:
    """增强RAG Web应用"""

    def __init__(self):
        self.app = FastAPI(
            title="Enhanced RAG System",
            description="AI Stack超级增强版 - RAG知识检索系统",
            version="1.0.0",
            docs_url="/api/docs",
            redoc_url="/api/redoc",
            lifespan=lifespan,
        )

        # 初始化核心组件
        self.rag_engine = None
        self.knowledge_graph = None
        self.file_parser = None
        self.ingestion_pipeline = None

        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        self.templates = Jinja2Templates(
            directory=os.path.join(os.path.dirname(__file__), "templates")
        )

    def _setup_middleware(self):
        """设置中间件"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 添加性能监控中间件
        @self.app.middleware("http")
        async def add_process_time_header(request, call_next):
            start_time = datetime.now()
            response = await call_next(request)
            process_time = (datetime.now() - start_time).total_seconds()
            response.headers["X-Process-Time"] = str(process_time)
            logger.info(
                f"Request processed in {process_time:.3f}s: {request.method} {request.url}"
            )
            return response

    def _setup_static_files(self):
        """设置静态文件"""
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        self.app.mount("/static", StaticFiles(directory=static_dir), name="static")

    def _setup_routes(self):
        """设置路由"""

        # 健康检查
        @self.app.get("/health", response_model=Dict[str, Any])
        async def health_check():
            """系统健康检查"""
            status = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "components": {
                    "rag_engine": self.rag_engine is not None,
                    "knowledge_graph": self.knowledge_graph is not None,
                    "file_parser": self.file_parser is not None,
                    "ingestion_pipeline": self.ingestion_pipeline is not None,
                },
            }
            return status

        # 文件上传接口
        @self.app.post("/api/upload")
        async def upload_file():
            """文件上传接口"""
            return {"message": "File upload endpoint", "status": "success"}

        # 搜索接口
        @self.app.post("/api/search")
        async def search_documents():
            """文档搜索接口"""
            return {"message": "Search endpoint", "status": "success"}

        # 知识图谱查询接口
        @self.app.get("/api/knowledge-graph")
        async def query_knowledge_graph():
            """知识图谱查询接口"""
            return {"message": "Knowledge graph query endpoint", "status": "success"}

        # 文件列表接口
        @self.app.get("/api/files")
        async def list_files():
            """获取文件列表"""
            return {"message": "File list endpoint", "status": "success"}

        # 文档检索接口
        @self.app.post("/api/retrieve")
        async def retrieve_documents():
            """文档检索接口"""
            return {"message": "Document retrieval endpoint", "status": "success"}

        # 主页面
        @self.app.get("/", response_class=HTMLResponse)
        async def read_root():
            """RAG系统主页面"""
            return self.templates.TemplateResponse(
                "rag-dashboard.html", {"request": {}}
            )

        # 知识图谱页面
        @self.app.get("/knowledge-graph", response_class=HTMLResponse)
        async def knowledge_graph_page():
            """知识图谱可视化页面"""
            return self.templates.TemplateResponse(
                "knowledge-graph.html", {"request": {}}
            )

        # 文件管理页面
        @self.app.get("/file-management", response_class=HTMLResponse)
        async def file_management_page():
            """文件管理页面"""
            return self.templates.TemplateResponse(
                "file-management.html", {"request": {}}
            )

        # 搜索界面
        @self.app.get("/search", response_class=HTMLResponse)
        async def search_interface():
            """搜索界面"""
            return self.templates.TemplateResponse(
                "search-interface.html", {"request": {}}
            )

        # 原始实现不自动包含外部 api routers
        # 尝试自动加载并包含外部定义的 API routers（例如 /rag, /file 等）
        try:
            # 延迟导入以避免循环依赖
            from web.api import get_api_routers

            routers = get_api_routers()
            if routers:
                for r in routers:
                    try:
                        self.app.include_router(r)
                        logger.info(
                            f"Included external router: {getattr(r, 'prefix', str(r))}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to include router {r}: {e}")
            else:
                logger.info("No external API routers found to include")
                # fallback: try loading rag-api.py directly (robust in app-dir context)
                try:
                    import importlib.util

                    api_path = os.path.join(
                        os.path.dirname(__file__), "api", "rag-api.py"
                    )
                    if os.path.exists(api_path):
                        spec = importlib.util.spec_from_file_location(
                            "web.api.rag_api", api_path
                        )
                        module = importlib.util.module_from_spec(spec)
                        module.__package__ = "web.api"
                        sys.modules["web.api.rag_api"] = module
                        spec.loader.exec_module(module)
                        if hasattr(module, "router"):
                            self.app.include_router(module.router)
                            logger.info(
                                "Included router from rag-api.py via direct load"
                            )
                except Exception as e:
                    logger.warning(f"Fallback direct load of rag-api.py failed: {e}")
        except Exception as e:
            logger.warning(f"Could not load external API routers: {e}")

    async def initialize_components(self):
        """异步初始化核心组件"""
        try:
            logger.info("Initializing RAG Web Application components...")

            # 创建共享配置
            shared_config = {
                "embedding_model": "text-embedding-ada-002",
                "embedding_dim": 1536,
                "similarity_threshold": 0.7,
                "max_results": 10,
            }

            # 初始化文件解析器
            self.file_parser = UniversalFileParser()
            self.file_parser.initialize()

            # 创建知识图谱配置
            kg_config = {
                "neo4j_uri": "bolt://localhost:7687",
                "neo4j_user": "neo4j",
                "neo4j_password": "password",
                "embedding_dim": shared_config["embedding_dim"],
                "similarity_threshold": shared_config["similarity_threshold"],
                "max_relationships_per_node": 50,
                "cache_size": 1000,
            }

            # 初始化知识图谱
            self.knowledge_graph = DynamicKnowledgeGraph(config=kg_config)
            await self.knowledge_graph.initialize()

            # 创建注入管道配置
            pipeline_config = {
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "max_file_size": 100 * 1024 * 1024,
                "supported_formats": [
                    ".pdf",
                    ".docx",
                    ".txt",
                    ".md",
                    ".html",
                    ".pptx",
                    ".xlsx",
                ],
                "batch_size": 10,
                "timeout": 300,
                "embedding_model": shared_config["embedding_model"],
            }

            # 初始化注入管道
            self.ingestion_pipeline = SmartIngestionPipeline(config=pipeline_config)
            await self.ingestion_pipeline.initialize()

            # 创建RAG引擎配置
            rag_config = {
                "retrieval_strategy": "hybrid",
                "rerank_enabled": True,
                "max_context_length": 4000,
                "temperature": 0.1,
                "embedding_model": shared_config["embedding_model"],
                "similarity_threshold": shared_config["similarity_threshold"],
                "max_results": shared_config["max_results"],
            }

            # 初始化RAG引擎 - 修复：传递完整的依赖关系和配置
            dependencies = {
                "file_parser": self.file_parser,
                "knowledge_graph": self.knowledge_graph,
                "ingestion_pipeline": self.ingestion_pipeline,
                "config": rag_config,
            }
            # 初始化并注入 RAG 引擎
            self.rag_engine = HybridRAGEngine()
            try:
                await self.rag_engine.initialize(dependencies)
            except Exception:
                logger.exception("RAG 引擎初始化失败")

            logger.info("RAG Web Application components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize RAG components: {str(e)}")
            raise

    def get_app(self):
        """获取FastAPI应用实例"""
        return self.app


# 创建应用实例
rag_web_app = RAGWebApp()
app = rag_web_app.get_app()


def main():
    """主运行函数"""
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
        access_log=True,
    )


if __name__ == "__main__":
    main()
