"""
资源自动调节器API接口 - AI-STACK优化：支持RESTful API设计

功能：
1. 提供资源监控状态查询
2. 支持调节建议获取和执行
3. 提供统计信息展示
4. 支持配置动态调整

API设计原则：
- RESTful风格
- 统一错误处理
- 请求参数验证
- 响应数据标准化
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import logging

# 导入资源调节器
from core.resource_auto_adjuster import (
    ResourceAutoAdjuster, ResourceConfig, ResourceIssue, 
    AdjustmentSuggestion, ResourceIssueType, AdjustmentAction
)

# 创建路由器
router = APIRouter(prefix="/api/resource-adjuster", tags=["Resource Auto Adjuster"])

# 全局调节器实例
_adjuster_instance = None


def get_adjuster() -> ResourceAutoAdjuster:
    """获取调节器实例 - AI-STACK优化：支持依赖注入"""
    global _adjuster_instance
    if _adjuster_instance is None:
        # 初始化调节器
        config = ResourceConfig()
        _adjuster_instance = ResourceAutoAdjuster(config=config)
    return _adjuster_instance


def create_response(data: Any = None, message: str = "成功", status: str = "success") -> Dict[str, Any]:
    """
    创建标准响应格式 - AI-STACK优化：统一响应格式
    
    Args:
        data: 响应数据
        message: 响应消息
        status: 响应状态
        
    Returns:
        标准响应字典
    """
    return {
        "status": status,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status", summary="获取资源调节器状态")
async def get_adjuster_status(
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    获取资源调节器当前状态
    
    Returns:
        包含调节器状态信息的响应
    """
    try:
        # 获取统计信息
        statistics = adjuster.get_statistics()
        
        # 获取当前问题列表
        issues = adjuster.issues[-10:] if adjuster.issues else []  # 最近10个问题
        
        # 获取配置信息
        config_info = {
            "auto_adjust_enabled": adjuster.config.get("monitoring.enable_auto_adjust", False),
            "monitoring_interval": adjuster.config.get("monitoring.interval", 5),
            "auto_adjust_threshold": adjuster.config.get("monitoring.auto_adjust_threshold", "medium")
        }
        
        status_data = {
            "statistics": statistics,
            "recent_issues": [
                {
                    "id": f"issue_{i}",
                    "type": issue.issue_type.value,
                    "severity": issue.severity,
                    "description": issue.description,
                    "detected_at": issue.detected_at.isoformat() if issue.detected_at else None,
                    "current_value": issue.current_value
                }
                for i, issue in enumerate(issues)
            ],
            "configuration": config_info,
            "system_health": "healthy" if len(issues) == 0 else "warning"
        }
        
        return create_response(status_data, "状态查询成功")
        
    except Exception as e:
        logging.error(f"获取调节器状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"状态查询失败: {str(e)}")


@router.post("/monitor", summary="执行资源监控")
async def monitor_resources(
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    手动触发资源监控
    
    Returns:
        包含监控结果和检测到的问题的响应
    """
    try:
        # 执行资源监控
        issues = await adjuster.monitor_resources()
        
        # 格式化问题数据
        formatted_issues = [
            {
                "id": f"issue_{i}",
                "type": issue.issue_type.value,
                "severity": issue.severity,
                "description": issue.description,
                "detected_at": issue.detected_at.isoformat() if issue.detected_at else None,
                "current_value": issue.current_value,
                "threshold": issue.threshold,
                "affected_modules": issue.affected_modules,
                "metadata": issue.metadata
            }
            for i, issue in enumerate(issues)
        ]
        
        response_data = {
            "issues_detected": len(issues),
            "issues": formatted_issues,
            "monitoring_time": datetime.now().isoformat()
        }
        
        return create_response(response_data, f"监控完成，检测到{len(issues)}个问题")
        
    except Exception as e:
        logging.error(f"资源监控失败: {e}")
        raise HTTPException(status_code=500, detail=f"监控失败: {str(e)}")


@router.get("/issues", summary="获取资源问题列表")
async def get_resource_issues(
    limit: int = Query(10, description="返回的问题数量限制", ge=1, le=100),
    severity: Optional[str] = Query(None, description="问题严重程度过滤"),
    issue_type: Optional[str] = Query(None, description="问题类型过滤"),
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    获取资源问题列表，支持过滤和分页
    
    Args:
        limit: 返回数量限制
        severity: 严重程度过滤
        issue_type: 问题类型过滤
        
    Returns:
        包含问题列表的响应
    """
    try:
        # 过滤问题
        filtered_issues = adjuster.issues
        
        if severity:
            filtered_issues = [issue for issue in filtered_issues if issue.severity == severity]
        
        if issue_type:
            filtered_issues = [issue for issue in filtered_issues if issue.issue_type.value == issue_type]
        
        # 限制数量
        limited_issues = filtered_issues[-limit:]
        
        # 格式化数据
        formatted_issues = [
            {
                "id": f"issue_{i}",
                "type": issue.issue_type.value,
                "severity": issue.severity,
                "description": issue.description,
                "detected_at": issue.detected_at.isoformat() if issue.detected_at else None,
                "current_value": issue.current_value,
                "threshold": issue.threshold,
                "affected_modules": issue.affected_modules,
                "metadata": issue.metadata
            }
            for i, issue in enumerate(limited_issues)
        ]
        
        response_data = {
            "total_issues": len(filtered_issues),
            "returned_issues": len(formatted_issues),
            "issues": formatted_issues
        }
        
        return create_response(response_data, "问题列表获取成功")
        
    except Exception as e:
        logging.error(f"获取问题列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题列表失败: {str(e)}")


@router.post("/issues/{issue_id}/analyze", summary="分析特定问题")
async def analyze_issue(
    issue_id: str,
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    分析特定资源问题并生成调节建议
    
    Args:
        issue_id: 问题ID
        
    Returns:
        包含分析结果和建议的响应
    """
    try:
        # 查找问题（简化实现，实际应该使用数据库存储）
        issue_index = int(issue_id.split('_')[1]) if '_' in issue_id else -1
        
        if issue_index < 0 or issue_index >= len(adjuster.issues):
            raise HTTPException(status_code=404, detail="问题不存在")
        
        issue = adjuster.issues[issue_index]
        
        # 分析问题
        suggestions = await adjuster.analyze_issue(issue)
        
        # 格式化建议数据
        formatted_suggestions = [
            {
                "id": f"suggestion_{i}",
                "action": suggestion.action.value,
                "description": suggestion.description,
                "estimated_improvement": suggestion.estimated_improvement,
                "requires_approval": suggestion.requires_approval,
                "issue_id": issue_id
            }
            for i, suggestion in enumerate(suggestions)
        ]
        
        response_data = {
            "issue": {
                "id": issue_id,
                "type": issue.issue_type.value,
                "severity": issue.severity,
                "description": issue.description
            },
            "suggestions": formatted_suggestions,
            "total_suggestions": len(suggestions)
        }
        
        return create_response(response_data, "问题分析完成")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"分析问题失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/suggestions/{suggestion_id}/execute", summary="执行调节建议")
async def execute_suggestion(
    suggestion_id: str,
    approved: bool = Query(False, description="是否已授权"),
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    执行调节建议
    
    Args:
        suggestion_id: 建议ID
        approved: 是否已授权
        
    Returns:
        包含执行结果的响应
    """
    try:
        # 查找建议（简化实现）
        suggestion_index = int(suggestion_id.split('_')[1]) if '_' in suggestion_id else -1
        
        if suggestion_index < 0 or suggestion_index >= len(adjuster.suggestions):
            raise HTTPException(status_code=404, detail="建议不存在")
        
        suggestion = adjuster.suggestions[suggestion_index]
        
        # 执行调节
        result = await adjuster.execute_adjustment(suggestion, approved=approved)
        
        response_data = {
            "suggestion_id": suggestion_id,
            "action": suggestion.action.value,
            "result": result,
            "executed_at": datetime.now().isoformat()
        }
        
        return create_response(response_data, "调节执行完成")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"执行调节失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.put("/configuration", summary="更新配置")
async def update_configuration(
    config_updates: Dict[str, Any],
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    更新资源调节器配置
    
    Args:
        config_updates: 配置更新字典
        
    Returns:
        包含更新结果的响应
    """
    try:
        # 验证配置更新
        valid_keys = [
            "monitoring.interval", "monitoring.enable_auto_adjust", 
            "monitoring.auto_adjust_threshold", "thresholds.cpu.warning",
            "thresholds.cpu.critical", "thresholds.memory.warning",
            "thresholds.memory.critical", "thresholds.disk.warning",
            "thresholds.disk.critical", "security.require_approval_for_critical",
            "security.max_auto_adjustments_per_hour"
        ]
        
        invalid_keys = [key for key in config_updates.keys() if key not in valid_keys]
        if invalid_keys:
            raise HTTPException(status_code=400, detail=f"无效的配置项: {invalid_keys}")
        
        # 应用配置更新
        for key, value in config_updates.items():
            adjuster.config.set(key, value)
        
        response_data = {
            "updated_config": config_updates,
            "current_config": {
                "monitoring_interval": adjuster.config.get("monitoring.interval"),
                "auto_adjust_enabled": adjuster.config.get("monitoring.enable_auto_adjust"),
                "auto_adjust_threshold": adjuster.config.get("monitoring.auto_adjust_threshold")
            }
        }
        
        logging.info(f"配置已更新: {config_updates}")
        
        return create_response(response_data, "配置更新成功")
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"配置更新失败: {e}")
        raise HTTPException(status_code=500, detail=f"配置更新失败: {str(e)}")


@router.get("/statistics", summary="获取详细统计信息")
async def get_detailed_statistics(
    adjuster: ResourceAutoAdjuster = Depends(get_adjuster)
) -> Dict[str, Any]:
    """
    获取详细的统计信息
    
    Returns:
        包含详细统计信息的响应
    """
    try:
        statistics = adjuster.get_statistics()
        
        return create_response(statistics, "统计信息获取成功")
        
    except Exception as e:
        logging.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")


# 错误处理函数（在应用级别设置中间件）
def create_error_response(error: Exception) -> JSONResponse:
    """创建错误响应"""
    logging.error(f"API请求异常: {error}")
    return JSONResponse(
        status_code=500,
        content=create_response(None, f"服务器内部错误: {str(error)}", "error")
    )