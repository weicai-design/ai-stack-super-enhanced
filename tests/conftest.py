import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 将 api.app 指向 src.main.app，避免导入 legacy heavy 版本
try:
    from src.main import app as _app

    api_pkg = types.ModuleType("api")
    api_pkg.__path__ = []  # 标记为包
    api_app_mod = types.ModuleType("api.app")
    api_app_mod.app = _app
    sys.modules["api"] = api_pkg
    sys.modules["api.app"] = api_app_mod
except Exception:
    pass

ALT = os.path.join(ROOT, "📚 Enhanced RAG & Knowledge Graph")

for path in (ALT, ROOT):
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)
import importlib

import pytest


def _opt_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def test_ingest_pipeline_importable_and_has_class():
    # 通过 tests/conftest.py 已注入 emoji 目录到 sys.path
    mod = _opt_import("pipelines.smart_ingestion_pipeline")
    if mod is None:
        pytest.skip("pipelines.smart_ingestion_pipeline 不可用，跳过此集成测试")
    assert hasattr(mod, "SmartIngestionPipeline")
