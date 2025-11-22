#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tenant Manager

提供统一的租户注册、查询与配置存储，支持多租户架构演进。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Optional

from .tenant_context import TenantContext


@dataclass
class Tenant:
    tenant_id: str
    name: str
    plan: str = "enterprise"
    active: bool = True
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_context(self) -> TenantContext:
        return TenantContext(tenant_id=self.tenant_id, name=self.name, metadata=self.metadata)


class TenantManager:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(
            storage_path
            or os.getenv("TENANT_CONFIG_PATH", "config/tenants.json")
        )
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tenants: Dict[str, Tenant] = {}
        self._load()

    # ------------------------------- Persistence -------------------------------
    def _load(self) -> None:
        if not self.storage_path.exists():
            self._tenants = {
                "global": Tenant(tenant_id="global", name="Global Default", plan="enterprise")
            }
            self._save()
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self._tenants = {
                item["tenant_id"]: Tenant(**item) for item in data.get("tenants", [])
            }
        except Exception:
            self._tenants = {
                "global": Tenant(tenant_id="global", name="Global Default", plan="enterprise")
            }

    def _save(self) -> None:
        payload = {"tenants": [asdict(t) for t in self._tenants.values()]}
        self.storage_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # --------------------------------- CRUD -----------------------------------
    def list_tenants(self, include_inactive: bool = False) -> List[Dict]:
        tenants = self._tenants.values()
        if not include_inactive:
            tenants = [t for t in tenants if t.active]
        return [asdict(t) for t in tenants]

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def upsert_tenant(self, tenant_id: str, name: str, **kwargs) -> Tenant:
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            plan=kwargs.get("plan", "enterprise"),
            active=kwargs.get("active", True),
            metadata=kwargs.get("metadata", {}),
        )
        self._tenants[tenant_id] = tenant
        self._save()
        return tenant

    def update_status(self, tenant_id: str, active: bool) -> bool:
        tenant = self._tenants.get(tenant_id)
        if not tenant:
            return False
        tenant.active = active
        self._save()
        return True

    def delete_tenant(self, tenant_id: str) -> bool:
        if tenant_id == "global":
            return False
        removed = self._tenants.pop(tenant_id, None)
        if removed:
            self._save()
        return removed is not None


tenant_manager = TenantManager()

__all__ = ["TenantManager", "Tenant", "tenant_manager"]


