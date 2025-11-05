"""
title: ERP Business Query
author: AI Stack Team
version: 1.0.0
description: Query and manage ERP business data through OpenWebUI
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any
import httpx
import json
from datetime import datetime


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        erp_api_endpoint: str = Field(
            default="http://localhost:8013",
            description="ERP系统API端点"
        )
        enable_write: bool = Field(
            default=False,
            description="启用写入操作（创建订单、修改数据等）"
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
        ERP集成动作
        
        支持的命令：
        - /erp financial [period] - 查询财务数据
        - /erp orders [status] - 查询订单
        - /erp customers - 查询客户
        - /erp production - 查询生产状态
        - /erp inventory - 查询库存
        - /erp dashboard - 综合看板
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 发送状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "正在查询ERP系统...", "done": False},
                }
            )
        
        # 解析命令
        if user_message.startswith("/erp financial"):
            parts = user_message.split()
            period = parts[2] if len(parts) > 2 else "month"
            return await self.query_financial(period, __event_emitter__)
        
        elif user_message.startswith("/erp orders"):
            parts = user_message.split()
            status = parts[2] if len(parts) > 2 else None
            return await self.query_orders(status, __event_emitter__)
        
        elif user_message.startswith("/erp customers"):
            return await self.query_customers(__event_emitter__)
        
        elif user_message.startswith("/erp production"):
            return await self.query_production(__event_emitter__)
        
        elif user_message.startswith("/erp inventory"):
            return await self.query_inventory(__event_emitter__)
        
        elif user_message.startswith("/erp dashboard"):
            return await self.get_dashboard(__event_emitter__)
        
        # 自动ERP查询
        else:
            return await self.auto_erp_query(user_message, __event_emitter__)
    
    async def query_financial(
        self, 
        period: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询财务数据"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api_endpoint}/api/finance/dashboard",
                    params={"period": period},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 格式化财务数据
                    formatted = self.format_financial_data(data, period)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "财务数据查询完成", "done": True},
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
    
    async def query_orders(
        self, 
        status: Optional[str], 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询订单"""
        try:
            params = {}
            if status:
                params["status"] = status
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api_endpoint}/api/business/orders",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 格式化订单数据
                    formatted = self.format_orders_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "订单查询完成", "done": True},
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
    
    async def query_customers(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询客户"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api_endpoint}/api/business/customers",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    formatted = self.format_customers_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "客户数据查询完成", "done": True},
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
    
    async def query_production(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询生产状态"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api_endpoint}/api/production/status",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    formatted = self.format_production_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "生产数据查询完成", "done": True},
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
    
    async def query_inventory(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询库存"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api_endpoint}/api/warehouse/inventory",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    formatted = self.format_inventory_data(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "库存数据查询完成", "done": True},
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
    
    async def get_dashboard(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """获取综合看板"""
        try:
            # 并发查询多个端点
            async with httpx.AsyncClient() as client:
                financial = client.get(f"{self.valves.erp_api_endpoint}/api/finance/summary", timeout=5.0)
                orders = client.get(f"{self.valves.erp_api_endpoint}/api/business/orders/summary", timeout=5.0)
                production = client.get(f"{self.valves.erp_api_endpoint}/api/production/summary", timeout=5.0)
                
                # 等待所有请求
                results = await httpx.gather(financial, orders, production)
                
                dashboard_data = {
                    "financial": results[0].json() if results[0].status_code == 200 else {},
                    "orders": results[1].json() if results[1].status_code == 200 else {},
                    "production": results[2].json() if results[2].status_code == 200 else {},
                }
                
                formatted = self.format_dashboard(dashboard_data)
                
                if event_emitter:
                    await event_emitter(
                        {
                            "type": "status",
                            "data": {"description": "看板数据加载完成", "done": True},
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
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def auto_erp_query(
        self, 
        user_message: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[dict]:
        """自动ERP查询 - 智能识别用户意图"""
        keywords = {
            "financial": ["财务", "收入", "支出", "利润", "成本"],
            "orders": ["订单", "客户订单", "销售"],
            "production": ["生产", "制造", "产量"],
            "inventory": ["库存", "仓库", "物料"],
        }
        
        # 简单关键词匹配
        for query_type, kws in keywords.items():
            if any(kw in user_message for kw in kws):
                return await getattr(self, f"query_{query_type}")(event_emitter)
        
        return None  # 没有匹配，继续正常对话
    
    def format_financial_data(self, data: dict, period: str) -> str:
        """格式化财务数据"""
        formatted = f"💰 **财务数据 ({period})**\n\n"
        
        if "revenue" in data:
            formatted += f"**收入**: ¥{data['revenue']:,.2f}\n"
        if "expenses" in data:
            formatted += f"**支出**: ¥{data['expenses']:,.2f}\n"
        if "profit" in data:
            formatted += f"**利润**: ¥{data['profit']:,.2f}\n"
        
        formatted += f"\n[查看详细财务看板](http://localhost:8012/finance/dashboard)"
        
        return formatted
    
    def format_orders_data(self, data: dict) -> str:
        """格式化订单数据"""
        orders = data.get("orders", [])
        total = data.get("total", len(orders))
        
        formatted = f"📦 **订单数据** (共{total}个)\n\n"
        
        for order in orders[:5]:
            formatted += f"- **{order.get('order_no')}**: {order.get('customer')} - ¥{order.get('amount', 0):,.2f} ({order.get('status', 'unknown')})\n"
        
        if total > 5:
            formatted += f"\n... 还有{total-5}个订单\n"
        
        formatted += f"\n[查看所有订单](http://localhost:8012/business/orders)"
        
        return formatted
    
    def format_customers_data(self, data: dict) -> str:
        """格式化客户数据"""
        customers = data.get("customers", [])
        
        formatted = f"👥 **客户数据** (共{len(customers)}个)\n\n"
        
        for customer in customers[:5]:
            formatted += f"- **{customer.get('name')}**: {customer.get('industry')} - {customer.get('level', 'N/A')}级\n"
        
        return formatted
    
    def format_production_data(self, data: dict) -> str:
        """格式化生产数据"""
        formatted = "🏭 **生产状态**\n\n"
        
        if "plans" in data:
            formatted += f"**生产计划**: {len(data['plans'])}个\n"
        if "completed" in data:
            formatted += f"**已完成**: {data['completed']}\n"
        if "in_progress" in data:
            formatted += f"**进行中**: {data['in_progress']}\n"
        
        return formatted
    
    def format_inventory_data(self, data: dict) -> str:
        """格式化库存数据"""
        formatted = "📦 **库存状态**\n\n"
        
        items = data.get("items", [])
        for item in items[:10]:
            formatted += f"- **{item.get('name')}**: {item.get('quantity')} {item.get('unit', '个')}\n"
        
        return formatted
    
    def format_dashboard(self, data: dict) -> str:
        """格式化综合看板"""
        formatted = "📊 **ERP综合看板**\n\n"
        
        if data.get("financial"):
            formatted += "### 💰 财务\n"
            formatted += self.format_financial_data(data["financial"], "今日")
            formatted += "\n\n"
        
        if data.get("orders"):
            formatted += "### 📦 订单\n"
            formatted += f"总订单: {data['orders'].get('total', 0)}\n"
            formatted += f"进行中: {data['orders'].get('in_progress', 0)}\n\n"
        
        if data.get("production"):
            formatted += "### 🏭 生产\n"
            formatted += f"计划: {data['production'].get('plans', 0)}\n"
            formatted += f"完成: {data['production'].get('completed', 0)}\n"
        
        formatted += f"\n\n[访问完整ERP系统](http://localhost:8012)"
        
        return formatted
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ ERP查询错误: {error}"
                }
            ]
        }



