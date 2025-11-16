"""
策略引擎（SLO与降级）
提供：请求预算、模型/检索降级、异步队列建议与缓存提示
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import threading


@dataclass
class StrategyDecision:
    use_fast_model: bool
    rag_top_k: int
    timeout_seconds: float
    enable_streaming: bool
    degrade_reason: Optional[str] = None
    cache_hint_key: Optional[str] = None


class RequestBudget:
    """简单请求预算器（滑动窗口QPS/并发）"""
    def __init__(self, max_qps: int = 8, max_concurrency: int = 4, window_seconds: int = 2):
        self.max_qps = max_qps
        self.max_concurrency = max_concurrency
        self.window_seconds = window_seconds
        self._events = []
        self._concurrency = 0
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        with self._lock:
            now = datetime.now()
            self._events = [t for t in self._events if (now - t).total_seconds() <= self.window_seconds]
            if len(self._events) >= self.max_qps or self._concurrency >= self.max_concurrency:
                return False
            self._events.append(now)
            self._concurrency += 1
            return True

    def release(self):
        with self._lock:
            if self._concurrency > 0:
                self._concurrency -= 1

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "qps_current": len(self._events) / max(self.window_seconds, 1),
                "concurrency": self._concurrency,
                "max_qps": self.max_qps,
                "max_concurrency": self.max_concurrency,
                "window_seconds": self.window_seconds
            }


class StrategyEngine:
    """基于简单规则的SLO策略引擎"""
    def __init__(self):
        self.request_budget = RequestBudget()
        self.default_timeouts = {
            "text": 8.0,
            "search": 10.0,
            "file": 12.0,
            "voice": 10.0
        }
        self.default_top_k = 3

    def decide(self, message: str, input_type: str = "text", complexity_hint: Optional[str] = None) -> StrategyDecision:
        budget_ok = self.request_budget.acquire()
        degrade_reason = None
        use_fast_model = True
        top_k = self.default_top_k
        timeout = self.default_timeouts.get(input_type, 8.0)
        enable_streaming = True

        # 简单复杂度估计：超长文本或包含“分析/报告/趋势”认为复杂
        if len(message) > 500 or any(tok in message for tok in ["分析", "报告", "趋势", "回测", "回归"]):
            use_fast_model = False
            top_k = max(2, self.default_top_k - 1)  # 减少检索数量以控时
            timeout = min(timeout + 2.0, 12.0)

        # 若预算不足，触发降级
        if not budget_ok:
            degrade_reason = "budget_exceeded"
            use_fast_model = True
            top_k = 2
            timeout = min(timeout, 6.0)
            enable_streaming = True

        return StrategyDecision(
            use_fast_model=use_fast_model,
            rag_top_k=top_k,
            timeout_seconds=timeout,
            enable_streaming=enable_streaming,
            degrade_reason=degrade_reason,
            cache_hint_key=(message[:100] if len(message) > 0 else None)
        )

    def release(self):
        self.request_budget.release()

    def get_stats(self) -> Dict[str, Any]:
        s = self.request_budget.stats()
        return {"budget": s}


