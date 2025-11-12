"""
自定义趋势分析API
支持用户自定义分析维度、时间范围、指标等
"""

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/🔍 Intelligent Trend Analysis')

from analysis.trend_analyzer import TrendAnalyzer
from crawlers.news_crawler import default_crawler_manager

router = APIRouter(prefix="/trend/custom", tags=["Custom Trend Analysis API"])

# 初始化分析器
analyzer = TrendAnalyzer()


class CustomAnalysisRequest(BaseModel):
    """自定义分析请求"""
    # 时间范围
    start_date: Optional[str] = Field(None, description="开始日期 (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="结束日期 (YYYY-MM-DD)")
    time_range: Optional[str] = Field(None, description="时间范围: today/week/month/quarter/year/custom")
    
    # 数据源筛选
    categories: Optional[List[str]] = Field(None, description="类别筛选: policy/tech/industry/hot")
    sources: Optional[List[str]] = Field(None, description="来源筛选")
    keywords: Optional[List[str]] = Field(None, description="关键词筛选")
    
    # 分析维度
    analysis_dimensions: List[str] = Field(
        default=["volume", "sentiment", "keywords", "topics"],
        description="分析维度: volume/sentiment/keywords/topics/trend/comparison"
    )
    
    # 自定义指标
    custom_metrics: Optional[Dict[str, Any]] = Field(None, description="自定义指标配置")
    
    # 分组方式
    group_by: Optional[str] = Field(None, description="分组方式: category/source/date/keyword")
    
    # 排序方式
    sort_by: Optional[str] = Field("relevance", description="排序方式: relevance/time/volume")
    sort_order: Optional[str] = Field("desc", description="排序顺序: asc/desc")
    
    # 结果限制
    limit: Optional[int] = Field(100, description="结果数量限制")


class CustomTrendComparisonRequest(BaseModel):
    """自定义趋势对比请求"""
    # 对比组1
    group1_name: str
    group1_config: Dict[str, Any]
    
    # 对比组2
    group2_name: str
    group2_config: Dict[str, Any]
    
    # 对比维度
    comparison_dimensions: List[str] = ["volume", "keywords", "sentiment", "topics"]


@router.post("/analyze")
async def custom_trend_analysis(request: CustomAnalysisRequest):
    """
    自定义趋势分析
    
    支持用户自定义：
    - 时间范围
    - 数据源筛选
    - 分析维度
    - 自定义指标
    - 分组和排序方式
    
    Args:
        request: 自定义分析请求
        
    Returns:
        分析结果
    """
    try:
        # 1. 获取数据
        all_data = default_crawler_manager.get_latest_results(1000)
        
        # 2. 时间范围筛选
        filtered_data = _filter_by_time_range(
            all_data,
            request.start_date,
            request.end_date,
            request.time_range
        )
        
        # 3. 类别筛选
        if request.categories:
            filtered_data = [
                d for d in filtered_data
                if d.get("category") in request.categories
            ]
        
        # 4. 来源筛选
        if request.sources:
            filtered_data = [
                d for d in filtered_data
                if d.get("source") in request.sources
            ]
        
        # 5. 关键词筛选
        if request.keywords:
            filtered_data = [
                d for d in filtered_data
                if any(kw in d.get("content", "").lower() or kw in d.get("title", "").lower()
                      for kw in request.keywords)
            ]
        
        # 6. 执行分析
        analysis_result = {}
        
        if "volume" in request.analysis_dimensions:
            analysis_result["volume"] = _analyze_volume(filtered_data, request.group_by)
        
        if "sentiment" in request.analysis_dimensions:
            analysis_result["sentiment"] = _analyze_sentiment(filtered_data)
        
        if "keywords" in request.analysis_dimensions:
            analysis_result["keywords"] = _analyze_keywords(filtered_data, request.limit)
        
        if "topics" in request.analysis_dimensions:
            analysis_result["topics"] = analyzer.detect_hot_topics(filtered_data)
        
        if "trend" in request.analysis_dimensions:
            analysis_result["trend"] = _analyze_trend(filtered_data, request.group_by)
        
        if "comparison" in request.analysis_dimensions:
            # 需要历史数据对比
            previous_data = _get_previous_period_data(all_data, request.time_range)
            analysis_result["comparison"] = analyzer.compare_trends(filtered_data, previous_data)
        
        # 7. 自定义指标计算
        if request.custom_metrics:
            analysis_result["custom_metrics"] = _calculate_custom_metrics(
                filtered_data,
                request.custom_metrics
            )
        
        # 8. 排序和限制
        if request.sort_by:
            analysis_result = _sort_results(analysis_result, request.sort_by, request.sort_order)
        
        return {
            "success": True,
            "analysis_config": request.dict(),
            "data_count": len(filtered_data),
            "results": analysis_result,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自定义分析失败: {str(e)}")


@router.post("/compare")
async def custom_trend_comparison(request: CustomTrendComparisonRequest):
    """
    自定义趋势对比分析
    
    对比两个自定义配置的数据组
    
    Args:
        request: 对比请求
        
    Returns:
        对比结果
    """
    try:
        # 获取两组数据
        all_data = default_crawler_manager.get_latest_results(1000)
        
        group1_data = _apply_config_filter(all_data, request.group1_config)
        group2_data = _apply_config_filter(all_data, request.group2_config)
        
        # 执行对比分析
        comparison_result = {}
        
        if "volume" in request.comparison_dimensions:
            comparison_result["volume"] = {
                "group1": len(group1_data),
                "group2": len(group2_data),
                "difference": len(group1_data) - len(group2_data),
                "difference_percent": (
                    (len(group1_data) - len(group2_data)) / len(group2_data) * 100
                    if len(group2_data) > 0 else 0
                )
            }
        
        if "keywords" in request.comparison_dimensions:
            group1_keywords = set(analyzer.extract_keywords(
                " ".join(d.get("content", "") for d in group1_data), 20
            ))
            group2_keywords = set(analyzer.extract_keywords(
                " ".join(d.get("content", "") for d in group2_data), 20
            ))
            
            comparison_result["keywords"] = {
                "common": list(group1_keywords & group2_keywords),
                "group1_only": list(group1_keywords - group2_keywords),
                "group2_only": list(group2_keywords - group1_keywords)
            }
        
        if "sentiment" in request.comparison_dimensions:
            comparison_result["sentiment"] = {
                "group1": _analyze_sentiment(group1_data),
                "group2": _analyze_sentiment(group2_data)
            }
        
        if "topics" in request.comparison_dimensions:
            comparison_result["topics"] = {
                "group1": analyzer.detect_hot_topics(group1_data)[:10],
                "group2": analyzer.detect_hot_topics(group2_data)[:10]
            }
        
        return {
            "success": True,
            "group1_name": request.group1_name,
            "group2_name": request.group2_name,
            "group1_count": len(group1_data),
            "group2_count": len(group2_data),
            "comparison": comparison_result,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比分析失败: {str(e)}")


@router.get("/dimensions")
async def get_available_dimensions():
    """获取可用的分析维度"""
    return {
        "dimensions": [
            {
                "id": "volume",
                "name": "数量分析",
                "description": "分析数据量、增长趋势等"
            },
            {
                "id": "sentiment",
                "name": "情感分析",
                "description": "分析情感倾向、正面/负面比例"
            },
            {
                "id": "keywords",
                "name": "关键词分析",
                "description": "提取和分析关键词频率"
            },
            {
                "id": "topics",
                "name": "话题分析",
                "description": "检测热点话题和趋势"
            },
            {
                "id": "trend",
                "name": "趋势分析",
                "description": "分析时间序列趋势"
            },
            {
                "id": "comparison",
                "name": "对比分析",
                "description": "与历史数据对比"
            }
        ],
        "group_by_options": [
            "category", "source", "date", "keyword"
        ],
        "sort_options": [
            "relevance", "time", "volume"
        ]
    }


# ============ 辅助函数 ============

def _filter_by_time_range(
    data: List[Dict],
    start_date: Optional[str],
    end_date: Optional[str],
    time_range: Optional[str]
) -> List[Dict]:
    """按时间范围筛选数据"""
    if start_date and end_date:
        return [
            d for d in data
            if start_date <= d.get("publish_date", "")[:10] <= end_date
        ]
    
    if time_range:
        today = datetime.now()
        if time_range == "today":
            date_str = today.strftime("%Y-%m-%d")
            return [d for d in data if d.get("publish_date", "")[:10] == date_str]
        elif time_range == "week":
            week_ago = today - timedelta(days=7)
            return [d for d in data if d.get("publish_date", "")[:10] >= week_ago.strftime("%Y-%m-%d")]
        elif time_range == "month":
            month_ago = today - timedelta(days=30)
            return [d for d in data if d.get("publish_date", "")[:10] >= month_ago.strftime("%Y-%m-%d")]
        elif time_range == "quarter":
            quarter_ago = today - timedelta(days=90)
            return [d for d in data if d.get("publish_date", "")[:10] >= quarter_ago.strftime("%Y-%m-%d")]
        elif time_range == "year":
            year_ago = today - timedelta(days=365)
            return [d for d in data if d.get("publish_date", "")[:10] >= year_ago.strftime("%Y-%m-%d")]
    
    return data


def _analyze_volume(data: List[Dict], group_by: Optional[str]) -> Dict[str, Any]:
    """数量分析"""
    result = {
        "total": len(data),
        "by_date": {}
    }
    
    if group_by == "category":
        from collections import Counter
        result["by_category"] = dict(Counter(d.get("category") for d in data))
    elif group_by == "source":
        from collections import Counter
        result["by_source"] = dict(Counter(d.get("source") for d in data))
    
    # 按日期统计
    dates = [d.get("publish_date", "")[:10] for d in data if d.get("publish_date")]
    from collections import Counter
    result["by_date"] = dict(Counter(dates))
    
    return result


def _analyze_sentiment(data: List[Dict]) -> Dict[str, Any]:
    """情感分析（简化版）"""
    # 这里可以集成实际的情感分析模型
    positive_keywords = ["好", "优", "增长", "提升", "成功", "利好"]
    negative_keywords = ["差", "下降", "失败", "风险", "危机", "利空"]
    
    positive_count = sum(
        1 for d in data
        if any(kw in d.get("content", "").lower() or kw in d.get("title", "").lower()
              for kw in positive_keywords)
    )
    negative_count = sum(
        1 for d in data
        if any(kw in d.get("content", "").lower() or kw in d.get("title", "").lower()
              for kw in negative_keywords)
    )
    
    total = len(data)
    return {
        "positive": positive_count,
        "negative": negative_count,
        "neutral": total - positive_count - negative_count,
        "positive_rate": positive_count / total * 100 if total > 0 else 0,
        "negative_rate": negative_count / total * 100 if total > 0 else 0
    }


def _analyze_keywords(data: List[Dict], limit: int) -> List[Dict[str, Any]]:
    """关键词分析"""
    all_content = " ".join(d.get("content", "") + " " + d.get("title", "") for d in data)
    keywords = analyzer.extract_keywords(all_content, limit)
    
    return [
        {"keyword": kw, "frequency": all_content.lower().count(kw.lower())}
        for kw in keywords
    ]


def _analyze_trend(data: List[Dict], group_by: Optional[str]) -> Dict[str, Any]:
    """趋势分析"""
    # 按时间排序
    sorted_data = sorted(
        data,
        key=lambda x: x.get("publish_date", ""),
        reverse=False
    )
    
    # 计算趋势方向
    if len(sorted_data) >= 2:
        early_count = len(sorted_data[:len(sorted_data)//2])
        late_count = len(sorted_data[len(sorted_data)//2:])
        
        if late_count > early_count * 1.2:
            trend_direction = "上升"
        elif late_count < early_count * 0.8:
            trend_direction = "下降"
        else:
            trend_direction = "稳定"
    else:
        trend_direction = "数据不足"
    
    return {
        "direction": trend_direction,
        "data_points": len(sorted_data),
        "time_series": [
            {
                "date": d.get("publish_date", "")[:10],
                "count": 1
            }
            for d in sorted_data
        ]
    }


def _calculate_custom_metrics(data: List[Dict], metrics_config: Dict[str, Any]) -> Dict[str, Any]:
    """计算自定义指标"""
    results = {}
    
    for metric_name, metric_config in metrics_config.items():
        metric_type = metric_config.get("type")
        
        if metric_type == "count":
            # 计数指标
            filter_condition = metric_config.get("filter", {})
            filtered = _apply_config_filter(data, filter_condition)
            results[metric_name] = len(filtered)
        
        elif metric_type == "average":
            # 平均值指标
            field = metric_config.get("field")
            values = [float(d.get(field, 0)) for d in data if d.get(field)]
            results[metric_name] = sum(values) / len(values) if values else 0
        
        elif metric_type == "sum":
            # 求和指标
            field = metric_config.get("field")
            values = [float(d.get(field, 0)) for d in data if d.get(field)]
            results[metric_name] = sum(values)
    
    return results


def _get_previous_period_data(all_data: List[Dict], time_range: Optional[str]) -> List[Dict]:
    """获取上一周期的数据用于对比"""
    if not time_range:
        return []
    
    today = datetime.now()
    if time_range == "week":
        start = today - timedelta(days=14)
        end = today - timedelta(days=7)
    elif time_range == "month":
        start = today - timedelta(days=60)
        end = today - timedelta(days=30)
    else:
        return []
    
    return [
        d for d in all_data
        if start.strftime("%Y-%m-%d") <= d.get("publish_date", "")[:10] <= end.strftime("%Y-%m-%d")
    ]


def _apply_config_filter(data: List[Dict], config: Dict[str, Any]) -> List[Dict]:
    """应用配置筛选"""
    filtered = data
    
    if config.get("categories"):
        filtered = [d for d in filtered if d.get("category") in config["categories"]]
    
    if config.get("sources"):
        filtered = [d for d in filtered if d.get("source") in config["sources"]]
    
    if config.get("keywords"):
        filtered = [
            d for d in filtered
            if any(kw in d.get("content", "").lower() or kw in d.get("title", "").lower()
                  for kw in config["keywords"])
        ]
    
    if config.get("start_date") and config.get("end_date"):
        filtered = [
            d for d in filtered
            if config["start_date"] <= d.get("publish_date", "")[:10] <= config["end_date"]
        ]
    
    return filtered


def _sort_results(results: Dict[str, Any], sort_by: str, sort_order: str) -> Dict[str, Any]:
    """排序结果"""
    # 这里可以根据需要实现排序逻辑
    return results


