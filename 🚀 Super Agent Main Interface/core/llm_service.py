"""
LLM服务
支持本地Ollama和外部API（OpenAI、Anthropic等）
"""

import httpx
import os
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime


class LLMProvider(str, Enum):
    """LLM提供商"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"


class LLMService:
    """
    LLM服务
    
    支持：
    1. 本地Ollama
    2. OpenAI API
    3. Anthropic Claude API
    4. Azure OpenAI
    """
    
    def __init__(
        self,
        provider: str = "ollama",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化LLM服务
        
        Args:
            provider: 提供商 (ollama/openai/anthropic/azure_openai)
            api_key: API密钥（外部API需要）
            base_url: API基础URL
            model: 模型名称
        """
        self.provider = LLMProvider(provider.lower())
        
        # 从环境变量读取配置
        self.api_key = api_key or os.getenv(f"{self.provider.value.upper()}_API_KEY")
        self.base_url = base_url or self._get_default_base_url()
        self.model = model or self._get_default_model()
        
        self.timeout = 15.0  # 优化：减少超时时间到15秒（使用更快模型）
        
    def _get_default_base_url(self) -> str:
        """获取默认API地址"""
        defaults = {
            LLMProvider.OLLAMA: "http://localhost:11434",
            LLMProvider.OPENAI: "https://api.openai.com/v1",
            LLMProvider.ANTHROPIC: "https://api.anthropic.com/v1",
            LLMProvider.AZURE_OPENAI: os.getenv("AZURE_OPENAI_ENDPOINT", "")
        }
        return defaults.get(self.provider, defaults[LLMProvider.OLLAMA])
    
    def _get_default_model(self) -> str:
        """获取默认模型（优先选择更快的模型）"""
        defaults = {
            # 使用更小的模型以提高速度：qwen2.5:1.5b (1.5B参数) 比 qwen2.5:7b (7B参数) 快3-4倍
            LLMProvider.OLLAMA: "qwen2.5:1.5b",  # 更快的模型，响应时间约1-2秒
            LLMProvider.OPENAI: "gpt-3.5-turbo",  # 比gpt-4快且便宜
            LLMProvider.ANTHROPIC: "claude-3-haiku-20240307",  # Claude最快的模型
            LLMProvider.AZURE_OPENAI: os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-3.5-turbo")
        }
        return defaults.get(self.provider, defaults[LLMProvider.OLLAMA])
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        生成文本
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            生成的文本
        """
        try:
            if self.provider == LLMProvider.OLLAMA:
                return await self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.OPENAI:
                return await self._generate_openai(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.ANTHROPIC:
                return await self._generate_anthropic(prompt, system_prompt, temperature, max_tokens)
            elif self.provider == LLMProvider.AZURE_OPENAI:
                return await self._generate_azure_openai(prompt, system_prompt, temperature, max_tokens)
            else:
                raise ValueError(f"不支持的提供商: {self.provider}")
        except Exception as e:
            # 如果失败，返回错误信息（而不是模拟数据）
            raise Exception(f"LLM生成失败 ({self.provider.value}): {str(e)}")
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """使用Ollama生成"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """使用OpenAI生成"""
        if not self.api_key:
            raise ValueError("OpenAI API密钥未设置")
        
        url = f"{self.base_url}/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]
    
    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """使用Anthropic Claude生成"""
        if not self.api_key:
            raise ValueError("Anthropic API密钥未设置")
        
        url = f"{self.base_url}/messages"
        
        payload = {
            "model": self.model,
            "max_tokens": max_tokens or 4096,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["content"][0]["text"]
    
    async def _generate_azure_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """使用Azure OpenAI生成"""
        if not self.api_key:
            raise ValueError("Azure OpenAI API密钥未设置")
        
        # Azure OpenAI端点格式: https://{resource}.openai.azure.com/openai/deployments/{deployment}/chat/completions
        url = f"{self.base_url}/openai/deployments/{self.model}/chat/completions"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "messages": messages,
            "temperature": temperature,
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]


# 全局LLM服务实例
_llm_service: Optional[LLMService] = None


def get_llm_service(
    provider: Optional[str] = None,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> LLMService:
    """
    获取LLM服务实例（单例模式）
    
    Args:
        provider: 提供商
        api_key: API密钥
        base_url: API地址
        model: 模型名称
        
    Returns:
        LLM服务实例
    """
    global _llm_service
    
    if _llm_service is None or provider is not None:
        # 从环境变量读取默认配置
        default_provider = provider or os.getenv("LLM_PROVIDER", "ollama")
        _llm_service = LLMService(
            provider=default_provider,
            api_key=api_key,
            base_url=base_url,
            model=model
        )
    
    return _llm_service

