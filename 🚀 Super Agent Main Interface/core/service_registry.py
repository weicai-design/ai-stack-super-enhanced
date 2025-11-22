#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Registry & Contracts

P3-002 微服务拆分：用于描述、注册、发现服务与通信契约。
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from collections import deque
from uuid import uuid4


def _utc_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class ServiceContract:
    service: str
    operation: str
    method: str = "POST"
    path: str = "/"
    version: str = "v1"
    timeout: float = 2.0
    schema: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ServiceInstance:
    service: str
    instance_id: str
    endpoint: str
    version: str = "v1"
    protocol: str = "http"
    status: str = "healthy"
    deployment_target: str = "monolith"
    last_heartbeat: str = field(default_factory=_utc_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ServiceRegistry:
    """轻量级服务注册中心（内存版，可替换为 Redis/DB）"""

    def __init__(self):
        self._contracts: Dict[str, ServiceContract] = {}
        self._instances: Dict[str, Dict[str, ServiceInstance]] = {}
        self._changelog: deque[Dict[str, Any]] = deque(maxlen=100)

    def register_contract(self, contract: ServiceContract) -> None:
        key = self._contract_key(contract.service, contract.operation)
        self._contracts[key] = contract
        self._record_change("contract_registered", contract.service, {"operation": contract.operation})

    def get_contract(self, service: str, operation: str) -> Optional[ServiceContract]:
        return self._contracts.get(self._contract_key(service, operation))

    def list_contracts(self) -> List[Dict[str, Any]]:
        return [contract.to_dict() for contract in self._contracts.values()]

    def register_instance(
        self,
        service: str,
        endpoint: str,
        version: str = "v1",
        protocol: str = "http",
        deployment_target: str = "monolith",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ServiceInstance:
        instance = ServiceInstance(
            service=service,
            instance_id=f"{service}-{uuid4().hex[:8]}",
            endpoint=endpoint.rstrip("/"),
            version=version,
            protocol=protocol,
            deployment_target=deployment_target,
            metadata=metadata or {},
        )
        self._instances.setdefault(service, {})[instance.instance_id] = instance
        self._record_change("instance_registered", service, instance.to_dict())
        return instance

    def heartbeat(self, service: str, instance_id: str, status: str = "healthy") -> bool:
        instance = self._instances.get(service, {}).get(instance_id)
        if not instance:
            return False
        instance.status = status
        instance.last_heartbeat = _utc_now()
        return True

    def list_instances(self, service: Optional[str] = None) -> List[Dict[str, Any]]:
        if service:
            service_map = self._instances.get(service, {})
            return [instance.to_dict() for instance in service_map.values()]
        result: List[Dict[str, Any]] = []
        for instances in self._instances.values():
            result.extend(instance.to_dict() for instance in instances.values())
        return result

    def get_service_summary(self) -> Dict[str, Any]:
        return {
            service: {
                "contracts": [
                    contract.to_dict()
                    for key, contract in self._contracts.items()
                    if key.startswith(f"{service}:")
                ],
                "instances": [instance.to_dict() for instance in instances.values()],
            }
            for service, instances in self._instances.items()
        }

    def get_changelog(self) -> List[Dict[str, Any]]:
        return list(self._changelog)

    def _contract_key(self, service: str, operation: str) -> str:
        return f"{service}:{operation}"

    def _record_change(self, action: str, service: str, payload: Dict[str, Any]) -> None:
        self._changelog.appendleft(
            {
                "timestamp": _utc_now(),
                "action": action,
                "service": service,
                "payload": payload,
            }
        )


# 全局单例
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry

