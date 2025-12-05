#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P2-003 · 专家协同完整实现

定义专家协同中枢，支持：
- 多专家联合会商会话
- 同步贡献与决策记录
- 协作指数、响应速度等量化指标
- 与 DataService 打通实现持久化与多租户隔离
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
import logging
import statistics
import uuid

from .data_service import DataService, get_data_service
from .unified_event_bus import (
    EventCategory,
    EventSeverity,
    get_unified_event_bus,
    UnifiedEventBus,
)


def _utc_now() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class ExpertContribution:
    timestamp: str
    expert_id: str
    expert_name: str
    channel: str
    summary: str
    action_items: List[str] = field(default_factory=list)
    impact_score: float = 0.5
    references: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborationDecision:
    decided_at: str
    owner: str
    summary: str
    kpis: List[str] = field(default_factory=list)
    followups: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollaborationSession:
    session_id: str
    topic: str
    initiator: str
    goals: List[str]
    experts: List[Dict[str, Any]]
    started_at: str
    status: str = "active"
    channel: str = "multi"
    contributions: List[ExpertContribution] = field(default_factory=list)
    decisions: List[CollaborationDecision] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "collaboration_session",
            "session_id": self.session_id,
            "topic": self.topic,
            "initiator": self.initiator,
            "goals": self.goals,
            "experts": self.experts,
            "started_at": self.started_at,
            "status": self.status,
            "channel": self.channel,
            "contributions": [c.to_dict() for c in self.contributions],
            "decisions": [d.to_dict() for d in self.decisions],
            "metadata": self.metadata,
        }


class ExpertCollaborationHub:
    """
    专家协同中枢
    
    - 负责管理协同会话生命周期
    - 记录贡献、决策、指标
    - 与 DataService 打通以便持久化和多租户隔离
    """

    def __init__(self, data_service: Optional[DataService] = None, event_bus: Optional[UnifiedEventBus] = None):
        self.data_service = data_service or get_data_service()
        self.event_bus = event_bus or get_unified_event_bus()

    async def start_session(
        self,
        topic: str,
        initiator: str,
        goals: List[str],
        experts: List[Dict[str, Any]],
        channel: str = "multi",
    ) -> Dict[str, Any]:
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            topic=topic,
            initiator=initiator,
            goals=goals,
            experts=experts,
            started_at=_utc_now(),
            channel=channel,
            metadata={
                "last_activity": _utc_now(),
                "synergy_score": 0.0,
                "response_latency_ms": None,
            },
        )
        await self._persist_session(session)
        await self._publish_event(
            event_type="collaboration.session.started",
            session=session,
            payload={"goals": goals, "experts": experts},
        )
        return session.to_dict()

    async def add_contribution(
        self,
        session_id: str,
        expert_id: str,
        expert_name: str,
        summary: str,
        channel: str,
        action_items: Optional[List[str]] = None,
        impact_score: float = 0.5,
        references: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        session = await self._load_session(session_id)
        contribution = ExpertContribution(
            timestamp=_utc_now(),
            expert_id=expert_id,
            expert_name=expert_name,
            channel=channel,
            summary=summary,
            action_items=action_items or [],
            impact_score=impact_score,
            references=references or [],
        )
        session.contributions.append(contribution)
        session.metadata["last_activity"] = contribution.timestamp
        session.metadata["synergy_score"] = self._calculate_synergy(session)
        session.metadata["response_latency_ms"] = self._calculate_latency(session)
        await self._persist_session(session)
        await self._publish_event(
            event_type="collaboration.session.updated",
            session=session,
            payload={
                "expert_id": expert_id,
                "channel": channel,
                "impact_score": impact_score,
            },
        )
        return session.to_dict()

    async def finalize_session(
        self,
        session_id: str,
        owner: str,
        summary: str,
        kpis: Optional[List[str]] = None,
        followups: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        session = await self._load_session(session_id)
        decision = CollaborationDecision(
            decided_at=_utc_now(),
            owner=owner,
            summary=summary,
            kpis=kpis or [],
            followups=followups or [],
        )
        session.decisions.append(decision)
        session.status = "resolved"
        session.metadata["resolved_at"] = decision.decided_at
        await self._persist_session(session)
        await self._publish_event(
            event_type="collaboration.session.resolved",
            session=session,
            payload={"owner": owner, "kpis": kpis or [], "followups": followups or []},
        )
        return session.to_dict()

    async def get_active_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        records = await self.data_service.query_data(
            module="expert",
            filters={"type": "collaboration_session", "status": "active"},
            limit=limit,
            order_by="updated_at",
            order_desc=True,
        )
        return [self._normalize_record(record) for record in records]

    async def get_summary(self, limit: int = 50) -> Dict[str, Any]:
        records = await self.data_service.query_data(
            module="expert",
            filters={"type": "collaboration_session"},
            limit=limit,
            order_by="updated_at",
            order_desc=True,
        )
        total = len(records)
        resolved = sum(1 for rec in records if rec.get("status") == "resolved")
        synergy_scores = [
            rec.get("metadata", {}).get("synergy_score", 0.0)
            for rec in records
            if rec.get("metadata")
        ]
        avg_synergy = statistics.mean(synergy_scores) if synergy_scores else 0.0
        avg_latency = statistics.mean(
            latency for rec in records
            if (latency := rec.get("metadata", {}).get("response_latency_ms"))
        ) if records else None

        return {
            "total_sessions": total,
            "resolved_sessions": resolved,
            "active_sessions": total - resolved,
            "avg_synergy": round(avg_synergy, 2),
            "avg_response_latency_ms": round(avg_latency, 2) if avg_latency else None,
            "recent_topics": [rec.get("topic") for rec in records[:5]],
        }

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        session = await self._load_session(session_id)
        return session.to_dict()

    async def create_collaboration_session(
        self,
        topic: str,
        expert_ids: List[str]
    ) -> str:
        """
        创建协同会话
        
        Args:
            topic: 会话主题
            expert_ids: 参与专家ID列表
            
        Returns:
            会话ID
        """
        # 将专家ID转换为专家信息字典
        experts = [{"expert_id": expert_id, "name": expert_id} for expert_id in expert_ids]
        
        # 使用现有的start_session方法创建会话
        session_data = await self.start_session(
            topic=topic,
            initiator="system_test",
            goals=[f"{topic}分析"],
            experts=experts,
            channel="multi"
        )
        
        return session_data["session_id"]

    def create_collaboration_session_sync(
        self,
        topic: str,
        expert_ids: List[str]
    ) -> str:
        """
        同步方式创建协同会话（用于测试）
        
        Args:
            topic: 会话主题
            expert_ids: 参与专家ID列表
            
        Returns:
            会话ID
        """
        import asyncio
        
        # 将专家ID转换为专家信息字典
        experts = [{"expert_id": expert_id, "name": expert_id} for expert_id in expert_ids]
        
        # 简化处理：总是创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            session_data = loop.run_until_complete(
                self.start_session(
                    topic=topic,
                    initiator="system_test",
                    goals=[f"{topic}分析"],
                    experts=experts,
                    channel="multi"
                )
            )
        finally:
            loop.close()
        
        return session_data["session_id"]

    async def _publish_event(
        self,
        event_type: str,
        session: CollaborationSession,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.event_bus:
            return
        event_payload = {
            "session_id": session.session_id,
            "topic": session.topic,
            "status": session.status,
            "metadata": session.metadata,
            **(payload or {}),
        }
        try:
            await self.event_bus.publish(
                category=EventCategory.WORKFLOW,
                event_type=event_type,
                source="expert_collaboration",
                severity=EventSeverity.INFO,
                payload=event_payload,
                correlation_id=session.session_id,
            )
        except Exception:
            # 避免影响主流程
            logger = logging.getLogger(__name__)
            logger.warning("发布协同事件到统一总线失败", exc_info=True)

    async def _persist_session(self, session: CollaborationSession) -> None:
        await self.data_service.save_data(
            module="expert",
            record_id=session.session_id,
            data={**session.to_dict(), "updated_at": _utc_now()},
            metadata={"category": "collaboration"},
        )

    async def _load_session(self, session_id: str) -> CollaborationSession:
        record = await self.data_service.load_data("expert", session_id)
        if not record:
            raise ValueError(f"协同会话 {session_id} 不存在")
        return self._record_to_session(record)

    def _record_to_session(self, record: Dict[str, Any]) -> CollaborationSession:
        contributions = [
            ExpertContribution(**contrib)
            for contrib in record.get("contributions", [])
        ]
        decisions = [
            CollaborationDecision(**decision)
            for decision in record.get("decisions", [])
        ]
        return CollaborationSession(
            session_id=record["session_id"],
            topic=record["topic"],
            initiator=record["initiator"],
            goals=record.get("goals", []),
            experts=record.get("experts", []),
            started_at=record["started_at"],
            status=record.get("status", "active"),
            channel=record.get("channel", "multi"),
            contributions=contributions,
            decisions=decisions,
            metadata=record.get("metadata", {}),
        )

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """确保 API 输出格式一致"""
        normalized = dict(record)
        normalized["contributions"] = record.get("contributions", [])
        normalized["decisions"] = record.get("decisions", [])
        normalized.setdefault("metadata", {})
        return normalized

    def _calculate_synergy(self, session: CollaborationSession) -> float:
        if not session.contributions:
            return 0.0
        expert_ids = {c.expert_id for c in session.contributions}
        channels = {c.channel for c in session.contributions}
        diversity_bonus = min(0.4, len(expert_ids) * 0.1 + len(channels) * 0.05)
        impact_avg = statistics.mean(c.impact_score for c in session.contributions)
        cadence = min(0.3, len(session.contributions) * 0.05)
        return round(min(1.0, impact_avg * 0.5 + diversity_bonus + cadence), 2)

    def _calculate_latency(self, session: CollaborationSession) -> Optional[float]:
        if len(session.contributions) < 2:
            return None
        first = datetime.fromisoformat(session.contributions[0].timestamp)
        last = datetime.fromisoformat(session.contributions[-1].timestamp)
        delta = (last - first).total_seconds() * 1000
        return round(delta, 2)


# 全局单例
_expert_collaboration_hub: Optional[ExpertCollaborationHub] = None


def get_expert_collaboration_hub() -> ExpertCollaborationHub:
    global _expert_collaboration_hub
    if _expert_collaboration_hub is None:
        _expert_collaboration_hub = ExpertCollaborationHub()
    return _expert_collaboration_hub


expert_collaboration_hub = get_expert_collaboration_hub()


