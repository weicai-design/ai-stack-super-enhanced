"""
Dual-channel export manager
结合数据导出器与ERP监听器，支持
1) 事件驱动自动导出（监听通道）
2) 快照/轮询导出（被动通道）
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.data_exporter import DataExporter
from core.data_listener import ERPDataListener, EventType, ERPEvent

logger = logging.getLogger(__name__)


@dataclass
class EventChannelConfig:
    channel_id: str
    event_type: EventType
    format: str = "excel"
    fields: Optional[List[str]] = None
    destination: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    total_exports: int = 0


@dataclass
class SnapshotChannelConfig:
    channel_id: str
    name: str
    format: str = "excel"
    endpoint: Optional[str] = None
    static_data: Optional[List[Dict[str, Any]]] = None
    destination: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    total_exports: int = 0


class DualChannelExportManager:
    """桥接数据监听与导出"""

    def __init__(self, listener: ERPDataListener, exporter: DataExporter):
        self.listener = listener
        self.exporter = exporter
        self.event_channels: Dict[str, EventChannelConfig] = {}
        self.snapshot_channels: Dict[str, SnapshotChannelConfig] = {}
        self._handler_refs: Dict[str, Any] = {}

    async def register_event_channel(self, payload: Dict[str, Any]) -> EventChannelConfig:
        event_type = EventType(payload["event_type"])
        channel_id = f"evt-{uuid.uuid4().hex[:8]}"
        config = EventChannelConfig(
            channel_id=channel_id,
            event_type=event_type,
            format=payload.get("format", "excel"),
            fields=payload.get("fields"),
            destination=payload.get("destination", {}),
            description=payload.get("description"),
        )

        async def handler(event: ERPEvent):
            await self._handle_event_export(config, event)

        self.listener.register_handler(event_type, handler, priority=payload.get("priority", 0))
        self._handler_refs[channel_id] = handler
        self.event_channels[channel_id] = config
        logger.info("注册监听导出通道 %s -> %s", channel_id, event_type.value)
        return config

    async def _handle_event_export(self, config: EventChannelConfig, event: ERPEvent):
        dataset = self._build_dataset_from_event(event, config.fields)
        if not dataset:
            logger.warning("事件缺少数据，跳过导出: %s", event.entity_id)
            return
        payload_bytes, meta = await self._export_dataset(dataset, config.format, f"{event.event_type.value} Report")
        await self._deliver_payload(payload_bytes, config.destination, meta)
        config.last_triggered = datetime.now()
        config.total_exports += 1

    def _build_dataset_from_event(self, event: ERPEvent, fields: Optional[List[str]]) -> List[Dict[str, Any]]:
        record = event.new_data or event.old_data or {}
        if fields:
            record = {field: record.get(field) for field in fields}
        enriched = {
            **record,
            "_event_type": event.event_type.value,
            "_entity": event.entity_type,
            "_entity_id": event.entity_id,
            "_timestamp": event.timestamp.isoformat(),
        }
        return [enriched]

    async def register_snapshot_channel(self, payload: Dict[str, Any]) -> SnapshotChannelConfig:
        channel_id = f"snap-{uuid.uuid4().hex[:8]}"
        config = SnapshotChannelConfig(
            channel_id=channel_id,
            name=payload.get("name", channel_id),
            format=payload.get("format", "excel"),
            endpoint=payload.get("endpoint"),
            static_data=payload.get("static_data"),
            destination=payload.get("destination", {}),
            schedule=payload.get("schedule"),
        )
        self.snapshot_channels[channel_id] = config
        logger.info("注册快照导出通道 %s", channel_id)
        return config

    async def trigger_snapshot(self, channel_id: str) -> Dict[str, Any]:
        config = self.snapshot_channels.get(channel_id)
        if not config:
            raise ValueError("未找到快照通道")

        data = await self._load_snapshot_data(config)
        if not data:
            raise ValueError("数据为空，无法导出")

        payload_bytes, meta = await self._export_dataset(data, config.format, config.name)
        await self._deliver_payload(payload_bytes, config.destination, meta)
        config.last_triggered = datetime.now()
        config.total_exports += 1
        return {"success": True, "channel_id": channel_id, "count": len(data)}

    async def _load_snapshot_data(self, config: SnapshotChannelConfig) -> List[Dict[str, Any]]:
        if config.static_data:
            return config.static_data

        if config.endpoint:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.get(config.endpoint)
                    resp.raise_for_status()
                    data = resp.json()
                    if isinstance(data, dict):
                        # 允许 {"items": [...] }
                        if "data" in data and isinstance(data["data"], list):
                            return data["data"]
                        if "items" in data and isinstance(data["items"], list):
                            return data["items"]
                        return [data]
                    return data
            except Exception as exc:
                logger.error("加载快照数据失败: %s", exc, exc_info=True)
                raise
        return []

    async def _export_dataset(self, data: List[Dict[str, Any]], fmt: str, title: str):
        fmt = fmt.lower()
        if fmt == "excel":
            content = await self.exporter.export_to_excel(data, title=title)
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            extension = ".xlsx"
        elif fmt == "csv":
            content = await self.exporter.export_to_csv(data)
            media_type = "text/csv"
            extension = ".csv"
        elif fmt == "pdf":
            content = await self.exporter.export_to_pdf(data, title=title)
            media_type = "text/html"
            extension = ".html"
        else:
            content = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            media_type = "application/json"
            extension = ".json"

        filename = f"erp_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
        return content, {"media_type": media_type, "filename": filename}

    async def _deliver_payload(self, payload: bytes, destination: Dict[str, Any], meta: Dict[str, Any]):
        dest_type = (destination or {}).get("type", "local_file")
        if dest_type == "webhook":
            url = destination.get("url")
            if not url:
                raise ValueError("Webhook目标缺少URL")
            await self._post_webhook(url, payload, meta)
        else:
            path = destination.get("path") or self._default_export_path(meta["filename"])
            await self._write_file(path, payload)

    async def _post_webhook(self, url: str, payload: bytes, meta: Dict[str, Any]):
        try:
            import httpx

            encoded = base64.b64encode(payload).decode("utf-8")
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    url,
                    json={
                        "filename": meta["filename"],
                        "media_type": meta["media_type"],
                        "content_b64": encoded,
                        "generated_at": datetime.now().isoformat(),
                    },
                )
                resp.raise_for_status()
        except Exception as exc:
            logger.error("Webhook推送失败: %s", exc, exc_info=True)
            raise

    async def _write_file(self, path: str, payload: bytes):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: open(path, "wb").write(payload))
        logger.info("导出文件写入: %s", path)

    def _default_export_path(self, filename: str) -> str:
        base = os.getenv("ERP_EXPORT_DIR") or (os.getcwd() + "/exports")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, filename)

    def get_status(self) -> Dict[str, Any]:
        return {
            "event_channels": [
                {
                    "channel_id": c.channel_id,
                    "event_type": c.event_type.value,
                    "format": c.format,
                    "destination": c.destination,
                    "description": c.description,
                    "total_exports": c.total_exports,
                    "last_triggered": c.last_triggered.isoformat() if c.last_triggered else None,
                }
                for c in self.event_channels.values()
            ],
            "snapshot_channels": [
                {
                    "channel_id": c.channel_id,
                    "name": c.name,
                    "format": c.format,
                    "destination": c.destination,
                    "schedule": c.schedule,
                    "total_exports": c.total_exports,
                    "last_triggered": c.last_triggered.isoformat() if c.last_triggered else None,
                }
                for c in self.snapshot_channels.values()
            ],
        }

