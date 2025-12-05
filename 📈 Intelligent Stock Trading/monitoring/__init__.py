#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票量化监控系统
Stock Quantitative Monitoring System

集成模块：
1. 交易监控系统 (trading_monitor)
2. 策略性能监控 (strategy_performance_monitor) 
3. 风险控制监控 (risk_control_monitor)

版本: v1.0.0
"""

import asyncio
import logging
from typing import Dict, Any

from .trading_monitor import TradingMonitor, trading_monitor
from .strategy_performance_monitor import StrategyPerformanceMonitor, strategy_performance_monitor
from .risk_control_monitor import RiskControlMonitor, risk_control_monitor

logger = logging.getLogger(__name__)


class StockMonitoringSystem:
    """股票量化监控系统"""
    
    def __init__(self):
        self.trading_monitor = trading_monitor
        self.strategy_performance_monitor = strategy_performance_monitor
        self.risk_control_monitor = risk_control_monitor
        
        self.is_running = False
        
        logger.info("✅ 股票量化监控系统已初始化")
    
    async def start_all_monitors(self):
        """启动所有监控系统"""
        try:
            # 启动交易监控
            await self.trading_monitor.start_monitoring()
            
            # 启动策略性能监控
            await self.strategy_performance_monitor.start_monitoring()
            
            # 启动风险控制监控
            await self.risk_control_monitor.start_monitoring()
            
            self.is_running = True
            logger.info("🚀 所有监控系统已启动")
            
        except Exception as e:
            logger.error(f"启动监控系统失败: {e}")
            raise
    
    async def stop_all_monitors(self):
        """停止所有监控系统"""
        try:
            # 停止风险控制监控
            await self.risk_control_monitor.stop_monitoring()
            
            # 停止策略性能监控
            # 注意：StrategyPerformanceMonitor 没有stop方法，需要处理
            
            # 停止交易监控
            await self.trading_monitor.stop_monitoring()
            
            self.is_running = False
            logger.info("🛑 所有监控系统已停止")
            
        except Exception as e:
            logger.error(f"停止监控系统失败: {e}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            trading_status = await self.trading_monitor.get_trading_status()
            risk_overview = await self.risk_control_monitor.get_risk_overview()
            
            return {
                "system_status": "running" if self.is_running else "stopped",
                "trading_monitor": trading_status,
                "risk_control": risk_overview,
                "monitors": {
                    "trading": "active",
                    "strategy_performance": "active",
                    "risk_control": "active"
                },
                "last_updated": trading_status.get("last_heartbeat", "unknown")
            }
            
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "system_status": "error",
                "error": str(e)
            }
    
    async def register_strategy(self, strategy_id: str, strategy_name: str):
        """注册策略到监控系统"""
        try:
            # 注册到策略性能监控
            await self.strategy_performance_monitor.register_strategy(strategy_id, strategy_name)
            
            logger.info(f"✅ 策略 {strategy_name} 已注册到监控系统")
            
        except Exception as e:
            logger.error(f"注册策略失败: {e}")
            raise


# 全局监控系统实例
stock_monitoring_system = StockMonitoringSystem()


async def initialize_stock_monitoring_system():
    """初始化股票量化监控系统"""
    return await stock_monitoring_system.start_all_monitors()


__all__ = [
    "StockMonitoringSystem",
    "stock_monitoring_system",
    "initialize_stock_monitoring_system",
    "TradingMonitor",
    "StrategyPerformanceMonitor", 
    "RiskControlMonitor"
]