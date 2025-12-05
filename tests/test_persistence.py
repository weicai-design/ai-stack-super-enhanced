import asyncio
import importlib
import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "🚀 Super Agent Main Interface"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


from core.database_persistence import DatabasePersistence  # noqa: E402
from core.data_service import DataService  # noqa: E402
from core.persistence_seed import PersistenceSeeder  # noqa: E402


class DummySyncManager:
    async def sync(self, *args, **kwargs):
        return None


@pytest.mark.asyncio
async def test_persistence_seeder_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("MULTITENANT_ENABLED", "0")
    db_path = tmp_path / "seed.db"
    persistence = DatabasePersistence(db_path=db_path, enable_sync=False)
    data_service = DataService(persistence=persistence, sync_manager=DummySyncManager())
    seeder = PersistenceSeeder(data_service)

    seeder.register_seed(
        "demo_seed",
        module="trend",
        type_field="type",
        type_value="demo_indicator",
        records=[{"id": "demo_1", "name": "Demo Indicator"}],
        record_id_field="id",
    )

    await seeder.ensure_seed("demo_seed")
    # 再次执行不会重复写入
    await seeder.ensure_seed("demo_seed")

    rows = await data_service.query_data(module="trend", filters={"type": "demo_indicator"})
    assert len(rows) == 1
    assert rows[0]["id"] == "demo_1"


def _reload_app(monkeypatch, tmp_path):
    pytest.importorskip("sqlalchemy", reason="ERP API 依赖 SQLAlchemy")
    tenants_path = tmp_path / "tenants.json"
    tenants_path.write_text(
        json.dumps(
            {
                "tenants": [
                    {"tenant_id": "global", "name": "Global", "plan": "enterprise", "active": True, "metadata": {}},
                    {"tenant_id": "demo", "name": "Demo", "plan": "enterprise", "active": True, "metadata": {}},
                ]
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    db_path = tmp_path / "api.db"
    monkeypatch.setenv("PERSISTENCE_DB_PATH", str(db_path))
    monkeypatch.setenv("TENANT_CONFIG_PATH", str(tenants_path))
    monkeypatch.setenv("MULTITENANT_ENABLED", "0")

    for module_name in ("api.main", "api.super_agent_api"):
        if module_name in sys.modules:
            del sys.modules[module_name]

    super_agent_api = importlib.import_module("api.super_agent_api")
    importlib.reload(super_agent_api)
    main = importlib.import_module("api.main")
    importlib.reload(main)
    return main.app, super_agent_api


def test_trend_indicator_endpoint_seeds(tmp_path, monkeypatch):
    app, super_agent_api = _reload_app(monkeypatch, tmp_path)
    client = TestClient(app)

    response = client.get("/api/super-agent/trend/indicators", headers={"X-Tenant-ID": "demo"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["count"] > 0

    count = asyncio.run(
        super_agent_api.data_service.count_data(module="trend", filters={"type": "indicator"})
    )
    assert count == payload["count"]

