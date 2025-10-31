import sys
from pathlib import Path

from fastapi.testclient import TestClient


def _get_app():
    base = Path(__file__).resolve().parents[2] / "📚 Enhanced RAG & Knowledge Graph"
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    from api.app import app  # type: ignore

    return app


def test_groups_endpoint(tmp_path):
    app = _get_app()
    client = TestClient(app)
    p = tmp_path / "a.txt"
    p.write_text(
        "Hello world. This is a small test document about AI.\nAnother line here."
    )
    r = client.post("/rag/ingest", json={"path": str(p), "save_index": True})
    assert r.status_code == 200 and r.json().get("success") is True
    r = client.get("/rag/groups", params={"k": 3, "max_items": 20})
    assert r.status_code == 200
    data = r.json()
    assert "groups" in data
