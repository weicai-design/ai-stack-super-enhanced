"""
RAG 预处理与真实性验证（轻量实现）
功能：
- 清洗：去除控制字符/多余空白
- 标准化：统一换行/空白
- 去重：基于哈希的段落级去重
- 验证：基本完整性与长度检查
- 真实性验证：启发式评分（来源提示/引用/时间线/一致性）
"""
from __future__ import annotations

from typing import Dict, Any, List, Tuple
from datetime import datetime
import hashlib
import re


def clean_text(text: str) -> str:
    t = text or ""
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", t)
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    return t.strip()


def standardize_text(text: str) -> str:
    t = re.sub(r"[ \t]+", " ", text)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def deduplicate(text: str) -> Dict[str, Any]:
    paragraphs = [p.strip() for p in (text or "").split("\n\n") if p.strip()]
    seen = set()
    unique: List[str] = []
    removed = 0
    for p in paragraphs:
        h = hashlib.sha1(p.encode("utf-8")).hexdigest()
        if h in seen:
            removed += 1
            continue
        seen.add(h)
        unique.append(p)
    return {
        "unique_text": "\n\n".join(unique),
        "removed": removed,
        "kept": len(unique)
    }


def validate(text: str) -> Dict[str, Any]:
    length = len(text or "")
    issues: List[str] = []
    if length < 20:
        issues.append("文本过短")
    if text and not re.search(r"[。.!?]", text):
        issues.append("缺少句子结束符，可能不完整")
    return {
        "valid": len(issues) == 0,
        "length": length,
        "issues": issues
    }


def authenticity_score(text: str) -> Dict[str, Any]:
    """
    启发式真实性评分（0-100）：
    - 包含来源/引用(“来源/参考/链接/doi/http”) +20
    - 包含时间线（年份/日期） +15
    - 覆盖多来源迹象（多个http链接） +15
    - 结构化（段落数>3） +10
    - 惩罚：强主观词密度高（“震惊/绝对/唯一/内幕/必涨”等） -0~20
    """
    t = (text or "").lower()
    score = 40.0
    reasons: List[str] = []

    if any(k in t for k in ["来源", "参考", "链接", "doi", "http://", "https://"]):
        score += 20; reasons.append("包含来源/引用")
    links = re.findall(r"https?://\S+", t)
    if len(links) >= 2:
        score += 15; reasons.append("多来源链接")
    if re.search(r"\b(19|20)\d{2}\b|\d{4}-\d{1,2}-\d{1,2}", t):
        score += 15; reasons.append("包含时间线")
    paragraphs = [p for p in t.split("\n\n") if p.strip()]
    if len(paragraphs) > 3:
        score += 10; reasons.append("结构化文本")
    hype_words = ["震惊", "绝对", "唯一", "内幕", "必涨", "稳赚", "零风险"]
    hype_hits = sum(t.count(w) for w in hype_words)
    if hype_hits:
        penalty = min(20.0, hype_hits * 4.0)
        score -= penalty
        reasons.append(f"主观夸张词惩罚 -{penalty:.0f}")

    score = max(0.0, min(100.0, score))
    level = "high" if score >= 75 else "medium" if score >= 55 else "low"
    return {
        "success": True,
        "score": round(score, 2),
        "level": level,
        "reasons": reasons,
        "timestamp": datetime.now().isoformat()
    }


