from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Set
import json

from .config import get_security_settings


@dataclass
class CommandPolicyResult:
    safe: bool
    reason: str | None = None
    blocked_token: str | None = None
    command: str | None = None


class CommandSecurityPolicy:
    """
    抽象出的命令安全策略，供终端执行器 / 其他模块复用。
    """

    def __init__(
        self,
        allowed_commands: Optional[Iterable[str]] = None,
        dangerous_commands: Optional[List[str]] = None,
        forbidden_tokens: Optional[List[str]] = None,
        config_path: Optional[Path] = None,
    ):
        settings = get_security_settings()
        self.config_path = config_path or settings.command_whitelist_path
        self.allowed_commands: Set[str] = set(allowed_commands or [])
        self.dangerous_commands = dangerous_commands or [
            "rm -rf",
            "format",
            "del /f",
            "shutdown",
            "reboot",
            "mkfs",
            "dd if=",
            "sudo rm",
            ":(){",
            "kill -9 1",
        ]
        self.forbidden_tokens = forbidden_tokens or [
            "&&",
            "||",
            ";",
            "|",
            ">",
            "<",
            "$(",
            "`",
            "\\",
            "../",
            "~",
            "%",
            "&",
        ]
        if not self.allowed_commands:
            self._load_defaults()

    def _load_defaults(self) -> None:
        if self.config_path.exists():
            try:
                config = json.loads(self.config_path.read_text(encoding="utf-8"))
                self.allowed_commands = set(config.get("allowed_commands", []))
                self.dangerous_commands = config.get("dangerous_commands", self.dangerous_commands)
                self.forbidden_tokens = config.get("forbidden_tokens", self.forbidden_tokens)
            except Exception:
                self.allowed_commands = {"ls", "pwd", "cat", "echo"}
        else:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            self.allowed_commands = {
                "ls",
                "pwd",
                "cd",
                "cat",
                "grep",
                "find",
                "ps",
                "top",
                "df",
                "du",
                "free",
                "uptime",
                "whoami",
                "date",
                "echo",
            }
            self._persist()

    def update_whitelist(self, commands: Iterable[str]) -> None:
        self.allowed_commands = set(commands)
        self._persist()

    def _persist(self) -> None:
        payload = {
            "allowed_commands": sorted(self.allowed_commands),
            "dangerous_commands": self.dangerous_commands,
            "forbidden_tokens": self.forbidden_tokens,
        }
        with open(self.config_path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def inspect(self, command: str) -> CommandPolicyResult:
        cmd = (command or "").strip()
        cmd_lower = cmd.lower()
        for token in self.forbidden_tokens:
            if token in cmd_lower:
                return CommandPolicyResult(False, reason=f"命令包含受限制符号 {token}", blocked_token=token, command=command)
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in cmd_lower:
                return CommandPolicyResult(False, reason=f"命令包含危险片段 {dangerous}", blocked_token=dangerous, command=command)
        base = cmd.split()[0] if cmd else ""
        if base not in self.allowed_commands:
            return CommandPolicyResult(False, reason=f"{base} 不在白名单中", blocked_token=base, command=command)
        return CommandPolicyResult(True, reason="命令通过白名单校验", command=command)


