#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Persistence Seeder

确保关键模块的初始数据自动写入 persistence 数据库，实现“冷启动即可查询”的能力。
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SeedDefinition:
    module: str
    type_field: Optional[str]
    type_value: Optional[Any]
    records: List[Dict[str, Any]]
    record_id_field: Optional[str] = None
    order_by: Optional[str] = None


class PersistenceSeeder:
    def __init__(self, data_service):
        self.data_service = data_service
        self._definitions: Dict[str, SeedDefinition] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._seeded: set[str] = set()

    def register_seed(
        self,
        key: str,
        *,
        module: str,
        type_field: Optional[str],
        type_value: Optional[Any],
        records: List[Dict[str, Any]],
        record_id_field: Optional[str] = None,
    ) -> None:
        self._definitions[key] = SeedDefinition(
            module=module,
            type_field=type_field,
            type_value=type_value,
            records=records,
            record_id_field=record_id_field,
        )
        self._locks[key] = asyncio.Lock()

    async def ensure_seed(self, key: str) -> None:
        if key in self._seeded:
            return
        definition = self._definitions.get(key)
        if not definition:
            raise KeyError(f"未注册的 seed: {key}")

        async with self._locks[key]:
            if key in self._seeded:
                return
            filters = {}
            if definition.type_field and definition.type_value is not None:
                filters[definition.type_field] = definition.type_value
            existing = await self.data_service.count_data(definition.module, filters if filters else None)
            if existing > 0:
                self._seeded.add(key)
                return

            for record in definition.records:
                payload = dict(record)
                if definition.type_field and definition.type_value is not None:
                    payload.setdefault(definition.type_field, definition.type_value)
                record_id = None
                if definition.record_id_field:
                    record_id = payload.get(definition.record_id_field)
                await self.data_service.save_data(
                    module=definition.module,
                    data=payload,
                    record_id=record_id,
                    metadata={"seed_key": key},
                    sync=False,
                )
            self._seeded.add(key)

    async def get_records(
        self,
        key: str,
        *,
        limit: int = 500,
        extra_filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = False,
    ) -> List[Dict[str, Any]]:
        await self.ensure_seed(key)
        definition = self._definitions[key]
        filters = {}
        if definition.type_field and definition.type_value is not None:
            filters[definition.type_field] = definition.type_value
        if extra_filters:
            filters.update(extra_filters)
        return await self.data_service.query_data(
            module=definition.module,
            filters=filters or None,
            limit=limit,
            order_by=order_by,
            order_desc=order_desc,
        )


__all__ = ["PersistenceSeeder"]


