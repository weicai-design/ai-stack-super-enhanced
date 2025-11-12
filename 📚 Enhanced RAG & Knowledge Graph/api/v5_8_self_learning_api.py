"""
V5.8 自我学习系统API
提供监视、分析、总结、优化、RAG传递功能
"""

from fastapi import APIRouter, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/v5/learning", tags=["V5.8-Self-Learning"])

# ==================== 数据模型 ====================

class WorkflowData(BaseModel):
    user_message: str
    rag_retrieval_1: Optional[Dict] = {}
    expert_analysis: Optional[Dict] = {}
    function_execution: Optional[Dict] = {}
    rag_retrieval_2: Optional[Dict] = {}
    final_response: str
    duration: float
    success: bool = True

# ==================== 自我学习API ====================

@router.post("/process-workflow")
async def process_workflow(data: WorkflowData):
    """
    处理工作流（完整学习循环）
    
    流程：监视 → 分析 → 总结 → 优化 → 传递RAG
    """
    try:
        from services.self_learning_system import get_self_learning_system
        learning_system = get_self_learning_system()
        
        result = await learning_system.process_workflow(data.dict())
        
        return {
            "success": True,
            "learning_executed": result["learning_cycle_executed"],
            "cycle_count": result["total_cycles"],
            "details": result["results"],
            "message": "工作流已处理，学习循环已执行" if result["learning_cycle_executed"] else "工作流已记录"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/status")
async def get_learning_status():
    """获取自我学习系统状态"""
    try:
        from services.self_learning_system import get_self_learning_system
        learning_system = get_self_learning_system()
        
        status = learning_system.get_learning_status()
        
        return {
            "success": True,
            "status": status,
            "message": "自我学习系统运行中"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/experiences")
async def get_learning_experiences(limit: int = 10):
    """获取学习经验列表"""
    try:
        from services.self_learning_system import get_self_learning_system
        learning_system = get_self_learning_system()
        
        summaries = learning_system.summarizer.summaries[-limit:]
        
        return {
            "success": True,
            "experiences": summaries,
            "total": len(summaries)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/manual-learning")
async def manual_learning_trigger(issue_description: str = Body(...)):
    """手动触发学习（用于测试）"""
    try:
        from services.self_learning_system import get_self_learning_system
        learning_system = get_self_learning_system()
        
        # 创建模拟工作流
        workflow_data = {
            "user_message": "测试学习功能",
            "rag_retrieval_1": {"results_count": 0},  # 故意设置问题
            "final_response": "测试回复",
            "duration": 6.5,  # 故意超时
            "success": False
        }
        
        result = await learning_system.process_workflow(workflow_data)
        
        return {
            "success": True,
            "message": "手动学习循环已执行",
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/save-experience-to-rag/{experience_id}")
async def save_experience_to_rag(experience_id: str):
    """手动将经验保存到RAG"""
    try:
        from services.self_learning_system import get_self_learning_system
        learning_system = get_self_learning_system()
        
        # 查找经验
        summaries = learning_system.summarizer.summaries
        summary = next((s for s in summaries if s["id"] == experience_id), None)
        
        if not summary:
            return {
                "success": False,
                "error": "经验不存在"
            }
        
        # 保存到RAG
        result = await learning_system.rag_integration.save_to_rag(summary)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


print("✅ V5.8自我学习API已加载")


