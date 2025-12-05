"""
LLM功能API端点（V3.2新增）
提供LLM增强功能的REST API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

router = APIRouter(prefix="/llm", tags=["LLM Enhancement"])
logger = logging.getLogger(__name__)

# 导入LLM客户端
try:
    from llm.openai_client import openai_client
    logger.info("✅ OpenAI客户端已加载")
except Exception as e:
    openai_client = None
    logger.warning(f"OpenAI客户端加载失败: {e}")


# ==================== 数据模型 ====================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Dict[str, str]] = Field(..., description="对话消息列表")
    temperature: float = Field(default=0.7, description="温度参数")
    max_tokens: int = Field(default=2000, description="最大token数")

class AnalyzeRequest(BaseModel):
    """文本分析请求模型"""
    text: str = Field(..., description="待分析文本")
    analysis_type: str = Field(default="summary", description="分析类型")

class RAGEnhanceRequest(BaseModel):
    """RAG增强请求模型"""
    query: str = Field(..., description="用户问题")
    context: str = Field(..., description="检索上下文")
    answer: str = Field(..., description="原始答案")


# ==================== API端点 ====================

@router.get("/health")
async def health_check():
    """LLM功能健康检查"""
    return {
        "status": "healthy",
        "module": "llm_enhancement",
        "version": "3.2.0",
        "openai_enabled": openai_client.enabled if openai_client else False,
        "features": [
            "chat_completion",
            "text_analysis",
            "rag_enhancement",
            "content_generation"
        ]
    }

@router.post("/chat")
async def chat_completion(request: ChatRequest):
    """GPT对话生成"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="LLM客户端未初始化")
    
    try:
        result = openai_client.chat_completion(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return result
    except Exception as e:
        logger.error(f"对话生成失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_text(request: AnalyzeRequest):
    """文本分析"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="LLM客户端未初始化")
    
    try:
        result = openai_client.analyze_text(
            text=request.text,
            analysis_type=request.analysis_type
        )
        return result
    except Exception as e:
        logger.error(f"文本分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhance-rag")
async def enhance_rag_answer(request: RAGEnhanceRequest):
    """增强RAG问答质量"""
    if not openai_client:
        raise HTTPException(status_code=503, detail="LLM客户端未初始化")
    
    try:
        result = openai_client.enhance_rag_answer(
            query=request.query,
            context=request.context,
            answer=request.answer
        )
        return result
    except Exception as e:
        logger.error(f"RAG增强失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models")
async def list_available_models():
    """列出可用的LLM模型"""
    return {
        "status": "success",
        "models": [
            {
                "name": "gpt-4",
                "provider": "OpenAI",
                "enabled": openai_client.enabled if openai_client else False
            },
            {
                "name": "gpt-3.5-turbo",
                "provider": "OpenAI",
                "enabled": openai_client.enabled if openai_client else False
            },
            {
                "name": "claude-3",
                "provider": "Anthropic",
                "enabled": False
            }
        ]
    }






































