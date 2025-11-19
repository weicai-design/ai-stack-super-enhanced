#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运营财务专家系统
功能：图表专家、财务专家看板、KPI定义、专家建议口径
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ChartExpert:
    """
    图表专家
    根据数据特征推荐最佳图表类型
    """
    
    def __init__(self):
        """初始化图表专家"""
        self.chart_types = {
            "line": {"name": "折线图", "score": 0, "description": "适合展示趋势变化"},
            "bar": {"name": "柱状图", "score": 0, "description": "适合对比不同类别"},
            "pie": {"name": "饼图", "score": 0, "description": "适合展示占比关系"},
            "area": {"name": "面积图", "score": 0, "description": "适合展示累计趋势"},
            "scatter": {"name": "散点图", "score": 0, "description": "适合展示相关性"},
            "radar": {"name": "雷达图", "score": 0, "description": "适合多维度对比"},
        }
    
    def recommend_chart(
        self,
        data: Dict[str, Any],
        purpose: str = "分析"
    ) -> Dict[str, Any]:
        """
        推荐图表类型
        
        Args:
            data: 数据字典，包含 keys, values, series_names 等
            purpose: 用途（趋势分析、占比展示、对比等）
            
        Returns:
            推荐结果
        """
        # 重置评分
        for chart_type in self.chart_types:
            self.chart_types[chart_type]["score"] = 0
        
        keys = data.get("keys", [])
        values = data.get("values", [])
        series_names = data.get("series_names", [])
        metadata = data.get("metadata", {})
        
        # 判断数据特征
        has_time = metadata.get("has_time", False)
        is_proportion = metadata.get("is_proportion", False)
        series_count = metadata.get("series_count", len(values) if isinstance(values, list) else 1)
        key_count = len(keys)
        
        # 评分逻辑
        if has_time and series_count > 1:
            # 时间序列 + 多系列 -> 折线图或面积图
            self.chart_types["line"]["score"] += 10
            self.chart_types["area"]["score"] += 8
        elif has_time:
            # 时间序列单系列 -> 折线图
            self.chart_types["line"]["score"] += 12
        
        if is_proportion or key_count <= 8:
            # 占比数据或类别少 -> 饼图
            self.chart_types["pie"]["score"] += 10
        
        if not has_time and key_count > 0 and key_count <= 10:
            # 非时间序列，类别适中 -> 柱状图
            self.chart_types["bar"]["score"] += 10
        
        if series_count >= 3 and not has_time:
            # 多维度对比 -> 雷达图
            self.chart_types["radar"]["score"] += 8
        
        if series_count == 2 and not has_time:
            # 两个变量 -> 散点图
            self.chart_types["scatter"]["score"] += 6
        
        # 根据用途调整
        if "趋势" in purpose or "变化" in purpose:
            self.chart_types["line"]["score"] += 5
            self.chart_types["area"]["score"] += 3
        elif "占比" in purpose or "比例" in purpose:
            self.chart_types["pie"]["score"] += 5
        elif "对比" in purpose:
            self.chart_types["bar"]["score"] += 5
            self.chart_types["radar"]["score"] += 3
        
        # 选择最佳图表
        best_chart = max(self.chart_types.items(), key=lambda x: x[1]["score"])
        
        # 生成推荐列表（按评分排序）
        recommendations = sorted(
            self.chart_types.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:3]
        
        return {
            "best_chart": {
                "chart_type": best_chart[0],
                "name": best_chart[1]["name"],
                "score": best_chart[1]["score"],
                "description": best_chart[1]["description"]
            },
            "recommendations": [
                {
                    "chart_type": chart_type,
                    "name": info["name"],
                    "score": info["score"],
                    "description": info["description"]
                }
                for chart_type, info in recommendations
            ],
            "reasoning": self._generate_reasoning(data, best_chart[0])
        }
    
    def _generate_reasoning(self, data: Dict[str, Any], chart_type: str) -> str:
        """生成推荐理由"""
        metadata = data.get("metadata", {})
        has_time = metadata.get("has_time", False)
        series_count = metadata.get("series_count", 1)
        
        if chart_type == "line":
            if has_time:
                return "数据包含时间序列，折线图能清晰展示趋势变化"
            return "多系列数据适合用折线图对比"
        elif chart_type == "pie":
            return "数据适合展示占比关系，饼图直观清晰"
        elif chart_type == "bar":
            return "类别数据适合用柱状图进行对比"
        elif chart_type == "area":
            return "时间序列数据适合用面积图展示累计趋势"
        return "根据数据特征推荐"


class FinanceExpert:
    """
    财务专家
    提供财务指标分析和建议
    """
    
    def __init__(self):
        """初始化财务专家"""
        self.kpi_definitions = {
            "net_cash": {
                "name": "净现金",
                "formula": "现金 + 银行存款 - 短期负债",
                "unit": "元",
                "threshold": {"warning": 100000, "critical": 50000}
            },
            "burn_rate": {
                "name": "月度 Burn Rate",
                "formula": "月度总支出",
                "unit": "元/月",
                "threshold": {"warning": 500000, "critical": 1000000}
            },
            "runway": {
                "name": "Runway（月）",
                "formula": "净现金 / 月度 Burn Rate",
                "unit": "月",
                "threshold": {"warning": 6, "critical": 3}
            },
            "collections": {
                "name": "季度回款",
                "formula": "季度应收账款回收总额",
                "unit": "元",
                "threshold": {"warning": 1000000, "critical": 500000}
            },
            "payments": {
                "name": "季度付款",
                "formula": "季度应付账款支付总额",
                "unit": "元",
                "threshold": {"warning": 2000000, "critical": 5000000}
            },
        }
    
    def calculate_kpis(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算KPI指标
        
        Args:
            financial_data: 财务数据
            
        Returns:
            KPI计算结果
        """
        cash = financial_data.get("cash", 0.0)
        bank_deposits = financial_data.get("bank_deposits", 0.0)
        short_term_liabilities = financial_data.get("short_term_liabilities", 0.0)
        monthly_expense = financial_data.get("monthly_expense", 0.0)
        quarterly_collections = financial_data.get("quarterly_collections", 0.0)
        quarterly_payments = financial_data.get("quarterly_payments", 0.0)
        
        # 计算净现金
        net_cash = cash + bank_deposits - short_term_liabilities
        
        # 计算 Runway
        runway = net_cash / monthly_expense if monthly_expense > 0 else 0.0
        
        kpis = {
            "net_cash": {
                "value": round(net_cash, 2),
                "unit": self.kpi_definitions["net_cash"]["unit"],
                "status": self._evaluate_status(net_cash, "net_cash"),
                "formula": self.kpi_definitions["net_cash"]["formula"]
            },
            "burn_rate": {
                "value": round(monthly_expense, 2),
                "unit": self.kpi_definitions["burn_rate"]["unit"],
                "status": self._evaluate_status(monthly_expense, "burn_rate"),
                "formula": self.kpi_definitions["burn_rate"]["formula"]
            },
            "runway": {
                "value": round(runway, 2),
                "unit": self.kpi_definitions["runway"]["unit"],
                "status": self._evaluate_status(runway, "runway"),
                "formula": self.kpi_definitions["runway"]["formula"]
            },
            "collections": {
                "value": round(quarterly_collections, 2),
                "unit": self.kpi_definitions["collections"]["unit"],
                "status": self._evaluate_status(quarterly_collections, "collections"),
                "formula": self.kpi_definitions["collections"]["formula"]
            },
            "payments": {
                "value": round(quarterly_payments, 2),
                "unit": self.kpi_definitions["payments"]["unit"],
                "status": self._evaluate_status(quarterly_payments, "payments"),
                "formula": self.kpi_definitions["payments"]["formula"]
            },
        }
        
        return kpis
    
    def _evaluate_status(self, value: float, kpi_name: str) -> str:
        """评估KPI状态"""
        thresholds = self.kpi_definitions[kpi_name]["threshold"]
        critical = thresholds.get("critical", 0)
        warning = thresholds.get("warning", 0)
        
        if kpi_name in ["runway"]:
            # Runway 越小越危险
            if value <= critical:
                return "critical"
            elif value <= warning:
                return "warning"
            return "normal"
        else:
            # 其他指标越大越好（或根据实际情况调整）
            if value <= critical:
                return "critical"
            elif value <= warning:
                return "warning"
            return "normal"
    
    def generate_insights(self, kpis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        生成财务洞察
        
        Args:
            kpis: KPI计算结果
            
        Returns:
            洞察列表
        """
        insights = []
        
        # 分析净现金
        net_cash = kpis.get("net_cash", {})
        if net_cash.get("status") == "critical":
            insights.append({
                "type": "critical",
                "title": "净现金告急",
                "description": f"当前净现金为 {net_cash.get('value')} 元，低于临界值，建议立即采取行动",
                "recommendations": [
                    "加快应收账款回收",
                    "延迟非关键支出",
                    "寻求融资支持"
                ]
            })
        elif net_cash.get("status") == "warning":
            insights.append({
                "type": "warning",
                "title": "净现金预警",
                "description": f"当前净现金为 {net_cash.get('value')} 元，需要关注",
                "recommendations": [
                    "监控现金流变化",
                    "优化支出结构"
                ]
            })
        
        # 分析 Runway
        runway = kpis.get("runway", {})
        if runway.get("status") == "critical":
            insights.append({
                "type": "critical",
                "title": "Runway 严重不足",
                "description": f"当前 Runway 为 {runway.get('value')} 个月，资金链紧张",
                "recommendations": [
                    "紧急融资",
                    "大幅削减成本",
                    "加速收入增长"
                ]
            })
        elif runway.get("status") == "warning":
            insights.append({
                "type": "warning",
                "title": "Runway 预警",
                "description": f"当前 Runway 为 {runway.get('value')} 个月，需要关注",
                "recommendations": [
                    "制定融资计划",
                    "优化运营效率"
                ]
            })
        
        # 分析回款和付款
        collections = kpis.get("collections", {})
        payments = kpis.get("payments", {})
        if collections.get("value", 0) < payments.get("value", 0) * 0.8:
            insights.append({
                "type": "warning",
                "title": "回款不足",
                "description": "季度回款低于季度付款的80%，现金流压力较大",
                "recommendations": [
                    "加强应收账款管理",
                    "优化付款节奏"
                ]
            })
        
        return insights
    
    def get_kpi_definitions(self) -> Dict[str, Any]:
        """获取KPI定义"""
        return {
            "definitions": self.kpi_definitions,
            "last_updated": datetime.now().isoformat()
        }


# 全局实例
chart_expert = ChartExpert()
finance_expert = FinanceExpert()

