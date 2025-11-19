"""
内容合规/版权检测服务
实现：文本原创度/相似度/敏感词检测（轻量版，后续可接第三方）
集成P0-017安全合规基线系统
"""
from __future__ import annotations

from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
import re
import math

if TYPE_CHECKING:
    from .security_compliance_baseline import SecurityComplianceBaseline

SENSITIVE_WORDS = ["涉政", "暴力", "极端", "黄赌毒", "敏感词"]


class ContentComplianceService:
    def __init__(self, security_baseline: Optional["SecurityComplianceBaseline"] = None):
        self.sensitive_words = set(SENSITIVE_WORDS)
        self.security_baseline = security_baseline  # P0-017: 集成安全合规基线

    def _similarity_token_jaccard(self, a: str, b: str) -> float:
        def tokenize(x: str) -> List[str]:
            # 简单分词（按非字母数字分隔）
            return [t for t in re.split(r"[^0-9A-Za-z\u4e00-\u9fa5]+", x) if t]
        sa, sb = set(tokenize(a)), set(tokenize(b))
        if not sa and not sb:
            return 1.0
        inter = len(sa & sb)
        union = len(sa | sb)
        return inter / union if union else 0.0

    def _check_sensitive(self, text: str) -> List[str]:
        hits = []
        for w in self.sensitive_words:
            if w in text:
                hits.append(w)
        return hits

    async def check_text(self, text: str, references: Optional[List[str]] = None, source: str = "system") -> Dict[str, any]:
        text = (text or "").strip()
        if not text:
            return {"success": False, "error": "空文本", "timestamp": datetime.now().isoformat()}

        # P0-017: 先调用安全合规基线系统检查
        if self.security_baseline:
            security_check = await self.security_baseline.check_content_security(text, "text", source)
            if not security_check.get("safe", True):
                return {
                    "success": False,
                    "error": "内容安全检查未通过",
                    "security_check": security_check,
                    "timestamp": datetime.now().isoformat()
                }

        sensitive_hits = self._check_sensitive(text)
        sensitive_score = 100.0 - min(len(sensitive_hits) * 30.0, 100.0)

        sim_scores: List[float] = []
        if references:
            for ref in references[:5]:
                try:
                    sim = self._similarity_token_jaccard(text, ref or "")
                    sim_scores.append(sim)
                except Exception:
                    continue
        max_sim = max(sim_scores) if sim_scores else 0.0

        # 简单原创度估计：1 - 最大相似度（转为百分比）
        originality = max(0.0, (1.0 - max_sim) * 100.0)

        # 综合合规评分（后续可加权）
        compliance_score = max(0.0, min(100.0, (originality * 0.6) + (sensitive_score * 0.4)))

        return {
            "success": True,
            "originality_percent": round(originality, 2),
            "max_similarity": round(max_sim, 4),
            "sensitive_hits": sensitive_hits,
            "sensitive_score": round(sensitive_score, 2),
            "compliance_score": round(compliance_score, 2),
            "timestamp": datetime.now().isoformat()
        }


