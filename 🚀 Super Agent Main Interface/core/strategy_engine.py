"""
策略引擎（SLO与降级）
提供：请求预算、模型/检索降级、异步队列建议与缓存提示
"""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
from datetime import datetime, timedelta


@dataclass
class StrategyDecision:
    use_fast_model: bool
    rag_top_k: int
    timeout_seconds: float
    enable_streaming: bool
    degrade_reason: Optional[str] = None
    cache_hint_key: Optional[str] = None
    queue_wait: float = 0.0
    degrade_level: str = "normal"
    max_module_time: float = 2.0
    allow_background: bool = False
    use_cache_only: bool = False
    need_release: bool = False


class AsyncRequestBudget:
    """异步请求预算器（控制并发与队列等待）"""
    def __init__(self, max_qps: int = 8, max_concurrency: int = 4, window_seconds: int = 2):
        self.max_qps = max_qps
        self.max_concurrency = max_concurrency
        self.window_seconds = window_seconds
        self._events = deque()
        self._sem = asyncio.Semaphore(max_concurrency)
        self._lock = asyncio.Lock()

    async def acquire(self, wait_timeout: float = 0.4) -> Tuple[bool, float, Optional[str]]:
        start = datetime.now()
        try:
            await asyncio.wait_for(self._sem.acquire(), timeout=wait_timeout)
            queue_wait = (datetime.now() - start).total_seconds()
        except asyncio.TimeoutError:
            return False, wait_timeout, "queue_timeout"

        async with self._lock:
            now = datetime.now()
            while self._events and (now - self._events[0]).total_seconds() > self.window_seconds:
                self._events.popleft()
            if len(self._events) >= self.max_qps:
                self._sem.release()
                return False, queue_wait, "qps_limit"
            self._events.append(now)

        return True, queue_wait, None

    def release(self):
        self._sem.release()

    async def stats(self) -> Dict[str, Any]:
        async with self._lock:
            qps_current = len(self._events) / max(self.window_seconds, 1)
        concurrency = self.max_concurrency - self._sem._value  # type: ignore[attr-defined]
        return {
            "qps_current": qps_current,
            "concurrency": concurrency,
            "max_qps": self.max_qps,
            "max_concurrency": self.max_concurrency,
            "window_seconds": self.window_seconds
        }


class StrategyEngine:
    """基于简单规则的SLO策略引擎"""
    def __init__(self):
        self.request_budget = AsyncRequestBudget()
        self.default_timeouts = {
            "text": 2.2,
            "search": 2.4,
            "file": 3.0,
            "voice": 2.5
        }
        self.default_top_k = 3

    async def decide(
        self,
        message: str,
        input_type: str = "text",
        complexity_hint: Optional[str] = None
    ) -> StrategyDecision:
        acquired, queue_wait, budget_reason = await self.request_budget.acquire()
        degrade_reason = budget_reason
        use_fast_model = True
        top_k = self.default_top_k
        timeout = self.default_timeouts.get(input_type, 2.2)
        enable_streaming = True
        degrade_level = "normal"
        allow_background = False
        use_cache_only = False
        need_release = acquired

        # 简单复杂度估计：超长文本或包含“分析/报告/趋势”认为复杂
        if len(message) > 500 or any(tok in message for tok in ["分析", "报告", "趋势", "回测", "回归"]):
            use_fast_model = False
            top_k = max(2, self.default_top_k - 1)  # 减少检索数量以控时
            timeout = min(timeout + 0.6, 2.8)
            degrade_level = "heavy"

        if not acquired:
            degrade_reason = degrade_reason or "budget_exceeded"
            degrade_level = "cache_only"
            use_cache_only = True
            top_k = 1
            timeout = 1.2
            enable_streaming = False
        elif queue_wait > 0.25:
            degrade_level = "light"
            top_k = max(1, top_k - 1)
            timeout = max(1.8, timeout - queue_wait)
        elif queue_wait > 0.1:
            degrade_level = "medium"
            timeout = max(2.0, timeout - queue_wait / 2)

        processing_budget = max(1.8 - queue_wait, 1.1)
        timeout = min(timeout, processing_budget + queue_wait + 0.4)
        max_module_time = max(0.6, processing_budget * 0.45)

        if degrade_level == "heavy":
            allow_background = True
            enable_streaming = True

        if complexity_hint == "background":
            allow_background = True

        cache_hint_key = (message[:120] if message else None)

        if use_cache_only:
            need_release = False

        return StrategyDecision(
            use_fast_model=use_fast_model,
            rag_top_k=top_k,
            timeout_seconds=timeout,
            enable_streaming=enable_streaming,
            degrade_reason=degrade_reason,
            cache_hint_key=cache_hint_key,
            queue_wait=queue_wait,
            degrade_level=degrade_level,
            max_module_time=max_module_time,
            allow_background=allow_background,
            use_cache_only=use_cache_only,
            need_release=need_release
        )

    def release(self, decision: Optional[StrategyDecision] = None):
        if decision and not decision.need_release:
            return
        self.request_budget.release()

    async def get_stats(self) -> Dict[str, Any]:
        s = await self.request_budget.stats()
        return {"budget": s}


