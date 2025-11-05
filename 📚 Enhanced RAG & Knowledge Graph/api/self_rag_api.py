"""
Self-RAG API
Self-RAG API端点

提供Self-RAG功能的API接口
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

# 尝试导入依赖，如果失败也不影响router注册
_SELF_RAG_AVAILABLE = False
try:
    # 使用绝对导入避免相对导入问题
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    try:
        from core.self_rag import get_self_rag, RetrievalDecision
        _SELF_RAG_AVAILABLE = True
    except ImportError:
        from ..core.self_rag import get_self_rag, RetrievalDecision
        _SELF_RAG_AVAILABLE = True
except ImportError:
    # 依赖不可用，但router仍然可以注册
    RetrievalDecision = None
    def get_self_rag(*args, **kwargs):
        raise ImportError("Self-RAG模块未找到")

# 延迟导入require_api_key以避免循环依赖
def _get_require_api_key():
    """获取API密钥验证依赖（延迟导入）"""
    try:
        from api.app import require_api_key
    except ImportError:
        from .app import require_api_key
    return require_api_key

router = APIRouter(prefix="/self-rag", tags=["Self-RAG API"])


class SelfRAGQueryRequest(BaseModel):
    """Self-RAG查询请求"""
    query: str
    context: Optional[str] = None
    top_k: int = 5
    max_iterations: int = 3
    enable_self_assessment: bool = True
    enable_iterative_retrieval: bool = True


class SelfRAGQueryResponse(BaseModel):
    """Self-RAG查询响应"""
    documents: List[Dict[str, Any]]
    context: str
    iterations: int
    assessments: List[str]
    relevance_level: str
    confidence: float
    decision_reasoning: str


@router.post("/retrieve", response_model=SelfRAGQueryResponse)
async def self_rag_retrieve(
    request: SelfRAGQueryRequest,
    _: bool = Depends(_get_require_api_key()),
) -> SelfRAGQueryResponse:
    """
    Self-RAG检索（差距2：自适应学习能力）
    
    实现Self-RAG功能：
    1. 自我评估检索结果相关性
    2. 自主决定是否需要更多检索
    3. 动态调整检索策略
    4. 基于评估的迭代检索
    
    Args:
        request: Self-RAG查询请求
        _: API密钥验证
        
    Returns:
        Self-RAG查询响应
    """
    try:
        from ..core.self_rag import get_self_rag
        from ..core.enhanced_rag_retrieval import EnhancedRAGRetrieval
        
        # 获取RAG检索器
        rag_retriever = None
        try:
            rag_retriever = EnhancedRAGRetrieval()
        except Exception:
            pass
        
        # 获取Self-RAG实例
        self_rag = get_self_rag(rag_retriever=rag_retriever)
        
        # 设置参数
        self_rag.max_iterations = request.max_iterations
        self_rag.enable_self_assessment = request.enable_self_assessment
        self_rag.enable_iterative_retrieval = request.enable_iterative_retrieval
        
        # 执行Self-RAG检索
        result = await self_rag.retrieve_with_assessment(
            query=request.query,
            context=request.context,
            top_k=request.top_k,
        )
        
        # 提取决策理由
        decision_reasoning = ""
        if result.get("assessments"):
            last_assessment = result["assessments"][-1] if result["assessments"] else ""
            decision_reasoning = f"最终决策: {last_assessment}"
        
        return SelfRAGQueryResponse(
            documents=result.get("documents", []),
            context=result.get("context", ""),
            iterations=result.get("iterations", 0),
            assessments=result.get("assessments", []),
            relevance_level=result.get("relevance_level", "unknown"),
            confidence=result.get("confidence", 0.0),
            decision_reasoning=decision_reasoning,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Self-RAG检索失败: {str(e)}"
        )

