#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
53个AI专家模型API接口（T004-T011）

提供RESTful API访问所有53个专家
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from core.experts import (
    get_all_experts,
    get_expert_count,
    get_rag_experts,
    get_erp_experts,
    get_content_experts,
    get_trend_experts,
    get_stock_experts,
    get_operations_finance_experts,
    get_coding_experts,
    ExpertCollaborationHub,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ 请求/响应模型 ============

class ExpertAnalysisRequest(BaseModel):
    """专家分析请求"""
    expert_id: str
    data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None


class ExpertAnalysisResponse(BaseModel):
    """专家分析响应"""
    expert_id: str
    expert_name: str
    result: Dict[str, Any]
    success: bool
    message: str = ""


class ExpertListResponse(BaseModel):
    """专家列表响应"""
    experts: Dict[str, Any]
    count: Dict[str, int]
    total: int


class CollaborationSessionRequest(BaseModel):
    """协同会话请求"""
    topic: str
    initiator: str
    goals: List[str]
    experts: List[Dict[str, Any]]
    channel: str = "multi"


class CollaborationContributionRequest(BaseModel):
    """协同贡献请求"""
    session_id: str
    expert_id: str
    expert_name: str
    summary: str
    channel: str
    action_items: Optional[List[str]] = None
    impact_score: float = 0.5
    references: Optional[List[str]] = None


# ============ API端点 ============

@router.get("/", response_model=ExpertListResponse)
async def list_all_experts():
    """
    获取所有53个专家列表
    
    Returns:
        所有专家的列表和统计信息
    """
    try:
        experts = get_all_experts()
        count = get_expert_count()
        
        # 格式化专家信息
        experts_info = {}
        for expert_id, expert in experts.items():
            experts_info[expert_id] = {
                "id": expert_id,
                "name": getattr(expert, "name", expert_id),
                "expert_id": getattr(expert, "expert_id", expert_id),
            }
        
        # 创建统计信息字典
        count_info = {
            "total": count,
            "rag": len([k for k in experts.keys() if k.startswith("rag_")]),
            "erp": len([k for k in experts.keys() if k.startswith("erp_")]),
            "content": len([k for k in experts.keys() if k.startswith("content_")]),
            "trend": len([k for k in experts.keys() if k.startswith("trend_")]),
            "stock": len([k for k in experts.keys() if k.startswith("stock_")]),
            "finance": len([k for k in experts.keys() if k.startswith("finance_")]),
            "coding": len([k for k in experts.keys() if k.startswith("coding_")])
        }
        
        return ExpertListResponse(
            experts=experts_info,
            count=count_info,
            total=count,
        )
    except Exception as e:
        logger.error(f"获取专家列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取专家列表失败: {str(e)}")


@router.get("/count", response_model=Dict[str, int])
async def get_expert_statistics():
    """
    获取专家统计信息
    
    Returns:
        各模块专家数量统计
    """
    try:
        experts = get_all_experts()
        total_count = get_expert_count()
        
        # 创建详细的统计信息字典
        count_info = {
            "total": total_count,
            "rag": len([k for k in experts.keys() if k.startswith("rag_")]),
            "erp": len([k for k in experts.keys() if k.startswith("erp_")]),
            "content": len([k for k in experts.keys() if k.startswith("content_")]),
            "trend": len([k for k in experts.keys() if k.startswith("trend_")]),
            "stock": len([k for k in experts.keys() if k.startswith("stock_")]),
            "finance": len([k for k in experts.keys() if k.startswith("finance_")]),
            "coding": len([k for k in experts.keys() if k.startswith("coding_")])
        }
        
        return count_info
    except Exception as e:
        logger.error(f"获取专家统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取专家统计失败: {str(e)}")


@router.post("/analyze", response_model=ExpertAnalysisResponse)
async def analyze_with_expert(request: ExpertAnalysisRequest):
    """
    使用指定专家进行分析
    
    Args:
        request: 分析请求
        
    Returns:
        分析结果
    """
    try:
        experts = get_all_experts()
        
        if request.expert_id not in experts:
            raise HTTPException(
                status_code=404,
                detail=f"专家 {request.expert_id} 不存在"
            )
        
        expert = experts[request.expert_id]
        expert_name = getattr(expert, "name", request.expert_id)
        
        # 根据专家类型调用相应的分析方法
        if hasattr(expert, "analyze_knowledge"):
            result = await expert.analyze_knowledge(
                request.data.get("knowledge_items", []),
                request.context
            )
        elif hasattr(expert, "analyze_quality"):
            result = await expert.analyze_quality(
                request.data,
                request.context
            )
        elif hasattr(expert, "analyze_planning"):
            result = await expert.analyze_planning(
                request.data,
                request.context
            )
        elif hasattr(expert, "analyze_collection"):
            result = await expert.analyze_collection(
                request.data,
                request.context
            )
        elif hasattr(expert, "analyze_quote"):
            result = await expert.analyze_quote(
                request.data,
                request.context
            )
        elif hasattr(expert, "analyze_operations"):
            result = await expert.analyze_operations(
                request.data,
                request.context
            )
        elif hasattr(expert, "analyze_generation"):
            result = await expert.analyze_generation(
                request.data,
                request.context
            )
        else:
            # 通用分析接口
            if hasattr(expert, "analyze"):
                result = await expert.analyze(request.data)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"专家 {request.expert_id} 不支持分析功能"
                )
        
        # 转换为字典
        if hasattr(result, "__dict__"):
            result_dict = {
                "domain": getattr(result, "domain", None),
                "stage": getattr(result, "stage", None),
                "dimension": getattr(result, "dimension", None),
                "confidence": getattr(result, "confidence", 0),
                "score": getattr(result, "score", 0),
                "accuracy": getattr(result, "accuracy", 0),
                "insights": getattr(result, "insights", []),
                "recommendations": getattr(result, "recommendations", []),
                "metadata": getattr(result, "metadata", {}),
            }
        else:
            result_dict = result if isinstance(result, dict) else {"result": str(result)}
        
        return ExpertAnalysisResponse(
            expert_id=request.expert_id,
            expert_name=expert_name,
            result=result_dict,
            success=True,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"专家分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"专家分析失败: {str(e)}")


# ============ 专家协同API ============

@router.post("/collaboration/session")
async def create_collaboration_session(request: CollaborationSessionRequest):
    """
    创建专家协同会话
    
    Args:
        request: 协同会话请求
        
    Returns:
        会话信息
    """
    try:
        hub = ExpertCollaborationHub()
        session = await hub.start_session(
            topic=request.topic,
            initiator=request.initiator,
            goals=request.goals,
            experts=request.experts,
            channel=request.channel,
        )
        return session
    except Exception as e:
        logger.error(f"创建协同会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建协同会话失败: {str(e)}")


@router.post("/collaboration/contribution")
async def add_collaboration_contribution(request: CollaborationContributionRequest):
    """
    添加专家贡献
    
    Args:
        request: 贡献请求
        
    Returns:
        更新后的会话信息
    """
    try:
        hub = ExpertCollaborationHub()
        session = await hub.add_contribution(
            session_id=request.session_id,
            expert_id=request.expert_id,
            expert_name=request.expert_name,
            summary=request.summary,
            channel=request.channel,
            action_items=request.action_items,
            impact_score=request.impact_score,
            references=request.references,
        )
        return session
    except Exception as e:
        logger.error(f"添加贡献失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"添加贡献失败: {str(e)}")


@router.get("/collaboration/session/{session_id}")
async def get_collaboration_session(session_id: str):
    """
    获取协同会话详情
    
    Args:
        session_id: 会话ID
        
    Returns:
        会话详情
    """
    try:
        hub = ExpertCollaborationHub()
        session = await hub.get_session(session_id)
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取会话失败: {str(e)}")


@router.get("/collaboration/sessions/active")
async def get_active_sessions(limit: int = 5):
    """
    获取活跃协同会话列表
    
    Args:
        limit: 返回数量限制
        
    Returns:
        活跃会话列表
    """
    try:
        hub = ExpertCollaborationHub()
        sessions = await hub.get_active_sessions(limit=limit)
        return {"sessions": sessions, "count": len(sessions)}
    except Exception as e:
        logger.error(f"获取活跃会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取活跃会话失败: {str(e)}")


@router.get("/collaboration/summary")
async def get_collaboration_summary(limit: int = 50):
    """
    获取协同统计摘要
    
    Args:
        limit: 统计范围限制
        
    Returns:
        统计摘要
    """
    try:
        hub = ExpertCollaborationHub()
        summary = await hub.get_summary(limit=limit)
        return summary
    except Exception as e:
        logger.error(f"获取协同摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取协同摘要失败: {str(e)}")


@router.post("/collaboration/session/{session_id}/finalize")
async def finalize_collaboration_session(
    session_id: str,
    owner: str,
    summary: str,
    kpis: Optional[List[str]] = None,
    followups: Optional[List[str]] = None,
):
    """
    完成协同会话
    
    Args:
        session_id: 会话ID
        owner: 负责人
        summary: 总结
        kpis: KPI列表
        followups: 后续行动列表
        
    Returns:
        完成的会话信息
    """
    try:
        hub = ExpertCollaborationHub()
        session = await hub.finalize_session(
            session_id=session_id,
            owner=owner,
            summary=summary,
            kpis=kpis,
            followups=followups,
        )
        return session
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"完成会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"完成会话失败: {str(e)}")

