from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass
class CrawlerPolicy:
    allowed_agents: tuple[str, ...]
    blocked_agents: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    blocked_paths: tuple[str, ...]
    rate_limit_per_minute: int


class CrawlerComplianceService:
    """简单的爬虫合规检查"""

    def __init__(
        self,
        policy_path: Optional[Path] = None,
        default_policy: Optional[CrawlerPolicy] = None,
    ):
        self.policy_path = policy_path or Path("config/compliance/crawler_policy.json")
        self._policy = default_policy or CrawlerPolicy(
            allowed_agents=("Googlebot", "Bingbot", "Bytespider"),
            blocked_agents=("sqlmap", "nikto", "dirbuster"),
            allowed_paths=("/docs", "/sitemaps", "/robots.txt"),
            blocked_paths=("/admin", "/security", "/api/secure"),
            rate_limit_per_minute=60,
        )
        self._rate_cache: Dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._load_policy()

    def _load_policy(self) -> None:
        if not self.policy_path.exists():
            return
        try:
            data = json.loads(self.policy_path.read_text(encoding="utf-8"))
            self._policy = CrawlerPolicy(
                allowed_agents=tuple(data.get("allowed_agents", self._policy.allowed_agents)),
                blocked_agents=tuple(data.get("blocked_agents", self._policy.blocked_agents)),
                allowed_paths=tuple(data.get("allowed_paths", self._policy.allowed_paths)),
                blocked_paths=tuple(data.get("blocked_paths", self._policy.blocked_paths)),
                rate_limit_per_minute=int(data.get("rate_limit_per_minute", self._policy.rate_limit_per_minute)),
            )
        except Exception:
            # 默认策略
            pass

    def evaluate(self, user_agent: str | None, path: str, client_ip: str | None) -> Dict[str, any]:
        agent = (user_agent or "").lower()
        result = {
            "allowed": True,
            "reasons": [],
            "user_agent": user_agent,
            "path": path,
        }

        if not agent:
            return result

        # 黑名单
        for blocked in self._policy.blocked_agents:
            if blocked.lower() in agent:
                result["allowed"] = False
                result["reasons"].append(f"blocked_agent:{blocked}")

        # 白名单路径
        if result["allowed"]:
            for blocked_path in self._policy.blocked_paths:
                if path.startswith(blocked_path):
                    result["allowed"] = False
                    result["reasons"].append(f"blocked_path:{blocked_path}")
                    break

        # 速率限制
        if client_ip:
            now = time.time()
            with self._lock:
                history = self._rate_cache.setdefault(client_ip, [])
                history.append(now)
                self._rate_cache[client_ip] = [t for t in history if t > now - 60]
                if len(self._rate_cache[client_ip]) > self._policy.rate_limit_per_minute:
                    result["allowed"] = False
                    result["reasons"].append("rate_limit_exceeded")

        return result


_crawler_service: Optional[CrawlerComplianceService] = None


def get_crawler_compliance_service() -> CrawlerComplianceService:
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerComplianceService()
    return _crawler_service


