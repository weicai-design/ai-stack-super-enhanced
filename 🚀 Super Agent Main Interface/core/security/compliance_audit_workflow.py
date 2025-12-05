#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规审计工作流
P1-204: 支持审批与回溯的审计流程
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import asyncio

from ..database_persistence import DatabasePersistence, get_persistence
from .audit_pipeline import SecurityAuditPipeline, get_audit_pipeline
from .approval_workflow import SensitiveOperationApprovalManager, get_approval_manager, ApprovalStatus
from .compliance_policy_manager import (
    CompliancePolicyManager,
    get_compliance_manager,
    OperationType,
    RiskLevel,
    ComplianceCheckResult,
)

logger = logging.getLogger(__name__)


class AuditStatus(str, Enum):
    """审计状态"""
    PENDING = "pending"  # 待审批
    APPROVED = "approved"  # 已批准
    REJECTED = "rejected"  # 已拒绝
    EXECUTED = "executed"  # 已执行
    FAILED = "failed"  # 执行失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class ComplianceAuditRecord:
    """合规审计记录"""
    audit_id: str
    operation_type: OperationType
    operation: str
    actor: str
    status: AuditStatus
    risk_level: RiskLevel
    compliance_check_result: ComplianceCheckResult
    approval_id: Optional[str] = None
    approver: Optional[str] = None
    approval_time: Optional[str] = None
    execution_time: Optional[str] = None
    execution_result: Optional[Dict[str, Any]] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data["operation_type"] = self.operation_type.value
        data["status"] = self.status.value
        data["risk_level"] = self.risk_level.value
        data["compliance_check_result"] = self.compliance_check_result.to_dict()
        return data


class ComplianceAuditWorkflow:
    """
    合规审计工作流
    
    功能：
    1. 执行合规检查
    2. 触发审批流程
    3. 记录审计日志
    4. 支持回溯查询
    5. 执行后验证
    """
    
    def __init__(
        self,
        compliance_manager: Optional[CompliancePolicyManager] = None,
        approval_manager: Optional[SensitiveOperationApprovalManager] = None,
        audit_pipeline: Optional[SecurityAuditPipeline] = None,
        persistence: Optional[DatabasePersistence] = None,
    ):
        self.compliance_manager = compliance_manager or get_compliance_manager()
        self.approval_manager = approval_manager or get_approval_manager()
        self.audit_pipeline = audit_pipeline or get_audit_pipeline()
        self.persistence = persistence or get_persistence()
        
        self.table_name = "compliance_audit_workflow"
        
        # 审计记录缓存
        self.audit_records: Dict[str, ComplianceAuditRecord] = {}
        
        logger.info("合规审计工作流初始化完成")
    
    async def execute_with_audit(
        self,
        operation_type: OperationType,
        operation: str,
        actor: str,
        executor: Optional[callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行操作并记录审计
        
        Args:
            operation_type: 操作类型
            operation: 操作内容
            actor: 执行者
            executor: 执行函数（可选）
            metadata: 元数据
            
        Returns:
            执行结果字典，包含状态和详细信息
        """
        audit_id = f"audit_{uuid4()}"
        metadata = metadata or {}
        
        # 1. 执行合规检查
        check_result = self._perform_compliance_check(operation_type, operation, actor, metadata)
        
        # 2. 创建并保存审计记录
        audit_record = self._create_audit_record(audit_id, operation_type, operation, actor, check_result, metadata)
        
        # 3. 处理审批需求
        if check_result.requires_approval:
            return self._handle_approval_required(audit_id, check_result)
        
        # 4. 处理操作阻止
        if not check_result.allowed:
            return self._handle_operation_blocked(audit_record, check_result)
        
        # 5. 执行操作（如果有执行器）
        if executor:
            return await self._execute_operation(audit_record, executor, operation, metadata)
        
        # 6. 无执行器的直接批准
        return self._handle_approved_without_execution(audit_record)
    
    def _perform_compliance_check(
        self,
        operation_type: OperationType,
        operation: str,
        actor: str,
        metadata: Dict[str, Any],
    ) -> ComplianceCheckResult:
        """执行合规检查"""
        return self.compliance_manager.check_compliance(
            operation_type=operation_type,
            operation=operation,
            actor=actor,
            metadata=metadata,
        )
    
    def _create_audit_record(
        self,
        audit_id: str,
        operation_type: OperationType,
        operation: str,
        actor: str,
        check_result: ComplianceCheckResult,
        metadata: Dict[str, Any],
    ) -> ComplianceAuditRecord:
        """创建审计记录"""
        status = AuditStatus.PENDING if check_result.requires_approval else AuditStatus.APPROVED
        
        audit_record = ComplianceAuditRecord(
            audit_id=audit_id,
            operation_type=operation_type,
            operation=operation,
            actor=actor,
            status=status,
            risk_level=check_result.risk_level,
            compliance_check_result=check_result,
            approval_id=check_result.approval_id,
            metadata=metadata,
        )
        
        self.audit_records[audit_id] = audit_record
        self._persist_audit_record(audit_record)
        
        return audit_record
    
    def _handle_approval_required(self, audit_id: str, check_result: ComplianceCheckResult) -> Dict[str, Any]:
        """处理需要审批的情况"""
        return {
            "success": False,
            "audit_id": audit_id,
            "status": "pending_approval",
            "approval_id": check_result.approval_id,
            "message": "操作需要审批，请等待审批结果",
            "check_result": check_result.to_dict(),
        }
    
    def _handle_operation_blocked(self, audit_record: ComplianceAuditRecord, check_result: ComplianceCheckResult) -> Dict[str, Any]:
        """处理操作被阻止的情况"""
        audit_record.status = AuditStatus.REJECTED
        audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
        self._persist_audit_record(audit_record)
        
        return {
            "success": False,
            "audit_id": audit_record.audit_id,
            "status": "blocked",
            "message": "操作被合规策略阻止",
            "reasons": check_result.reasons,
            "check_result": check_result.to_dict(),
        }
    
    async def _execute_operation(
        self,
        audit_record: ComplianceAuditRecord,
        executor: callable,
        operation: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """执行操作并记录结果"""
        try:
            start_time = datetime.utcnow()
            
            # 执行操作
            if asyncio.iscoroutinefunction(executor):
                execution_result = await executor(operation, metadata)
            else:
                execution_result = executor(operation, metadata)
            
            execution_time = datetime.utcnow()
            
            # 更新审计记录
            audit_record.status = AuditStatus.EXECUTED
            audit_record.execution_time = execution_time.isoformat() + "Z"
            audit_record.execution_result = {
                "success": True,
                "result": execution_result,
                "duration_ms": (execution_time - start_time).total_seconds() * 1000,
            }
            audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
            self._persist_audit_record(audit_record)
            
            return {
                "success": True,
                "audit_id": audit_record.audit_id,
                "status": "executed",
                "result": execution_result,
                "duration_ms": (execution_time - start_time).total_seconds() * 1000,
            }
            
        except Exception as e:
            logger.error(f"操作执行失败: {e}", exc_info=True)
            audit_record.status = AuditStatus.FAILED
            audit_record.execution_result = {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
            }
            audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
            self._persist_audit_record(audit_record)
            
            return {
                "success": False,
                "audit_id": audit_record.audit_id,
                "status": "failed",
                "error": str(e),
                "error_type": type(e).__name__,
            }
    
    def _handle_approved_without_execution(self, audit_record: ComplianceAuditRecord) -> Dict[str, Any]:
        """处理无执行器的直接批准情况"""
        audit_record.status = AuditStatus.APPROVED
        audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
        self._persist_audit_record(audit_record)
        
        return {
            "success": True,
            "audit_id": audit_record.audit_id,
            "status": "approved",
            "message": "操作已批准，无需执行",
        }
                audit_record.execution_result = {
                    "success": False,
                    "error": str(e),
                }
                execution_result = {"success": False, "error": str(e)}
        else:
            # 没有执行器，只记录审计
            audit_record.status = AuditStatus.APPROVED
            execution_result = {"success": True, "message": "已通过合规检查，但未执行操作"}
        
        audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
        self._persist_audit_record(audit_record)
        
        # 6. 记录审计日志
        self._log_audit_event(audit_record)
        
        return {
            "success": True,
            "audit_id": audit_id,
            "status": audit_record.status.value,
            "execution_result": execution_result,
            "check_result": check_result.to_dict(),
        }
    
    async def approve_and_execute(
        self,
        approval_id: str,
        approver: str,
        executor: Optional[callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        审批并执行操作
        
        Args:
            approval_id: 审批ID
            approver: 审批人
            executor: 执行函数
            metadata: 元数据
            
        Returns:
            执行结果
        """
        # 1. 获取审批请求
        approval = self.approval_manager.get_request(approval_id)
        if not approval:
            return {"success": False, "error": "审批请求不存在"}
        
        if approval.status != ApprovalStatus.PENDING:
            return {"success": False, "error": f"审批已处理: {approval.status.value}"}
        
        # 2. 批准请求
        approved = self.approval_manager.approve(approval_id, approver, "已批准执行")
        if not approved:
            return {"success": False, "error": "审批失败"}
        
        # 3. 查找对应的审计记录
        audit_record = None
        for record in self.audit_records.values():
            if record.approval_id == approval_id:
                audit_record = record
                break
        
        if not audit_record:
            # 从持久化中查找
            records = self.persistence.query(
                table_name=self.table_name,
                filters={"approval_id": approval_id},
                limit=1,
            )
            if records:
                record_data = records[0]
                audit_record = ComplianceAuditRecord(
                    audit_id=record_data.get("audit_id"),
                    operation_type=OperationType(record_data.get("operation_type")),
                    operation=record_data.get("operation"),
                    actor=record_data.get("actor"),
                    status=AuditStatus(record_data.get("status")),
                    risk_level=RiskLevel(record_data.get("risk_level")),
                    compliance_check_result=ComplianceCheckResult(**record_data.get("compliance_check_result", {})),
                    approval_id=approval_id,
                    metadata=record_data.get("metadata", {}),
                    created_at=record_data.get("created_at"),
                    updated_at=record_data.get("updated_at"),
                )
        
        if not audit_record:
            return {"success": False, "error": "审计记录不存在"}
        
        # 4. 更新审计记录
        audit_record.status = AuditStatus.APPROVED
        audit_record.approver = approver
        audit_record.approval_time = datetime.utcnow().isoformat() + "Z"
        audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 5. 执行操作
        execution_result = None
        if executor:
            try:
                start_time = datetime.utcnow()
                
                # 从审批元数据中获取操作信息
                operation = approval.metadata.get("operation", "")
                operation_type_str = approval.metadata.get("operation_type", "")
                
                if asyncio.iscoroutinefunction(executor):
                    execution_result = await executor(operation, metadata or {})
                else:
                    execution_result = executor(operation, metadata or {})
                
                execution_time = datetime.utcnow()
                
                audit_record.status = AuditStatus.EXECUTED
                audit_record.execution_time = execution_time.isoformat() + "Z"
                audit_record.execution_result = {
                    "success": True,
                    "result": execution_result,
                    "duration_ms": (execution_time - start_time).total_seconds() * 1000,
                }
                
            except Exception as e:
                logger.error(f"操作执行失败: {e}", exc_info=True)
                audit_record.status = AuditStatus.FAILED
                audit_record.execution_result = {
                    "success": False,
                    "error": str(e),
                }
                execution_result = {"success": False, "error": str(e)}
        else:
            audit_record.status = AuditStatus.APPROVED
            execution_result = {"success": True, "message": "已批准，但未执行操作"}
        
        audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
        self._persist_audit_record(audit_record)
        
        # 6. 记录审计日志
        self._log_audit_event(audit_record)
        
        return {
            "success": True,
            "audit_id": audit_record.audit_id,
            "approval_id": approval_id,
            "status": audit_record.status.value,
            "execution_result": execution_result,
        }
    
    def reject_operation(
        self,
        approval_id: str,
        approver: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        拒绝操作
        
        Args:
            approval_id: 审批ID
            approver: 审批人
            reason: 拒绝原因
            
        Returns:
            拒绝结果
        """
        # 1. 拒绝审批请求
        rejected = self.approval_manager.reject(approval_id, approver, reason)
        if not rejected:
            return {"success": False, "error": "拒绝失败"}
        
        # 2. 更新审计记录
        audit_record = None
        for record in self.audit_records.values():
            if record.approval_id == approval_id:
                audit_record = record
                break
        
        if not audit_record:
            # 从持久化中查找
            records = self.persistence.query(
                table_name=self.table_name,
                filters={"approval_id": approval_id},
                limit=1,
            )
            if records:
                record_data = records[0]
                audit_record = ComplianceAuditRecord(
                    audit_id=record_data.get("audit_id"),
                    operation_type=OperationType(record_data.get("operation_type")),
                    operation=record_data.get("operation"),
                    actor=record_data.get("actor"),
                    status=AuditStatus(record_data.get("status")),
                    risk_level=RiskLevel(record_data.get("risk_level")),
                    compliance_check_result=ComplianceCheckResult(**record_data.get("compliance_check_result", {})),
                    approval_id=approval_id,
                    metadata=record_data.get("metadata", {}),
                    created_at=record_data.get("created_at"),
                    updated_at=record_data.get("updated_at"),
                )
        
        if audit_record:
            audit_record.status = AuditStatus.REJECTED
            audit_record.approver = approver
            audit_record.approval_time = datetime.utcnow().isoformat() + "Z"
            audit_record.updated_at = datetime.utcnow().isoformat() + "Z"
            audit_record.metadata["rejection_reason"] = reason
            
            self._persist_audit_record(audit_record)
            self._log_audit_event(audit_record)
        
        return {
            "success": True,
            "approval_id": approval_id,
            "status": "rejected",
            "message": "操作已拒绝",
        }
    
    def query_audit_history(
        self,
        operation_type: Optional[OperationType] = None,
        actor: Optional[str] = None,
        status: Optional[AuditStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        查询审计历史（回溯）
        
        Args:
            operation_type: 操作类型
            actor: 执行者
            status: 状态
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
            
        Returns:
            审计历史列表
        """
        filters: Dict[str, Any] = {}
        
        if operation_type:
            filters["operation_type"] = operation_type.value
        if actor:
            filters["actor"] = actor
        if status:
            filters["status"] = status.value
        
        try:
            records = self.persistence.query(
                table_name=self.table_name,
                filters=filters or None,
                limit=limit,
                order_by="_created_at",
                order_desc=True,
            )
            
            # 转换为标准格式
            result = []
            for record in records:
                data = {k: v for k, v in record.items() if not k.startswith("_")}
                
                # 时间过滤
                if start_time or end_time:
                    timestamp_str = data.get("created_at", "")
                    if timestamp_str:
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            if start_time and timestamp < start_time:
                                continue
                            if end_time and timestamp > end_time:
                                continue
                        except Exception:
                            pass
                
                result.append(data)
            
            return result
        except Exception as e:
            logger.error(f"查询审计历史失败: {e}")
            return []
    
    def get_audit_record(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """获取审计记录"""
        # 从缓存中查找
        if audit_id in self.audit_records:
            return self.audit_records[audit_id].to_dict()
        
        # 从持久化中查找
        try:
            record = self.persistence.load(self.table_name, audit_id)
            if record:
                return {k: v for k, v in record.items() if not k.startswith("_")}
        except Exception as e:
            logger.error(f"获取审计记录失败: {e}")
        
        return None
    
    def _persist_audit_record(self, record: ComplianceAuditRecord):
        """持久化审计记录"""
        try:
            self.persistence.save(
                table_name=self.table_name,
                data=record.to_dict(),
                record_id=record.audit_id,
                metadata={
                    "operation_type": record.operation_type.value,
                    "status": record.status.value,
                    "risk_level": record.risk_level.value,
                },
            )
        except Exception as e:
            logger.error(f"审计记录持久化失败: {e}")
    
    def _log_audit_event(self, record: ComplianceAuditRecord):
        """记录审计事件"""
        if self.audit_pipeline:
            self.audit_pipeline.log_security_event(
                event_type=f"compliance_audit.{record.operation_type.value}",
                source="compliance_audit_workflow",
                severity="warning" if record.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] else "info",
                status=record.status.value,
                actor=record.actor,
                metadata=record.to_dict(),
            )


_compliance_audit_workflow: Optional[ComplianceAuditWorkflow] = None


def get_compliance_audit_workflow() -> ComplianceAuditWorkflow:
    """获取合规审计工作流实例"""
    global _compliance_audit_workflow
    if _compliance_audit_workflow is None:
        _compliance_audit_workflow = ComplianceAuditWorkflow()
    return _compliance_audit_workflow

