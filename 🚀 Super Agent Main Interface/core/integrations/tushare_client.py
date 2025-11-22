#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare 数据云客户端

提供最小版行情/指标查询，用于真实 API 对接。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from .api_monitor import APIMonitor


class TushareClient:
    def __init__(self, api_monitor: Optional[APIMonitor] = None):
        self.token = os.getenv("TUSHARE_TOKEN")
        self.base_url = os.getenv("TUSHARE_API", "https://api.waditu.com")
        self.api_monitor = api_monitor or APIMonitor()

    def is_configured(self) -> bool:
        return bool(self.token)

    async def quote(self, symbol: str) -> Dict[str, Any]:
        """
        查询日线行情（真实请求需要有效 token）。
        """
        endpoint = "/daily"
        payload = {
            "api_name": "daily",
            "token": self.token,
            "params": {"ts_code": symbol, "limit": 1},
            "fields": "ts_code,trade_date,open,high,low,close,vol,amount",
        }
        request_id = symbol
        status_code = None
        success = False
        duration_ms = 0.0
        error = None
        response_json: Optional[Dict[str, Any]] = None

        if not self.is_configured():
            return {"success": False, "error": "未配置 TUSHARE_TOKEN", "symbol": symbol}

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(self.base_url, json=payload)
                status_code = resp.status_code
                duration_ms = resp.elapsed.total_seconds() * 1000
                resp.raise_for_status()
                response_json = resp.json()
                items = response_json.get("data", {}).get("items") or []
                if not items:
                    return {"success": False, "error": "Tushare无数据返回", "symbol": symbol, "raw": response_json}
                item = items[0]
                success = True
                return {
                    "success": True,
                    "symbol": symbol,
                    "trade_date": item[1],
                    "open": item[2],
                    "high": item[3],
                    "low": item[4],
                    "close": item[5],
                    "volume": item[6],
                    "amount": item[7],
                    "raw": response_json,
                }
        except Exception as exc:  # pragma: no cover
            error = str(exc)
            return {"success": False, "error": error, "symbol": symbol}
        finally:
            self.api_monitor.record_call(
                system="tushare",
                endpoint=endpoint,
                method="POST",
                status_code=status_code,
                success=success,
                duration_ms=duration_ms,
                request_id=request_id,
                error=error,
                metadata={"symbol": symbol},
            )


__all__ = ["TushareClient"]


