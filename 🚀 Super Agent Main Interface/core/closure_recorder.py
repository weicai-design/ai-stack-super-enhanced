from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4


class ClosurePhase(str, Enum):
    ACCEPT = "accept"
    EXECUTE = "execute"
    CHECK = "check"
    FEEDBACK = "feedback"
    REEXECUTE = "reexecute"


@dataclass
class ClosureEventRecord:
    event_id: str
    phase: ClosurePhase
    status: str
    source: str
    task_id: Optional[str]
    module: Optional[str]
    timestamp: str
    metadata: Dict[str, Any]


class ClosureRecorder:
    """
    统一“接受→执行→检查→反馈→再执行”闭环事件记录器。

    - 通过 record() API 可手动记录闭环阶段
    - 通过 attach_to_event_bus() 可自动监听 LearningEventBus
    - 写入 artifacts/evidence/closure_events.jsonl，并维护摘要
    """

    PHASE_MAPPING = {
        "task_created": ClosurePhase.ACCEPT,
        "task_updated": ClosurePhase.CHECK,
        "task_blocked": ClosurePhase.FEEDBACK,
        "workflow_anomaly": ClosurePhase.FEEDBACK,
        "performance": ClosurePhase.CHECK,
    }

    def __init__(self, log_path: Optional[Path] = None):
        project_root = Path(__file__).resolve().parents[2]
        default_path = project_root / "artifacts" / "evidence" / "closure_events.jsonl"
        self.log_path = log_path or default_path
        self.summary_path = self.log_path.with_suffix(".summary.json")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._summary = {"total": 0, "by_phase": {}}
        if self.summary_path.exists():
            try:
                self._summary = json.loads(self.summary_path.read_text(encoding="utf-8"))
            except Exception:
                pass

    def record(
        self,
        phase: ClosurePhase,
        source: str,
        status: str = "success",
        task_id: Optional[str] = None,
        module: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ClosureEventRecord:
        record = ClosureEventRecord(
            event_id=f"closure_{uuid4()}",
            phase=phase,
            status=status,
            source=source,
            task_id=task_id,
            module=module,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {},
        )
        serialized = json.dumps(asdict(record), ensure_ascii=False)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as fp:
                fp.write(serialized + "\n")
            self._summary["total"] = self._summary.get("total", 0) + 1
            by_phase = self._summary.setdefault("by_phase", {})
            by_phase[phase.value] = by_phase.get(phase.value, 0) + 1
            self.summary_path.write_text(json.dumps(self._summary, ensure_ascii=False, indent=2), encoding="utf-8")
        return record

    def attach_to_event_bus(self, event_bus) -> None:
        if not event_bus:
            return

        def _handler(event):
            try:
                phase = self.PHASE_MAPPING.get(event.event_type.value)
                if not phase:
                    return
                self.record(
                    phase=phase,
                    source=f"event_bus::{event.source}",
                    status=event.severity,
                    task_id=event.payload.get("task_id") if isinstance(event.payload, dict) else None,
                    module=event.payload.get("module") if isinstance(event.payload, dict) else None,
                    metadata={"event_id": event.event_id, "payload": event.payload},
                )
            except Exception as exc:  # noqa: BLE001
                print(f"[ClosureRecorder] event bus hook failed: {exc}")

        event_bus.subscribe(_handler)


