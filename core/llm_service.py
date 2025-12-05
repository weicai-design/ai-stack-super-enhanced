"""
LLM服务模块
"""

from typing import Dict, Any, Optional
from enum import Enum


class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"


class LLMService:
    """LLM服务"""
    
    def __init__(self, provider: LLMProvider = LLMProvider.OPENAI):
        self.provider = provider
    
    def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """生成文本"""
        return {
            "text": f"Generated response for: {prompt}",
            "provider": self.provider.value,
            "tokens_used": 100
        }


def get_llm_service(provider: LLMProvider = LLMProvider.OPENAI) -> LLMService:
    """获取LLM服务实例"""
    return LLMService(provider)