"""
OpenAI API客户端
用于调用GPT-4等模型
"""

import os
import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)

# 尝试导入OpenAI库
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("openai库未安装，将使用模拟模式")


class OpenAIClient:
    """
    OpenAI API客户端
    
    功能:
    1. GPT-4对话生成
    2. 文本分析和总结
    3. 智能问答增强
    4. 内容创作辅助
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化OpenAI客户端"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = "gpt-4"
        
        if HAS_OPENAI and self.api_key:
            openai.api_key = self.api_key
            self.enabled = True
            logger.info("✅ OpenAI客户端已启用（V3.2）")
        else:
            self.enabled = False
            if not HAS_OPENAI:
                logger.info("OpenAI库未安装，使用模拟模式")
            else:
                logger.info("未配置OpenAI API密钥，使用模拟模式")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Dict[str, Any]:
        """
        GPT对话生成
        
        Args:
            messages: 对话消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            生成结果
        """
        if not self.enabled:
            return self._mock_chat_completion(messages)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return {
                "status": "success",
                "content": response.choices[0].message.content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "source": "OpenAI API"
            }
        
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            return self._mock_chat_completion(messages)
    
    def analyze_text(self, text: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        文本分析
        
        Args:
            text: 待分析文本
            analysis_type: 分析类型（summary/sentiment/keywords）
            
        Returns:
            分析结果
        """
        if not self.enabled:
            return self._mock_analysis(text, analysis_type)
        
        prompts = {
            "summary": f"请总结以下文本的核心内容：\n\n{text}",
            "sentiment": f"请分析以下文本的情感倾向（积极/中性/消极）：\n\n{text}",
            "keywords": f"请提取以下文本的关键词（5-10个）：\n\n{text}"
        }
        
        prompt = prompts.get(analysis_type, prompts["summary"])
        
        messages = [
            {"role": "system", "content": "你是一个专业的文本分析助手"},
            {"role": "user", "content": prompt}
        ]
        
        return self.chat_completion(messages, temperature=0.3)
    
    def enhance_rag_answer(
        self,
        query: str,
        context: str,
        answer: str
    ) -> Dict[str, Any]:
        """
        增强RAG问答质量
        
        Args:
            query: 用户问题
            context: 检索到的上下文
            answer: 原始答案
            
        Returns:
            增强后的答案
        """
        if not self.enabled:
            return {"enhanced_answer": answer, "source": "原始答案"}
        
        prompt = f"""
基于以下信息，请提供更准确、更详细的答案：

用户问题：{query}

检索上下文：
{context}

原始答案：
{answer}

请提供改进后的答案：
"""
        
        messages = [
            {"role": "system", "content": "你是一个RAG问答优化助手，擅长基于上下文提供准确答案"},
            {"role": "user", "content": prompt}
        ]
        
        result = self.chat_completion(messages, temperature=0.5)
        return {
            "enhanced_answer": result.get("content", answer),
            "original_answer": answer,
            "source": "GPT-4增强"
        }
    
    def _mock_chat_completion(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """模拟GPT响应"""
        last_message = messages[-1]["content"] if messages else ""
        
        return {
            "status": "success",
            "content": f"[模拟回复] 收到您的消息：{last_message[:50]}...",
            "model": "mock",
            "usage": {"total_tokens": 100},
            "source": "模拟数据"
        }
    
    def _mock_analysis(self, text: str, analysis_type: str) -> Dict[str, Any]:
        """模拟分析结果"""
        results = {
            "summary": f"文本摘要：{text[:100]}...",
            "sentiment": "中性",
            "keywords": ["关键词1", "关键词2", "关键词3"]
        }
        
        return {
            "status": "success",
            "content": results.get(analysis_type, "分析结果"),
            "source": "模拟数据"
        }


# 创建全局实例
openai_client = OpenAIClient()






















