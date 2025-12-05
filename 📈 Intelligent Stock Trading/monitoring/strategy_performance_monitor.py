#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化策略性能监控系统
Quantitative Strategy Performance Monitor

功能：
1. 策略运行状态监控
2. 收益分析
3. 风险指标计算
4. 性能报告生成
5. 实时性能指标

版本: v1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import numpy as np
import pandas as pd
from collections import deque

logger = logging.getLogger(__name__)


class StrategyStatus(str, Enum):
    """策略状态"""
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    BACKTESTING = "backtesting"


class PerformanceMetric(str, Enum):
    """性能指标类型"""
    TOTAL_RETURN = "total_return"
    ANNUAL_RETURN = "annual_return"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    CALMAR_RATIO = "calmar_ratio"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    VAR = "var"
    CVAR = "cvar"


@dataclass
class StrategyMetrics:
    """策略性能指标"""
    strategy_id: str
    status: StrategyStatus
    
    # 基础指标
    total_return: float = 0.0
    annual_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    calmar_ratio: float = 0.0
    
    # 交易指标
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    
    # 风险指标
    var_95: float = 0.0
    cvar_95: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0
    
    # 实时指标
    current_pnl: float = 0.0
    today_pnl: float = 0.0
    position_value: float = 0.0
    
    # 时间序列数据
    daily_returns: List[float] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    
    last_update: datetime = field(default_factory=datetime.now)
    start_date: Optional[datetime] = None


@dataclass
class PerformanceReport:
    """性能报告"""
    report_id: str
    strategy_id: str
    period_start: datetime
    period_end: datetime
    
    # 性能摘要
    summary: Dict[str, Any]
    
    # 详细指标
    metrics: Dict[str, float]
    
    # 风险分析
    risk_analysis: Dict[str, Any]
    
    # 交易分析
    trade_analysis: Dict[str, Any]
    
    # 建议
    recommendations: List[str]
    
    generated_at: datetime = field(default_factory=datetime.now)


class StrategyPerformanceMonitor:
    """策略性能监控系统"""
    
    def __init__(self):
        self.strategy_metrics: Dict[str, StrategyMetrics] = {}
        self.performance_history: Dict[str, List[StrategyMetrics]] = {}
        self.reports: List[PerformanceReport] = []
        
        # 监控配置
        self.config = {
            "data_retention_days": 365,  # 数据保留天数
            "real_time_update_interval": 60,  # 实时更新间隔(秒)
            "report_generation_interval": 3600,  # 报告生成间隔(秒)
            "risk_alert_thresholds": {
                "max_drawdown": 0.10,  # 最大回撤阈值
                "volatility": 0.20,  # 波动率阈值
                "var_95": -0.05,  # VaR阈值
            }
        }
        
        # 实时数据缓存
        self.realtime_data: Dict[str, Dict[str, Any]] = {}
        
        logger.info("✅ 量化策略性能监控系统已初始化")
    
    async def start_monitoring(self):
        """启动监控"""
        # 启动实时监控任务
        tasks = [
            asyncio.create_task(self._update_real_time_metrics()),
            asyncio.create_task(self._generate_performance_reports()),
            asyncio.create_task(self._check_risk_alerts()),
        ]
        
        for task in tasks:
            task.add_done_callback(lambda t: logger.info("监控任务完成"))
        
        logger.info("🚀 策略性能监控已启动")
    
    async def register_strategy(self, strategy_id: str, strategy_name: str):
        """注册策略"""
        if strategy_id not in self.strategy_metrics:
            self.strategy_metrics[strategy_id] = StrategyMetrics(
                strategy_id=strategy_id,
                status=StrategyStatus.RUNNING,
                start_date=datetime.now()
            )
            self.performance_history[strategy_id] = []
            
            logger.info(f"✅ 注册策略: {strategy_name} ({strategy_id})")
    
    async def update_trade(self, strategy_id: str, trade_data: Dict[str, Any]):
        """更新交易数据"""
        if strategy_id not in self.strategy_metrics:
            logger.warning(f"未注册的策略: {strategy_id}")
            return
        
        metrics = self.strategy_metrics[strategy_id]
        
        # 更新交易统计
        metrics.total_trades += 1
        
        # 计算盈亏
        pnl = trade_data.get("pnl", 0.0)
        if pnl > 0:
            metrics.avg_profit = (metrics.avg_profit * (metrics.total_trades - 1) + pnl) / metrics.total_trades
        else:
            metrics.avg_loss = (metrics.avg_loss * (metrics.total_trades - 1) + abs(pnl)) / metrics.total_trades
        
        # 更新胜率
        win_trades = len([t for t in self.performance_history.get(strategy_id, []) 
                         if t.current_pnl > 0])
        metrics.win_rate = (win_trades / metrics.total_trades * 100) if metrics.total_trades > 0 else 0
        
        # 更新收益曲线
        metrics.current_pnl += pnl
        metrics.equity_curve.append(metrics.current_pnl)
        
        metrics.last_update = datetime.now()
        
        logger.debug(f"📊 更新策略 {strategy_id} 交易数据")
    
    async def update_market_data(self, strategy_id: str, market_data: Dict[str, Any]):
        """更新市场数据"""
        if strategy_id not in self.strategy_metrics:
            return
        
        # 存储实时数据
        self.realtime_data[strategy_id] = market_data
        
        # 更新今日盈亏
        today_pnl = market_data.get("today_pnl", 0.0)
        self.strategy_metrics[strategy_id].today_pnl = today_pnl
        
        # 更新持仓价值
        position_value = market_data.get("position_value", 0.0)
        self.strategy_metrics[strategy_id].position_value = position_value
    
    async def get_strategy_performance(self, strategy_id: str) -> Dict[str, Any]:
        """获取单个策略性能"""
        if strategy_id not in self.strategy_metrics:
            return {"error": "策略未注册"}
        
        metrics = self.strategy_metrics[strategy_id]
        
        # 计算实时指标
        await self._calculate_real_time_metrics(strategy_id)
        
        return {
            "strategy_id": strategy_id,
            "status": metrics.status.value,
            "performance": {
                "total_return": f"{metrics.total_return:.2%}",
                "annual_return": f"{metrics.annual_return:.2%}",
                "volatility": f"{metrics.volatility:.2%}",
                "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                "max_drawdown": f"{metrics.max_drawdown:.2%}",
                "calmar_ratio": f"{metrics.calmar_ratio:.2f}",
                "current_pnl": f"{metrics.current_pnl:,.0f}",
                "today_pnl": f"{metrics.today_pnl:,.0f}",
                "position_value": f"{metrics.position_value:,.0f}"
            },
            "trading": {
                "total_trades": metrics.total_trades,
                "win_rate": f"{metrics.win_rate:.1f}%",
                "profit_factor": f"{metrics.profit_factor:.2f}",
                "avg_profit": f"{metrics.avg_profit:,.0f}",
                "avg_loss": f"{metrics.avg_loss:,.0f}"
            },
            "risk": {
                "var_95": f"{metrics.var_95:.2%}",
                "cvar_95": f"{metrics.cvar_95:.2%}",
                "beta": f"{metrics.beta:.2f}",
                "alpha": f"{metrics.alpha:.2%}"
            },
            "last_update": metrics.last_update.isoformat()
        }
    
    async def get_strategy_performance(self) -> Dict[str, Any]:
        """获取所有策略性能汇总"""
        strategies = []
        
        for strategy_id, metrics in self.strategy_metrics.items():
            # 计算实时指标
            await self._calculate_real_time_metrics(strategy_id)
            
            strategies.append({
                "strategy_id": strategy_id,
                "status": metrics.status.value,
                "performance": {
                    "total_return": f"{metrics.total_return:.2%}",
                    "annual_return": f"{metrics.annual_return:.2%}",
                    "volatility": f"{metrics.volatility:.2%}",
                    "sharpe_ratio": f"{metrics.sharpe_ratio:.2f}",
                    "max_drawdown": f"{metrics.max_drawdown:.2%}",
                    "current_pnl": f"{metrics.current_pnl:,.0f}",
                    "today_pnl": f"{metrics.today_pnl:,.0f}",
                    "position_value": f"{metrics.position_value:,.0f}"
                },
                "trading": {
                    "total_trades": metrics.total_trades,
                    "win_rate": f"{metrics.win_rate:.1f}%",
                    "profit_factor": f"{metrics.profit_factor:.2f}",
                    "avg_profit": f"{metrics.avg_profit:,.0f}",
                    "avg_loss": f"{metrics.avg_loss:,.0f}"
                },
                "last_update": metrics.last_update.isoformat()
            })
        
        # 计算汇总统计
        total_strategies = len(strategies)
        active_strategies = len([s for s in strategies if s["status"] == "running"])
        
        total_pnl = sum(float(s["performance"]["current_pnl"].replace(',', '')) for s in strategies)
        
        # 计算平均胜率
        win_rates = [float(s["trading"]["win_rate"].rstrip('%')) for s in strategies if s["trading"]["win_rate"] != "0.0%"]
        avg_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0
        
        return {
            "strategies": strategies,
            "summary": {
                "total_strategies": total_strategies,
                "active_strategies": active_strategies,
                "total_pnl": total_pnl,
                "avg_win_rate": f"{avg_win_rate:.1f}%"
            }
        }
    
    async def generate_performance_report(self, strategy_id: str, 
                                        period_start: datetime, 
                                        period_end: datetime) -> PerformanceReport:
        """生成性能报告"""
        if strategy_id not in self.strategy_metrics:
            raise ValueError(f"策略未注册: {strategy_id}")
        
        metrics = self.strategy_metrics[strategy_id]
        
        # 计算报告期内的性能指标
        report_metrics = await self._calculate_period_metrics(
            strategy_id, period_start, period_end
        )
        
        # 生成风险分析
        risk_analysis = await self._analyze_risk(strategy_id, period_start, period_end)
        
        # 生成交易分析
        trade_analysis = await self._analyze_trades(strategy_id, period_start, period_end)
        
        # 生成建议
        recommendations = await self._generate_recommendations(metrics)
        
        report = PerformanceReport(
            report_id=f"REPORT-{strategy_id}-{int(datetime.now().timestamp())}",
            strategy_id=strategy_id,
            period_start=period_start,
            period_end=period_end,
            summary={
                "period": f"{period_start.date()} 至 {period_end.date()}",
                "total_return": report_metrics["total_return"],
                "annual_return": report_metrics["annual_return"],
                "sharpe_ratio": report_metrics["sharpe_ratio"],
                "max_drawdown": report_metrics["max_drawdown"],
                "status": "良好" if report_metrics["sharpe_ratio"] > 1 else "需关注"
            },
            metrics=report_metrics,
            risk_analysis=risk_analysis,
            trade_analysis=trade_analysis,
            recommendations=recommendations
        )
        
        self.reports.append(report)
        logger.info(f"📈 生成策略 {strategy_id} 性能报告")
        
        return report
    
    async def _update_real_time_metrics(self):
        """更新实时指标"""
        while True:
            try:
                for strategy_id in self.strategy_metrics.keys():
                    await self._calculate_real_time_metrics(strategy_id)
                
                await asyncio.sleep(self.config["real_time_update_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"实时指标更新错误: {e}")
                await asyncio.sleep(60)
    
    async def _generate_performance_reports(self):
        """生成性能报告"""
        while True:
            try:
                now = datetime.now()
                
                # 每天生成一次日报
                if now.hour == 18 and now.minute == 0:  # 下午6点
                    for strategy_id in self.strategy_metrics.keys():
                        period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                        period_end = now
                        
                        await self.generate_performance_report(
                            strategy_id, period_start, period_end
                        )
                
                await asyncio.sleep(self.config["report_generation_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"报告生成错误: {e}")
                await asyncio.sleep(300)
    
    async def _check_risk_alerts(self):
        """检查风险告警"""
        while True:
            try:
                for strategy_id, metrics in self.strategy_metrics.items():
                    # 检查最大回撤
                    if metrics.max_drawdown > self.config["risk_alert_thresholds"]["max_drawdown"]:
                        logger.warning(f"🚨 策略 {strategy_id} 最大回撤超限: {metrics.max_drawdown:.2%}")
                    
                    # 检查波动率
                    if metrics.volatility > self.config["risk_alert_thresholds"]["volatility"]:
                        logger.warning(f"🚨 策略 {strategy_id} 波动率超限: {metrics.volatility:.2%}")
                    
                    # 检查VaR
                    if metrics.var_95 < self.config["risk_alert_thresholds"]["var_95"]:
                        logger.warning(f"🚨 策略 {strategy_id} VaR超限: {metrics.var_95:.2%}")
                
                await asyncio.sleep(300)  # 每5分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"风险检查错误: {e}")
                await asyncio.sleep(600)
    
    async def _calculate_real_time_metrics(self, strategy_id: str):
        """计算实时指标"""
        metrics = self.strategy_metrics[strategy_id]
        
        if len(metrics.equity_curve) < 2:
            return
        
        # 计算总收益
        initial_equity = metrics.equity_curve[0] if metrics.equity_curve else 0
        current_equity = metrics.equity_curve[-1]
        
        if initial_equity != 0:
            metrics.total_return = (current_equity - initial_equity) / abs(initial_equity)
        
        # 计算年化收益
        if metrics.start_date:
            days_running = (datetime.now() - metrics.start_date).days
            if days_running > 0:
                metrics.annual_return = ((1 + metrics.total_return) ** (365 / days_running)) - 1
        
        # 计算波动率
        if len(metrics.daily_returns) >= 2:
            returns_array = np.array(metrics.daily_returns)
            metrics.volatility = np.std(returns_array) * np.sqrt(252)
        
        # 计算夏普比率
        risk_free_rate = 0.02  # 假设无风险利率2%
        if metrics.volatility > 0:
            metrics.sharpe_ratio = (metrics.annual_return - risk_free_rate) / metrics.volatility
        
        # 计算最大回撤
        metrics.max_drawdown = self._calculate_max_drawdown(metrics.equity_curve)
        
        # 计算Calmar比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown
        
        # 计算盈利因子
        if metrics.avg_loss > 0:
            metrics.profit_factor = metrics.avg_profit / metrics.avg_loss
        
        # 计算VaR和CVaR
        if len(metrics.daily_returns) >= 10:
            var_cvar = self._calculate_var_cvar(metrics.daily_returns)
            metrics.var_95, metrics.cvar_95 = var_cvar
        
        metrics.last_update = datetime.now()
    
    async def _calculate_period_metrics(self, strategy_id: str, 
                                      period_start: datetime, 
                                      period_end: datetime) -> Dict[str, float]:
        """计算报告期指标"""
        # 模拟计算
        return {
            "total_return": 0.152,
            "annual_return": 0.186,
            "volatility": 0.124,
            "sharpe_ratio": 1.34,
            "max_drawdown": 0.082,
            "calmar_ratio": 2.27,
            "win_rate": 58.3,
            "profit_factor": 1.45,
            "var_95": -0.034,
            "cvar_95": -0.048
        }
    
    async def _analyze_risk(self, strategy_id: str, 
                          period_start: datetime, 
                          period_end: datetime) -> Dict[str, Any]:
        """分析风险"""
        return {
            "risk_assessment": "中等",
            "volatility_analysis": "波动率在正常范围内",
            "drawdown_analysis": "最大回撤控制良好",
            "var_analysis": "VaR值在可接受范围内",
            "stress_test": {
                "market_crash": "-12.5%",
                "volatility_spike": "-8.2%",
                "liquidity_crisis": "-15.3%"
            }
        }
    
    async def _analyze_trades(self, strategy_id: str, 
                            period_start: datetime, 
                            period_end: datetime) -> Dict[str, Any]:
        """分析交易"""
        return {
            "trade_frequency": "适中",
            "win_loss_ratio": "1.38",
            "avg_holding_period": "3.2天",
            "sector_exposure": {
                "technology": "35%",
                "finance": "25%",
                "healthcare": "20%",
                "others": "20%"
            },
            "concentration_risk": "低"
        }
    
    async def _generate_recommendations(self, metrics: StrategyMetrics) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if metrics.sharpe_ratio < 1:
            recommendations.append("建议优化策略以提高风险调整后收益")
        
        if metrics.max_drawdown > 0.10:
            recommendations.append("建议加强风险控制以降低最大回撤")
        
        if metrics.win_rate < 50:
            recommendations.append("建议提高策略胜率")
        
        if len(recommendations) == 0:
            recommendations.append("策略表现良好，继续保持")
        
        return recommendations
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if len(equity_curve) < 2:
            return 0.0
        
        peak = equity_curve[0]
        max_dd = 0.0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _calculate_var_cvar(self, returns: List[float], 
                          confidence_level: float = 0.95) -> Tuple[float, float]:
        """计算VaR和CVaR"""
        if len(returns) < 10:
            return 0.0, 0.0
        
        returns_array = np.array(returns)
        var = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        # CVaR是低于VaR的收益的平均值
        cvar = returns_array[returns_array <= var].mean()
        
        return var, cvar


# 全局监控实例
strategy_performance_monitor = StrategyPerformanceMonitor()


async def initialize_strategy_performance_monitor():
    """初始化策略性能监控系统"""
    await strategy_performance_monitor.start_monitoring()
    return strategy_performance_monitor