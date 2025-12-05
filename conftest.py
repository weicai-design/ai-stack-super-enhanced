"""
根级别 conftest.py
确保在 pytest 收集测试之前设置 Python 路径，以便正确导入 core 模块
"""

import sys
from pathlib import Path

# 获取项目根目录
ROOT_DIR = Path(__file__).resolve().parent
SUPER_AGENT_DIR = ROOT_DIR / "🚀 Super Agent Main Interface"
ASCII_LINK_DIR = ROOT_DIR / "super_agent_main_interface"

# 在模块级别立即设置路径（在导入时执行，早于任何 hook）
for candidate in (SUPER_AGENT_DIR, ASCII_LINK_DIR):
    if candidate.exists():
        path_str = str(candidate.resolve())
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def pytest_configure(config):
    """
    pytest 配置 hook，在收集测试之前执行
    确保路径已设置，即使测试文件在 conftest 之前被导入
    """
    # 再次确保路径已设置（双重保险）
    for candidate in (SUPER_AGENT_DIR, ASCII_LINK_DIR):
        if candidate.exists():
            path_str = str(candidate.resolve())
            if path_str not in sys.path:
                sys.path.insert(0, path_str)


def pytest_collection_modifyitems(config, items):
    """
    在收集测试后修改测试项
    这里可以确保路径已设置
    """
    pass

