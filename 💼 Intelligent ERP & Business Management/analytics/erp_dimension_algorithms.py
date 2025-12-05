"""
算法库：根据模板计算8维度指标得分 - 生产级实现
"""

from __future__ import annotations

import math
import time
import logging
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime

# 配置日志
logger = logging.getLogger(__name__)


def safe_get(data: Dict[str, Any], field: str, default: float = 0.0) -> float:
    """安全获取数值，带错误处理和监控"""
    try:
        value = data.get(field, default)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"字段 {field} 的值 {value} 无法转换为数值，使用默认值 {default}")
            return default
    except Exception as e:
        logger.error(f"获取字段 {field} 时发生错误: {e}")
        return default


def normalize_score(value: float, target: float, direction: str) -> float:
    """标准化得分计算，带边界检查和异常处理"""
    try:
        if target == 0:
            target = 0.0001
        
        if direction == "positive":
            # 正向指标：越高越好
            score = (value / target) * 100
        else:
            # 负向指标：越低越好
            if value == 0:
                return 100.0
            score = (target / value) * 100
        
        # 边界检查：限制在0-120分之间
        normalized_score = max(0.0, min(120.0, score))
        
        # 监控极端值
        if normalized_score > 110 or normalized_score < 10:
            logger.warning(f"指标得分异常: {normalized_score:.1f} (值: {value}, 目标: {target}, 方向: {direction})")
        
        return normalized_score
    except Exception as e:
        logger.error(f"标准化得分计算错误: {e}")
        return 50.0  # 默认中等分数


def evaluate_indicator(data: Dict[str, Any], indicator: Dict[str, Any]) -> Tuple[float, float]:
    """评估单个指标，带性能监控和数据验证"""
    start_time = time.time()
    
    try:
        # 获取指标值
        field_name = indicator.get("field", "")
        value = safe_get(data, field_name, 0.0)
        
        # 处理百分比单位
        if indicator.get("unit") == "%":
            value = value if value <= 100 else value * 100
        
        target = indicator.get("target", 0.0)
        direction = indicator.get("direction", "positive")
        
        # 数据验证
        if value < 0:
            logger.warning(f"指标 {field_name} 的值为负数: {value}")
        
        score = normalize_score(value, target, direction)
        
        # 性能监控
        execution_time = time.time() - start_time
        if execution_time > 0.1:  # 超过100ms记录警告
            logger.warning(f"指标 {field_name} 评估耗时过长: {execution_time:.3f}s")
        
        return value, score
    
    except Exception as e:
        logger.error(f"评估指标 {indicator.get('name', 'unknown')} 时发生错误: {e}")
        return 0.0, 50.0  # 默认值


def evaluate_dimension(data: Dict[str, Any], template: Dict[str, Any]) -> Dict[str, Any]:
    """评估整个维度，带性能监控和高级分析"""
    start_time = time.time()
    
    try:
        indicators_result: List[Dict[str, Any]] = []
        weighted_score = 0.0
        total_weight = 0.0

        # 检查模板完整性
        if "indicators" not in template or not template["indicators"]:
            logger.error(f"维度 {template.get('label', 'unknown')} 的指标模板为空")
            return _get_default_dimension_result(template)

        # 评估所有指标
        for ind in template["indicators"]:
            value, score = evaluate_indicator(data, ind)
            indicator_weight = ind.get("weight", 0)
            indicator_score = score * indicator_weight
            weighted_score += indicator_score
            total_weight += indicator_weight
            
            indicators_result.append(
                {
                    "name": ind["name"],
                    "label": ind["label"],
                    "value": round(value, 2),
                    "unit": ind.get("unit", ""),
                    "score": round(score, 2),
                    "target": ind.get("target"),
                    "direction": ind.get("direction"),
                    "suggestion": ind.get("suggestion"),
                    "weight": indicator_weight,
                    "weighted_score": round(indicator_score, 2),
                }
            )

        # 计算最终得分
        if total_weight > 0:
            score = round(weighted_score / total_weight, 2)
        else:
            score = 0.0
            logger.warning(f"维度 {template.get('label', 'unknown')} 的总权重为0")

        # 生成分析报告
        analysis = build_analysis(template["label"], indicators_result)
        suggestions = _build_suggestions(indicators_result)
        
        # 性能监控
        execution_time = time.time() - start_time
        logger.info(f"维度 {template['label']} 分析完成，耗时: {execution_time:.3f}s")
        
        return {
            "dimension": template["label"],
            "score": score,
            "level": classify_level(score),
            "indicators": indicators_result,
            "analysis": analysis,
            "suggestions": suggestions,
            "execution_time": round(execution_time, 3),
            "indicators_count": len(indicators_result),
            "timestamp": datetime.now().isoformat(),
        }
    
    except Exception as e:
        logger.error(f"评估维度 {template.get('label', 'unknown')} 时发生错误: {e}")
        return _get_default_dimension_result(template)


def build_analysis(label: str, indicators: List[Dict[str, Any]]) -> str:
    top = sorted(indicators, key=lambda x: x["score"], reverse=True)[:2]
    summary = ", ".join(
        f"{item['label']}{item['value']}{item.get('unit','')}"
        for item in top
    )
    return f"{label}关键指标：{summary}"


def _get_default_dimension_result(template: Dict[str, Any]) -> Dict[str, Any]:
    """获取默认维度结果（错误处理用）"""
    return {
        "dimension": template.get("label", "未知维度"),
        "score": 50.0,
        "level": "average",
        "indicators": [],
        "analysis": "维度分析失败，请检查数据完整性",
        "suggestions": ["检查数据源连接", "验证指标模板配置"],
        "execution_time": 0.0,
        "indicators_count": 0,
        "timestamp": datetime.now().isoformat(),
        "error": True
    }


def _build_suggestions(indicators: List[Dict[str, Any]]) -> List[str]:
    """构建改进建议列表"""
    suggestions = []
    
    # 低分指标建议
    low_score_indicators = [ind for ind in indicators if ind["score"] < 80]
    for indicator in low_score_indicators:
        if indicator.get("suggestion"):
            suggestions.append(f"{indicator['label']}: {indicator['suggestion']}")
    
    # 如果所有指标都高分，提供优化建议
    if not suggestions and indicators:
        avg_score = sum(ind["score"] for ind in indicators) / len(indicators)
        if avg_score >= 90:
            suggestions.append("所有指标表现优秀，继续保持并寻求持续改进机会")
        elif avg_score >= 80:
            suggestions.append("整体表现良好，关注个别指标进一步提升空间")
    
    return suggestions[:5]  # 最多返回5条建议


def classify_level(score: float) -> str:
    """根据得分分类等级"""
    if score >= 90:
        return "excellent"
    if score >= 80:
        return "good"
    if score >= 70:
        return "average"
    if score >= 60:
        return "poor"
    return "critical"


