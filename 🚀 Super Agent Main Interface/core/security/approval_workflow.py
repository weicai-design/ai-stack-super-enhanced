from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ..database_persistence import DatabasePersistence, get_persistence
from .audit_pipeline import SecurityAuditPipeline, get_audit_pipeline


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class SensitiveOperationRequestModel:
    approval_id: str
    applicant: str
    operation: str
    justification: str
    status: ApprovalStatus
    created_at: str
    updated_at: str
    reviewer: Optional[str] = None
    decision_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SensitiveOperationApprovalManager:
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        audit_pipeline: Optional[SecurityAuditPipeline] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.audit_pipeline = audit_pipeline or get_audit_pipeline()
        self.table_name = "security_sensitive_ops"

    def _persist(self, data: Dict[str, Any], record_id: Optional[str] = None) -> str:
        return self.persistence.save(
            table_name=self.table_name,
            data=data,
            record_id=record_id,
            metadata={"status": data.get("status")},
        )

    def _serialize_model(self, model: SensitiveOperationRequestModel) -> Dict[str, Any]:
        data = model.__dict__.copy()
        data["status"] = model.status.value
        return data

    def submit_request(
        self,
        applicant: str,
        operation: str,
        justification: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SensitiveOperationRequestModel:
        approval_id = f"approval_{uuid4()}"
        now = datetime.utcnow().isoformat() + "Z"
        model = SensitiveOperationRequestModel(
            approval_id=approval_id,
            applicant=applicant,
            operation=operation,
            justification=justification,
            status=ApprovalStatus.PENDING,
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        self._persist(self._serialize_model(model), record_id=approval_id)
        if self.audit_pipeline:
            self.audit_pipeline.log_security_event(
                event_type="sensitive_operation.requested",
                source="approval_manager",
                severity="info",
                metadata=self._serialize_model(model),
            )
        return model

    def _update_status(
        self,
        approval_id: str,
        status: ApprovalStatus,
        reviewer: str,
        reason: Optional[str],
    ) -> Optional[SensitiveOperationRequestModel]:
        model = self.get_request(approval_id)
        if not model:
            return None
        if model.status != ApprovalStatus.PENDING:
            return model
        model.status = status
        model.reviewer = reviewer
        model.updated_at = datetime.utcnow().isoformat() + "Z"
        model.decision_reason = reason
        self._persist(self._serialize_model(model), record_id=approval_id)
        if self.audit_pipeline:
            self.audit_pipeline.log_security_event(
                event_type=f"sensitive_operation.{status.value}",
                source="approval_manager",
                severity="warning" if status == ApprovalStatus.REJECTED else "info",
                metadata=self._serialize_model(model),
            )
        return model

    def approve(self, approval_id: str, reviewer: str, reason: Optional[str] = None) -> Optional[SensitiveOperationRequestModel]:
        return self._update_status(approval_id, ApprovalStatus.APPROVED, reviewer, reason)

    def reject(self, approval_id: str, reviewer: str, reason: Optional[str] = None) -> Optional[SensitiveOperationRequestModel]:
        return self._update_status(approval_id, ApprovalStatus.REJECTED, reviewer, reason)

    def get_request(self, approval_id: str) -> Optional[SensitiveOperationRequestModel]:
        record = self.persistence.load(self.table_name, approval_id)
        if not record:
            return None
        record["status"] = ApprovalStatus(record.get("status", ApprovalStatus.PENDING.value))
        return SensitiveOperationRequestModel(**record)

    def list_requests(self, status: Optional[ApprovalStatus] = None, limit: int = 100) -> List[Dict[str, Any]]:
        filters = {"status": status.value} if status else None
        rows = self.persistence.query(
            table_name=self.table_name,
            filters=filters,
            limit=limit,
            order_by="_created_at",
            order_desc=True,
        )
        return rows


_approval_manager: Optional[SensitiveOperationApprovalManager] = None


def get_approval_manager() -> SensitiveOperationApprovalManager:
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = SensitiveOperationApprovalManager()
    return _approval_manager


