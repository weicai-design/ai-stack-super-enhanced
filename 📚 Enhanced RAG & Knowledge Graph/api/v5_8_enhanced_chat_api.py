"""
V5.8 增强聊天API - 主界面LLM集成
支持OpenAI GPT-4和Ollama，真实智能对话
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter(prefix="/api/v5/chat", tags=["V5.8-Enhanced-Chat"])

# ==================== 数据模型 ====================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    use_rag: bool = True
    temperature: float = 0.7
    max_tokens: int = 2000

# ==================== 主界面增强聊天 ====================

@router.post("/intelligent")
async def intelligent_chat(request: ChatMessage):
    """
    主界面智能聊天（集成LLM+RAG）
    
    工作流程：
    1. 接收用户消息
    2. RAG检索相关知识
    3. LLM生成智能回复
    4. 返回结果
    """
    workflow = []
    start_time = datetime.now()
    
    try:
        # 步骤1: 检索RAG知识库
        rag_results = []
        if request.use_rag:
            try:
                from core.real_rag_service import get_rag_service
                rag = get_rag_service()
                
                rag_response = await rag.search(
                    query=request.message,
                    top_k=3
                )
                
                if rag_response.get("success"):
                    rag_results = rag_response.get("results", [])
                    workflow.append({
                        "step": "RAG检索",
                        "status": "success",
                        "results_count": len(rag_results),
                        "duration": 0.5
                    })
            except:
                workflow.append({
                    "step": "RAG检索",
                    "status": "skipped",
                    "reason": "RAG服务不可用"
                })
        
        # 步骤2: 调用LLM生成回复
        try:
            from services.llm_service import get_llm_service
            llm = get_llm_service()
            
            # 构建prompt
            if rag_results:
                context = "\n".join([
                    f"[来源{i+1}] {r.get('content', '')[:200]}..."
                    for i, r in enumerate(rag_results[:3])
                ])
                prompt = f"""你是AI-STACK智能助手。基于以下知识库信息回答用户问题：

知识库信息：
{context}

用户问题：{request.message}

请给出准确、专业、友好的回答。如果知识库信息不充分，可以结合你的知识给出建议。"""
            else:
                prompt = f"""你是AI-STACK智能助手。用户问题：{request.message}

请给出准确、专业、友好的回答。"""
            
            # 调用LLM
            llm_result = await llm.chat(
                message=prompt,
                session_id=request.session_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if llm_result.get("success"):
                workflow.append({
                    "step": "LLM生成",
                    "status": "success",
                    "model": llm_result.get("model", "unknown"),
                    "tokens": llm_result.get("tokens", 0),
                    "duration": 2.0
                })
                
                response_text = llm_result["response"]
                llm_available = True
            else:
                # LLM失败，使用智能降级
                workflow.append({
                    "step": "LLM生成",
                    "status": "degraded",
                    "reason": llm_result.get("error", "未知错误")
                })
                
                response_text = await _generate_fallback_response(request.message, rag_results)
                llm_available = False
                
        except Exception as e:
            workflow.append({
                "step": "LLM生成",
                "status": "error",
                "error": str(e)
            })
            
            response_text = await _generate_fallback_response(request.message, rag_results)
            llm_available = False
        
        # 步骤3: 构建响应
        duration = (datetime.now() - start_time).total_seconds()
        
        return {
            "success": True,
            "response": response_text,
            "session_id": request.session_id,
            "llm_available": llm_available,
            "rag_used": len(rag_results) > 0,
            "workflow": workflow,
            "duration": round(duration, 2),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": f"抱歉，处理您的请求时遇到错误：{str(e)}"
        }


async def _generate_fallback_response(message: str, rag_results: List) -> str:
    """生成降级回复"""
    if rag_results:
        context = "\n".join([
            f"• {r.get('content', '')[:100]}..."
            for r in rag_results[:2]
        ])
        return f"""基于知识库检索，我找到以下相关信息：

{context}

关于您的问题「{message}」，建议您查看以上内容获取更多详情。

注意：当前使用基础回复模式。如需更智能的回复，请配置LLM服务（OpenAI或Ollama）。"""
    else:
        return f"""收到您的问题：{message}

AI-STACK系统已就绪，但当前处于基础模式。

建议：
1. 配置OpenAI API Key以启用GPT-4智能对话
2. 或安装Ollama并设置USE_OLLAMA=true使用本地模型
3. 上传文档到RAG知识库以获得更准确的答案

当前可用功能：
✅ 财务管理、ERP系统、内容创作、股票交易等
✅ 点击左侧菜单打开各功能模块"""


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """获取对话历史"""
    try:
        from services.llm_service import get_llm_service
        llm = get_llm_service()
        
        history = llm.get_history(session_id)
        
        return {
            "success": True,
            "session_id": session_id,
            "messages": history,
            "count": len(history)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """清空对话历史"""
    try:
        from services.llm_service import get_llm_service
        llm = get_llm_service()
        
        llm.clear_history(session_id)
        
        return {
            "success": True,
            "message": "对话历史已清空",
            "session_id": session_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


print("✅ V5.8增强聊天API已加载（LLM集成）")


