#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Gateway

为单体/Sidecar/微服务通信提供统一入口，支持：
- 内部 handler 调用（同进程）
- HTTP 调度（对Sidecar/远端实例）
- 请求跟踪与统计
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple
from uuid import uuid4

import httpx

from .service_registry import ServiceRegistry, ServiceContract, get_service_registry

InternalHandler = Callable[[Dict[str, Any]], Awaitable[Any]] | Callable[[Dict[str, Any]], Any]


@dataclass
class ServiceCallResult:
    request_id: str
    service: str
    operation: str
    status: str
    response: Any
    latency_ms: float
    instance_id: Optional[str] = None
    executed_via: str = "internal"  # internal / http

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "service": self.service,
            "operation": self.operation,
            "status": self.status,
            "response": self.response,
            "latency_ms": round(self.latency_ms, 2),
            "instance_id": self.instance_id,
            "executed_via": self.executed_via,
        }


class ServiceGateway:
    def __init__(
        self,
        registry: Optional[ServiceRegistry] = None,
        timeout: float = 3.0,
    ):
        self.registry = registry or get_service_registry()
        self.timeout = timeout
        self.internal_handlers: Dict[Tuple[str, str], InternalHandler] = {}

    def register_internal_handler(self, service: str, operation: str, handler: InternalHandler) -> None:
        self.internal_handlers[(service, operation)] = handler

    async def call_service(
        self,
        service: str,
        operation: str,
        payload: Optional[Dict[str, Any]] = None,
        prefer_internal: bool = True,
    ) -> ServiceCallResult:
        contract = self.registry.get_contract(service, operation)
        if not contract:
            return ServiceCallResult(
                request_id=self._request_id(),
                service=service,
                operation=operation,
                status="error",
                response={"error": "contract_not_found"},
                latency_ms=0.0,
            )

        start = perf_counter()

        if prefer_internal and (handler := self.internal_handlers.get((service, operation))):
            response = await self._execute_internal(handler, payload or {})
            return ServiceCallResult(
                request_id=self._request_id(),
                service=service,
                operation=operation,
                status="success",
                response=response,
                latency_ms=(perf_counter() - start) * 1000,
                executed_via="internal",
            )

        instance = self._pick_instance(service)
        if not instance:
            return ServiceCallResult(
                request_id=self._request_id(),
                service=service,
                operation=operation,
                status="error",
                response={"error": "instance_not_found"},
                latency_ms=(perf_counter() - start) * 1000,
            )

        http_result = await self._execute_http(instance, contract, payload or {})
        return ServiceCallResult(
            request_id=self._request_id(),
            service=service,
            operation=operation,
            status=http_result.get("status", "error"),
            response=http_result.get("data"),
            latency_ms=(perf_counter() - start) * 1000,
            instance_id=instance.instance_id,
            executed_via="http",
        )

    async def _execute_internal(self, handler: InternalHandler, payload: Dict[str, Any]) -> Any:
        result = handler(payload)
        if asyncio.iscoroutine(result):
            return await result
        return result

    def _pick_instance(self, service: str):
        instances = self.registry.list_instances(service)
        healthy = [inst for inst in instances if inst["status"] == "healthy"]
        target = healthy[0] if healthy else (instances[0] if instances else None)
        if not target:
            return None
        from .service_registry import ServiceInstance

        return ServiceInstance(**target)

    async def _execute_http(self, instance, contract: ServiceContract, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{instance.endpoint}{contract.path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if contract.method.upper() == "GET":
                    resp = await client.get(url, params=payload)
                else:
                    resp = await client.post(url, json=payload)
        except Exception as exc:
            return {"status": "error", "data": {"error": str(exc)}}

        try:
            data = resp.json()
        except json.JSONDecodeError:
            data = resp.text

        status = "success" if resp.status_code < 400 else "error"
        return {"status": status, "data": data}

    def _request_id(self) -> str:
        return f"svc_{uuid4().hex[:10]}"


_service_gateway: Optional[ServiceGateway] = None


def get_service_gateway() -> ServiceGateway:
    global _service_gateway
    if _service_gateway is None:
        _service_gateway = ServiceGateway()
    return _service_gateway

