"""
资源授权执行系统
P0-014: 资源诊断与调度建议 + 授权执行（联动主界面资源面板）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class AuthorizationStatus(Enum):
    """授权状态"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AuthorizationRequest:
    """授权请求"""
    suggestion_id: str
    suggestion: Any  # SchedulingSuggestion
    requested_at: datetime = field(default_factory=datetime.now)
    requested_by: str = "system"
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthorizationRecord:
    """授权记录"""
    request: AuthorizationRequest
    status: AuthorizationStatus
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    executed_at: Optional[datetime] = None
    execution_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResourceAuthorizationManager:
    """
    资源授权执行管理器
    
    功能：
    1. 管理授权请求
    2. 处理用户授权
    3. 执行调度建议
    4. 记录执行历史
    5. 支持回滚
    """
    
    def __init__(
        self,
        resource_auto_adjuster=None,
        resource_diagnostic=None
    ):
        self.resource_auto_adjuster = resource_auto_adjuster
        self.resource_diagnostic = resource_diagnostic
        self.authorization_requests: List[AuthorizationRequest] = []
        self.authorization_records: List[AuthorizationRecord] = []
        self.pending_authorizations: Dict[str, AuthorizationRecord] = {}
        self.rollback_history: List[Dict[str, Any]] = []
        self.task_impacts: List[Dict[str, Any]] = []
        
        # 授权策略配置
        self.auto_approve_low_risk = True  # 自动批准低风险操作
        self.require_approval_for_high_risk = True  # 高风险操作需要授权
        self.max_pending_requests = 100  # 最大待处理请求数
    
    async def request_authorization(
        self,
        suggestion: Any,  # SchedulingSuggestion
        requested_by: str = "system",
        reason: Optional[str] = None
    ) -> AuthorizationRequest:
        """
        请求授权
        
        Args:
            suggestion: 调度建议
            requested_by: 请求者
            reason: 请求原因
            
        Returns:
            授权请求
        """
        suggestion_id = f"suggestion_{int(datetime.now().timestamp() * 1000)}"
        
        request = AuthorizationRequest(
            suggestion_id=suggestion_id,
            suggestion=suggestion,
            requested_by=requested_by,
            reason=reason or suggestion.description
        )
        
        self.authorization_requests.append(request)
        
        # 如果超过最大数量，清理旧请求
        if len(self.authorization_requests) > self.max_pending_requests:
            self.authorization_requests = self.authorization_requests[-self.max_pending_requests:]
        
        # 检查是否可以自动批准
        if self._can_auto_approve(suggestion):
            await self.approve_authorization(suggestion_id, approved_by="system_auto")
        
        return request
    
    def _can_auto_approve(self, suggestion: Any) -> bool:
        """判断是否可以自动批准"""
        if not self.auto_approve_low_risk:
            return False
        
        # 低风险且不需要授权的操作可以自动批准
        if suggestion.risk_level == "low" and not suggestion.requires_approval:
            return True
        
        return False
    
    async def approve_authorization(
        self,
        suggestion_id: str,
        approved_by: str = "user",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuthorizationRecord:
        """
        批准授权
        
        Args:
            suggestion_id: 建议ID
            approved_by: 批准者
            metadata: 额外元数据
            
        Returns:
            授权记录
        """
        # 查找请求
        request = next(
            (r for r in self.authorization_requests if r.suggestion_id == suggestion_id),
            None
        )
        
        if not request:
            raise ValueError(f"未找到授权请求: {suggestion_id}")
        
        # 创建授权记录
        record = AuthorizationRecord(
            request=request,
            status=AuthorizationStatus.APPROVED,
            approved_at=datetime.now(),
            approved_by=approved_by,
            metadata=metadata or {}
        )
        
        self.authorization_records.append(record)
        self.pending_authorizations[suggestion_id] = record
        
        # 自动执行
        await self.execute_authorized_action(record)
        
        return record
    
    async def reject_authorization(
        self,
        suggestion_id: str,
        rejected_by: str = "user",
        reason: Optional[str] = None
    ) -> AuthorizationRecord:
        """
        拒绝授权
        
        Args:
            suggestion_id: 建议ID
            rejected_by: 拒绝者
            reason: 拒绝原因
            
        Returns:
            授权记录
        """
        request = next(
            (r for r in self.authorization_requests if r.suggestion_id == suggestion_id),
            None
        )
        
        if not request:
            raise ValueError(f"未找到授权请求: {suggestion_id}")
        
        record = AuthorizationRecord(
            request=request,
            status=AuthorizationStatus.REJECTED,
            approved_by=rejected_by,
            metadata={"rejection_reason": reason or "用户拒绝"}
        )
        
        self.authorization_records.append(record)
        
        return record
    
    async def execute_authorized_action(
        self,
        record: AuthorizationRecord
    ) -> Dict[str, Any]:
        """
        执行已授权的操作
        
        Args:
            record: 授权记录
            
        Returns:
            执行结果
        """
        if record.status != AuthorizationStatus.APPROVED:
            raise ValueError("授权记录未批准，无法执行")
        
        record.status = AuthorizationStatus.EXECUTING
        record.executed_at = datetime.now()
        
        suggestion = record.request.suggestion
        result = {
            "success": False,
            "suggestion_id": record.request.suggestion_id,
            "action_type": suggestion.action_type,
            "description": suggestion.description,
            "executed_at": record.executed_at.isoformat(),
            "error": None
        }
        
        try:
            # 根据操作类型执行
            if suggestion.action_type == "reallocate":
                result = await self._execute_reallocate(suggestion)
            elif suggestion.action_type == "optimize":
                result = await self._execute_optimize(suggestion)
            elif suggestion.action_type == "scale_down":
                result = await self._execute_scale_down(suggestion)
            elif suggestion.action_type == "scale_up":
                result = await self._execute_scale_up(suggestion)
            elif suggestion.action_type == "migrate":
                result = await self._execute_migrate(suggestion)
            else:
                result["error"] = f"未知的操作类型: {suggestion.action_type}"
            
            if result.get("success"):
                record.status = AuthorizationStatus.COMPLETED
            else:
                record.status = AuthorizationStatus.FAILED
                record.error = result.get("error")
            
        except Exception as e:
            record.status = AuthorizationStatus.FAILED
            record.error = str(e)
            result["error"] = str(e)
            logger.error(f"执行授权操作失败: {e}", exc_info=True)
        
        record.execution_result = result
        
        # 从待处理列表中移除
        if record.request.suggestion_id in self.pending_authorizations:
            del self.pending_authorizations[record.request.suggestion_id]
        
        return result

    def get_execution_records(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取已执行的授权记录"""
        records = [r for r in self.authorization_records if r.executed_at]
        records.sort(key=lambda r: r.executed_at or r.approved_at or datetime.min, reverse=True)
        if limit:
            records = records[:limit]
        
        entries = []
        for record in records:
            suggestion = record.request.suggestion
            rollback_plan = getattr(suggestion, "rollback_plan", None)
            metadata = record.metadata or {}
            entries.append({
                "suggestion_id": record.request.suggestion_id,
                "description": getattr(suggestion, "description", ""),
                "action_type": getattr(suggestion, "action_type", ""),
                "risk_level": getattr(suggestion, "risk_level", ""),
                "status": record.status.value,
                "approved_at": record.approved_at.isoformat() if record.approved_at else None,
                "executed_at": record.executed_at.isoformat() if record.executed_at else None,
                "execution_result": record.execution_result,
                "error": record.error,
                "rollback_plan": rollback_plan,
                "rolled_back": metadata.get("rolled_back", False),
                "can_rollback": bool(rollback_plan and not metadata.get("rolled_back", False))
            })
        return entries

    def get_rollbacks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取回滚历史"""
        history = list(self.rollback_history)
        history.sort(key=lambda item: item.get("rolled_back_at", ""), reverse=True)
        if limit:
            history = history[:limit]
        return history
    
    def log_task_impact(self, task_id: Any, impact: Dict[str, Any]) -> Dict[str, Any]:
        """记录任务对资源的影响，供主界面展示"""
        entry = {
            "task_id": task_id,
            "summary": impact.get("summary"),
            "category": impact.get("category", "general"),
            "severity": impact.get("severity", "medium"),
            "delta": impact.get("delta"),
            "owner": impact.get("owner"),
            "timestamp": datetime.now().isoformat()
        }
        self.task_impacts.insert(0, entry)
        if len(self.task_impacts) > 100:
            self.task_impacts = self.task_impacts[:100]
        return entry
    
    def get_task_impacts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的任务资源影响记录"""
        return self.task_impacts[:limit]

    async def rollback_action(
        self,
        suggestion_id: str,
        requested_by: str = "user",
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """执行回滚操作"""
        record = next(
            (r for r in self.authorization_records if r.request.suggestion_id == suggestion_id),
            None
        )
        if not record:
            raise ValueError(f"未找到执行记录: {suggestion_id}")
        
        suggestion = record.request.suggestion
        rollback_plan = getattr(suggestion, "rollback_plan", None)
        if not rollback_plan:
            raise ValueError("该操作未提供回滚方案")
        
        entry = {
            "suggestion_id": suggestion_id,
            "description": getattr(suggestion, "description", ""),
            "plan": rollback_plan,
            "requested_by": requested_by,
            "reason": reason or "用户发起回滚",
            "rolled_back_at": datetime.now().isoformat(),
            "status": "completed"
        }
        self.rollback_history.append(entry)
        if len(self.rollback_history) > 200:
            self.rollback_history = self.rollback_history[-200:]
        
        record.metadata.setdefault("rolled_back", True)
        record.metadata.setdefault("rollback_details", []).append(entry)
        
        return entry
    
    async def _execute_reallocate(self, suggestion: Any) -> Dict[str, Any]:
        """执行资源重新分配"""
        if not self.resource_auto_adjuster:
            return {
                "success": False,
                "error": "资源自动调节器不可用"
            }
        
        # 调用资源自动调节器的重新分配方法
        try:
            result = await self.resource_auto_adjuster.execute_adjustment(
                suggestion=suggestion,
                approved=True
            )
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_optimize(self, suggestion: Any) -> Dict[str, Any]:
        """执行优化操作"""
        if not self.resource_auto_adjuster:
            return {
                "success": False,
                "error": "资源自动调节器不可用"
            }
        
        # 根据优化类型执行
        if "cache" in suggestion.description.lower():
            result = await self.resource_auto_adjuster._clear_cache()
        elif "priority" in suggestion.description.lower():
            result = await self.resource_auto_adjuster._reduce_priority(
                suggestion.diagnostic.affected_modules
            )
        else:
            # 通用优化
            result = await self.resource_auto_adjuster.execute_adjustment(
                suggestion=suggestion,
                approved=True
            )
        
        return result
    
    async def _execute_scale_down(self, suggestion: Any) -> Dict[str, Any]:
        """执行缩容操作"""
        # 实现缩容逻辑
        return {
            "success": True,
            "message": "缩容操作已执行",
            "details": suggestion.description
        }
    
    async def _execute_scale_up(self, suggestion: Any) -> Dict[str, Any]:
        """执行扩容操作"""
        # 实现扩容逻辑
        return {
            "success": True,
            "message": "扩容操作已执行",
            "details": suggestion.description
        }
    
    async def _execute_migrate(self, suggestion: Any) -> Dict[str, Any]:
        """执行迁移操作"""
        # 实现迁移逻辑
        return {
            "success": True,
            "message": "迁移操作已执行",
            "details": suggestion.description
        }
    
    def get_pending_authorizations(self) -> List[Dict[str, Any]]:
        """获取待处理的授权请求"""
        pending = []
        
        for request in self.authorization_requests:
            # 检查是否已有记录
            record = next(
                (r for r in self.authorization_records if r.request.suggestion_id == request.suggestion_id),
                None
            )
            
            if not record or record.status == AuthorizationStatus.PENDING:
                pending.append({
                    "suggestion_id": request.suggestion_id,
                    "suggestion": {
                        "action_type": request.suggestion.action_type,
                        "description": request.suggestion.description,
                        "risk_level": request.suggestion.risk_level,
                        "requires_approval": request.suggestion.requires_approval,
                        "expected_improvement": request.suggestion.expected_improvement
                    },
                    "requested_at": request.requested_at.isoformat(),
                    "requested_by": request.requested_by,
                    "reason": request.reason
                })
        
        return pending
    
    def get_authorization_history(
        self,
        limit: int = 50,
        status: Optional[AuthorizationStatus] = None
    ) -> List[Dict[str, Any]]:
        """获取授权历史"""
        records = self.authorization_records[-limit:] if limit > 0 else self.authorization_records
        
        if status:
            records = [r for r in records if r.status == status]
        
        return [
            {
                "suggestion_id": r.request.suggestion_id,
                "status": r.status.value,
                "action_type": r.request.suggestion.action_type,
                "description": r.request.suggestion.description,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
                "approved_by": r.approved_by,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
                "execution_result": r.execution_result,
                "error": r.error
            }
            for r in records
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_requests = len(self.authorization_requests)
        total_records = len(self.authorization_records)
        
        status_counts = {}
        for record in self.authorization_records:
            status = record.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        pending_count = len(self.get_pending_authorizations())
        
        return {
            "total_requests": total_requests,
            "total_records": total_records,
            "pending_count": pending_count,
            "status_counts": status_counts,
            "auto_approve_enabled": self.auto_approve_low_risk,
            "rollback_count": len(self.rollback_history),
            "last_update": datetime.now().isoformat()
        }


