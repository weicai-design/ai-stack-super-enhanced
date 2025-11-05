"""
title: AIStack_Plugin
author: aistack
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable
import httpx
import re
import json
from datetime import datetime


class Functions:
    class Valves(BaseModel):
        rag_api: str = Field(default="http://host.docker.internal:8011", description="RAG系统API")
        erp_api: str = Field(default="http://host.docker.internal:8013", description="ERP系统API")
        stock_api: str = Field(default="http://host.docker.internal:8014", description="股票系统API")
        learning_api: str = Field(default="http://host.docker.internal:8019", description="学习系统API")
        
        enable_auto_rag: bool = Field(default=True, description="启用自动RAG检索")
        enable_smart_routing: bool = Field(default=True, description="启用智能路由")
        enable_learning: bool = Field(default=True, description="启用自动学习")

    def __init__(self):
        self.valves = self.Valves()
        
        self.keyword_map = {
            "rag": ["知识", "搜索", "文档", "知识库"],
            "erp": ["财务", "订单", "客户", "生产", "库存", "经营"],
            "stock": ["股票", "股价", "行情", "茅台", "平安"],
        }

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """处理用户输入"""
        
        if not body.get("messages"):
            return body
        
        user_message = body["messages"][-1]["content"]
        
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "AI Stack智能分析中...",
                        "done": False
                    },
                }
            )
        
        detected_system = None
        if self.valves.enable_smart_routing:
            detected_system = self.detect_intent(user_message)
            
            if detected_system and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"识别到{detected_system}相关问题",
                            "done": False
                        },
                    }
                )
        
        rag_context = None
        if self.valves.enable_auto_rag:
            rag_context = await self.auto_rag_search(user_message)
        
        system_data = None
        if detected_system:
            system_data = await self.call_system(detected_system, user_message)
        
        enhanced_context = ""
        
        if rag_context:
            enhanced_context += f"【知识库检索】\n{rag_context}\n\n"
        
        if system_data:
            enhanced_context += f"【{detected_system.upper()}系统数据】\n{system_data}\n\n"
        
        if enhanced_context:
            body["messages"].insert(-1, {
                "role": "system",
                "content": f"{enhanced_context}请基于以上信息为用户提供专业回答。"
            })
            
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "已集成AI Stack数据", "done": True},
                    }
                )
        
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """处理AI回复"""
        
        if not body.get("messages") or len(body["messages"]) < 2:
            return body
        
        user_message = body["messages"][-2]["content"] if len(body["messages"]) >= 2 else ""
        ai_response = body["messages"][-1]["content"]
        user_id = __user__.get("id") if __user__ else "anonymous"
        
        if self.valves.enable_learning and user_message and ai_response:
            await self.ingest_interaction(user_message, ai_response, user_id)
        
        return body

    def detect_intent(self, message: str) -> Optional[str]:
        """智能意图识别"""
        scores = {}
        
        for system, keywords in self.keyword_map.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[system] = score
        
        return max(scores, key=scores.get) if scores else None

    async def auto_rag_search(self, query: str) -> Optional[str]:
        """RAG检索"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api}/rag/search",
                    params={"query": query, "top_k": 3},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results and len(results) > 0:
                        context = ""
                        for i, r in enumerate(results[:3], 1):
                            text = r.get("text", "")[:200]
                            context += f"{i}. {text}...\n"
                        
                        return context
        except:
            pass
        
        return None

    async def call_system(self, system: str, message: str) -> Optional[str]:
        """调用系统"""
        try:
            if system == "erp":
                return await self.query_erp(message)
            elif system == "stock":
                return await self.query_stock(message)
        except:
            pass
        
        return None

    async def query_erp(self, message: str) -> Optional[str]:
        """查询ERP"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api}/api/finance/summary",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"收入: ¥{data.get('revenue', 0):,.0f}\n支出: ¥{data.get('expenses', 0):,.0f}\n利润: ¥{data.get('profit', 0):,.0f}"
        except:
            pass
        
        return None

    async def query_stock(self, message: str) -> Optional[str]:
        """查询股票"""
        code_match = re.search(r'\d{6}', message)
        if not code_match:
            if "茅台" in message:
                code = "600519"
            else:
                return None
        else:
            code = code_match.group()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api}/api/stock/price/{code}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"{data.get('name')} ({code})\n当前价格: ¥{data.get('price', 0):.2f}"
        except:
            pass
        
        return None

    async def ingest_interaction(self, user_msg: str, ai_response: str, user_id: str) -> bool:
        """保存对话到RAG"""
        try:
            knowledge_entry = f"【用户】{user_msg}\n【AI】{ai_response}\n【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.rag_api}/rag/ingest/text",
                    json={
                        "text": knowledge_entry,
                        "metadata": {
                            "type": "interaction",
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat()
                        },
                        "save_index": True
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
        except:
            return False


