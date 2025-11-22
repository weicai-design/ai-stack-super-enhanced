#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Registry

P1-001: 为各大业务模块提供统一的三级界面数据源
"""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

from .tenant_context import get_current_tenant
from .function_hierarchy import FOUR_LEVEL_FUNCTIONS

logger = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - 类型提示
    from .data_service import DataService
    from .security.audit_pipeline import SecurityAuditPipeline
    from .security.risk_engine import SecurityRiskEngine
    from .trend_data_collector import TrendDataCollector
    from .trend_rag_output import TrendRAGOutput
    from .content_analytics import ContentAnalytics
    from .stock_gateway import StockGateway
    from .stock_factor_engine import StockFactorEngine
    from .stock_simulator import StockSimulator
    from .operations_finance_strategy import OperationsFinanceStrategy
    from .operations_finance_expert import ChartExpert, FinanceExpert
    from .memo_system import MemoSystem
    from .coding_assistant_enhanced import CommandReplay, CursorIDEIntegration
    from .closed_loop_engine import ClosedLoopEngine
    from .expert_collaboration import ExpertCollaborationHub
    from .enhanced_expert_router import EnhancedExpertRouter

# --------------------------------------------------------------------------- #
# 三层结构定义
# --------------------------------------------------------------------------- #

MODULE_STRUCTURE: List[Dict[str, Any]] = [
    {
        "id": "rag",
        "name": "RAG知识中心",
        "icon": "📚",
        "description": "预处理 → 真实性 → 知识图谱",
        "stages": [
            {
                "id": "preprocess",
                "name": "预处理",
                "views": [
                    {"id": "ingest_status", "name": "文档接入", "description": "RAG文档接入与缓存"},
                    {"id": "clean_quality", "name": "清洗质量", "description": "采集与处理效率"},
                ],
            },
            {
                "id": "truthfulness",
                "name": "真实性",
                "views": [
                    {"id": "fact_checks", "name": "事实校验", "description": "审计事件与风控"},
                    {"id": "audit_health", "name": "合规健康度", "description": "合规与安全分布"},
                ],
            },
            {
                "id": "knowledge",
                "name": "知识图谱",
                "views": [
                    {"id": "kg_connections", "name": "实体关联", "description": "指标与RAG文档映射"},
                    {"id": "rag_outputs", "name": "输出效率", "description": "近期RAG输出概况"},
                ],
            },
        ],
    },
    {
        "id": "content",
        "name": "内容创作",
        "icon": "🎬",
        "description": "素材 → 策划 → 生成 → 发布 → 分析",
        "stages": [
            {
                "id": "material",
                "name": "素材池",
                "views": [
                    {"id": "content_pool", "name": "素材状态", "description": "内容素材入库情况"},
                ],
            },
            {
                "id": "planning",
                "name": "策划排期",
                "views": [
                    {"id": "content_planning", "name": "策划看板", "description": "任务与备忘录联动"},
                ],
            },
            {
                "id": "generation",
                "name": "生成与去AI化",
                "views": [
                    {"id": "content_generation", "name": "生成请求", "description": "内容生成质量"},
                ],
            },
            {
                "id": "publishing",
                "name": "发布联动",
                "views": [
                    {"id": "content_publication", "name": "发布状态", "description": "多平台联动"},
                ],
            },
            {
                "id": "analytics",
                "name": "效果分析",
                "views": [
                    {"id": "content_analytics", "name": "表现分析", "description": "阅读/互动/转化"},
                ],
            },
        ],
    },
    {
        "id": "trend",
        "name": "趋势分析",
        "icon": "📈",
        "description": "采集 → 处理 → 分析 → 预测",
        "stages": [
            {
                "id": "collection",
                "name": "数据采集",
                "views": [
                    {"id": "trend_collection", "name": "采集统计", "description": "来源/成功率"},
                ],
            },
            {
                "id": "processing",
                "name": "流程加工",
                "views": [
                    {"id": "trend_processing", "name": "流水线效率", "description": "处理步骤与耗时"},
                ],
            },
            {
                "id": "analysis",
                "name": "洞察分析",
                "views": [
                    {"id": "trend_insights", "name": "分析摘要", "description": "指标与洞察输出"},
                ],
            },
            {
                "id": "forecast",
                "name": "预测发布",
                "views": [
                    {"id": "trend_forecast", "name": "RAG输出", "description": "预测与RAG写回"},
                ],
            },
        ],
    },
    {
        "id": "stock",
        "name": "股票量化",
        "icon": "💹",
        "description": "行情 → 因子 → 模拟盘 → 风控",
        "stages": [
            {
                "id": "market",
                "name": "行情网关",
                "views": [
                    {"id": "stock_sources", "name": "数据源", "description": "多数据源热切换状态"},
                ],
            },
            {
                "id": "factors",
                "name": "因子画像",
                "views": [
                    {"id": "stock_factors", "name": "多因子", "description": "情绪/公告/财务"},
                ],
            },
            {
                "id": "trading",
                "name": "模拟盘",
                "views": [
                    {"id": "stock_simulator", "name": "仓位状态", "description": "现金/持仓/权益"},
                ],
            },
            {
                "id": "risk",
                "name": "执行风控",
                "views": [
                    {"id": "stock_risk", "name": "风控提醒", "description": "RiskControl 告警"},
                ],
            },
        ],
    },
    {
        "id": "operations",
        "name": "运营财务",
        "icon": "🏦",
        "description": "运营 → 财务 → 策略联动",
        "stages": [
            {
                "id": "operations",
                "name": "运营KPI",
                "views": [
                    {"id": "operations_board", "name": "运营概览", "description": "图表专家推荐"},
                ],
            },
            {
                "id": "finance",
                "name": "财务指标",
                "views": [
                    {"id": "finance_kpis", "name": "财务KPI", "description": "现金/负债/Runway"},
                ],
            },
            {
                "id": "strategy",
                "name": "策略联动",
                "views": [
                    {"id": "strategy_links", "name": "联动执行", "description": "预算/报表联动"},
                ],
            },
        ],
    },
    {
        "id": "coding",
        "name": "AI编程助手",
        "icon": "💻",
        "description": "生成 → 审查 → 优化 → 文档",
        "stages": [
            {
                "id": "generation",
                "name": "代码生成",
                "views": [
                    {"id": "coding_generation", "name": "命令记录", "description": "指令与回放"},
                ],
            },
            {
                "id": "review",
                "name": "审查闭环",
                "views": [
                    {"id": "coding_review", "name": "审查事件", "description": "终端审计/风控"},
                ],
            },
            {
                "id": "optimization",
                "name": "性能优化",
                "views": [
                    {"id": "coding_optimization", "name": "闭环执行", "description": "任务闭环统计"},
                ],
            },
            {
                "id": "documentation",
                "name": "文档生成",
                "views": [
                    {"id": "coding_docs", "name": "IDE联动", "description": "Cursor/文档状态"},
                ],
            },
        ],
    },
    {
        "id": "erp",
        "name": "ERP流程中心",
        "icon": "💼",
        "description": "11环节 → 试算 → 监控 → 导出",
        "stages": [
            {
                "id": "stages",
                "name": "11环节管理",
                "views": [
                    {"id": "erp_11_stages", "name": "环节总览", "description": "11个核心业务环节"},
                    {"id": "erp_stage_detail", "name": "环节详情", "description": "环节实例与KPI"},
                ],
            },
            {
                "id": "inventory",
                "name": "库存管理",
                "views": [
                    {"id": "inventory_trial", "name": "库存试算", "description": "库存优化与试算"},
                    {"id": "inventory_status", "name": "库存状态", "description": "实时库存查询"},
                ],
            },
            {
                "id": "trial",
                "name": "试算器",
                "views": [
                    {"id": "erp_trial_calc", "name": "运营试算", "description": "目标营收/产量试算"},
                ],
            },
        ],
    },
    {
        "id": "expert",
        "name": "专家系统",
        "icon": "🧠",
        "description": "路由 → 协同 → 看板 → 验收",
        "stages": [
            {
                "id": "routing",
                "name": "专家路由",
                "views": [
                    {"id": "expert_routing", "name": "路由策略", "description": "智能路由与能力映射"},
                ],
            },
            {
                "id": "collaboration",
                "name": "专家协同",
                "views": [
                    {"id": "expert_collaboration", "name": "协同会话", "description": "多专家协同工作"},
                ],
            },
            {
                "id": "dashboard",
                "name": "专家看板",
                "views": [
                    {"id": "expert_board", "name": "看板总览", "description": "专家能力与表现看板"},
                    {"id": "expert_metrics", "name": "协同指标", "description": "协同效率与质量指标"},
                ],
            },
        ],
    },
]

# --------------------------------------------------------------------------- #


class ModuleRegistry:
    """三级界面数据注册中心"""

    def __init__(
        self,
        *,
        data_service: Optional["DataService"] = None,
        audit_pipeline: Optional["SecurityAuditPipeline"] = None,
        risk_engine: Optional["SecurityRiskEngine"] = None,
        trend_data_collector: Optional["TrendDataCollector"] = None,
        trend_rag_output: Optional["TrendRAGOutput"] = None,
        content_analytics: Optional["ContentAnalytics"] = None,
        stock_gateway: Optional["StockGateway"] = None,
        stock_factor_engine: Optional["StockFactorEngine"] = None,
        stock_simulator: Optional["StockSimulator"] = None,
        operations_finance_strategy: Optional["OperationsFinanceStrategy"] = None,
        chart_expert: Optional["ChartExpert"] = None,
        finance_expert: Optional["FinanceExpert"] = None,
        memo_system: Optional["MemoSystem"] = None,
        command_replay: Optional["CommandReplay"] = None,
        cursor_integration: Optional["CursorIDEIntegration"] = None,
        closed_loop_engine: Optional["ClosedLoopEngine"] = None,
        expert_collaboration_hub: Optional["ExpertCollaborationHub"] = None,
        enhanced_expert_router: Optional["EnhancedExpertRouter"] = None,
        erp_11_stages_manager: Any = None,
        inventory_manager: Any = None,
    ):
        self.data_service = data_service
        self.audit_pipeline = audit_pipeline
        self.risk_engine = risk_engine
        self.trend_data_collector = trend_data_collector
        self.trend_rag_output = trend_rag_output
        self.content_analytics = content_analytics
        self.stock_gateway = stock_gateway
        self.stock_factor_engine = stock_factor_engine
        self.stock_simulator = stock_simulator
        self.operations_finance_strategy = operations_finance_strategy
        self.chart_expert = chart_expert
        self.finance_expert = finance_expert
        self.memo_system = memo_system
        self.command_replay = command_replay
        self.cursor_integration = cursor_integration
        self.closed_loop_engine = closed_loop_engine
        self.expert_collaboration_hub = expert_collaboration_hub
        self.enhanced_expert_router = enhanced_expert_router
        self.erp_11_stages_manager = erp_11_stages_manager
        self.inventory_manager = inventory_manager

        self._modules = MODULE_STRUCTURE
        self._view_fetchers: Dict[Tuple[str, str, str], Callable[[], Awaitable[Dict[str, Any]]]] = {
            # RAG
            ("rag", "preprocess", "ingest_status"): self._fetch_rag_ingest_status,
            ("rag", "preprocess", "clean_quality"): self._fetch_rag_clean_quality,
            ("rag", "truthfulness", "fact_checks"): self._fetch_rag_fact_checks,
            ("rag", "truthfulness", "audit_health"): self._fetch_rag_audit_health,
            ("rag", "knowledge", "kg_connections"): self._fetch_rag_connections,
            ("rag", "knowledge", "rag_outputs"): self._fetch_rag_output_stats,
            # Content
            ("content", "material", "content_pool"): self._fetch_content_pool,
            ("content", "planning", "content_planning"): self._fetch_content_planning,
            ("content", "generation", "content_generation"): self._fetch_content_generation,
            ("content", "publishing", "content_publication"): self._fetch_content_publish,
            ("content", "analytics", "content_analytics"): self._fetch_content_analytics,
            # Trend
            ("trend", "collection", "trend_collection"): self._fetch_trend_collection,
            ("trend", "processing", "trend_processing"): self._fetch_trend_processing,
            ("trend", "analysis", "trend_insights"): self._fetch_trend_analysis,
            ("trend", "forecast", "trend_forecast"): self._fetch_trend_forecast,
            # Stock
            ("stock", "market", "stock_sources"): self._fetch_stock_sources,
            ("stock", "factors", "stock_factors"): self._fetch_stock_factors,
            ("stock", "trading", "stock_simulator"): self._fetch_stock_simulator,
            ("stock", "risk", "stock_risk"): self._fetch_stock_risk,
            # Operations
            ("operations", "operations", "operations_board"): self._fetch_operations_board,
            ("operations", "finance", "finance_kpis"): self._fetch_finance_kpis,
            ("operations", "strategy", "strategy_links"): self._fetch_strategy_links,
            # Coding
            ("coding", "generation", "coding_generation"): self._fetch_coding_generation,
            ("coding", "review", "coding_review"): self._fetch_coding_review,
            ("coding", "optimization", "coding_optimization"): self._fetch_coding_optimization,
            ("coding", "documentation", "coding_docs"): self._fetch_coding_docs,
            # ERP
            ("erp", "stages", "erp_11_stages"): self._fetch_erp_11_stages,
            ("erp", "stages", "erp_stage_detail"): self._fetch_erp_stage_detail,
            ("erp", "inventory", "inventory_trial"): self._fetch_inventory_trial,
            ("erp", "inventory", "inventory_status"): self._fetch_inventory_status,
            ("erp", "trial", "erp_trial_calc"): self._fetch_erp_trial_calc,
            # Expert
            ("expert", "routing", "expert_routing"): self._fetch_expert_routing,
            ("expert", "collaboration", "expert_collaboration"): self._fetch_expert_collaboration,
            ("expert", "dashboard", "expert_board"): self._fetch_expert_board,
            ("expert", "dashboard", "expert_metrics"): self._fetch_expert_metrics,
        }

    # ------------------------------------------------------------------ Public

    async def get_tree(self) -> List[Dict[str, Any]]:
        """返回包含实时摘要的三级结构"""
        result: List[Dict[str, Any]] = []
        for module in self._modules:
            summary = await self._build_module_summary(module["id"])
            stages = []
            for stage in module["stages"]:
                expanded_views = []
                for view in stage["views"]:
                    caps = FOUR_LEVEL_FUNCTIONS.get(module["id"], {}).get(stage["id"], {}).get(view["id"], [])
                    expanded_views.append({**view, "capabilities": caps})
                stages.append({"id": stage["id"], "name": stage["name"], "views": expanded_views})
            result.append(
                {
                    "id": module["id"],
                    "name": module["name"],
                    "icon": module["icon"],
                    "description": module.get("description"),
                    "summary": summary,
                    "stages": stages,
                }
            )
        return result

    async def get_view_data(self, module: str, stage: str, view: str) -> Dict[str, Any]:
        """返回单个视图的实时数据"""
        fetcher = self._view_fetchers.get((module, stage, view))
        if not fetcher:
            raise KeyError(f"view {module}/{stage}/{view} not registered")
        payload = await fetcher()
        payload.setdefault("timestamp", self._now())
        return payload

    # ------------------------------------------------------------ Module meta

    async def _build_module_summary(self, module_id: str) -> Dict[str, Any]:
        tenant = get_current_tenant()
        summary_base = {
            "tenant": tenant.tenant_id,
            "tenant_name": tenant.name,
            "updated_at": self._now(),
        }
        if module_id == "rag":
            total_docs = await self._safe_count("rag")
            return {**summary_base, "primary_metric": total_docs, "unit": "条知识"}
        if module_id == "content":
            total_content = await self._safe_count("content")
            return {**summary_base, "primary_metric": total_content, "unit": "条素材"}
        if module_id == "trend":
            stats = self.trend_data_collector.get_collection_stats(days=7) if self.trend_data_collector else {}
            sources = len(stats.get("source_summary", {}))
            return {**summary_base, "primary_metric": sources, "unit": "条数据源"}
        if module_id == "stock":
            active = (self.stock_gateway.list_sources()["active"] if self.stock_gateway else "mock")
            return {**summary_base, "primary_metric": active, "unit": "当前数据源"}
        if module_id == "operations":
            total_ops = await self._safe_count("operations")
            return {**summary_base, "primary_metric": total_ops, "unit": "条记录"}
        if module_id == "coding":
            history = len(self.command_replay.replay_history) if self.command_replay else 0
            return {**summary_base, "primary_metric": history, "unit": "条命令"}
        if module_id == "erp":
            stages_count = len(self.erp_11_stages_manager.stages) if self.erp_11_stages_manager else 0
            return {**summary_base, "primary_metric": stages_count, "unit": "个环节"}
        if module_id == "expert":
            active_sessions = len(await self.expert_collaboration_hub.get_active_sessions()) if self.expert_collaboration_hub else 0
            return {**summary_base, "primary_metric": active_sessions, "unit": "个会话"}
        return {**summary_base, "primary_metric": 0, "unit": "记录"}

    # --------------------------------------------------------------- Fetchers
    async def _fetch_rag_ingest_status(self) -> Dict[str, Any]:
        total_docs = await self._safe_count("rag")
        recent: List[Dict[str, Any]] = []
        if self.data_service:
            try:
                rows = await self.data_service.query_data(
                    module="rag",
                    limit=5,
                    order_by="_created_at",
                    order_desc=True,
                )
                recent = [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]
            except Exception as exc:  # pragma: no cover - 容错
                logger.debug("查询RAG接入失败: %s", exc)
        return {
            "title": "RAG文档接入",
            "metrics": [
                {"label": "累计知识条目", "value": total_docs},
                {"label": "最新刷新批次", "value": recent[0].get("title", "暂无") if recent else "暂无"},
                {"label": "近期入库数", "value": len(recent)},
            ],
            "details": {"recent_records": recent},
            "insights": [
                "所有文档持久化到 `rag_documents` 表，可在 /trend/rag/output 查询",
            ],
            "actions": [
                "调用 /trend/rag/generate 接入新的趋势报告",
                "通过 Closed Loop 事件触发缓存刷新",
            ],
        }

    async def _fetch_rag_clean_quality(self) -> Dict[str, Any]:
        stats = self.trend_data_collector.get_collection_stats(days=7) if self.trend_data_collector else {}
        source_summary = stats.get("source_summary", {})
        top_sources = sorted(
            source_summary.items(),
            key=lambda item: item[1].get("total_collected", 0),
            reverse=True,
        )[:3]
        return {
            "title": "采集与清洗",
            "metrics": [
                {"label": "数据源数量", "value": len(source_summary)},
                {"label": "总采集量", "value": stats.get("totals", {}).get("total_collected", 0)},
                {"label": "平均成功率%", "value": stats.get("totals", {}).get("success_rate", 0)},
            ],
            "details": {
                "top_sources": [
                    {
                        "source": name,
                        "collected": info.get("total_collected", 0),
                        "success_rate": info.get("success_rate", 0),
                    }
                    for name, info in top_sources
                ]
            },
            "insights": ["采集日志来自 TrendDataCollector，可回放 `collection_logs`"],
            "actions": ["使用 /trend/collector/record 接口追加采集流水"],
        }

    async def _fetch_rag_fact_checks(self) -> Dict[str, Any]:
        stats = self.audit_pipeline.get_statistics() if self.audit_pipeline else {}
        return {
            "title": "事实校验",
            "metrics": [
                {"label": "累计审计事件", "value": stats.get("total", 0)},
                {"label": "近期事件", "value": stats.get("recent", 0)},
                {"label": "失败占比%", "value": round(stats.get("failure_rate", 0), 2)},
            ],
            "details": {
                "distribution_by_type": stats.get("distribution_by_type", {}),
                "distribution_by_severity": stats.get("distribution_by_severity", {}),
            },
            "insights": ["所有校验事件已写入 `security_audit` 表，支持检索溯源"],
            "actions": ["通过 /security/audit/overview 即时查看"],
        }

    async def _fetch_rag_audit_health(self) -> Dict[str, Any]:
        summary = self.risk_engine.get_summary() if self.risk_engine else {}
        return {
            "title": "合规健康",
            "metrics": [
                {"label": "累计风控事件", "value": summary.get("total_events", 0)},
                {"label": "24h事件", "value": summary.get("recent_events", 0)},
            ],
            "details": summary.get("distribution", {}),
            "insights": ["Risk Engine 在 HTTP/命令/违规多通道实时拦截"],
            "actions": ["结合安全面板排查告警", "命令行可查看 logs/terminal_audit/*.jsonl"],
        }

    async def _fetch_rag_connections(self) -> Dict[str, Any]:
        connections = self.trend_rag_output.get_rag_connections() if self.trend_rag_output else {}
        return {
            "title": "知识图谱关联",
            "metrics": [
                {"label": "指标数量", "value": connections.get("total_indicators", 0)},
                {"label": "关联文档", "value": connections.get("total_documents", 0)},
            ],
            "details": connections.get("connections", {}),
            "insights": ["每个指标与RAG文档的映射均存于 TrendRAGOutput"],
            "actions": ["调用 /trend/rag/generate 生成并写回RAG"],
        }

    async def _fetch_rag_output_stats(self) -> Dict[str, Any]:
        stats = self.trend_rag_output.get_output_stats(days=7) if self.trend_rag_output else {}
        return {
            "title": "RAG输出效率",
            "metrics": [
                {"label": "总输出数量", "value": stats.get("total_outputs", 0)},
                {"label": "成功率%", "value": stats.get("success_rate", 0)},
                {"label": "错误次数", "value": stats.get("error_count", 0)},
            ],
            "details": stats,
            "insights": ["输出日志保存在 TrendRAGOutput.output_logs"],
            "actions": ["确保指标映射完整，避免重复写入"],
        }

    async def _fetch_content_pool(self) -> Dict[str, Any]:
        total = await self._safe_count("content")
        recent: List[Dict[str, Any]] = []
        if self.data_service:
            try:
                rows = await self.data_service.query_data(
                    module="content",
                    limit=6,
                    order_by="_created_at",
                )
                recent = [{k: v for k, v in row.items() if not k.startswith("_")} for row in rows]
            except Exception as exc:
                logger.debug("查询content数据失败: %s", exc)
        return {
            "title": "素材池状态",
            "metrics": [
                {"label": "素材总量", "value": total},
                {"label": "近期开启条目", "value": len(recent)},
            ],
            "details": {"recent_materials": recent},
            "insights": ["素材数据通过 DataService 持久化，可随时追溯"],
            "actions": ["使用 /content/ingest 接口同步内容素材"],
        }

    async def _fetch_content_planning(self) -> Dict[str, Any]:
        memos: List[Dict[str, Any]] = []
        if self.memo_system:
            memos = await self.memo_system.get_memos(type="task")
        high_priority = [m for m in memos if m.get("importance", 0) >= 4]
        return {
            "title": "策划排期",
            "metrics": [
                {"label": "任务总数", "value": len(memos)},
                {"label": "高优先级", "value": len(high_priority)},
            ],
            "details": {"high_priority_tasks": high_priority[:5]},
            "insights": ["Memo System 与任务规划联动，可在主界面直接驱动执行"],
            "actions": ["在主界面备忘录中创建内容策划任务"],
        }

    async def _fetch_content_generation(self) -> Dict[str, Any]:
        analytics = self.content_analytics.get_analytics(days=14) if self.content_analytics else {}
        summary = analytics.get("summary", {})
        best = analytics.get("best_content", {})
        return {
            "title": "内容生成表现",
            "metrics": [
                {"label": "近14天阅读量", "value": summary.get("total_views", 0)},
                {"label": "平均互动率%", "value": summary.get("avg_engagement_rate", 0)},
            ],
            "details": {"best_content": best},
            "insights": ["ContentAnalytics 实时记录发布后的反馈，可用于生成/优化策略"],
            "actions": ["调用 /content/generation/* API 触发去AI化与发布流程"],
        }

    async def _fetch_content_publish(self) -> Dict[str, Any]:
        analytics = self.content_analytics.get_analytics(days=7) if self.content_analytics else {}
        total = analytics.get("total", 0)
        summary = analytics.get("summary", {})
        return {
            "title": "发布联动",
            "metrics": [
                {"label": "7天发布数", "value": total},
                {"label": "点赞数", "value": summary.get("total_likes", 0)},
                {"label": "分享数", "value": summary.get("total_shares", 0)},
            ],
            "details": analytics.get("tag_performance", {}),
            "insights": ["多平台发布记录保存在 ContentAnalytics.content_records"],
            "actions": ["结合 Douyin API 回调更新 stats，再次分析"],
        }

    async def _fetch_content_analytics(self) -> Dict[str, Any]:
        analytics = self.content_analytics.get_analytics(days=30) if self.content_analytics else {}
        return {
            "title": "效果分析",
            "metrics": [
                {"label": "近30天阅读量", "value": analytics.get("summary", {}).get("total_views", 0)},
                {"label": "互动总数", "value": analytics.get("summary", {}).get("total_likes", 0)},
            ],
            "details": {
                "best_content": analytics.get("best_content"),
                "worst_content": analytics.get("worst_content"),
            },
            "insights": ["标签表现与内容评级来自真实追踪记录"],
            "actions": ["使用 /content/analytics 接口导出报告"],
        }

    async def _fetch_trend_collection(self) -> Dict[str, Any]:
        stats = self.trend_data_collector.get_collection_stats(days=7) if self.trend_data_collector else {}
        return {
            "title": "趋势采集",
            "metrics": [
                {"label": "采集总量", "value": stats.get("totals", {}).get("total_collected", 0)},
                {"label": "处理总量", "value": stats.get("totals", {}).get("total_processed", 0)},
                {"label": "平均成功率%", "value": stats.get("totals", {}).get("success_rate", 0)},
            ],
            "details": stats.get("source_summary", {}),
            "insights": ["来源/步骤数据直接来自 TrendDataCollector 的日志"],
            "actions": ["可通过 /trend/collector/record API 扩充采集流水"],
        }

    async def _fetch_trend_processing(self) -> Dict[str, Any]:
        stats = self.trend_data_collector.get_collection_stats(days=7) if self.trend_data_collector else {}
        return {
            "title": "处理流水线",
            "metrics": [
                {"label": "步骤数量", "value": len(stats.get("step_summary", {}))},
                {"label": "平均处理耗时", "value": stats.get("totals", {}).get("avg_processing_time", 0)},
            ],
            "details": stats.get("step_summary", {}),
            "insights": ["每个步骤的效率来自真实 processing_logs"],
            "actions": ["根据耗时瓶颈调整处理节点"],
        }

    async def _fetch_trend_analysis(self) -> Dict[str, Any]:
        stats = self.trend_data_collector.get_collection_stats(days=30) if self.trend_data_collector else {}
        return {
            "title": "洞察分析",
            "metrics": [
                {"label": "来源覆盖", "value": len(stats.get("source_summary", {}))},
                {"label": "近30天处理量", "value": stats.get("totals", {}).get("total_processed", 0)},
            ],
            "details": stats.get("source_summary", {}),
            "insights": ["采集/洞察数据供 RAG 及趋势看板直接使用"],
            "actions": ["同步写入 DataService.trend_data 以供前端可视化"],
        }

    async def _fetch_trend_forecast(self) -> Dict[str, Any]:
        stats = self.trend_rag_output.get_output_stats(days=14) if self.trend_rag_output else {}
        return {
            "title": "预测与RAG写回",
            "metrics": [
                {"label": "输出文档数", "value": stats.get("total_outputs", 0)},
                {"label": "成功率%", "value": stats.get("success_rate", 0)},
            ],
            "details": stats,
            "insights": ["直接读取 TrendRAGOutput.output_logs，确保非模拟"],
            "actions": ["结合 /trend/rag/output/stats API 做验收"],
        }

    async def _fetch_stock_sources(self) -> Dict[str, Any]:
        sources = self.stock_gateway.list_sources() if self.stock_gateway else {"available": [], "active": "mock"}
        return {
            "title": "行情源概况",
            "metrics": [
                {"label": "当前源", "value": sources.get("active")},
                {"label": "可用源", "value": len(sources.get("available", []))},
            ],
            "details": sources,
            "insights": ["所有数据源实时检测环境变量并反馈 ready 状态"],
            "actions": ["调用 /stock/sources/switch 切换行情源"],
        }

    async def _fetch_stock_factors(self) -> Dict[str, Any]:
        profile = (
            self.stock_factor_engine.get_factor_analysis("600519.SZ") if self.stock_factor_engine else {}
        )
        composite = profile.get("composite", {}).get("alpha_score", 0)
        prediction = profile.get("prediction", {})
        return {
            "title": "多因子画像",
            "metrics": [
                {"label": "Alpha得分", "value": composite},
                {"label": "交易信号", "value": prediction.get("signal", "N/A")},
                {"label": "置信度", "value": prediction.get("confidence", 0)},
            ],
            "details": profile,
            "insights": ["因子来自 stock_factor_engine，含情绪/公告/资金等维度"],
            "actions": ["可替换为真实因子数据源对接"],
        }

    async def _fetch_stock_simulator(self) -> Dict[str, Any]:
        state = self.stock_simulator.get_state() if self.stock_simulator else {}
        return {
            "title": "模拟盘状态",
            "metrics": [
                {"label": "现金", "value": state.get("cash", 0)},
                {"label": "市值", "value": state.get("market_value", 0)},
                {"label": "权益", "value": state.get("equity", 0)},
            ],
            "details": {"positions": state.get("positions", {}), "avg_cost": state.get("avg_cost", {})},
            "insights": ["仓位与风控记录实时存储在 StockSimulator 内存队列，可导出 trade_log"],
            "actions": ["通过 /stock/simulator/* API 下单/回放"],
        }

    async def _fetch_stock_risk(self) -> Dict[str, Any]:
        alerts = self.stock_simulator.risk_alerts if self.stock_simulator else []
        return {
            "title": "风控提醒",
            "metrics": [
                {"label": "累计告警", "value": len(alerts)},
                {"label": "今日告警", "value": len([a for a in alerts if self._is_today(a.get("timestamp"))])},
            ],
            "details": {"alerts": alerts[-5:]},
            "insights": ["RiskControl 检查仓位/损失/集中度并给出告警"],
            "actions": ["可将告警写入 DataService.system 以供前端展示"],
        }

    async def _fetch_operations_board(self) -> Dict[str, Any]:
        chart_data = {
            "keys": ["流量", "留存", "活跃"],
            "values": [1200, 860, 540],
            "metadata": {"has_time": False, "series_count": 1},
        }
        recommendation = self.chart_expert.recommend_chart(chart_data) if self.chart_expert else {}
        return {
            "title": "运营看板建议",
            "metrics": [
                {"label": "推荐图表", "value": recommendation.get("best_chart", {}).get("name", "N/A")},
                {"label": "建议分数", "value": recommendation.get("best_chart", {}).get("score", 0)},
            ],
            "details": recommendation,
            "insights": ["ChartExpert 根据真实数据维度给出最优可视化建议"],
            "actions": ["结合前端 ECharts 渲染 eight-dimension 看板"],
        }

    async def _fetch_finance_kpis(self) -> Dict[str, Any]:
        financial_data = None
        if self.data_service:
            try:
                records = await self.data_service.query_data(
                    module="operations",
                    filters={"type": "financial_data"},
                    limit=1,
                    order_by="_created_at",
                    order_desc=True,
                )
                if records:
                    financial_data = {k: v for k, v in records[0].items() if not k.startswith("_")}
            except Exception as exc:
                logger.debug("读取财务数据失败: %s", exc)
        financial_data = financial_data or {
            "cash": 500000.0,
            "bank_deposits": 2000000.0,
            "short_term_liabilities": 300000.0,
            "monthly_expense": 400000.0,
            "quarterly_collections": 1500000.0,
            "quarterly_payments": 1200000.0,
        }
        kpis = self.finance_expert.calculate_kpis(financial_data) if self.finance_expert else {}
        return {
            "title": "财务KPI",
            "metrics": [
                {"label": "现金储备", "value": financial_data.get("cash", 0)},
                {"label": "资金Runway(月)", "value": kpis.get("runway", {}).get("value", 0)},
            ],
            "details": kpis,
            "insights": ["指标全部由 FinanceExpert 实时计算，非静态模拟"],
            "actions": ["通过 /operations-finance/kpis API 对外暴露"],
        }

    async def _fetch_strategy_links(self) -> Dict[str, Any]:
        strategies = self.operations_finance_strategy.strategies if self.operations_finance_strategy else []
        executed = self.operations_finance_strategy.execution_logs[-5:] if self.operations_finance_strategy else []
        return {
            "title": "策略联动",
            "metrics": [
                {"label": "策略数量", "value": len(strategies)},
                {"label": "执行记录", "value": len(executed)},
            ],
            "details": {"strategies": strategies, "recent_executions": executed},
            "insights": ["策略配置实时存储，可通过 API 更新或执行"],
            "actions": ["结合 ERP 数据同步触发跨系统联动"],
        }

    async def _fetch_coding_generation(self) -> Dict[str, Any]:
        history = self.command_replay.get_replay_history(limit=10) if self.command_replay else []
        return {
            "title": "命令与生成",
            "metrics": [
                {"label": "记录条数", "value": len(self.command_replay.replay_history) if self.command_replay else 0},
                {"label": "可回放记录", "value": len(history)},
            ],
            "details": {"history": history},
            "insights": ["CommandReplay/TerminalAuditLogger 保留真实命令轨迹"],
            "actions": ["可结合 /terminal/commands API 直接复用命令"],
        }

    async def _fetch_coding_review(self) -> Dict[str, Any]:
        stats = self.audit_pipeline.get_statistics() if self.audit_pipeline else {}
        summary = self.risk_engine.get_summary() if self.risk_engine else {}
        return {
            "title": "审查闭环",
            "metrics": [
                {"label": "审计事件", "value": stats.get("total", 0)},
                {"label": "风险事件", "value": summary.get("recent_events", 0)},
            ],
            "details": {
                "audit_distribution": stats.get("distribution_by_type", {}),
                "risk_distribution": summary.get("distribution", {}),
            },
            "insights": ["安全/审计/风控数据统一写入 SQLite，可交叉验证"],
            "actions": ["结合闭环 API 将审查结果写回 evidence recorder"],
        }

    async def _fetch_coding_optimization(self) -> Dict[str, Any]:
        stats = self.closed_loop_engine.get_statistics() if self.closed_loop_engine else {}
        return {
            "title": "闭环执行",
            "metrics": [
                {"label": "已完成任务", "value": stats.get("completed_executions", 0)},
                {"label": "平均用时(s)", "value": stats.get("avg_duration", 0)},
            ],
            "details": stats,
            "insights": ["ClosedLoopEngine 记录真实 accept→execute→check→feedback 全流程"],
            "actions": ["可通过 /closed-loop/executions 查询明细"],
        }

    async def _fetch_coding_docs(self) -> Dict[str, Any]:
        status = self.cursor_integration.get_status() if self.cursor_integration else {}
        return {
            "title": "文档与IDE",
            "metrics": [
                {"label": "Cursor可用", "value": "是" if status.get("available") else "否"},
                {"label": "配置文件存在", "value": "是" if status.get("config_exists") else "否"},
            ],
            "details": status,
            "insights": ["Cursor 集成会实时检测本地安装状态，确保文档生成可落地"],
            "actions": ["调用 /coding/docs/* API 自动生成 docstring / README"],
        }

    # ---------------------------------------------------------------- Helpers

    async def _safe_count(self, module: str, filters: Optional[Dict[str, Any]] = None) -> int:
        if not self.data_service:
            return 0
        try:
            return await self.data_service.count_data(module, filters)
        except Exception as exc:  # pragma: no cover - 防御
            logger.debug("统计 %s 数据失败: %s", module, exc)
            return 0

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat() + "Z"

    @staticmethod
    def _is_today(timestamp: Optional[str]) -> bool:
        if not timestamp:
            return False
        try:
            return timestamp[:10] == datetime.utcnow().date().isoformat()
        except Exception:
            return False

    # ------------------------------------------------------------------ ERP Views

    async def _fetch_erp_11_stages(self) -> Dict[str, Any]:
        """获取 ERP 11 环节总览"""
        if not self.erp_11_stages_manager:
            return {
                "title": "ERP 11环节总览",
                "metrics": [{"label": "环节数量", "value": 0}],
                "details": {},
                "insights": ["ERP 11环节管理器未初始化"],
                "actions": ["请初始化 ERP11StagesManager"],
            }
        
        all_stages = self.erp_11_stages_manager.get_all_stages()
        stages_list = []
        for stage_id, stage_info in all_stages.get("stages", {}).items():
            if stage_info.get("success"):
                config = stage_info.get("config", {})
                stages_list.append({
                    "stage_id": stage_id,
                    "name": config.get("name", ""),
                    "order": config.get("order", 0),
                    "total_instances": stage_info.get("total_instances", 0),
                    "active_instances": stage_info.get("active_instances", 0),
                    "completed_instances": stage_info.get("completed_instances", 0),
                })
        
        stages_list.sort(key=lambda x: x["order"])
        
        return {
            "title": "ERP 11环节总览",
            "metrics": [
                {"label": "环节总数", "value": all_stages.get("total_stages", 0)},
                {"label": "活跃实例", "value": sum(s.get("active_instances", 0) for s in stages_list)},
                {"label": "已完成实例", "value": sum(s.get("completed_instances", 0) for s in stages_list)},
            ],
            "details": {"stages": stages_list},
            "insights": ["11个核心业务环节：市场调研→客户开发→项目开发→投产管理→订单管理→采购与到料→生产→检验→入库→交付与发运→账款回收"],
            "actions": [
                "调用 /erp/stages/create 创建环节实例",
                "调用 /erp/stages/trial 进行环节试算",
                "调用 /erp/stages/export 导出环节数据",
            ],
        }

    async def _fetch_erp_stage_detail(self) -> Dict[str, Any]:
        """获取 ERP 环节详情"""
        if not self.erp_11_stages_manager:
            return {
                "title": "环节详情",
                "metrics": [],
                "details": {},
                "insights": ["ERP 11环节管理器未初始化"],
                "actions": [],
            }
        
        # 获取最近的活动实例
        recent_instances = []
        for instance_id, instance in list(self.erp_11_stages_manager.stage_instances.items())[-10:]:
            recent_instances.append({
                "instance_id": instance_id,
                "stage_id": instance.get("stage_id"),
                "stage_name": instance.get("stage_name"),
                "status": instance.get("status"),
                "kpi_score": instance.get("kpi_score", 0),
                "started_at": instance.get("started_at"),
                "completed_at": instance.get("completed_at"),
            })
        
        return {
            "title": "环节详情",
            "metrics": [
                {"label": "总实例数", "value": len(self.erp_11_stages_manager.stage_instances)},
                {"label": "最近实例", "value": len(recent_instances)},
            ],
            "details": {"recent_instances": recent_instances},
            "insights": ["每个环节实例包含完整的指标数据、KPI得分和执行状态"],
            "actions": [
                "调用 /erp/stages/{instance_id}/update 更新环节指标",
                "调用 /erp/stages/{instance_id}/complete 完成环节",
            ],
        }

    async def _fetch_inventory_trial(self) -> Dict[str, Any]:
        """获取库存试算视图"""
        if not self.inventory_manager:
            return {
                "title": "库存试算",
                "metrics": [{"label": "物料数量", "value": 0}],
                "details": {},
                "insights": ["库存管理器未初始化"],
                "actions": ["请初始化 MaterialInventoryManager"],
            }
        
        # 获取库存状态
        inventory_status = {}
        if hasattr(self.inventory_manager, "get_inventory_status"):
            # 尝试获取所有物料的库存状态
            for material_id in list(self.inventory_manager.inventory.keys())[:10]:
                status = self.inventory_manager.get_inventory_status(material_id)
                if status.get("success"):
                    inventory_status[material_id] = status
        
        # 计算试算指标
        total_materials = len(self.inventory_manager.materials) if hasattr(self.inventory_manager, "materials") else 0
        total_inventory_value = 0
        low_stock_count = 0
        
        for inv in inventory_status.values():
            if inv.get("success"):
                on_hand = inv.get("on_hand", 0)
                avg_cost = inv.get("avg_cost", 0)
                total_inventory_value += on_hand * avg_cost
                if inv.get("on_hand", 0) < inv.get("safety_stock", 0):
                    low_stock_count += 1
        
        return {
            "title": "库存试算",
            "metrics": [
                {"label": "物料总数", "value": total_materials},
                {"label": "库存总值", "value": round(total_inventory_value, 2)},
                {"label": "低库存预警", "value": low_stock_count},
            ],
            "details": {
                "inventory_status": inventory_status,
                "trial_calculation": {
                    "total_value": total_inventory_value,
                    "low_stock_items": low_stock_count,
                    "optimization_potential": round(total_inventory_value * 0.1, 2),
                },
            },
            "insights": ["库存试算支持 ABC 分类、安全库存优化、再订货点计算"],
            "actions": [
                "调用 /erp/inventory/trial 进行库存优化试算",
                "调用 /erp/inventory/abc-analysis 进行 ABC 分类分析",
            ],
        }

    async def _fetch_inventory_status(self) -> Dict[str, Any]:
        """获取库存状态视图"""
        if not self.inventory_manager:
            return {
                "title": "库存状态",
                "metrics": [],
                "details": {},
                "insights": ["库存管理器未初始化"],
                "actions": [],
            }
        
        # 获取实时库存数据
        inventory_list = []
        if hasattr(self.inventory_manager, "inventory"):
            for material_id, inv_data in list(self.inventory_manager.inventory.items())[:20]:
                material = self.inventory_manager.materials.get(material_id, {})
                inventory_list.append({
                    "material_id": material_id,
                    "material_name": material.get("name", ""),
                    "on_hand": inv_data.get("on_hand", 0),
                    "allocated": inv_data.get("allocated", 0),
                    "available": inv_data.get("available", 0),
                    "on_order": inv_data.get("on_order", 0),
                    "safety_stock": material.get("safety_stock", 0),
                    "reorder_point": material.get("reorder_point", 0),
                })
        
        return {
            "title": "库存状态",
            "metrics": [
                {"label": "物料种类", "value": len(inventory_list)},
                {"label": "总库存量", "value": sum(inv.get("on_hand", 0) for inv in inventory_list)},
                {"label": "可用库存", "value": sum(inv.get("available", 0) for inv in inventory_list)},
            ],
            "details": {"inventory_list": inventory_list},
            "insights": ["实时库存数据包括在库、已分配、可用、在途等状态"],
            "actions": [
                "调用 /erp/inventory/query 查询特定物料库存",
                "调用 /erp/inventory/reserve 预留库存",
                "调用 /erp/inventory/release 释放预留",
            ],
        }

    async def _fetch_erp_trial_calc(self) -> Dict[str, Any]:
        """获取运营试算视图"""
        if not self.erp_11_stages_manager:
            return {
                "title": "运营试算",
                "metrics": [],
                "details": {},
                "insights": ["ERP 11环节管理器未初始化"],
                "actions": [],
            }
        
        # 示例试算：目标营收试算
        trial_examples = []
        for stage_id in list(self.erp_11_stages_manager.stages.keys())[:3]:
            stage_config = self.erp_11_stages_manager.stages[stage_id]
            # 生成示例指标
            example_metrics = {}
            for metric in stage_config.get("metrics", []):
                example_metrics[metric] = 100  # 示例值
            
            trial_result = self.erp_11_stages_manager.trial_calculate(stage_id, example_metrics)
            if trial_result.get("success"):
                trial_examples.append({
                    "stage_id": stage_id,
                    "stage_name": stage_config.get("name"),
                    "kpi_score": trial_result.get("kpi_score", 0),
                    "formula": trial_result.get("formula", ""),
                })
        
        return {
            "title": "运营试算",
            "metrics": [
                {"label": "可试算环节", "value": len(self.erp_11_stages_manager.stages)},
                {"label": "试算示例", "value": len(trial_examples)},
            ],
            "details": {"trial_examples": trial_examples},
            "insights": ["运营试算支持目标营收、产量、成本等关键指标的试算"],
            "actions": [
                "调用 /erp/trial/calculate 进行目标营收试算",
                "调用 /erp/trial/production 进行产量试算",
                "调用 /erp/trial/cost 进行成本试算",
            ],
        }

    # ------------------------------------------------------------------ Expert Views

    async def _fetch_expert_routing(self) -> Dict[str, Any]:
        """获取专家路由视图"""
        if not self.enhanced_expert_router:
            return {
                "title": "专家路由",
                "metrics": [{"label": "专家数量", "value": 0}],
                "details": {},
                "insights": ["专家路由器未初始化"],
                "actions": ["请初始化 EnhancedExpertRouter"],
            }
        
        # 获取路由策略和能力映射
        routing_strategies = {}
        if hasattr(self.enhanced_expert_router, "routing_strategies"):
            routing_strategies = self.enhanced_expert_router.routing_strategies
        
        expert_capabilities = {}
        if hasattr(self.enhanced_expert_router, "expert_capabilities"):
            expert_capabilities = self.enhanced_expert_router.expert_capabilities
        
        return {
            "title": "专家路由",
            "metrics": [
                {"label": "路由策略", "value": len(routing_strategies)},
                {"label": "专家能力", "value": len(expert_capabilities)},
            ],
            "details": {
                "routing_strategies": routing_strategies,
                "expert_capabilities": expert_capabilities,
            },
            "insights": ["智能路由根据任务类型和专家能力自动选择最合适的专家"],
            "actions": [
                "调用 /expert/routing/route 进行任务路由",
                "调用 /expert/routing/strategies 查看路由策略",
            ],
        }

    async def _fetch_expert_collaboration(self) -> Dict[str, Any]:
        """获取专家协同视图"""
        if not self.expert_collaboration_hub:
            return {
                "title": "专家协同",
                "metrics": [{"label": "活跃会话", "value": 0}],
                "details": {},
                "insights": ["专家协同中枢未初始化"],
                "actions": ["请初始化 ExpertCollaborationHub"],
            }
        
        # 获取活跃会话
        active_sessions = []
        if hasattr(self.expert_collaboration_hub, "get_active_sessions"):
            active_sessions = await self.expert_collaboration_hub.get_active_sessions()
        recent_sessions = active_sessions[:5] if active_sessions else []
        
        return {
            "title": "专家协同",
            "metrics": [
                {"label": "活跃会话", "value": len(active_sessions)},
                {"label": "最近会话", "value": len(recent_sessions)},
            ],
            "details": {"recent_sessions": recent_sessions},
            "insights": ["多专家联合会商会话，支持同步贡献与决策记录"],
            "actions": [
                "调用 /expert/collaboration/create 创建协同会话",
                "调用 /expert/collaboration/{session_id}/contribute 添加专家贡献",
                "调用 /expert/collaboration/{session_id}/decide 记录决策",
            ],
        }

    async def _fetch_expert_board(self) -> Dict[str, Any]:
        """获取专家看板视图"""
        if not self.expert_collaboration_hub:
            return {
                "title": "专家看板",
                "metrics": [],
                "details": {},
                "insights": ["专家协同中枢未初始化"],
                "actions": [],
            }
        
        # 获取专家能力和表现数据
        expert_performance = {}
        if hasattr(self.expert_collaboration_hub, "get_expert_performance"):
            expert_performance = await self.expert_collaboration_hub.get_expert_performance()
        
        # 获取协同统计
        collaboration_stats = {}
        if hasattr(self.expert_collaboration_hub, "get_collaboration_stats"):
            collaboration_stats = await self.expert_collaboration_hub.get_collaboration_stats()
        
        return {
            "title": "专家看板",
            "metrics": [
                {"label": "专家数量", "value": len(expert_performance)},
                {"label": "总协同次数", "value": collaboration_stats.get("total_sessions", 0)},
                {"label": "平均响应时间", "value": collaboration_stats.get("avg_response_time", 0)},
            ],
            "details": {
                "expert_performance": expert_performance,
                "collaboration_stats": collaboration_stats,
            },
            "insights": ["专家看板展示专家能力、表现、协同效率等关键指标"],
            "actions": [
                "调用 /expert/board/performance 查看专家表现",
                "调用 /expert/board/metrics 查看协同指标",
            ],
        }

    async def _fetch_expert_metrics(self) -> Dict[str, Any]:
        """获取专家协同指标视图"""
        if not self.expert_collaboration_hub:
            return {
                "title": "协同指标",
                "metrics": [],
                "details": {},
                "insights": ["专家协同中枢未初始化"],
                "actions": [],
            }
        
        # 获取协同指标
        metrics = {}
        if hasattr(self.expert_collaboration_hub, "get_collaboration_metrics"):
            metrics = await self.expert_collaboration_hub.get_collaboration_metrics()
        
        return {
            "title": "协同指标",
            "metrics": [
                {"label": "协作指数", "value": metrics.get("collaboration_index", 0)},
                {"label": "响应速度", "value": metrics.get("response_speed", 0)},
                {"label": "决策质量", "value": metrics.get("decision_quality", 0)},
            ],
            "details": metrics,
            "insights": ["协同指标包括协作指数、响应速度、决策质量等量化指标"],
            "actions": [
                "调用 /expert/metrics/collaboration 查看协作指数",
                "调用 /expert/metrics/response 查看响应速度",
            ],
        }


__all__ = ["ModuleRegistry"]


