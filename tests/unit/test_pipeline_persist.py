import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "📚 Enhanced RAG & Knowledge Graph"
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import asyncio

from pipelines.smart_ingestion_pipeline import SmartIngestionPipeline  # noqa


class FakeSemantic:
    def encode_query(self, text: str):
        # 简单按长度映射到3维
        l = float(len(text) or 1)
        return [l, 0.0, 1.0]


def test_pipeline_ingest_and_auto_save_index(tmp_path):
    # 构造临时文件
    doc = tmp_path / "t.txt"
    doc.write_text("hello ingestion pipeline")

    idx = tmp_path / "index.json"
    p = SmartIngestionPipeline(
        core_services={
            "semantic_engine": FakeSemantic(),
            "auto_save_index": True,
            "index_path": str(idx),
        }
    )

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        res = loop.run_until_complete(p.ingest_single_file(str(doc)))
        assert res.success is True
    finally:
        loop.close()

    # 验证索引已保存
    assert idx.is_file()
