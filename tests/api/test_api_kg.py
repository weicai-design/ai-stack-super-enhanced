import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _get_app():
    # 确保可导入到 emoji 目录下的 api.app
    base = Path(__file__).resolve().parents[2] / "📚 Enhanced RAG & Knowledge Graph"
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    from api.app import app  # type: ignore

    return app


@pytest.fixture(scope="function")
def client(monkeypatch):
    monkeypatch.setenv("RAG_API_KEY", "testkey")
    app = _get_app()
    with TestClient(app) as c:
        yield c


def test_kg_save_clear_load_roundtrip(tmp_path, client: TestClient):
    # 1) 构造文本并先采集一条，确保 KG 有内容
    p = tmp_path / "a.txt"
    p.write_text("Hello KG, email me at test@example.com and visit https://example.com")
    r = client.post("/rag/ingest", json={"path": str(p), "save_index": True})
    assert r.status_code == 200
    assert r.json().get("success") is True

    # 2) 快照应有实体/文档
    r = client.get("/kg/snapshot")
    assert r.status_code == 200
    snap = r.json()
    assert isinstance(snap.get("entities", []), list)
    assert len(snap.get("entities", [])) >= 1

    # 3) 保存 KG 到文件
    kg_file = tmp_path / "kg.json"
    r = client.post(
        "/kg/save", params={"path": str(kg_file)}, headers={"X-API-Key": "testkey"}
    )
    assert r.status_code == 200
    assert kg_file.is_file()

    # 4) 清空索引与 KG
    r = client.delete(
        "/index/clear",
        params={"remove_file": False, "clear_kg": True},
        headers={"X-API-Key": "testkey"},
    )
    assert r.status_code == 200

    # 5) 验证 KG 已清空
    r = client.get("/kg/snapshot")
    assert r.status_code == 200
    snap2 = r.json()
    assert len(snap2.get("entities", [])) == 0

    # 6) 从文件加载 KG
    r = client.post(
        "/kg/load", params={"path": str(kg_file)}, headers={"X-API-Key": "testkey"}
    )
    assert r.status_code == 200

    # 7) 验证 KG 已恢复
    r = client.get("/kg/snapshot")
    assert r.status_code == 200
    snap3 = r.json()
    assert len(snap3.get("entities", [])) >= 1
