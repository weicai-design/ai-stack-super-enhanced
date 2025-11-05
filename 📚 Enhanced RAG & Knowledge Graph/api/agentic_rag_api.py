"""
Agentic RAG API
Agentic RAG API端点

提供Agentic RAG功能的API接口
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

# 尝试导入依赖，如果失败也不影响router注册
_AGENTIC_RAG_AVAILABLE = False
try:
    # 使用绝对导入避免相对导入问题
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        from core.agentic_rag import get_agentic_rag
        _AGENTIC_RAG_AVAILABLE = True
    except ImportError:
        from ..core.agentic_rag import get_agentic_rag
        _AGENTIC_RAG_AVAILABLE = True
except ImportError:
    # 依赖不可用，但router仍然可以注册
    def get_agentic_rag(*args, **kwargs):
        raise ImportError("Agentic RAG模块未找到")

# 延迟导入require_api_key以避免循环依赖
def _get_require_api_key():
    """获取API密钥验证依赖（延迟导入）"""
    try:
        from api.app import require_api_key
    except ImportError:
        from .app import require_api_key
    return require_api_key

router = APIRouter(prefix="/agentic-rag", tags=["Agentic RAG API"])


class AgenticTaskRequest(BaseModel):
    """Agentic任务请求"""
    goal: str
    context: Optional[str] = None
    max_iterations: int = 5


class AgenticTaskResponse(BaseModel):
    """Agentic任务响应"""
    task_id: str
    goal: str
    status: str
    iterations: int
    sub_goals: List[Dict[str, Any]]
    result: Dict[str, Any]
    confidence: float


@router.post("/execute", response_model=AgenticTaskResponse)
async def agentic_execute(
    request: AgenticTaskRequest,
    _: bool = Depends(_get_require_api_key()),
) -> AgenticTaskResponse:
    """
    Agentic RAG任务执行（差距7：自主规划）
    
    实现Agentic RAG功能：
    1. 自主规划和迭代优化
    2. 多轮检索规划
    3. 自我改进循环
    4. 任务分解和子目标规划
    5. 执行评估机制
    
    Args:
        request: Agentic任务请求
        _: API密钥验证
        
    Returns:
        Agentic任务响应
    """
    try:
        from ..core.agentic_rag import get_agentic_rag
        
        # 创建简单的RAG检索器适配器
        class SimpleRAGRetriever:
            async def retrieve_for_response(self, user_query: str, top_k: int):
                from ..api.app import _embed_texts, _index_matrix, _docs
                import numpy as np
                
                q = _embed_texts([user_query])[0].astype(np.float32)
                X = _index_matrix()
                scores = (X @ q).tolist()
                order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                items = []
                for i in order:
                    d = _docs[i]
                    items.append({
                        "id": d.id,
                        "document_id": d.id,
                        "content": d.text,
                        "snippet": d.text[:200],
                        "score": float(scores[i]),
                    })
                return {"knowledge_items": items}
        
        # 获取Agentic RAG实例
        rag_retriever = SimpleRAGRetriever()
        agentic_rag = get_agentic_rag(rag_retriever=rag_retriever)
        agentic_rag.max_iterations = request.max_iterations
        
        # 执行任务
        result = await agentic_rag.execute_task(
            goal=request.goal,
            context=request.context,
        )
        
        return AgenticTaskResponse(
            task_id=result.get("task_id", ""),
            goal=result.get("goal", ""),
            status=result.get("status", ""),
            iterations=result.get("iterations", 0),
            sub_goals=result.get("sub_goals", []),
            result=result.get("result", {}),
            confidence=result.get("confidence", 0.0),
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Agentic RAG任务执行失败: {str(e)}"
        )

