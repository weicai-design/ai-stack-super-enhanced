"""
title: aistack
author: aistack
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable
import httpx
import re
import json
from datetime import datetime


class Plugin:
    class Valves(BaseModel):
        rag_api: str = Field(default="http://host.docker.internal:8011")
        erp_api: str = Field(default="http://host.docker.internal:8013")
        stock_api: str = Field(default="http://host.docker.internal:8014")
        learning_api: str = Field(default="http://host.docker.internal:8019")
        
        enable_auto_rag: bool = Field(default=True)
        enable_smart_routing: bool = Field(default=True)
        enable_learning: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()
        
        self.keyword_map = {
            "rag": ["知识", "搜索", "文档"],
            "erp": ["财务", "订单", "库存"],
            "stock": ["股票", "股价", "茅台"],
        }

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        
        if not body.get("messages"):
            return body
        
        user_message = body["messages"][-1]["content"]
        
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "AI Stack分析中...",
                        "done": False
                    },
                }
            )
        
        detected_system = None
        if self.valves.enable_smart_routing:
            detected_system = self.detect_intent(user_message)
        
        rag_context = None
        if self.valves.enable_auto_rag:
            rag_context = await self.auto_rag_search(user_message)
        
        system_data = None
        if detected_system:
            system_data = await self.call_system(detected_system, user_message)
        
        enhanced_context = ""
        
        if rag_context:
            enhanced_context += f"【知识库】\n{rag_context}\n\n"
        
        if system_data:
            enhanced_context += f"【{detected_system.upper()}数据】\n{system_data}\n\n"
        
        if enhanced_context:
            body["messages"].insert(-1, {
                "role": "system",
                "content": enhanced_context
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
        
        if not body.get("messages") or len(body["messages"]) < 2:
            return body
        
        user_message = body["messages"][-2]["content"] if len(body["messages"]) >= 2 else ""
        ai_response = body["messages"][-1]["content"]
        user_id = __user__.get("id") if __user__ else "anonymous"
        
        if self.valves.enable_learning and user_message and ai_response:
            await self.ingest_interaction(user_message, ai_response, user_id)
        
        return body

    def detect_intent(self, message: str) -> Optional[str]:
        scores = {}
        
        for system, keywords in self.keyword_map.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[system] = score
        
        return max(scores, key=scores.get) if scores else None

    async def auto_rag_search(self, query: str) -> Optional[str]:
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
        try:
            if system == "erp":
                return await self.query_erp(message)
            elif system == "stock":
                return await self.query_stock(message)
        except:
            pass
        
        return None

    async def query_erp(self, message: str) -> Optional[str]:
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

    async def ingest_interaction(
        self, 
        user_msg: str, 
        ai_response: str, 
        user_id: str
    ) -> bool:
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


