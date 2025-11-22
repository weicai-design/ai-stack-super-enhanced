"""
测试公共配置，确保可以导入 core 模块
"""

import sys
import uuid
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = PROJECT_ROOT.parent
ASCII_LINK = WORKSPACE_ROOT / "super_agent_main_interface"

for candidate in (PROJECT_ROOT, ASCII_LINK):
    if candidate.exists():
        path_str = str(candidate.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


@pytest.fixture()
def writable_tmp_path(tmp_path):
    """
    直接复用 pytest 提供的 tmp_path；真正写入前会在测试内部二次检测。
    """
    return tmp_path


