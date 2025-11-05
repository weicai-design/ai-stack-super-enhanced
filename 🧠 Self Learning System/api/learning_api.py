"""
自我学习系统 - API接口
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from core.function_analyzer import FunctionAnalyzer
from core.problem_detector import ProblemDetector
from core.optimization_suggester import OptimizationSuggester
from core.user_learning import UserLearning

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning", tags=["learning"])

# 初始化核心组件
function_analyzer = FunctionAnalyzer()
problem_detector = ProblemDetector()
optimization_suggester = OptimizationSuggester()
user_learning = UserLearning()


# ==================== Pydantic 模型 ====================

class FunctionUsageRecord(BaseModel):
    """功能使用记录"""
    module_name: str
    function_name: str
    success: bool
    response_time: float
    error: Optional[str] = None


class UserActionRecord(BaseModel):
    """用户行为记录"""
    action_type: str
    module: str
    function: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class FeedbackRequest(BaseModel):
    """反馈请求"""
    suggestion_id: str
    response: str  # accepted/rejected/ignored
    comment: Optional[str] = None


# ==================== 功能分析 API ====================

@router.post("/record/usage")
async def record_function_usage(record: FunctionUsageRecord):
    """记录功能使用情况"""
    try:
        function_analyzer.record_function_usage(
            record.module_name,
            record.function_name,
            record.success,
            record.response_time,
            record.error
        )
        
        return {
            "success": True,
            "message": "使用记录已保存"
        }
        
    except Exception as e:
        logger.error(f"记录功能使用失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/module/{module_name}")
async def analyze_module(module_name: str):
    """分析模块性能"""
    try:
        analysis = function_analyzer.analyze_module_performance(module_name)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"分析模块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/all")
async def analyze_all_modules():
    """分析所有模块"""
    try:
        analysis = function_analyzer.analyze_all_modules()
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"分析所有模块失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/function/{module_name}/{function_name}")
async def analyze_function(module_name: str, function_name: str):
    """分析特定功能"""
    try:
        details = function_analyzer.get_function_details(module_name, function_name)
        
        return {
            "success": True,
            "details": details
        }
        
    except Exception as e:
        logger.error(f"分析功能失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analyze/unused")
async def get_unused_functions(days: int = 7):
    """获取未使用的功能"""
    try:
        unused = function_analyzer.identify_unused_functions(days)
        
        return {
            "success": True,
            "unused_functions": unused
        }
        
    except Exception as e:
        logger.error(f"获取未使用功能失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 问题检测 API ====================

@router.post("/problems/detect")
async def detect_problems():
    """检测问题"""
    try:
        # 从功能分析器获取指标
        metrics = function_analyzer.function_metrics
        
        # 检测问题
        problems = problem_detector.detect_problems_from_metrics(metrics)
        
        return {
            "success": True,
            "problems": problems,
            "count": len(problems)
        }
        
    except Exception as e:
        logger.error(f"问题检测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/summary")
async def get_problem_summary():
    """获取问题摘要"""
    try:
        summary = problem_detector.get_problem_summary()
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"获取问题摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/problems/trends")
async def get_problem_trends(hours: int = 24):
    """获取问题趋势"""
    try:
        trends = problem_detector.analyze_problem_trends(hours)
        
        return {
            "success": True,
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"获取问题趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/problems/{problem_id}/resolve")
async def mark_problem_resolved(problem_id: str, resolution: str):
    """标记问题已解决"""
    try:
        success = problem_detector.mark_problem_resolved(problem_id, resolution)
        
        return {
            "success": success,
            "message": "问题已标记为解决" if success else "问题不存在"
        }
        
    except Exception as e:
        logger.error(f"标记问题解决失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 优化建议 API ====================

@router.get("/suggestions/function/{module_name}/{function_name}")
async def get_function_suggestions(module_name: str, function_name: str):
    """获取功能优化建议"""
    try:
        # 获取功能详情
        details = function_analyzer.get_function_details(module_name, function_name)
        
        # 生成建议
        suggestions = optimization_suggester.generate_suggestions_for_function(details)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"生成功能建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/module/{module_name}")
async def get_module_suggestions(module_name: str):
    """获取模块优化建议"""
    try:
        # 分析模块
        analysis = function_analyzer.analyze_module_performance(module_name)
        
        # 生成建议
        suggestions = optimization_suggester.generate_module_suggestions(analysis)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"生成模块建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/system")
async def get_system_suggestions():
    """获取系统优化建议"""
    try:
        # 分析所有模块
        all_analysis = function_analyzer.analyze_all_modules()
        
        # 生成建议
        suggestions = optimization_suggester.generate_system_suggestions(all_analysis)
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"生成系统建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/plan")
async def get_improvement_plan(weeks: int = 4):
    """获取改进计划"""
    try:
        # 获取所有建议
        all_analysis = function_analyzer.analyze_all_modules()
        all_suggestions = optimization_suggester.generate_system_suggestions(all_analysis)
        
        # 生成计划
        plan = optimization_suggester.generate_improvement_plan(all_suggestions, weeks)
        
        return {
            "success": True,
            "plan": plan
        }
        
    except Exception as e:
        logger.error(f"生成改进计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 用户学习 API ====================

@router.post("/user/action")
async def record_user_action(action: UserActionRecord):
    """记录用户行为"""
    try:
        user_learning.record_user_action(
            action.action_type,
            action.module,
            action.function,
            action.context
        )
        
        return {
            "success": True,
            "message": "用户行为已记录"
        }
        
    except Exception as e:
        logger.error(f"记录用户行为失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/preferences")
async def get_user_preferences():
    """获取用户偏好"""
    try:
        preferences = user_learning.analyze_user_preferences()
        
        return {
            "success": True,
            "preferences": preferences
        }
        
    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/workflows")
async def get_user_workflows():
    """获取用户工作流模式"""
    try:
        workflows = user_learning.identify_workflow_patterns()
        
        return {
            "success": True,
            "workflows": workflows
        }
        
    except Exception as e:
        logger.error(f"获取用户工作流失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/suggestions")
async def get_personalized_suggestions():
    """获取个性化建议"""
    try:
        suggestions = user_learning.generate_personalized_suggestions()
        
        return {
            "success": True,
            "suggestions": suggestions
        }
        
    except Exception as e:
        logger.error(f"获取个性化建议失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """提交用户反馈"""
    try:
        user_learning.learn_from_feedback(
            feedback.suggestion_id,
            {
                "response": feedback.response,
                "comment": feedback.comment
            }
        )
        
        return {
            "success": True,
            "message": "反馈已记录"
        }
        
    except Exception as e:
        logger.error(f"提交反馈失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/profile")
async def get_user_profile():
    """获取用户画像"""
    try:
        profile = user_learning.get_user_profile()
        
        return {
            "success": True,
            "profile": profile
        }
        
    except Exception as e:
        logger.error(f"获取用户画像失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计 API ====================

@router.get("/statistics/overview")
async def get_learning_overview():
    """获取学习系统统计概览"""
    try:
        # 功能分析统计
        all_analysis = function_analyzer.analyze_all_modules()
        
        # 问题统计
        problem_summary = problem_detector.get_problem_summary()
        
        # 用户统计
        user_preferences = user_learning.analyze_user_preferences()
        
        overview = {
            "timestamp": all_analysis.get("timestamp"),
            "functions": {
                "total": all_analysis["overall"]["total_functions"],
                "total_usage": all_analysis["overall"]["total_usage"],
                "success_rate": all_analysis["overall"]["overall_success_rate"]
            },
            "problems": {
                "total": problem_summary.get("total_problems", 0),
                "status": problem_summary.get("status", "unknown"),
                "critical_count": problem_summary.get("by_severity", {}).get("critical", 0)
            },
            "user": {
                "total_actions": user_preferences.get("total_actions", 0),
                "activity_level": user_learning._calculate_activity_level()
            }
        }
        
        return {
            "success": True,
            "overview": overview
        }
        
    except Exception as e:
        logger.error(f"获取统计概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

