#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票执行分析器
功能：分析交易执行质量、滑点、成交效率、订单执行统计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import logging

logger = logging.getLogger(__name__)


class ExecutionAnalyzer:
    """
    执行分析器
    分析交易执行质量、滑点、成交效率等
    """
    
    def __init__(self):
        """初始化执行分析器"""
        self.execution_records: List[Dict[str, Any]] = []
        self.order_stats: Dict[str, Any] = defaultdict(lambda: {
            "total": 0,
            "filled": 0,
            "rejected": 0,
            "canceled": 0,
            "total_volume": 0,
            "total_amount": 0,
        })
    
    def record_execution(
        self,
        order_id: str,
        symbol: str,
        side: str,
        qty: int,
        order_type: str,
        limit_price: Optional[float],
        exec_price: float,
        reference_price: float,
        slippage_bps: float,
        status: str,
        timestamp: str
    ):
        """
        记录执行记录
        
        Args:
            order_id: 订单ID
            symbol: 股票代码
            side: 方向（buy/sell）
            qty: 数量
            order_type: 订单类型（market/limit）
            limit_price: 限价（如果是限价单）
            exec_price: 执行价格
            reference_price: 参考价格
            slippage_bps: 滑点（基点）
            status: 状态（filled/rejected/canceled）
            timestamp: 时间戳
        """
        record = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "order_type": order_type,
            "limit_price": limit_price,
            "exec_price": exec_price,
            "reference_price": reference_price,
            "slippage_bps": slippage_bps,
            "status": status,
            "timestamp": timestamp,
            "amount": exec_price * qty if status == "filled" else 0.0,
        }
        
        self.execution_records.append(record)
        self.execution_records = self.execution_records[-1000:]  # 保留最近1000条
        
        # 更新统计
        self.order_stats[symbol]["total"] += 1
        if status == "filled":
            self.order_stats[symbol]["filled"] += 1
            self.order_stats[symbol]["total_volume"] += qty
            self.order_stats[symbol]["total_amount"] += record["amount"]
        elif status == "rejected":
            self.order_stats[symbol]["rejected"] += 1
        elif status == "canceled":
            self.order_stats[symbol]["canceled"] += 1
    
    def get_execution_report(
        self,
        symbol: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取执行分析报告
        
        Args:
            symbol: 股票代码（None表示全部）
            days: 时间范围（天）
            
        Returns:
            执行分析报告
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # 筛选记录
        records = [
            r for r in self.execution_records
            if datetime.fromisoformat(r["timestamp"]) >= cutoff
        ]
        
        if symbol:
            records = [r for r in records if r["symbol"] == symbol]
        
        if not records:
            return {
                "success": True,
                "period": {"days": days, "start": cutoff.isoformat(), "end": datetime.now().isoformat()},
                "total_orders": 0,
                "summary": {},
                "slippage_analysis": {},
                "execution_efficiency": {},
                "order_type_analysis": {},
            }
        
        # 基础统计
        total_orders = len(records)
        filled_orders = [r for r in records if r["status"] == "filled"]
        rejected_orders = [r for r in records if r["status"] == "rejected"]
        canceled_orders = [r for r in records if r["status"] == "canceled"]
        
        fill_rate = len(filled_orders) / total_orders if total_orders > 0 else 0.0
        rejection_rate = len(rejected_orders) / total_orders if total_orders > 0 else 0.0
        cancellation_rate = len(canceled_orders) / total_orders if total_orders > 0 else 0.0
        
        # 滑点分析
        slippage_values = [r["slippage_bps"] for r in filled_orders if r["slippage_bps"] is not None]
        avg_slippage = statistics.mean(slippage_values) if slippage_values else 0.0
        median_slippage = statistics.median(slippage_values) if slippage_values else 0.0
        max_slippage = max(slippage_values) if slippage_values else 0.0
        min_slippage = min(slippage_values) if slippage_values else 0.0
        
        # 按方向分析滑点
        buy_slippage = [r["slippage_bps"] for r in filled_orders if r["side"] == "buy" and r["slippage_bps"] is not None]
        sell_slippage = [r["slippage_bps"] for r in filled_orders if r["side"] == "sell" and r["slippage_bps"] is not None]
        
        # 执行效率分析
        total_volume = sum(r["qty"] for r in filled_orders)
        total_amount = sum(r["amount"] for r in filled_orders)
        avg_exec_price = total_amount / total_volume if total_volume > 0 else 0.0
        
        # 订单类型分析
        market_orders = [r for r in filled_orders if r["order_type"] == "market"]
        limit_orders = [r for r in filled_orders if r["order_type"] == "limit"]
        
        market_fill_rate = len(market_orders) / len([r for r in records if r["order_type"] == "market"]) if len([r for r in records if r["order_type"] == "market"]) > 0 else 0.0
        limit_fill_rate = len(limit_orders) / len([r for r in records if r["order_type"] == "limit"]) if len([r for r in records if r["order_type"] == "limit"]) > 0 else 0.0
        
        # 限价单价格偏离分析
        limit_price_deviations = []
        for r in limit_orders:
            if r["limit_price"] and r["exec_price"]:
                deviation = abs(r["exec_price"] - r["limit_price"]) / r["limit_price"] * 10000  # 转换为基点
                limit_price_deviations.append(deviation)
        
        avg_limit_deviation = statistics.mean(limit_price_deviations) if limit_price_deviations else 0.0
        
        return {
            "success": True,
            "period": {
                "days": days,
                "start": cutoff.isoformat(),
                "end": datetime.now().isoformat()
            },
            "total_orders": total_orders,
            "summary": {
                "filled": len(filled_orders),
                "rejected": len(rejected_orders),
                "canceled": len(canceled_orders),
                "fill_rate": round(fill_rate * 100, 2),
                "rejection_rate": round(rejection_rate * 100, 2),
                "cancellation_rate": round(cancellation_rate * 100, 2),
                "total_volume": total_volume,
                "total_amount": round(total_amount, 2),
                "avg_exec_price": round(avg_exec_price, 2),
            },
            "slippage_analysis": {
                "avg_slippage_bps": round(avg_slippage, 2),
                "median_slippage_bps": round(median_slippage, 2),
                "max_slippage_bps": round(max_slippage, 2),
                "min_slippage_bps": round(min_slippage, 2),
                "buy_avg_slippage_bps": round(statistics.mean(buy_slippage), 2) if buy_slippage else 0.0,
                "sell_avg_slippage_bps": round(statistics.mean(sell_slippage), 2) if sell_slippage else 0.0,
            },
            "execution_efficiency": {
                "total_volume": total_volume,
                "total_amount": round(total_amount, 2),
                "avg_exec_price": round(avg_exec_price, 2),
                "orders_per_day": round(total_orders / days, 2) if days > 0 else 0.0,
            },
            "order_type_analysis": {
                "market_orders": len(market_orders),
                "limit_orders": len(limit_orders),
                "market_fill_rate": round(market_fill_rate * 100, 2),
                "limit_fill_rate": round(limit_fill_rate * 100, 2),
                "avg_limit_price_deviation_bps": round(avg_limit_deviation, 2),
            },
            "symbol_stats": dict(self.order_stats) if not symbol else {symbol: self.order_stats.get(symbol, {})},
        }
    
    def get_performance_metrics(
        self,
        symbol: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取性能指标
        
        Args:
            symbol: 股票代码（None表示全部）
            days: 时间范围（天）
            
        Returns:
            性能指标
        """
        report = self.get_execution_report(symbol, days)
        
        # 计算综合执行质量得分（0-100）
        fill_rate = report["summary"]["fill_rate"]
        avg_slippage_bps = abs(report["slippage_analysis"]["avg_slippage_bps"])
        
        # 执行质量得分：成交率权重70%，滑点权重30%（滑点越小越好）
        execution_quality_score = (
            fill_rate * 0.7 + 
            max(0, 100 - min(avg_slippage_bps * 10, 100)) * 0.3
        )
        
        return {
            "execution_quality_score": round(execution_quality_score, 2),
            "fill_rate": fill_rate,
            "avg_slippage_bps": avg_slippage_bps,
            "recommendations": self._generate_recommendations(report),
        }
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        
        fill_rate = report["summary"]["fill_rate"]
        avg_slippage = report["slippage_analysis"]["avg_slippage_bps"]
        rejection_rate = report["summary"]["rejection_rate"]
        
        if fill_rate < 80:
            recommendations.append(f"成交率较低（{fill_rate:.1f}%），建议检查订单价格设置或市场流动性")
        
        if avg_slippage > 10:
            recommendations.append(f"平均滑点较高（{avg_slippage:.2f} bps），建议使用限价单或调整订单规模")
        
        if rejection_rate > 10:
            recommendations.append(f"拒单率较高（{rejection_rate:.1f}%），建议检查风控参数设置")
        
        if report["order_type_analysis"]["limit_fill_rate"] < 50:
            recommendations.append("限价单成交率较低，建议调整限价策略或使用市价单")
        
        if not recommendations:
            recommendations.append("执行质量良好，继续保持")
        
        return recommendations


# 全局实例
execution_analyzer = ExecutionAnalyzer()

