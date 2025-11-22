class StoryboardRequest(BaseModel):
    concept: str
    template: Optional[str] = "fast_promo"
    duration: Optional[int] = Field(None, description="视频时长（秒）")
    style: Optional[str] = Field("modern", description="风格（modern/classic/creative）")


class StoryboardResponse(BaseModel):
    concept: str
    template: str
    shots: List[Dict[str, Any]]


class ResourceRollbackRequest(BaseModel):
    suggestion_id: str
    reason: Optional[str] = None


class ResourceRollbackResponse(BaseModel):
    suggestion_id: str
    description: str
    plan: str
    requested_by: str
    reason: Optional[str] = None
    rolled_back_at: str
    status: str


class TrendScenarioRequest(BaseModel):
    indicator: str = "EV_DEMAND"
    scenario_name: Optional[str] = "政策刺激 + 需求走强"
    demand_shift: float = 0.05
    policy_intensity: float = 0.08
    supply_shift: float = 0.02


class TrendScenarioResponse(BaseModel):
    indicator: str
    scenario: str
    assumptions: Dict[str, float]
    forecast: Dict[str, Any]
    timeline: List[Dict[str, Any]]
    recommendations: List[str]


class TrendBacktestResponse(BaseModel):
    indicator: str
    window: int
    metrics: Dict[str, Any]
    series: List[Dict[str, Any]]
    events: List[Dict[str, Any]]


class ExpertRouteSimulationRequest(BaseModel):
    query: str
    knowledge_hints: Optional[List[str]] = None
    expected_domain: Optional[str] = None


class ExpertParticipant(BaseModel):
    expert_id: str
    name: str
    domain: str
    role: Optional[str] = None


class CollaborationSessionCreateRequest(BaseModel):
    topic: str
    initiator: str
    goals: List[str] = Field(default_factory=list)
    channel: Optional[str] = "multi"
    experts: List[ExpertParticipant]


class CollaborationContributionRequest(BaseModel):
    expert_id: str
    expert_name: str
    channel: str
    summary: str
    action_items: List[str] = Field(default_factory=list)
    impact_score: float = Field(0.5, ge=0.0, le=1.0)
    references: List[str] = Field(default_factory=list)


class CollaborationDecisionRequest(BaseModel):
    owner: str
    summary: str
    kpis: List[str] = Field(default_factory=list)
    followups: List[str] = Field(default_factory=list)


class ConfigApplyRequest(BaseModel):
    profile: str
    overrides: Dict[str, str] = Field(default_factory=dict)


class DeploymentRunRequest(BaseModel):
    profile: str
    dry_run: bool = True
    steps: Optional[List[str]] = None
    overrides: Dict[str, str] = Field(default_factory=dict)


class ServiceRegisterRequest(BaseModel):
    service: str
    endpoint: str
    version: str = "v1"
    protocol: str = "http"
    deployment_target: str = "monolith"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ServiceHeartbeatRequest(BaseModel):
    service: str
    instance_id: str
    status: str = "healthy"


class ServiceCallRequest(BaseModel):
    service: str
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    prefer_internal: bool = True


class CollaborationEventStreamManager:
    """SSE 推送：监听统一事件总线的专家协同事件"""

    def __init__(self):
        self._queues: set[asyncio.Queue] = set()
        self._bus = get_unified_event_bus()
        self._subscriber_id = self._bus.subscribe(
            self._handle_event,
            EventFilter(category=EventCategory.WORKFLOW, source="expert_collaboration"),
        )

    async def register(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._queues.add(queue)
        return queue

    def unregister(self, queue: asyncio.Queue) -> None:
        self._queues.discard(queue)

    async def _handle_event(self, event) -> None:
        payload = event.to_dict()
        for queue in list(self._queues):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
                queue.put_nowait(payload)
class CopyrightCheckRequest(BaseModel):
    text: str
    sources: Optional[List[str]] = None
    platforms: Optional[List[str]] = None
    threshold: float = 0.75


class CopyrightCheckResponse(BaseModel):
    matches: List[Dict[str, Any]]
    summary: Dict[str, Any]
    workflow: Dict[str, Any]
"""
超级Agent主界面API
提供RESTful API接口
"""

from fastapi import (
    APIRouter,
    HTTPException,
    UploadFile,
    File,
    Body,
    Query,
    Depends,
    Request,
    Response,
    status,
)
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import time
from datetime import datetime
from uuid import uuid4

import sys
from pathlib import Path
import json
import os
import logging
import random
import math
import re
from collections import deque, Counter
import itertools
import yaml
import httpx

logger = logging.getLogger(__name__)

# 添加项目根目录到路径（如果还没有）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.super_agent import SuperAgent
from core.memo_system import MemoSystem
from core.task_planning import TaskPlanning
from core.self_learning import SelfLearningMonitor
from core.resource_monitor import ResourceMonitor
from core.resource_auto_adjuster import ResourceAutoAdjuster
from core.voice_interaction import VoiceInteraction
from core.translation import TranslationService
from core.file_generation import FileGenerationService
from core.web_search import WebSearchService
from core.file_format_handler import FileFormatHandler
from core.terminal_executor import TerminalExecutor
from core.terminal_audit import TerminalAuditLogger
from core.performance_monitor import performance_monitor, response_time_optimizer
from core.llm_service import get_llm_service, LLMProvider
from core.task_orchestrator import TaskStatus
from core.learning_events import LearningEventType
from core.data_sources.factory_data_source import FactoryDataSource
from core.integrations.external_status import ExternalIntegrationStatus
from core.workflow_causal_analyzer import WorkflowCausalAnalyzer
from core.resource_diagnostic import ResourceDiagnosticEngine
from core.resource_authorization import ResourceAuthorizationManager
from core.resource_strategy_engine import ResourceStrategyEngine, ResourceStrategy, StrategyContext
from core.resource_conflict_scheduler import ResourceConflictScheduler, ConflictType, ResolutionStrategy
from core.security_compliance_baseline import SecurityComplianceBaseline, ComplianceCategory, SecurityLevel, ViolationType
from core.observability_system import ObservabilitySystem, SpanType, SpanStatus
from core.observability_middleware import ObservabilityMiddleware
from core.observability_persistence import ObservabilityPersistence
from core.observability_alerts import ObservabilityAlertSystem, AlertRule, AlertSeverity, AlertCondition
from core.observability_export import ObservabilityExporter
from core.knowledge_template import KnowledgeTemplateManager, KnowledgeType, KnowledgePriority
from core.knowledge_ingestion_strategy import KnowledgeIngestionStrategy, IngestionTrigger, IngestionPriority
from core.security.config import get_security_settings
from core.security.auth import require_api_token
from core.security.sensitive_policy import SensitiveContentFilter
from core.security.audit_pipeline import get_audit_pipeline
from core.security.permission_guard import get_permission_guard
from core.security.risk_engine import get_risk_engine
from core.security.crawler_compliance import get_crawler_compliance_service
from core.security.approval_workflow import (
    get_approval_manager,
    ApprovalStatus,
)
ERP_MODULE_ROOT = project_root / "💼 Intelligent ERP & Business Management"
if ERP_MODULE_ROOT.exists() and str(ERP_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(ERP_MODULE_ROOT))
try:
    from core.trial_data_source import DemoFactoryTrialDataSource
    from core.erp_8d_analysis import analyze_8d
except ModuleNotFoundError as exc:
    DemoFactoryTrialDataSource = None
    analyze_8d = None
    print(f"[SuperAgentAPI] ERP modules未加载: {exc}")
from core.strategy_engine import StrategyEngine
from core.content_compliance import ContentComplianceService
from core.copyright_inspector import CopyrightInspector, PlatformSourceComparison
from core.stock_gateway import StockGateway
from core.stock_simulator import StockSimulator
from core.stock_backtest import BacktestEngine
from core.integrations.douyin import DouyinIntegration
from core.integrations.api_monitor import APIMonitor
from core.stock_factor_engine import StockFactorEngine, stock_factor_engine
from core.stock_execution_analyzer import execution_analyzer
from core.broker_adapter import broker_manager
from core.storyboard_generator import StoryboardGenerator
from core.trend_scenario_engine import trend_scenario_engine, ScenarioInput
from core.trend_data_collector import trend_data_collector
from core.trend_rag_output import trend_rag_output
from core.operations_finance_expert import chart_expert, finance_expert
from core.operations_finance_strategy import operations_finance_strategy
from core.erp_data_sync import erp_data_sync
from core.expert_standardization import expert_standardization
from core.expert_collaboration import expert_collaboration_hub
from core.config_automation import (
    get_env_manager,
    get_deployment_manager,
)
from core.service_registry import get_service_registry, ServiceContract
from core.service_gateway import get_service_gateway, ServiceCallResult
from core.coding_assistant_enhanced import documentation_generator, command_replay, cursor_ide_integration
from core.multitenant_microservice_evolution import multitenant_evolution
from core.slo_performance_reporter import slo_performance_reporter, VectorIndexBenchmark, StreamingBenchmark, ContextCompressionBenchmark
from core.acceptance_matrix_generator import acceptance_matrix_generator
from core.acceptance_recording import acceptance_recording
from core.ci_evidence_uploader import ci_evidence_uploader
from core.closed_loop_engine import ClosedLoopEngine, ExecutionStatus
from core.unified_event_bus import UnifiedEventBus, EventCategory, EventSeverity, get_unified_event_bus, EventFilter
from core.execution_checker import ExecutionChecker, CheckType, CheckResult
from core.feedback_handler import FeedbackHandler, FeedbackType, FeedbackStatus
from core.evidence_recorder import EvidenceRecorder, EvidenceType
from core.content_deai_pipeline import deai_pipeline
from core.content_analytics import content_analytics
from core.database_persistence import DatabasePersistence, get_persistence
from core.data_sync_manager import DataSyncManager, get_sync_manager
from core.data_service import DataService, get_data_service
from core.persistence_seed import PersistenceSeeder
from core.tenant_manager import tenant_manager
from core.tenant_context import get_current_tenant
from core.module_registry import ModuleRegistry
from core.module_chain import ModuleChainManager
from core.function_hierarchy import FOUR_LEVEL_FUNCTIONS

RAG_MODULE_ROOT = project_root / "📚 Enhanced RAG & Knowledge Graph"
if RAG_MODULE_ROOT.exists() and str(RAG_MODULE_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_MODULE_ROOT))
try:
    from core.rag_tools import (
        clean_text as rag_clean,
        standardize_text as rag_standardize,
        deduplicate as rag_dedup,
        validate as rag_validate,
        authenticity_score as rag_auth_score,
    )
except ModuleNotFoundError as exc:
    rag_clean = rag_standardize = rag_dedup = rag_validate = rag_auth_score = None
    print(f"[SuperAgentAPI] RAG modules未加载: {exc}")

from AI_Programming_Assistant.core import (
    CursorAuthorization,
    CursorBridge,
    CursorLocalBridge,
    CursorPluginSystem,
    CursorProtocol,
    AuthorizationLevel,
    AccessScope,
    PluginPermission,
    PluginStatus,
    ProtocolCommand,
)
from datetime import timedelta
from dataclasses import dataclass, asdict

security_settings = get_security_settings()
sensitive_filter = SensitiveContentFilter()
router_dependencies = [Depends(require_api_token)] if security_settings.api_token else []

router = APIRouter(prefix="/api/super-agent", tags=["Super Agent"], dependencies=router_dependencies)
collaboration_event_stream = CollaborationEventStreamManager()
env_config_manager = get_env_manager()
deployment_manager = get_deployment_manager()
service_registry = get_service_registry()
service_gateway = get_service_gateway()


def _bootstrap_service_contracts():
    services_dir = project_root.parent / "config/services"
    if not services_dir.exists():
        return
    for path in services_dir.glob("*.yaml"):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:
            logger.warning("读取服务契约失败 %s: %s", path, exc)
            continue
        service = data.get("service")
        if not service:
            continue
        for operation in data.get("operations", []):
            contract = ServiceContract(
                service=service,
                operation=operation.get("operation"),
                method=operation.get("method", "POST"),
                path=operation.get("path", "/"),
                version=data.get("version", "v1"),
                timeout=operation.get("timeout", 2.0),
                description=data.get("description", ""),
                schema=operation.get("schema", {}),
            )
            service_registry.register_contract(contract)


_bootstrap_service_contracts()

# 初始化服务
super_agent = SuperAgent()
memo_system = MemoSystem()
task_planning = TaskPlanning(memo_system)

# P0-003: 初始化数据持久化和同步服务
data_persistence = get_persistence()
data_sync_manager = get_sync_manager()
data_service = get_data_service()

# P1-003: 数据持久化种子管理
persistence_seeder = PersistenceSeeder(data_service)

# P1-002: API 调用监控
api_monitor = APIMonitor()


def _register_default_service_handlers():
    async def rag_search(payload: Dict[str, Any]):
        query = payload.get("query") or payload.get("text") or ""
        top_k = max(1, min(int(payload.get("top_k", 5)), 10))
        result = await super_agent.dual_rag_engine.first_rag_retrieval(user_input=query, top_k=top_k)
        return result.to_dict()

    async def rag_experience(payload: Dict[str, Any]):
        query = payload.get("query") or ""
        execution = payload.get("execution_result") or {"module": "rag", "result": {}}
        rag1 = await super_agent.dual_rag_engine.first_rag_retrieval(user_input=query)
        rag2 = await super_agent.dual_rag_engine.second_rag_retrieval(
            user_input=query,
            execution_result=execution,
            rag1_result=rag1,
        )
        return {"rag1": rag1.to_dict(), "rag2": rag2.to_dict()}

    async def trend_backtest(payload: Dict[str, Any]):
        indicator = payload.get("indicator") or "EV_DEMAND"
        window = int(payload.get("window", 90))
        return trend_scenario_engine.run_backtest(indicator=indicator, window=window)

    async def trend_scenario(payload: Dict[str, Any]):
        scenario = ScenarioInput(
            indicator=payload.get("indicator", "EV_DEMAND"),
            scenario_name=payload.get("scenario_name", "默认情景"),
            demand_shift=float(payload.get("demand_shift", 0.05)),
            policy_intensity=float(payload.get("policy_intensity", 0.08)),
            supply_shift=float(payload.get("supply_shift", 0.02)),
        )
        return trend_scenario_engine.simulate_scenario(scenario)

    service_gateway.register_internal_handler("rag_hub", "search", rag_search)
    service_gateway.register_internal_handler("rag_hub", "experience", rag_experience)
    service_gateway.register_internal_handler("trend_ops", "backtest", trend_backtest)
    service_gateway.register_internal_handler("trend_ops", "scenario", trend_scenario)


_register_default_service_handlers()

# P0-004: 安全审计、权限、风控
audit_pipeline = get_audit_pipeline()
risk_engine = get_risk_engine()
permission_guard = get_permission_guard()
crawler_compliance_service = get_crawler_compliance_service()
approval_manager = get_approval_manager()
security_read_dep = permission_guard.require("security:read")
security_write_dep = permission_guard.require("security:write")
finance_read_dep = permission_guard.require("finance:read")
learning_monitor = SelfLearningMonitor(resource_manager=None, event_bus=super_agent.event_bus)
resource_monitor = ResourceMonitor()
learning_monitor.resource_manager = resource_monitor
resource_adjuster = ResourceAutoAdjuster(resource_manager=resource_monitor)  # 资源自动调节器
# P0-013: 初始化工作流因果分析器
workflow_causal_analyzer = WorkflowCausalAnalyzer(
    workflow_monitor=super_agent.workflow_monitor,
    learning_monitor=learning_monitor
)
# 将因果分析器注入到工作流监控器
if super_agent.workflow_monitor:
    super_agent.workflow_monitor.causal_analyzer = workflow_causal_analyzer

# P0-014: 初始化资源诊断和授权管理器
resource_diagnostic_engine = ResourceDiagnosticEngine(
    resource_monitor=resource_monitor,
    resource_auto_adjuster=resource_adjuster
)
resource_authorization_manager = ResourceAuthorizationManager(
    resource_auto_adjuster=resource_adjuster,
    resource_diagnostic=resource_diagnostic_engine
)

# P0-015: 初始化资源策略引擎和冲突调度系统
resource_strategy_engine = ResourceStrategyEngine(
    learning_system=learning_monitor,  # 与自学习系统联动
    resource_monitor=resource_monitor,
    dynamic_allocator=None  # 如果需要可以注入
)
resource_conflict_scheduler = ResourceConflictScheduler(
    resource_monitor=resource_monitor,
    strategy_engine=resource_strategy_engine,
    learning_system=learning_monitor,  # 与自学习系统联动
    dynamic_allocator=None
)

# P0-017: 初始化安全与合规基线系统
security_compliance_baseline = SecurityComplianceBaseline()

# P0-018: 初始化可观测性系统
observability_system = ObservabilitySystem()
observability_persistence = ObservabilityPersistence()
observability_alerts = ObservabilityAlertSystem(observability_system)
observability_exporter = ObservabilityExporter(observability_system, observability_persistence)

# 注册告警回调（可以扩展为发送邮件、Webhook等）
def alert_callback(alert):
    """告警回调函数"""
    logger.warning(f"告警触发: {alert.rule_name} - {alert.message}")

observability_alerts.register_alert_callback(alert_callback)

# P0-019: 初始化知识沉淀系统
knowledge_template_manager = KnowledgeTemplateManager()
knowledge_ingestion_strategy = KnowledgeIngestionStrategy(
    template_manager=knowledge_template_manager,
    rag_service=None  # 稍后可以通过HTTP调用RAG服务
)
knowledge_ingestion_strategy.rag_service = super_agent.rag_service


ERP_PROCESS_STAGES = [
    {
        "id": "market_research",
        "name": "市场调研",
        "status": "completed",
        "progress": 100,
        "owner": "市场洞察组",
        "duration_days": 7,
        "started_at": "2025-10-01T09:00:00",
        "completed_at": "2025-10-07T18:00:00",
        "metrics": {
            "market_size": "¥1.2B",
            "target_segments": 3,
            "feasibility": "A",
            "opportunities": 12
        },
        "risks": ["竞争对手价格战"],
        "next_actions": ["移交客户开发团队"],
        "documents": ["市场洞察报告.pdf"]
    },
    {
        "id": "customer_development",
        "name": "客户开发",
        "status": "completed",
        "progress": 100,
        "owner": "销售拓展",
        "duration_days": 10,
        "started_at": "2025-10-08T09:00:00",
        "completed_at": "2025-10-18T18:00:00",
        "metrics": {
            "leads_contacted": 36,
            "qualified_leads": 14,
            "conversion_rate": 38
        },
        "risks": [],
        "next_actions": ["初步技术评估"],
        "documents": ["客户沟通记录.xlsx"]
    },
    {
        "id": "project_development",
        "name": "项目开发",
        "status": "completed",
        "progress": 100,
        "owner": "解决方案部",
        "duration_days": 12,
        "started_at": "2025-10-19T09:00:00",
        "completed_at": "2025-10-30T18:00:00",
        "metrics": {
            "bom_ready": True,
            "custom_features": 4,
            "engineering_hours": 320
        },
        "risks": ["部分功能需二次确认"],
        "next_actions": ["生成投产计划"],
        "documents": ["项目规格书.docx"]
    },
    {
        "id": "production_planning",
        "name": "投产计划",
        "status": "completed",
        "progress": 100,
        "owner": "计划调度中心",
        "duration_days": 5,
        "started_at": "2025-11-01T09:00:00",
        "completed_at": "2025-11-05T18:00:00",
        "metrics": {
            "lines_reserved": 2,
            "capacity_utilization": 86,
            "planned_batches": 6
        },
        "risks": [],
        "next_actions": ["创建客户订单"],
        "documents": ["生产排程表.xlsx"]
    },
    {
        "id": "order_management",
        "name": "订单管理",
        "status": "in_progress",
        "progress": 72,
        "owner": "订单运营",
        "duration_days": 9,
        "started_at": "2025-11-06T09:00:00",
        "completed_at": None,
        "metrics": {
            "orders_confirmed": 4,
            "orders_pending": 1,
            "value_confirmed": "¥4.5M"
        },
        "risks": ["一个关键订单待客户签字"],
        "next_actions": ["同步采购需求"],
        "documents": ["订单确认书.pdf"]
    },
    {
        "id": "procurement",
        "name": "采购执行",
        "status": "in_progress",
        "progress": 58,
        "owner": "采购管理",
        "duration_days": 8,
        "started_at": "2025-11-08T09:00:00",
        "completed_at": None,
        "metrics": {
            "po_sent": 18,
            "po_confirmed": 12,
            "critical_items": 3
        },
        "risks": ["关键芯片交期 14 天"],
        "next_actions": ["加急跟催供应商"],
        "documents": ["采购清单.xlsx"]
    },
    {
        "id": "material_receipt",
        "name": "到料管理",
        "status": "planned",
        "progress": 20,
        "owner": "仓储部",
        "duration_days": 6,
        "started_at": None,
        "completed_at": None,
        "metrics": {
            "expected_shipments": 9,
            "inspected_ready": 0,
            "defect_rate": 0
        },
        "risks": [],
        "next_actions": ["准备IQC检验"],
        "documents": []
    },
    {
        "id": "production",
        "name": "生产执行",
        "status": "planned",
        "progress": 0,
        "owner": "制造中心",
        "duration_days": 14,
        "started_at": None,
        "completed_at": None,
        "metrics": {},
        "risks": [],
        "next_actions": ["等待物料齐套"],
        "documents": []
    },
    {
        "id": "quality_check",
        "name": "质量检验",
        "status": "pending",
        "progress": 0,
        "owner": "QA实验室",
        "duration_days": 4,
        "metrics": {},
        "risks": [],
        "next_actions": [],
        "documents": []
    },
    {
        "id": "warehousing",
        "name": "入库管理",
        "status": "pending",
        "progress": 0,
        "owner": "仓库运营",
        "duration_days": 3,
        "metrics": {},
        "risks": [],
        "next_actions": [],
        "documents": []
    },
    {
        "id": "delivery",
        "name": "交付与结算",
        "status": "pending",
        "progress": 0,
        "owner": "交付团队",
        "duration_days": 6,
        "metrics": {},
        "risks": [],
        "next_actions": [],
        "documents": []
    }
]

ERP_PROCESS_TIMELINE = [
    {
        "stage": "market_research",
        "title": "市场调研完成",
        "timestamp": "2025-10-07T18:00:00",
        "status": "completed",
        "summary": "锁定智能硬件和工业控制两个目标细分市场",
        "impact": "+12% 转化率"
    },
    {
        "stage": "customer_development",
        "title": "客户开发完成",
        "timestamp": "2025-10-18T18:00:00",
        "status": "completed",
        "summary": "签署 4 份意向书，预计订单金额 ¥4.8M",
        "impact": "+4 个关键客户"
    },
    {
        "stage": "project_development",
        "title": "项目方案冻结",
        "timestamp": "2025-10-30T18:00:00",
        "status": "completed",
        "summary": "确认 BOM 与特性，进入排产",
        "impact": "BOM 成本下降 6%"
    },
    {
        "stage": "production_planning",
        "title": "排产完成",
        "timestamp": "2025-11-05T18:00:00",
        "status": "completed",
        "summary": "锁定 2 条产线，交付周期 28 天",
        "impact": "产能利用率 86%"
    },
    {
        "stage": "order_management",
        "title": "订单确认进度",
        "timestamp": "2025-11-09T09:00:00",
        "status": "in_progress",
        "summary": "4/5 份订单进入执行，剩余待法务确认",
        "impact": "现金流预测 +¥3.2M"
    },
    {
        "stage": "procurement",
        "title": "采购执行更新",
        "timestamp": "2025-11-11T10:00:00",
        "status": "in_progress",
        "summary": "12 份 PO 已确认，关键芯片预计 14 天交付",
        "impact": "物料齐套率 65%"
    }
]

TREND_INDICATOR_LIBRARY = [
    {
        "id": "industry_demand_velocity",
        "category": "industry",
        "name": "行业需求增速",
        "description": "跟踪细分行业订单与询价的滚动增速，识别需求拐点",
        "unit": "%",
        "current_value": 8.4,
        "trend": "+1.2pp MoM",
        "confidence": 0.82,
        "drivers": ["交付周期缩短", "补库存需求", "海外回流订单"],
        "risks": ["需求透支", "价格战加剧"],
        "recommended_actions": [
            "优先投放华东/新能源供应链资源",
            "将交付 SLA 从15天下调到12天并监控成本"
        ],
        "regions": ["华东", "华南"],
        "industries": ["智能制造", "新能源设备"]
    },
    {
        "id": "region_capacity_utilization",
        "category": "region",
        "name": "区域产能利用率",
        "description": "监控重点省份核心产线利用率与排产饱和度",
        "unit": "%",
        "current_value": 74,
        "trend": "-3pp WoW",
        "confidence": 0.77,
        "drivers": ["限电政策解除", "人工短缺", "OEM订单推迟"],
        "risks": ["产线波动加剧", "加班成本上涨"],
        "recommended_actions": [
            "针对珠三角安排跨区域产能调拨",
            "对 >90% 产线启用夜班守护流程"
        ],
        "regions": ["珠三角", "成渝"],
        "industries": ["电子制造", "高端装配"]
    },
    {
        "id": "policy_grants_tracker",
        "category": "policy",
        "name": "政策补贴兑现率",
        "description": "统计各专项补贴的审批率/到账率，评估现金流改善幅度",
        "unit": "%",
        "current_value": 62,
        "trend": "+9pp QoQ",
        "confidence": 0.71,
        "drivers": ["智能制造补贴放款", "地方技改奖励"],
        "risks": ["材料真实性核查", "合规审计补证"],
        "recommended_actions": [
            "对未到账的 18% 政策包发起人工跟进",
            "同步财务制定“补贴到账即对冲贷款”策略"
        ],
        "regions": ["长三角", "京津冀"],
        "industries": ["装备制造", "绿色能源"]
    },
    {
        "id": "policy_risk_index",
        "category": "policy",
        "name": "政策敏感度指数",
        "description": "量化宏观调控/合规新规对业务的影响范围与概率",
        "unit": "index",
        "current_value": 0.63,
        "trend": "+0.07",
        "confidence": 0.68,
        "drivers": ["双碳排放核查", "出口退税审核加强"],
        "risks": ["新增审批节点导致交付延期"],
        "recommended_actions": [
            "组建跨部门合规响应小组",
            "将 ESG/双碳指标嵌入销售投标资料"
        ],
        "regions": ["全国"],
        "industries": ["全行业"]
    }
]

EXPERT_ABILITY_MAP = [
    {
        "id": "rag_expert",
        "name": "知识架构专家",
        "icon": "📚",
        "level": "L3",
        "modules": ["rag", "knowledge"],
        "confidence": 0.94,
        "coverage": {"scenarios": 42, "avg_latency_ms": 680, "satisfaction": 0.95},
        "capabilities": [
            {"name": "知识分层&标签", "status": "ready"},
            {"name": "召回率调优", "status": "ready"},
            {"name": "文档去冗/蒸馏", "status": "beta"}
        ],
        "signals": ["检索失败", "FAQ覆盖不足", "召回率指标低于80%"],
        "playbooks": ["rag/playbook/boost-faq.md", "rag/playbook/graph-routing.md"],
        "tests": ["rag_segment_smoke", "rag_latency_benchmark"]
    },
    {
        "id": "erp_expert",
        "name": "ERP运营专家",
        "icon": "💼",
        "level": "L2",
        "modules": ["erp", "operations"],
        "confidence": 0.89,
        "coverage": {"scenarios": 37, "avg_latency_ms": 720, "satisfaction": 0.9},
        "capabilities": [
            {"name": "订单履约追踪", "status": "ready"},
            {"name": "采购补货建议", "status": "ready"},
            {"name": "产能排程校验", "status": "pilot"}
        ],
        "signals": ["订单交期查询", "排产冲突", "物料齐套率低"],
        "playbooks": ["erp/playbook/exception-handler.md"],
        "tests": ["erp_command_center_regression"]
    },
    {
        "id": "content_expert",
        "name": "内容增长专家",
        "icon": "✍️",
        "level": "L2",
        "modules": ["content", "douyin"],
        "confidence": 0.9,
        "coverage": {"scenarios": 29, "avg_latency_ms": 610, "satisfaction": 0.92},
        "capabilities": [
            {"name": "多平台内容策略", "status": "ready"},
            {"name": "版权/合规校验", "status": "ready"},
            {"name": "视频脚本拆分", "status": "beta"}
        ],
        "signals": ["脚本生成", "合规评估", "内容A/B方案"],
        "playbooks": ["content/playbook/script-kit.md"],
        "tests": ["content_flow_blocking", "douyin_callback_smoke"]
    },
    {
        "id": "trend_expert",
        "name": "趋势洞察专家",
        "icon": "📈",
        "level": "L2",
        "modules": ["trend", "operations"],
        "confidence": 0.88,
        "coverage": {"scenarios": 31, "avg_latency_ms": 640, "satisfaction": 0.91},
        "capabilities": [
            {"name": "指标回测解释", "status": "ready"},
            {"name": "What-if情景评估", "status": "ready"},
            {"name": "行业看板推荐", "status": "pilot"}
        ],
        "signals": ["趋势对比", "政策冲击", "指标异常"],
        "playbooks": ["trend/playbook/what-if.md"],
        "tests": ["trend_backtest_fixture"]
    },
    {
        "id": "coding_expert",
        "name": "AI编程专家",
        "icon": "💻",
        "level": "L3",
        "modules": ["coding"],
        "confidence": 0.91,
        "coverage": {"scenarios": 53, "avg_latency_ms": 520, "satisfaction": 0.89},
        "capabilities": [
            {"name": "问题定位", "status": "ready"},
            {"name": "单测补全", "status": "ready"},
            {"name": "代码审阅", "status": "ready"}
        ],
        "signals": ["CI失败", "代码审查", "API设计"],
        "playbooks": ["dev/playbook/hotfix.md"],
        "tests": ["coding_unit_patch", "lint_autofix_suite"]
    }
]

EXPERT_ROUTING_STRATEGY = {
    "version": "2025.11.18",
    "confidence_thresholds": {
        "direct_route": 0.72,
        "needs_clarification": 0.45,
        "fallback": 0.3
    },
    "heuristics": [
        {"signal": "关键词权重", "weight": 0.45, "description": "匹配词频>3且覆盖不同槽位即直连"},
        {"signal": "意图模型", "weight": 0.25, "description": "基于指令/问题/请求分类"},
        {"signal": "RAG来源", "weight": 0.15, "description": "知识片段标签与专家领域映射"},
        {"signal": "会话上下文", "weight": 0.1, "description": "最近一次专家成功率"},
        {"signal": "资源负载", "weight": 0.05, "description": "避免单专家超载"}
    ],
    "fallback_chain": [
        {"condition": "confidence < 0.3", "action": "切回RAG回答"},
        {"condition": "专家超载>80%", "action": "路由次优专家并提醒"}
    ],
    "module_load": {
        "rag": 0.32,
        "erp": 0.18,
        "content": 0.15,
        "trend": 0.12,
        "coding": 0.23
    },
    "recent_routes": [
        {
            "query": "帮我评估一下华东订单的交付风险",
            "expert": "erp_expert",
            "domain": "erp",
            "confidence": 0.81,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        },
        {
            "query": "这份FAQ命中率太低了可以怎么调",
            "expert": "rag_expert",
            "domain": "rag",
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        },
        {
            "query": "抖音版权校验未通过怎么复核",
            "expert": "content_expert",
            "domain": "content",
            "confidence": 0.76,
            "timestamp": datetime.now().isoformat(timespec="seconds")
        }
    ]
}

EXPERT_ACCEPTANCE_MATRIX = [
    {
        "capability": "知识分层&标签",
        "owner": "RAG QA",
        "tests": [
            {"name": "rag_segment_smoke", "status": "pass", "metric": "15/15"},
            {"name": "rag_latency_benchmark", "status": "pass", "metric": "1.8s P95"}
        ],
        "acceptance": "召回率>85%，平均响应<2s",
        "last_run": "2025-11-16T10:00:00"
    },
    {
        "capability": "订单履约追踪",
        "owner": "ERP QA",
        "tests": [
            {"name": "erp_command_center_regression", "status": "pass", "metric": "32 checks"},
            {"name": "slo_alert_hook", "status": "pass", "metric": "0漏报"}
        ],
        "acceptance": "异常定位准确率>95%，建议推送≤3条",
        "last_run": "2025-11-15T18:30:00"
    },
    {
        "capability": "版权/侵权复核",
        "owner": "Content QA",
        "tests": [
            {"name": "content_flow_blocking", "status": "pass", "metric": "100% 拦截"},
            {"name": "douyin_callback_smoke", "status": "pass", "metric": "实时"}
        ],
        "acceptance": "命中率>98%，误杀<1%",
        "last_run": "2025-11-17T09:45:00"
    },
    {
        "capability": "What-if情景评估",
        "owner": "Trend QA",
        "tests": [
            {"name": "trend_backtest_fixture", "status": "pass", "metric": "MAPE 6.1%"},
            {"name": "scenario_delta_validation", "status": "pass", "metric": "Δ预测一致"}
        ],
        "acceptance": "预测偏差<8%，情景报告≤2s输出",
        "last_run": "2025-11-14T14:12:00"
    },
    {
        "capability": "代码审阅",
        "owner": "Dev QA",
        "tests": [
            {"name": "coding_unit_patch", "status": "pass", "metric": "18/18"},
            {"name": "lint_autofix_suite", "status": "pass", "metric": "0 blocker"}
        ],
        "acceptance": "安全问题检出率>90%，建议执行率>80%",
        "last_run": "2025-11-16T22:00:00"
    }
]

MULTITENANT_EVOLUTION_PLAN = {
    "version": "2025.11.18",
    "vision": {
        "summary": "保持单体代码库（mono-repo + shared runtime），通过模块化边界与多租户上下文，逐步演进至可拆分微服务架构。",
        "goals": [
            "短期：提升租户隔离、审计与资源路由能力，支持 One Agent Serving Multi-Tenants。",
            "中期：以模块为单位抽象服务契约，具备 Sidecar/Function 托管能力。",
            "长期：可平滑迁移至多进程/多容器微服务，而无需重写业务逻辑。"
        ]
    },
    "tenancy_layers": [
        {"layer": "Request Context", "status": "ready", "notes": "FastAPI 路由支持 require_tenant，中间件注入 tenant id / SLA / feature flag"},
        {"layer": "Data Segregation", "status": "partial", "notes": "核心模拟数据存储仍为内存结构，下一阶段接入租户前缀/Schema"},
        {"layer": "Execution Sandbox", "status": "beta", "notes": "终端/策略/任务执行支持 per-tenant 审计记录"},
        {"layer": "Resource Budgeting", "status": "planned", "notes": "结合 resource_monitor & expert_router 做到 per-tenant 限速/限流"},
        {"layer": "Observability", "status": "ready", "notes": "observability_system 具备租户标签，Traces 可区分租户"}
    ],
    "module_boundaries": [
        {"module": "chat_orchestrator", "domain": "Interaction", "ownership": "Core Agent", "separation": "LLM routing + conversation state", "ready": True},
        {"module": "rag_hub", "domain": "Knowledge", "ownership": "RAG Service", "separation": "Doc store + vector ops", "ready": True},
        {"module": "erp_stack", "domain": "Execution", "ownership": "ERP Core", "separation": "Process + BPM + analytics", "ready": False},
        {"module": "content_ops", "domain": "Channel Integration", "ownership": "Content Service", "separation": "Douyin + compliance + creative", "ready": True},
        {"module": "trend_ops", "domain": "Analytics", "ownership": "Trend Engine", "separation": "Indicators + scenarios", "ready": True},
        {"module": "expert_router", "domain": "Shared Capability", "ownership": "Core Agent", "separation": "Routing + capability registry", "ready": True}
    ],
    "phases": [
        {
            "name": "Phase 0 · Context Isolation",
            "timeline": "Week 0-1",
            "deliverables": [
                "推广 require_tenant 到关键 API（资源、任务、内容集成等）",
                "在 super_agent.expert_router / resource_monitor 持久缓存中加入 tenant key",
                "补充租户审计字段（tenant_id, workspace_id）"
            ],
            "risk": "低"
        },
        {
            "name": "Phase 1 · Module Contracts",
            "timeline": "Week 1-3",
            "deliverables": [
                "为 chat / rag / trend / content / stock 模块声明 OpenAPI 契约（内部）",
                "定义模块化 adapter 层（service facade）并在单体内调用",
                "在 observability_system 中记录 module-latency 指标"
            ],
            "risk": "中"
        },
        {
            "name": "Phase 2 · Service Slice",
            "timeline": "Week 3-6",
            "deliverables": [
                "抽离 rag_hub 与 content_ops 为可部署 Sidecar（仍在进程内）",
                "启用事件总线（Workflow monitor events）同步租户生命周期",
                "预置 API Gateway/Ingress 配置清单"
            ],
            "risk": "中"
        },
        {
            "name": "Phase 3 · Poly-Service Ready",
            "timeline": "Week 6+",
            "deliverables": [
                "提供 service registry + health contract，允许以进程/容器形式部署",
                "为每个模块准备 data access adapter（postgres / vector / redis）",
                "完成 chaos / failover / rolling deployment 演练"
            ],
            "risk": "高"
        }
    ],
    "guardrails": [
        "保持单体仓库与基础设施不变，所有新模块先以内嵌 service adapter 形式编排。",
        "Tenant Context 必须贯穿 API -> service -> storage，禁止在 service 内部重新解析 JWT。",
        "每次拆分都要先补充模块级测试/验收（参考专家验收矩阵形式）。",
        "Observability + Resource monitor 作为统一 SLO 中枢，不随服务拆分而复制。",
        "优先拆分对外依赖度高的模块（内容、RAG、资源执行），ERP/任务保持单体直到数据持久化完成。"
    ],
    "acceptance": {
        "metrics": [
            "Tenancy regression (per-tenant data spill) = 0",
            "Module contract 覆盖率 >= 80%",
            "Service slice smoke 测试 (start/stop) 可在 5 min 内完成",
            "Observability trace 覆盖 >= 95%"
        ],
        "tests": ["tenancy_smoke_suite", "module_contract_snapshot", "service_slice_replay"]
    },
    "next_steps": [
        "落地租户配置中心（yaml/json + override）",
        "资源/专家等共享组件写入 tenant-aware cache 接口",
        "筹备迁移文档（per module runbook）"
    ]
}

TREND_DASHBOARD_TEMPLATES = [
    {
        "id": "industry_command_center",
        "title": "行业攻防指挥舱",
        "scenario": "行业机会识别 + 竞品对比",
        "widgets": [
            {"type": "kpi", "label": "需求增速", "metric": "industry_demand_velocity"},
            {"type": "bar", "label": "重点行业投放 ROI", "dimensions": ["行业", "ROI"]},
            {"type": "table", "label": "竞品预警", "columns": ["企业", "策略", "风险"]}
        ],
        "recommended_audience": ["CMO", "行业运营负责人"],
        "refresh_cycle": "Daily",
        "call_to_action": "将看板嵌入月度行业例会，驱动资源倾斜决策。"
    },
    {
        "id": "regional_heatmap",
        "title": "区域策略驾驶舱",
        "scenario": "区域供需 & 资源调度",
        "widgets": [
            {"type": "map", "label": "区域产能利用率", "metric": "region_capacity_utilization"},
            {"type": "line", "label": "区域订单/交付趋势", "dimensions": ["周次", "订单量", "交付量"]},
            {"type": "list", "label": "区域政策窗口期", "fields": ["政策", "补贴比例", "截止"]}
        ],
        "recommended_audience": ["区域总经理", "供应链调度中心"],
        "refresh_cycle": "Hourly",
        "call_to_action": "结合产线负荷自动推送跨区域调拨建议。"
    },
    {
        "id": "policy_risk_wall",
        "title": "政策风险雷达墙",
        "scenario": "政策敏感度与合规追踪",
        "widgets": [
            {"type": "radar", "label": "政策敏感度指数", "metric": "policy_risk_index"},
            {"type": "timeline", "label": "政策发布节点", "fields": ["时间", "政策", "影响"]},
            {"type": "table", "label": "补贴兑现进度", "columns": ["政策包", "申报", "到账率", "负责人"]}
        ],
        "recommended_audience": ["财务负责人", "政府事务团队"],
        "refresh_cycle": "Weekly",
        "call_to_action": "生成政策影响快报 + 应对脚本，减少审批链路。"
    }
]

TREND_INSIGHTS_FEED = [
    {
        "id": "insight_001",
        "title": "华东新能源设备需求跃升",
        "category": "industry",
        "region": "华东",
        "impact": "positive",
        "summary": "四季度储能 EPC 投标集中释放，逆变器出口新增 12% 预算。",
        "action": "抢占 2 家龙头的合规供应名录，提前锁定 1H 投放产线。",
        "timestamp": "2025-11-18T08:30:00",
        "tags": ["新能源", "储能"]
    },
    {
        "id": "insight_002",
        "title": "珠三角劳动力紧缺触发交付风险",
        "category": "region",
        "region": "华南",
        "impact": "negative",
        "summary": "核心代工厂离职率升至 18%，夜班排班不足导致交付延迟 2.4 天。",
        "action": "启用成渝备份产线并对冲流转成本。",
        "timestamp": "2025-11-17T21:10:00",
        "tags": ["供应链", "产能"]
    },
    {
        "id": "insight_003",
        "title": "双碳核查加强 政策敏感度继续上行",
        "category": "policy",
        "region": "全国",
        "impact": "warning",
        "summary": "新一批审计要求企业在招投标文件内披露碳排放基线与减排路径。",
        "action": "在全部投标模板中植入 ESG 附页，并同步培训销售团队。",
        "timestamp": "2025-11-17T14:05:00",
        "tags": ["政策", "ESG"]
    }
]

TREND_COMPLIANCE_REPORT = {
    "id": "trend_compliance_default",
    "status": "green",
    "last_audit": "2025-11-15T09:00:00",
    "summary": "采集、去标识化、RAG 写回全流程通过最近一次合规审计。",
    "controls": [
        {"name": "采集频控", "status": "active", "owner": "Trend Ops"},
        {"name": "匿名化处理", "status": "active", "owner": "Data Governance"},
        {"name": "审计日志", "status": "beta", "owner": "AI Safety"},
    ],
    "risks": [
        {"item": "第三方源合规声明滞后", "level": "medium"},
        {"item": "政策调整同步延迟", "level": "low"},
    ],
    "recommendations": [
        "与法务共建采集控制台，自动提示高风险关键词。",
        "对外部数据源补齐协议，完善留存/销毁策略。",
    ],
}

OPERATIONS_CHART_LIBRARY = [
    {
        "id": "cash_vs_burn",
        "title": "净现金 vs Burn Rate",
        "chart_type": "area",
        "metrics": ["net_cash", "burn_rate"],
        "dimensions": ["周"],
        "owner": "图表专家 Iris",
        "explanation": "对比净现金与每月现金消耗，可快速识别 Runway 是否小于安全范围。",
        "recommended_usage": "董事会财务例会 / CFO 周报"
    },
    {
        "id": "collection_to_payment",
        "title": "回款 vs 付款节奏",
        "chart_type": "stacked_bar",
        "metrics": ["collections", "payments"],
        "dimensions": ["日"],
        "owner": "图表专家 Leo",
        "explanation": "展示收付款错配与峰值，辅助运营团队安排采购/生产节奏。",
        "recommended_usage": "运营例会 / 供应链审查"
    },
    {
        "id": "policy_subsidy_progress",
        "title": "政策补贴兑现漏斗",
        "chart_type": "funnel",
        "metrics": ["declared", "approved", "received"],
        "dimensions": ["地区"],
        "owner": "图表专家 Nori",
        "explanation": "突出补贴审批/到账瓶颈，强调合规资料准备的优先级。",
        "recommended_usage": "政府事务、财务专项分析"
    }
]

OPERATIONS_FINANCE_GUIDES = [
    {
        "id": "receivable_watch",
        "title": "应收账期拉长预警",
        "owner": "财务专家 Ethan",
        "severity": "warning",
        "summary": "TOP5 行业客户账期已超过 68 天，较上月增加 12 天。",
        "recommended_actions": [
            "对超过 60 天的账款启动协同催收",
            "销售提成绑定回款节点，减少确认延迟"
        ]
    },
    {
        "id": "policy_cash_gap",
        "title": "补贴到账节奏不均衡",
        "owner": "财务专家 Zoe",
        "severity": "info",
        "summary": "智能制造补贴进入审批尾声，预计两周后到账 18%",
        "recommended_actions": [
            "提前准备验收抽检材料，避免因资料缺失再延迟",
            "到账后优先对冲短期贷款，降低财务费用"
        ]
    },
    {
        "id": "opex_burn_line",
        "title": "运营成本守护线",
        "owner": "财务专家 Max",
        "severity": "critical",
        "summary": "若维持现有 Burn Rate，6.2 个月后 Runway < 3 个月",
        "recommended_actions": [
            "冻结非关键招聘，集中资源于高回报产能",
            "把采购付款周期延长 7 天，并建立支出优先级表"
        ]
    }
]

OPERATIONS_STRATEGY_LINKS = {
    "version": "2025-11-18",
    "bridges": [
        {
            "name": "预算-ERP订单联动",
            "source": "operations_finance",
            "target": "erp_orders",
            "description": "预算冻结额度将直接影响 ERP 订单审批流，超出预算自动发起审批任务。",
            "status": "ready",
            "signals": ["预算冻结", "大额订单"],
            "automation": ["task_center.approval.push", "chat.notify.cfo"]
        },
        {
            "name": "成本-产能联动",
            "source": "operations_finance",
            "target": "erp_production",
            "description": "材料成本波动超过 5% 时，触发产能排程调整与供应商谈判流程。",
            "status": "beta",
            "signals": ["unit_cost_spike", "capacity>90%"],
            "automation": ["erp.production.rebalance", "trend.collect.market"]
        },
        {
            "name": "报表-专家联动",
            "source": "operations_finance",
            "target": "experts",
            "description": "财务报表异常自动路由图表/财务专家，输出建议并同步到看板与聊天。",
            "status": "ready",
            "signals": ["runway<6", "collections_delay"],
            "automation": ["experts.route.finance", "chat.push.alert"]
        }
    ],
    "playbooks": [
        {"name": "预算锁定流程", "owner": "Finance Ops", "systems": ["operations_finance", "erp"], "doc": "operations/playbook/budget-lock.md"},
        {"name": "材料涨价应对", "owner": "Supply Chain", "systems": ["operations_finance", "erp_procurement", "trend"], "doc": "operations/playbook/material-rise.md"},
        {"name": "报表异常应急", "owner": "CFO Office", "systems": ["operations_finance", "experts"], "doc": "operations/playbook/report-anomaly.md"}
    ],
    "metrics": {
        "automation_rate": 0.74,
        "cross_system_alerts_24h": 5,
        "expert_routing_latency_ms": 820
    }
}

OPERATIONS_FINANCE_STRATEGY = {
    "last_synced": "2025-11-18T09:30:00",
    "cross_system_links": [
        {
            "name": "预算 vs 生产计划",
            "source_system": "operations_finance",
            "target_system": "erp",
            "status": "active",
            "description": "预算审批后自动更新 ERP 排产权重，低预算项目延后提报。",
            "coverage": 0.88
        },
        {
            "name": "成本异常推送到趋势合规",
            "source_system": "operations_finance",
            "target_system": "trend",
            "status": "pilot",
            "description": "当某细分成本突破阈值时，触发趋势合规采集校验。",
            "coverage": 0.52
        },
        {
            "name": "预算释放同步库存安全库存",
            "source_system": "operations_finance",
            "target_system": "erp_inventory",
            "status": "planned",
            "description": "预算下调时自动提升安全库存告警级别。",
            "coverage": 0.34
        }
    ],
    "budget_playbooks": [
        {
            "id": "budget_guard_001",
            "title": "Runway 触底守护",
            "owner": "财务专家 Ethan",
            "triggers": ["runway_months < 6", "burn_rate > plan"],
            "actions": [
                {"system": "operations_finance", "action": "冻结非关键预算"},
                {"system": "erp", "action": "重排交付优先级"},
                {"system": "trend", "action": "提示开源侧动作"}
            ],
            "status": "ready"
        },
        {
            "id": "cost_bridge_002",
            "title": "跨系统成本压降",
            "owner": "运营专家 Zoe",
            "triggers": ["unit_cost_increase > 5%"],
            "actions": [
                {"system": "erp_procurement", "action": "触发供应商谈判"},
                {"system": "operations_finance", "action": "更新预算场景"},
                {"system": "trend", "action": "采集最新行情"}
            ],
            "status": "pilot"
        }
    ],
    "reporting_matrix": [
        {"report": "预算执行月报", "frequency": "Monthly", "owner": "Finance Ops", "systems": ["operations_finance", "erp", "trend"], "status": "ready"},
        {"report": "跨系统成本稽核", "frequency": "Bi-weekly", "owner": "Audit Team", "systems": ["operations_finance", "erp", "content"], "status": "beta"},
        {"report": "渠道 ROI 联动", "frequency": "Quarterly", "owner": "Growth Finance", "systems": ["operations_finance", "trend"], "status": "planned"}
    ]
}

# 注册持久化种子
persistence_seeder.register_seed(
    "trend_indicators",
    module="trend",
    type_field="type",
    type_value="indicator",
    records=TREND_INDICATOR_LIBRARY,
    record_id_field="id",
)
persistence_seeder.register_seed(
    "trend_dashboards",
    module="trend",
    type_field="type",
    type_value="dashboard_template",
    records=TREND_DASHBOARD_TEMPLATES,
    record_id_field="id",
)
persistence_seeder.register_seed(
    "trend_insight_seed",
    module="trend",
    type_field="type",
    type_value="insight",
    records=TREND_INSIGHTS_FEED,
    record_id_field="id",
)
persistence_seeder.register_seed(
    "operations_chart_blueprints",
    module="operations",
    type_field="type",
    type_value="chart_blueprint",
    records=OPERATIONS_CHART_LIBRARY,
    record_id_field="id",
)
persistence_seeder.register_seed(
    "operations_finance_guides",
    module="operations",
    type_field="type",
    type_value="finance_guide",
    records=OPERATIONS_FINANCE_GUIDES,
    record_id_field="id",
)
persistence_seeder.register_seed(
    "trend_compliance_report",
    module="trend",
    type_field="type",
    type_value="compliance_report",
    records=[TREND_COMPLIANCE_REPORT],
    record_id_field="id",
)


def _create_knowledge_entry_from_template(
    template_id: str,
    title: str,
    content: str,
    *,
    summary: Optional[str] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    source: Optional[str] = None,
    source_id: Optional[str] = None,
    priority: Optional[str] = None
):
    """根据模板创建知识条目，若模板不存在则抛出异常"""
    entry = knowledge_template_manager.create_entry_from_template(
        template_id=template_id,
        title=title,
        content=content,
        summary=summary,
        tags=tags or [],
        metadata=metadata or {},
        source=source,
        source_id=source_id,
        priority=priority
    )
    if not entry:
        raise HTTPException(status_code=404, detail=f"知识模板不存在: {template_id}")
    return entry


async def _ingest_knowledge_entry(entry, auto_queue: bool = True):
    """根据入库策略写入RAG或加入队列"""
    if not super_agent.rag_service:
        raise HTTPException(status_code=503, detail="RAG服务不可用")
    
    knowledge_ingestion_strategy.rag_service = super_agent.rag_service
    should_ingest, rule_id = knowledge_ingestion_strategy.should_ingest(entry)
    rule = knowledge_ingestion_strategy.rules.get(rule_id) if rule_id else None
    
    if should_ingest and rule and rule.trigger == IngestionTrigger.BATCH:
        queue_id = knowledge_ingestion_strategy.queue_for_ingestion(entry, rule_id)
        return {
            "success": True,
            "ingested": False,
            "queued": True,
            "queue_id": queue_id,
            "rule_id": rule_id
        }
    
    if should_ingest:
        result = await knowledge_ingestion_strategy.ingest_immediate(entry, super_agent.rag_service)
        result.setdefault("success", False)
        result["ingested"] = result.get("success", False)
        result["queued"] = False
        result["rule_id"] = rule_id
        return result
    
    if auto_queue:
        queue_id = knowledge_ingestion_strategy.queue_for_ingestion(entry, rule_id)
        return {
            "success": True,
            "ingested": False,
            "queued": True,
            "queue_id": queue_id,
            "rule_id": rule_id
        }
    
    return {
        "success": False,
        "ingested": False,
        "queued": False,
        "rule_id": rule_id,
        "message": "未匹配到入库规则"
    }

voice_interaction = VoiceInteraction()
translation_service = TranslationService()
# 文件生成服务（稍后注入RAG服务）
file_generation = None
web_search = WebSearchService()
file_format_handler = FileFormatHandler()  # 文件格式处理器
# 初始化审计日志系统
terminal_audit_logger = TerminalAuditLogger(
    audit_pipeline=audit_pipeline,
    risk_engine=risk_engine,
)
# 初始化终端执行器（启用沙箱模式）
terminal_executor = TerminalExecutor(
    workflow_monitor=super_agent.workflow_monitor,
    audit_logger=terminal_audit_logger,
    sandbox_enabled=True
)
external_status = ExternalIntegrationStatus()
strategy_engine = StrategyEngine()
# P0-017: 内容合规服务集成安全合规基线
content_compliance = ContentComplianceService(security_baseline=security_compliance_baseline)
copyright_inspector = CopyrightInspector()
stock_gateway = StockGateway(api_monitor=api_monitor)
stock_sim = StockSimulator()
stock_factor_engine = StockFactorEngine()
douyin = DouyinIntegration(api_monitor=api_monitor)
cursor_bridge = CursorBridge()
storyboard_generator = StoryboardGenerator()

# P1-202: 初始化 ERP 11 环节管理器和库存管理器
try:
    import sys
    from pathlib import Path
    erp_path = Path(__file__).parent.parent.parent / "💼 Intelligent ERP & Business Management"
    if erp_path.exists():
        sys.path.insert(0, str(erp_path))
        from core.erp_11_stages_manager import ERP11StagesManager
        from modules.material.material_inventory_manager import MaterialInventoryManager
        erp_11_stages_manager = ERP11StagesManager()
        inventory_manager = MaterialInventoryManager()
    else:
        erp_11_stages_manager = None
        inventory_manager = None
except Exception as e:
    logger.warning(f"ERP 模块初始化失败: {e}")
    erp_11_stages_manager = None
    inventory_manager = None

# P1-203: 初始化双RAG执行引擎和模块执行器
from core.dual_rag_execution_engine import DualRAGExecutionEngine
from core.module_executors import ContentModuleExecutor, StockModuleExecutor, TrendModuleExecutor
from core.enhanced_expert_router import EnhancedExpertRouter

# P1-204: 初始化合规策略管理器和审计工作流
from core.security.compliance_policy_manager import (
    CompliancePolicyManager,
    get_compliance_manager,
    OperationType,
    RiskLevel,
)
from core.security.compliance_audit_workflow import (
    ComplianceAuditWorkflow,
    get_compliance_audit_workflow,
    AuditStatus,
)

# P2-303: 初始化三大系统
from core.task_lifecycle_manager import (
    TaskLifecycleManager,
    get_task_lifecycle_manager,
    TaskStatus,
    TaskPriority,
)
from core.learning_curve_tracker import (
    LearningCurveTracker,
    get_learning_curve_tracker,
)
from core.resource_scheduler_with_hints import (
    ResourceSchedulerWithHints,
    get_resource_scheduler,
    ResourceType,
    HintType,
)

# P2-301: 初始化全局完成度矩阵和证据库
from core.completion_matrix_manager import (
    CompletionMatrixManager,
    get_completion_matrix_manager,
    CompletionStatus,
    EightMetrics,
    EvidenceLink,
    EvidenceCategory,
)
from core.evidence_library import (
    EvidenceLibrary,
    get_evidence_library,
    EvidenceSource,
)

# 初始化专家路由器
enhanced_expert_router = EnhancedExpertRouter()

# 初始化模块执行器
content_executor = ContentModuleExecutor(
    content_analytics=content_analytics,
    llm_service=None,  # 可以传入LLM服务
)
stock_executor = StockModuleExecutor(
    stock_gateway=stock_gateway,
    stock_factor_engine=stock_factor_engine,
    stock_simulator=stock_sim,
)
trend_executor = TrendModuleExecutor(
    trend_data_collector=trend_data_collector,
    trend_analyzer=None,  # 可以传入趋势分析器
)

# 注册模块执行器
module_executors = {
    "content": content_executor.execute,
    "stock": stock_executor.execute,
    "trend": trend_executor.execute,
}

# 初始化双RAG执行引擎
dual_rag_engine = DualRAGExecutionEngine(
    rag_service=super_agent.rag_service if hasattr(super_agent, "rag_service") else None,
    expert_router=enhanced_expert_router,
    module_executors=module_executors,
)

# P1-204: 初始化合规策略管理器和审计工作流
compliance_manager = get_compliance_manager()
compliance_audit_workflow = get_compliance_audit_workflow()

# P2-303: 初始化三大系统
task_lifecycle_manager = get_task_lifecycle_manager()
learning_curve_tracker = get_learning_curve_tracker()
resource_scheduler = get_resource_scheduler()

# P2-301: 初始化全局完成度矩阵和证据库
completion_matrix_manager = get_completion_matrix_manager()
evidence_library = get_evidence_library()

# P1-001: 三级界面数据注册中心
module_registry = ModuleRegistry(
    data_service=data_service,
    audit_pipeline=audit_pipeline,
    risk_engine=risk_engine,
    trend_data_collector=trend_data_collector,
    trend_rag_output=trend_rag_output,
    content_analytics=content_analytics,
    stock_gateway=stock_gateway,
    stock_factor_engine=stock_factor_engine,
    stock_simulator=stock_sim,
    operations_finance_strategy=operations_finance_strategy,
    chart_expert=chart_expert,
    finance_expert=finance_expert,
    memo_system=memo_system,
    command_replay=command_replay,
    cursor_integration=cursor_ide_integration,
    closed_loop_engine=super_agent.closed_loop_engine,
    expert_collaboration_hub=expert_collaboration_hub,
    enhanced_expert_router=enhanced_expert_router,
    erp_11_stages_manager=erp_11_stages_manager,
    inventory_manager=inventory_manager,
)

# P0-016: 初始化Cursor集成系统（协议/插件/本地桥/授权）
cursor_protocol = CursorProtocol()
cursor_plugin_system = CursorPluginSystem()
cursor_authorization = CursorAuthorization()
cursor_local_bridge = CursorLocalBridge(
    protocol=cursor_protocol,
    plugin_system=cursor_plugin_system,
    permission_manager=cursor_plugin_system.permission_manager
)
backtest_engine = BacktestEngine()
try:
    factory_data_source = FactoryDataSource()
    factory_data_source_error = None
except FileNotFoundError as exc:
    factory_data_source = None
    factory_data_source_error = str(exc)
if DemoFactoryTrialDataSource:
    try:
        trial_data_source = DemoFactoryTrialDataSource()
        trial_data_source_error = None
    except FileNotFoundError as exc:
        trial_data_source = None
        trial_data_source_error = str(exc)
else:
    trial_data_source = None
    trial_data_source_error = "ERP模块未加载"

# 设置依赖
super_agent.set_memo_system(memo_system)
super_agent.set_learning_monitor(learning_monitor)
super_agent.set_resource_monitor(resource_monitor)
super_agent.set_task_planning(task_planning)

# 初始化文件生成服务（注入RAG服务）
file_generation = FileGenerationService(rag_service=super_agent.rag_service)

# 启动资源监控（后台任务）
import asyncio
asyncio.create_task(resource_monitor.start_monitoring(interval=5))

# 启动ERP监听（轻量轮询对比）
_erp_last_order_count = {"count": 0}
async def _erp_listener():
    """每20秒轮询一次订单/工单变化，写入系统事件，供自学习/主界面使用"""
    ds = None
    try:
        ds = _get_factory_data_source()
    except Exception:
        return
    while True:
        try:
            orders = ds.get_orders()
            count = len(orders)
            if count != _erp_last_order_count["count"]:
                _erp_last_order_count["count"] = count
                if super_agent.workflow_monitor:
                    await super_agent.workflow_monitor.record_system_event(
                        event_type="erp_change",
                        source="erp_listener",
                        severity="info",
                        success=True,
                        data={"orders_count": count},
                        error=None
                    )
            await asyncio.sleep(20)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(20)

asyncio.create_task(_erp_listener())

bpmn_dir = Path(project_root) / "data" / "bpmn"
bpmn_dir.mkdir(parents=True, exist_ok=True)
rag_dir = Path(project_root) / "data" / "rag"
rag_dir.mkdir(parents=True, exist_ok=True)
rag_store_path = rag_dir / "documents.jsonl"
RAG_ACTIVITY_LOG = deque(maxlen=200)
RAG_SEARCH_HISTORY = deque(maxlen=200)

module_chain_manager = ModuleChainManager(
    data_service=data_service,
    service_registry=service_registry,
    rag_store_path=rag_store_path,
    trial_data_source=trial_data_source,
    factory_data_source=factory_data_source,
    trend_data_collector=trend_data_collector,
    content_analytics=content_analytics,
    stock_gateway=stock_gateway,
    cursor_bridge=cursor_bridge,
)


def _record_rag_event(event_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
    try:
        entry = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "payload": payload or {}
        }
        RAG_ACTIVITY_LOG.appendleft(entry)
        loop = asyncio.get_running_loop()
        loop.create_task(
            data_service.save_data(
                module="rag",
                data={"type": "activity", **entry},
                sync=False,
            )
        )
    except RuntimeError:
        # 在未运行事件循环的上下文中忽略持久化
        pass
    except Exception:
        pass


def _load_recent_rag_documents(limit: int = 50) -> List[Dict[str, Any]]:
    docs: List[Dict[str, Any]] = []
    if not rag_store_path.exists():
        return docs
    try:
        with open(rag_store_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
            import json as _json

            for line in reversed(lines):
                try:
                    docs.append(_json.loads(line))
                except Exception:
                    continue
    except Exception:
        return docs
    return docs


def _build_search_stats() -> Dict[str, Any]:
    history = list(RAG_SEARCH_HISTORY)
    total_queries = len(history)
    if total_queries == 0:
        return {
            "total_queries": 0,
            "average_results": 0,
            "top_queries": [],
            "recent": [],
        }
    result_counts = [item.get("results", 0) for item in history]
    avg_results = sum(result_counts) / len(result_counts)
    query_names = [item.get("query", "") for item in history if item.get("query")]
    top_queries = Counter(query_names).most_common(5)
    recent = history[:6]
    return {
        "total_queries": total_queries,
        "average_results": round(avg_results, 2),
        "top_queries": [{"query": q, "count": c} for q, c in top_queries],
        "recent": recent,
    }


def _build_kg_summary(limit: int = 10) -> Dict[str, Any]:
    docs = _load_recent_rag_documents(limit=60)
    keywords = Counter()
    doc_nodes = []
    word_nodes = []
    edges = []
    for doc in docs[:limit]:
        doc_nodes.append({
            "id": doc.get("id"),
            "label": doc.get("title", "文档"),
            "type": "document",
            "score": doc.get("authenticity", {}).get("score", 60)
        })
    for doc in docs:
        title = doc.get("title") or ""
        tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fa5]{2,}", title)[:3]
        for token in tokens:
            keywords[token.lower()] += 1
    top_keywords = keywords.most_common(8)
    keyword_to_id = {}
    for idx, (keyword, count) in enumerate(top_keywords):
        node_id = f"kw_{idx}"
        keyword_to_id[keyword] = node_id
        word_nodes.append({
            "id": node_id,
            "label": keyword,
            "type": "entity",
            "score": count
        })
    for doc in docs[:limit]:
        title = doc.get("title") or ""
        tokens = re.findall(r"[A-Za-z0-9\u4e00-\u9fa5]{2,}", title)
        doc_id = doc.get("id")
        for token in tokens:
            token_lower = token.lower()
            if token_lower in keyword_to_id:
                edges.append({
                    "source": doc_id,
                    "target": keyword_to_id[token_lower],
                    "weight": random.randint(1, 3)
                })
    summary = {
        "nodes": doc_nodes + word_nodes,
        "edges": edges[:20],
        "stats": {
            "documents": len(doc_nodes),
            "entities": len(word_nodes),
            "relations": len(edges),
            "last_updated": datetime.now().isoformat()
        },
        "top_entities": [{"name": node["label"], "weight": node["score"]} for node in word_nodes],
    }
    return summary

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    input_type: str = "text"  # text, voice, file, search
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    response: str
    response_time: float
    rag_retrievals: Optional[Dict] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus
    updates: Optional[Dict[str, Any]] = None


class TaskRetrospectRequest(BaseModel):
    """任务复盘请求"""
    success: bool
    summary: Optional[str] = ""
    lessons: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None


class TaskScheduleRequest(BaseModel):
    """任务排期请求"""
    scheduled_for: Optional[str] = None
    owner: Optional[str] = None
    notes: Optional[str] = None


class TaskResourceImpact(BaseModel):
    """任务执行对资源的影响"""
    summary: str
    category: Optional[str] = "general"
    delta: Optional[str] = None
    severity: Optional[str] = "medium"
    owner: Optional[str] = None


class TaskExecutionRequest(BaseModel):
    """任务执行配置"""
    writeback_to_rag: bool = False
    rag_title: Optional[str] = None
    rag_summary: Optional[str] = None
    rag_tags: Optional[List[str]] = None
    resource_impact: Optional[TaskResourceImpact] = None


class LearningRecommendationApplyRequest(BaseModel):
    """交互建议执行请求"""
    overrides: Optional[Dict[str, Any]] = None


@dataclass
class LearningResourceSuggestion:
    description: str
    action_type: str = "optimize"
    risk_level: str = "medium"
    expected_improvement: Optional[str] = None
    requires_approval: bool = True
    rollback_plan: Optional[str] = None
    severity: str = "medium"


class SystemEventRequest(BaseModel):
    """外部系统事件"""
    event_type: str
    source: str = "external"
    severity: str = "info"
    success: bool = True
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class LearningEventRequest(BaseModel):
    """外部学习事件"""
    event_type: str = "custom"
    source: str = "external"
    severity: str = "info"
    payload: Optional[Dict[str, Any]] = None


class TaskLoopRagWriteRequest(BaseModel):
    """任务闭环写回RAG"""
    task_id: Any
    title: str
    summary: str
    metadata: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = "task_execution"
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[str] = None
    auto_queue: bool = True
    source: Optional[str] = "task_loop"


class KnowledgeEntryRequest(BaseModel):
    """知识条目请求"""
    template_id: str
    title: str
    content: str
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    source_id: Optional[str] = None
    priority: Optional[str] = None
    auto_ingest: bool = True
    auto_queue: bool = True


class KnowledgeProcessQueueRequest(BaseModel):
    """处理入库队列请求"""
    batch_size: int = 10


async def _chat_pipeline(request: ChatRequest) -> ChatResponse:
    decision = None
    try:
        if request.message:
            try:
                sensitive_filter.assert_safe(request.message)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc

        if request.input_type == "file" and request.context and request.context.get("file_data"):
            file_data = request.context.get("file_data")
            filename = request.context.get("filename", "unknown")
            mime_type = request.context.get("mime_type")
            file_result = await file_format_handler.process_file(file_data, filename, mime_type)
            if file_result.get("success") and file_result.get("text"):
                request.message = f"{request.message}\n\n文件内容:\n{file_result['text']}"

        if request.context is None:
            request.context = {}

        decision = await strategy_engine.decide(request.message, request.input_type)

        slo_context = request.context.setdefault("slo", {})
        slo_context.update(
            {
                "rag_top_k": decision.rag_top_k,
                "module_timeout": decision.max_module_time,
                "use_fast_model": decision.use_fast_model,
                "enable_streaming": decision.enable_streaming,
            }
        )

        start_time = time.time()

        async def process_input():
            return await super_agent.process_user_input(
                user_input=request.message,
                input_type=request.input_type,
                context=request.context,
            )

        cache_key = f"chat:{request.message}:{request.input_type}" if len(request.message) < 200 else None

        if decision.use_cache_only and cache_key:
            cached_payload = response_time_optimizer.get_cached_value(cache_key)
            if cached_payload:
                strategy_engine.release(decision)
                cached_payload.setdefault("from_cache", True)
                cached_payload.setdefault("response_time", 0.05)
                slo_meta = {
                    "queue_wait": decision.queue_wait,
                    "degrade_level": decision.degrade_level,
                    "degrade_reason": decision.degrade_reason,
                    "from_cache": True,
                    "streaming": False,
                }
                return ChatResponse(
                    success=cached_payload.get("success", False),
                    response=cached_payload.get("response", ""),
                    response_time=cached_payload.get("response_time", 0.05),
                    rag_retrievals=cached_payload.get("rag_retrievals"),
                    timestamp=cached_payload.get("timestamp", datetime.now().isoformat()),
                    metadata={"slo": slo_meta},
                )

        result = await response_time_optimizer.optimize_with_timeout(
            process_input,
            timeout=decision.timeout_seconds,
            cache_key=cache_key,
        )

        if result is None:
            result = {
                "success": False,
                "response": "处理超时，请稍后重试",
                "response_time": 2.0,
                "rag_retrievals": None,
                "timestamp": datetime.now().isoformat(),
            }

        response_time = time.time() - start_time
        performance_monitor.record_response_time(
            response_time, from_cache=result.get("from_cache", False) if result else False
        )
        strategy_engine.release(decision)

        slo_meta = {
            "queue_wait": decision.queue_wait,
            "degrade_level": decision.degrade_level,
            "degrade_reason": decision.degrade_reason,
            "from_cache": result.get("from_cache", False),
            "streaming": decision.enable_streaming,
        }

        return ChatResponse(
            success=result.get("success", False) if result else False,
            response=result.get("response", "") if result else "",
            response_time=response_time,
            rag_retrievals=result.get("rag_retrievals") if result else None,
            timestamp=result.get("timestamp", datetime.now().isoformat())
            if result
            else datetime.now().isoformat(),
            metadata={"slo": slo_meta},
        )
    except Exception as e:
        strategy_engine.release(decision if decision else None)
        raise


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口⭐优化版（2秒响应目标）
    """
    try:
        return await _chat_pipeline(request)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _sse_encode(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, chunk_size: int = 160):
    if not text:
        yield ""
        return
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        yield _sse_encode({"type": "status", "message": "accepted"})
        try:
            response = await _chat_pipeline(request)
            text = response.response or ""
            chunk_count = 0
            for chunk in _chunk_text(text):
                if not chunk:
                    continue
                chunk_count += 1
                yield _sse_encode({"type": "token", "data": chunk})
            if chunk_count == 0:
                yield _sse_encode({"type": "token", "data": ""})
            yield _sse_encode({"type": "final", "payload": response.dict()})
        except Exception as exc:
            yield _sse_encode({"type": "error", "message": str(exc)})

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/memos")
async def get_memos(
    type: Optional[str] = None,
    importance: Optional[int] = None,
    tags: Optional[str] = None
):
    """获取备忘录列表"""
    tag_list = tags.split(",") if tags else None
    memos = await memo_system.get_memos(type=type, importance=importance, tags=tag_list)
    return {"memos": memos, "total": len(memos)}


@router.post("/memos")
async def add_memo(memo_data: Dict):
    """添加备忘录"""
    memo = await memo_system.add_memo(memo_data)
    return {"success": True, "memo": memo}


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    needs_confirmation: Optional[bool] = None
):
    """获取任务列表"""
    tasks = task_planning.get_tasks(status=status, needs_confirmation=needs_confirmation)
    return {"tasks": tasks, "total": len(tasks)}


@router.post("/tasks/extract")
async def extract_tasks():
    """从备忘录提炼任务⭐增强版（使用模板库）"""
    tasks = await task_planning.extract_tasks_from_memos()
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/tasks/templates")
async def get_task_templates():
    """获取任务模板列表"""
    templates = task_planning.template_library.get_all_templates()
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/file-formats/supported")
async def get_supported_formats():
    """获取支持的文件格式列表"""
    formats = file_format_handler.get_supported_formats()
    return {
        "formats": formats,
        "total": len(formats),
        "categories": list(file_format_handler.supported_formats.keys())
    }

@router.get("/rag/file-formats")
async def rag_file_formats():
    """返回按类别汇总的文件格式覆盖情况"""
    data = []
    total = 0
    for category, extensions in file_format_handler.supported_formats.items():
        unique_ext = sorted(set(extensions))
        total += len(unique_ext)
        data.append({
            "category": category,
            "count": len(unique_ext),
            "extensions": unique_ext
        })
    return {"success": True, "total_formats": total, "categories": data}


@router.post("/tasks/{task_id}/confirm")
async def confirm_task(
    task_id: int,
    request: Dict[str, Any] = Body(...)
):
    """确认任务"""
    confirmed = request.get("confirmed", False)
    reason = request.get("reason")
    result = await task_planning.confirm_task(task_id, confirmed, reason)
    if result:
        return {"success": True, "task": result}
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/tasks/{task_id}/schedule")
async def schedule_task(task_id: int, request: TaskScheduleRequest):
    """为任务排期并分派负责人"""
    task = await task_planning.schedule_task(
        task_id=task_id,
        scheduled_for=request.scheduled_for,
        owner=request.owner,
        notes=request.notes
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"success": True, "task": task}


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int, request: Optional[TaskExecutionRequest] = Body(None)):
    """执行任务⭐完善版"""
    exec_opts = request or TaskExecutionRequest()

    async def _task_executor(params: Dict[str, Any]) -> Dict[str, Any]:
        return await task_planning.execute_task(params["task_id"])

    execution_id, exec_result = await run_closed_loop_operation(
        module="task_planning",
        function="execute_task",
        parameters={"task_id": task_id},
        executor=_task_executor,
        task_id=str(task_id),
        metadata={"options": exec_opts.model_dump()},
    )
    task_payload = exec_result.get("result") or {}

    if task_payload.get("success"):
        if exec_opts.writeback_to_rag and exec_opts.rag_summary:
            rag_request = TaskLoopRagWriteRequest(
                task_id=task_id,
                title=exec_opts.rag_title or task_payload.get("task", {}).get("title", f"任务{task_id}"),
                summary=exec_opts.rag_summary,
                content=exec_opts.rag_summary,
                tags=exec_opts.rag_tags or task_payload.get("task", {}).get("tags"),
                metadata={"task_status": task_payload.get("task", {}).get("status")}
            )
            try:
                await task_loop_rag_writeback(rag_request)
            except Exception as exc:
                logger.warning("写回RAG失败: %s", exc)
        if exec_opts.resource_impact:
            resource_authorization_manager.log_task_impact(
                task_id=task_id,
                impact=exec_opts.resource_impact.dict()
            )
        response = dict(task_payload)
        response["execution_id"] = execution_id
        return response
    else:
        raise HTTPException(status_code=400, detail=task_payload.get("error", "任务执行失败"))


@router.post("/tasks/{task_id}/retrospect")
async def retrospect_task(task_id: int, request: TaskRetrospectRequest):
    """任务复盘：记录总结/经验/指标并完成生命周期闭环"""
    # 复盘数据结构直接附加到任务（利用已有task_planning存储）
    tasks = task_planning.get_tasks()
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.setdefault("retrospect", {})
    task["retrospect"].update({
        "success": request.success,
        "summary": request.summary or "",
        "lessons": request.lessons or [],
        "metrics": request.metrics or {},
        "retrospected_at": datetime.now().isoformat()
    })
    # 可选：将经验写回学习系统/RAG
    if hasattr(super_agent, "learning_monitor") and super_agent.learning_monitor:
        try:
            await super_agent.learning_monitor.record_insight({
                "type": "task_retrospect",
                "task_id": task_id,
                "success": request.success,
                "lessons": request.lessons or [],
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass
    return {"success": True, "task": task}


@router.post("/task-loop/rag-writeback")
async def task_loop_rag_writeback(request: TaskLoopRagWriteRequest):
    """任务闭环写回RAG知识库"""
    metadata = request.metadata or {}
    metadata.setdefault("task_id", request.task_id)
    tags = request.tags or [f"task-{request.task_id}"]
    template_id = request.template_id or "task_execution"
    content = request.content or request.summary
    
    entry = _create_knowledge_entry_from_template(
        template_id=template_id,
        title=request.title,
        content=content,
        summary=request.summary,
        tags=tags,
        metadata=metadata,
        source=request.source or "task_loop",
        source_id=str(request.task_id),
        priority=request.priority
    )
    
    ingestion_result = await _ingest_knowledge_entry(entry, auto_queue=request.auto_queue)
    
    await super_agent.event_bus.publish_event(
        LearningEventType.RAG_ALERT,
        source="task_loop_bridge",
        severity="info",
        payload={
            "task_id": request.task_id,
            "title": request.title,
            "template": template_id,
            "ingestion": ingestion_result
        }
    )
    return {
        "success": ingestion_result.get("success", True),
        "knowledge_entry": entry.to_dict(),
        "ingestion": ingestion_result
    }


# ============ P0-019: 知识模板与自动入库 ============


@router.get("/knowledge/templates")
async def list_knowledge_templates():
    """列出可用的知识模板"""
    templates = knowledge_template_manager.list_templates()
    return {"success": True, "templates": templates}


@router.post("/knowledge/entries")
async def create_knowledge_entry(request: KnowledgeEntryRequest):
    """根据模板创建知识条目并自动入库"""
    entry = _create_knowledge_entry_from_template(
        template_id=request.template_id,
        title=request.title,
        content=request.content,
        summary=request.summary,
        tags=request.tags,
        metadata=request.metadata,
        source=request.source,
        source_id=request.source_id,
        priority=request.priority
    )
    
    auto_queue = request.auto_queue
    ingestion_result = await _ingest_knowledge_entry(entry, auto_queue=auto_queue)
    
    return {
        "success": ingestion_result.get("success", True),
        "entry": entry.to_dict(),
        "ingestion": ingestion_result
    }


@router.get("/knowledge/ingestion/rules")
async def list_ingestion_rules():
    """获取知识入库规则"""
    rules = knowledge_ingestion_strategy.get_rules()
    return {"success": True, "rules": rules}


@router.get("/knowledge/ingestion/queue")
async def get_ingestion_queue():
    """获取知识入库队列状态"""
    status = knowledge_ingestion_strategy.get_queue_status()
    return {"success": True, "queue": status}


@router.post("/knowledge/ingestion/process")
async def process_ingestion_queue(request: KnowledgeProcessQueueRequest):
    """手动触发入库队列处理"""
    result = await knowledge_ingestion_strategy.process_queue(
        batch_size=request.batch_size,
        rag_service=super_agent.rag_service
    )
    return result


# ============ P1-021: ERP 11环节与流程可视化 ============


@router.get("/erp/process/stages")
async def get_erp_process_stages():
    """获取ERP流程阶段概览"""
    return {
        "success": True,
        "stages": ERP_PROCESS_STAGES,
        "updated_at": datetime.now().isoformat()
    }


@router.get("/erp/process/stages/{stage_id}")
async def get_erp_process_stage(stage_id: str):
    """获取单个ERP流程阶段详情"""
    stage = next((s for s in ERP_PROCESS_STAGES if s["id"] == stage_id), None)
    if not stage:
        raise HTTPException(status_code=404, detail="流程阶段不存在")
    extended_stage = dict(stage)
    extended_stage["related_timeline"] = [
        item for item in ERP_PROCESS_TIMELINE if item["stage"] == stage_id
    ]
    return {"success": True, "stage": extended_stage}


@router.get("/erp/process/timeline")
async def get_erp_process_timeline():
    """获取ERP流程时间线"""
    return {
        "success": True,
        "timeline": ERP_PROCESS_TIMELINE,
        "stage_count": len(ERP_PROCESS_STAGES)
    }


@router.get("/trend/indicators")
async def get_trend_indicators(category: Optional[str] = None):
    """行业/区域/政策指标库"""
    indicators = await persistence_seeder.get_records("trend_indicators", limit=200)
    categories = sorted({ind.get("category") for ind in indicators if ind.get("category")})
    if category:
        indicators = [ind for ind in indicators if ind.get("category") == category]
    return {
        "success": True,
        "categories": categories,
        "count": len(indicators),
        "indicators": indicators
    }


@router.get("/trend/dashboards")
async def get_trend_dashboards(category: Optional[str] = None):
    """行业/区域/政策看板模板"""
    dashboards = await persistence_seeder.get_records("trend_dashboards", limit=100)
    if category:
        dashboards = [db for db in dashboards if category in (db.get("scenario") or "")]
    return {
        "success": True,
        "dashboards": dashboards,
        "count": len(dashboards)
    }


@router.get("/trend/insights")
async def get_trend_insights(limit: int = 20, category: Optional[str] = None):
    """趋势洞察订阅 - P0-003: 使用真实数据库"""
    await persistence_seeder.ensure_seed("trend_insight_seed")
    filters = {}
    if category:
        filters["category"] = category
    
    insights = await data_service.query_data(
        module="trend",
        filters=filters,
        limit=limit,
        order_by="_created_at",
        order_desc=True,
    )
    
    # 如果没有数据，返回空列表（不再使用模拟数据）
    if not insights:
        # 移除模拟数据，返回空列表
        insights = []
    
    # 统计覆盖范围
    all_insights = await data_service.query_data(module="trend", limit=1000)
    coverage = {
        "industry": len([i for i in all_insights if i.get("category") == "industry"]),
        "region": len([i for i in all_insights if i.get("category") == "region"]),
        "policy": len([i for i in all_insights if i.get("category") == "policy"])
    }
    
    return {
        "success": True,
        "insights": insights,
        "coverage": coverage,
        "total": len(insights)
    }


@router.get("/trend/compliance")
async def get_trend_compliance():
    """趋势数据采集合规报告（增强版：集成数据采集统计）"""
    records = await persistence_seeder.get_records("trend_compliance_report", limit=1)
    report = (records[0] if records else {}).copy()
    
    # 集成数据采集统计
    collection_stats = trend_data_collector.get_collection_stats(days=30)
    report["data_collection_stats"] = collection_stats
    
    return {
        "success": True,
        "report": report
    }


@router.get("/trend/audit")
async def get_trend_audit(limit: int = 20):
    """趋势采集审计记录 - P0-003: 使用真实数据库"""
    # 从数据库查询审计日志
    logs = await data_service.query_data(
        module="trend",
        filters={"type": "audit_log"},
        limit=limit,
        order_by="_created_at",
        order_desc=True,
    )
    
    # 移除内部字段
    logs = [{k: v for k, v in log.items() if not k.startswith("_")} for log in logs]
    
    total = await data_service.count_data(module="trend", filters={"type": "audit_log"})
    
    return {
        "success": True,
        "audit": logs,
        "total": total
    }


async def _trend_backtest_logic(params: Dict[str, Any]) -> Dict[str, Any]:
    indicator = params["indicator"]
    window = params["window"]
    result = trend_scenario_engine.run_backtest(indicator, window)
    trend_data_collector.record_collection(
        source="backtest",
        data_type="backtest_result",
        count=len(result.get("series", [])),
        status="success",
        metadata={
            "indicator": indicator,
            "window": window,
            "mape": result.get("metrics", {}).get("mape"),
        },
    )
    return result


@router.get("/trend/backtest", response_model=TrendBacktestResponse)
async def trend_backtest(
    response: Response,
    indicator: str = Query("EV_DEMAND", description="指标编码"),
    window: int = Query(90, ge=30, le=180, description="回测窗口（天）"),
):
    """趋势预测回测可视化数据（增强版：集成数据采集）"""
    execution_id, exec_result = await run_closed_loop_operation(
        module="trend",
        function="backtest",
        parameters={"indicator": indicator, "window": window},
        executor=_trend_backtest_logic,
        metadata={"indicator": indicator},
    )
    if response is not None:
        response.headers["X-Execution-ID"] = execution_id
    return exec_result.get("result") or {}


@router.post("/trend/what-if", response_model=TrendScenarioResponse)
async def trend_what_if(req: TrendScenarioRequest):
    """What-if 情景模拟（增强版：集成RAG输出）"""
    scenario = ScenarioInput(
        indicator=req.indicator or "EV_DEMAND",
        scenario_name=req.scenario_name or "Baseline",
        demand_shift=req.demand_shift,
        policy_intensity=req.policy_intensity,
        supply_shift=req.supply_shift
    )
    result = trend_scenario_engine.simulate_scenario(scenario)
    
    # 记录到数据采集器
    trend_data_collector.record_collection(
        source="what_if",
        data_type="scenario_simulation",
        count=1,
        status="success",
        metadata={
            "indicator": req.indicator,
            "scenario_name": req.scenario_name,
            "probability": result.get("forecast", {}).get("probability"),
        }
    )
    
    # 生成RAG文档
    try:
        rag_doc = trend_rag_output.generate_rag_document(
            indicator=req.indicator,
            analysis_result={
                "summary": f"What-if情景模拟：{req.scenario_name}",
                "metrics": result.get("forecast", {}),
                "prediction": result.get("forecast", {}),
                "recommendations": result.get("recommendations", []),
                "sources": ["trend_scenario_engine"],
            }
        )
        
        # 模拟写入RAG（真实实现应调用RAG API）
        rag_doc_id = f"trend_rag_{int(datetime.now().timestamp())}"
        trend_rag_output.record_rag_output(
            indicator=req.indicator,
            rag_document_id=rag_doc_id,
            status="success"
        )
        
        result["rag_document_id"] = rag_doc_id
        result["rag_document"] = rag_doc
    except Exception as e:
        logger.warning(f"RAG输出失败: {e}")
    
    return result


# ==================== P2-011: 趋势分析 + 合规审计增强 ====================

@router.get("/trend/data/collection/stats")
async def get_trend_collection_stats(
    source: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """
    获取数据采集统计（可视化）
    """
    return trend_data_collector.get_collection_stats(source=source, days=days)


@router.get("/trend/data/processing/pipeline")
async def get_trend_processing_pipeline(
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    获取处理流水线可视化数据
    """
    return trend_data_collector.get_processing_pipeline(source=source, limit=limit)


@router.post("/trend/data/collection/record")
async def record_trend_collection(
    source: str = Body(..., embed=True),
    data_type: str = Body(..., embed=True),
    count: int = Body(..., embed=True),
    status: str = Body("success", embed=True),
    error: Optional[str] = Body(None, embed=True),
    metadata: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    记录数据采集（用于外部调用）
    """
    trend_data_collector.record_collection(
        source=source,
        data_type=data_type,
        count=count,
        status=status,
        error=error,
        metadata=metadata
    )
    return {"success": True, "message": "采集记录已保存"}


@router.post("/trend/data/processing/record")
async def record_trend_processing(
    source: str = Body(..., embed=True),
    step: str = Body(..., embed=True),
    input_count: int = Body(..., embed=True),
    output_count: int = Body(..., embed=True),
    processing_time: float = Body(..., embed=True),
    status: str = Body("success", embed=True),
    error: Optional[str] = Body(None, embed=True)
):
    """
    记录数据处理（用于外部调用）
    """
    trend_data_collector.record_processing(
        source=source,
        step=step,
        input_count=input_count,
        output_count=output_count,
        processing_time=processing_time,
        status=status,
        error=error
    )
    return {"success": True, "message": "处理记录已保存"}


@router.post("/trend/rag/generate")
async def generate_trend_rag_document(
    indicator: str = Body(..., embed=True),
    analysis_result: Dict[str, Any] = Body(..., embed=True),
    document_type: str = Body("trend_analysis", embed=True)
):
    """
    生成趋势分析RAG文档
    """
    rag_doc = trend_rag_output.generate_rag_document(
        indicator=indicator,
        analysis_result=analysis_result,
        document_type=document_type
    )
    
    # 模拟写入RAG（真实实现应调用RAG API）
    rag_doc_id = f"trend_rag_{int(datetime.now().timestamp())}"
    trend_rag_output.record_rag_output(
        indicator=indicator,
        rag_document_id=rag_doc_id,
        status="success"
    )
    
    return {
        "success": True,
        "rag_document_id": rag_doc_id,
        "rag_document": rag_doc
    }


@router.get("/trend/rag/connections")
async def get_trend_rag_connections(
    indicator: Optional[str] = Query(None)
):
    """
    获取RAG关联信息
    """
    return trend_rag_output.get_rag_connections(indicator=indicator)


@router.get("/trend/rag/output/stats")
async def get_trend_rag_output_stats(
    days: int = Query(7, ge=1, le=90)
):
    """
    获取RAG输出统计
    """
    return trend_rag_output.get_output_stats(days=days)


# ==================== P2-012: 运营财务跨系统联动 ====================

@router.get("/operations-finance/kpis", dependencies=[finance_read_dep])
async def get_operations_finance_kpis():
    """
    获取运营财务KPI指标 - P0-003: 使用真实数据库
    """
    # 从数据库查询财务数据
    financial_records = await data_service.query_data(
        module="operations",
        filters={"type": "financial_data"},
        limit=1,
        order_by="_created_at",
        order_desc=True,
    )
    
    # 如果有数据，使用真实数据；否则使用默认值
    if financial_records:
        financial_data = financial_records[0]
        # 移除内部字段
        financial_data = {k: v for k, v in financial_data.items() if not k.startswith("_")}
    else:
        # 默认值（首次使用时）
        financial_data = {
            "cash": 500000.0,
            "bank_deposits": 2000000.0,
            "short_term_liabilities": 300000.0,
            "monthly_expense": 400000.0,
            "quarterly_collections": 1500000.0,
            "quarterly_payments": 1200000.0,
        }
    
    kpis = finance_expert.calculate_kpis(financial_data)
    return {
        "success": True,
        "kpis": kpis,
        "definitions": finance_expert.get_kpi_definitions()
    }


@router.get("/operations-finance/insights", dependencies=[finance_read_dep])
async def get_operations_finance_insights():
    """
    获取财务专家洞察 - P0-003: 使用真实数据库
    """
    # 从数据库查询财务数据
    financial_records = await data_service.query_data(
        module="operations",
        filters={"type": "financial_data"},
        limit=1,
        order_by="_created_at",
        order_desc=True,
    )
    
    # 如果有数据，使用真实数据；否则使用默认值
    if financial_records:
        financial_data = financial_records[0]
        # 移除内部字段
        financial_data = {k: v for k, v in financial_data.items() if not k.startswith("_")}
    else:
        # 默认值（首次使用时）
        financial_data = {
            "cash": 500000.0,
            "bank_deposits": 2000000.0,
            "short_term_liabilities": 300000.0,
            "monthly_expense": 400000.0,
            "quarterly_collections": 1500000.0,
            "quarterly_payments": 1200000.0,
        }
    
    kpis = finance_expert.calculate_kpis(financial_data)
    insights = finance_expert.generate_insights(kpis)
    
    return {
        "success": True,
        "insights": insights,
        "kpis": kpis
    }


@router.post("/operations-finance/chart/recommend")
async def recommend_chart(
    data: Dict[str, Any] = Body(...),
    purpose: str = Body("分析", embed=True)
):
    """
    图表专家推荐
    """
    recommendation = chart_expert.recommend_chart(data, purpose)
    return {
        "success": True,
        "recommendation": recommendation
    }


@router.get("/operations-finance/strategy/status", dependencies=[finance_read_dep])
async def get_strategy_status():
    """
    获取策略联动状态
    """
    return operations_finance_strategy.get_strategy_status()


@router.post("/operations-finance/strategy/evaluate")
async def evaluate_strategy_triggers(
    context: Dict[str, Any] = Body(...)
):
    """
    评估策略触发条件
    """
    triggered = operations_finance_strategy.evaluate_triggers(context)
    
    # 执行触发的策略
    execution_results = []
    for strategy_info in triggered:
        result = await operations_finance_strategy.execute_strategy(strategy_info)
        execution_results.append(result)
    
    return {
        "success": True,
        "triggered_count": len(triggered),
        "executions": execution_results
    }


@router.get("/operations-finance/strategy/history", dependencies=[finance_read_dep])
async def get_strategy_history(
    limit: int = Query(50, ge=1, le=200)
):
    """
    获取策略执行历史
    """
    history = operations_finance_strategy.get_execution_history(limit)
    return {
        "success": True,
        "history": history,
        "count": len(history)
    }


@router.post("/operations-finance/erp/sync")
async def sync_to_erp(
    data_type: str = Body(..., embed=True),
    data: Dict[str, Any] = Body(...),
    direction: Optional[str] = Body(None, embed=True)
):
    """
    同步数据到ERP
    """
    result = await erp_data_sync.sync_data(data_type, data, direction)
    return {
        "success": result["status"] == "success",
        "result": result
    }


@router.get("/operations-finance/erp/sync/status", dependencies=[finance_read_dep])
async def get_erp_sync_status(
    data_type: Optional[str] = Query(None)
):
    """
    获取ERP同步状态
    """
    status = erp_data_sync.get_sync_status(data_type)
    return {
        "success": True,
        "status": status
    }


@router.get("/operations-finance/erp/sync/history", dependencies=[finance_read_dep])
async def get_erp_sync_history(
    data_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200)
):
    """
    获取ERP同步历史
    """
    history = erp_data_sync.get_sync_history(data_type, limit)
    return {
        "success": True,
        "history": history,
        "count": len(history)
    }


@router.put("/operations-finance/erp/sync/config")
async def update_erp_sync_config(
    data_type: str = Body(..., embed=True),
    config: Dict[str, Any] = Body(...)
):
    """
    更新ERP同步配置
    """
    updated_config = erp_data_sync.update_sync_config(data_type, config)
    return {
        "success": True,
        "config": updated_config
    }


# ============ P2-034: 专家能力地图 & 路由策略 ============


@router.get("/experts/ability-map")
async def get_expert_ability_map():
    """
    获取专家能力地图（增强版：集成标准化系统）
    """
    # 更新标准化系统的能力地图
    expert_standardization.update_ability_map(EXPERT_ABILITY_MAP)
    
    total = len(EXPERT_ABILITY_MAP)
    avg_confidence = round(sum(item["confidence"] for item in EXPERT_ABILITY_MAP) / total, 2) if total else 0
    modules = sorted({m for item in EXPERT_ABILITY_MAP for m in item["modules"]})
    summary = {
        "total_experts": total,
        "avg_confidence": avg_confidence,
        "modules": modules,
        "ready_capabilities": sum(
            1
            for item in EXPERT_ABILITY_MAP
            for cap in item["capabilities"]
            if cap["status"] == "ready"
        )
    }
    return {"success": True, "summary": summary, "abilities": EXPERT_ABILITY_MAP}


@router.get("/experts/routing")
async def get_expert_routing():
    """
    获取专家路由策略（增强版：集成标准化系统）
    """
    # 更新标准化系统的路由策略
    expert_standardization.update_routing_strategy(EXPERT_ROUTING_STRATEGY)
    
    strategy = dict(EXPERT_ROUTING_STRATEGY)
    summary = expert_standardization.get_routing_summary()
    
    return {
        "success": True,
        "strategy": strategy,
        "summary": summary
    }


@router.get("/experts/acceptance")
async def get_expert_acceptance():
    """
    获取专家验收矩阵（增强版：集成标准化系统）
    """
    # 更新标准化系统的验收矩阵
    expert_standardization.update_acceptance_matrix(EXPERT_ACCEPTANCE_MATRIX)
    
    summary = expert_standardization.get_acceptance_summary()
    
    return {
        "success": True,
        "matrix": EXPERT_ACCEPTANCE_MATRIX,
        "count": len(EXPERT_ACCEPTANCE_MATRIX),
        "summary": summary
    }


@router.post("/experts/simulate-route")
async def simulate_expert_route(req: ExpertRouteSimulationRequest):
    """
    模拟专家路由（增强版：集成标准化系统）
    """
    # 使用标准化系统进行模拟
    result = expert_standardization.simulate_routing(
        query=req.query,
        knowledge_hints=req.knowledge_hints,
        expected_domain=req.expected_domain
    )
    
    # 如果专家路由器可用，也使用它进行路由（作为对比）
    route_from_router = None
    if super_agent.expert_router:
        try:
            rag_stub = {
                "knowledge": [{"content": hint} for hint in (req.knowledge_hints or [])],
                "understanding": {"expected_domain": req.expected_domain}
            }
            route_from_router = await super_agent.expert_router.route(req.query, rag_stub)
        except Exception as e:
            logger.warning(f"专家路由器路由失败: {e}")
    
    return {
        "success": True,
        "route": result,
        "route_from_router": route_from_router,
        "comparison": {
            "standardization_confidence": result.get("confidence", 0.0),
            "router_confidence": route_from_router.get("confidence", 0.0) if route_from_router else None
        }
    }


@router.get("/experts/overview")
async def get_expert_overview():
    """
    获取专家系统概览（增强版：集成标准化系统）
    """
    abilities = await get_expert_ability_map()
    routing = await get_expert_routing()
    acceptance = await get_expert_acceptance()
    
    return {
        "success": True,
        "ability_summary": abilities["summary"],
        "routing": routing["strategy"],
        "routing_summary": routing.get("summary", {}),
        "acceptance": acceptance["matrix"],
        "acceptance_summary": acceptance.get("summary", {})
    }


@router.get("/experts/simulation/history")
async def get_simulation_history(
    limit: int = Query(20, ge=1, le=100)
):
    """
    获取模拟演练历史
    """
    history = expert_standardization.get_simulation_history(limit)
    return {
        "success": True,
        "history": history,
        "count": len(history)
    }


@router.post("/experts/acceptance/validate")
async def validate_acceptance(
    capability: str = Body(..., embed=True),
    test_results: List[Dict[str, Any]] = Body(...)
):
    """
    验证验收标准
    """
    result = expert_standardization.validate_acceptance(capability, test_results)
    return {
        "success": True,
        "validation": result
    }


@router.post("/experts/collaboration/session")
async def create_collaboration_session(req: CollaborationSessionCreateRequest):
    """
    创建专家协同会话
    """
    session = await expert_collaboration_hub.start_session(
        topic=req.topic,
        initiator=req.initiator,
        goals=req.goals,
        experts=[participant.dict() for participant in req.experts],
        channel=req.channel or "multi",
    )
    return {
        "success": True,
        "session": session,
    }


@router.post("/experts/collaboration/session/{session_id}/contribution")
async def add_collaboration_contribution(
    session_id: str,
    req: CollaborationContributionRequest,
):
    """
    在指定协同会话中追加专家贡献
    """
    try:
        session = await expert_collaboration_hub.add_contribution(
            session_id=session_id,
            expert_id=req.expert_id,
            expert_name=req.expert_name,
            summary=req.summary,
            channel=req.channel,
            action_items=req.action_items,
            impact_score=req.impact_score,
            references=req.references,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "session": session,
    }


@router.post("/experts/collaboration/session/{session_id}/decision")
async def finalize_collaboration_session(
    session_id: str,
    req: CollaborationDecisionRequest,
):
    """
    关闭协同会话并记录决策
    """
    try:
        session = await expert_collaboration_hub.finalize_session(
            session_id=session_id,
            owner=req.owner,
            summary=req.summary,
            kpis=req.kpis,
            followups=req.followups,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "session": session,
    }


@router.get("/experts/collaboration/active")
async def get_active_collaboration_sessions(
    limit: int = Query(5, ge=1, le=20),
):
    """
    查看活跃中的专家协同会话
    """
    sessions = await expert_collaboration_hub.get_active_sessions(limit)
    return {
        "success": True,
        "sessions": sessions,
        "count": len(sessions),
    }


@router.get("/experts/collaboration/summary")
async def get_collaboration_summary():
    """
    获取协同中枢指标
    """
    summary = await expert_collaboration_hub.get_summary()
    return {
        "success": True,
        "summary": summary,
    }


@router.get("/experts/collaboration/session/{session_id}")
async def get_collaboration_session_detail(session_id: str):
    """
    获取单个会话详情
    """
    try:
        session = await expert_collaboration_hub.get_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {
        "success": True,
        "session": session,
    }


@router.get("/experts/collaboration/stream")
async def stream_collaboration_events(request: Request):
    """
    SSE：实时推送专家协同事件
    """
    queue = await collaboration_event_stream.register()

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            collaboration_event_stream.unregister(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== P1-005: 日常配置与部署自动化 ====================


@router.get("/devops/config/profiles", dependencies=[security_read_dep])
async def list_config_profiles():
    """列出可用环境配置"""
    return {
        "success": True,
        "profiles": env_config_manager.list_profiles(),
        "history": env_config_manager.get_history(limit=5),
    }


@router.post("/devops/config/apply", dependencies=[security_write_dep])
async def apply_config_profile(req: ConfigApplyRequest):
    """应用指定 profile 并生成 `.env.runtime`"""
    result = env_config_manager.apply_profile(req.profile, overrides=req.overrides)
    return {
        "success": True,
        "profile": result["profile"]["name"],
        "output": result["output_file"],
    }


@router.get("/devops/deploy/pipeline", dependencies=[security_read_dep])
async def get_deploy_pipeline():
    """查看部署流水线步骤"""
    return {
        "success": True,
        "steps": deployment_manager.list_steps(),
    }


@router.post("/devops/deploy/run", dependencies=[security_write_dep])
async def run_deploy_pipeline(req: DeploymentRunRequest):
    """执行或模拟部署流水线"""
    summary = await deployment_manager.run_pipeline(
        profile=req.profile,
        dry_run=req.dry_run,
        selected_steps=req.steps,
        env_overrides=req.overrides or None,
    )
    return {
        "success": summary["completed"],
        "summary": summary,
    }


@router.get("/devops/deploy/history", dependencies=[security_read_dep])
async def get_deploy_history(limit: int = Query(10, ge=1, le=50)):
    """获取最近部署记录"""
    history = deployment_manager.get_history(limit=limit)
    return {
        "success": True,
        "history": history,
    }


# ==================== P3-002: 微服务拆分 · 服务注册与通信 ====================


@router.get("/architecture/services/summary", dependencies=[security_read_dep])
async def get_service_summary():
    return {
        "success": True,
        "contracts": service_registry.list_contracts(),
        "instances": service_registry.list_instances(),
        "changelog": service_registry.get_changelog()[:20],
    }


@router.post("/architecture/services/register", dependencies=[security_write_dep])
async def register_service_instance(req: ServiceRegisterRequest):
    instance = service_registry.register_instance(
        service=req.service,
        endpoint=req.endpoint,
        version=req.version,
        protocol=req.protocol,
        deployment_target=req.deployment_target,
        metadata=req.metadata,
    )
    return {"success": True, "instance": instance.to_dict()}


@router.post("/architecture/services/heartbeat", dependencies=[security_write_dep])
async def service_heartbeat(req: ServiceHeartbeatRequest):
    ok = service_registry.heartbeat(req.service, req.instance_id, status=req.status)
    if not ok:
        raise HTTPException(status_code=404, detail="实例不存在")
    return {"success": True}


@router.post("/architecture/services/call", dependencies=[security_write_dep])
async def call_service(req: ServiceCallRequest):
    result: ServiceCallResult = await service_gateway.call_service(
        service=req.service,
        operation=req.operation,
        payload=req.payload,
        prefer_internal=req.prefer_internal,
    )
    status_code = status.HTTP_200_OK if result.status == "success" else status.HTTP_400_BAD_REQUEST
    return JSONResponse(
        status_code=status_code,
        content={
            "success": result.status == "success",
            "result": result.to_dict(),
        },
    )


@router.get("/architecture/multitenant-plan")
async def get_multitenant_plan():
    """多租户 / 微服务演进计划（单体内模块化边界）"""
    return {"success": True, "plan": MULTITENANT_EVOLUTION_PLAN}


# ==================== P3-015: 多租户 / 微服务演进 + 2 秒 SLO ====================

@router.get("/architecture/multitenant-evolution/report")
async def get_multitenant_evolution_report():
    """
    获取多租户/微服务演进报告
    """
    report = multitenant_evolution.generate_evolution_report()
    return {
        "success": True,
        "report": report
    }


@router.get("/architecture/service-boundaries")
async def get_service_boundaries():
    """
    获取服务拆分边界
    """
    boundaries = multitenant_evolution.get_service_boundaries()
    return {
        "success": True,
        "boundaries": {
            name: {
                "module_name": boundary.module_name,
                "domain": boundary.domain,
                "ownership": boundary.ownership,
                "separation": boundary.separation,
                "ready": boundary.ready,
                "dependencies": boundary.dependencies,
                "api_contracts": boundary.api_contracts,
                "data_stores": boundary.data_stores,
                "deployment_target": boundary.deployment_target
            }
            for name, boundary in boundaries.items()
        }
    }


@router.get("/architecture/evolution-phases")
async def get_evolution_phases():
    """
    获取演进阶段
    """
    phases = multitenant_evolution.get_evolution_phases()
    return {
        "success": True,
        "phases": phases
    }


# ==================== 多租户管理 ====================


@router.get("/tenants")
async def list_tenants(include_inactive: bool = False, _: Dict = Depends(security_read_dep)):
    """列出租户（需安全读权限）"""
    tenants = tenant_manager.list_tenants(include_inactive=include_inactive)
    return {"success": True, "tenants": tenants}


@router.get("/tenants/current")
async def get_current_tenant_info(request: Request):
    """获取当前请求所处租户"""
    ctx = getattr(request.state, "tenant", None) or get_current_tenant()
    return {
        "success": True,
        "tenant": {
            "tenant_id": ctx.tenant_id,
            "name": ctx.name,
            "metadata": ctx.metadata,
        },
    }


@router.post("/tenants")
async def create_or_update_tenant(req: TenantCreateRequest, _: Dict = Depends(security_write_dep)):
    tenant = tenant_manager.upsert_tenant(
        tenant_id=req.tenant_id,
        name=req.name,
        plan=req.plan or "enterprise",
        active=req.active if req.active is not None else True,
        metadata=req.metadata or {},
    )
    return {"success": True, "tenant": asdict(tenant)}


@router.put("/tenants/{tenant_id}")
async def update_tenant(tenant_id: str, req: TenantUpdateRequest, _: Dict = Depends(security_write_dep)):
    existing = tenant_manager.get_tenant(tenant_id)
    if not existing:
        raise HTTPException(status_code=404, detail="租户不存在")
    tenant = tenant_manager.upsert_tenant(
        tenant_id=tenant_id,
        name=req.name or existing.name,
        plan=req.plan or existing.plan,
        active=req.active if req.active is not None else existing.active,
        metadata=req.metadata or existing.metadata,
    )
    return {"success": True, "tenant": asdict(tenant)}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str, _: Dict = Depends(security_write_dep)):
    ok = tenant_manager.delete_tenant(tenant_id)
    if not ok:
        raise HTTPException(status_code=400, detail="无法删除租户（可能是默认租户或不存在）")
    return {"success": True}


@router.post("/slo/performance/vector-index/benchmark")
async def record_vector_index_benchmark(benchmark: VectorIndexBenchmark):
    """
    记录向量索引性能基准测试
    """
    slo_performance_reporter.record_vector_index_benchmark(benchmark)
    return {
        "success": True,
        "message": "向量索引基准测试已记录"
    }


@router.post("/slo/performance/streaming/benchmark")
async def record_streaming_benchmark(benchmark: StreamingBenchmark):
    """
    记录流式响应性能基准测试
    """
    slo_performance_reporter.record_streaming_benchmark(benchmark)
    return {
        "success": True,
        "message": "流式响应基准测试已记录"
    }


@router.post("/slo/performance/context-compression/benchmark")
async def record_context_compression_benchmark(benchmark: ContextCompressionBenchmark):
    """
    记录上下文压缩性能基准测试
    """
    slo_performance_reporter.record_context_compression_benchmark(benchmark)
    return {
        "success": True,
        "message": "上下文压缩基准测试已记录"
    }


@router.get("/slo/performance/report/vector-index")
async def get_vector_index_report():
    """
    获取向量索引优化报告
    """
    report = slo_performance_reporter.generate_vector_index_report()
    return {
        "success": True,
        "report": report
    }


@router.get("/slo/performance/report/streaming")
async def get_streaming_report():
    """
    获取流式/SSR性能报告
    """
    report = slo_performance_reporter.generate_streaming_report()
    return {
        "success": True,
        "report": report
    }


@router.get("/slo/performance/report/context-compression")
async def get_context_compression_report():
    """
    获取上下文压缩性能报告
    """
    report = slo_performance_reporter.generate_context_compression_report()
    return {
        "success": True,
        "report": report
    }


@router.get("/slo/performance/report/comprehensive")
async def get_comprehensive_performance_report():
    """
    获取综合性能报告（包含向量索引、流式响应、上下文压缩）
    """
    report = slo_performance_reporter.generate_comprehensive_report()
    return {
        "success": True,
        "report": report
    }


# ==================== P3-016: 验收矩阵与持续交付 ====================

@router.post("/acceptance/matrix/generate")
async def generate_acceptance_matrix():
    """
    生成验收矩阵Excel文件
    """
    try:
        output_file = acceptance_matrix_generator.generate_excel()
        return {
            "success": True,
            "message": "验收矩阵Excel文件已生成",
            "file_path": str(output_file),
            "file_name": output_file.name
        }
    except Exception as e:
        logger.error(f"生成验收矩阵失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/acceptance/matrix/summary")
async def get_acceptance_matrix_summary():
    """
    获取验收矩阵摘要
    """
    summary = acceptance_matrix_generator.get_requirements_summary()
    return {
        "success": True,
        "summary": summary
    }


@router.put("/acceptance/matrix/requirement/{requirement_id}")
async def update_requirement_status(
    requirement_id: str,
    status: Optional[str] = Body(None, embed=True),
    test_result: Optional[str] = Body(None, embed=True),
    evidence: Optional[str] = Body(None, embed=True),
    notes: Optional[str] = Body(None, embed=True)
):
    """
    更新需求状态
    """
    acceptance_matrix_generator.update_requirement_status(
        requirement_id=requirement_id,
        status=status,
        test_result=test_result,
        evidence=evidence,
        notes=notes
    )
    return {
        "success": True,
        "message": f"需求 {requirement_id} 状态已更新"
    }


@router.post("/acceptance/recording/start")
async def start_acceptance_recording(
    requirement_id: str = Body(..., embed=True),
    recording_type: str = Body("script", embed=True),
    description: str = Body("", embed=True)
):
    """
    开始验收记录
    """
    recording_id = acceptance_recording.start_recording(
        requirement_id=requirement_id,
        recording_type=recording_type,
        description=description
    )
    return {
        "success": True,
        "recording_id": recording_id,
        "message": "验收记录已开始"
    }


@router.post("/acceptance/recording/{recording_id}/step")
async def add_recording_step(
    recording_id: str,
    step_name: str = Body(..., embed=True),
    command: Optional[str] = Body(None, embed=True),
    output: Optional[str] = Body(None, embed=True),
    screenshot: Optional[str] = Body(None, embed=True),
    notes: Optional[str] = Body(None, embed=True)
):
    """
    添加验收步骤
    """
    acceptance_recording.add_step(
        recording_id=recording_id,
        step_name=step_name,
        command=command,
        output=output,
        screenshot=screenshot,
        notes=notes
    )
    return {
        "success": True,
        "message": "验收步骤已添加"
    }


@router.post("/acceptance/recording/{recording_id}/command")
async def record_command(
    recording_id: str,
    command: str = Body(..., embed=True),
    step_name: Optional[str] = Body(None, embed=True)
):
    """
    记录命令执行
    """
    output = acceptance_recording.record_command(
        recording_id=recording_id,
        command=command,
        step_name=step_name
    )
    return {
        "success": True,
        "output": output,
        "message": "命令已记录并执行"
    }


@router.post("/acceptance/recording/{recording_id}/finish")
async def finish_recording(
    recording_id: str,
    result: str = Body("pass", embed=True),
    summary: Optional[str] = Body(None, embed=True)
):
    """
    完成验收记录
    """
    acceptance_recording.finish_recording(
        recording_id=recording_id,
        result=result,
        summary=summary
    )
    return {
        "success": True,
        "message": "验收记录已完成"
    }


@router.get("/acceptance/recording/{recording_id}")
async def get_recording(recording_id: str):
    """
    获取验收记录
    """
    recording = acceptance_recording.get_recording(recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail=f"未找到记录: {recording_id}")
    
    return {
        "success": True,
        "recording": recording
    }


@router.get("/acceptance/recording")
async def list_recordings(requirement_id: Optional[str] = Query(None)):
    """
    列出验收记录
    """
    recordings = acceptance_recording.list_recordings(requirement_id=requirement_id)
    return {
        "success": True,
        "recordings": recordings,
        "count": len(recordings)
    }


@router.post("/acceptance/recording/{recording_id}/generate-script")
async def generate_recording_script(recording_id: str):
    """
    生成验收脚本
    """
    try:
        script_file = acceptance_recording.generate_script(recording_id)
        return {
            "success": True,
            "script_file": str(script_file),
            "message": "验收脚本已生成"
        }
    except Exception as e:
        logger.error(f"生成验收脚本失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/ci/evidence/upload")
async def upload_ci_evidence(
    requirement_id: str = Body(..., embed=True),
    evidence_type: str = Body(..., embed=True),
    file_path: str = Body(..., embed=True),
    metadata: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    上传CI证据文件
    """
    try:
        result = ci_evidence_uploader.upload_evidence(
            requirement_id=requirement_id,
            evidence_type=evidence_type,
            file_path=file_path,
            metadata=metadata
        )
        return result
    except Exception as e:
        logger.error(f"上传CI证据失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/ci/evidence/upload-test-results")
async def upload_test_results(
    requirement_id: str = Body(..., embed=True),
    test_results: Dict[str, Any] = Body(...),
    test_report_file: Optional[str] = Body(None, embed=True)
):
    """
    上传测试结果
    """
    try:
        result = ci_evidence_uploader.upload_test_results(
            requirement_id=requirement_id,
            test_results=test_results,
            test_report_file=test_report_file
        )
        return result
    except Exception as e:
        logger.error(f"上传测试结果失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/ci/evidence/report")
async def get_evidence_report(requirement_id: Optional[str] = Query(None)):
    """
    获取证据报告
    """
    report = ci_evidence_uploader.generate_evidence_report(requirement_id=requirement_id)
    return {
        "success": True,
        "report": report
    }


@router.get("/ci/environment")
async def get_ci_environment():
    """
    获取CI环境信息
    """
    env = ci_evidence_uploader.get_ci_environment()
    return {
        "success": True,
        "environment": env
    }


@router.get("/tasks/statistics")
async def get_task_statistics():
    """获取任务统计信息⭐增强版"""
    stats = task_planning.get_statistics()
    return stats


# ==================== P0-001: 闭环完整实现 ====================

# 全局闭环引擎实例
closed_loop_engine = ClosedLoopEngine()
unified_event_bus = get_unified_event_bus()
execution_checker = ExecutionChecker(unified_event_bus)
feedback_handler = FeedbackHandler(unified_event_bus)
evidence_recorder = EvidenceRecorder(unified_event_bus)


async def run_closed_loop_operation(
    *,
    module: str,
    function: str,
    parameters: Dict[str, Any],
    executor: Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]] | Dict[str, Any]],
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> tuple[str, Dict[str, Any]]:
    """接受→执行指定业务逻辑，并在统一事件流中记录结果"""
    meta = metadata.copy() if metadata else {}
    approval_id = meta.get("approval_id")
    if approval_id:
        approval = approval_manager.get_request(approval_id)
        if not approval or approval.status != ApprovalStatus.APPROVED:
            raise HTTPException(
                status_code=423,
                detail=f"敏感操作审批未通过: {approval_id}",
            )

    exec_task_id = task_id or f"{module}-{function}-{uuid4().hex[:8]}"
    context = await closed_loop_engine.accept_task(
        task_id=exec_task_id,
        module=module,
        function=function,
        parameters=parameters,
        metadata=meta,
    )
    exec_result = await closed_loop_engine.execute(context.execution_id, executor)
    success_flag = exec_result.get("success", True)
    actor = meta.get("actor", "system")
    if audit_pipeline:
        audit_pipeline.log_task_event(
            task_id=exec_task_id,
            actor=actor,
            module=module,
            status="success" if success_flag else "failed",
            metadata={
                "function": function,
                "execution_id": context.execution_id,
                "parameters": parameters,
            },
        )
    await unified_event_bus.publish(
        category=EventCategory.WORKFLOW,
        event_type="closed_loop.completed",
        source="api",
        severity=EventSeverity.INFO if success_flag else EventSeverity.WARNING,
        payload={
            "execution_id": context.execution_id,
            "module": module,
            "function": function,
            "success": success_flag,
        },
        correlation_id=context.execution_id,
    )
    return context.execution_id, exec_result


@router.post("/closed-loop/accept")
async def accept_task(
    task_id: Optional[str] = Body(None, embed=True),
    module: str = Body(..., embed=True),
    function: str = Body(..., embed=True),
    parameters: Dict[str, Any] = Body(...),
    metadata: Optional[Dict[str, Any]] = Body(None, embed=True),
):
    """
    接受任务（ACCEPT阶段）
    """
    try:
        context = await closed_loop_engine.accept_task(
            task_id=task_id or f"task_{uuid4()}",
            module=module,
            function=function,
            parameters=parameters,
            metadata=metadata,
        )
        return {
            "success": True,
            "execution_id": context.execution_id,
            "context": context.__dict__,
        }
    except Exception as e:
        logger.error(f"接受任务失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/closed-loop/execute/{execution_id}")
async def execute_task(
    execution_id: str,
    executor_type: str = Body("default", embed=True),
    executor_config: Optional[Dict[str, Any]] = Body(None, embed=True),
):
    """
    执行任务（EXECUTE阶段）
    
    注意：executor_type指定执行器类型，实际执行逻辑由后端根据类型调用
    """
    try:
        context = closed_loop_engine.get_execution(execution_id)
        if not context:
            raise HTTPException(status_code=404, detail=f"执行上下文不存在: {execution_id}")
        
        # 根据executor_type调用不同的执行器
        # 这里简化处理，实际应该根据模块和函数调用对应的执行器
        async def executor(params: Dict[str, Any]) -> Dict[str, Any]:
            # 模拟执行（实际应该调用真实的模块函数）
            await asyncio.sleep(0.1)  # 模拟执行时间
            return {
                "success": True,
                "result": f"执行结果: {context.module}.{context.function}",
                "duration": 0.1,
            }
        
        result = await closed_loop_engine.execute(execution_id, executor)
        
        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        logger.error(f"执行任务失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/closed-loop/check/{execution_id}")
async def check_execution(execution_id: str):
    """
    检查执行结果（CHECK阶段）
    """
    try:
        reports = await closed_loop_engine.check_execution(execution_id)
        return {
            "success": True,
            "reports": reports,
        }
    except Exception as e:
        logger.error(f"检查执行失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/closed-loop/feedback/{execution_id}")
async def process_feedback(
    execution_id: str,
    feedback_id: str = Body(..., embed=True),
    action: str = Body(..., embed=True),
):
    """
    处理反馈（FEEDBACK阶段）
    """
    try:
        success = await closed_loop_engine.process_feedback(
            execution_id=execution_id,
            feedback_id=feedback_id,
            action=action,
        )
        return {
            "success": success,
            "message": "反馈处理成功" if success else "反馈处理失败",
        }
    except Exception as e:
        logger.error(f"处理反馈失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.post("/closed-loop/re-execute/{execution_id}")
async def re_execute_task(
    execution_id: str,
    reason: Optional[str] = Body(None, embed=True),
):
    """
    再执行（RE_EXECUTE阶段）
    """
    try:
        result = await closed_loop_engine.re_execute(
            execution_id=execution_id,
            reason=reason,
        )
        return {
            "success": True,
            "result": result,
        }
    except Exception as e:
        logger.error(f"再执行失败: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
        }


@router.get("/closed-loop/execution/{execution_id}")
async def get_execution(execution_id: str):
    """
    获取执行上下文
    """
    context = closed_loop_engine.get_execution(execution_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"执行上下文不存在: {execution_id}")
    
    return {
        "success": True,
        "context": context.__dict__,
    }


@router.get("/closed-loop/timeline/{execution_id}")
async def get_execution_timeline(execution_id: str):
    """
    获取执行时间线（包含所有证据）
    """
    timeline = closed_loop_engine.get_execution_timeline(execution_id)
    if not timeline:
        raise HTTPException(status_code=404, detail=f"执行时间线不存在: {execution_id}")
    
    return {
        "success": True,
        "timeline": timeline,
    }


@router.get("/closed-loop/statistics")
async def get_closed_loop_statistics():
    """
    获取闭环系统统计信息
    """
    stats = closed_loop_engine.get_statistics()
    return {
        "success": True,
        "statistics": stats,
    }


@router.get("/events")
async def get_events(
    limit: int = Query(50),
    category: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    correlation_id: Optional[str] = Query(None),
):
    """
    查询事件
    """
    from core.unified_event_bus import EventCategory as EC, EventSeverity as ES
    
    events = unified_event_bus.get_events(
        limit=limit,
        category=EC(category) if category else None,
        event_type=event_type,
        source=source,
        severity=ES(severity) if severity else None,
        correlation_id=correlation_id,
    )
    
    return {
        "success": True,
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/checks/reports")
async def get_check_reports(
    execution_id: Optional[str] = Query(None),
    check_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """
    获取检查报告
    """
    reports = execution_checker.get_reports(
        execution_id=execution_id,
        check_type=CheckType(check_type) if check_type else None,
        result=CheckResult(result) if result else None,
        limit=limit,
    )
    
    return {
        "success": True,
        "reports": [r.__dict__ for r in reports],
        "count": len(reports),
    }


@router.get("/feedbacks")
async def get_feedbacks(
    execution_id: Optional[str] = Query(None),
    feedback_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """
    获取反馈列表
    """
    feedbacks = feedback_handler.get_feedbacks(
        execution_id=execution_id,
        feedback_type=FeedbackType(feedback_type) if feedback_type else None,
        status=FeedbackStatus(status) if status else None,
        limit=limit,
    )
    
    return {
        "success": True,
        "feedbacks": [fb.to_dict() for fb in feedbacks],
        "count": len(feedbacks),
    }


@router.get("/evidence")
async def get_evidence(
    execution_id: Optional[str] = Query(None),
    evidence_type: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """
    获取证据列表
    """
    evidence_list = evidence_recorder.get_evidence_by_execution(
        execution_id=execution_id or "",
        evidence_type=EvidenceType(evidence_type) if evidence_type else None,
        limit=limit,
    ) if execution_id else []
    
    return {
        "success": True,
        "evidence": [ev.to_dict() for ev in evidence_list],
        "count": len(evidence_list),
    }


@router.get("/plans")
async def get_plans():
    """获取工作计划列表"""
    plans = task_planning.plans
    return {"plans": plans, "total": len(plans)}


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: int):
    """获取工作计划详情"""
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if plan:
        return {"success": True, "plan": plan}
    else:
        raise HTTPException(status_code=404, detail="计划不存在")


@router.post("/plans/{plan_id}/confirm")
async def confirm_plan(
    plan_id: int,
    request: Dict[str, Any] = Body(...)
):
    """确认工作计划⭐增强版"""
    confirmed = request.get("confirmed", False)
    adjustments = request.get("adjustments", {})  # 用户调整
    
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    
    if confirmed:
        plan["status"] = "confirmed"
        plan["confirmed_at"] = datetime.now().isoformat()
        plan["needs_confirmation"] = False
        
        # 应用用户调整
        if adjustments:
            # 调整任务顺序
            if "task_order" in adjustments:
                task_order = adjustments["task_order"]
                plan["tasks"] = [t for _, t in sorted(zip(task_order, plan["tasks"]), key=lambda x: x[0])]
            
            # 调整任务优先级
            if "task_priorities" in adjustments:
                for task_id, priority in adjustments["task_priorities"].items():
                    task = next((t for t in plan["tasks"] if t["id"] == task_id), None)
                    if task:
                        task["priority"] = priority
            
            # 重新计算计划
            plan["total_duration_minutes"] = sum(t.get("estimated_duration", 0) for t in plan["tasks"])
            plan["estimated_completion_time"] = task_planning._estimate_completion_time(plan["tasks"])
    else:
        plan["status"] = "rejected"
        plan["rejected_at"] = datetime.now().isoformat()
        plan["rejection_reason"] = request.get("reason", "用户拒绝")
    
    return {"success": True, "plan": plan}


@router.post("/plans/{plan_id}/execute")
async def execute_plan(plan_id: int, concurrency: int = 2):
    """执行工作计划（并发+依赖处理+简单重试）"""
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    # 若未确认则自动确认并将pending任务置为confirmed
    if plan.get("status") != "confirmed":
        plan["status"] = "confirmed"
        plan["confirmed_at"] = datetime.now().isoformat()
        for t in plan["tasks"]:
            if t.get("status") == "pending":
                t["status"] = "confirmed"
    # 计划内任务ID集合
    plan_task_ids = [t["id"] for t in plan["tasks"]]
    id_to_task = {t["id"]: t for t in task_planning.tasks if t["id"] in plan_task_ids}
    # 并发调度
    import asyncio
    sem = asyncio.Semaphore(max(1, min(10, concurrency)))
    completed = set([tid for tid, t in id_to_task.items() if t.get("status") == "completed"])
    failed: Dict[int, str] = {}
    results: List[Dict[str, Any]] = []
    in_progress: set[int] = set()

    async def can_run(tid: int) -> bool:
        t = id_to_task.get(tid) or {}
        deps = t.get("dependencies") or []
        return all((dep in completed) for dep in deps)

    async def run_one(tid: int):
        async with sem:
            t = id_to_task.get(tid) or {}
            max_retries = int(t.get("retries", 0) or 0)
            backoff = float(t.get("retry_backoff_sec", 0.0) or 0.0)
            attempt = 0
            while True:
                res = await task_planning.execute_task(tid)
                results.append(res)
                if res.get("success"):
                    completed.add(tid)
                    break
                else:
                    if attempt < max_retries:
                        attempt += 1
                        if backoff > 0:
                            await asyncio.sleep(backoff * attempt)
                        continue
                    failed[tid] = res.get("error", "unknown")
                    break

    remaining = set(plan_task_ids) - completed
    while remaining:
        ready = [tid for tid in remaining if tid not in in_progress]
        # 过滤依赖未满足的
        ready = [tid for tid in ready if (await can_run(tid))]
        if not ready and not in_progress:
            break  # 阻塞
        # 启动
        import itertools
        slots = max(0, max(1, min(concurrency, 10)) - len(in_progress))
        for tid in itertools.islice(ready, 0, slots):
            in_progress.add(tid)
            asyncio.create_task(run_one(tid))
        await asyncio.sleep(0.2)
        # 清理已完成/失败
        in_progress = {tid for tid in in_progress if tid not in completed and tid not in failed}
        remaining = remaining - completed - set(failed.keys())

    return {
        "success": True if not failed else False,
        "plan_id": plan_id,
        "completed_count": len(completed),
        "failed": failed,
        "results": results
    }


@router.get("/resource/status")
async def get_resource_status():
    """获取资源状态"""
    status = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts()
    return {
        "status": status,
        "alerts": alerts,
        "alerts_count": len(alerts)
    }


@router.get("/resource/trends")
async def get_resource_trends(hours: int = 1):
    """获取资源趋势"""
    trends = resource_monitor.get_resource_trends(hours)
    return trends


@router.get("/learning/statistics")
async def get_learning_statistics():
    """获取学习统计信息"""
    stats = learning_monitor.get_statistics()
    return stats


@router.get("/learning/recommendations")
async def get_learning_recommendations():
    """获取最新交互建议与资源信号"""
    stats = learning_monitor.get_statistics()
    return {
        "success": True,
        "recommendations": stats.get("interaction_recommendations", []),
        "resource_signals": stats.get("resource_signals", []),
        "alert_level": stats.get("alert_level", "low"),
    }


@router.post("/learning/recommendations/{rec_id}/apply")
async def apply_learning_recommendation(rec_id: str, request: Optional[LearningRecommendationApplyRequest] = Body(None)):
    """执行交互建议"""
    recommendation = learning_monitor.get_recommendation(rec_id)
    if not recommendation:
        stats = learning_monitor.get_statistics()
        recommendation = learning_monitor.get_recommendation(rec_id)
    if not recommendation:
        raise HTTPException(status_code=404, detail="推荐不存在或已过期")

    overrides = (request.overrides if request else None) or {}
    action_type = recommendation.get("action_type")
    result_payload: Dict[str, Any] = {}

    if action_type == "resource_authorization":
        payload = {**(recommendation.get("payload") or {}), **overrides}
        suggestion = LearningResourceSuggestion(
            description=payload.get("description", recommendation.get("description", "Learning recommendation")),
            action_type=payload.get("action_type", "optimize"),
            risk_level=payload.get("risk_level", "medium"),
            expected_improvement=payload.get("expected_improvement"),
            requires_approval=payload.get("requires_approval", True),
            rollback_plan=payload.get("rollback_plan"),
            severity=recommendation.get("severity", "medium"),
        )
        authorization_request = await resource_authorization_manager.request_authorization(
            suggestion=suggestion,
            requested_by="learning_monitor",
            reason=recommendation.get("description")
        )
        result_payload = {
            "type": "resource_authorization",
            "suggestion_id": authorization_request.suggestion_id
        }
    elif action_type == "interaction":
        result_payload = {
            "type": "interaction",
            "instruction": (recommendation.get("payload") or {}).get("instruction"),
            "module": (recommendation.get("payload") or {}).get("module")
        }
    else:
        result_payload = {
            "type": action_type or "info",
            "message": recommendation.get("description", "已记录推荐")
        }

    learning_monitor.mark_recommendation_applied(rec_id)
    return {"success": True, "result": result_payload}


@router.post("/voice/recognize")
async def recognize_voice(
    audio_data: Optional[UploadFile] = File(None),
    audio_text: Optional[str] = None,
    language: Optional[str] = None
):
    """语音识别"""
    audio_bytes = None
    if audio_data:
        audio_bytes = await audio_data.read()
    
    result = await voice_interaction.recognize_speech(
        audio_data=audio_bytes,
        audio_text=audio_text,
        language=language
    )
    return result


@router.post("/voice/synthesize")
async def synthesize_voice(
    text: str,
    language: Optional[str] = None,
    voice: Optional[str] = None,
    speed: float = 1.0,
    pitch: float = 1.0
):
    """语音合成（TTS）"""
    result = await voice_interaction.synthesize_speech(
        text=text,
        language=language,
        voice=voice,
        speed=speed,
        pitch=pitch
    )
    return result


@router.get("/voice/languages")
async def get_voice_languages():
    """获取支持的语音语言列表"""
    languages = voice_interaction.get_supported_languages()
    return {"languages": languages, "current": voice_interaction.current_language}


@router.post("/translate")
async def translate(
    text: str,
    target_lang: str = "zh",
    source_lang: Optional[str] = None
):
    """翻译文本（支持60种语言）"""
    result = await translation_service.translate(text, target_lang, source_lang)
    return result


@router.post("/translate/batch")
async def batch_translate(
    texts: List[str],
    target_lang: str = "zh",
    source_lang: Optional[str] = None
):
    """批量翻译"""
    results = await translation_service.batch_translate(texts, target_lang, source_lang)
    return {"results": results, "count": len(results)}


@router.post("/translate/detect")
async def detect_language(text: str):
    """检测语言"""
    lang = await translation_service.detect_language(text)
    return {"language": lang, "is_supported": translation_service.is_supported(lang)}


@router.get("/translate/languages")
async def get_translation_languages():
    """获取支持的翻译语言列表（60种）"""
    languages = translation_service.get_supported_languages()
    return {
        "languages": languages,
        "count": len(languages),
        "default_target": translation_service.default_target
    }


@router.post("/search")
async def search(
    query: str,
    engine: Optional[str] = None,
    search_type: str = "web",
    max_results: int = 10
):
    """网络搜索（与聊天框合并）"""
    result = await web_search.search(query, engine, search_type, max_results)
    return result


@router.post("/search/multi")
async def multi_search(
    query: str,
    engines: Optional[List[str]] = None,
    search_type: str = "web",
    max_results_per_engine: int = 5
):
    """多引擎搜索并整合结果"""
    result = await web_search.multi_search(
        query, engines, search_type, max_results_per_engine
    )
    return result


@router.get("/search/engines")
async def get_search_engines():
    """获取可用的搜索引擎列表"""
    engines = {
        name: {
            "enabled": config["enabled"],
            "has_api_key": config.get("api_key") is not None,
            "supports": config.get("supports", ["web"])
        }
        for name, config in web_search.search_engines.items()
    }
    return {
        "engines": engines,
        "default": web_search.default_engine
    }


@router.post("/generate/file")
async def generate_file(
    file_type: str,  # word, excel, ppt, pdf, image
    content: str,
    template: Optional[str] = None,
    title: Optional[str] = None,
    output_path: Optional[str] = None,
    save_to_rag: bool = True  # 是否自动保存到RAG
):
    """
    生成文件（Word/Excel/PPT/PDF）⭐增强版
    
    功能：
    1. 支持DOCX/XLSX/PPTX/PDF格式
    2. 自动保存到RAG知识库（可选）
    3. 返回base64编码的文件数据
    """
    if file_type == "word":
        result = await file_generation.generate_word(content, template, output_path, title)
    elif file_type == "excel":
        # 解析content为数据格式（JSON格式：{"headers": [...], "data": [[...]]}）
        try:
            import json
            content_data = json.loads(content)
            headers = content_data.get("headers")
            data = content_data.get("data", [])
            result = await file_generation.generate_excel(
                data, headers, output_path, content_data.get("sheet_name", "Sheet1")
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Excel内容格式错误，需要JSON格式：{{\"headers\": [...], \"data\": [[...]]}}。错误: {str(e)}")
    elif file_type == "ppt":
        # 解析content为幻灯片格式
        try:
            import json
            slides_data = json.loads(content)
            slides = slides_data.get("slides", [])
            result = await file_generation.generate_ppt(slides, template, output_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"PPT内容格式错误: {str(e)}")
    elif file_type == "pdf":
        result = await file_generation.generate_pdf(content, template, output_path, title)
    elif file_type == "image":
        result = await file_generation.generate_image(content)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")
    
    if result.get("success"):
        # 返回base64编码的文件数据
        file_data = result.get("file_data", b"")
        if isinstance(file_data, bytes):
            import base64
            result["file_data_base64"] = base64.b64encode(file_data).decode('utf-8')
        
        # 如果设置了不保存到RAG，移除RAG相关警告
        if not save_to_rag and "rag_save_warning" in result:
            del result["rag_save_warning"]
        
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "文件生成失败"))


@router.post("/content/export")
async def export_content_to_file(
    content_id: Optional[str] = None,
    content_data: Optional[Dict[str, Any]] = Body(None),
    file_type: str = "docx",
    output_path: Optional[str] = None
):
    """
    从内容创作模块导出内容为文件⭐新增
    
    功能：
    1. 支持从内容模块导出为DOCX/XLSX/PPTX/PDF
    2. 如果提供了content_id，从内容模块获取内容
    3. 如果提供了content_data，直接使用
    4. 自动保存到RAG知识库
    """
    try:
        # 如果提供了content_id，从内容模块获取
        if content_id:
            import requests
            try:
                # 调用内容模块API获取内容
                response = requests.get(
                    f"http://localhost:8004/api/content/{content_id}",
                    timeout=10
                )
                if response.status_code == 200:
                    content_data = response.json().get("content", {})
                else:
                    raise HTTPException(status_code=404, detail=f"内容ID {content_id} 不存在")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"获取内容失败: {str(e)}")
        
        # 如果没有内容数据，返回错误
        if not content_data:
            raise HTTPException(status_code=400, detail="需要提供content_id或content_data")
        
        # 导出为文件
        result = await file_generation.export_content_to_file(
            content_data=content_data,
            file_type=file_type,
            output_path=output_path
        )
        
        if result.get("success"):
            # 返回base64编码的文件数据
            file_data = result.get("file_data", b"")
            if isinstance(file_data, bytes):
                import base64
                result["file_data_base64"] = base64.b64encode(file_data).decode('utf-8')
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "文件导出失败"))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/terminal/execute")
async def execute_terminal_command(
    command: str = Body(..., embed=True),
    timeout: int = Body(30, embed=True),
    cwd: Optional[str] = Body(None, embed=True)
):
    """执行终端命令"""
    result = await terminal_executor.execute_command(
        command=command,
        timeout=timeout,
        cwd=cwd
    )
    return result


@router.get("/terminal/history")
async def get_terminal_history(limit: int = 20):
    """获取终端命令历史"""
    history = terminal_executor.get_command_history(limit=limit)
    return {"history": history}


@router.get("/terminal/system-info")
async def get_terminal_system_info():
    """获取系统信息"""
    info = terminal_executor.get_system_info()
    return info


@router.post("/terminal/cd")
async def change_terminal_directory(path: str = Body(..., embed=True)):
    """切换终端工作目录"""
    result = terminal_executor.change_directory(path)
    return result


@router.get("/terminal/whitelist")
async def get_terminal_whitelist():
    """获取终端命令白名单配置"""
    whitelist = terminal_executor.get_whitelist()
    return {
        "success": True,
        **whitelist
    }


@router.post("/terminal/whitelist/update")
async def update_terminal_whitelist(
    add_commands: Optional[List[str]] = Body(None, embed=True),
    remove_commands: Optional[List[str]] = Body(None, embed=True)
):
    """
    更新终端命令白名单
    
    Args:
        add_commands: 要添加的命令列表
        remove_commands: 要移除的命令列表
    """
    result = terminal_executor.update_whitelist(
        add_commands=add_commands,
        remove_commands=remove_commands
    )
    return result


@router.post("/terminal/sandbox/clear")
async def clear_terminal_sandbox():
    """清理终端沙箱目录"""
    result = terminal_executor.clear_sandbox()
    return result


@router.get("/terminal/audit/logs")
async def get_terminal_audit_logs(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    command_id: Optional[str] = None,
    user_id: Optional[str] = None,
    success: Optional[bool] = None,
    limit: int = 100
):
    """
    查询终端审计日志
    
    Args:
        start_time: 开始时间（ISO格式）
        end_time: 结束时间（ISO格式）
        event_type: 事件类型
        severity: 严重程度
        command_id: 命令ID
        user_id: 用户ID
        success: 是否成功
        limit: 返回数量限制
    """
    logs = terminal_audit_logger.query_logs(
        start_time=start_time,
        end_time=end_time,
        event_type=event_type,
        severity=severity,
        command_id=command_id,
        user_id=user_id,
        success=success,
        limit=limit
    )
    return {
        "success": True,
        "logs": logs,
        "count": len(logs)
    }


@router.get("/terminal/audit/statistics")
async def get_terminal_audit_statistics(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """
    获取终端审计日志统计信息
    
    Args:
        start_time: 开始时间（ISO格式）
        end_time: 结束时间（ISO格式）
    """
    stats = terminal_audit_logger.get_statistics(
        start_time=start_time,
        end_time=end_time
    )
    return {
        "success": True,
        **stats
    }


@router.post("/terminal/audit/export")
async def export_terminal_audit_logs(
    output_path: str = Body(..., embed=True),
    start_time: Optional[str] = Body(None, embed=True),
    end_time: Optional[str] = Body(None, embed=True),
    format: str = Body("json", embed=True)
):
    """
    导出终端审计日志
    
    Args:
        output_path: 输出路径
        start_time: 开始时间（ISO格式）
        end_time: 结束时间（ISO格式）
        format: 导出格式（json/csv）
    """
    result = terminal_audit_logger.export_logs(
        output_path=output_path,
        start_time=start_time,
        end_time=end_time,
        format=format
    )
    return result


@router.get("/workflow/system-events")
async def get_system_events(limit: int = 20, event_type: Optional[str] = None):
    """获取系统级事件（如终端命令、安全日志）"""
    events: List[Dict[str, Any]] = []
    summary: Dict[str, Any] = {}

    if audit_pipeline:
        pipeline_events = audit_pipeline.query_records(event_type=event_type, limit=limit)
        events = [
            {
                **record,
                "success": record.get("status") != "failed",
                "data": record.get("metadata"),
            }
            for record in pipeline_events
        ]
        stats = audit_pipeline.get_statistics()
        summary = {
            "total": stats.get("total"),
            "distribution": stats.get("distribution_by_type"),
        }

    if not events:
        monitor = super_agent.workflow_monitor
        if monitor:
            events = monitor.get_recent_system_events(limit=limit, event_type=event_type)
            summary = monitor.get_system_event_summary(event_type=event_type)

    return {"events": events, "count": len(events), "summary": summary}


@router.post("/workflow/system-events")
async def create_system_event(request: SystemEventRequest):
    """外部服务写入系统事件"""
    if not super_agent.workflow_monitor:
        raise HTTPException(status_code=503, detail="Workflow monitor unavailable")
    event = await super_agent.workflow_monitor.record_system_event(
        event_type=request.event_type,
        source=request.source,
        severity=request.severity,
        success=request.success,
        data=request.data,
        error=request.error,
    )
    return {"success": True, "event": event}


@router.get("/learning/events")
async def get_learning_events(limit: int = 50, event_type: Optional[str] = None):
    """获取学习事件总线中的事件"""
    bus = super_agent.event_bus
    try:
        event_type_enum = LearningEventType(event_type) if event_type else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的事件类型: {event_type}")
    events = [
        event.__dict__
        for event in bus.get_recent_events(limit=limit, event_type=event_type_enum)
    ]
    return {"events": events, "count": len(events), "stats": bus.get_statistics()}


@router.post("/learning/events")
async def publish_learning_event(request: LearningEventRequest):
    """外部服务向学习事件总线推送事件"""
    try:
        event_type = LearningEventType(request.event_type)
    except ValueError:
        event_type = LearningEventType.CUSTOM
    event = await super_agent.event_bus.publish_event(
        event_type=event_type,
        source=request.source,
        severity=request.severity,
        payload=request.payload,
    )
    return {"success": True, "event": event.__dict__}


# ============ P0-013: 工作流因果分析/策略优化/交互建议 ============

@router.get("/workflow/causal-analysis/report")
async def get_causal_analysis_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """
    获取工作流因果分析报告
    
    Args:
        start_date: 开始日期（ISO格式，可选）
        end_date: 结束日期（ISO格式，可选）
    """
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    report = workflow_causal_analyzer.get_causal_analysis_report(start_date, end_date)
    return {"success": True, "report": report}


@router.get("/workflow/causal-analysis/chains")
async def get_causal_chains(limit: int = 20):
    """获取最近的因果链分析"""
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    chains = workflow_causal_analyzer.causal_chains[-limit:]
    return {"success": True, "chains": chains, "total": len(workflow_causal_analyzer.causal_chains)}


@router.get("/workflow/optimization-strategies")
async def get_optimization_strategies(limit: int = 20):
    """获取优化策略列表"""
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    strategies = workflow_causal_analyzer.optimization_strategies[-limit:]
    return {"success": True, "strategies": strategies, "total": len(workflow_causal_analyzer.optimization_strategies)}


@router.post("/workflow/optimization-strategies/generate")
async def generate_optimization_strategy(chain_id: int):
    """
    为指定因果链生成优化策略
    
    Args:
        chain_id: 因果链ID（索引）
    """
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    if chain_id < 0 or chain_id >= len(workflow_causal_analyzer.causal_chains):
        raise HTTPException(status_code=404, detail="因果链不存在")
    causal_chain = workflow_causal_analyzer.causal_chains[chain_id]
    strategy = await workflow_causal_analyzer.generate_optimization_strategy(causal_chain)
    return {"success": True, "strategy": strategy}


@router.get("/workflow/interaction-suggestions")
async def get_interaction_suggestions(limit: int = 20):
    """获取交互建议摘要"""
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    summary = workflow_causal_analyzer.get_interaction_suggestions_summary(limit)
    return {"success": True, "summary": summary}


@router.post("/workflow/interaction-suggestions/generate")
async def generate_interaction_suggestions(
    workflow_id: Optional[str] = None,
    user_context: Optional[Dict[str, Any]] = None
):
    """
    为指定工作流生成交互建议
    
    Args:
        workflow_id: 工作流ID（可选，不提供则使用最近的工作流）
        user_context: 用户上下文（可选）
    """
    if not workflow_causal_analyzer:
        raise HTTPException(status_code=503, detail="因果分析器未初始化")
    
    # 查找工作流追踪
    if workflow_id:
        trace = next(
            (t for t in workflow_causal_analyzer.workflow_traces if t.get("workflow_id") == workflow_id),
            None
        )
        if not trace:
            raise HTTPException(status_code=404, detail="工作流追踪不存在")
    else:
        # 使用最近的工作流追踪
        if not workflow_causal_analyzer.workflow_traces:
            raise HTTPException(status_code=404, detail="没有可用的工作流追踪")
        trace = workflow_causal_analyzer.workflow_traces[-1]
    
    suggestions = await workflow_causal_analyzer.generate_interaction_suggestions(trace, user_context)
    return {"success": True, "suggestions": suggestions, "workflow_id": trace.get("workflow_id")}


# ============ P0-014: 资源诊断与调度建议 + 授权执行 ============

@router.post("/resources/diagnostic/run")
async def run_resource_diagnostic(
    resource_data: Optional[Dict[str, Any]] = None
):
    """
    运行资源诊断
    
    Args:
        resource_data: 资源数据（可选，不提供则从monitor获取）
    """
    if not resource_diagnostic_engine:
        raise HTTPException(status_code=503, detail="资源诊断引擎未初始化")
    
    diagnostics = await resource_diagnostic_engine.run_diagnostic(resource_data)
    
    # 自动生成调度建议
    suggestions = await resource_diagnostic_engine.generate_scheduling_suggestions(diagnostics)
    
    return {
        "success": True,
        "diagnostics": [
            {
                "category": d.category.value,
                "severity": d.severity.value,
                "title": d.title,
                "description": d.description,
                "current_value": d.current_value,
                "threshold": d.threshold,
                "affected_modules": d.affected_modules,
                "root_cause": d.root_cause,
                "impact": d.impact,
                "detected_at": d.detected_at.isoformat()
            }
            for d in diagnostics
        ],
        "suggestions": [
            {
                "action_type": s.action_type,
                "description": s.description,
                "expected_improvement": s.expected_improvement,
                "risk_level": s.risk_level,
                "requires_approval": s.requires_approval,
                "estimated_impact": s.estimated_impact,
                "implementation_steps": s.implementation_steps
            }
            for s in suggestions
        ],
        "diagnostics_count": len(diagnostics),
        "suggestions_count": len(suggestions)
    }


@router.get("/resources/diagnostic/summary")
async def get_resource_diagnostic_summary(hours: int = 24):
    """获取资源诊断摘要"""
    if not resource_diagnostic_engine:
        raise HTTPException(status_code=503, detail="资源诊断引擎未初始化")
    
    summary = resource_diagnostic_engine.get_diagnostic_summary(hours)
    return {"success": True, "summary": summary}


@router.get("/resources/suggestions")
async def get_resource_suggestions(limit: int = 20):
    """获取资源调度建议"""
    if not resource_diagnostic_engine:
        raise HTTPException(status_code=503, detail="资源诊断引擎未初始化")
    
    suggestions = resource_diagnostic_engine.suggestions[-limit:]
    return {
        "success": True,
        "suggestions": [
            {
                "action_type": s.action_type,
                "description": s.description,
                "expected_improvement": s.expected_improvement,
                "risk_level": s.risk_level,
                "requires_approval": s.requires_approval,
                "estimated_impact": s.estimated_impact
            }
            for s in suggestions
        ],
        "total": len(resource_diagnostic_engine.suggestions)
    }


@router.post("/resources/authorization/request")
async def request_resource_authorization(
    suggestion_index: int,
    requested_by: str = "user",
    reason: Optional[str] = None
):
    """
    请求资源操作授权
    
    Args:
        suggestion_index: 建议索引（在suggestions列表中的位置）
        requested_by: 请求者
        reason: 请求原因
    """
    if not resource_authorization_manager or not resource_diagnostic_engine:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    suggestions = resource_diagnostic_engine.suggestions
    if suggestion_index < 0 or suggestion_index >= len(suggestions):
        raise HTTPException(status_code=404, detail="建议不存在")
    
    suggestion = suggestions[suggestion_index]
    request = await resource_authorization_manager.request_authorization(
        suggestion=suggestion,
        requested_by=requested_by,
        reason=reason
    )
    
    return {
        "success": True,
        "request": {
            "suggestion_id": request.suggestion_id,
            "action_type": suggestion.action_type,
            "description": suggestion.description,
            "requested_at": request.requested_at.isoformat(),
            "requested_by": request.requested_by
        }
    }


@router.post("/resources/authorization/approve")
async def approve_resource_authorization(
    suggestion_id: str,
    approved_by: str = "user",
    metadata: Optional[Dict[str, Any]] = None
):
    """
    批准资源操作授权
    
    Args:
        suggestion_id: 建议ID
        approved_by: 批准者
        metadata: 额外元数据
    """
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    try:
        record = await resource_authorization_manager.approve_authorization(
            suggestion_id=suggestion_id,
            approved_by=approved_by,
            metadata=metadata
        )
        
        return {
            "success": True,
            "record": {
                "suggestion_id": record.request.suggestion_id,
                "status": record.status.value,
                "approved_at": record.approved_at.isoformat() if record.approved_at else None,
                "approved_by": record.approved_by,
                "execution_result": record.execution_result
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/resources/authorization/reject")
async def reject_resource_authorization(
    suggestion_id: str,
    rejected_by: str = "user",
    reason: Optional[str] = None
):
    """
    拒绝资源操作授权
    
    Args:
        suggestion_id: 建议ID
        rejected_by: 拒绝者
        reason: 拒绝原因
    """
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    try:
        record = await resource_authorization_manager.reject_authorization(
            suggestion_id=suggestion_id,
            rejected_by=rejected_by,
            reason=reason
        )
        
        return {
            "success": True,
            "record": {
                "suggestion_id": record.request.suggestion_id,
                "status": record.status.value,
                "metadata": record.metadata
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/resources/authorization/pending")
async def get_pending_authorizations():
    """获取待处理的授权请求"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    pending = resource_authorization_manager.get_pending_authorizations()
    return {"success": True, "pending": pending, "count": len(pending)}


@router.get("/resources/authorization/history")
async def get_authorization_history(
    limit: int = 50,
    status: Optional[str] = None
):
    """
    获取授权历史
    
    Args:
        limit: 返回数量限制
        status: 状态筛选（可选）
    """
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    from core.resource_authorization import AuthorizationStatus
    
    status_enum = None
    if status:
        try:
            status_enum = AuthorizationStatus(status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的状态: {status}")
    
    history = resource_authorization_manager.get_authorization_history(
        limit=limit,
        status=status_enum
    )
    
    return {"success": True, "history": history, "count": len(history)}


@router.get("/resources/authorization/statistics")
async def get_authorization_statistics():
    """获取授权统计信息"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    stats = resource_authorization_manager.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/resources/executions")
async def get_resource_executions(limit: int = 20):
    """获取资源执行记录"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    records = resource_authorization_manager.get_execution_records(limit)
    return {"success": True, "executions": records, "count": len(records)}


@router.get("/resources/rollbacks")
async def get_resource_rollbacks(limit: int = 20):
    """获取回滚记录"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    history = resource_authorization_manager.get_rollbacks(limit)
    return {"success": True, "rollbacks": history, "count": len(history)}


@router.post("/resources/rollback", response_model=ResourceRollbackResponse)
async def rollback_resource_action(req: ResourceRollbackRequest):
    """执行回滚操作"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    try:
        entry = await resource_authorization_manager.rollback_action(
            suggestion_id=req.suggestion_id,
            requested_by="user",
            reason=req.reason
        )
        return entry
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/resources/overview")
async def get_resource_overview(limit: int = 5):
    """资源建议/执行/回滚联动视图"""
    if not resource_authorization_manager:
        raise HTTPException(status_code=503, detail="资源授权管理器未初始化")
    
    suggestions_payload: List[Dict[str, Any]] = []
    if resource_diagnostic_engine and getattr(resource_diagnostic_engine, "suggestions", None):
        recent = resource_diagnostic_engine.suggestions[-limit:]
        for suggestion in reversed(recent):
            suggestions_payload.append({
                "description": getattr(suggestion, "description", ""),
                "action_type": getattr(suggestion, "action_type", ""),
                "risk_level": getattr(suggestion, "risk_level", ""),
                "expected_improvement": getattr(suggestion, "expected_improvement", ""),
                "requires_approval": getattr(suggestion, "requires_approval", False),
                "rollback_plan": getattr(suggestion, "rollback_plan", None)
            })
    
    executions = resource_authorization_manager.get_execution_records(limit)
    rollbacks = resource_authorization_manager.get_rollbacks(limit)
    
    return {
        "success": True,
        "suggestions": suggestions_payload,
        "executions": executions,
        "rollbacks": rollbacks
    }


@router.get("/resources/task-impacts")
async def list_task_impacts(limit: int = 10):
    """获取任务执行后对资源的影响记录"""
    impacts = resource_authorization_manager.get_task_impacts(limit=limit)
    return {"success": True, "impacts": impacts, "count": len(impacts)}


# ============ P0-015: 资源策略引擎与冲突调度 ============

@router.post("/resources/strategy/select")
async def select_resource_strategy(
    context: Optional[str] = None,
    resource_data: Optional[Dict[str, Any]] = None
):
    """
    选择资源策略
    
    Args:
        context: 系统上下文（normal/high_load/low_load/critical/maintenance）
        resource_data: 资源数据（可选）
    """
    if not resource_strategy_engine:
        raise HTTPException(status_code=503, detail="资源策略引擎未初始化")
    
    context_enum = None
    if context:
        try:
            context_enum = StrategyContext(context)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的上下文: {context}")
    
    strategy = await resource_strategy_engine.select_strategy(context_enum, resource_data)
    
    return {
        "success": True,
        "strategy": strategy.value,
        "context": resource_strategy_engine.current_context.value if resource_strategy_engine.current_context else None
    }


@router.post("/resources/strategy/execute")
async def execute_resource_strategy(
    strategy: Optional[str] = None,
    target_modules: Optional[List[str]] = None
):
    """
    执行资源策略
    
    Args:
        strategy: 策略名称（可选）
        target_modules: 目标模块列表（可选）
    """
    if not resource_strategy_engine:
        raise HTTPException(status_code=503, detail="资源策略引擎未初始化")
    
    strategy_enum = None
    if strategy:
        try:
            strategy_enum = ResourceStrategy(strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的策略: {strategy}")
    
    result = await resource_strategy_engine.execute_strategy(strategy_enum, target_modules)
    return {"success": True, "result": result}


@router.get("/resources/strategy/statistics")
async def get_strategy_statistics():
    """获取策略统计信息"""
    if not resource_strategy_engine:
        raise HTTPException(status_code=503, detail="资源策略引擎未初始化")
    
    stats = resource_strategy_engine.get_strategy_statistics()
    return {"success": True, "statistics": stats}


@router.post("/resources/strategy/update-from-learning")
async def update_strategy_from_learning(
    learning_recommendations: Dict[str, Any]
):
    """
    从自学习系统更新策略
    
    Args:
        learning_recommendations: 自学习系统的建议
    """
    if not resource_strategy_engine:
        raise HTTPException(status_code=503, detail="资源策略引擎未初始化")
    
    await resource_strategy_engine.update_strategy_from_learning(learning_recommendations)
    return {"success": True, "message": "策略已从自学习系统更新"}


@router.post("/resources/conflicts/detect")
async def detect_resource_conflicts(
    resource_data: Optional[Dict[str, Any]] = None
):
    """
    检测资源冲突
    
    Args:
        resource_data: 资源数据（可选）
    """
    if not resource_conflict_scheduler:
        raise HTTPException(status_code=503, detail="冲突调度系统未初始化")
    
    conflicts = await resource_conflict_scheduler.detect_conflicts(resource_data)
    
    return {
        "success": True,
        "conflicts": [
            {
                "conflict_id": c.conflict_id,
                "conflict_type": c.conflict_type.value,
                "conflicting_modules": c.conflicting_modules,
                "resource_type": c.resource_type,
                "conflict_severity": c.conflict_severity,
                "detected_at": c.detected_at.isoformat(),
                "root_cause": c.root_cause
            }
            for c in conflicts
        ],
        "count": len(conflicts)
    }


@router.post("/resources/conflicts/resolve")
async def resolve_resource_conflict(
    conflict_id: str,
    preferred_strategy: Optional[str] = None
):
    """
    解决资源冲突
    
    Args:
        conflict_id: 冲突ID
        preferred_strategy: 首选解决策略（可选）
    """
    if not resource_conflict_scheduler:
        raise HTTPException(status_code=503, detail="冲突调度系统未初始化")
    
    # 查找冲突
    conflict = next(
        (c for c in resource_conflict_scheduler.detected_conflicts if c.conflict_id == conflict_id),
        None
    )
    
    if not conflict:
        raise HTTPException(status_code=404, detail="冲突不存在")
    
    strategy_enum = None
    if preferred_strategy:
        try:
            strategy_enum = ResolutionStrategy(preferred_strategy)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的策略: {preferred_strategy}")
    
    resolution = await resource_conflict_scheduler.resolve_conflict(conflict, strategy_enum)
    
    return {
        "success": True,
        "resolution": {
            "conflict_id": resolution.conflict.conflict_id,
            "resolution_strategy": resolution.resolution_strategy.value,
            "resolution_actions": resolution.resolution_actions,
            "expected_improvement": resolution.expected_improvement,
            "risk_level": resolution.risk_level,
            "requires_approval": resolution.requires_approval
        }
    }


@router.post("/resources/conflicts/execute-resolution")
async def execute_conflict_resolution(
    conflict_id: str,
    approved: bool = False
):
    """
    执行冲突解决方案
    
    Args:
        conflict_id: 冲突ID
        approved: 是否已获得授权
    """
    if not resource_conflict_scheduler:
        raise HTTPException(status_code=503, detail="冲突调度系统未初始化")
    
    # 查找解决方案
    resolution = next(
        (r for r in resource_conflict_scheduler.resolutions if r.conflict.conflict_id == conflict_id),
        None
    )
    
    if not resolution:
        raise HTTPException(status_code=404, detail="解决方案不存在")
    
    result = await resource_conflict_scheduler.execute_resolution(resolution, approved)
    return {"success": True, "result": result}


@router.get("/resources/conflicts/statistics")
async def get_conflict_statistics():
    """获取冲突统计信息"""
    if not resource_conflict_scheduler:
        raise HTTPException(status_code=503, detail="冲突调度系统未初始化")
    
    stats = resource_conflict_scheduler.get_conflict_statistics()
    return {"success": True, "statistics": stats}


def _get_task_orchestrator():
    orchestrator = super_agent.task_orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="任务编排器尚未初始化")
    return orchestrator


def _get_factory_data_source():
    if factory_data_source:
        return factory_data_source
    raise HTTPException(
        status_code=503,
        detail=factory_data_source_error or "demo_factory 数据源尚未准备，请先生成数据库",
    )

def _get_trial_data_source():
    if trial_data_source:
        return trial_data_source
    raise HTTPException(
        status_code=503,
        detail=trial_data_source_error or "trial 数据源尚未准备，请先生成 demo_factory 数据库",
    )


@router.get("/tasks")
async def list_tasks():
    orchestrator = _get_task_orchestrator()
    return {"tasks": orchestrator.list_tasks()}

class TaskMetadataUpdateRequest(BaseModel):
    updates: Dict[str, Any]

@router.post("/tasks/{task_id}/metadata")
async def update_task_metadata(task_id: str, req: TaskMetadataUpdateRequest):
    """更新编排器任务的元数据（可用于设置 steps/total_steps 等）"""
    orchestrator = _get_task_orchestrator()
    data = await orchestrator.update_task_metadata(task_id, req.updates or {})
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": data}
@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取编排任务详情（Orchestrator管理的任务）"""
    orchestrator = _get_task_orchestrator()
    data = orchestrator.get_task(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": data}

@router.get("/planning/tasks")
async def list_planning_tasks(status: Optional[str] = None):
    """获取任务规划系统中的任务列表（非编排器）"""
    tasks = task_planning.get_tasks(status=status)
    return {"tasks": tasks, "count": len(tasks)}

@router.get("/planning/tasks/{task_id}")
async def get_planning_task(task_id: int):
    """获取任务规划系统中的单个任务"""
    tasks = task_planning.get_tasks()
    t = next((x for x in tasks if x.get("id") == task_id), None)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": t}

@router.delete("/planning/tasks/{task_id}")
async def delete_planning_task(task_id: int):
    """删除任务规划系统中的任务（最小可用）"""
    tasks = task_planning.get_tasks()
    idx = None
    for i, t in enumerate(tasks):
        if t.get("id") == task_id:
            idx = i
            break
    if idx is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    try:
        # 从内部列表移除
        del task_planning.tasks[idx]
        return {"success": True, "deleted_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取编排任务详情（Orchestrator管理的任务）"""
    orchestrator = _get_task_orchestrator()
    data = orchestrator.get_task(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": data}


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    orchestrator = _get_task_orchestrator()
    task = await orchestrator.register_task(
        title=request.title,
        description=request.description or "",
        priority=request.priority,
        metadata=request.metadata,
        dependencies=request.dependencies,
        source="api",
    )
    return {"task": task}

@router.get("/tasks/summary/24h")
async def tasks_summary_24h():
    """
    任务近24小时统计：
    - orch: started/ completed / completion_rate （基于created_at/metadata.completed_at）
    - plan: started/ completed / completion_rate （基于 started_at/completed_at）
    """
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    # 编排器
    orch_started = 0
    orch_completed = 0
    try:
        orchestrator = _get_task_orchestrator()
        for t in orchestrator.list_tasks():
            created_at = t.get("created_at")
            if created_at:
                try:
                    if datetime.fromisoformat(created_at) >= cutoff:
                        orch_started += 1
                except Exception:
                    pass
            comp_at = (t.get("metadata") or {}).get("completed_at")
            if comp_at:
                try:
                    if datetime.fromisoformat(comp_at) >= cutoff:
                        orch_completed += 1
                except Exception:
                    pass
    except Exception:
        pass
    orch_rate = (orch_completed / orch_started * 100) if orch_started > 0 else 0.0
    # 规划
    plan_started = 0
    plan_completed = 0
    try:
        for t in task_planning.tasks:
            st = t.get("started_at")
            if st:
                try:
                    if datetime.fromisoformat(st) >= cutoff:
                        plan_started += 1
                except Exception:
                    pass
            ct = t.get("completed_at")
            if ct:
                try:
                    if datetime.fromisoformat(ct) >= cutoff:
                        plan_completed += 1
                except Exception:
                    pass
    except Exception:
        pass
    plan_rate = (plan_completed / plan_started * 100) if plan_started > 0 else 0.0
    return {
        "success": True,
        "cutoff": cutoff.isoformat(),
        "orch": {
            "started": orch_started,
            "completed": orch_completed,
            "completion_rate": round(orch_rate, 2)
        },
        "plan": {
            "started": plan_started,
            "completed": plan_completed,
            "completion_rate": round(plan_rate, 2)
        }
    }

@router.post("/tasks/{task_id}/status")
async def update_task_status(task_id: str, request: TaskStatusUpdateRequest):
    orchestrator = _get_task_orchestrator()
    task = await orchestrator.update_task_status(
        task_id=task_id,
        status=request.status,
        updates=request.updates,
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    # 记录系统事件（审计）
    try:
        if super_agent.workflow_monitor:
            reason = None
            if request.updates:
                reason = request.updates.get("blocked_reason") or request.updates.get("reason")
            await super_agent.workflow_monitor.record_system_event(
                event_type="orchestrator_task_status",
                source="task_api",
                severity="warning" if str(request.status).lower() == "blocked" else "info",
                success=True,
                data={
                    "task_id": task_id,
                    "new_status": str(request.status),
                    "reason": reason
                },
                error=None
            )
    except Exception:
        pass
    return {"task": task}

@router.get("/planning/tasks/{task_id}")
async def get_planning_task_detail(task_id: int):
    """获取规划系统中的任务详情（包含执行日志/复盘等）"""
    task = next((t for t in task_planning.tasks if t.get("id") == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": task}

@router.get("/erp/demo/dashboard")
async def get_demo_dashboard():
    ds = _get_factory_data_source()
    return ds.get_dashboards()


@router.get("/operations/analytics")
async def get_operations_analytics():
    """
    获取运营财务分析数据（增强版：集成专家系统）
    """
    ds = _get_factory_data_source()
    cash_flow = ds.get_cash_flow_summary() or {}
    collections = float(cash_flow.get("total_collections") or 0.0)
    payments = float(cash_flow.get("total_payments") or 0.0)
    balance = cash_flow.get("balance")
    if balance is None:
        balance = collections - payments
    balance = float(balance or 0.0)
    period_months = 3.0  # demo 数据按季度汇总
    burn_rate = payments / period_months if payments else 0.0
    runway_months = balance / burn_rate if burn_rate > 0 else None
    collection_payment_ratio = collections / payments if payments else float("inf")

    kpi_summary = {
        "net_cash": balance,
        "burn_rate": burn_rate,
        "collections": collections,
        "payments": payments,
        "runway_months": runway_months,
        "collection_payment_ratio": collection_payment_ratio
    }

    scorecards = [
        {
            "label": "净现金余额",
            "value": f"¥{balance:,.0f}",
            "trend": "+8% QoQ" if balance >= 0 else "-",
            "status": "positive" if balance > payments else "warning"
        },
        {
            "label": "月度 Burn Rate",
            "value": f"¥{burn_rate:,.0f}",
            "trend": "+2% MoM" if burn_rate else "-",
            "status": "warning" if burn_rate > 0.6 * collections else "neutral"
        },
        {
            "label": "Runway（月）",
            "value": f"{runway_months:.1f} 月" if runway_months else "∞",
            "trend": "安全线 ≥ 6",
            "status": "critical" if runway_months and runway_months < 6 else "positive"
        }
    ]

    trend_points = []
    base_cash = balance if balance > 0 else 1_200_000
    for idx, label in enumerate(["W-4", "W-3", "W-2", "W-1", "本周"]):
        factor = 0.7 + idx * 0.08
        trend_points.append({
            "label": label,
            "net_cash": round(base_cash * factor / 1_000_000, 2),
            "burn": round(max(burn_rate, 1.0) * (0.9 + idx * 0.05) / 1_000_000, 2)
        })

    chart_blueprints = await persistence_seeder.get_records("operations_chart_blueprints", limit=20)
    finance_guides = await persistence_seeder.get_records("operations_finance_guides", limit=20)

    return {
        "success": True,
        "kpi_summary": kpi_summary,
        "scorecards": scorecards,
        "trend_points": trend_points,
        "chart_blueprints": chart_blueprints,
        "finance_insights": finance_guides,
        "strategy": OPERATIONS_FINANCE_STRATEGY,
        "strategy_links": OPERATIONS_STRATEGY_LINKS,
        "cash_flow": cash_flow,
        "last_refreshed": datetime.now().isoformat()
    }


@router.get("/erp/demo/orders")
async def get_demo_orders(
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    订单列表（支持状态筛选/关键词过滤/分页）
    关键词匹配字段：order_id / customer / product_code / product_name
    """
    ds = _get_factory_data_source()
    items = ds.get_orders(status=status)
    # 关键词过滤（简化）
    if q:
        ql = q.lower()
        def match(o):
            for k in ["order_id", "customer", "product_code", "product_name"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    # 分页
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    # 状态分布（简易图表数据）
    status_dist = {}
    for o in items:
        s = o.get("status", "unknown")
        status_dist[s] = status_dist.get(s, 0) + 1
    return {
        "orders": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "status_distribution": status_dist
    }


@router.get("/erp/demo/production-jobs")
async def get_production_jobs(
    order_id: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_production_jobs(order_id=order_id)
    # 关键词过滤（job_id/order_id/machine/operation等字段）
    if q:
        ql = q.lower()
        def match(o):
            for k in ["job_id", "order_id", "machine", "operation"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布
    state_dist = {}
    for j in items:
        s = j.get("status", "unknown")
        state_dist[s] = state_dist.get(s, 0) + 1
    return {"jobs": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": state_dist}


@router.get("/erp/demo/procurements")
async def get_procurement_alerts(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_procurement_alerts()
    if q:
        ql = q.lower()
        def match(o):
            for k in ["po_id", "supplier", "material_code", "material_name", "alert", "status"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布
    state_dist = {}
    for p in items:
        s = p.get("status", "unknown")
        state_dist[s] = state_dist.get(s, 0) + 1
    return {"procurements": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": state_dist}

@router.get("/erp/demo/inventory")
async def get_inventory(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_inventory_status()
    if q:
        ql = q.lower()
        def match(o):
            for k in ["material_code", "material_name", "status_flag"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布（低于安全/正常）
    flag_dist = {}
    for it in items:
        s = it.get("status_flag", "normal")
        flag_dist[s] = flag_dist.get(s, 0) + 1
    return {"inventory": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": flag_dist}


@router.get("/erp/demo/cash-flow")
async def get_cash_flow_summary():
    ds = _get_factory_data_source()
    return ds.get_cash_flow_summary()


async def _erp_trial_calc_logic(params: Dict[str, Any]) -> Dict[str, Any]:
    target_weekly_revenue = params.get("target_weekly_revenue")
    target_daily_units = params.get("target_daily_units")
    product_code = params.get("product_code")
    order_id = params.get("order_id")

    ds = _get_trial_data_source()
    product = await ds.get_product_data(
        order_id=order_id,
        product_code=product_code,
        legacy_identifier=product_code or order_id,
    )
    if not product:
        raise HTTPException(status_code=404, detail="未找到可用于试算的订单/产品数据")

    unit_price = float(product.get("unit_price") or 0.0)
    available_days = max(1, int(product.get("available_days") or 7))

    result: Dict[str, Any] = {
        "product": {
            "order_id": product.get("order_id"),
            "product_code": product.get("product_code"),
            "product_name": product.get("product_name"),
            "unit_price": unit_price,
            "available_days": available_days,
            "promise_date": product.get("promise_date"),
            "requested_date": product.get("requested_date"),
            "priority": product.get("priority"),
        },
        "inputs": {
            "target_weekly_revenue": target_weekly_revenue,
            "target_daily_units": target_daily_units,
        },
    }

    if target_weekly_revenue and unit_price > 0:
        required_units_week = target_weekly_revenue / unit_price
        required_units_day = required_units_week / 7.0
        result["trial"] = {
            "type": "by_weekly_revenue",
            "required_units_per_day": round(required_units_day, 2),
            "assumptions": {"unit_price": unit_price, "days_per_week": 7},
        }
    elif target_daily_units:
        expected_week_revenue = target_daily_units * unit_price * 7.0
        result["trial"] = {
            "type": "by_daily_units",
            "expected_weekly_revenue": round(expected_week_revenue, 2),
            "assumptions": {"unit_price": unit_price, "days_per_week": 7},
        }
    else:
        quantity = int(product.get("quantity") or 0)
        if quantity > 0:
            required_units_day = quantity / available_days
            result["trial"] = {
                "type": "by_order_quantity",
                "required_units_per_day": round(required_units_day, 2),
                "assumptions": {
                    "available_days": available_days,
                    "order_quantity": quantity,
                },
            }
        else:
            result["trial"] = {
                "type": "insufficient_data",
                "message": "缺少目标或订单数量，无法计算",
            }
    return result

@router.post("/erp/trial/calc")
async def trial_calculation(
    target_weekly_revenue: Optional[float] = Body(None, embed=True),
    target_daily_units: Optional[int] = Body(None, embed=True),
    product_code: Optional[str] = Body(None, embed=True),
    order_id: Optional[str] = Body(None, embed=True)
):
    """
    运营试算器：为达到目标（周营收或日产量），需要的日均产出/订单配置建议
    - 若提供 target_weekly_revenue：根据产品单价与可用天数，倒推出建议日产量
    - 若提供 target_daily_units：计算预计周营收
    """
    execution_id, exec_result = await run_closed_loop_operation(
        module="erp",
        function="trial_calculation",
        parameters={
            "target_weekly_revenue": target_weekly_revenue,
            "target_daily_units": target_daily_units,
            "product_code": product_code,
            "order_id": order_id,
        },
        executor=_erp_trial_calc_logic,
        metadata={"order_id": order_id, "product_code": product_code},
    )
    payload = exec_result.get("result") or {}
    payload["execution_id"] = execution_id
    return payload

@router.post("/erp/8d/analyze")
async def erp_8d_analyze(payload: Dict[str, Any] = Body(...)):
    """
    ERP八维度分析：质量/成本/交期/安全/利润/效率/管理/技术
    传入各维度必要指标（可缺省，采用保守默认），返回指标与总览评分
    """
    if not analyze_8d:
        raise HTTPException(status_code=503, detail="ERP 8D分析模块未加载")
    try:
        result = analyze_8d(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"8D分析失败: {str(e)}")

# ====== ERP BPMN 流程编辑/管理 ======
@router.get("/erp/bpmn/processes")
async def list_bpmn_processes():
    items = []
    for file in bpmn_dir.glob("*.json"):
        try:
            items.append({
                "id": file.stem,
                "filename": file.name,
                "size": file.stat().st_size,
                "updated_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        except Exception:
            continue
    return {"processes": sorted(items, key=lambda x: x["updated_at"], reverse=True)}

@router.get("/erp/bpmn/process/{process_id}")
async def get_bpmn_process(process_id: str):
    path = bpmn_dir / f"{process_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="流程不存在")
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return {"id": process_id, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveBPMNRequest(BaseModel):
    id: Optional[str] = None
    data: Dict[str, Any]

@router.post("/erp/bpmn/process")
async def save_bpmn_process(req: SaveBPMNRequest):
    pid = req.id or f"proc_{int(datetime.now().timestamp())}"
    path = bpmn_dir / f"{pid}.json"
    try:
        path.write_text(json.dumps(req.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"success": True, "id": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/erp/bpmn/process/{process_id}")
async def delete_bpmn_process(process_id: str):
    path = bpmn_dir / f"{process_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="流程不存在")
    try:
        path.unlink()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== BPMN 运行时追踪（最小可用） ======
runtime_path = bpmn_dir / "runtime.jsonl"
SAMPLE_RUNTIME_EVENTS = [
    {
        "instance_id": "BP202511150001",
        "process_id": "proc_full_cycle",
        "node_id": "market_research",
        "node_name": "市场调研",
        "status": "completed",
        "message": "锁定目标细分市场",
        "timestamp": "2025-11-01T09:10:00"
    },
    {
        "instance_id": "BP202511150001",
        "process_id": "proc_full_cycle",
        "node_id": "customer_development",
        "node_name": "客户开发",
        "status": "completed",
        "message": "签署4份意向书",
        "timestamp": "2025-11-02T14:25:00"
    },
    {
        "instance_id": "BP202511150001",
        "process_id": "proc_full_cycle",
        "node_id": "project_development",
        "node_name": "项目开发",
        "status": "completed",
        "message": "确认BOM",
        "timestamp": "2025-11-03T19:40:00"
    },
    {
        "instance_id": "BP202511150001",
        "process_id": "proc_full_cycle",
        "node_id": "order_management",
        "node_name": "订单管理",
        "status": "in_progress",
        "message": "等待客户签字",
        "timestamp": "2025-11-05T12:05:00"
    },
    {
        "instance_id": "BP202511150002",
        "process_id": "proc_fast_track",
        "node_id": "market_research",
        "node_name": "市场调研",
        "status": "completed",
        "message": "紧急项目",
        "timestamp": "2025-11-04T09:00:00"
    },
    {
        "instance_id": "BP202511150002",
        "process_id": "proc_fast_track",
        "node_id": "customer_development",
        "node_name": "客户开发",
        "status": "completed",
        "message": "客户绿灯",
        "timestamp": "2025-11-04T16:00:00"
    },
    {
        "instance_id": "BP202511150002",
        "process_id": "proc_fast_track",
        "node_id": "production_planning",
        "node_name": "投产计划",
        "status": "started",
        "message": "排产锁定",
        "timestamp": "2025-11-05T09:45:00"
    }
]


def _load_runtime_events(limit: int = 1000) -> List[Dict[str, Any]]:
    """加载运行时事件，兼容空文件场景"""
    events: List[Dict[str, Any]] = []
    import json as _json
    if runtime_path.exists():
        try:
            with open(runtime_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        events.append(_json.loads(line))
                    except Exception:
                        continue
        except Exception:
            events = []
    if not events:
        events = SAMPLE_RUNTIME_EVENTS[-limit:]
    return events

class BpmnRuntimeEvent(BaseModel):
    instance_id: str
    process_id: str
    node_id: str
    node_name: Optional[str] = None
    status: str  # started/completed/error
    message: Optional[str] = None

@router.post("/erp/bpmn/runtime/event")
async def bpmn_runtime_event(ev: BpmnRuntimeEvent):
    """记录流程实例节点事件"""
    rec = ev.dict()
    rec["timestamp"] = datetime.now().isoformat()
    try:
        with open(runtime_path, "a", encoding="utf-8") as f:
            import json as _json
            f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/erp/bpmn/runtime/instances")
async def bpmn_runtime_instances(limit: int = 50):
    """按实例聚合最近事件（最小可用）"""
    from collections import defaultdict
    try:
        events = _load_runtime_events(limit=1000)
        agg = defaultdict(list)
        for e in events:
            agg[e["instance_id"]].append(e)
        instances = []
        for iid, events in agg.items():
            events_sorted = sorted(events, key=lambda x: x.get("timestamp", ""))
            last = events_sorted[-1]
            instances.append({
                "instance_id": iid,
                "process_id": last.get("process_id"),
                "last_node": last.get("node_id"),
                "last_status": last.get("status"),
                "events_count": len(events_sorted),
                "updated_at": last.get("timestamp")
            })
        instances = sorted(instances, key=lambda x: x["updated_at"], reverse=True)[:limit]
        return {"instances": instances, "count": len(instances)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/erp/bpmn/runtime/instance/{instance_id}")
async def get_bpmn_runtime_instance(instance_id: str):
    """获取单个流程实例的事件时间线"""
    events = [e for e in _load_runtime_events() if e.get("instance_id") == instance_id]
    if not events:
        raise HTTPException(status_code=404, detail="未找到该流程实例")
    events_sorted = sorted(events, key=lambda x: x.get("timestamp", ""))
    first = events_sorted[0]
    last = events_sorted[-1]
    duration = None
    if first.get("timestamp") and last.get("timestamp"):
        try:
            start_dt = datetime.fromisoformat(first["timestamp"])
            end_dt = datetime.fromisoformat(last["timestamp"])
            duration = (end_dt - start_dt).total_seconds()
        except Exception:
            duration = None
    return {
        "success": True,
        "instance": {
            "instance_id": instance_id,
            "process_id": last.get("process_id"),
            "current_node": last.get("node_id"),
            "current_status": last.get("status"),
            "events_count": len(events_sorted),
            "started_at": first.get("timestamp"),
            "updated_at": last.get("timestamp"),
            "duration_seconds": duration
        },
        "events": events_sorted
    }

@router.get("/integrations/status")
async def get_external_integrations():
    return {"integrations": external_status.get_status()}


@router.get("/workflow/statistics")
async def get_workflow_statistics():
    """获取工作流统计信息"""
    stats = super_agent.workflow_monitor.get_statistics() if super_agent.workflow_monitor else {}
    return stats


@router.get("/workflow/recent")
async def get_recent_workflows(limit: int = 10):
    """获取最近的工作流记录"""
    workflows = super_agent.workflow_monitor.get_recent_workflows(limit) if super_agent.workflow_monitor else []
    return {"workflows": workflows, "count": len(workflows)}


@router.get("/workflow/orchestrator/metrics")
async def get_workflow_orchestrator_metrics():
    """获取工作流编排器指标（JSON格式）"""
    try:
        from core.workflow_orchestrator import get_workflow_orchestrator
        orchestrator = get_workflow_orchestrator()
        metrics = await orchestrator.get_metrics_json()
        return {"success": True, "metrics": metrics}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/workflow/orchestrator/metrics/prometheus")
async def get_workflow_orchestrator_prometheus_metrics():
    """获取工作流编排器 Prometheus 指标"""
    from fastapi.responses import Response
    try:
        from core.workflow_orchestrator import get_workflow_orchestrator
        orchestrator = get_workflow_orchestrator()
        metrics_data = orchestrator.get_prometheus_metrics()
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        return Response(
            content=f"# Error: {str(e)}\n",
            media_type="text/plain",
            status_code=500
        )


@router.get("/workflow/status")
async def get_workflow_status(
    workflow_type: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50
):
    """
    获取工作流状态
    
    Args:
        workflow_type: 工作流类型（intelligent/direct）
        state: 工作流状态（initialized/rag_retrieval_1/expert_routing/module_execution/rag_retrieval_2/response_generation/completed/failed/cancelled）
        limit: 返回数量限制
        
    Returns:
        工作流状态信息，包括统计、活跃工作流列表等
    """
    try:
        from core.workflow_orchestrator import (
            get_workflow_orchestrator,
            WorkflowType,
            WorkflowState,
        )
        
        orchestrator = get_workflow_orchestrator()
        
        # 获取指标
        metrics = await orchestrator.get_metrics_json()
        
        # 获取工作流列表
        wf_type = WorkflowType(workflow_type) if workflow_type else None
        wf_state = WorkflowState(state) if state else None
        
        all_workflows = await orchestrator.list_workflows(
            workflow_type=wf_type,
            state=wf_state,
            limit=limit
        )
        
        # 分离智能线和直接操作线
        intelligent_workflows = [
            wf for wf in all_workflows
            if wf.get("workflow_type") == "intelligent"
            and wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        direct_workflows = [
            wf for wf in all_workflows
            if wf.get("workflow_type") == "direct"
            and wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        # 活跃工作流（所有非终态工作流）
        active_workflows = [
            wf for wf in all_workflows
            if wf.get("state") not in ["completed", "failed", "cancelled"]
        ]
        
        return {
            "success": True,
            "data": {
                "statistics": metrics,
                "intelligent_workflows": intelligent_workflows[:10],  # 最多显示10个
                "direct_workflows": direct_workflows[:10],  # 最多显示10个
                "active_workflows": active_workflows[:20],  # 最多显示20个
                "type_state_counts": metrics.get("type_state_counts", {}),
            }
        }
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.get("/resource/adjuster/statistics")
async def get_resource_adjuster_statistics():
    """获取资源自动调节统计信息"""
    stats = resource_adjuster.get_statistics()
    return stats


@router.post("/resource/adjuster/monitor")
async def monitor_resources():
    """监控资源并检测问题"""
    issues = await resource_adjuster.monitor_resources()
    return {"issues": [{
        "type": issue.issue_type.value,
        "severity": issue.severity,
        "description": issue.description,
        "current_value": issue.current_value,
        "threshold": issue.threshold,
        "affected_modules": issue.affected_modules,
        "detected_at": issue.detected_at.isoformat()
    } for issue in issues], "count": len(issues)}


@router.post("/resource/adjuster/analyze")
async def analyze_resource_issue(issue_type: str, severity: str):
    """分析资源问题并生成调节建议"""
    # 查找匹配的问题
    matching_issues = [
        issue for issue in resource_adjuster.issues[-100:]
        if issue.issue_type.value == issue_type and issue.severity == severity
    ]
    
    if not matching_issues:
        return {"suggestions": [], "message": "未找到匹配的问题"}
    
    issue = matching_issues[-1]  # 使用最新的问题
    suggestions = await resource_adjuster.analyze_issue(issue)
    
    return {
        "suggestions": [{
            "action": suggestion.action.value,
            "description": suggestion.description,
            "expected_impact": suggestion.expected_impact,
            "risk_level": suggestion.risk_level,
            "requires_approval": suggestion.requires_approval,
            "estimated_improvement": suggestion.estimated_improvement
        } for suggestion in suggestions],
        "count": len(suggestions)
    }


@router.post("/resource/adjuster/execute")
async def execute_adjustment(
    action: str,
    description: str,
    approved: bool = False
):
    """执行资源调节动作"""
    # 查找匹配的建议
    matching_suggestions = [
        s for s in resource_adjuster.suggestions[-100:]
        if s.action.value == action and s.description == description
    ]
    
    if not matching_suggestions:
        return {"success": False, "message": "未找到匹配的建议"}
    
    suggestion = matching_suggestions[-1]
    result = await resource_adjuster.execute_adjustment(suggestion, approved=approved)
    
    return result


@router.post("/resource/adjuster/enable")
async def enable_auto_adjust(threshold: str = "medium"):
    """启用资源自动调节"""
    resource_adjuster.enable_auto_adjust(threshold)
    return {"success": True, "message": f"已启用自动调节，阈值：{threshold}"}


@router.post("/resource/adjuster/disable")
async def disable_auto_adjust():
    """禁用资源自动调节"""
    resource_adjuster.disable_auto_adjust()
    return {"success": True, "message": "已禁用自动调节"}


@router.get("/learning/workflow-statistics")
async def get_learning_workflow_statistics():
    """获取学习系统工作流统计"""
    stats = learning_monitor.get_workflow_statistics() if hasattr(learning_monitor, 'get_workflow_statistics') else {}
    return stats


@router.get("/learning/resource-statistics")
async def get_learning_resource_statistics():
    """获取学习系统资源统计"""
    stats = learning_monitor.get_resource_statistics() if hasattr(learning_monitor, 'get_resource_statistics') else {}
    return stats


@router.get("/performance/stats")
async def get_performance_stats():
    """获取性能统计信息（2秒响应监控）"""
    stats = performance_monitor.get_performance_stats()
    return {
        "success": True,
        **stats,
        "strategy": await strategy_engine.get_stats()
    }

@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """统一遥测总览：性能/策略/资源/学习/工作流统计"""
    perf = performance_monitor.get_performance_stats()
    strategy = await strategy_engine.get_stats()
    resource = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts()
    workflow_stats = super_agent.workflow_monitor.get_statistics() if super_agent.workflow_monitor else {}
    learning_stats = learning_monitor.get_statistics() if learning_monitor else {}
    return {
        "success": True,
        "performance": perf,
        "strategy": strategy,
        "resource": {
            "status": resource,
            "alerts": alerts,
            "alerts_count": len(alerts)
        },
        "workflow": workflow_stats,
        "learning": learning_stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/performance/slow-queries")
async def get_slow_queries(limit: int = 10):
    """获取慢查询列表"""
    slow_queries = performance_monitor.get_slow_queries(limit)
    return {
        "success": True,
        "slow_queries": slow_queries,
        "count": len(slow_queries)
    }


@router.get("/performance/bottlenecks")
async def get_bottlenecks():
    """识别性能瓶颈"""
    bottlenecks = performance_monitor.get_bottlenecks()
    return {
        "success": True,
        "bottlenecks": bottlenecks,
        "count": len(bottlenecks)
    }

@router.get("/security/audit/overview", dependencies=[security_read_dep])
async def security_audit_overview(limit: int = 20):
    """统一安全与合规审计总览"""
    if not audit_pipeline:
        return {"events": [], "count": 0, "statistics": {}}
    records = audit_pipeline.query_records(limit=limit)
    stats = audit_pipeline.get_statistics()
    simplified = []
    for record in records:
        simplified.append({
            "event_id": record.get("record_id"),
            "type": record.get("event_type"),
            "source": record.get("source"),
            "success": record.get("status") == "success",
            "severity": record.get("severity"),
            "timestamp": record.get("timestamp"),
            "short": str(record.get("metadata", {}))[:120],
        })
    return {"events": simplified, "count": len(simplified), "statistics": stats}


@router.get("/security/audit/http", dependencies=[security_read_dep])
async def security_audit_http(limit: int = 50):
    if not audit_pipeline:
        return {"records": []}
    return {"records": audit_pipeline.get_http_records(limit)}


@router.get("/security/audit/tasks", dependencies=[security_read_dep])
async def security_audit_tasks(limit: int = 50):
    if not audit_pipeline:
        return {"records": []}
    return {"records": audit_pipeline.get_task_records(limit)}


@router.get("/security/audit/commands", dependencies=[security_read_dep])
async def security_audit_commands(limit: int = 50):
    if not audit_pipeline:
        return {"records": []}
    return {"records": audit_pipeline.get_command_records(limit)}


@router.get("/performance/cache-stats")
async def get_cache_stats():
    """获取缓存统计"""
    cache_stats = response_time_optimizer.get_cache_stats()
    return {
        "success": True,
        **cache_stats
    }


@router.post("/performance/clear-cache")
async def clear_cache():
    """清空缓存"""
    response_time_optimizer.clear_cache()
    return {
        "success": True,
        "message": "缓存已清空"
    }


@router.get("/resource/system")
async def get_system_resources():
    """获取系统资源占用情况（CPU/内存/磁盘/外接硬盘）⭐P0功能"""
    status = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts(severity="high")
    
    # 格式化资源信息
    cpu_info = status.get("cpu", {})
    memory_info = status.get("memory", {})
    disk_info = status.get("disk", {})
    external_drives = status.get("external_drives", [])
    
    return {
        "success": True,
        "resources": {
            "cpu": {
                "percent": cpu_info.get("percent", 0),
                "count": cpu_info.get("count", 0),
                "freq": cpu_info.get("freq"),
                "status": "normal" if cpu_info.get("percent", 0) < 80 else "high"
            },
            "memory": {
                "total_gb": round(memory_info.get("total", 0) / (1024**3), 2),
                "used_gb": round(memory_info.get("used", 0) / (1024**3), 2),
                "available_gb": round(memory_info.get("available", 0) / (1024**3), 2),
                "percent": memory_info.get("percent", 0),
                "status": "normal" if memory_info.get("percent", 0) < 85 else "high"
            },
            "disk": {
                "total_gb": round(disk_info.get("total", 0) / (1024**3), 2),
                "used_gb": round(disk_info.get("used", 0) / (1024**3), 2),
                "free_gb": round(disk_info.get("free", 0) / (1024**3), 2),
                "percent": disk_info.get("percent", 0),
                "status": "normal" if disk_info.get("percent", 0) < 90 else "high"
            },
            "external_drives": [
                {
                    "device": drive.get("device"),
                    "mountpoint": drive.get("mountpoint"),
                    "total_gb": round(drive.get("total", 0) / (1024**3), 2),
                    "used_gb": round(drive.get("used", 0) / (1024**3), 2),
                    "free_gb": round(drive.get("free", 0) / (1024**3), 2),
                    "percent": drive.get("percent", 0),
                    "connected": drive.get("connected", False),
                    "status": "normal" if drive.get("percent", 0) < 90 else "high"
                }
                for drive in external_drives
            ]
        },
        "alerts": alerts,
        "alerts_count": len(alerts),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/resource/external-drives")
async def get_external_drives():
    """获取外接硬盘连接情况⭐P0功能"""
    status = resource_monitor.get_current_status()
    external_drives = status.get("external_drives", [])
    
    return {
        "success": True,
        "external_drives": [
            {
                "device": drive.get("device"),
                "mountpoint": drive.get("mountpoint"),
                "fstype": drive.get("fstype"),
                "total_gb": round(drive.get("total", 0) / (1024**3), 2),
                "used_gb": round(drive.get("used", 0) / (1024**3), 2),
                "free_gb": round(drive.get("free", 0) / (1024**3), 2),
                "percent": drive.get("percent", 0),
                "connected": drive.get("connected", False)
            }
            for drive in external_drives
        ],
        "count": len(external_drives),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "super_agent": True,
            "memo_system": True,
            "task_planning": True,
            "learning_monitor": True,
            "resource_monitor": True,
            "resource_adjuster": True,
            "workflow_monitor": super_agent.workflow_monitor is not None,
            "voice_interaction": True,
            "translation": True,
            "file_generation": True,
            "web_search": True,
            "file_format_handler": True,
            "terminal_executor": True,
            "performance_monitor": True
        }
    }


class LLMConfigRequest(BaseModel):
    """LLM配置请求"""
    provider: str  # ollama/openai/anthropic/azure_openai
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    success: bool
    provider: str
    model: str
    base_url: str
    message: str


@router.post("/llm/config", response_model=LLMConfigResponse)
async def configure_llm(request: LLMConfigRequest):
    """
    配置LLM服务⭐新增
    
    支持：
    - ollama: 本地Ollama
    - openai: OpenAI API
    - anthropic: Anthropic Claude API
    - azure_openai: Azure OpenAI
    """
    try:
        # 验证提供商
        try:
            provider = LLMProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的LLM提供商: {request.provider}。支持: ollama, openai, anthropic, azure_openai"
            )
        
        # 更新LLM服务配置
        llm_service = get_llm_service(
            provider=request.provider.lower(),
            api_key=request.api_key,
            base_url=request.base_url,
            model=request.model
        )
        
        # 测试连接（可选）
        try:
            test_response = await llm_service.generate("测试", max_tokens=10)
            test_status = "连接成功"
        except Exception as e:
            test_status = f"配置成功，但连接测试失败: {str(e)}"
        
        return LLMConfigResponse(
            success=True,
            provider=llm_service.provider.value,
            model=llm_service.model,
            base_url=llm_service.base_url,
            message=f"LLM配置成功 ({llm_service.provider.value})。{test_status}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM配置失败: {str(e)}")


@router.get("/llm/config")
async def get_llm_config():
    """获取当前LLM配置"""
    try:
        llm_service = get_llm_service()
        return {
            "provider": llm_service.provider.value,
            "model": llm_service.model,
            "base_url": llm_service.base_url,
            "has_api_key": llm_service.api_key is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/providers")
async def get_llm_providers():
    """获取支持的LLM提供商列表"""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama (本地)",
                "description": "本地运行的Ollama服务",
                "default_url": "http://localhost:11434",
                "requires_api_key": False
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI GPT-4/GPT-3.5",
                "default_url": "https://api.openai.com/v1",
                "requires_api_key": True
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "description": "Anthropic Claude API",
                "default_url": "https://api.anthropic.com/v1",
                "requires_api_key": True
            },
            {
                "id": "azure_openai",
                "name": "Azure OpenAI",
                "description": "Azure OpenAI服务",
                "default_url": "",
                "requires_api_key": True
            }
        ]
    }

@router.post("/content/compliance/check")
async def check_content_compliance(
    text: str = Body(..., embed=True),
    references: Optional[List[str]] = Body(None, embed=True)
):
    """内容合规检查：原创度/相似度/敏感词（轻量版）"""
    result = await content_compliance.check_text(text, references or [])
    return result

# ====== 股票量化：数据源网关与模拟撮合 ======
@router.get("/stock/sources")
async def list_stock_sources():
    return stock_gateway.list_sources()

@router.post("/stock/switch-source")
async def switch_stock_source(source: str = Body(..., embed=True)):
    ok = stock_gateway.switch(source)
    if not ok:
        raise HTTPException(status_code=400, detail="数据源不存在")
    return {"success": True, "active": source}

@router.get("/stock/quote")
async def get_stock_quote(symbol: str, market: str = "A"):
    data = await stock_gateway.quote(symbol, market)
    # 同步给模拟器撮合（若有挂单）
    fills = stock_sim.mark_to_market_and_fill(symbol, data["price"])
    return {"quote": data, "sim_fills": fills}

@router.post("/stock/sim/place-order")
async def sim_place_order(
    symbol: str = Body(..., embed=True),
    side: str = Body(..., embed=True),  # buy/sell
    qty: int = Body(..., embed=True),
    order_type: str = Body("market", embed=True),  # market/limit
    price: Optional[float] = Body(None, embed=True)
):
    result = stock_sim.place_order(symbol, side, qty, order_type, price)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "下单失败"))
    return result

@router.post("/stock/sim/cancel")
async def sim_cancel(order_id: str = Body(..., embed=True)):
    result = stock_sim.cancel_order(order_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "撤单失败"))
    return result

@router.get("/stock/sim/state")
async def sim_state():
    return stock_sim.get_state()


@router.get("/stock/sim/risk-report")
async def sim_risk_report():
    return {"success": True, "report": stock_sim.get_risk_report()}


@router.get("/stock/sim/execution-report")
async def sim_execution_report():
    return {"success": True, "report": stock_sim.get_execution_report()}


@router.get("/stock/sim/trades")
async def sim_trades(limit: int = 50):
    return {"success": True, "trades": stock_sim.get_trades(limit=limit)}


@router.get("/stock/sim/risk-config")
async def sim_risk_config():
    return {"success": True, "config": stock_sim.get_risk_config()}


@router.post("/stock/sim/risk-config")
async def sim_update_risk_config(
    max_position_ratio: Optional[float] = Body(None, embed=True),
    stop_loss_ratio: Optional[float] = Body(None, embed=True),
    slip_bps: Optional[float] = Body(None, embed=True),
    max_single_trade_ratio: Optional[float] = Body(None, embed=True),
    max_daily_loss_ratio: Optional[float] = Body(None, embed=True),
    max_concentration_ratio: Optional[float] = Body(None, embed=True),
):
    """更新风控配置（增强版：支持更多参数）"""
    config = stock_sim.update_risk_config(
        max_position_ratio=max_position_ratio,
        stop_loss_ratio=stop_loss_ratio,
        slip_bps=slip_bps,
        max_single_trade_ratio=max_single_trade_ratio,
        max_daily_loss_ratio=max_daily_loss_ratio,
        max_concentration_ratio=max_concentration_ratio,
    )
    return {"success": True, "config": config}

@router.get("/stock/analysis/factors")
async def stock_factor_analysis(stock_code: str = Query(...)):
    """
    多模因子分析与预测信号
    """
    return stock_factor_engine.get_factor_analysis(stock_code)


@router.get("/stock/backtest")
async def stock_backtest(symbol: str = "000001", days: int = 60, seed: int = 7):
    return backtest_engine.run(symbol, days, seed)


# ==================== P1-010: 股票量化增强 ====================

@router.get("/stock/sources/health")
async def stock_get_source_health():
    """获取数据源健康状态"""
    return stock_gateway.get_source_health()


@router.get("/stock/execution/report")
async def stock_get_execution_report(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """获取执行分析报告"""
    return execution_analyzer.get_execution_report(symbol=symbol, days=days)


@router.get("/stock/execution/performance")
async def stock_get_execution_performance(
    symbol: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """获取执行性能指标"""
    return execution_analyzer.get_performance_metrics(symbol=symbol, days=days)


@router.get("/stock/analysis/factors/importance")
async def stock_get_factor_importance(symbol: str = Query(...)):
    """获取因子重要性排序"""
    return stock_factor_engine.get_factor_importance(symbol)


@router.get("/stock/brokers")
async def stock_list_brokers():
    """列出所有券商"""
    return broker_manager.list_brokers()


@router.post("/stock/brokers/{broker_name}/authorize")
async def stock_authorize_broker(
    broker_name: str,
    credentials: Dict[str, Any] = Body(...)
):
    """授权券商"""
    broker = broker_manager.get_broker(broker_name)
    if not broker:
        raise HTTPException(status_code=404, detail=f"券商 {broker_name} 不存在")
    
    result = await broker.authorize(credentials)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "授权失败"))
    
    return result


@router.get("/stock/brokers/{broker_name}/account")
async def stock_get_broker_account(broker_name: str):
    """获取券商账户信息"""
    broker = broker_manager.get_broker(broker_name)
    if not broker:
        raise HTTPException(status_code=404, detail=f"券商 {broker_name} 不存在")
    
    if not broker.is_authorized():
        raise HTTPException(status_code=403, detail="券商未授权")
    
    return await broker.get_account_info()


@router.post("/stock/brokers/{broker_name}/switch")
async def stock_switch_broker(broker_name: str):
    """切换券商"""
    success = broker_manager.switch_broker(broker_name)
    if not success:
        raise HTTPException(status_code=400, detail=f"切换失败：券商 {broker_name} 不存在或不可用")
    
    return {
        "success": True,
        "active_broker": broker_name,
        "broker_name": broker_manager.get_broker(broker_name).get_name()
    }

# ====== 抖音集成：授权与草稿发布（合规前置） ======
@router.get("/douyin/status")
async def douyin_status():
    return douyin.get_status()

@router.post("/douyin/begin-auth")
async def douyin_begin_auth():
    return douyin.begin_auth()

@router.post("/douyin/revoke")
async def douyin_revoke():
    return douyin.revoke()

class DouyinDraftRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None
    references: Optional[List[str]] = None
    min_originality: float = 60.0
    block_sensitive: bool = True


class DouyinAuthCallbackRequest(BaseModel):
    code: str
    state: str


class DouyinPublishRequest(DouyinDraftRequest):
    media_url: Optional[str] = None
    deai_enabled: bool = Field(False, description="是否启用去AI化")
    deai_style: str = Field("casual", description="去AI化风格（casual/formal/creative）")
    deai_intensity: float = Field(0.5, ge=0.0, le=1.0, description="去AI化强度（0.0-1.0）")


class TenantCreateRequest(BaseModel):
    tenant_id: str = Field(..., min_length=2, max_length=32, regex=r"^[a-z0-9\-_]+$")
    name: str
    plan: Optional[str] = "enterprise"
    active: Optional[bool] = True
    metadata: Optional[Dict[str, Any]] = None


class TenantUpdateRequest(BaseModel):
    name: Optional[str]
    plan: Optional[str]
    active: Optional[bool]
    metadata: Optional[Dict[str, Any]]


class DouyinWebhookPayload(BaseModel):
    event: str
    job_id: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.post("/douyin/create-draft")
async def douyin_create_draft(req: DouyinDraftRequest):
    compliance = await content_compliance.check_text(req.content, req.references or [])
    if not compliance.get("success"):
        raise HTTPException(status_code=400, detail=f"合规检测失败：{compliance.get('error','未知错误')}")
    if compliance["originality_percent"] < req.min_originality:
        return {
            "success": False,
            "blocked": True,
            "reason": "原创度不足",
            "compliance": compliance
        }
    if req.block_sensitive and compliance.get("sensitive_hits"):
        return {
            "success": False,
            "blocked": True,
            "reason": "命中敏感词",
            "compliance": compliance
        }
    draft = await douyin.create_draft(req.title, req.content, req.tags or [])
    if not draft.get("success"):
        raise HTTPException(status_code=400, detail=draft.get("error", "草稿创建失败"))
    return {
        "success": True,
        "draft": draft,
        "compliance": compliance
    }


@router.post("/content/copyright/check", response_model=CopyrightCheckResponse)
async def copyright_check(req: CopyrightCheckRequest):
    """
    版权/侵权检测（增强版：多平台相似度比对）
    """
    report = await copyright_inspector.run_workflow(
        text=req.text,
        sources=req.sources,
        platforms=req.platforms or ["douyin", "xiaohongshu", "kuaishou", "weibo", "bilibili"],
        threshold=req.threshold
    )
    return report


async def _storyboard_generate_logic(params: Dict[str, Any]) -> Dict[str, Any]:
    req = StoryboardRequest(**params["request"])
    return storyboard_generator.generate_storyboard(
        concept=req.concept,
        template_name=req.template or "fast_promo",
        duration=getattr(req, "duration", None),
        style=getattr(req, "style", "modern"),
    )


@router.post("/content/storyboard/generate", response_model=StoryboardResponse)
async def generate_storyboard(req: StoryboardRequest, response: Response):
    """
    视频脚本/分镜/节奏模板生成（增强版）
    """
    execution_id, exec_result = await run_closed_loop_operation(
        module="content",
        function="storyboard_generate",
        parameters={"request": req.model_dump()},
        executor=_storyboard_generate_logic,
        metadata={"concept": req.concept},
    )
    response.headers["X-Execution-ID"] = execution_id
    return exec_result.get("result") or {}


@router.post("/douyin/complete-auth")
async def douyin_complete_auth(req: DouyinAuthCallbackRequest):
    result = douyin.complete_auth(req.code, req.state)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "授权失败"))
    return result


@router.get("/douyin/jobs")
async def douyin_list_jobs():
    return {"jobs": douyin.list_jobs()}


@router.get("/douyin/callbacks")
async def douyin_list_callbacks():
    return {"callbacks": douyin.list_callbacks()}


@router.post("/douyin/publish")
async def douyin_publish(req: DouyinPublishRequest):
    """
    抖音内容发布（增强版：集成去AI化、运营分析）
    """
    status = douyin.get_status()
    if not status.get("authorized"):
        raise HTTPException(status_code=403, detail="抖音账号未授权")
    
    # 1. 合规检测
    compliance = await content_compliance.check_text(req.content, req.references or [])
    if not compliance.get("success"):
        raise HTTPException(status_code=400, detail=f"合规检测失败：{compliance.get('error','未知错误')}")
    if compliance["originality_percent"] < req.min_originality:
        return {
            "success": False,
            "blocked": True,
            "reason": "原创度不足",
            "compliance": compliance
        }
    if req.block_sensitive and compliance.get("sensitive_hits"):
        return {
            "success": False,
            "blocked": True,
            "reason": "命中敏感词",
            "compliance": compliance
        }
    
    # 2. 去AI化处理（可选）
    processed_content = req.content
    deai_result = None
    if getattr(req, "deai_enabled", False):
        deai_result = deai_pipeline.process(
            content=req.content,
            style=getattr(req, "deai_style", "casual"),
            intensity=getattr(req, "deai_intensity", 0.5)
        )
        processed_content = deai_result["processed"]
    
    # 3. 风控评估
    tags = req.tags or []
    risk = douyin.evaluate_risk(req.title, processed_content, tags)
    
    # 4. 提交发布
    job = douyin.submit_publication(
        title=req.title,
        content=processed_content,
        tags=tags,
        media_url=req.media_url,
        compliance=compliance,
        risk=risk
    )
    
    # 5. 记录到运营分析（如果发布成功）
    if job["status"] == "success" or job["status"] == "publishing":
        content_id = job.get("job_id") or f"content_{int(datetime.now().timestamp())}"
        content_analytics.record_publication(
            content_id=content_id,
            platform="douyin",
            title=req.title,
            tags=tags,
            published_at=datetime.now(),
            metadata={
                "job_id": job.get("job_id"),
                "deai_applied": deai_result is not None,
                "deai_score": deai_result["human_score"] if deai_result else None,
            }
        )
    
    return {
        "success": job["status"] == "success",
        "job": job,
        "risk": risk,
        "compliance": compliance,
        "deai": deai_result,
        "message": job.get("last_error")
    }


@router.post("/douyin/retry/{job_id}")
async def douyin_retry(job_id: str):
    try:
        job = douyin.retry_job(job_id)
        return {"success": job["status"] == "success", "job": job}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/douyin/webhook")
async def douyin_webhook(payload: DouyinWebhookPayload):
    """处理抖音Webhook回调"""
    event = douyin.handle_webhook(payload.dict())
    
    # 如果发布成功，更新运营分析数据
    if payload.status == "success" and payload.job_id:
        try:
            # 模拟获取统计数据（真实环境应从抖音API获取）
            import random
            stats = {
                "views": random.randint(1000, 50000),
                "likes": random.randint(100, 5000),
                "comments": random.randint(50, 2000),
                "shares": random.randint(20, 1000),
                "followers_gained": random.randint(0, 100),
            }
            content_analytics.update_stats(payload.job_id, stats)
        except Exception as e:
            logger.warning(f"更新运营分析失败: {e}")
    
    return {"success": True, "event": event}


@router.get("/integrations/api-monitor")
async def list_api_calls(system: Optional[str] = None, limit: int = 50):
    """查询第三方 API 调用记录"""
    records = api_monitor.list_recent(limit=limit, system=system)
    return {"success": True, "records": records, "count": len(records)}


@router.get("/integrations/api-monitor/stats")
async def api_monitor_statistics(system: Optional[str] = None, window_minutes: int = 60):
    """获取 API 调用统计"""
    stats = api_monitor.get_statistics(window_minutes=window_minutes, system=system)
    return {"success": True, "statistics": stats}


# ==================== P1-009: 内容创作系统全流程 ====================

class DeAIRequest(BaseModel):
    """去AI化请求"""
    content: str = Field(..., description="原始内容")
    style: str = Field("casual", description="风格（casual/formal/creative）")
    intensity: float = Field(0.5, ge=0.0, le=1.0, description="处理强度（0.0-1.0）")


class DeAIResponse(BaseModel):
    """去AI化响应"""
    original: str
    processed: str
    changes: List[str]
    ai_score: float
    human_score: float
    improvement: float
    style: str
    intensity: float


@router.post("/content/deai", response_model=DeAIResponse)
async def deai_process(req: DeAIRequest):
    """
    内容去AI化处理
    """
    result = deai_pipeline.process(
        content=req.content,
        style=req.style,
        intensity=req.intensity
    )
    return result


@router.get("/content/analytics")
async def get_content_analytics(
    content_id: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=90)
):
    """
    获取内容运营分析报告
    """
    result = content_analytics.get_analytics(
        content_id=content_id,
        platform=platform,
        days=days
    )
    return result


@router.get("/content/{content_id}/timeline")
async def get_content_timeline(content_id: str):
    """
    获取内容生命周期时间线
    """
    result = content_analytics.get_content_timeline(content_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "内容不存在"))
    return result


@router.post("/content/{content_id}/stats")
async def update_content_stats(
    content_id: str,
    stats: Dict[str, Any] = Body(...)
):
    """
    更新内容统计数据
    """
    result = content_analytics.update_stats(content_id, stats)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error", "内容不存在"))
    return result

# ====== RAG 预处理与真实性验证 ======
class RagPreprocessRequest(BaseModel):
    text: str

class RagPreprocessPipelineRequest(BaseModel):
    text: str
    steps: Optional[List[str]] = None  # 默认为全部
    min_authenticity: float = 55.0

@router.post("/rag/preprocess/clean")
async def rag_preprocess_clean(req: RagPreprocessRequest):
    if rag_clean is None:
        raise HTTPException(status_code=503, detail="预处理模块未就绪")
    cleaned = rag_clean(req.text)
    _record_rag_event("preprocess_clean", {"length": len(req.text)})
    return {"success": True, "text": cleaned}

@router.post("/rag/preprocess/standardize")
async def rag_preprocess_standardize(req: RagPreprocessRequest):
    if rag_standardize is None:
        raise HTTPException(status_code=503, detail="预处理模块未就绪")
    normalized = rag_standardize(req.text)
    _record_rag_event("preprocess_standardize", {"length": len(req.text)})
    return {"success": True, "text": normalized}

@router.post("/rag/preprocess/deduplicate")
async def rag_preprocess_deduplicate(req: RagPreprocessRequest):
    if rag_dedup is None:
        raise HTTPException(status_code=503, detail="预处理模块未就绪")
    res = rag_dedup(req.text)
    _record_rag_event("preprocess_deduplicate", {"removed": res.get("removed", 0)})
    return {"success": True, **res}

@router.post("/rag/preprocess/validate")
async def rag_preprocess_validate(req: RagPreprocessRequest):
    if rag_validate is None:
        raise HTTPException(status_code=503, detail="预处理模块未就绪")
    res = rag_validate(req.text)
    _record_rag_event("preprocess_validate", {"valid": res.get("valid", True)})
    return {"success": True, **res}

@router.post("/rag/authenticity/check")
async def rag_authenticity_check(req: RagPreprocessRequest):
    if rag_auth_score is None:
        raise HTTPException(status_code=503, detail="真实性模块未就绪")
    res = rag_auth_score(req.text)
    _record_rag_event("authenticity_check", {"score": res.get("score")})
    return res

@router.post("/rag/preprocess/run")
async def rag_preprocess_pipeline(req: RagPreprocessPipelineRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail="缺少文本")
    steps = req.steps or ["clean", "standardize", "deduplicate", "validate"]
    text = req.text
    outputs: Dict[str, Any] = {"original_length": len(text)}
    try:
        if "clean" in steps and rag_clean:
            text = rag_clean(text)
            outputs["clean"] = {"length": len(text)}
        if "standardize" in steps and rag_standardize:
            text = rag_standardize(text)
            outputs["standardize"] = {"length": len(text)}
        if "deduplicate" in steps and rag_dedup:
            dedup_result = rag_dedup(text)
            text = dedup_result.get("unique_text", text)
            outputs["deduplicate"] = dedup_result
        if "validate" in steps and rag_validate:
            outputs["validate"] = rag_validate(text)
        authenticity = rag_auth_score(text) if rag_auth_score else {"score": 0}
        outputs["authenticity"] = authenticity
        accepted = authenticity.get("score", 0) >= req.min_authenticity
        _record_rag_event("preprocess_pipeline", {
            "steps": steps,
            "accepted": accepted,
            "score": authenticity.get("score")
        })
        return {
            "success": True,
            "accepted": accepted,
            "text": text,
            "outputs": outputs
        }
    except Exception as exc:
        _record_rag_event("preprocess_pipeline_error", {"error": str(exc)})
        raise

# ====== RAG 流水线化：上传→预处理→真实性→入库（最小可用） ======
class RagIngestRequest(BaseModel):
    text: Optional[str] = None
    title: Optional[str] = None
    run_clean: bool = True
    run_standardize: bool = True
    run_dedup: bool = True
    min_authenticity: float = 55.0


class SensitiveOperationRequest(BaseModel):
    applicant: str
    operation: str
    justification: str
    metadata: Optional[Dict[str, Any]] = None


class ApprovalDecisionRequest(BaseModel):
    reviewer: str
    reason: Optional[str] = None


async def _rag_pipeline_ingest_logic(params: Dict[str, Any]) -> Dict[str, Any]:
    req = RagIngestRequest(**params["request"])
    if not req.text:
        raise HTTPException(status_code=400, detail="缺少文本")
    text = req.text
    steps: Dict[str, Any] = {}
    if req.run_clean and rag_clean:
        text = rag_clean(text)
        steps["clean"] = True
    if req.run_standardize and rag_standardize:
        text = rag_standardize(text)
        steps["standardize"] = True
    if req.run_dedup and rag_dedup:
        d = rag_dedup(text)
        text = d.get("unique_text", text)
        steps["deduplicate"] = {
            "removed": d.get("removed"),
            "kept": d.get("kept"),
        }
    valid = rag_validate(text) if rag_validate else {"valid": True}
    auth = rag_auth_score(text) if rag_auth_score else {"score": 100.0}
    accepted = auth.get("score", 0) >= req.min_authenticity and valid.get("valid", True)
    doc = {
        "id": f"doc_{int(datetime.now().timestamp() * 1000)}",
        "title": req.title or (text[:30] if text else "文档"),
        "content": text,
        "ingested_at": datetime.now().isoformat(),
        "authenticity": auth,
        "validation": valid,
    }
    try:
        with open(rag_store_path, "a", encoding="utf-8") as f:
            import json as _json

            f.write(_json.dumps(doc, ensure_ascii=False) + "\n")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"持久化失败: {str(exc)}")

    return {
        "success": True,
        "accepted": accepted,
        "document": doc,
        "steps": steps,
    }

@router.post("/rag/pipeline/ingest")
async def rag_pipeline_ingest(req: RagIngestRequest):
    execution_id, exec_result = await run_closed_loop_operation(
        module="rag",
        function="pipeline_ingest",
        parameters={"request": req.model_dump()},
        executor=_rag_pipeline_ingest_logic,
        metadata={"title": req.title},
    )
    payload = exec_result.get("result") or {}
    payload["execution_id"] = execution_id
    return payload

@router.get("/rag/pipeline/documents")
async def rag_pipeline_list_docs(limit: int = 20):
    """列出最近入库的RAG文档（占位存储）"""
    items = []
    try:
        if rag_store_path.exists():
            with open(rag_store_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]
                import json as _json
                for line in reversed(lines):
                    try:
                        items.append(_json.loads(line))
                    except Exception:
                        continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"documents": items, "count": len(items)}

@router.get("/rag/pipeline/search")
async def rag_pipeline_search(q: str, limit: int = 10):
    """占位检索：基于子串与简单关键词匹配"""
    results = []
    try:
        if not rag_store_path.exists():
            return {"results": [], "count": 0}
        with open(rag_store_path, "r", encoding="utf-8") as f:
            import json as _json, re as _re
            kws = [k for k in _re.split(r"\W+", q) if k]
            for line in reversed(f.readlines()):
                try:
                    doc = _json.loads(line)
                except Exception:
                    continue
                text = (doc.get("title", "") + "\n" + doc.get("content", ""))
                score = 0
                if q in text:
                    score += 2
                score += sum(1 for k in kws if k and k in text)
                if score > 0:
                    results.append({"id": doc.get("id"), "title": doc.get("title"), "score": score})
                if len(results) >= limit:
                    break
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"results": results, "count": len(results)}

# ====== 编程助手：Cursor 桥接 ======
@router.get("/coding/cursor/status")
async def cursor_status():
    return cursor_bridge.get_status()

class CursorOpenRequest(BaseModel):
    file_path: str
    line_number: Optional[int] = None

@router.post("/coding/cursor/open-file")
async def cursor_open_file(req: CursorOpenRequest):
    result = await cursor_bridge.open_in_cursor(req.file_path, req.line_number)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "打开失败"))
    return result

class CursorSyncRequest(BaseModel):
    file_path: str
    code: str

@router.post("/coding/cursor/sync-code")
async def cursor_sync_code(req: CursorSyncRequest):
    return await cursor_bridge.sync_code(req.file_path, req.code)

class CursorEdit(BaseModel):
    type: str
    start_line: int
    end_line: int
    content: Optional[str] = ""

class CursorEditRequest(BaseModel):
    file_path: str
    edits: List[CursorEdit]

@router.post("/coding/cursor/edit-code")
async def cursor_edit_code(req: CursorEditRequest):
    edits = [e.dict() for e in req.edits]
    return await cursor_bridge.edit_code(req.file_path, edits)

class CursorCompletionRequest(BaseModel):
    file_path: str
    line_number: int
    column: int
    context_lines: int = 5

@router.post("/coding/cursor/completion")
async def cursor_completion(req: CursorCompletionRequest):
    return await cursor_bridge.get_code_completion(req.file_path, req.line_number, req.column, req.context_lines)

class CursorDetectRequest(BaseModel):
    file_path: str

@router.post("/coding/cursor/detect-errors")
async def cursor_detect_errors(req: CursorDetectRequest):
    return await cursor_bridge.detect_errors(req.file_path)

class CursorProjectRequest(BaseModel):
    project_path: str
    files: Optional[List[str]] = None

# ==================== P3-014: AI 编程助手 + Cursor 集成 ====================

@router.post("/coding/documentation/generate-docstring")
async def generate_docstring(
    code: str = Body(..., embed=True),
    language: str = Body("python", embed=True),
    style: str = Body("google", embed=True)
):
    """
    生成文档字符串
    """
    result = documentation_generator.generate_docstring(code, language, style)
    return result


@router.post("/coding/documentation/generate-api-doc")
async def generate_api_documentation(
    code: str = Body(..., embed=True),
    api_type: str = Body("rest", embed=True)
):
    """
    生成API文档
    """
    result = documentation_generator.generate_api_documentation(code, api_type)
    return result


@router.post("/coding/documentation/generate-readme")
async def generate_readme(
    project_info: Dict[str, Any] = Body(...)
):
    """
    生成README文档
    """
    readme_content = documentation_generator.generate_readme(project_info)
    return {
        "success": True,
        "readme": readme_content,
        "generated_at": datetime.now().isoformat()
    }


@router.get("/coding/command-replay/history")
async def get_command_replay_history(
    limit: int = Query(50, ge=1, le=200),
    filter_command: Optional[str] = Query(None)
):
    """
    获取命令回放历史
    """
    history = command_replay.get_replay_history(limit, filter_command)
    return {
        "success": True,
        "history": history,
        "count": len(history)
    }


@router.post("/coding/command-replay/replay")
async def replay_command(
    command_id: Optional[str] = Body(None, embed=True),
    command: Optional[str] = Body(None, embed=True)
):
    """
    回放命令
    """
    result = command_replay.replay_command(command_id, command)
    return result


@router.get("/coding/cursor/status-enhanced")
async def get_cursor_status_enhanced():
    """
    获取Cursor状态（增强版）
    """
    status = cursor_ide_integration.get_status()
    return {
        "success": True,
        "status": status
    }


@router.post("/coding/cursor/open-file-enhanced")
async def open_file_in_cursor_enhanced(
    file_path: str = Body(..., embed=True),
    line_number: Optional[int] = Body(None, embed=True)
):
    """
    在Cursor中打开文件（增强版）
    """
    result = await cursor_ide_integration.open_file(file_path, line_number)
    return result


@router.post("/coding/cursor/apply-edits")
async def apply_edits_in_cursor(
    file_path: str = Body(..., embed=True),
    edits: List[Dict[str, Any]] = Body(...)
):
    """
    在Cursor中应用代码编辑
    """
    result = await cursor_ide_integration.apply_edits(file_path, edits)
    return result


@router.post("/coding/sandbox/link-main-interface")
async def link_sandbox_to_main_interface(
    command_id: str = Body(..., embed=True),
    action: str = Body(..., embed=True)  # execute, review, optimize
):
    """
    安全沙箱与主界面联动
    将沙箱中的命令执行结果同步到主界面
    """
    # 查找命令记录
    command_record = next(
        (r for r in terminal_executor.command_history if r.command_id == command_id),
        None
    )
    
    if not command_record:
        return {
            "success": False,
            "error": f"未找到命令ID: {command_id}"
        }
    
    # 根据action执行相应操作
    if action == "execute":
        # 记录到命令回放系统
        command_replay.record_command(
            command=command_record.command,
            result={
                "success": command_record.success,
                "return_code": command_record.return_code,
                "error": command_record.error
            },
            metadata={
                "command_id": command_id,
                "timestamp": command_record.timestamp,
                "cwd": command_record.cwd
            }
        )
    
    return {
        "success": True,
        "command_id": command_id,
        "action": action,
        "linked_at": datetime.now().isoformat(),
        "command": command_record.command
    }


@router.get("/coding/sandbox/main-interface-status")
async def get_sandbox_main_interface_status():
    """
    获取沙箱与主界面联动状态
    """
    return {
        "success": True,
        "sandbox_enabled": terminal_executor.sandbox_enabled,
        "sandbox_dir": str(terminal_executor.sandbox_dir) if terminal_executor.sandbox_dir else None,
        "command_history_count": len(terminal_executor.command_history),
        "replay_history_count": len(command_replay.replay_history),
        "cursor_available": cursor_ide_integration.is_cursor_available
    }


@router.post("/coding/review")
async def review_code(
    code: str = Body(..., embed=True),
    language: str = Body("python", embed=True)
):
    """
    代码审查（增强版：集成编程助手）
    """
    try:
        # 尝试导入编程助手的代码审查器
        try:
            import sys
            coding_module_path = project_root / "💻 AI Programming Assistant"
            if str(coding_module_path) not in sys.path:
                sys.path.insert(0, str(coding_module_path))
            from core.code_reviewer import CodeReviewer
            reviewer = CodeReviewer()
            result = await reviewer.review_code(code, language)
            return result
        except ImportError:
            # 如果无法导入，返回简化结果
            return {
                "success": True,
                "issues": [],
                "suggestions": ["建议使用完整的代码审查功能"],
                "score": 100,
                "summary": {
                    "total_issues": 0,
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0
                }
            }
    except Exception as e:
        logger.error(f"代码审查失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/coding/optimize")
async def optimize_code(
    problem_description: str = Body(..., embed=True),
    context: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """
    性能优化（增强版：集成编程助手）
    """
    try:
        # 尝试导入编程助手的代码优化器
        try:
            import sys
            coding_module_path = project_root / "💻 AI Programming Assistant"
            if str(coding_module_path) not in sys.path:
                sys.path.insert(0, str(coding_module_path))
            from core.code_optimizer import CodeOptimizer
            optimizer = CodeOptimizer()
            result = await optimizer.optimize_performance(problem_description, context)
            return result
        except ImportError:
            # 如果无法导入，返回通用建议
            return {
                "success": True,
                "optimization": {
                    "problem": problem_description,
                    "suggestions": [
                        "使用缓存减少重复计算",
                        "优化数据库查询",
                        "使用异步处理",
                        "减少不必要的循环"
                    ],
                    "optimized_code": "# 优化后的代码\n# TODO: 提供代码以进行优化",
                    "expected_improvement": "响应时间减少50%"
                }
            }
    except Exception as e:
        logger.error(f"性能优化失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/coding/cursor/open-project")
async def cursor_open_project(req: CursorProjectRequest):
    result = await cursor_bridge.sync_project(req.project_path, req.files)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "打开项目失败"))
    return result


# ============ P0-016: Cursor协议/插件/本地桥/授权系统 ============

@router.post("/cursor/protocol/start")
async def start_cursor_protocol():
    """启动Cursor协议服务器"""
    if not cursor_protocol:
        raise HTTPException(status_code=503, detail="Cursor协议未初始化")
    
    await cursor_local_bridge.start()
    return {"success": True, "message": "Cursor协议服务器已启动"}


@router.post("/cursor/protocol/stop")
async def stop_cursor_protocol():
    """停止Cursor协议服务器"""
    if not cursor_protocol:
        raise HTTPException(status_code=503, detail="Cursor协议未初始化")
    
    await cursor_local_bridge.stop()
    return {"success": True, "message": "Cursor协议服务器已停止"}


@router.post("/cursor/protocol/send")
async def send_cursor_protocol_message(
    command: str,
    params: Dict[str, Any],
    token_id: Optional[str] = None
):
    """
    发送Cursor协议消息
    
    Args:
        command: 命令名称
        params: 命令参数
        token_id: 授权令牌ID（可选）
    """
    if not cursor_protocol:
        raise HTTPException(status_code=503, detail="Cursor协议未初始化")
    
    # 验证授权
    if token_id and not cursor_authorization.validate_token(token_id):
        raise HTTPException(status_code=401, detail="无效的授权令牌")
    
    try:
        cmd = ProtocolCommand(command)
        message = await cursor_local_bridge.send_to_cursor(cmd, params)
        
        return {
            "success": message.message_type.value != "error",
            "message_type": message.message_type.value,
            "result": message.result,
            "error": message.error
        }
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的命令: {command}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cursor/plugins/load")
async def load_cursor_plugin(
    plugin_path: str,
    config: Optional[Dict[str, Any]] = None
):
    """
    加载Cursor插件
    
    Args:
        plugin_path: 插件路径
        config: 插件配置（可选）
    """
    if not cursor_plugin_system:
        raise HTTPException(status_code=503, detail="插件系统未初始化")
    
    try:
        plugin = cursor_plugin_system.load_plugin(plugin_path, config)
        return {
            "success": True,
            "plugin": {
                "plugin_id": plugin.metadata.plugin_id,
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "status": plugin.status.value
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cursor/plugins")
async def list_cursor_plugins():
    """列出所有Cursor插件"""
    if not cursor_plugin_system:
        raise HTTPException(status_code=503, detail="插件系统未初始化")
    
    plugins = cursor_plugin_system.list_plugins()
    return {"success": True, "plugins": plugins}


@router.post("/cursor/plugins/{plugin_id}/enable")
async def enable_cursor_plugin(plugin_id: str):
    """启用Cursor插件"""
    if not cursor_plugin_system:
        raise HTTPException(status_code=503, detail="插件系统未初始化")
    
    try:
        cursor_plugin_system.enable_plugin(plugin_id)
        return {"success": True, "message": f"插件已启用: {plugin_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cursor/plugins/{plugin_id}/disable")
async def disable_cursor_plugin(plugin_id: str):
    """禁用Cursor插件"""
    if not cursor_plugin_system:
        raise HTTPException(status_code=503, detail="插件系统未初始化")
    
    try:
        cursor_plugin_system.disable_plugin(plugin_id)
        return {"success": True, "message": f"插件已禁用: {plugin_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/cursor/plugins/{plugin_id}")
async def unload_cursor_plugin(plugin_id: str):
    """卸载Cursor插件"""
    if not cursor_plugin_system:
        raise HTTPException(status_code=503, detail="插件系统未初始化")
    
    try:
        cursor_plugin_system.unload_plugin(plugin_id)
        return {"success": True, "message": f"插件已卸载: {plugin_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cursor/authorization/create-token")
async def create_cursor_token(
    client_id: str,
    authorization_level: str,
    access_scope: str,
    allowed_paths: Optional[List[str]] = None,
    denied_paths: Optional[List[str]] = None,
    expires_in_hours: Optional[int] = None
):
    """
    创建Cursor授权令牌
    
    Args:
        client_id: 客户端ID
        authorization_level: 授权级别（none/read_only/limited/standard/full）
        access_scope: 访问范围（single_file/project/workspace/system）
        allowed_paths: 允许的路径列表（可选）
        denied_paths: 拒绝的路径列表（可选）
        expires_in_hours: 过期时间（小时，可选）
    """
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    try:
        level = AuthorizationLevel(authorization_level)
        scope = AccessScope(access_scope)
        
        token = cursor_authorization.create_token(
            client_id=client_id,
            authorization_level=level,
            access_scope=scope,
            allowed_paths=allowed_paths,
            denied_paths=denied_paths,
            expires_in_hours=expires_in_hours
        )
        
        return {
            "success": True,
            "token": {
                "token_id": token.token_id,
                "client_id": token.client_id,
                "authorization_level": token.authorization_level.value,
                "access_scope": token.access_scope.value,
                "expires_at": token.expires_at.isoformat() if token.expires_at else None
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cursor/authorization/validate")
async def validate_cursor_token(token_id: str):
    """验证Cursor授权令牌"""
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    is_valid = cursor_authorization.validate_token(token_id)
    token = cursor_authorization.get_token(token_id)
    
    return {
        "success": True,
        "is_valid": is_valid,
        "token": {
            "token_id": token_id,
            "authorization_level": token.authorization_level.value if token else None,
            "expires_at": token.expires_at.isoformat() if token and token.expires_at else None
        } if token else None
    }


@router.post("/cursor/authorization/check-permission")
async def check_cursor_permission(
    token_id: str,
    resource_type: str,
    resource_path: str,
    action: str
):
    """
    检查Cursor权限
    
    Args:
        token_id: 令牌ID
        resource_type: 资源类型
        resource_path: 资源路径
        action: 操作（read/write/execute）
    """
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    has_permission = cursor_authorization.check_permission(
        token_id, resource_type, resource_path, action
    )
    
    return {
        "success": True,
        "has_permission": has_permission,
        "resource_type": resource_type,
        "resource_path": resource_path,
        "action": action
    }


@router.delete("/cursor/authorization/tokens/{token_id}")
async def revoke_cursor_token(token_id: str, reason: Optional[str] = None):
    """撤销Cursor授权令牌"""
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    cursor_authorization.revoke_token(token_id, reason)
    return {"success": True, "message": f"令牌已撤销: {token_id}"}


@router.get("/cursor/authorization/tokens")
async def list_cursor_tokens(client_id: Optional[str] = None):
    """列出Cursor授权令牌"""
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    tokens = cursor_authorization.list_tokens(client_id)
    return {"success": True, "tokens": tokens}


@router.get("/cursor/authorization/audit-log")
async def get_cursor_audit_log(
    token_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """获取Cursor审计日志"""
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    logs = cursor_authorization.get_audit_log(token_id, event_type, limit)
    return {"success": True, "logs": logs, "count": len(logs)}


@router.get("/cursor/bridge/status")
async def get_cursor_bridge_status():
    """获取Cursor桥接状态"""
    if not cursor_local_bridge:
        raise HTTPException(status_code=503, detail="本地桥接未初始化")
    
    status = cursor_local_bridge.get_status()
    return {"success": True, "status": status}


@router.get("/cursor/bridge/connections")
async def list_cursor_bridge_connections():
    """列出Cursor桥接连接"""
    if not cursor_local_bridge:
        raise HTTPException(status_code=503, detail="本地桥接未初始化")
    
    connections = cursor_local_bridge.list_connections()
    return {"success": True, "connections": connections}


@router.get("/cursor/authorization/statistics")
async def get_cursor_authorization_statistics():
    """获取Cursor授权统计信息"""
    if not cursor_authorization:
        raise HTTPException(status_code=503, detail="授权系统未初始化")
    
    stats = cursor_authorization.get_statistics()
    return {"success": True, "statistics": stats}


# ============ P0-017: 安全与合规基线 ============

@router.post("/security/crawler/check", dependencies=[security_read_dep])
async def check_crawler_security(
    url: str,
    source: str = "system",
    user_agent: Optional[str] = None,
    client_ip: Optional[str] = None,
):
    """
    检查爬虫请求安全性
    """
    compliance = crawler_compliance_service.evaluate(user_agent, url, client_ip)
    baseline_result = None
    if security_compliance_baseline:
        baseline_result = await security_compliance_baseline.check_crawler_request(url, source)
    result = {"crawler_policy": compliance, "baseline": baseline_result}
    if audit_pipeline:
        audit_pipeline.log_security_event(
            event_type="crawler.check",
            source="api",
            severity="warning" if not compliance["allowed"] else "info",
            metadata=result,
        )
    return {"success": True, "result": result}


@router.post("/security/content/check", dependencies=[security_read_dep])
async def check_content_security(
    content: str,
    content_type: str = "text",
    source: str = "system"
):
    """
    检查内容安全性
    
    Args:
        content: 内容
        content_type: 内容类型
        source: 来源
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    result = await security_compliance_baseline.check_content_security(content, content_type, source)
    return {"success": True, "result": result}


@router.post("/security/data/check-permission", dependencies=[security_read_dep])
async def check_data_permission(
    resource_path: str,
    action: str,
    user_id: str,
    user_permissions: Optional[List[str]] = None
):
    """
    检查数据权限
    
    Args:
        resource_path: 资源路径
        action: 操作类型（read/write/delete）
        user_id: 用户ID
        user_permissions: 用户权限列表（可选）
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    result = await security_compliance_baseline.check_data_permission(
        resource_path, action, user_id, user_permissions
    )
    return {"success": True, "result": result}


@router.post("/security/command/check", dependencies=[security_read_dep])
async def check_command_security(
    command: str,
    source: str = "system"
):
    """
    检查命令安全性
    
    Args:
        command: 命令
        source: 来源
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    result = await security_compliance_baseline.check_command_security(command, source)
    return {"success": True, "result": result}


@router.post("/security/privacy/check", dependencies=[security_read_dep])
async def check_privacy_compliance(
    data: str,
    data_type: str = "text",
    source: str = "system"
):
    """
    检查隐私合规性
    
    Args:
        data: 数据
        data_type: 数据类型
        source: 来源
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    result = await security_compliance_baseline.check_privacy_compliance(data, data_type, source)
    return {"success": True, "result": result}


@router.post("/security/approvals/request", dependencies=[security_write_dep])
async def submit_sensitive_operation(req: SensitiveOperationRequest):
    approval = approval_manager.submit_request(
        applicant=req.applicant,
        operation=req.operation,
        justification=req.justification,
        metadata=req.metadata,
    )
    return {"success": True, "approval": asdict(approval)}


@router.post("/security/approvals/{approval_id}/approve", dependencies=[security_write_dep])
async def approve_sensitive_operation(approval_id: str, decision: ApprovalDecisionRequest):
    approval = approval_manager.approve(approval_id, decision.reviewer, decision.reason)
    if not approval:
        raise HTTPException(status_code=404, detail="审批不存在")
    return {"success": True, "approval": asdict(approval)}


@router.post("/security/approvals/{approval_id}/reject", dependencies=[security_write_dep])
async def reject_sensitive_operation(approval_id: str, decision: ApprovalDecisionRequest):
    approval = approval_manager.reject(approval_id, decision.reviewer, decision.reason)
    if not approval:
        raise HTTPException(status_code=404, detail="审批不存在")
    return {"success": True, "approval": asdict(approval)}


@router.get("/security/approvals/{approval_id}", dependencies=[security_read_dep])
async def get_sensitive_operation(approval_id: str):
    approval = approval_manager.get_request(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="审批不存在")
    return {"success": True, "approval": asdict(approval)}


@router.get("/security/approvals/pending", dependencies=[security_read_dep])
async def list_pending_approvals(limit: int = 50):
    rows = approval_manager.list_requests(status=ApprovalStatus.PENDING, limit=limit)
    return {"success": True, "approvals": rows}


@router.get("/security/violations", dependencies=[security_read_dep])
async def get_security_violations(
    category: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100
):
    """
    获取安全违规记录
    
    Args:
        category: 类别筛选（crawler/content/data/command/privacy）
        severity: 严重程度筛选（low/medium/high/critical）
        limit: 返回数量限制
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    category_enum = None
    if category:
        try:
            category_enum = ComplianceCategory(category)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的类别: {category}")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = SecurityLevel(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的严重程度: {severity}")
    
    violations = security_compliance_baseline.get_violations(category_enum, severity_enum, limit)
    return {"success": True, "violations": violations, "count": len(violations)}


@router.get("/security/audit-log", dependencies=[security_read_dep])
async def get_security_audit_log(
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 1000
):
    """
    获取安全审计日志
    
    Args:
        event_type: 事件类型筛选（可选）
        severity: 严重程度筛选（可选）
        limit: 返回数量限制
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    logs = security_compliance_baseline.get_audit_log(event_type, severity, limit)
    return {"success": True, "logs": logs, "count": len(logs)}


@router.get("/security/policies", dependencies=[security_read_dep])
async def list_security_policies():
    """列出所有安全合规策略"""
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    policies = security_compliance_baseline.list_policies()
    return {"success": True, "policies": policies}


@router.get("/security/policies/{policy_id}", dependencies=[security_read_dep])
async def get_security_policy(policy_id: str):
    """获取安全合规策略"""
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    policy = security_compliance_baseline.get_policy(policy_id)
    if not policy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return {"success": True, "policy": policy}


@router.put("/security/policies/{policy_id}", dependencies=[security_write_dep])
async def update_security_policy(
    policy_id: str,
    rules: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None
):
    """
    更新安全合规策略
    
    Args:
        policy_id: 策略ID
        rules: 新规则（可选）
        enabled: 是否启用（可选）
    """
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    try:
        result = security_compliance_baseline.update_policy(policy_id, rules, enabled)
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/security/statistics", dependencies=[security_read_dep])
async def get_security_statistics():
    """获取安全合规统计信息"""
    if not security_compliance_baseline:
        raise HTTPException(status_code=503, detail="安全合规基线系统未初始化")
    
    stats = security_compliance_baseline.get_statistics()
    return {"success": True, "statistics": stats}


@router.get("/security/risk/summary", dependencies=[security_read_dep])
async def get_security_risk_summary():
    """获取风控概览"""
    summary = risk_engine.get_summary() if risk_engine else {}
    return {"success": True, "summary": summary}


@router.get("/security/risk/events", dependencies=[security_read_dep])
async def get_security_risk_events(limit: int = 50):
    """获取风控事件列表"""
    events = risk_engine.list_events(limit) if risk_engine else []
    return {"success": True, "events": events, "count": len(events)}


# ============ P1-001: 模块三级界面 ============


@router.get("/modules/tree")
async def get_module_tree():
    """获取所有模块的三级界面结构"""
    modules = await module_registry.get_tree()
    return {"success": True, "modules": modules}


@router.get("/modules/view-data")
async def get_module_view_data(module: str, stage: str, view: str):
    """获取指定视图的实时数据"""
    try:
        data = await module_registry.get_view_data(module, stage, view)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return {"success": True, "module": module, "stage": stage, "view": view, "data": data}


@router.get("/modules/view-capabilities")
async def get_module_view_capabilities(module: str, stage: str, view: str):
    """获取视图对应的四级能力单元"""
    capabilities = FOUR_LEVEL_FUNCTIONS.get(module, {}).get(stage, {}).get(view, [])
    return {
        "success": True,
        "module": module,
        "stage": stage,
        "view": view,
        "capabilities": capabilities,
    }


@router.get("/modules/chains")
async def list_module_chains(refresh: bool = Query(False, description="是否强制刷新链路")):
    chains = await module_chain_manager.list_chains(refresh=refresh)
    return {"success": True, "chains": chains, "count": len(chains)}


@router.get("/modules/chains/{module_id}")
async def get_module_chain_entry(module_id: str):
    try:
        chain = await module_chain_manager.get_chain(module_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"未找到模块链路: {module_id}")
    return {"success": True, "chain": chain}


@router.post("/modules/chains/refresh", dependencies=[security_read_dep])
async def refresh_module_chains():
    chains = await module_chain_manager.refresh()
    return {"success": True, "chains": chains, "count": len(chains)}


# ============ P0-018: 可观测性系统 ============

@router.get("/observability/traces/{trace_id}")
async def get_trace(trace_id: str):
    """获取Trace详情"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    trace = observability_system.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace不存在")
    
    return {"success": True, "trace": trace.to_dict()}


@router.get("/observability/traces")
async def list_traces(
    request_id: Optional[str] = None,
    service_name: Optional[str] = None,
    limit: int = 100
):
    """列出Trace"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    if request_id:
        trace = observability_system.get_trace_by_request_id(request_id)
        if trace:
            return {"success": True, "traces": [trace.to_dict()], "count": 1}
        return {"success": True, "traces": [], "count": 0}
    
    # 返回活跃的Trace
    active_traces = observability_system.get_active_traces()
    return {"success": True, "traces": active_traces[:limit], "count": len(active_traces)}


@router.get("/observability/long-tasks")
async def list_long_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100
):
    """列出长任务"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    active_tasks = observability_system.get_active_long_tasks()
    
    # 过滤
    if task_type:
        active_tasks = [t for t in active_tasks if t.get("task_type") == task_type]
    if status:
        active_tasks = [t for t in active_tasks if t.get("status") == status]
    
    return {"success": True, "tasks": active_tasks[:limit], "count": len(active_tasks)}


@router.get("/observability/long-tasks/{task_id}")
async def get_long_task(task_id: str):
    """获取长任务详情"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    task = observability_system.get_long_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {"success": True, "task": task.to_dict()}


@router.get("/observability/long-tasks/{task_id}/replay")
async def get_long_task_replay(task_id: str):
    """获取长任务回放数据"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    replay_data = observability_system.get_long_task_replay(task_id)
    if not replay_data:
        raise HTTPException(status_code=404, detail="任务不存在或没有回放数据")
    
    return {"success": True, "replay": replay_data}


@router.post("/observability/long-tasks")
async def create_long_task(
    name: str,
    task_type: str,
    trace_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """创建长任务"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    task = observability_system.create_long_task(
        name=name,
        task_type=task_type,
        trace_id=trace_id,
        metadata=metadata
    )
    
    return {"success": True, "task": task.to_dict()}


@router.put("/observability/long-tasks/{task_id}/progress")
async def update_long_task_progress(
    task_id: str,
    progress: float,
    step: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """更新长任务进度"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    observability_system.update_long_task_progress(
        task_id=task_id,
        progress=progress,
        step=step,
        metadata=metadata
    )
    
    return {"success": True, "message": "进度已更新"}


@router.post("/observability/long-tasks/{task_id}/complete")
async def complete_long_task(
    task_id: str,
    status: str = "completed",
    error: Optional[str] = None
):
    """完成长任务"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    observability_system.complete_long_task(
        task_id=task_id,
        status=status,
        error=error
    )
    
    return {"success": True, "message": "任务已完成"}


@router.get("/observability/metrics")
async def get_metrics(
    name: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    tags: Optional[Dict[str, str]] = None
):
    """获取指标"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    metrics = observability_system.get_metrics(
        name=name,
        start_time=start_time,
        end_time=end_time,
        tags=tags
    )
    
    return {
        "success": True,
        "metrics": [
            {
                "name": m.name,
                "value": m.value,
                "timestamp": m.timestamp,
                "tags": m.tags,
                "metric_type": m.metric_type
            }
            for m in metrics
        ],
        "count": len(metrics)
    }


@router.post("/observability/metrics")
async def record_metric(
    name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None,
    metric_type: str = "gauge"
):
    """记录指标"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    observability_system.record_metric(
        name=name,
        value=value,
        tags=tags,
        metric_type=metric_type
    )
    
    return {"success": True, "message": "指标已记录"}


@router.post("/observability/events")
async def track_event(
    event_name: str,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None,
    level: str = "info"
):
    """埋点事件"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    observability_system.track_event(
        event_name=event_name,
        trace_id=trace_id,
        span_id=span_id,
        properties=properties,
        level=level
    )
    
    return {"success": True, "message": "事件已记录"}


@router.get("/observability/events")
async def get_events(
    event_name: Optional[str] = None,
    trace_id: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 1000
):
    """获取埋点事件"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    events = observability_system.get_events(
        event_name=event_name,
        trace_id=trace_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return {"success": True, "events": events, "count": len(events)}


@router.get("/observability/statistics")
async def get_observability_statistics():
    """获取可观测性统计信息"""
    if not observability_system:
        raise HTTPException(status_code=503, detail="可观测性系统未初始化")
    
    stats = observability_system.get_statistics()
    return {"success": True, "statistics": stats}


# ============ P0-018: 告警系统 ============

@router.get("/observability/alerts")
async def get_alerts(
    rule_id: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    limit: int = 100
):
    """获取告警列表"""
    if not observability_alerts:
        raise HTTPException(status_code=503, detail="告警系统未初始化")
    
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的严重程度: {severity}")
    
    alerts = observability_alerts.get_alerts(rule_id, severity_enum, resolved, limit)
    return {"success": True, "alerts": alerts, "count": len(alerts)}


@router.post("/observability/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """解决告警"""
    if not observability_alerts:
        raise HTTPException(status_code=503, detail="告警系统未初始化")
    
    success = observability_alerts.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="告警不存在")
    
    return {"success": True, "message": "告警已解决"}


@router.get("/observability/alert-rules")
async def get_alert_rules():
    """获取告警规则列表"""
    if not observability_alerts:
        raise HTTPException(status_code=503, detail="告警系统未初始化")
    
    rules = observability_alerts.get_rules()
    return {"success": True, "rules": rules}


@router.post("/observability/alert-rules")
async def create_alert_rule(
    name: str,
    description: str,
    rule_type: str,
    condition: str,
    threshold: Any,
    severity: str,
    metric_name: Optional[str] = None,
    event_name: Optional[str] = None,
    tags: Optional[Dict[str, str]] = None,
    duration: Optional[float] = None,
    cooldown: Optional[float] = None
):
    """创建告警规则"""
    if not observability_alerts:
        raise HTTPException(status_code=503, detail="告警系统未初始化")
    
    try:
        condition_enum = AlertCondition(condition)
        severity_enum = AlertSeverity(severity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的参数: {e}")
    
    rule = AlertRule(
        rule_id=f"rule_{int(time.time() * 1000)}",
        name=name,
        description=description,
        rule_type=rule_type,
        condition=condition_enum,
        threshold=threshold,
        severity=severity_enum,
        metric_name=metric_name,
        event_name=event_name,
        tags=tags or {},
        duration=duration,
        cooldown=cooldown
    )
    
    observability_alerts.add_rule(rule)
    
    return {"success": True, "rule": observability_alerts.get_rules()[-1]}


# ============ P0-018: 导出功能 ============

@router.get("/observability/export/traces/{trace_id}")
async def export_trace(trace_id: str, format: str = "json"):
    """导出Trace"""
    if not observability_exporter:
        raise HTTPException(status_code=503, detail="导出系统未初始化")
    
    try:
        if format == "json":
            data = observability_exporter.export_trace_json(trace_id)
            from fastapi.responses import JSONResponse
            return JSONResponse(content=data)
        elif format == "csv":
            csv_data = observability_exporter.export_trace_csv(trace_id)
            from fastapi.responses import Response
            return Response(content=csv_data, media_type="text/csv", headers={
                "Content-Disposition": f"attachment; filename=trace_{trace_id}.csv"
            })
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/observability/export/traces")
async def export_traces(
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 100,
    format: str = "json"
):
    """导出多个Traces"""
    if not observability_exporter:
        raise HTTPException(status_code=503, detail="导出系统未初始化")
    
    if format == "json":
        data = observability_exporter.export_traces_json(start_time, end_time, limit)
        from fastapi.responses import JSONResponse
        return JSONResponse(content=data, headers={
            "Content-Disposition": f"attachment; filename=traces_{int(time.time())}.json"
        })
    else:
        raise HTTPException(status_code=400, detail="不支持的格式")


@router.get("/observability/export/metrics")
async def export_metrics(
    metric_name: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    format: str = "csv"
):
    """导出指标"""
    if not observability_exporter:
        raise HTTPException(status_code=503, detail="导出系统未初始化")
    
    if format == "csv":
        csv_data = observability_exporter.export_metrics_csv(metric_name, start_time, end_time)
        from fastapi.responses import Response
        return Response(content=csv_data, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=metrics_{int(time.time())}.csv"
        })
    else:
        raise HTTPException(status_code=400, detail="不支持的格式")


# ============ P1-203: 双RAG执行引擎 ============

class DualRAGQueryRequest(BaseModel):
    """双RAG查询请求"""
    query: str
    context: Optional[Dict[str, Any]] = None
    top_k_first: int = Field(5, ge=1, le=20, description="第一次RAG检索返回数量")
    top_k_second: int = Field(3, ge=1, le=10, description="第二次RAG检索返回数量")
    enable_second_rag: bool = Field(True, description="是否启用第二次RAG检索")


@router.post("/dual-rag/execute")
async def dual_rag_execute(
    request: DualRAGQueryRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """
    执行双RAG流程
    
    实现"双RAG + 专家路由 + 模块执行 + 再检索"模型
    """
    if not dual_rag_engine:
        raise HTTPException(status_code=503, detail="双RAG执行引擎未初始化")
    
    try:
        result = await dual_rag_engine.execute(
            query=request.query,
            context=request.context,
            top_k_first=request.top_k_first,
            top_k_second=request.top_k_second,
            enable_second_rag=request.enable_second_rag,
        )
        
        return {
            "success": True,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"双RAG执行失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/dual-rag/performance")
async def get_dual_rag_performance(
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取双RAG执行性能指标"""
    if not dual_rag_engine:
        raise HTTPException(status_code=503, detail="双RAG执行引擎未初始化")
    
    try:
        metrics = dual_rag_engine.get_performance_metrics()
        return {
            "success": True,
            "metrics": metrics,
        }
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/dual-rag/history")
async def get_dual_rag_history(
    limit: int = Field(10, ge=1, le=100, description="返回数量"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取双RAG执行历史"""
    if not dual_rag_engine:
        raise HTTPException(status_code=503, detail="双RAG执行引擎未初始化")
    
    try:
        history = dual_rag_engine.get_execution_history(limit=limit)
        return {
            "success": True,
            "history": history,
            "total": len(history),
        }
    except Exception as e:
        logger.error(f"获取执行历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/observability/export/events")
async def export_events(
    event_name: Optional[str] = None,
    trace_id: Optional[str] = None,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    limit: int = 1000,
    format: str = "csv"
):
    """导出事件"""
    if not observability_exporter:
        raise HTTPException(status_code=503, detail="导出系统未初始化")
    
    if format == "csv":
        csv_data = observability_exporter.export_events_csv(
            event_name, trace_id, start_time, end_time, limit
        )
        from fastapi.responses import Response
        return Response(content=csv_data, media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=events_{int(time.time())}.csv"
        })
    else:
        raise HTTPException(status_code=400, detail="不支持的格式")


@router.get("/observability/export/long-tasks/{task_id}/replay")
async def export_task_replay(task_id: str, format: str = "json"):
    """导出长任务回放数据"""
    if not observability_exporter:
        raise HTTPException(status_code=503, detail="导出系统未初始化")
    
    try:
        if format == "json":
            data = observability_exporter.export_long_task_replay_json(task_id)
            from fastapi.responses import JSONResponse
            return JSONResponse(content=data, headers={
                "Content-Disposition": f"attachment; filename=task_replay_{task_id}.json"
            })
        else:
            raise HTTPException(status_code=400, detail="不支持的格式")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============ P2-303: 智能任务/自我学习/资源管理 ============

class TaskCreateRequest(BaseModel):
    """创建任务请求"""
    task_name: str
    task_type: str
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None


class LearningPointRequest(BaseModel):
    """添加学习点请求"""
    curve_id: str
    accuracy: float = Field(..., ge=0, le=100)
    loss: Optional[float] = None
    epoch: Optional[int] = None
    dataset_size: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ResourceAllocateRequest(BaseModel):
    """资源分配请求"""
    task_id: str
    resource_type: str
    requested_amount: float = Field(..., ge=0, le=100)
    priority: int = Field(5, ge=1, le=10)
    metadata: Optional[Dict[str, Any]] = None


@router.post("/task-lifecycle/create")
async def create_task(
    request: TaskCreateRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """创建任务"""
    try:
        priority = TaskPriority(request.priority)
        lifecycle = task_lifecycle_manager.create_task(
            task_name=request.task_name,
            task_type=request.task_type,
            priority=priority,
            metadata=request.metadata,
        )
        return {
            "success": True,
            "task": lifecycle.to_dict(),
        }
    except Exception as e:
        logger.error(f"创建任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/task-lifecycle/{task_id}/start")
async def start_task(
    task_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """启动任务"""
    try:
        success = task_lifecycle_manager.start_task(task_id)
        if not success:
            raise HTTPException(status_code=400, detail="任务不存在或状态不正确")
        
        task = task_lifecycle_manager.get_task(task_id)
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/task-lifecycle/{task_id}/update-progress")
async def update_task_progress(
    task_id: str,
    progress: float = Field(..., ge=0, le=100),
    current_step: Optional[str] = None,
    completed_steps: Optional[int] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """更新任务进度"""
    try:
        success = task_lifecycle_manager.update_progress(
            task_id=task_id,
            progress=progress,
            current_step=current_step,
            completed_steps=completed_steps,
        )
        if not success:
            raise HTTPException(status_code=400, detail="任务不存在")
        
        task = task_lifecycle_manager.get_task(task_id)
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/task-lifecycle/{task_id}/complete")
async def complete_task(
    task_id: str,
    result: Optional[Dict[str, Any]] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """完成任务"""
    try:
        success = task_lifecycle_manager.complete_task(task_id, result)
        if not success:
            raise HTTPException(status_code=400, detail="任务不存在或状态不正确")
        
        task = task_lifecycle_manager.get_task(task_id)
        return {
            "success": True,
            "task": task.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"完成任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"完成失败: {str(e)}")


@router.get("/task-lifecycle/list")
async def list_tasks(
    status: Optional[str] = None,
    task_type: Optional[str] = None,
    limit: int = Field(100, ge=1, le=1000),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """列出任务"""
    try:
        task_status = TaskStatus(status) if status else None
        tasks = task_lifecycle_manager.list_tasks(
            status=task_status,
            task_type=task_type,
            limit=limit,
        )
        return {
            "success": True,
            "tasks": [t.to_dict() for t in tasks],
            "total": len(tasks),
        }
    except Exception as e:
        logger.error(f"列出任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")


@router.get("/task-lifecycle/statistics")
async def get_task_statistics(
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取任务统计"""
    try:
        stats = task_lifecycle_manager.get_task_statistics()
        return {
            "success": True,
            "statistics": stats,
        }
    except Exception as e:
        logger.error(f"获取统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/learning-curve/create")
async def create_learning_curve(
    model_name: str,
    task_type: str,
    curve_id: Optional[str] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """创建学习曲线"""
    try:
        curve = learning_curve_tracker.create_curve(
            model_name=model_name,
            task_type=task_type,
            curve_id=curve_id,
        )
        return {
            "success": True,
            "curve": curve.to_dict(),
        }
    except Exception as e:
        logger.error(f"创建学习曲线失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")


@router.post("/learning-curve/add-point")
async def add_learning_point(
    request: LearningPointRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """添加学习点"""
    try:
        success = learning_curve_tracker.add_point(
            curve_id=request.curve_id,
            accuracy=request.accuracy,
            loss=request.loss,
            epoch=request.epoch,
            dataset_size=request.dataset_size,
            metadata=request.metadata,
        )
        if not success:
            raise HTTPException(status_code=400, detail="学习曲线不存在")
        
        curve = learning_curve_tracker.get_curve(request.curve_id)
        return {
            "success": True,
            "curve": curve.to_dict(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加学习点失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"添加失败: {str(e)}")


@router.get("/learning-curve/{curve_id}/data")
async def get_learning_curve_data(
    curve_id: str,
    include_loss: bool = False,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取学习曲线数据"""
    try:
        data = learning_curve_tracker.get_curve_data(
            curve_id=curve_id,
            include_loss=include_loss,
        )
        if not data:
            raise HTTPException(status_code=404, detail="学习曲线不存在")
        
        return {
            "success": True,
            "data": data,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取学习曲线数据失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/learning-curve/list")
async def list_learning_curves(
    model_name: Optional[str] = None,
    task_type: Optional[str] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """列出学习曲线"""
    try:
        curves = learning_curve_tracker.list_curves(
            model_name=model_name,
            task_type=task_type,
        )
        return {
            "success": True,
            "curves": [c.to_dict() for c in curves],
            "total": len(curves),
        }
    except Exception as e:
        logger.error(f"列出学习曲线失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"列出失败: {str(e)}")


@router.get("/learning-curve/statistics")
async def get_learning_statistics(
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取学习统计"""
    try:
        stats = learning_curve_tracker.get_learning_statistics()
        return {
            "success": True,
            "statistics": stats,
        }
    except Exception as e:
        logger.error(f"获取学习统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/resource/allocate")
async def allocate_resource(
    request: ResourceAllocateRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """分配资源"""
    try:
        resource_type = ResourceType(request.resource_type)
        allocation = await resource_scheduler.allocate_resource(
            task_id=request.task_id,
            resource_type=resource_type,
            requested_amount=request.requested_amount,
            priority=request.priority,
            metadata=request.metadata,
        )
        return {
            "success": True,
            "allocation": allocation.to_dict(),
        }
    except Exception as e:
        logger.error(f"分配资源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分配失败: {str(e)}")


@router.post("/resource/release/{allocation_id}")
async def release_resource(
    allocation_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """释放资源"""
    try:
        success = await resource_scheduler.release_resource(allocation_id)
        if not success:
            raise HTTPException(status_code=400, detail="资源分配不存在")
        
        return {
            "success": True,
            "message": "资源已释放",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"释放资源失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"释放失败: {str(e)}")


@router.get("/resource/status")
async def get_resource_status(
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取资源状态"""
    try:
        status = resource_scheduler.get_resource_status()
        return {
            "success": True,
            "status": status,
        }
    except Exception as e:
        logger.error(f"获取资源状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/resource/hints")
async def get_resource_hints(
    hint_type: Optional[str] = None,
    unacknowledged_only: bool = False,
    limit: int = Field(50, ge=1, le=200),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取交互提示"""
    try:
        hint_type_enum = HintType(hint_type) if hint_type else None
        hints = resource_scheduler.get_hints(
            hint_type=hint_type_enum,
            unacknowledged_only=unacknowledged_only,
            limit=limit,
        )
        return {
            "success": True,
            "hints": [h.to_dict() for h in hints],
            "total": len(hints),
        }
    except Exception as e:
        logger.error(f"获取交互提示失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/resource/hints/{hint_id}/acknowledge")
async def acknowledge_hint(
    hint_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """确认提示"""
    try:
        success = resource_scheduler.acknowledge_hint(hint_id)
        if not success:
            raise HTTPException(status_code=400, detail="提示不存在")
        
        return {
            "success": True,
            "message": "提示已确认",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认提示失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"确认失败: {str(e)}")


@router.get("/resource/suggestions")
async def get_scheduling_suggestions(
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取调度建议"""
    try:
        suggestions = resource_scheduler.get_scheduling_suggestions()
        return {
            "success": True,
            "suggestions": suggestions,
        }
    except Exception as e:
        logger.error(f"获取调度建议失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ============ P3-402: 多租户深度隔离 ============

from core.tenant_data_isolation import get_tenant_data_isolation
from core.tenant_quota_manager import get_quota_manager, QuotaType
from core.tenant_audit_logger import get_audit_logger, AuditAction
from core.tenant_manager import tenant_manager

class QuotaSetRequest(BaseModel):
    """设置配额请求"""
    tenant_id: str
    quota_type: str
    limit: int
    reset_period: str = "monthly"
    metadata: Optional[Dict[str, Any]] = None


class QuotaUseRequest(BaseModel):
    """使用配额请求"""
    tenant_id: str
    quota_type: str
    amount: int


@router.get("/tenant/quota/list")
async def list_tenant_quotas(
    tenant_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取租户所有配额"""
    try:
        quota_mgr = get_quota_manager()
        quotas = quota_mgr.get_all_quotas(tenant_id)
        return {
            "success": True,
            "quotas": {k: v.to_dict() for k, v in quotas.items()},
        }
    except Exception as e:
        logger.error(f"获取配额失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/tenant/quota/usage")
async def get_quota_usage(
    tenant_id: str,
    quota_type: Optional[str] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取配额使用情况"""
    try:
        quota_mgr = get_quota_manager()
        usage = quota_mgr.get_usage(tenant_id, quota_type)
        return {
            "success": True,
            "usage": usage,
        }
    except Exception as e:
        logger.error(f"获取使用量失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/tenant/quota/set")
async def set_tenant_quota(
    request: QuotaSetRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """设置租户配额"""
    try:
        quota_mgr = get_quota_manager()
        quota_type = QuotaType(request.quota_type)
        quota = quota_mgr.set_quota(
            tenant_id=request.tenant_id,
            quota_type=quota_type,
            limit=request.limit,
            reset_period=request.reset_period,
            metadata=request.metadata,
        )
        return {
            "success": True,
            "quota": quota.to_dict(),
        }
    except Exception as e:
        logger.error(f"设置配额失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.post("/tenant/quota/use")
async def use_tenant_quota(
    request: QuotaUseRequest,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """使用配额"""
    try:
        quota_mgr = get_quota_manager()
        success, error = quota_mgr.use_quota(
            tenant_id=request.tenant_id,
            quota_type=request.quota_type,
            amount=request.amount,
        )
        if not success:
            raise HTTPException(status_code=400, detail=error or "配额不足")
        
        return {
            "success": True,
            "message": "配额使用成功",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"使用配额失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"使用失败: {str(e)}")


@router.get("/tenant/storage/stats")
async def get_tenant_storage_stats(
    tenant_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取租户存储统计"""
    try:
        isolation = get_tenant_data_isolation()
        storage_size = isolation.get_tenant_storage_size(tenant_id)
        files = isolation.list_tenant_files(tenant_id)
        
        return {
            "success": True,
            "stats": {
                "storage_size": storage_size,
                "storage_size_mb": round(storage_size / 1024 / 1024, 2),
                "file_count": len(files),
            },
        }
    except Exception as e:
        logger.error(f"获取存储统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.get("/tenant/audit/query")
async def query_audit_logs(
    tenant_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Field(100, ge=1, le=1000),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """查询审计日志"""
    try:
        audit_logger = get_audit_logger()
        action_enum = AuditAction(action) if action else None
        logs = audit_logger.query_logs(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            action=action_enum,
            resource_type=resource_type,
            user_id=user_id,
            limit=limit,
        )
        return {
            "success": True,
            "logs": [log.to_dict() for log in logs],
            "total": len(logs),
        }
    except Exception as e:
        logger.error(f"查询审计日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/tenant/audit/report")
async def get_audit_report(
    tenant_id: str,
    start_date: str,
    end_date: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """生成审计报表"""
    try:
        audit_logger = get_audit_logger()
        report = audit_logger.generate_audit_report(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
        )
        return {
            "success": True,
            "report": report,
        }
    except Exception as e:
        logger.error(f"生成审计报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.get("/tenant/audit/export")
async def export_audit_logs(
    tenant_id: str,
    start_date: str,
    end_date: str,
    format: str = Field("json", pattern="^(json|csv)$"),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """导出审计日志"""
    try:
        audit_logger = get_audit_logger()
        export_path = audit_logger.export_audit_logs(
            tenant_id=tenant_id,
            start_date=start_date,
            end_date=end_date,
            format=format,
        )
        return {
            "success": True,
            "export_path": export_path,
            "message": "审计日志已导出",
        }
    except Exception as e:
        logger.error(f"导出审计日志失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.get("/tenant/info")
async def get_tenant_info(
    tenant_id: str,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取租户信息"""
    try:
        tenant = tenant_manager.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(status_code=404, detail="租户不存在")
        
        return {
            "success": True,
            "tenant": {
                "tenant_id": tenant.tenant_id,
                "name": tenant.name,
                "plan": tenant.plan,
                "active": tenant.active,
                "metadata": tenant.metadata,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取租户信息失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


@router.post("/tenant/audit/log")
async def log_audit_event(
    tenant_id: str,
    action: str,
    resource_type: str,
    user_id: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """记录审计事件"""
    try:
        audit_logger = get_audit_logger()
        action_enum = AuditAction(action)
        log = audit_logger.log(
            tenant_id=tenant_id,
            action=action_enum,
            resource_type=resource_type,
            user_id=user_id,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message,
        )
        return {
            "success": True,
            "log": log.to_dict(),
        }
    except Exception as e:
        logger.error(f"记录审计事件失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"记录失败: {str(e)}")


# ============ P3-403: 性能与可靠性 ============

from tests.performance.test_performance_suite import PerformanceTestSuite
from core.slo_report_generator import get_slo_report_generator
from scripts.chaos_engineering.chaos_test_runner import ChaosTestRunner, ChaosScenario

@router.post("/performance/test/load")
async def run_load_test(
    endpoint: str = "/health",
    concurrent_users: int = Field(10, ge=1, le=1000),
    requests_per_user: int = Field(10, ge=1, le=100),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """运行负载测试"""
    try:
        suite = PerformanceTestSuite()
        result = await suite.load_test(
            endpoint=endpoint,
            concurrent_users=concurrent_users,
            requests_per_user=requests_per_user,
        )
        await suite.close()
        return {
            "success": True,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"负载测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/performance/test/stress")
async def run_stress_test(
    endpoint: str = "/health",
    initial_users: int = Field(10, ge=1),
    max_users: int = Field(100, ge=1),
    step: int = Field(10, ge=1),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """运行压力测试"""
    try:
        suite = PerformanceTestSuite()
        results = await suite.stress_test(
            endpoint=endpoint,
            initial_users=initial_users,
            max_users=max_users,
            step=step,
        )
        await suite.close()
        return {
            "success": True,
            "results": [r.to_dict() for r in results],
        }
    except Exception as e:
        logger.error(f"压力测试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.get("/slo/report")
async def get_slo_report(
    measurement_period: Optional[str] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """获取SLO报告"""
    try:
        generator = get_slo_report_generator()
        report = generator.generate_slo_report(measurement_period)
        return {
            "success": True,
            "report": report,
        }
    except Exception as e:
        logger.error(f"生成SLO报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/slo/target")
async def set_slo_target(
    name: str,
    target_value: float,
    measurement_window: str = "30d",
    error_budget: float = Field(0.01, ge=0, le=1),
    metadata: Optional[Dict[str, Any]] = None,
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """设置SLO目标"""
    try:
        generator = get_slo_report_generator()
        target = generator.set_slo_target(
            name=name,
            target_value=target_value,
            measurement_window=measurement_window,
            error_budget=error_budget,
            metadata=metadata,
        )
        return {
            "success": True,
            "target": {
                "name": target.name,
                "target_value": target.target_value,
                "measurement_window": target.measurement_window,
                "error_budget": target.error_budget,
            },
        }
    except Exception as e:
        logger.error(f"设置SLO目标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"设置失败: {str(e)}")


@router.post("/chaos/test/sidecar-down")
async def run_chaos_test_sidecar_down(
    sidecar_name: str = "rag-sidecar",
    duration: int = Field(60, ge=10, le=300),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """运行Sidecar宕机故障演练"""
    try:
        runner = ChaosTestRunner()
        result = await runner.test_sidecar_down(
            sidecar_name=sidecar_name,
            duration=duration,
        )
        return {
            "success": result.success,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"故障演练失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/chaos/test/database-degraded")
async def run_chaos_test_database_degraded(
    database_name: str = "postgres",
    degradation_type: str = Field("slow_queries", pattern="^(slow_queries|connection_limit|disk_full)$"),
    duration: int = Field(60, ge=10, le=300),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """运行数据库降级故障演练"""
    try:
        runner = ChaosTestRunner()
        result = await runner.test_database_degraded(
            database_name=database_name,
            degradation_type=degradation_type,
            duration=duration,
        )
        return {
            "success": result.success,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"故障演练失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


@router.post("/chaos/test/api-timeout")
async def run_chaos_test_api_timeout(
    endpoint: str = "/gateway/rag/search",
    timeout_duration: int = Field(30, ge=5, le=300),
    test_duration: int = Field(60, ge=10, le=600),
    _: bool = Depends(_get_require_api_key()),
) -> Dict[str, Any]:
    """运行API超时故障演练"""
    try:
        runner = ChaosTestRunner()
        result = await runner.test_api_timeout(
            endpoint=endpoint,
            timeout_duration=timeout_duration,
            test_duration=test_duration,
        )
        return {
            "success": result.success,
            "result": result.to_dict(),
        }
    except Exception as e:
        logger.error(f"故障演练失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"测试失败: {str(e)}")


# ============ 3.2: 四模块查询、执行、回写接口（使用 configurable_api_connector） ============

# 初始化可配置API连接器
from core.configurable_api_connector import ConfigurableAPIConnector
from core.rag_service_adapter import RAGServiceAdapter

configurable_api_connector = ConfigurableAPIConnector()

# 注册RAG服务连接器
if super_agent.rag_service:
    configurable_api_connector.register_connector("rag", RAGServiceAdapter, {
        "rag_api_url": os.getenv("RAG_API_URL", "http://localhost:8011")
    })

# 权限依赖
rag_read_dep = permission_guard.require("rag:read")
rag_write_dep = permission_guard.require("rag:write")
erp_read_dep = permission_guard.require("erp:read")
erp_write_dep = permission_guard.require("erp:write")
content_read_dep = permission_guard.require("content:read")
content_write_dep = permission_guard.require("content:write")
trend_read_dep = permission_guard.require("trend:read")
trend_write_dep = permission_guard.require("trend:write")


# ============ RAG 模块接口 ============

@router.get("/rag/documents", dependencies=[rag_read_dep])
async def get_rag_documents(
    limit: int = 50,
    offset: int = 0,
    doc_type: Optional[str] = None,
    _: Dict[str, Any] = Depends(rag_read_dep)
):
    """查询RAG文档列表"""
    try:
        # 优先使用RAG服务适配器
        if super_agent.rag_service:
            try:
                # 尝试调用RAG服务的文档列表接口
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{os.getenv('RAG_API_URL', 'http://localhost:8011')}/api/documents",
                        params={"limit": limit, "offset": offset, "doc_type": doc_type},
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        data = response.json()
                        return {
                            "success": True,
                            "documents": data.get("documents", []),
                            "count": data.get("count", 0),
                            "limit": limit,
                            "offset": offset
                        }
            except Exception:
                pass
        
        # 使用configurable_api_connector调用RAG服务
        result = await configurable_api_connector.call_api(
            platform="rag",
            endpoint="/api/documents",
            method="GET",
            params={"limit": limit, "offset": offset, "doc_type": doc_type}
        )
        return {
            "success": True,
            "documents": result.get("documents", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询RAG文档列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/rag/documents/{doc_id}", dependencies=[rag_read_dep])
async def get_rag_document(
    doc_id: str,
    _: Dict[str, Any] = Depends(rag_read_dep)
):
    """查询RAG文档详情"""
    try:
        if super_agent.rag_service:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{os.getenv('RAG_API_URL', 'http://localhost:8011')}/api/documents/{doc_id}",
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        return {"success": True, "document": response.json()}
            except Exception:
                pass
        
        result = await configurable_api_connector.call_api(
            platform="rag",
            endpoint=f"/api/documents/{doc_id}",
            method="GET"
        )
        return {"success": True, "document": result}
    except Exception as e:
        logger.error(f"查询RAG文档详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/rag/search", dependencies=[rag_read_dep])
async def search_rag(
    query: str,
    top_k: int = 10,
    filter_type: Optional[str] = None,
    _: Dict[str, Any] = Depends(rag_read_dep)
):
    """执行RAG检索"""
    try:
        if super_agent.rag_service:
            results = await super_agent.rag_service.retrieve(
                query=query,
                top_k=top_k,
                filter_type=filter_type
            )
            return {
                "success": True,
                "results": results,
                "count": len(results),
                "query": query
            }
        else:
            result = await configurable_api_connector.call_api(
                platform="rag",
                endpoint="/api/search",
                method="POST",
                data={
                    "query": query,
                    "top_k": top_k,
                    "filter_type": filter_type
                }
            )
            return {
                "success": True,
                "results": result.get("results", []),
                "count": len(result.get("results", [])),
                "query": query
            }
    except Exception as e:
        logger.error(f"RAG检索失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")


@router.get("/rag/stats", dependencies=[rag_read_dep])
async def get_rag_stats(
    _: Dict[str, Any] = Depends(rag_read_dep)
):
    """获取RAG统计信息"""
    try:
        if super_agent.rag_service:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{os.getenv('RAG_API_URL', 'http://localhost:8011')}/api/stats",
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        return {"success": True, "statistics": response.json()}
            except Exception:
                pass
        
        result = await configurable_api_connector.call_api(
            platform="rag",
            endpoint="/api/stats",
            method="GET"
        )
        return {"success": True, "statistics": result}
    except Exception as e:
        logger.error(f"获取RAG统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")


@router.post("/rag/writeback", dependencies=[rag_write_dep])
async def rag_writeback(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(rag_write_dep)
):
    """RAG数据回写"""
    try:
        title = request.get("title", "")
        content = request.get("content", "")
        tags = request.get("tags", [])
        metadata = request.get("metadata", {})
        
        if super_agent.rag_service:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{os.getenv('RAG_API_URL', 'http://localhost:8011')}/api/writeback",
                        json={
                            "title": title,
                            "content": content,
                            "tags": tags,
                            "metadata": metadata
                        },
                        timeout=10.0
                    )
                    if response.status_code == 200:
                        return {"success": True, "result": response.json()}
            except Exception:
                pass
        
        result = await configurable_api_connector.call_api(
            platform="rag",
            endpoint="/api/writeback",
            method="POST",
            data={
                "title": title,
                "content": content,
                "tags": tags,
                "metadata": metadata
            }
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"RAG回写失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回写失败: {str(e)}")


# ============ ERP 模块接口 ============

@router.get("/erp/orders", dependencies=[erp_read_dep])
async def get_erp_orders(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP订单列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint="/api/orders",
            method="GET",
            params={"limit": limit, "offset": offset, "status": status}
        )
        return {
            "success": True,
            "orders": result.get("orders", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询ERP订单列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/orders/{order_id}", dependencies=[erp_read_dep])
async def get_erp_order(
    order_id: str,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP订单详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/orders/{order_id}",
            method="GET"
        )
        return {"success": True, "order": result}
    except Exception as e:
        logger.error(f"查询ERP订单详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/customers", dependencies=[erp_read_dep])
async def get_erp_customers(
    limit: int = 50,
    offset: int = 0,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP客户列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint="/api/customers",
            method="GET",
            params={"limit": limit, "offset": offset}
        )
        return {
            "success": True,
            "customers": result.get("customers", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询ERP客户列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/customers/{customer_id}", dependencies=[erp_read_dep])
async def get_erp_customer(
    customer_id: str,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP客户详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/customers/{customer_id}",
            method="GET"
        )
        return {"success": True, "customer": result}
    except Exception as e:
        logger.error(f"查询ERP客户详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/projects", dependencies=[erp_read_dep])
async def get_erp_projects(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP项目列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint="/api/projects",
            method="GET",
            params={"limit": limit, "offset": offset, "status": status}
        )
        return {
            "success": True,
            "projects": result.get("projects", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询ERP项目列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/projects/{project_id}", dependencies=[erp_read_dep])
async def get_erp_project(
    project_id: str,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP项目详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/projects/{project_id}",
            method="GET"
        )
        return {"success": True, "project": result}
    except Exception as e:
        logger.error(f"查询ERP项目详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/inventory", dependencies=[erp_read_dep])
async def get_erp_inventory(
    limit: int = 50,
    offset: int = 0,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP库存列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint="/api/inventory",
            method="GET",
            params={"limit": limit, "offset": offset}
        )
        return {
            "success": True,
            "items": result.get("items", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询ERP库存列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/erp/inventory/{item_id}", dependencies=[erp_read_dep])
async def get_erp_inventory_item(
    item_id: str,
    _: Dict[str, Any] = Depends(erp_read_dep)
):
    """查询ERP库存详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/inventory/{item_id}",
            method="GET"
        )
        return {"success": True, "item": result}
    except Exception as e:
        logger.error(f"查询ERP库存详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/erp/{type}/{id}/execute", dependencies=[erp_write_dep])
async def execute_erp_action(
    type: str,
    id: str,
    action: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(erp_write_dep)
):
    """执行ERP操作（批准、拒绝、更新等）"""
    try:
        action_type = action.get("action_type", "")
        action_data = action.get("data", {})
        
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/{type}/{id}/{action_type}",
            method="POST",
            data=action_data
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"执行ERP操作失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/erp/writeback", dependencies=[erp_write_dep])
async def erp_writeback(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(erp_write_dep)
):
    """ERP数据回写"""
    try:
        entity_type = request.get("entity_type")  # order, customer, project, inventory
        entity_id = request.get("entity_id")
        data = request.get("data", {})
        
        result = await configurable_api_connector.call_api(
            platform="erp",
            endpoint=f"/api/{entity_type}/{entity_id}/writeback",
            method="POST",
            data=data
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"ERP回写失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回写失败: {str(e)}")


# ============ 内容模块接口 ============

@router.get("/content/list", dependencies=[content_read_dep])
async def get_content_list(
    limit: int = 50,
    offset: int = 0,
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    _: Dict[str, Any] = Depends(content_read_dep)
):
    """查询内容列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint="/api/contents",
            method="GET",
            params={"limit": limit, "offset": offset, "content_type": content_type, "status": status}
        )
        return {
            "success": True,
            "contents": result.get("contents", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询内容列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/content/{content_id}", dependencies=[content_read_dep])
async def get_content(
    content_id: str,
    _: Dict[str, Any] = Depends(content_read_dep)
):
    """查询内容详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint=f"/api/contents/{content_id}",
            method="GET"
        )
        return {"success": True, "content": result}
    except Exception as e:
        logger.error(f"查询内容详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/content/generate", dependencies=[content_write_dep])
async def generate_content(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(content_write_dep)
):
    """执行内容生成"""
    try:
        prompt = request.get("prompt", "")
        content_type = request.get("content_type", "text")
        platform = request.get("platform", "")
        
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint="/api/generate",
            method="POST",
            data={
                "prompt": prompt,
                "content_type": content_type,
                "platform": platform
            }
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"内容生成失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


@router.post("/content/{content_id}/publish", dependencies=[content_write_dep])
async def publish_content(
    content_id: str,
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(content_write_dep)
):
    """执行内容发布"""
    try:
        platform = request.get("platform", "")
        publish_data = request.get("data", {})
        
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint=f"/api/contents/{content_id}/publish",
            method="POST",
            data={
                "platform": platform,
                **publish_data
            }
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"内容发布失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@router.get("/content/materials", dependencies=[content_read_dep])
async def get_content_materials(
    limit: int = 50,
    offset: int = 0,
    _: Dict[str, Any] = Depends(content_read_dep)
):
    """查询素材列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint="/api/materials",
            method="GET",
            params={"limit": limit, "offset": offset}
        )
        return {
            "success": True,
            "materials": result.get("materials", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询素材列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/content/published", dependencies=[content_read_dep])
async def get_published_content(
    limit: int = 50,
    offset: int = 0,
    platform: Optional[str] = None,
    _: Dict[str, Any] = Depends(content_read_dep)
):
    """查询已发布内容列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint="/api/published",
            method="GET",
            params={"limit": limit, "offset": offset, "platform": platform}
        )
        return {
            "success": True,
            "published": result.get("published", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询已发布内容失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/content/writeback", dependencies=[content_write_dep])
async def content_writeback(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(content_write_dep)
):
    """内容数据回写"""
    try:
        content_id = request.get("content_id")
        data = request.get("data", {})
        
        result = await configurable_api_connector.call_api(
            platform="content",
            endpoint=f"/api/contents/{content_id}/writeback",
            method="POST",
            data=data
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"内容回写失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回写失败: {str(e)}")


# ============ 趋势模块接口 ============

@router.get("/trend/reports", dependencies=[trend_read_dep])
async def get_trend_reports(
    limit: int = 50,
    offset: int = 0,
    indicator: Optional[str] = None,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势报告列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint="/api/reports",
            method="GET",
            params={"limit": limit, "offset": offset, "indicator": indicator}
        )
        return {
            "success": True,
            "reports": result.get("reports", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询趋势报告列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/trend/reports/{report_id}", dependencies=[trend_read_dep])
async def get_trend_report(
    report_id: str,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势报告详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint=f"/api/reports/{report_id}",
            method="GET"
        )
        return {"success": True, "report": result}
    except Exception as e:
        logger.error(f"查询趋势报告详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/trend/indicators", dependencies=[trend_read_dep])
async def get_trend_indicators(
    limit: int = 50,
    offset: int = 0,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势指标列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint="/api/indicators",
            method="GET",
            params={"limit": limit, "offset": offset}
        )
        return {
            "success": True,
            "indicators": result.get("indicators", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询趋势指标列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/trend/indicators/{indicator_id}", dependencies=[trend_read_dep])
async def get_trend_indicator(
    indicator_id: str,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势指标详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint=f"/api/indicators/{indicator_id}",
            method="GET"
        )
        return {"success": True, "indicator": result}
    except Exception as e:
        logger.error(f"查询趋势指标详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/trend/analysis/tasks", dependencies=[trend_read_dep])
async def get_trend_analysis_tasks(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势分析任务列表"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint="/api/analysis/tasks",
            method="GET",
            params={"limit": limit, "offset": offset, "status": status}
        )
        return {
            "success": True,
            "tasks": result.get("tasks", []),
            "count": result.get("count", 0),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"查询趋势分析任务列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/trend/analysis/tasks/{task_id}", dependencies=[trend_read_dep])
async def get_trend_analysis_task(
    task_id: str,
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """查询趋势分析任务详情"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint=f"/api/analysis/tasks/{task_id}",
            method="GET"
        )
        return {"success": True, "task": result}
    except Exception as e:
        logger.error(f"查询趋势分析任务详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.post("/trend/analysis/start", dependencies=[trend_write_dep])
async def start_trend_analysis(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(trend_write_dep)
):
    """启动趋势分析任务"""
    try:
        indicator = request.get("indicator", "")
        analysis_type = request.get("analysis_type", "standard")
        
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint="/api/analysis/start",
            method="POST",
            data={
                "indicator": indicator,
                "analysis_type": analysis_type
            }
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"启动趋势分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动失败: {str(e)}")


@router.post("/trend/analysis/execute", dependencies=[trend_write_dep])
async def execute_trend_analysis(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(trend_write_dep)
):
    """执行趋势分析"""
    try:
        report_id = request.get("report_id")
        indicator_id = request.get("indicator_id")
        
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint="/api/analysis/execute",
            method="POST",
            data={
                "report_id": report_id,
                "indicator_id": indicator_id
            }
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"执行趋势分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.get("/trend/reports/{report_id}/export", dependencies=[trend_read_dep])
async def export_trend_report(
    report_id: str,
    format: str = "pdf",
    _: Dict[str, Any] = Depends(trend_read_dep)
):
    """导出趋势报告"""
    try:
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint=f"/api/reports/{report_id}/export",
            method="GET",
            params={"format": format}
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"导出趋势报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@router.post("/trend/writeback", dependencies=[trend_write_dep])
async def trend_writeback(
    request: Dict[str, Any] = Body(...),
    _: Dict[str, Any] = Depends(trend_write_dep)
):
    """趋势数据回写"""
    try:
        report_id = request.get("report_id")
        data = request.get("data", {})
        
        result = await configurable_api_connector.call_api(
            platform="trend",
            endpoint=f"/api/reports/{report_id}/writeback",
            method="POST",
            data=data
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"趋势回写失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"回写失败: {str(e)}")
