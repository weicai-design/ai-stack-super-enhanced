import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
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