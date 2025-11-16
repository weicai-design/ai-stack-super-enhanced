"""
AI Agent API
提供智能交互接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import time

from .agent_engine import AgentEngine

router = APIRouter(prefix="/agent", tags=["AI Agent"])

# Agent引擎实例
agent_engine = AgentEngine()


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    session_id: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    message: str
    result: Optional[dict] = None
    workflow: list
    performance: dict
    intent: dict
    expert: str
    success: bool


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    AI Agent智能聊天接口
    
    工作流程：
    1. RAG检索 → 2. 意图识别 → 3. 专家路由 → 4. 指令生成 
    → 5. 执行指令 → 6. 二次RAG → 7. 综合结果
    
    性能目标: 2秒内完成
    """
    try:
        # 调用Agent引擎
        response = await agent_engine.process_message(
            message=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(**response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    return {
        "session_id": session_id,
        "status": "active",
        "message_count": agent_engine.session_memory.get(session_id, {}).get("count", 0)
    }


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """清除会话"""
    if session_id in agent_engine.session_memory:
        del agent_engine.session_memory[session_id]
    return {"message": f"Session {session_id} cleared"}


@router.get("/performance")
async def get_performance():
    """获取性能统计"""
    return {
        "cache_size": len(agent_engine.rag_cache),
        "session_count": len(agent_engine.session_memory),
        "avg_response_time": "1.5s",  # 示例
        "target": "< 2.0s"
    }


@router.get("/experts")
async def list_experts():
    """列出所有专家"""
    return {
        "experts": [
            {"name": "财务专家", "icon": "💰", "type": "finance", "capabilities": ["财务看板", "盈亏分析", "报表查询"]},
            {"name": "股票专家", "icon": "📈", "type": "stock", "capabilities": ["股票查询", "行情分析", "交易建议"]},
            {"name": "内容专家", "icon": "✍️", "type": "content", "capabilities": ["内容创作", "素材收集", "效果分析"]},
            {"name": "趋势专家", "icon": "📊", "type": "trend", "capabilities": ["趋势分析", "数据爬取", "报告生成"]},
            {"name": "ERP专家", "icon": "🏭", "type": "erp", "capabilities": ["订单管理", "客户管理", "库存查询"]},
            {"name": "运营专家", "icon": "⚙️", "type": "operations", "capabilities": ["运营看板", "流程管理", "统计分析"]},
            {"name": "通用助手", "icon": "🤖", "type": "general", "capabilities": ["通用查询", "信息检索", "任务执行"]}
        ]
    }


@router.post("/batch")
async def batch_process(requests: list[ChatRequest]):
    """批量处理"""
    results = []
    for req in requests:
        try:
            result = await agent_engine.process_message(
                message=req.message,
                session_id=req.session_id
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "success": False})
    
    return {"results": results, "count": len(results)}






















