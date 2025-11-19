"""
可观测性中间件
自动生成和传播 requestId/traceId，记录请求性能
"""

from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from .observability_system import SpanType, SpanStatus

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """可观测性中间件"""
    
    def __init__(self, app: ASGIApp, observability_system):
        super().__init__(app)
        self.observability = observability_system
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        # 从请求头获取或生成 trace_id 和 request_id
        trace_id = request.headers.get("X-Trace-ID") or self.observability.generate_trace_id()
        request_id = request.headers.get("X-Request-ID") or self.observability.generate_request_id()
        
        # 存储到请求状态
        request.state.trace_id = trace_id
        request.state.request_id = request_id
        
        # 开始Trace
        trace = self.observability.start_trace(
            request_id=request_id,
            trace_id=trace_id,
            service_name="super-agent",
            tags={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.url.query),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent")
            }
        )
        
        # 开始HTTP Span
        span = self.observability.start_span(
            trace_id=trace_id,
            name=f"{request.method} {request.url.path}",
            span_type=SpanType.HTTP,
            tags={
                "http.method": request.method,
                "http.path": request.url.path,
                "http.query": str(request.url.query),
                "http.client_ip": request.client.host if request.client else None
            }
        )
        
        # 记录埋点事件
        self.observability.track_event(
            event_name="http_request_start",
            trace_id=trace_id,
            span_id=span.span_id,
            properties={
                "method": request.method,
                "path": request.url.path
            }
        )
        
        start_time = time.time()
        status_code = 200
        error = None
        
        try:
            # 执行请求
            response = await call_next(request)
            status_code = response.status_code
            
            # 记录响应指标
            duration = time.time() - start_time
            self.observability.record_metric(
                name="http_request_duration",
                value=duration,
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": str(status_code)
                },
                metric_type="histogram"
            )
            
            self.observability.record_metric(
                name="http_request_count",
                value=1,
                tags={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": str(status_code)
                },
                metric_type="counter"
            )
            
            # 添加响应头
            response.headers["X-Trace-ID"] = trace_id
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            status_code = 500
            error = str(e)
            logger.error(f"请求处理失败: {e}", exc_info=True)
            raise
        
        finally:
            # 完成Span
            span_status = SpanStatus.ERROR if status_code >= 400 else SpanStatus.OK
            self.observability.finish_span(
                span_id=span.span_id,
                status=span_status,
                error=error
            )
            
            # 完成Trace
            trace_status = "error" if status_code >= 400 else "ok"
            self.observability.finish_trace(trace_id, trace_status)
            
            # 记录埋点事件
            duration = time.time() - start_time
            self.observability.track_event(
                event_name="http_request_end",
                trace_id=trace_id,
                span_id=span.span_id,
                properties={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration": duration
                },
                level="error" if status_code >= 400 else "info"
            )

