"""
记忆系统模块
"""

from typing import Dict, Any, Optional


class MemoSystem:
    """记忆系统"""
    
    def __init__(self):
        self.memory = {}
    
    def store(self, key: str, value: Any):
        """存储记忆"""
        self.memory[key] = value
    
    def retrieve(self, key: str) -> Optional[Any]:
        """检索记忆"""
        return self.memory.get(key)