"""
股票数据源网关（可插拔，支持热切换）
目标：抽象不同行情源（同花顺/聚宽/自建等），提供统一查询接口
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime
import random


class BaseStockSource:
    name: str = "base"

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        raise NotImplementedError


class MockSource(BaseStockSource):
    name = "mock"

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


class StockGateway:
    def __init__(self):
        self.sources: Dict[str, BaseStockSource] = {
            "mock": MockSource(),
            # "ths": THSSource(...),  # 预留：同花顺
        }
        self.active_source: str = "mock"

    def list_sources(self) -> Dict[str, Any]:
        return {
            "active": self.active_source,
            "available": list(self.sources.keys())
        }

    def switch(self, source: str) -> bool:
        if source in self.sources:
            self.active_source = source
            return True
        return False

    async def quote(self, symbol: str, market: str = "A") -> Dict[str, Any]:
        src = self.sources.get(self.active_source) or self.sources["mock"]
        data = await src.quote(symbol, market)
        data["source"] = self.active_source
        return data


