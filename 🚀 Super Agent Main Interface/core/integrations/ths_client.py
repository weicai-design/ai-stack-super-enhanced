#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同花顺极速行情 API 客户端

真实接口：需要申请 App Key / Secret。
当未配置密钥或网络不可达时，返回 graceful fallback。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx

from .api_monitor import APIMonitor


@dataclass
class THSQuoteResponse:
    success: bool
    symbol: str
    price: Optional[float]
    bid: Optional[float]
    ask: Optional[float]
    vendor: str
    error: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class THSQuoteClient:
    """
    同花顺行情客户端（REST）
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_monitor: Optional[APIMonitor] = None,
    ):
        self.base_url = base_url or os.getenv("THS_API_BASE", "https://openapi.ths123.com/data/v2")
        self.app_key = os.getenv("THS_APP_KEY")
        self.app_secret = os.getenv("THS_APP_SECRET")
        self.api_monitor = api_monitor or APIMonitor()

    def is_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)

    async def quote(self, symbol: str, market: str = "A") -> THSQuoteResponse:
        if not self.is_configured():
            return THSQuoteResponse(
                success=False,
                symbol=symbol,
                price=None,
                bid=None,
                ask=None,
                vendor="THS",
                error="THS_APP_KEY/SECRET 未配置",
            )

        endpoint = "/quote/real-time"
        params = {
            "app_key": self.app_key,
            "app_secret": self.app_secret,
            "symbol": symbol,
            "market": market,
        }
        url = f"{self.base_url}{endpoint}"
        request_id = symbol
        method = "GET"
        status_code = None
        success = False
        duration_ms = 0.0
        error = None
        response_json: Optional[Dict[str, Any]] = None

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                status_code = resp.status_code
                duration_ms = resp.elapsed.total_seconds() * 1000
                resp.raise_for_status()
                response_json = resp.json()
                quote = response_json.get("data", {})
                price = float(quote.get("last_price"))
                bid = float(quote.get("bid_price"))
                ask = float(quote.get("ask_price"))
                success = True
                return THSQuoteResponse(
                    success=True,
                    symbol=symbol,
                    price=price,
                    bid=bid,
                    ask=ask,
                    vendor="THS",
                    raw=response_json,
                )
        except Exception as exc:  # pragma: no cover - 网络环境不可控
            error = str(exc)
            return THSQuoteResponse(
                success=False,
                symbol=symbol,
                price=None,
                bid=None,
                ask=None,
                vendor="THS",
                error=error,
            )
        finally:
            self.api_monitor.record_call(
                system="ths",
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                success=success,
                duration_ms=duration_ms,
                request_id=request_id,
                error=error,
                metadata={"symbol": symbol, "market": market, "url": url},
            )


__all__ = ["THSQuoteClient", "THSQuoteResponse"]


