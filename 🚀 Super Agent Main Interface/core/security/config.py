from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import os
from typing import List


@dataclass(frozen=True)
class SecuritySettings:
    api_token: str | None
    audit_log_path: Path
    sensitive_words: List[str]
    command_whitelist_path: Path
    request_log_enabled: bool = True
    skip_audit_paths: tuple[str, ...] = (
        "/health",
        "/docs",
        "/openapi.json",
        "/static",
    )


@lru_cache()
def get_security_settings() -> SecuritySettings:
    base_dir = Path(os.getenv("SECURITY_LOG_DIR", "logs"))
    audit_file = Path(os.getenv("SECURITY_AUDIT_LOG", base_dir / "security_audit.log"))
    sensitive_words = [
        word.strip()
        for word in os.getenv(
            "SENSITIVE_KEYWORDS",
            "password,secret,token,key,credential,敏感,机密,泄漏,违规,外挂",
        ).split(",")
        if word.strip()
    ]
    whitelist_path = Path(
        os.getenv(
            "TERMINAL_WHITELIST_PATH",
            Path(__file__).resolve().parent.parent / "data" / "terminal_whitelist.json",
        )
    )
    return SecuritySettings(
        api_token=os.getenv("API_TOKEN") or os.getenv("SUPER_AGENT_API_TOKEN"),
        audit_log_path=audit_file,
        sensitive_words=sensitive_words,
        command_whitelist_path=whitelist_path,
    )


