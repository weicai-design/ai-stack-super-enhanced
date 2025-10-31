"""
Multi-Stage Preprocessor
多阶段数据预处理器

功能概述：
1. 四阶段数据预处理流程
2. 智能内容清洗和标准化
3. 语义分析和增强
4. 质量验证和评分

版本: 1.0.0
依赖: Text Processors, Core Engine
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List


class PreprocessResult(dict):
    pass


class PreprocessorStage:
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        return doc


class NormalizeStage(PreprocessorStage):
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        text = (doc.get("text") or "").replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        doc["text"] = text.strip()
        return doc


class SafetyFilterStage(PreprocessorStage):
    EMAIL = re.compile(r"([A-Za-z0-9._%+-]+)@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
    URL = re.compile(r"(https?://[^\s]+)")

    def __init__(
        self, redact_email: bool = True, redact_url: bool = False, max_len: int = 20000
    ):
        self.redact_email = redact_email
        self.redact_url = redact_url
        self.max_len = max_len

    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        t = doc.get("text") or ""
        if self.redact_email:
            t = self.EMAIL.sub("[email_redacted]", t)
        if self.redact_url:
            t = self.URL.sub("[url_redacted]", t)
        if len(t) > self.max_len:
            t = t[: self.max_len]
            doc["truncated"] = True
        doc["text"] = t
        return doc


class QualityAssessStage(PreprocessorStage):
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        t = doc.get("text") or ""
        chars = len(t)
        lines = t.count("\n") + 1 if t else 0
        unique_ratio = len(set(t)) / (chars or 1)
        doc["quality"] = {
            "chars": chars,
            "lines": lines,
            "unique_ratio": round(unique_ratio, 3),
            "ok": (chars >= 10 and unique_ratio >= 0.1),
        }
        return doc


class MetadataUnifyStage(PreprocessorStage):
    def process(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        t = (doc.get("text") or "").encode("utf-8", errors="ignore")
        checksum = hashlib.md5(t).hexdigest()
        meta = doc.get("meta") or {}
        meta["checksum"] = checksum
        doc["meta"] = meta
        doc["checksum"] = checksum
        return doc


class MultiStagePreprocessor:
    def __init__(self, stages: List[PreprocessorStage] | None = None):
        self.stages = stages or [
            NormalizeStage(),
            SafetyFilterStage(),
            QualityAssessStage(),
            MetadataUnifyStage(),
        ]

    def run(self, doc: Dict[str, Any]) -> PreprocessResult:
        for s in self.stages:
            doc = s.process(doc)
        return PreprocessResult(doc)
