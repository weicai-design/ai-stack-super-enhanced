"""
图表专家
智能推荐图表类型、自动生成配置、优化展示效果
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ChartType(Enum):
    """图表类型枚举"""
    LINE = "line"  # 折线图
    BAR = "bar"    # 柱状图
    PIE = "pie"    # 饼图
    SCATTER = "scatter"  # 散点图
    AREA = "area"  # 面积图
    RADAR = "radar"  # 雷达图
    GAUGE = "gauge"  # 仪表盘
    FUNNEL = "funnel"  # 漏斗图
    HEATMAP = "heatmap"  # 热力图
    TREEMAP = "treemap"  # 矩形树图
    SUNBURST = "sunburst"  # 旭日图
    SANKEY = "sankey"  # 桑基图
    GRAPH = "graph"  # 关系图
    MAP = "map"  # 地图
    CANDLESTICK = "candlestick"  # K线图
    PARALLEL = "parallel"  # 平行坐标


class DataPattern(Enum):
    """数据模式枚举"""
    TIME_SERIES = "time_series"  # 时间序列
    CATEGORY_COMPARISON = "category_comparison"  # 类别对比
    PROPORTION = "proportion"  # 比例
    DISTRIBUTION = "distribution"  # 分布
    CORRELATION = "correlation"  # 相关性
    HIERARCHY = "hierarchy"  # 层级
    FLOW = "flow"  # 流向
    GEOGRAPHIC = "geographic"  # 地理
    MULTI_DIMENSION = "multi_dimension"  # 多维


class ChartExpert:
    """
    图表专家
    智能推荐图表类型、自动生成配置
    """
    
    def __init__(self):
        # 图表类型库
        self.chart_library = {
            ChartType.LINE: {
                "name": "折线图",
                "description": "适合展示趋势变化、时间序列数据",
                "suitable_patterns": [
                    DataPattern.TIME_SERIES,
                    DataPattern.DISTRIBUTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 10,
                    "min_points": 2,
                    "supports_time": True
                }
            },
            ChartType.BAR: {
                "name": "柱状图",
                "description": "适合展示类别对比、排名",
                "suitable_patterns": [
                    DataPattern.CATEGORY_COMPARISON,
                    DataPattern.DISTRIBUTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 5,
                    "min_points": 1,
                    "supports_time": False
                }
            },
            ChartType.PIE: {
                "name": "饼图",
                "description": "适合展示比例、占比",
                "suitable_patterns": [
                    DataPattern.PROPORTION,
                    DataPattern.CATEGORY_COMPARISON
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 1,
                    "min_points": 2,
                    "max_points": 10,
                    "supports_time": False
                }
            },
            ChartType.AREA: {
                "name": "面积图",
                "description": "适合展示累计趋势、堆叠对比",
                "suitable_patterns": [
                    DataPattern.TIME_SERIES,
                    DataPattern.CATEGORY_COMPARISON
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 5,
                    "min_points": 2,
                    "supports_time": True
                }
            },
            ChartType.SCATTER: {
                "name": "散点图",
                "description": "适合展示相关性、分布",
                "suitable_patterns": [
                    DataPattern.CORRELATION,
                    DataPattern.DISTRIBUTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 5,
                    "min_points": 3,
                    "supports_time": False
                }
            },
            ChartType.RADAR: {
                "name": "雷达图",
                "description": "适合展示多维对比、能力评估",
                "suitable_patterns": [
                    DataPattern.MULTI_DIMENSION,
                    DataPattern.CATEGORY_COMPARISON
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 5,
                    "min_points": 3,
                    "max_points": 10,
                    "supports_time": False
                }
            },
            ChartType.HEATMAP: {
                "name": "热力图",
                "description": "适合展示二维数据密度、相关性矩阵",
                "suitable_patterns": [
                    DataPattern.CORRELATION,
                    DataPattern.DISTRIBUTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 1,
                    "min_points": 4,
                    "supports_time": False
                }
            },
            ChartType.TREEMAP: {
                "name": "矩形树图",
                "description": "适合展示层级数据、占比",
                "suitable_patterns": [
                    DataPattern.HIERARCHY,
                    DataPattern.PROPORTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 1,
                    "min_points": 2,
                    "supports_time": False
                }
            },
            ChartType.FUNNEL: {
                "name": "漏斗图",
                "description": "适合展示流程转化、阶段对比",
                "suitable_patterns": [
                    DataPattern.FLOW,
                    DataPattern.PROPORTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 1,
                    "min_points": 2,
                    "max_points": 10,
                    "supports_time": False
                }
            },
            ChartType.GAUGE: {
                "name": "仪表盘",
                "description": "适合展示指标、进度、完成度",
                "suitable_patterns": [
                    DataPattern.PROPORTION
                ],
                "data_requirements": {
                    "min_series": 1,
                    "max_series": 1,
                    "min_points": 1,
                    "max_points": 1,
                    "supports_time": False
                }
            }
        }
    
    def analyze_data_pattern(self, data: Dict[str, Any]) -> DataPattern:
        """
        分析数据模式
        
        Args:
            data: 数据字典，包含keys, values, metadata等
            
        Returns:
            数据模式
        """
        keys = data.get("keys", [])
        values = data.get("values", [])
        metadata = data.get("metadata", {})
        
        # 检查是否有时间字段
        has_time = any(
            "time" in str(k).lower() or 
            "date" in str(k).lower() or
            "日期" in str(k) or
            "时间" in str(k)
            for k in keys
        )
        
        # 检查数据维度
        series_count = len(values) if isinstance(values, list) else 1
        point_count = len(values[0]) if values and isinstance(values[0], list) else len(values)
        
        # 检查是否为比例数据（总和接近100或1）
        if isinstance(values, list) and len(values) > 0:
            if isinstance(values[0], (int, float)):
                total = sum(values)
                if 95 <= total <= 105:  # 接近100%
                    return DataPattern.PROPORTION
        
        # 检查是否为层级数据
        if metadata.get("hierarchy") or metadata.get("parent"):
            return DataPattern.HIERARCHY
        
        # 检查是否为地理数据
        if metadata.get("geographic") or any("省" in str(k) or "市" in str(k) for k in keys):
            return DataPattern.GEOGRAPHIC
        
        # 检查是否为多维数据
        if series_count >= 3 and point_count >= 3:
            return DataPattern.MULTI_DIMENSION
        
        # 检查是否为相关性数据
        if series_count >= 2 and point_count >= 5:
            return DataPattern.CORRELATION
        
        # 时间序列
        if has_time:
            return DataPattern.TIME_SERIES
        
        # 类别对比
        if series_count >= 2:
            return DataPattern.CATEGORY_COMPARISON
        
        # 默认分布
        return DataPattern.DISTRIBUTION
    
    def recommend_chart_type(
        self,
        data: Dict[str, Any],
        purpose: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        推荐图表类型
        
        Args:
            data: 数据字典
            purpose: 用途（如：趋势分析、对比分析、占比展示等）
            
        Returns:
            推荐的图表类型列表（按推荐度排序）
        """
        # 分析数据模式
        pattern = self.analyze_data_pattern(data)
        
        # 获取数据特征
        keys = data.get("keys", [])
        values = data.get("values", [])
        series_count = len(values) if isinstance(values, list) else 1
        point_count = len(values[0]) if values and isinstance(values[0], list) else len(values)
        
        # 根据用途调整推荐
        purpose_keywords = {
            "趋势": [ChartType.LINE, ChartType.AREA],
            "对比": [ChartType.BAR, ChartType.RADAR],
            "占比": [ChartType.PIE, ChartType.TREEMAP],
            "分布": [ChartType.SCATTER, ChartType.HEATMAP],
            "流程": [ChartType.FUNNEL],
            "指标": [ChartType.GAUGE],
            "相关性": [ChartType.SCATTER, ChartType.HEATMAP]
        }
        
        recommendations = []
        
        # 1. 根据数据模式推荐
        for chart_type, chart_info in self.chart_library.items():
            if pattern in chart_info["suitable_patterns"]:
                req = chart_info["data_requirements"]
                
                # 检查数据要求
                if series_count < req.get("min_series", 1):
                    continue
                if series_count > req.get("max_series", 999):
                    continue
                if point_count < req.get("min_points", 1):
                    continue
                if point_count > req.get("max_points", 999):
                    continue
                
                score = 80  # 基础分数
                
                # 根据用途调整分数
                if purpose:
                    for keyword, preferred_charts in purpose_keywords.items():
                        if keyword in purpose and chart_type in preferred_charts:
                            score += 20
                
                recommendations.append({
                    "chart_type": chart_type.value,
                    "name": chart_info["name"],
                    "description": chart_info["description"],
                    "score": score,
                    "reason": f"数据模式匹配：{pattern.value}"
                })
        
        # 2. 根据用途推荐（如果指定了用途）
        if purpose:
            for keyword, preferred_charts in purpose_keywords.items():
                if keyword in purpose:
                    for chart_type in preferred_charts:
                        chart_info = self.chart_library.get(chart_type)
                        if chart_info:
                            # 检查是否已在推荐列表中
                            existing = next(
                                (r for r in recommendations if r["chart_type"] == chart_type.value),
                                None
                            )
                            if not existing:
                                req = chart_info["data_requirements"]
                                if (req.get("min_series", 1) <= series_count <= req.get("max_series", 999) and
                                    req.get("min_points", 1) <= point_count <= req.get("max_points", 999)):
                                    recommendations.append({
                                        "chart_type": chart_type.value,
                                        "name": chart_info["name"],
                                        "description": chart_info["description"],
                                        "score": 70,
                                        "reason": f"用途匹配：{keyword}"
                                    })
        
        # 按分数排序
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        # 返回前5个推荐
        return recommendations[:5]
    
    def generate_chart_config(
        self,
        chart_type: str,
        data: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成图表配置（ECharts格式）
        
        Args:
            chart_type: 图表类型
            data: 数据字典
            options: 可选配置
            
        Returns:
            ECharts配置对象
        """
        options = options or {}
        keys = data.get("keys", [])
        values = data.get("values", [])
        title = options.get("title", data.get("title", "图表"))
        
        # 基础配置
        config = {
            "title": {
                "text": title,
                "left": "center"
            },
            "tooltip": {
                "trigger": "axis" if chart_type in ["line", "bar", "area"] else "item"
            },
            "legend": {
                "data": data.get("series_names", keys[:5]),
                "top": "10%"
            },
            "grid": {
                "left": "3%",
                "right": "4%",
                "bottom": "3%",
                "containLabel": True
            }
        }
        
        # 根据图表类型生成特定配置
        if chart_type == "line":
            config.update({
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": keys
                },
                "yAxis": {
                    "type": "value"
                },
                "series": [
                    {
                        "name": name if isinstance(name, str) else f"系列{i+1}",
                        "type": "line",
                        "data": val if isinstance(val, list) else [val],
                        "smooth": True
                    }
                    for i, (name, val) in enumerate(zip(
                        data.get("series_names", keys),
                        values if isinstance(values[0], list) else [values]
                    ))
                ]
            })
        
        elif chart_type == "bar":
            config.update({
                "xAxis": {
                    "type": "category",
                    "data": keys
                },
                "yAxis": {
                    "type": "value"
                },
                "series": [
                    {
                        "name": name if isinstance(name, str) else f"系列{i+1}",
                        "type": "bar",
                        "data": val if isinstance(val, list) else [val]
                    }
                    for i, (name, val) in enumerate(zip(
                        data.get("series_names", keys),
                        values if isinstance(values[0], list) else [values]
                    ))
                ]
            })
        
        elif chart_type == "pie":
            # 饼图数据格式
            pie_data = [
                {"value": val, "name": key}
                for key, val in zip(keys, values if isinstance(values, list) else [values])
            ]
            config.update({
                "series": [
                    {
                        "name": title,
                        "type": "pie",
                        "radius": "70%",
                        "data": pie_data,
                        "emphasis": {
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowOffsetX": 0,
                                "shadowColor": "rgba(0, 0, 0, 0.5)"
                            }
                        }
                    }
                ]
            })
            # 饼图不需要xAxis和yAxis
            config.pop("xAxis", None)
            config.pop("yAxis", None)
            config.pop("grid", None)
        
        elif chart_type == "area":
            config.update({
                "xAxis": {
                    "type": "category",
                    "boundaryGap": False,
                    "data": keys
                },
                "yAxis": {
                    "type": "value"
                },
                "series": [
                    {
                        "name": name if isinstance(name, str) else f"系列{i+1}",
                        "type": "line",
                        "data": val if isinstance(val, list) else [val],
                        "areaStyle": {},
                        "stack": options.get("stack", "总量")
                    }
                    for i, (name, val) in enumerate(zip(
                        data.get("series_names", keys),
                        values if isinstance(values[0], list) else [values]
                    ))
                ]
            })
        
        elif chart_type == "gauge":
            value = values[0] if isinstance(values, list) else values
            max_value = options.get("max", 100)
            config.update({
                "series": [
                    {
                        "name": title,
                        "type": "gauge",
                        "data": [{"value": value, "name": keys[0] if keys else "指标"}],
                        "min": 0,
                        "max": max_value,
                        "splitNumber": 10
                    }
                ]
            })
            config.pop("xAxis", None)
            config.pop("yAxis", None)
            config.pop("grid", None)
        
        # 应用自定义选项
        if options.get("colors"):
            config["color"] = options["colors"]
        
        if options.get("width"):
            config["width"] = options["width"]
        
        if options.get("height"):
            config["height"] = options["height"]
        
        return config
    
    def optimize_chart_config(
        self,
        config: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        优化图表配置
        
        Args:
            config: 原始配置
            data: 数据字典
            
        Returns:
            优化后的配置
        """
        # 自动调整颜色
        if "color" not in config:
            config["color"] = [
                "#5470C6", "#91CC75", "#FAC858", "#EE6666",
                "#73C0DE", "#3BA272", "#FC8452", "#9A60B4"
            ]
        
        # 自动调整tooltip格式
        if "tooltip" in config:
            if config["tooltip"].get("trigger") == "axis":
                config["tooltip"]["formatter"] = None  # 使用默认formatter
            elif config["tooltip"].get("trigger") == "item":
                config["tooltip"]["formatter"] = "{a} <br/>{b}: {c} ({d}%)"
        
        # 自动调整图例位置
        if "legend" in config:
            if not config["legend"].get("orient"):
                config["legend"]["orient"] = "horizontal"
            if not config["legend"].get("top"):
                config["legend"]["top"] = "10%"
        
        return config


# 全局实例
chart_expert = ChartExpert()


