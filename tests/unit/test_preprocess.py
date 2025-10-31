import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / "📚 Enhanced RAG & Knowledge Graph"
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from pipelines.multi_stage_preprocessor import (
    MetadataUnifyStage,
    MultiStagePreprocessor,
    NormalizeStage,
    QualityAssessStage,
    SafetyFilterStage,
)


def test_preprocessor_pipeline_basic():
    pp = MultiStagePreprocessor(
        [
            NormalizeStage(),
            SafetyFilterStage(),
            QualityAssessStage(),
            MetadataUnifyStage(),
        ]
    )
    res = pp.run(
        {
            "text": "Hello  World \n visit https://example.com \nmail me a@b.com",
            "meta": {"path": "/tmp/a.txt"},
        }
    )
    assert res["text"].startswith("Hello World")
    assert "quality" in res and res["quality"]["ok"] is True
    assert "checksum" in res
