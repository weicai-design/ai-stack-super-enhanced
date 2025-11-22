from __future__ import annotations

import time
from typing import Awaitable, Callable, Optional
from uuid import uuid4

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .audit import AuditLogger, get_audit_logger
from .audit_pipeline import SecurityAuditPipeline, get_audit_pipeline
from .config import get_security_settings
from .crawler_compliance import CrawlerComplianceService, get_crawler_compliance_service
from .permission_guard import PermissionGuard, get_permission_guard
from .risk_engine import SecurityRiskEngine, get_risk_engine
from .security_context import SecurityContext, attach_security_context


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    统一安全栈中间件：审计 + 风控 + RBAC 上下文 + 爬虫合规。
    """

    def __init__(
        self,
        app,
        audit_logger: Optional[AuditLogger] = None,
        skip_paths: Optional[tuple[str, ...]] = None,
        audit_pipeline: Optional[SecurityAuditPipeline] = None,
        risk_engine: Optional[SecurityRiskEngine] = None,
        permission_guard: Optional[PermissionGuard] = None,
        crawler_compliance: Optional[CrawlerComplianceService] = None,
    ):
        super().__init__(app)
        settings = get_security_settings()
        self.audit_logger = audit_logger or get_audit_logger()
        self.skip_paths = skip_paths or settings.skip_audit_paths
        self.audit_pipeline = audit_pipeline or get_audit_pipeline()
        self.risk_engine = risk_engine or get_risk_engine()
        self.permission_guard = permission_guard or get_permission_guard()
        self.crawler_compliance = crawler_compliance or get_crawler_compliance_service()

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        security_context = self._build_security_context(request, request_id)
        attach_security_context(request, security_context)

        if self._is_crawler_request(security_context):
            evaluation = self.crawler_compliance.evaluate(
                security_context.user_agent,
                request.url.path,
                security_context.ip,
            )
            if not evaluation["allowed"]:
                if self.audit_pipeline:
                    self.audit_pipeline.log_security_event(
                        event_type="crawler.blocked",
                        source="security_middleware",
                        severity="warning",
                        status="failed",
                        actor=security_context.user_id,
                        metadata=evaluation,
                    )
                raise HTTPException(status_code=451, detail="Crawler request not compliant")

        if any(request.url.path.startswith(path) for path in self.skip_paths):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            self._log_http(request, 500, duration_ms, {"error": str(exc)})
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        self._log_http(request, response.status_code, duration_ms, {"request_id": request_id})
        return response

    def _log_http(self, request: Request, status_code: int, duration_ms: float, metadata: Optional[dict] = None) -> None:
        if self.audit_logger:
            self.audit_logger.log_http_request(
                request,
                response_status=status_code,
                duration_ms=duration_ms,
                metadata=metadata or {},
            )
        if self.audit_pipeline:
            self.audit_pipeline.log_http_request(
                request=request,
                response_status=status_code,
                duration_ms=duration_ms,
                metadata=metadata or {},
            )
        if self.risk_engine:
            actor = request.headers.get("x-user-id") or "anonymous"
            self.risk_engine.observe_http_request(actor, status_code, request.url.path, duration_ms)

    def _build_security_context(self, request: Request, request_id: str) -> SecurityContext:
        user_id = request.headers.get("x-user-id") or "anonymous"
        roles_header = request.headers.get("x-user-roles")
        roles = self.permission_guard.parse_roles(roles_header)
        return SecurityContext(
            request_id=request_id,
            user_id=user_id,
            roles=roles,
            ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

    def _is_crawler_request(self, context: SecurityContext) -> bool:
        if not context.user_agent:
            return False
        ua = context.user_agent.lower()
        if not self.crawler_compliance:
            return False
        return any(keyword in ua for keyword in ("bot", "spider", "crawler"))
