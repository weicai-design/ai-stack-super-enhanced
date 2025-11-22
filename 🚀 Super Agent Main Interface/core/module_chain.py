#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module Chain Manager

P0-104: 记录主界面 → 二级 → 三级/四级真实链路，串联 API 与数据层。
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .data_service import DataService
from .service_registry import ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass
class ModuleChain:
    module_id: str
    module_name: str
    hierarchy: Dict[str, str]
    apis: List[Dict[str, str]]
    data_sources: List[Dict[str, Any]]
    sidecars: List[Dict[str, Any]]
    verification: Dict[str, Any]
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModuleChainManager:
    """维护主界面到数据层的链路信息，并提供校验指标。"""

    def __init__(
        self,
        data_service: DataService,
        service_registry: ServiceRegistry,
        rag_store_path: Optional[Path] = None,
        trial_data_source: Any = None,
        factory_data_source: Any = None,
        trend_data_collector: Any = None,
        content_analytics: Any = None,
        stock_gateway: Any = None,
        cursor_bridge: Any = None,
    ):
        self.data_service = data_service
        self.service_registry = service_registry
        self.rag_store_path = rag_store_path
        self.trial_data_source = trial_data_source
        self.factory_data_source = factory_data_source
        self.trend_data_collector = trend_data_collector
        self.content_analytics = content_analytics
        self.stock_gateway = stock_gateway
        self.cursor_bridge = cursor_bridge

        self._chains: List[ModuleChain] = []
        self._lock = asyncio.Lock()

    async def list_chains(self, refresh: bool = False) -> List[Dict[str, Any]]:
        async with self._lock:
            if refresh or not self._chains:
                await self._refresh_locked()
            return [chain.to_dict() for chain in self._chains]

    async def get_chain(self, module_id: str) -> Dict[str, Any]:
        chains = await self.list_chains()
        for chain in chains:
            if chain["module_id"] == module_id:
                return chain
        raise KeyError(module_id)

    async def refresh(self) -> List[Dict[str, Any]]:
        async with self._lock:
            await self._refresh_locked()
            return [chain.to_dict() for chain in self._chains]

    async def _refresh_locked(self) -> None:
        chains: List[ModuleChain] = []
        chains.append(await self._build_rag_chain())
        chains.append(await self._build_erp_chain())
        chains.append(await self._build_content_chain())
        chains.append(await self._build_trend_chain())
        chains.append(await self._build_stock_chain())
        chains.append(await self._build_operations_chain())
        chains.append(await self._build_coding_chain())

        self._chains = chains

    async def _build_rag_chain(self) -> ModuleChain:
        data_records = await self._safe_count("rag")
        rag_search_contract = self.service_registry.get_contract("rag_hub", "search")
        rag_experience_contract = self.service_registry.get_contract("rag_hub", "experience")
        rag_file_path = str(self.rag_store_path) if self.rag_store_path else None
        rag_file_exists = bool(self.rag_store_path and self.rag_store_path.exists())

        return self._chain(
            module_id="rag",
            module_name="RAG知识中心",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='rag']",
                "secondary_route": "three_level.html?module=rag",
                "tertiary_view": "preprocess → ingest_status",
                "quaternary_capability": "upload_document (四级能力)",
            },
            apis=[
                {"method": "POST", "path": "/rag/pipeline/ingest", "description": "接入与预处理"},
                {"method": "GET", "path": "/rag/pipeline/documents", "description": "列出入库文档"},
                {"method": "GET", "path": "/modules/view-data?module=rag&stage=preprocess&view=ingest_status", "description": "三级视图数据"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("rag"),
                    "records": data_records,
                },
                {
                    "type": "file",
                    "resource": rag_file_path,
                    "exists": rag_file_exists,
                },
            ],
            sidecars=[
                {"service": "rag_hub", "operation": "search", "contract": bool(rag_search_contract)},
                {"service": "rag_hub", "operation": "experience", "contract": bool(rag_experience_contract)},
            ],
            verification={
                "data_records": data_records,
                "rag_file_exists": rag_file_exists,
                "service_contracts": {
                    "rag_hub.search": bool(rag_search_contract),
                    "rag_hub.experience": bool(rag_experience_contract),
                },
            },
        )

    async def _build_erp_chain(self) -> ModuleChain:
        erp_records = await self._safe_count("erp")
        return self._chain(
            module_id="erp",
            module_name="ERP流程中心",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='erp']",
                "secondary_route": "three_level.html?module=erp",
                "tertiary_view": "operations → operations_board",
                "quaternary_capability": "strategy_links (四级策略)",
            },
            apis=[
                {"method": "POST", "path": "/erp/trial/calc", "description": "运营试算器"},
                {"method": "POST", "path": "/erp/8d/analyze", "description": "8D 分析"},
                {"method": "GET", "path": "/operations-finance/erp/sync/status", "description": "ERP 数据同步状态"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("erp"),
                    "records": erp_records,
                },
                {
                    "type": "datasource",
                    "resource": "DemoFactoryTrialDataSource",
                    "available": self.trial_data_source is not None,
                },
                {
                    "type": "datasource",
                    "resource": "FactoryDataSource",
                    "available": self.factory_data_source is not None,
                },
            ],
            sidecars=[],
            verification={
                "data_records": erp_records,
                "trial_data_source": bool(self.trial_data_source),
                "factory_data_source": bool(self.factory_data_source),
            },
        )

    async def _build_content_chain(self) -> ModuleChain:
        content_records = await self._safe_count("content")
        publication_records = len(getattr(self.content_analytics, "content_records", {})) if self.content_analytics else 0
        return self._chain(
            module_id="content",
            module_name="内容创作系统",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='content']",
                "secondary_route": "three_level.html?module=content",
                "tertiary_view": "generation → content_generation",
                "quaternary_capability": "content_generation -> storyline 模板",
            },
            apis=[
                {"method": "POST", "path": "/douyin/publish", "description": "抖音真实发布"},
                {"method": "POST", "path": "/content/storyboard/generate", "description": "脚本/分镜生成"},
                {"method": "GET", "path": "/content/analytics", "description": "运营表现分析"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("content"),
                    "records": content_records,
                },
                {
                    "type": "analytics",
                    "resource": "ContentAnalytics",
                    "records": publication_records,
                },
            ],
            sidecars=[],
            verification={
                "data_records": content_records,
                "analytics_records": publication_records,
            },
        )

    async def _build_trend_chain(self) -> ModuleChain:
        trend_records = await self._safe_count("trend")
        collection_stats = self.trend_data_collector.get_collection_stats(days=7) if self.trend_data_collector else {}
        sources = len(collection_stats.get("source_summary", {}))
        trend_contract = self.service_registry.get_contract("trend_ops", "backtest")

        return self._chain(
            module_id="trend",
            module_name="趋势分析",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='trend']",
                "secondary_route": "three_level.html?module=trend",
                "tertiary_view": "analysis → trend_insights",
                "quaternary_capability": "trend_insights -> trend_rag_output",
            },
            apis=[
                {"method": "GET", "path": "/trend/backtest", "description": "回测与RAG链路"},
                {"method": "POST", "path": "/trend/what-if", "description": "What-if 情景模拟"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("trend"),
                    "records": trend_records,
                },
                {
                    "type": "collector",
                    "resource": "TrendDataCollector",
                    "recent_sources": sources,
                },
            ],
            sidecars=[
                {"service": "trend_ops", "operation": "backtest", "contract": bool(trend_contract)},
            ],
            verification={
                "data_records": trend_records,
                "collector_sources": sources,
                "service_contracts": {"trend_ops.backtest": bool(trend_contract)},
            },
        )

    async def _build_stock_chain(self) -> ModuleChain:
        stock_records = await self._safe_count("stock")
        gateway_sources = self.stock_gateway.list_sources() if self.stock_gateway else {}
        active_source = gateway_sources.get("active")
        return self._chain(
            module_id="stock",
            module_name="股票量化",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='stock']",
                "secondary_route": "three_level.html?module=stock",
                "tertiary_view": "trading → stock_simulator",
                "quaternary_capability": "stock_simulator -> risk_control",
            },
            apis=[
                {"method": "GET", "path": "/stock/quote", "description": "实时行情（多源热切换）"},
                {"method": "POST", "path": "/stock/sim/place-order", "description": "模拟盘下单"},
                {"method": "GET", "path": "/stock/sim/risk-report", "description": "模拟盘风控"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("stock"),
                    "records": stock_records,
                },
                {
                    "type": "gateway",
                    "resource": "StockGateway",
                    "active_source": active_source,
                    "sources": gateway_sources,
                },
            ],
            sidecars=[],
            verification={
                "data_records": stock_records,
                "active_source": active_source,
            },
        )

    async def _build_operations_chain(self) -> ModuleChain:
        operations_records = await self._safe_count("operations")
        return self._chain(
            module_id="operations",
            module_name="运营财务",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='operations']",
                "secondary_route": "three_level.html?module=operations",
                "tertiary_view": "operations → operations_board",
                "quaternary_capability": "strategy_links -> cross_system_sync",
            },
            apis=[
                {"method": "GET", "path": "/operations-finance/kpis", "description": "运营财务KPI"},
                {"method": "GET", "path": "/operations-finance/insights", "description": "专家洞察"},
                {"method": "POST", "path": "/operations-finance/erp/sync", "description": "ERP数据回写"},
            ],
            data_sources=[
                {
                    "type": "database",
                    "resource": self.data_service.get_table_name("operations"),
                    "records": operations_records,
                },
            ],
            sidecars=[],
            verification={
                "data_records": operations_records,
            },
        )

    async def _build_coding_chain(self) -> ModuleChain:
        cursor_status = self.cursor_bridge.get_status() if self.cursor_bridge else {"available": False}
        return self._chain(
            module_id="coding",
            module_name="AI 编程助手",
            hierarchy={
                "primary_card": "sidebar.nav-btn[data-module='coding']",
                "secondary_route": "three_level.html?module=coding",
                "tertiary_view": "generation → coding_generation",
                "quaternary_capability": "coding_generation -> cursor_bridge",
            },
            apis=[
                {"method": "GET", "path": "/coding/cursor/status", "description": "Cursor 桥接状态"},
                {"method": "POST", "path": "/coding/cursor/open-file", "description": "打开文件到 Cursor"},
                {"method": "POST", "path": "/coding/cursor/apply-edits", "description": "推送编辑 diff"},
            ],
            data_sources=[
                {
                    "type": "bridge",
                    "resource": "CursorBridge",
                    "status": cursor_status,
                },
            ],
            sidecars=[],
            verification={
                "cursor_available": cursor_status.get("available", False),
                "cursor_path": cursor_status.get("path"),
            },
        )

    async def _safe_count(self, module: str) -> int:
        try:
            return await self.data_service.count_data(module)
        except Exception as exc:  # pragma: no cover - 统计失败时返回0
            logger.warning("Count data failed for module %s: %s", module, exc)
            return 0

    def _chain(
        self,
        module_id: str,
        module_name: str,
        hierarchy: Dict[str, str],
        apis: List[Dict[str, str]],
        data_sources: List[Dict[str, Any]],
        sidecars: List[Dict[str, Any]],
        verification: Dict[str, Any],
    ) -> ModuleChain:
        return ModuleChain(
            module_id=module_id,
            module_name=module_name,
            hierarchy=hierarchy,
            apis=apis,
            data_sources=data_sources,
            sidecars=sidecars,
            verification={**verification, "last_checked": self._now()},
            updated_at=self._now(),
        )

    def _now(self) -> str:
        return datetime.utcnow().isoformat() + "Z"



