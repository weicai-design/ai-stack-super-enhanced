"""
图表专家API
提供图表类型推荐、配置生成等功能
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import sys
import os

# 添加core目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.chart_expert import ChartExpert, ChartType

router = APIRouter(prefix="/api/chart-expert", tags=["Chart Expert API"])

# 初始化图表专家
chart_expert = ChartExpert()


class ChartRecommendationRequest(BaseModel):
    """图表推荐请求"""
    data: Dict[str, Any]  # 数据字典
    purpose: Optional[str] = None  # 用途（如：趋势分析、对比分析）


class ChartConfigRequest(BaseModel):
    """图表配置生成请求"""
    chart_type: str  # 图表类型
    data: Dict[str, Any]  # 数据字典
    options: Optional[Dict[str, Any]] = None  # 可选配置


@router.post("/recommend")
async def recommend_chart_type(request: ChartRecommendationRequest):
    """
    推荐图表类型
    
    根据数据特征和用途，智能推荐最适合的图表类型
    """
    try:
        recommendations = chart_expert.recommend_chart_type(
            data=request.data,
            purpose=request.purpose
        )
        
        return {
            "success": True,
            "recommendations": recommendations,
            "message": f"为您推荐了{len(recommendations)}种图表类型"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/generate-config")
async def generate_chart_config(request: ChartConfigRequest):
    """
    生成图表配置（ECharts格式）
    
    根据图表类型和数据，自动生成ECharts配置
    """
    try:
        config = chart_expert.generate_chart_config(
            chart_type=request.chart_type,
            data=request.data,
            options=request.options or {}
        )
        
        # 优化配置
        optimized_config = chart_expert.optimize_chart_config(config, request.data)
        
        return {
            "success": True,
            "config": optimized_config,
            "message": f"已生成{request.chart_type}图表配置"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成配置失败: {str(e)}")


@router.post("/analyze-data-pattern")
async def analyze_data_pattern(data: Dict[str, Any] = Body(...)):
    """
    分析数据模式
    
    分析数据特征，识别数据模式（时间序列、类别对比、比例等）
    """
    try:
        pattern = chart_expert.analyze_data_pattern(data)
        
        return {
            "success": True,
            "pattern": pattern.value,
            "suitable_charts": [
                {
                    "chart_type": chart_type.value,
                    "name": info["name"],
                    "description": info["description"]
                }
                for chart_type, info in chart_expert.chart_library.items()
                if pattern in info["suitable_patterns"]
            ],
            "message": f"数据模式：{pattern.value}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/chart-types")
async def get_chart_types():
    """
    获取支持的图表类型列表
    """
    chart_types = []
    for chart_type, info in chart_expert.chart_library.items():
        chart_types.append({
            "type": chart_type.value,
            "name": info["name"],
            "description": info["description"],
            "suitable_patterns": [p.value for p in info["suitable_patterns"]],
            "data_requirements": info["data_requirements"]
        })
    
    return {
        "success": True,
        "chart_types": chart_types,
        "total": len(chart_types)
    }


@router.post("/smart-chart")
async def smart_chart(
    data: Dict[str, Any] = Body(...),
    purpose: Optional[str] = Body(None)
):
    """
    智能图表生成（一站式）
    
    自动分析数据、推荐图表类型、生成配置
    """
    try:
        # 1. 分析数据模式
        pattern = chart_expert.analyze_data_pattern(data)
        
        # 2. 推荐图表类型
        recommendations = chart_expert.recommend_chart_type(data, purpose)
        
        # 3. 为最佳推荐生成配置
        best_chart = recommendations[0] if recommendations else None
        config = None
        if best_chart:
            config = chart_expert.generate_chart_config(
                chart_type=best_chart["chart_type"],
                data=data,
                options={"title": data.get("title", "智能图表")}
            )
            config = chart_expert.optimize_chart_config(config, data)
        
        return {
            "success": True,
            "data_pattern": pattern.value,
            "recommendations": recommendations,
            "best_chart": best_chart,
            "config": config,
            "message": "智能图表生成完成"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")


