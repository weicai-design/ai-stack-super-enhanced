from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# 确保仓库根路径在 sys.path 中
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import app  # noqa: E402


def test_readyz():
    with TestClient(app) as c:
        r = c.get("/readyz")
        assert r.status_code == 200
        assert r.json().get("ok") is True


def test_expert_predict_with_key():
    os.environ["RAG_API_KEY"] = "devkey"
    with TestClient(app) as c:
        r = c.post(
            "/experts/finance_expert/predict",
            headers={"x-api-key": "devkey"},
            json={"metrics": {"debt_ratio": 0.7, "cash_flow": 0.4}},
        )
        assert r.status_code == 200
        body = r.json()
        assert "risk" in body and "score" in body
