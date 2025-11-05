"""
RAG Expert API
RAG专家API

将RAG功能提升到100%的专家级API端点
"""

from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

# 尝试导入依赖，如果失败也不影响router注册
_EXPERT_SYSTEM_AVAILABLE = False
try:
    # 使用绝对导入避免相对导入问题
    import sys
    from pathlib import Path
    core_path = Path(__file__).parent.parent / "core"
    sys.path.insert(0, str(core_path.parent))
    
    try:
        from core.rag_expert_system import (
            get_rag_expert_system,
            ExpertDomain,
            ReasoningType,
        )
        _EXPERT_SYSTEM_AVAILABLE = True
    except ImportError:
        # 回退到相对导入
        from ..core.rag_expert_system import (
            get_rag_expert_system,
            ExpertDomain,
            ReasoningType,
        )
        _EXPERT_SYSTEM_AVAILABLE = True
except ImportError:
    # 依赖不可用，但router仍然可以注册
    ExpertDomain = None
    ReasoningType = None
    def get_rag_expert_system(*args, **kwargs):
        raise ImportError("专家系统模块未找到")

# 延迟导入require_api_key以避免循环依赖
def _get_require_api_key():
    """获取API密钥验证依赖（延迟导入）"""
    try:
        from api.app import require_api_key
    except ImportError:
        from .app import require_api_key
    return require_api_key

router = APIRouter(prefix="/expert", tags=["Expert RAG API"])


class ExpertQueryRequest(BaseModel):
    """专家查询请求"""
    query: str
    domain: Optional[str] = None  # 可选的领域指定
    enable_reasoning: bool = True
    expected_depth: Optional[int] = None


class ExpertAnswerResponse(BaseModel):
    """专家答案响应"""
    answer: str
    domain: str
    confidence: float
    sources: List[Dict[str, Any]]
    reasoning_steps: List[str]
    related_concepts: List[str]
    recommendations: List[str]
    query_analysis: Dict[str, Any]


@router.post("/query", response_model=ExpertAnswerResponse)
async def expert_query(
    request: ExpertQueryRequest,
    _: bool = Depends(_get_require_api_key()),
) -> ExpertAnswerResponse:
    """
    专家级查询（需求：将RAG功能提升到100%）
    
    提供专家级的知识处理和问答能力：
    1. 深度查询理解（领域识别、复杂度评估）
    2. 专家级检索（领域特定、智能扩展）
    3. 专家级推理（多种推理类型）
    4. 专家级答案生成（高质量、结构化）
    5. 专家建议和推荐
    
    Args:
        request: 专家查询请求
        _: API密钥验证
        
    Returns:
        专家级答案响应
        
    Raises:
        HTTPException: 如果查询失败
    """
    if not _EXPERT_SYSTEM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="专家系统功能暂未完全实现，依赖模块未找到。请检查核心模块是否正确安装。"
        )
    
    try:
        # 延迟导入避免循环依赖
        try:
            from core.rag_expert_system import get_rag_expert_system
            from core.enhanced_rag_retrieval import EnhancedRAGRetrieval
            from knowledge_graph.enhanced_kg_query import get_kg_query_engine
        except ImportError:
            from ..core.rag_expert_system import get_rag_expert_system
            from ..core.enhanced_rag_retrieval import EnhancedRAGRetrieval
            from ..knowledge_graph.enhanced_kg_query import get_kg_query_engine
        
        # 获取RAG检索器（如果可用）
        rag_retriever = None
        try:
            rag_retriever = EnhancedRAGRetrieval()
        except Exception:
            pass
        
        # 获取知识图谱查询引擎（如果可用）
        kg_query_engine = None
        try:
            from ..api.app import _kg_nodes, _kg_edges
            if _kg_nodes and _kg_edges:
                kg_query_engine = get_kg_query_engine(_kg_nodes, _kg_edges)
        except Exception:
            pass
        
        # 获取专家系统
        expert_system = get_rag_expert_system(
            rag_retriever=rag_retriever,
            kg_query_engine=kg_query_engine,
        )
        
        # 执行专家查询
        answer = await expert_system.generate_expert_answer(
            query=request.query,
            analysis=None,  # 自动分析
        )
        
        # 构建响应
        return ExpertAnswerResponse(
            answer=answer.answer,
            domain=answer.domain.value,
            confidence=answer.confidence,
            sources=answer.sources,
            reasoning_steps=answer.reasoning_steps,
            related_concepts=answer.related_concepts,
            recommendations=answer.recommendations,
            query_analysis={
                "domain": answer.domain.value,
                "confidence": answer.confidence,
                "has_reasoning": len(answer.reasoning_steps) > 0,
            },
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"专家查询失败: {str(e)}"
        )


@router.post("/analyze-query")
async def analyze_query(
    query: str = Query(..., description="要分析的查询"),
    _: bool = Depends(require_api_key),
) -> Dict[str, Any]:
    """
    专家级查询分析
    
    分析查询的领域、复杂度、需要的推理类型等
    
    Args:
        query: 查询文本
        _: API密钥验证
        
    Returns:
        查询分析结果
    """
    try:
        from ..core.rag_expert_system import get_rag_expert_system
        
        expert_system = get_rag_expert_system()
        analysis = expert_system.analyze_query(query)
        
        return {
            "query": analysis.query,
            "domain": analysis.domain.value,
            "complexity": analysis.complexity,
            "requires_reasoning": analysis.requires_reasoning,
            "reasoning_types": [rt.value for rt in analysis.reasoning_types],
            "key_concepts": analysis.key_concepts,
            "expected_depth": analysis.expected_depth,
            "confidence": analysis.confidence,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询分析失败: {str(e)}"
        )


@router.get("/domains")
async def get_expert_domains(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    获取支持的专家领域列表
    
    Returns:
        支持的领域列表及其描述
    """
    domains_info = {
        "general": "通用领域",
        "technical": "技术领域（编程、算法、系统）",
        "business": "商业领域（营销、市场、客户）",
        "medical": "医疗领域（疾病、治疗、健康）",
        "legal": "法律领域（法规、合同、诉讼）",
        "financial": "金融领域（投资、股票、财务）",
        "scientific": "科学领域（研究、实验、理论）",
        "educational": "教育领域（学习、课程、教学）",
    }
    
    return {
        "domains": domains_info,
        "total": len(domains_info),
    }


@router.get("/reasoning-types")
async def get_reasoning_types(_: bool = Depends(require_api_key)) -> Dict[str, Any]:
    """
    获取支持的推理类型列表
    
    Returns:
        支持的推理类型及其描述
    """
    reasoning_info = {
        "deductive": "演绎推理（从一般到特殊）",
        "inductive": "归纳推理（从特殊到一般）",
        "abductive": "溯因推理（最佳解释推理）",
        "analogical": "类比推理（基于相似性）",
        "causal": "因果推理（因果关系分析）",
    }
    
    return {
        "reasoning_types": reasoning_info,
        "total": len(reasoning_info),
    }

