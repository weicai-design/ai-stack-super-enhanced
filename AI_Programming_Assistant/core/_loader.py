from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

EMOJI_PACKAGE_ROOT = (
    Path(__file__).resolve().parents[2] / "💻 AI Programming Assistant" / "core"
)


@lru_cache(maxsize=None)
def load_original_module(module_name: str):
    """
    动态加载原始 emoji 路径下的模块，并返回已执行的 module 对象。
    这样可以避免重复加载，同时让 ASCII 包与原文件保持一次性绑定。
    """
    target_path = EMOJI_PACKAGE_ROOT / f"{module_name}.py"
    if not target_path.exists():
        raise ImportError(
            f"无法找到原始模块 '{module_name}'，期望路径: {target_path}"
        )

    spec = importlib.util.spec_from_file_location(
        f"emoji_ai_programming.{module_name}", target_path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"无法为模块 {module_name} 创建 spec")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


