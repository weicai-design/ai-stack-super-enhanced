import asyncio
import importlib

import pytest


def _opt_import(name: str):
    try:
        return importlib.import_module(name)
    except Exception:
        return None


async def _run_ingest(tmp_path, monkeypatch):
    pdf_path = tmp_path / "f.pdf"
    pdf_path.write_text("dummy content")

    pipeline_mod = _opt_import("pipelines.smart_ingestion_pipeline")
    if pipeline_mod is None:
        pytest.skip("pipelines.smart_ingestion_pipeline 不可用，跳过此集成测试")
    SmartIngestionPipeline = getattr(pipeline_mod, "SmartIngestionPipeline")

    def fake_parse_pdf(path):
        return [
            {
                "text": "hello from pdf",
                "source": str(path),
                "page": 1,
                "checksum": "abc123",
            }
        ]

    if hasattr(pipeline_mod, "pdf_parser"):
        monkeypatch.setattr(
            pipeline_mod.pdf_parser, "parse_pdf", fake_parse_pdf, raising=False
        )
    else:
        try:
            pdf_parser = importlib.import_module(
                "processors.file_processors.pdf_parser"
            )
            monkeypatch.setattr(pdf_parser, "parse_pdf", fake_parse_pdf, raising=False)
        except Exception:
            pass

    class FakeVectorStore:
        def __init__(self):
            self.added = []

        def add_documents(self, vectors, ids):
            self.added.append((vectors, ids))

    class FakeSemantic:
        def encode_query(self, text):
            return [0.1, 0.2, 0.3]

    vs = FakeVectorStore()
    sem = FakeSemantic()

    p = SmartIngestionPipeline(
        core_services={"semantic_engine": sem, "vector_store": vs}
    )
    if hasattr(p, "initialize") and asyncio.iscoroutinefunction(p.initialize):
        await p.initialize()
    res = await p.ingest_single_file(str(pdf_path))
    return res, vs


def test_ingest_pipeline_writes_vectors(tmp_path, monkeypatch):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        res, vs = loop.run_until_complete(_run_ingest(tmp_path, monkeypatch))
        assert getattr(res, "success", False) is True
        assert len(vs.added) >= 1
    finally:
        loop.close()
