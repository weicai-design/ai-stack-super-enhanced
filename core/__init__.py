"""
顶层别名包：将项目根目录下的 `🚀 Super Agent Main Interface/core`
暴露为标准的 `core` 包，便于 pytest 以及其他子项目通过
`import core.xxx` 的方式复用 Super Agent 的实现。
"""

from __future__ import annotations

from pathlib import Path
from types import ModuleType
from typing import List

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

_ROOT = Path(__file__).resolve().parent.parent
_CANDIDATES: List[Path] = [
    _ROOT / "🚀 Super Agent Main Interface" / "core",
    _ROOT / "super_agent_main_interface" / "core",
]

for candidate in _CANDIDATES:
    if candidate.exists():
        path_str = str(candidate.resolve())
        if path_str not in __path__:
            __path__.append(path_str)


def __getattr__(name: str):
    """
    将 `from core import Foo` 这样的写法代理到真正的模块实现。
    """
    for candidate in _CANDIDATES:
        module_file = candidate / "__init__.py"
        if module_file.exists():
            module_globals: dict = {}
            with open(module_file, "r", encoding="utf-8") as f:
                code = compile(f.read(), str(module_file), "exec")
                exec(code, module_globals, module_globals)
            if name in module_globals:
                value = module_globals[name]
                globals()[name] = value
                return value
    raise AttributeError(f"module 'core' has no attribute '{name}'")


def __dir__():
    entries = set(globals().keys())
    for candidate in _CANDIDATES:
        module_file = candidate / "__init__.py"
        if module_file.exists():
            module_globals: dict = {}
            with open(module_file, "r", encoding="utf-8") as f:
                code = compile(f.read(), str(module_file), "exec")
                exec(code, module_globals, module_globals)
            entries.update(module_globals.keys())
    return sorted(entries)



