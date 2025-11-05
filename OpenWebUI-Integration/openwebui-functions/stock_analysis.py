"""
title: Stock Trading & Analysis
author: AI Stack Team
version: 1.0.0
description: AI-powered stock analysis and trading through OpenWebUI
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any
import httpx
import json


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        stock_api_endpoint: str = Field(
            default="http://localhost:8014",
            description="股票系统API端点"
        )
        enable_trading: bool = Field(
            default=False,
            description="启用自动交易功能（谨慎开启）"
        )
        max_trade_amount: float = Field(
            default=10000.0,
            description="单笔交易最大金额"
        )
    
    def __init__(self):
        self.valves = self.Valves()
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> Optional[dict]:
        """
        股票分析动作
        
        支持的命令：
        - /stock price <code> - 查询股票价格
        - /stock analyze <code> - 策略分析
        - /stock sentiment - 市场情绪
        - /stock buy <code> <amount> - 买入股票（需启用交易）
        - /stock sell <code> <amount> - 卖出股票（需启用交易）
        - /stock portfolio - 查看持仓
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 发送状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "正在处理股票请求...", "done": False},
                }
            )
        
        # 解析命令
        if user_message.startswith("/stock price"):
            code = user_message.replace("/stock price", "").strip()
            return await self.get_price(code, __event_emitter__)
        
        elif user_message.startswith("/stock analyze"):
            code = user_message.replace("/stock analyze", "").strip()
            return await self.analyze_stock(code, __event_emitter__)
        
        elif user_message.startswith("/stock sentiment"):
            return await self.get_sentiment(__event_emitter__)
        
        elif user_message.startswith("/stock buy"):
            if not self.valves.enable_trading:
                return self.error_response("自动交易功能未启用")
            parts = user_message.split()
            if len(parts) < 4:
                return self.error_response("格式: /stock buy <code> <amount>")
            code, amount = parts[2], float(parts[3])
            return await self.buy_stock(code, amount, __event_emitter__)
        
        elif user_message.startswith("/stock sell"):
            if not self.valves.enable_trading:
                return self.error_response("自动交易功能未启用")
            parts = user_message.split()
            if len(parts) < 4:
                return self.error_response("格式: /stock sell <code> <amount>")
            code, amount = parts[2], float(parts[3])
            return await self.sell_stock(code, amount, __event_emitter__)
        
        elif user_message.startswith("/stock portfolio"):
            return await self.get_portfolio(__event_emitter__)
        
        return None
    
    async def get_price(
        self, 
        code: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询股票价格"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api_endpoint}/api/stock/price/{code}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_price_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "价格查询完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def analyze_stock(
        self, 
        code: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """股票策略分析"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api_endpoint}/api/stock/analyze/{code}",
                    timeout=15.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_analysis_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "策略分析完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def get_sentiment(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """市场情绪分析"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api_endpoint}/api/stock/sentiment",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_sentiment_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "情绪分析完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def buy_stock(
        self, 
        code: str, 
        amount: float, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """买入股票"""
        if amount > self.valves.max_trade_amount:
            return self.error_response(f"交易金额超过限制: ¥{self.valves.max_trade_amount:,.2f}")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.stock_api_endpoint}/api/stock/trade",
                    json={"action": "buy", "code": code, "amount": amount},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = f"✅ **买入成功**\n\n"
                    formatted += f"**股票**: {code}\n"
                    formatted += f"**金额**: ¥{amount:,.2f}\n"
                    formatted += f"**订单号**: {data.get('order_id', 'N/A')}\n"
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "交易完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def sell_stock(
        self, 
        code: str, 
        amount: float, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """卖出股票"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.stock_api_endpoint}/api/stock/trade",
                    json={"action": "sell", "code": code, "amount": amount},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = f"✅ **卖出成功**\n\n"
                    formatted += f"**股票**: {code}\n"
                    formatted += f"**金额**: ¥{amount:,.2f}\n"
                    formatted += f"**订单号**: {data.get('order_id', 'N/A')}\n"
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "交易完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def get_portfolio(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查看持仓"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api_endpoint}/api/stock/portfolio",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_portfolio_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "持仓查询完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response(f"HTTP {response.status_code}")
        
        except Exception as e:
            return self.error_response(str(e))
    
    def format_price_data(self, data: dict) -> str:
        """格式化价格数据"""
        code = data.get("code", "N/A")
        name = data.get("name", "N/A")
        price = data.get("price", 0.0)
        change = data.get("change", 0.0)
        change_pct = data.get("change_percent", 0.0)
        
        arrow = "📈" if change >= 0 else "📉"
        color = "🟢" if change >= 0 else "🔴"
        
        formatted = f"{arrow} **{name} ({code})**\n\n"
        formatted += f"**当前价格**: ¥{price:.2f}\n"
        formatted += f"**涨跌**: {color} {change:+.2f} ({change_pct:+.2f}%)\n"
        formatted += f"\n[查看K线图](http://localhost:8014/stock/{code})"
        
        return formatted
    
    def format_analysis_data(self, data: dict) -> str:
        """格式化分析数据"""
        code = data.get("code", "N/A")
        
        formatted = f"📊 **{code} 策略分析**\n\n"
        
        strategies = data.get("strategies", {})
        for name, result in strategies.items():
            recommendation = result.get("recommendation", "hold")
            confidence = result.get("confidence", 0.0)
            
            icon = "🟢" if recommendation == "buy" else "🔴" if recommendation == "sell" else "🟡"
            
            formatted += f"### {name}\n"
            formatted += f"{icon} **建议**: {recommendation} (置信度: {confidence:.1%})\n"
            formatted += f"**理由**: {result.get('reason', 'N/A')}\n\n"
        
        return formatted
    
    def format_sentiment_data(self, data: dict) -> str:
        """格式化情绪数据"""
        sentiment_score = data.get("sentiment_score", 0.5)
        fear_greed_index = data.get("fear_greed_index", 50)
        trend = data.get("trend", "neutral")
        
        formatted = "😊 **市场情绪分析**\n\n"
        formatted += f"**情绪指数**: {sentiment_score:.2f}\n"
        formatted += f"**恐惧贪婪指数**: {fear_greed_index}\n"
        formatted += f"**市场趋势**: {trend}\n"
        
        return formatted
    
    def format_portfolio_data(self, data: dict) -> str:
        """格式化持仓数据"""
        total_value = data.get("total_value", 0.0)
        total_profit = data.get("total_profit", 0.0)
        positions = data.get("positions", [])
        
        formatted = "💼 **我的持仓**\n\n"
        formatted += f"**总市值**: ¥{total_value:,.2f}\n"
        formatted += f"**总收益**: ¥{total_profit:,.2f}\n\n"
        
        if positions:
            formatted += "### 持仓明细\n\n"
            for pos in positions:
                formatted += f"- **{pos.get('name')} ({pos.get('code')})**: {pos.get('quantity')}股 | 市值 ¥{pos.get('market_value', 0):,.2f}\n"
        
        return formatted
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ 股票操作错误: {error}"
                }
            ]
        }



