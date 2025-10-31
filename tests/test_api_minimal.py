from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from src.main import app

ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "📚 Enhanced RAG & Knowledge Graph" / "api" / "app.py"
os.environ.setdefault("LOCAL_ST_MODEL_PATH", str(ROOT / "models" / "all-MiniLM-L6-v2"))


def _load_app_module():
    spec = importlib.util.spec_from_file_location("api_app", APP_PATH)
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    sys.modules["api_app"] = mod
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore
    return mod


mod = _load_app_module()
app = mod.app
INDEX_DOCS, INDEX_VECS = mod.INDEX_DOCS, mod.INDEX_VECS
client = TestClient(app)


def _clear_files():
    for p in (INDEX_DOCS, INDEX_VECS):
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass


def test_readyz():
    with TestClient(app) as c:
        r = c.get("/readyz")
        assert r.status_code == 200
        assert r.json().get("ok") is True


def test_ingest_text_and_search():
    _clear_files()
    client.delete("/index/clear?remove_file=true&clear_kg=true")
    r = client.post(
        "/rag/ingest", json={"text": "hello email test@example.com", "save_index": True}
    )
    assert r.status_code == 200
    assert r.json()["size"] >= 1
    r = client.get("/rag/search", params={"query": "email", "top_k": 3})
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert items[0]["score"] > 0


def test_expert_predict_auth():
    with TestClient(app) as c:
        import os

        os.environ["RAG_API_KEY"] = "devkey"
        r = c.post(
            "/experts/finance_expert/predict",
            json={"metrics": {"debt_ratio": 0.7, "cash_flow": 0.4}},
        )
        assert r.status_code in (200, 401)


def test_persistence_reload():
    r = client.post("/index/save")
    assert r.status_code == 200
    r = client.post("/index/load")
    assert r.status_code == 200
    r = client.get("/rag/search", params={"query": "email", "top_k": 3})
    assert r.status_code == 200
    assert len(r.json()["items"]) >= 1
