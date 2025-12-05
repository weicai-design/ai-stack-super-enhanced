#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制监控系统
Risk Control Monitor System

功能：
1. 仓位监控
2. 止损止盈监控
3. 风险指标计算
4. 风险限额管理
5. 实时风险报警

版本: v1.0.0
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import time

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """风险级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PositionStatus(str, Enum):
    """持仓状态"""
    OPEN = "open"
    CLOSED = "closed"
    HEDGED = "hedged"
    PARTIAL = "partial"


@dataclass
class Position:
    """持仓信息"""
    position_id: str
    symbol: str
    quantity: int
    avg_price: float
    current_price: float
    direction: str  # long/short
    status: PositionStatus
    strategy_id: str
    open_time: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_level: RiskLevel = RiskLevel.LOW
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskAlert:
    """风险告警"""
    alert_id: str
    level: RiskLevel
    type: str
    message: str
    symbol: Optional[str] = None
    strategy_id: Optional[str] = None
    position_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "active"
    action_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RiskLimit:
    """风险限额"""
    limit_id: str
    type: str
    value: float
    current_value: float = 0.0
    utilization: float = 0.0
    breached: bool = False
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class PortfolioRisk:
    """组合风险"""
    portfolio_id: str
    total_value: float = 0.0
    total_pnl: float = 0.0
    today_pnl: float = 0.0
    
    # 风险指标
    var_95: float = 0.0
    cvar_95: float = 0.0
    volatility: float = 0.0
    beta: float = 0.0
    correlation: float = 0.0
    
    # 集中度风险
    concentration_risk: float = 0.0
    sector_concentration: Dict[str, float] = field(default_factory=dict)
    
    # 流动性风险
    liquidity_risk: float = 0.0
    
    last_updated: datetime = field(default_factory=datetime.now)


class RiskControlMonitor:
    """风险控制监控系统"""
    
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.active_alerts: List[RiskAlert] = []
        self.risk_limits: Dict[str, RiskLimit] = {}
        self.portfolio_risk: PortfolioRisk = PortfolioRisk(portfolio_id="default")
        
        # 风险控制配置
        self.config = {
            # 仓位限制
            "max_position_size": 1000000,  # 最大单笔持仓
            "max_portfolio_exposure": 0.3,  # 最大组合暴露
            "max_sector_exposure": 0.2,  # 最大行业暴露
            
            # 止损止盈
            "default_stop_loss": 0.05,  # 默认止损比例
            "default_take_profit": 0.15,  # 默认止盈比例
            "trailing_stop_enabled": True,  # 移动止损
            
            # 风险限额
            "max_daily_loss": 50000,  # 最大单日亏损
            "max_drawdown": 0.10,  # 最大回撤
            "var_limit": -100000,  # VaR限额
            
            # 监控频率
            "position_monitor_interval": 30,  # 持仓监控间隔
            "risk_calc_interval": 60,  # 风险计算间隔
        }
        
        # 初始化风险限额
        self._initialize_risk_limits()
        
        self.monitoring_tasks: Set[asyncio.Task] = set()
        
        logger.info("✅ 风险控制监控系统已初始化")
    
    def _initialize_risk_limits(self):
        """初始化风险限额"""
        self.risk_limits = {
            "daily_loss": RiskLimit(
                limit_id="daily_loss",
                type="daily_loss",
                value=self.config["max_daily_loss"]
            ),
            "position_size": RiskLimit(
                limit_id="position_size",
                type="position_size",
                value=self.config["max_position_size"]
            ),
            "portfolio_exposure": RiskLimit(
                limit_id="portfolio_exposure",
                type="exposure",
                value=self.config["max_portfolio_exposure"]
            ),
            "var_limit": RiskLimit(
                limit_id="var_limit",
                type="var",
                value=self.config["var_limit"]
            )
        }
    
    async def start_monitoring(self):
        """启动监控"""
        tasks = [
            asyncio.create_task(self._monitor_positions()),
            asyncio.create_task(self._calculate_portfolio_risk()),
            asyncio.create_task(self._check_risk_limits()),
            asyncio.create_task(self._cleanup_old_alerts()),
        ]
        
        for task in tasks:
            self.monitoring_tasks.add(task)
            task.add_done_callback(self.monitoring_tasks.discard)
        
        logger.info("🚀 风险控制监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        for task in self.monitoring_tasks:
            task.cancel()
        
        await asyncio.gather(*self.monitoring_tasks, return_exceptions=True)
        logger.info("🛑 风险控制监控已停止")
    
    async def add_position(self, position: Position):
        """添加持仓"""
        # 检查持仓限制
        await self._check_position_limits(position)
        
        # 设置默认止损止盈
        if position.stop_loss is None:
            position.stop_loss = position.avg_price * (1 - self.config["default_stop_loss"])
        if position.take_profit is None:
            position.take_profit = position.avg_price * (1 + self.config["default_take_profit"])
        
        self.positions[position.position_id] = position
        
        logger.info(f"📊 添加持仓: {position.symbol} {position.direction} {position.quantity}股")
    
    async def update_position_price(self, position_id: str, current_price: float):
        """更新持仓价格"""
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        position.current_price = current_price
        
        # 计算未实现盈亏
        price_diff = current_price - position.avg_price
        if position.direction == "short":
            price_diff = -price_diff
        
        position.unrealized_pnl = price_diff * position.quantity
        
        # 检查止损止盈
        await self._check_stop_loss_take_profit(position)
        
        # 更新风险级别
        await self._update_position_risk_level(position)
    
    async def close_position(self, position_id: str, close_price: float):
        """平仓"""
        if position_id not in self.positions:
            return
        
        position = self.positions[position_id]
        
        # 计算已实现盈亏
        price_diff = close_price - position.avg_price
        if position.direction == "short":
            price_diff = -price_diff
        
        position.realized_pnl = price_diff * position.quantity
        position.status = PositionStatus.CLOSED
        
        # 移除持仓
        del self.positions[position_id]
        
        logger.info(f"💵 平仓: {position.symbol} 盈亏{position.realized_pnl:,.0f}")
    
    async def add_risk_alert(self, alert: RiskAlert):
        """添加风险告警"""
        self.active_alerts.append(alert)
        
        # 高风险告警需要立即处理
        if alert.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            alert.action_required = True
            logger.error(f"🚨 高风险告警: {alert.message}")
        else:
            logger.warning(f"⚠️ 风险告警: {alert.message}")
    
    async def get_risk_overview(self) -> Dict[str, Any]:
        """获取风险概览"""
        # 计算当前风险指标
        await self._calculate_current_risk()
        
        return {
            "portfolio": {
                "total_value": self.portfolio_risk.total_value,
                "total_pnl": self.portfolio_risk.total_pnl,
                "today_pnl": self.portfolio_risk.today_pnl,
                "active_positions": len(self.positions),
                "risk_score": self._calculate_risk_score()
            },
            "risk_metrics": {
                "var_95": self.portfolio_risk.var_95,
                "cvar_95": self.portfolio_risk.cvar_95,
                "volatility": self.portfolio_risk.volatility,
                "beta": self.portfolio_risk.beta,
                "concentration_risk": self.portfolio_risk.concentration_risk
            },
            "risk_limits": {
                limit_id: {
                    "type": limit.type,
                    "limit": limit.value,
                    "current": limit.current_value,
                    "utilization": f"{limit.utilization:.1%}",
                    "breached": limit.breached
                }
                for limit_id, limit in self.risk_limits.items()
            },
            "alerts": {
                "total": len(self.active_alerts),
                "by_level": {
                    "critical": len([a for a in self.active_alerts if a.level == RiskLevel.CRITICAL]),
                    "high": len([a for a in self.active_alerts if a.level == RiskLevel.HIGH]),
                    "medium": len([a for a in self.active_alerts if a.level == RiskLevel.MEDIUM]),
                    "low": len([a for a in self.active_alerts if a.level == RiskLevel.LOW])
                }
            },
            "last_updated": self.portfolio_risk.last_updated.isoformat()
        }
    
    async def get_risk_status(self) -> Dict[str, Any]:
        """获取风险状态（API兼容版本）"""
        # 计算当前风险指标
        await self._calculate_current_risk()
        
        # 计算仓位风险
        total_position_value = sum(p.current_price * p.quantity for p in self.positions.values())
        total_portfolio_value = self.portfolio_risk.total_value
        total_position_rate = (total_position_value / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # 计算最大单笔持仓
        max_single_position = 0
        if self.positions:
            max_single_position = max(p.current_price * p.quantity for p in self.positions.values())
            max_single_position_rate = (max_single_position / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
        
        # 计算行业集中度
        sector_concentration = {}
        for position in self.positions.values():
            # 这里需要根据股票代码获取行业信息，暂时使用模拟数据
            sector = "科技"  # 模拟行业
            if sector not in sector_concentration:
                sector_concentration[sector] = 0
            sector_concentration[sector] += position.current_price * position.quantity
        
        # 转换为百分比
        for sector, value in sector_concentration.items():
            sector_concentration[sector] = f"{(value / total_portfolio_value * 100):.1f}%" if total_portfolio_value > 0 else "0%"
        
        # 获取止损监控
        stop_loss_monitor = []
        for position in self.positions.values():
            if position.stop_loss:
                distance = ((position.current_price - position.stop_loss) / position.current_price * 100)
                stop_loss_monitor.append({
                    "symbol": position.symbol,
                    "stop_loss_price": position.stop_loss,
                    "current_price": position.current_price,
                    "distance": f"{distance:.2f}%",
                    "risk_level": position.risk_level.value
                })
        
        # 获取风险告警
        risk_alerts = []
        for alert in self.active_alerts:
            risk_alerts.append({
                "level": alert.level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat()
            })
        
        # 计算风险分数和级别
        risk_score = self._calculate_risk_score()
        risk_level = "低风险"
        if risk_score > 80:
            risk_level = "高风险"
        elif risk_score > 60:
            risk_level = "中高风险"
        elif risk_score > 40:
            risk_level = "中等风险"
        elif risk_score > 20:
            risk_level = "中低风险"
        
        return {
            "position_risk": {
                "total_position_rate": f"{total_position_rate:.1f}%",
                "max_single_position": f"{max_single_position_rate:.1f}%" if self.positions else "0%",
                "sector_concentration": sector_concentration,
                "leverage_ratio": "1.0x",  # 模拟杠杆率
                "margin_usage": f"{total_position_rate:.1f}%"
            },
            "stop_loss_monitor": stop_loss_monitor,
            "risk_alerts": risk_alerts,
            "risk_score": risk_score,
            "risk_level": risk_level
        }
    
    async def get_position_risk(self, position_id: str) -> Dict[str, Any]:
        """获取持仓风险"""
        if position_id not in self.positions:
            return {"error": "持仓不存在"}
        
        position = self.positions[position_id]
        
        return {
            "position_id": position_id,
            "symbol": position.symbol,
            "risk_level": position.risk_level.value,
            "metrics": {
                "unrealized_pnl": position.unrealized_pnl,
                "unrealized_pnl_rate": f"{(position.unrealized_pnl / (position.avg_price * position.quantity)) * 100:.2f}%",
                "stop_loss_distance": f"{((position.current_price - position.stop_loss) / position.current_price * 100) if position.stop_loss else 0:.2f}%" if position.stop_loss else "未设置",
                "take_profit_distance": f"{((position.take_profit - position.current_price) / position.current_price * 100) if position.take_profit else 0:.2f}%" if position.take_profit else "未设置"
            },
            "limits": {
                "max_position_size": self.config["max_position_size"],
                "current_size": position.avg_price * position.quantity,
                "size_utilization": f"{(position.avg_price * position.quantity) / self.config['max_position_size'] * 100:.1f}%"
            }
        }
    
    async def _monitor_positions(self):
        """监控持仓"""
        while True:
            try:
                for position in list(self.positions.values()):
                    # 检查止损止盈
                    await self._check_stop_loss_take_profit(position)
                    
                    # 检查持仓风险
                    await self._check_position_risk(position)
                
                await asyncio.sleep(self.config["position_monitor_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"持仓监控错误: {e}")
                await asyncio.sleep(60)
    
    async def _calculate_portfolio_risk(self):
        """计算组合风险"""
        while True:
            try:
                await self._calculate_current_risk()
                await asyncio.sleep(self.config["risk_calc_interval"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"组合风险计算错误: {e}")
                await asyncio.sleep(120)
    
    async def _check_risk_limits(self):
        """检查风险限额"""
        while True:
            try:
                # 更新限额当前值
                await self._update_risk_limits()
                
                # 检查限额突破
                for limit_id, limit in self.risk_limits.items():
                    if limit.utilization > 0.8 and not limit.breached:  # 80%使用率警告
                        alert = RiskAlert(
                            alert_id=f"LIMIT-{limit_id}-{int(time.time())}",
                            level=RiskLevel.MEDIUM,
                            type="limit_warning",
                            message=f"风险限额接近上限: {limit_id} 使用率{limit.utilization:.1%}"
                        )
                        await self.add_risk_alert(alert)
                    
                    if limit.utilization >= 1.0 and not limit.breached:  # 限额突破
                        limit.breached = True
                        alert = RiskAlert(
                            alert_id=f"LIMIT-BREACH-{limit_id}-{int(time.time())}",
                            level=RiskLevel.HIGH,
                            type="limit_breach",
                            message=f"风险限额已突破: {limit_id}",
                            action_required=True
                        )
                        await self.add_risk_alert(alert)
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"风险限额检查错误: {e}")
                await asyncio.sleep(120)
    
    async def _cleanup_old_alerts(self):
        """清理旧告警"""
        while True:
            try:
                now = datetime.now()
                cutoff_time = now - timedelta(hours=24)  # 保留24小时告警
                
                self.active_alerts = [
                    a for a in self.active_alerts 
                    if a.timestamp > cutoff_time or a.status == "active"
                ]
                
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"告警清理错误: {e}")
                await asyncio.sleep(7200)
    
    async def _check_position_limits(self, position: Position):
        """检查持仓限制"""
        position_value = position.avg_price * position.quantity
        
        # 检查单笔持仓大小
        if position_value > self.config["max_position_size"]:
            alert = RiskAlert(
                alert_id=f"SIZE-{int(time.time())}",
                level=RiskLevel.HIGH,
                type="position_size",
                message=f"持仓超限: {position.symbol} 金额{position_value:,.0f}",
                symbol=position.symbol,
                position_id=position.position_id,
                action_required=True
            )
            await self.add_risk_alert(alert)
    
    async def _check_stop_loss_take_profit(self, position: Position):
        """检查止损止盈"""
        if position.stop_loss and position.current_price <= position.stop_loss:
            alert = RiskAlert(
                alert_id=f"STOP-LOSS-{int(time.time())}",
                level=RiskLevel.MEDIUM,
                type="stop_loss",
                message=f"触发止损: {position.symbol} 价格{position.current_price}",
                symbol=position.symbol,
                position_id=position.position_id
            )
            await self.add_risk_alert(alert)
        
        if position.take_profit and position.current_price >= position.take_profit:
            alert = RiskAlert(
                alert_id=f"TAKE-PROFIT-{int(time.time())}",
                level=RiskLevel.LOW,
                type="take_profit",
                message=f"触发止盈: {position.symbol} 价格{position.current_price}",
                symbol=position.symbol,
                position_id=position.position_id
            )
            await self.add_risk_alert(alert)
    
    async def _check_position_risk(self, position: Position):
        """检查持仓风险"""
        # 检查亏损过大
        if position.unrealized_pnl < -0.1 * (position.avg_price * position.quantity):  # 亏损超过10%
            alert = RiskAlert(
                alert_id=f"LOSS-{int(time.time())}",
                level=RiskLevel.MEDIUM,
                type="position_loss",
                message=f"持仓亏损过大: {position.symbol} 亏损{position.unrealized_pnl:,.0f}",
                symbol=position.symbol,
                position_id=position.position_id
            )
            await self.add_risk_alert(alert)
    
    async def _update_position_risk_level(self, position: Position):
        """更新持仓风险级别"""
        # 基于盈亏比例设置风险级别
        pnl_ratio = abs(position.unrealized_pnl) / (position.avg_price * position.quantity)
        
        if pnl_ratio > 0.15:
            position.risk_level = RiskLevel.CRITICAL
        elif pnl_ratio > 0.10:
            position.risk_level = RiskLevel.HIGH
        elif pnl_ratio > 0.05:
            position.risk_level = RiskLevel.MEDIUM
        else:
            position.risk_level = RiskLevel.LOW
    
    async def _calculate_current_risk(self):
        """计算当前风险"""
        # 计算组合总价值
        total_value = sum(
            p.current_price * p.quantity 
            for p in self.positions.values()
        )
        self.portfolio_risk.total_value = total_value
        
        # 计算总盈亏
        total_pnl = sum(p.unrealized_pnl for p in self.positions.values())
        self.portfolio_risk.total_pnl = total_pnl
        
        # 计算今日盈亏（简化计算）
        self.portfolio_risk.today_pnl = total_pnl * 0.1  # 模拟今日盈亏
        
        # 计算风险指标（模拟数据）
        self.portfolio_risk.var_95 = -total_value * 0.03  # 3% VaR
        self.portfolio_risk.cvar_95 = -total_value * 0.05  # 5% CVaR
        self.portfolio_risk.volatility = 0.12  # 12%波动率
        self.portfolio_risk.beta = 1.05  # 贝塔系数
        self.portfolio_risk.concentration_risk = 0.25  # 集中度风险
        
        self.portfolio_risk.last_updated = datetime.now()
    
    async def _update_risk_limits(self):
        """更新风险限额"""
        # 更新单日亏损限额
        daily_loss_limit = self.risk_limits["daily_loss"]
        daily_loss_limit.current_value = abs(self.portfolio_risk.today_pnl)
        daily_loss_limit.utilization = daily_loss_limit.current_value / daily_loss_limit.value
        daily_loss_limit.last_updated = datetime.now()
        
        # 更新持仓大小限额
        position_size_limit = self.risk_limits["position_size"]
        if self.positions:
            max_position_value = max(
                p.avg_price * p.quantity 
                for p in self.positions.values()
            )
            position_size_limit.current_value = max_position_value
            position_size_limit.utilization = max_position_value / position_size_limit.value
        position_size_limit.last_updated = datetime.now()
        
        # 更新组合暴露限额
        exposure_limit = self.risk_limits["portfolio_exposure"]
        if self.portfolio_risk.total_value > 0:
            # 计算最大行业暴露（简化）
            max_sector_exposure = 0.35  # 模拟数据
            exposure_limit.current_value = max_sector_exposure
            exposure_limit.utilization = max_sector_exposure / exposure_limit.value
        exposure_limit.last_updated = datetime.now()
        
        # 更新VaR限额
        var_limit = self.risk_limits["var_limit"]
        var_limit.current_value = self.portfolio_risk.var_95
        var_limit.utilization = abs(self.portfolio_risk.var_95) / abs(var_limit.value)
        var_limit.last_updated = datetime.now()
    
    def _calculate_risk_score(self) -> float:
        """计算风险评分（0-100，越高风险越大）"""
        score = 0
        
        # 基于风险指标计算评分
        if self.portfolio_risk.volatility > 0.15:
            score += 25
        elif self.portfolio_risk.volatility > 0.10:
            score += 15
        
        if self.portfolio_risk.concentration_risk > 0.3:
            score += 20
        elif self.portfolio_risk.concentration_risk > 0.2:
            score += 10
        
        # 基于限额使用率
        for limit in self.risk_limits.values():
            if limit.utilization > 0.8:
                score += 15
            elif limit.utilization > 0.5:
                score += 5
        
        # 基于活跃告警
        critical_alerts = len([a for a in self.active_alerts if a.level == RiskLevel.CRITICAL])
        high_alerts = len([a for a in self.active_alerts if a.level == RiskLevel.HIGH])
        
        score += critical_alerts * 10
        score += high_alerts * 5
        
        return min(score, 100)


# 全局监控实例
risk_control_monitor = RiskControlMonitor()


async def initialize_risk_control_monitor():
    """初始化风险控制监控系统"""
    await risk_control_monitor.start_monitoring()
    return risk_control_monitor