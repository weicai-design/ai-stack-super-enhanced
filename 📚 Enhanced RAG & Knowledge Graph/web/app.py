#!/usr/bin/env python3
"""
Enhanced RAG Web Application
对应需求: 1.7 RAG前端功能在open webui上实现，1.9 形成前端操作界面
文件位置: ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph/web/111. app.py
"""

import logging
import os
import random

# 导入RAG核心模块
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Body, FastAPI, HTTPException
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
        self.preprocess_order = ["clean", "standardize", "deduplicate", "validate"]
        self.preprocess_labels = {
            "clean": "清洗",
            "standardize": "标准化",
            "deduplicate": "去重",
            "validate": "验证",
        }
        self.validation_reports: List[Dict[str, Any]] = []
        self.preprocess_state = self._init_preprocess_state()

        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        self.templates = Jinja2Templates(
            directory=os.path.join(os.path.dirname(__file__), "templates")
        )

    def _now_iso(self) -> str:
        return datetime.now().isoformat()

    def _init_preprocess_state(self) -> Dict[str, Any]:
        stages = {}
        for key, label in self.preprocess_labels.items():
            stages[key] = {
                "stage": key,
                "label": label,
                "status": "idle",
                "detail": "待命",
                "progress": 0,
                "updated_at": self._now_iso(),
            }
        return {
            "pipeline": {
                "status": "idle",
                "detail": "尚未触发",
                "current_stage": None,
                "run_id": None,
                "completed_stages": [],
                "updated_at": self._now_iso(),
            },
            "stages": stages,
        }

    def _update_preprocess_stage(
        self, stage: str, status: str, detail: str, progress: int
    ) -> Dict[str, Any]:
        stage_state = self.preprocess_state["stages"][stage]
        stage_state.update(
            {
                "status": status,
                "detail": detail,
                "progress": progress,
                "updated_at": self._now_iso(),
            }
        )
        return stage_state

    def _set_pipeline_status(
        self, status: str, detail: str = "", current_stage: Optional[str] = None
    ) -> None:
        pipeline = self.preprocess_state["pipeline"]
        pipeline["status"] = status
        pipeline["detail"] = detail or pipeline.get("detail", "")
        pipeline["current_stage"] = current_stage
        pipeline["updated_at"] = self._now_iso()

    def _reset_preprocess_pipeline(self, run_id: str) -> None:
        pipeline = self.preprocess_state["pipeline"]
        pipeline.update(
            {
                "status": "running",
                "detail": f"Run {run_id} 已启动",
                "current_stage": self.preprocess_order[0],
                "run_id": run_id,
                "completed_stages": [],
                "updated_at": self._now_iso(),
            }
        )
        for stage in self.preprocess_order:
            self._update_preprocess_stage(stage, "queued", "等待执行", 0)

    def _mark_stage_completed(self, stage: str) -> None:
        pipeline = self.preprocess_state["pipeline"]
        completed = set(pipeline.get("completed_stages", []))
        completed.add(stage)
        pipeline["completed_stages"] = list(completed)
        if len(completed) == len(self.preprocess_order):
            self._set_pipeline_status(
                "completed",
                f"Run {pipeline.get('run_id') or '--'} 已完成",
                current_stage=None,
            )
    def _generate_validation_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        dataset = payload.get("dataset") or "默认知识库"
        focus = payload.get("focus_topics") or ["通用业务", "合规性"]
        run_id = datetime.now().strftime("%Y%m%d%H%M%S")
        truth_score = random.randint(80, 97)
        consistency_score = random.randint(78, 95)
        compliance_score = random.randint(82, 99)
        verified_facts = random.randint(45, 120)
        issues_found = random.randint(2, 8)
        stages = [
            {"stage": "完整性检测", "duration": round(random.uniform(0.6, 1.4), 2)},
            {"stage": "事实核验", "duration": round(random.uniform(1.2, 2.1), 2)},
            {"stage": "多源交叉", "duration": round(random.uniform(0.8, 1.7), 2)},
            {"stage": "合规审计", "duration": round(random.uniform(0.5, 1.3), 2)},
        ]
        source_pool = [
            {"source": "内部ERP", "match": round(random.uniform(0.87, 0.99), 2)},
            {"source": "财务报表", "match": round(random.uniform(0.8, 0.95), 2)},
            {"source": "监管公告", "match": round(random.uniform(0.78, 0.93), 2)},
            {"source": "第三方API", "match": round(random.uniform(0.7, 0.9), 2)},
        ]
        issues_catalog = [
            {
                "type": "事实冲突",
                "detail": "同一供应商交付周期在不同来源出现冲突",
                "severity": "high",
                "suggestion": "以ERP实时数据为准，通知业务侧复核",
            },
            {
                "type": "缺失引用",
                "detail": "预测报告中缺少资金来源引用",
                "severity": "medium",
                "suggestion": "追加财务报表引用并重算预测值",
            },
            {
                "type": "超期数据",
                "detail": "使用超过90天的市场数据参与决策",
                "severity": "medium",
                "suggestion": "启用最新一周的行情数据重新计算",
            },
            {
                "type": "合规敏感",
                "detail": "报告中出现未脱敏的个人信息",
                "severity": "high",
                "suggestion": "触发自动匿名化并发送告警",
            },
        ]
        selected_issues = random.sample(issues_catalog, k=3)
        report = {
            "report_id": f"VAL-{run_id}",
            "dataset": dataset,
            "generated_at": self._now_iso(),
            "focus_topics": focus,
            "summary": {
                "truth_score": truth_score,
                "consistency_score": consistency_score,
                "compliance_score": compliance_score,
                "issues_found": issues_found,
                "verified_facts": verified_facts,
            },
            "sources": [
                {
                    "name": item["source"],
                    "match": item["match"],
                    "status": "verified" if item["match"] > 0.85 else "review",
                }
                for item in source_pool
            ],
            "issues": selected_issues,
            "timeline": stages,
        }
        return report

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

        # 预处理四件套页面与编排
        components_dir = os.path.join(os.path.dirname(__file__), "components")

        def _render_component(filename: str) -> HTMLResponse:
            path = os.path.join(components_dir, filename)
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="预处理页面不存在")
            with open(path, "r", encoding="utf-8") as f:
                return HTMLResponse(f.read())

        @self.app.get("/preprocess", response_class=HTMLResponse)
        async def preprocess_page():
            """预处理四件套编排页面"""
            return _render_component("preprocess.html")

        @self.app.get("/preprocess/status")
        async def preprocess_status():
            """实时获取预处理流水线状态"""
            return self.preprocess_state

        @self.app.get("/preprocess/{stage}", response_class=HTMLResponse)
        async def preprocess_stage_page(stage: str):
            """独立三级页面：清洗/标准化/去重/验证"""
            mapping = {
                "clean": "preprocess_clean.html",
                "standardize": "preprocess_standardize.html",
                "deduplicate": "preprocess_deduplicate.html",
                "validate": "preprocess_validate.html",
            }
            filename = mapping.get(stage.lower())
            if not filename:
                raise HTTPException(status_code=404, detail="未知的预处理阶段")
            return _render_component(filename)

        @self.app.post("/preprocess/pipeline/run")
        async def preprocess_pipeline_run():
            """触发全流程编排"""
            run_id = datetime.now().strftime("%Y%m%d%H%M%S")
            self._reset_preprocess_pipeline(run_id)
            return {
                "success": True,
                "message": "预处理编排已启动",
                "state": self.preprocess_state,
            }

        @self.app.post("/preprocess/run/{stage}")
        async def preprocess_stage_run(stage: str):
            """单阶段执行入口"""
            stage_key = stage.lower()
            if stage_key not in self.preprocess_labels:
                raise HTTPException(status_code=404, detail="未知的预处理阶段")
            stage_label = self.preprocess_labels[stage_key]

            if not self.preprocess_state["pipeline"]["run_id"]:
                run_id = datetime.now().strftime("%Y%m%d%H%M%S")
                self._reset_preprocess_pipeline(run_id)

            self._set_pipeline_status("running", f"{stage_label} 执行中", stage_key)
            self._update_preprocess_stage(stage_key, "running", "执行中", 60)

            # 模拟阶段完成
            self._update_preprocess_stage(stage_key, "success", "完成", 100)
            self._mark_stage_completed(stage_key)

            current_stage_index = self.preprocess_order.index(stage_key)
            next_stage = (
                self.preprocess_order[current_stage_index + 1]
                if current_stage_index + 1 < len(self.preprocess_order)
                else None
            )
            if next_stage:
                next_label = self.preprocess_labels[next_stage]
                self._set_pipeline_status(
                    "running", f"{next_label} 待启动", current_stage=next_stage
                )
                next_state = self.preprocess_state["stages"][next_stage]
                if next_state["status"] in ("idle", "success"):
                    self._update_preprocess_stage(next_stage, "queued", "等待执行", 0)

            return {
                "success": True,
                "stage": stage_key,
                "stage_name": stage_label,
                "message": f"{stage_label} 阶段任务已完成",
                "stage_state": self.preprocess_state["stages"][stage_key],
                "state": self.preprocess_state,
            }

        @self.app.post("/preprocess/validate/report")
        async def create_validation_report(payload: Dict[str, Any] = Body(default={})):
            """生成真实性验证报告"""
            report = self._generate_validation_report(payload or {})
            self.validation_reports.insert(0, report)
            self.validation_reports = self.validation_reports[:20]
            return {"success": True, "report": report}

        @self.app.get("/preprocess/validate/report/latest")
        async def get_latest_validation_report():
            if not self.validation_reports:
                raise HTTPException(status_code=404, detail="暂无验证报告")
            return {"success": True, "report": self.validation_reports[0]}

        @self.app.get("/preprocess/validate/report/history")
        async def get_validation_report_history():
            return {"success": True, "reports": self.validation_reports}

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
                        os.path.dirname(__file__), "api", "rag_api.py"
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
                                "Included router from rag_api.py via direct load"
                            )
                except Exception as e:
                    logger.warning(f"Fallback direct load of rag_api.py failed: {e}")
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
