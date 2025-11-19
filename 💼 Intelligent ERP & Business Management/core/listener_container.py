"""
共享监听器容器
在多个API模块之间复用同一个 ERPDataListener 实例，避免重复监听。
"""

from core.data_listener import ERPDataListener

# 全局唯一的监听器实例
data_listener = ERPDataListener()

__all__ = ["data_listener"]

