"""
敏感内容策略模块
"""

from typing import Dict, Any, List


class SensitiveContentFilter:
    """敏感内容过滤器"""
    
    def __init__(self):
        self.sensitive_patterns = ["password", "api_key", "secret"]
    
    def filter_content(self, content: str) -> Dict[str, Any]:
        """过滤敏感内容"""
        filtered = content
        for pattern in self.sensitive_patterns:
            if pattern in content.lower():
                filtered = filtered.replace(pattern, "[REDACTED]")
        return {
            "original": content,
            "filtered": filtered,
            "sensitive_found": len(self.sensitive_patterns) > 0
        }