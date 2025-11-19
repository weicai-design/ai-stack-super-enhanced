"""
对LLM上下文进行轻量压缩，保障2秒响应 SLA
"""
from __future__ import annotations

from typing import List


class ContextCompressor:
    def __init__(self, max_chars: int = 12000, tail_sections: int = 3):
        self.max_chars = max_chars
        self.tail_sections = tail_sections

    def compress_sections(self, sections: List[str]) -> List[str]:
        sections = [s for s in sections if s]
        total = sum(len(s) for s in sections)
        if total <= self.max_chars:
            return sections
        if len(sections) <= self.tail_sections + 2:
            return self._truncate_sections(sections)
        head = sections[:2]
        tail = sections[-self.tail_sections :]
        middle = sections[2 : len(sections) - self.tail_sections]
        summary = self._summarize_middle(middle)
        return self._truncate_sections(head + [summary] + tail)

    def _truncate_sections(self, sections: List[str]) -> List[str]:
        truncated = []
        for sec in sections:
            if len(sec) > 800:
                truncated.append(sec[:800] + " …")
            else:
                truncated.append(sec)
        combined = []
        running = 0
        for sec in truncated:
            running += len(sec)
            combined.append(sec)
            if running >= self.max_chars:
                break
        return combined

    def _summarize_middle(self, sections: List[str]) -> str:
        bullets = []
        for sec in sections:
            snippet = sec.strip().replace("\n", " ")
            if len(snippet) > 200:
                snippet = snippet[:200] + "…"
            bullets.append(f"- {snippet}")
            if len(bullets) >= 6:
                break
        return "⚡ 历史提要：\n" + "\n".join(bullets) if bullets else ""

