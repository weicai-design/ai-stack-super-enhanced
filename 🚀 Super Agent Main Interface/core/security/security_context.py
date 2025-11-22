from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set


@dataclass
class SecurityContext:
    """当前请求的安全上下文"""

    request_id: str
    user_id: str = "anonymous"
    roles: Set[str] = field(default_factory=set)
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    sensitive_flags: Set[str] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "roles": list(self.roles),
            "ip": self.ip,
            "user_agent": self.user_agent,
            "sensitive_flags": list(self.sensitive_flags),
        }


def attach_security_context(request, context: SecurityContext) -> None:
    """将安全上下文绑定到 request.state 方便后续依赖使用"""
    request.state.security_context = context


