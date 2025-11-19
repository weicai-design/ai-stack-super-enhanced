from __future__ import annotations

import time
from typing import Callable, Awaitable, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .audit import AuditLogger, get_audit_logger
from .config import get_security_settings


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    统一请求审计：为每个请求打 request_id，记录响应耗时、IP、状态等信息。
    """

    def __init__(
        self,
        app,
        audit_logger: Optional[AuditLogger] = None,
        skip_paths: Optional[tuple[str, ...]] = None,
    ):
        super().__init__(app)
        settings = get_security_settings()
        self.audit_logger = audit_logger or get_audit_logger()
        self.skip_paths = skip_paths or settings.skip_audit_paths

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = str(uuid4())
        request.state.request_id = request_id
        if any(request.url.path.startswith(path) for path in self.skip_paths):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:  # noqa: BLE001
            duration_ms = (time.perf_counter() - start) * 1000
            self.audit_logger.log_http_request(
                request,
                response_status=500,
                duration_ms=duration_ms,
                metadata={"error": str(exc)},
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        self.audit_logger.log_http_request(
            request,
            response_status=response.status_code,
            duration_ms=duration_ms,
            metadata={"request_id": request_id},
        )
        return response


