import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.expert_collaboration import ExpertCollaborationHub
from core.data_service import DataService
from core.database_persistence import DatabasePersistence


class DummyDataService:
    def __init__(self):
        self.records = {}

    async def save_data(self, module, data, record_id=None, metadata=None, sync=True):
        record_id = record_id or data.get("session_id") or str(uuid.uuid4())
        record = dict(data)
        record["record_id"] = record_id
        self.records[record_id] = record
        return record_id

    async def load_data(self, module, record_id):
        return self.records.get(record_id)

    async def query_data(
        self,
        module,
        filters=None,
        limit=100,
        offset=0,
        order_by=None,
        order_desc=True,
    ):
        filters = filters or {}
        result = []
        for record in self.records.values():
            if all(record.get(key) == value for key, value in filters.items()):
                result.append(record)
        if order_by:
            result.sort(key=lambda item: item.get(order_by), reverse=order_desc)
        return result[offset : offset + limit]


class DummySyncManager:
    async def sync(self, *args, **kwargs):
        return None


@pytest.fixture()
def collab_hub(tmp_path, monkeypatch):
    monkeypatch.setenv("MULTITENANT_ENABLED", "0")
    db_path = tmp_path / "collaboration.db"
    persistence = DatabasePersistence(db_path=db_path, enable_sync=False)
    data_service = DataService(persistence=persistence, sync_manager=DummySyncManager())
    return ExpertCollaborationHub(data_service=data_service)


@pytest.mark.asyncio
async def test_expert_collaboration_flow():
    hub = ExpertCollaborationHub(data_service=DummyDataService())
    session = await hub.start_session(
        topic="跨域风控会诊",
        initiator="ops_lead",
        goals=["梳理风险", "制定行动"],
        experts=[
            {"expert_id": "rag-1", "name": "RAG 专家", "domain": "rag"},
            {"expert_id": "ops-9", "name": "运营专家", "domain": "operations"},
        ],
    )
    session_id = session["session_id"]
    session = await hub.add_contribution(
        session_id=session_id,
        expert_id="rag-1",
        expert_name="RAG 专家",
        summary="提供最新知识库差异分析",
        channel="rag",
        action_items=["同步索引清单"],
        impact_score=0.7,
        references=["doc://rag_diff"],
    )
    assert session["metadata"]["synergy_score"] >= 0

    session = await hub.finalize_session(
        session_id=session_id,
        owner="ops_lead",
        summary="完成版本发布前风险清单确认",
        kpis=["响应时长<2h"],
        followups=["三天后复盘"],
    )
    assert session["status"] == "resolved"

    summary = await hub.get_summary()
    assert summary["total_sessions"] == 1
    assert summary["resolved_sessions"] == 1


@pytest.mark.asyncio
async def test_add_contribution_missing_session():
    hub = ExpertCollaborationHub(data_service=DummyDataService())
    with pytest.raises(ValueError):
        await hub.add_contribution(
            session_id="unknown",
            expert_id="ops",
            expert_name="Ops",
            summary="无效会话",
            channel="ops",
        )


@pytest.mark.asyncio
async def test_collaboration_lifecycle(collab_hub):
    session = await collab_hub.start_session(
        topic="测试协同",
        initiator="ops_lead",
        goals=["降低库存风险"],
        experts=[{"expert_id": "rag_expert", "name": "知识专家", "domain": "rag", "role": "owner"}],
    )
    session_id = session["session_id"]

    updated = await collab_hub.add_contribution(
        session_id=session_id,
        expert_id="rag_expert",
        expert_name="知识专家",
        summary="输出风险分析",
        channel="rag",
        action_items=["同步趋势组"],
        impact_score=0.8,
    )
    assert updated["metadata"]["synergy_score"] > 0

    resolved = await collab_hub.finalize_session(
        session_id=session_id,
        owner="ops_lead",
        summary="已确认行动计划",
        kpis=["stock_turnover"],
        followups=["两周复盘"],
    )
    assert resolved["status"] == "resolved"

    summary = await collab_hub.get_summary()
    assert summary["resolved_sessions"] >= 1

