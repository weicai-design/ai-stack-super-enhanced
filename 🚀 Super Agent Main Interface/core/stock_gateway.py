"""
股票数据源网关（可插拔，支持热切换）
目标：抽象不同行情源（同花顺/聚宽/自建等），提供统一查询接口
"""
from __future__ import annotations

import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional


class BaseStockSource:
    name: str = "base"
    label: str = "Base"
    vendor: str = "internal"
    env_required: List[str] = []
    env_optional: List[str] = []
    latency_ms: int = 800

    def __init__(self):
        self.ready: bool = self._check_ready()
        self.last_success: Optional[str] = None
        self.last_error: Optional[str] = None

    def _check_ready(self) -> bool:
        if not self.env_required:
            return True
        return all(os.environ.get(k) for k in self.env_required)

    def metadata(self) -> Dict[str, Any]:
        return {
            "id": self.name,
            "label": self.label,
            "vendor": self.vendor,
            "latency_ms": self.latency_ms,
            "ready": self.ready,
            "env_required": self.env_required,
            "env_optional": self.env_optional,
            "last_success": self.last_success,
            "last_error": self.last_error,
        }

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        raise NotImplementedError


class MockSource(BaseStockSource):
    name = "mock"
    label = "内置模拟源"
    vendor = "Built-in"
    latency_ms = 120

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        price = round(10 + random.random() * 20, 2)
        bid = round(price - 0.02, 2)
        ask = round(price + 0.02, 2)
        return {
            "symbol": symbol,
            "market": market,
            "price": price,
            "bid": bid,
            "ask": ask,
            "ts": datetime.now().isoformat()
        }


class THSSource(BaseStockSource):
    name = "ths"
    label = "同花顺极速行情"
    vendor = "THS"
    env_required = ["THS_APP_KEY", "THS_APP_SECRET"]
    env_optional = ["THS_SIM_ACCOUNT", "THS_SIM_PASSWORD"]
    latency_ms = 380

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        # 真实实现应调用同花顺接口；此处模拟带环境数据的结果
        base = 20 + (hash(symbol) % 50) / 3
        jitter = random.uniform(-0.5, 0.5)
        price = round(base + jitter, 2)
        return {
            "symbol": symbol,
            "market": market,
            "price": price,
            "bid": round(price - 0.03, 2),
            "ask": round(price + 0.03, 2),
            "ts": datetime.now().isoformat(),
            "vendor": self.vendor
        }


class TushareSource(BaseStockSource):
    name = "tushare"
    label = "Tushare 数据云"
    vendor = "Tushare"
    env_required = ["TUSHARE_TOKEN"]
    latency_ms = 520

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        base = 15 + (hash(symbol + "ts") % 70) / 4
        drift = random.uniform(-0.6, 0.6)
        price = round(base + drift, 2)
        return {
            "symbol": symbol,
            "market": market,
            "price": price,
            "bid": round(price - 0.05, 2),
            "ask": round(price + 0.05, 2),
            "ts": datetime.now().isoformat(),
            "vendor": self.vendor
        }


class AlphaVantageSource(BaseStockSource):
    name = "alphavantage"
    label = "Alpha Vantage"
    vendor = "AlphaVantage"
    env_required = ["ALPHAVANTAGE_API_KEY"]
    latency_ms = 640

    async def quote(self, symbol: str, market: str = "US"):
        base = 30 + (hash(symbol + market) % 100) / 2
        drift = random.uniform(-1, 1)
        price = round(base + drift, 2)
        return {
            "symbol": symbol,
            "market": market,
            "price": price,
            "bid": round(price - 0.08, 2),
            "ask": round(price + 0.08, 2),
            "ts": datetime.now().isoformat(),
            "vendor": self.vendor
        }


class StockGateway:
    def __init__(self):
        self.sources: Dict[str, BaseStockSource] = {}
        self.register_source(MockSource())
        self.register_source(THSSource())
        self.register_source(TushareSource())
        self.register_source(AlphaVantageSource())
        ready_sources = [key for key, src in self.sources.items() if src.ready]
        self.active_source: str = ready_sources[0] if ready_sources else "mock"

    def register_source(self, source: BaseStockSource):
        self.sources[source.name] = source

    def list_sources(self) -> Dict[str, Any]:
        return {
            "active": self.active_source,
            "available": [src.metadata() for src in self.sources.values()]
        }

    def switch(self, source: str) -> bool:
        src = self.sources.get(source)
        if src and (src.ready or source == "mock"):
            self.active_source = source
            return True
        return False

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        """
        获取行情（增强版：支持热切换和自动故障转移）
        """
        ordered_sources = [self.active_source] + [sid for sid in self.sources if sid != self.active_source]
        errors = []
        last_error_source = None
        
        for source_id in ordered_sources:
            src = self.sources.get(source_id)
            if not src or (not src.ready and source_id != "mock"):
                continue
            try:
                data = await src.quote(symbol, market)
                src.last_success = datetime.now().isoformat()
                src.last_error = None
                data["source"] = source_id
                
                # 如果使用了备用源，自动切换
                if source_id != self.active_source:
                    self.active_source = source_id
                    logger.info(f"自动切换到数据源: {source_id}")
                
                return data
            except Exception as exc:  # pragma: no cover - fallback
                src.last_error = str(exc)
                src.last_success = None
                errors.append(f"{source_id}: {exc}")
                last_error_source = source_id
                continue
        
        # 所有源都失败，记录错误
        if last_error_source:
            logger.error(f"所有行情源不可用，最后尝试: {last_error_source}")
        
        raise RuntimeError(f"所有行情源不可用: {'; '.join(errors) if errors else '无可用源'}")
    
    def get_source_health(self) -> Dict[str, Any]:
        """获取数据源健康状态"""
        health_status = {}
        for source_id, src in self.sources.items():
            health_status[source_id] = {
                "ready": src.ready,
                "last_success": src.last_success,
                "last_error": src.last_error,
                "latency_ms": src.latency_ms,
                "is_active": source_id == self.active_source,
            }
        return {
            "active_source": self.active_source,
            "sources": health_status,
            "total_sources": len(self.sources),
            "ready_sources": len([s for s in self.sources.values() if s.ready]),
        }


