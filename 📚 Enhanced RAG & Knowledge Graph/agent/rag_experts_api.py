"""
RAG专家API接口
V4.0 Week 1-2
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .rag_experts import knowledge_expert, search_expert, graph_expert

router = APIRouter(prefix="/rag-experts", tags=["RAG Experts"])


class ExpertChatRequest(BaseModel):
    """专家对话请求"""
    expert_type: str  # knowledge, search, graph
    message: str
    context: Optional[Dict[str, Any]] = None


class DocumentAnalysisRequest(BaseModel):
    """文档分析请求"""
    content: str
    metadata: Optional[Dict[str, Any]] = None


@router.post("/chat")
async def chat_with_expert(request: ExpertChatRequest):
    """
    与RAG专家对话（中文自然语言）
    
    专家类型:
    - knowledge: 知识管理专家
    - search: 检索优化专家
    - graph: 知识图谱专家
    """
    
    experts = {
        "knowledge": knowledge_expert,
        "search": search_expert,
        "graph": graph_expert
    }
    
    expert = experts.get(request.expert_type)
    if not expert:
        raise HTTPException(status_code=400, detail="未知的专家类型")
    
    response = await expert.chat_response(request.message, request.context or {})
    
    return {
        "expert": expert.name,
        "response": response,
        "capabilities": expert.capabilities
    }


@router.post("/analyze-document")
async def analyze_document(request: DocumentAnalysisRequest):
    """
    文档质量分析（知识管理专家）
    """
    
    analysis = await knowledge_expert.analyze_document(
        request.content,
        request.metadata or {}
    )
    
    return {
        "expert": knowledge_expert.name,
        "analysis": analysis
    }


@router.post("/optimize-query")
async def optimize_query(query: str):
    """
    查询优化（检索优化专家）
    """
    
    optimization = await search_expert.optimize_query(query)
    
    return {
        "expert": search_expert.name,
        "optimization": optimization
    }


@router.post("/extract-entities")
async def extract_entities(text: str):
    """
    实体提取（知识图谱专家）
    """
    
    entities = await graph_expert.extract_entities(text)
    
    return {
        "expert": graph_expert.name,
        "entities": entities
    }


@router.post("/build-graph")
async def build_knowledge_graph(documents: List[Dict]):
    """
    构建知识图谱（知识图谱专家）
    """
    
    graph = await graph_expert.build_graph(documents)
    
    return {
        "expert": graph_expert.name,
        "graph": graph
    }


@router.get("/experts")
async def list_rag_experts():
    """列出所有RAG专家"""
    return {
        "experts": [
            {
                "type": "knowledge",
                "name": knowledge_expert.name,
                "capabilities": knowledge_expert.capabilities
            },
            {
                "type": "search",
                "name": search_expert.name,
                "capabilities": search_expert.capabilities
            },
            {
                "type": "graph",
                "name": graph_expert.name,
                "capabilities": graph_expert.capabilities
            }
        ]
    }





