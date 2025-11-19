from __future__ import annotations

import re
from typing import Iterable, List, Sequence

from .config import get_security_settings


class SensitiveContentFilter:
    """
    轻量级敏感词过滤与风控策略。
    """

    def __init__(self, blocklist: Sequence[str] | None = None):
        settings = get_security_settings()
        keywords = blocklist or settings.sensitive_words
        self.blocklist: List[str] = [word for word in keywords if word]
        self._regex = (
            re.compile("|".join(re.escape(word) for word in self.blocklist), re.IGNORECASE)
            if self.blocklist
            else None
        )

    def scan(self, text: str) -> List[str]:
        if not text or not self._regex:
            return []
        return list({match.group(0) for match in self._regex.finditer(text)})

    def assert_safe(self, text: str) -> None:
        findings = self.scan(text)
        if findings:
            raise ValueError(f"输入命中敏感词: {', '.join(findings)}")

    def extend(self, custom_words: Iterable[str]) -> None:
        for word in custom_words:
            if word and word not in self.blocklist:
                self.blocklist.append(word)
        self._regex = re.compile("|".join(re.escape(word) for word in self.blocklist), re.IGNORECASE)


