"""
简易回测引擎（占位）：按日收益序列/随机波动生成曲线与指标
"""
from __future__ import annotations

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random


class BacktestEngine:
    def run(self, symbol: str, days: int = 60, seed: int = 7) -> Dict[str, Any]:
        random.seed(seed)
        equity = 1_000_000.0
        series: List[Dict[str, Any]] = []
        max_equity = equity
        peak = equity
        max_drawdown = 0.0
        for i in range(days):
            ret = random.uniform(-0.02, 0.02)
            equity *= (1.0 + ret)
            ts = (datetime.now() - timedelta(days=days - i)).date().isoformat()
            series.append({"date": ts, "ret": round(ret, 4), "equity": round(equity, 2)})
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, (peak - equity) / peak)
        total_ret = (equity / 1_000_000.0) - 1.0
        ann_ret = total_ret * (252.0 / max(days, 1))
        return {
            "success": True,
            "symbol": symbol,
            "days": days,
            "equity_end": round(equity, 2),
            "total_return": round(total_ret, 4),
            "annual_return_est": round(ann_ret, 4),
            "max_drawdown": round(max_drawdown, 4),
            "series": series
        }


