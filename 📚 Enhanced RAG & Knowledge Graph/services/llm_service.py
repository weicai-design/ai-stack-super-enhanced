"""
V5.8 LLM服务 - 大模型集成
支持OpenAI GPT-4和Ollama本地模型
"""

import os
from typing import List, Dict, Any, Optional
import httpx
from datetime import datetime

class LLMService:
    """大模型服务"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = os.getenv("DEFAULT_LLM_MODEL", "gpt-3.5-turbo")
        self.use_ollama = os.getenv("USE_OLLAMA", "false").lower() == "true"
        
        # 对话历史（内存存储）
        self.conversations: Dict[str, List[Dict]] = {}
        
        # 启动时检测Ollama
        self._check_ollama_availability()
    
    def _check_ollama_availability(self):
        """检测Ollama是否可用"""
        try:
            import httpx
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.ollama_base_url}/api/version")
                if resp.status_code == 200:
                    print(f"✅ Ollama服务可用: {resp.json()}")
                    # 如果Ollama可用但未配置OpenAI，自动启用Ollama
                    if not self.openai_api_key and not self.use_ollama:
                        self.use_ollama = True
                        print("✅ 自动启用Ollama（未配置OpenAI）")
        except:
            if self.use_ollama:
                print("⚠️  Ollama服务不可用，请检查服务是否运行")
    
    async def chat(
        self,
        message: str,
        session_id: str = "default",
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        智能对话
        
        Args:
            message: 用户消息
            session_id: 会话ID
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            {"response": str, "model": str, "tokens": int}
        """
        try:
            # 获取或创建对话历史
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            # 添加用户消息
            self.conversations[session_id].append({
                "role": "user",
                "content": message
            })
            
            # 调用LLM
            if self.use_ollama:
                result = await self._call_ollama(
                    messages=self.conversations[session_id],
                    model=model or "llama2",
                    temperature=temperature
                )
            else:
                result = await self._call_openai(
                    messages=self.conversations[session_id],
                    model=model or self.default_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            # 添加助手回复到历史
            if result.get("success"):
                self.conversations[session_id].append({
                    "role": "assistant",
                    "content": result["response"]
                })
                
                # 限制历史长度（保留最近20条消息）
                if len(self.conversations[session_id]) > 20:
                    self.conversations[session_id] = self.conversations[session_id][-20:]
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"抱歉，我遇到了一个错误：{str(e)}"
            }
    
    async def _call_openai(
        self,
        messages: List[Dict],
        model: str,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """调用OpenAI API"""
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OpenAI API Key未配置",
                "response": "请设置OPENAI_API_KEY环境变量"
            }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.openai_base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data["choices"][0]["message"]["content"],
                        "model": data["model"],
                        "tokens": data["usage"]["total_tokens"]
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API错误: {response.status_code}",
                        "response": f"OpenAI API返回错误：{response.text}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"调用OpenAI失败：{str(e)}"
            }
    
    async def _call_ollama(
        self,
        messages: List[Dict],
        model: str,
        temperature: float
    ) -> Dict[str, Any]:
        """调用Ollama本地模型"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/chat",
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": temperature
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "response": data["message"]["content"],
                        "model": model,
                        "tokens": data.get("eval_count", 0)
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Ollama错误: {response.status_code}",
                        "response": "Ollama服务不可用，请检查服务是否运行"
                    }
                    
        except httpx.ConnectError:
            return {
                "success": False,
                "error": "无法连接Ollama",
                "response": "无法连接到Ollama服务，请确保Ollama正在运行（默认端口11434）"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": f"调用Ollama失败：{str(e)}"
            }
    
    def clear_history(self, session_id: str):
        """清空对话历史"""
        if session_id in self.conversations:
            self.conversations[session_id] = []
    
    def get_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.conversations.get(session_id, [])


# 全局LLM服务实例
_llm_service = None

def get_llm_service() -> LLMService:
    """获取全局LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


print("✅ LLM服务已加载")
print(f"   - OpenAI: {'已配置' if os.getenv('OPENAI_API_KEY') else '未配置'}")
print(f"   - Ollama: {'启用' if os.getenv('USE_OLLAMA', 'false').lower() == 'true' else '禁用'}")

