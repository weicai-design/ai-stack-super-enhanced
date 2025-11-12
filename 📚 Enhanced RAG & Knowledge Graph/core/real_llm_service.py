"""
真实的LLM服务集成
支持OpenAI GPT-4和本地Ollama
"""
import os
import asyncio
from typing import Dict, List, Optional, Any
import httpx


class LLMService:
    """LLM服务管理器"""
    
    def __init__(self, provider: str = "auto"):
        """
        初始化LLM服务
        
        Args:
            provider: LLM提供商（openai, ollama, auto）
        """
        self.provider = provider
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_URL", "http://localhost:11434"))
        self.ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # 使用更好的中文模型
        self.ollama_available = False
        
        # 检测Ollama是否可用
        self._check_ollama()
        
        # 自动选择可用的provider
        if provider == "auto":
            if self.openai_api_key:
                self.provider = "openai"
                print("✅ 使用OpenAI GPT-4")
            elif self.ollama_available:
                self.provider = "ollama"
                print(f"✅ 使用本地Ollama - 模型: {self.ollama_model}")
            else:
                self.provider = "ollama"  # 默认ollama，运行时会提示错误
                print("⚠️  OpenAI和Ollama均未配置，将尝试使用Ollama")
    
    def _check_ollama(self):
        """同步检测Ollama是否可用"""
        try:
            import httpx
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(f"{self.ollama_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    self.ollama_available = True
                    print(f"✅ Ollama服务运行中 - 已安装{len(models)}个模型")
                    
                    # 检查推荐的模型是否存在
                    if self.ollama_model not in model_names:
                        # 尝试使用第一个可用的模型
                        if model_names:
                            self.ollama_model = model_names[0]
                            print(f"⚠️  {os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')}未安装，改用: {self.ollama_model}")
        except Exception as e:
            self.ollama_available = False
            print(f"⚠️  Ollama服务未运行: {e}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        生成文本
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成结果
        """
        if self.provider == "openai":
            return await self._generate_openai(prompt, system_prompt, temperature, max_tokens)
        elif self.provider == "ollama":
            return await self._generate_ollama(prompt, system_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的provider: {self.provider}")
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """使用OpenAI API生成"""
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY未设置",
                "provider": "openai",
                "text": ""
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                messages = []
                
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                
                messages.append({"role": "user", "content": prompt})
                
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "text": data["choices"][0]["message"]["content"],
                        "provider": "openai",
                        "model": "gpt-4",
                        "usage": data.get("usage", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API错误: {response.status_code}",
                        "provider": "openai",
                        "text": ""
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "openai",
                "text": ""
            }
    
    async def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """使用本地Ollama生成"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # 检查Ollama是否运行
                try:
                    await client.get(f"{self.ollama_url}/api/tags")
                except:
                    return {
                        "success": False,
                        "error": "Ollama未运行，请先启动Ollama服务",
                        "provider": "ollama",
                        "text": ""
                    }
                
                # 构建完整提示词
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                
                # 调用Ollama API - 使用配置的模型
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": temperature,
                            "num_predict": max_tokens
                        }
                    }
                )
                
                print(f"🔍 Ollama响应状态: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Ollama返回数据: {list(data.keys())}")
                    if "response" in data:
                        return {
                            "success": True,
                            "text": data["response"],
                            "provider": "ollama",
                            "model": self.ollama_model
                        }
                    else:
                        print(f"❌ Ollama返回缺少response字段: {data}")
                        return {
                            "success": False,
                            "error": f"Ollama返回格式错误: 缺少response字段",
                            "provider": "ollama",
                            "text": ""
                        }
                else:
                    error_text = await response.aread()
                    print(f"❌ Ollama API错误: {response.status_code}, {error_text[:200]}")
                    return {
                        "success": False,
                        "error": f"Ollama API错误: {response.status_code}",
                        "provider": "ollama",
                        "text": ""
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "provider": "ollama",
                "text": ""
            }
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        多轮对话
        
        Args:
            messages: 消息列表 [{"role": "user/assistant", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成结果
        """
        if self.provider == "openai":
            return await self._chat_openai(messages, temperature, max_tokens)
        elif self.provider == "ollama":
            # Ollama的chat功能
            return await self._chat_ollama(messages, temperature, max_tokens)
        else:
            raise ValueError(f"不支持的provider: {self.provider}")
    
    async def _chat_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """OpenAI多轮对话"""
        if not self.openai_api_key:
            return {
                "success": False,
                "error": "OPENAI_API_KEY未设置"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4",
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "text": data["choices"][0]["message"]["content"],
                        "provider": "openai",
                        "usage": data.get("usage", {})
                    }
                else:
                    return {
                        "success": False,
                        "error": f"API错误: {response.status_code}"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Ollama多轮对话"""
        try:
            # 将消息转换为单个prompt
            prompt = "\n\n".join([
                f"{msg['role']}: {msg['content']}" for msg in messages
            ])
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "text": data["response"],
                        "provider": "ollama"
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Ollama错误: {response.status_code}"
                    }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_provider(self) -> str:
        """获取当前provider"""
        return self.provider
    
    async def test_connection(self) -> Dict[str, Any]:
        """测试LLM连接"""
        if self.provider == "openai":
            if not self.openai_api_key:
                return {
                    "success": False,
                    "provider": "openai",
                    "message": "OPENAI_API_KEY未设置"
                }
            
            # 测试简单调用
            result = await self.generate("测试", temperature=0.7)
            return {
                "success": result.get("success", False),
                "provider": "openai",
                "message": "OpenAI API连接正常" if result.get("success") else f"连接失败: {result.get('error')}"
            }
        
        elif self.provider == "ollama":
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{self.ollama_url}/api/tags")
                    if response.status_code == 200:
                        return {
                            "success": True,
                            "provider": "ollama",
                            "message": "Ollama服务运行正常"
                        }
                    else:
                        return {
                            "success": False,
                            "provider": "ollama",
                            "message": "Ollama服务响应异常"
                        }
            except:
                return {
                    "success": False,
                    "provider": "ollama",
                    "message": "Ollama服务未运行"
                }


# 全局LLM服务实例
_llm_service = None

def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(provider="auto")
    return _llm_service


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test():
        llm = get_llm_service()
        
        print(f"✅ LLM服务已加载")
        print(f"📋 当前Provider: {llm.get_provider()}")
        
        # 测试连接
        test_result = await llm.test_connection()
        print(f"🔌 连接测试: {test_result['message']}")
        
        if test_result["success"]:
            # 测试生成
            result = await llm.generate(
                prompt="你好，请介绍一下AI-STACK系统",
                system_prompt="你是AI-STACK的智能助手",
                temperature=0.7
            )
            
            if result["success"]:
                print(f"\n✅ 生成成功:")
                print(f"{result['text'][:200]}...")
            else:
                print(f"\n❌ 生成失败: {result['error']}")
    
    asyncio.run(test())


