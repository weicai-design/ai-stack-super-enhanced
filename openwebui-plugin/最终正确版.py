"""
title: AIStack_Plugin
author: aistack
version: 2.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable
import httpx
import re
import json
from datetime import datetime


class Function:
    class Valves(BaseModel):
        rag_api: str = Field(default="http://host.docker.internal:8011", description="RAG系统API")
        erp_api: str = Field(default="http://host.docker.internal:8013", description="ERP系统API")
        stock_api: str = Field(default="http://host.docker.internal:8014", description="股票系统API")
        content_api: str = Field(default="http://host.docker.internal:8016", description="内容创作API")
        learning_api: str = Field(default="http://host.docker.internal:8019", description="学习系统API")
        
        enable_auto_rag: bool = Field(default=True, description="启用自动RAG检索")
        enable_smart_routing: bool = Field(default=True, description="启用智能路由")
        enable_expert_analysis: bool = Field(default=True, description="启用专家分析")
        enable_interaction_learning: bool = Field(default=True, description="启用交互学习")
        enable_auto_rag_ingest: bool = Field(default=True, description="启用对话入库")
        enable_self_evolution: bool = Field(default=True, description="启用自我进化")

    def __init__(self):
        self.valves = self.Valves()
        
        self.keyword_map = {
            "rag": ["知识", "搜索", "文档", "知识库"],
            "erp": ["财务", "订单", "客户", "生产", "库存", "经营"],
            "stock": ["股票", "股价", "行情", "茅台", "平安"],
            "content": ["创作", "内容", "文案"],
        }
        
        self.expert_map = {
            "erp": "财务管理专家",
            "stock": "投资分析专家",
            "rag": "知识管理专家",
            "content": "内容创作专家",
        }

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """处理用户输入 - 智能增强"""
        
        if not body.get("messages"):
            return body
        
        user_message = body["messages"][-1]["content"]
        user_id = __user__.get("id") if __user__ else "anonymous"
        
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "🧠 AI Stack智能分析中...",
                        "done": False
                    },
                }
            )
        
        # 1. 智能路由 - 识别意图
        detected_system = None
        if self.valves.enable_smart_routing:
            detected_system = self.detect_intent(user_message)
            
            if detected_system and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"🎯 识别到{detected_system}相关问题，正在查询...",
                            "done": False
                        },
                    }
                )
        
        # 2. RAG检索
        rag_context = None
        if self.valves.enable_auto_rag:
            rag_context = await self.auto_rag_search(user_message)
        
        # 3. 系统数据查询
        system_data = None
        if detected_system:
            system_data = await self.call_system(detected_system, user_message)
        
        # 4. 专家分析
        expert_advice = None
        if self.valves.enable_expert_analysis and detected_system:
            expert_advice = await self.get_expert_analysis(
                detected_system, 
                user_message, 
                system_data
            )
        
        # 5. 组合增强上下文
        enhanced_context = ""
        
        if rag_context:
            enhanced_context += f"【📚 知识库检索】\n{rag_context}\n\n"
        
        if system_data:
            enhanced_context += f"【📊 {detected_system.upper()}系统数据】\n{system_data}\n\n"
        
        if expert_advice:
            enhanced_context += f"【👨‍🔬 专家分析建议】\n{expert_advice}\n\n"
        
        if enhanced_context:
            body["messages"].insert(-1, {
                "role": "system",
                "content": f"{enhanced_context}请基于以上信息，为用户提供专业、准确的回答和建议。"
            })
            
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "✅ 已集成RAG知识+实时数据+专家分析", "done": True},
                    }
                )
        
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """处理AI回复 - 自动学习和进化"""
        
        if not body.get("messages") or len(body["messages"]) < 2:
            return body
        
        user_message = body["messages"][-2]["content"] if len(body["messages"]) >= 2 else ""
        ai_response = body["messages"][-1]["content"]
        user_id = __user__.get("id") if __user__ else "anonymous"
        
        # 1. 对话入库RAG
        if self.valves.enable_auto_rag_ingest and user_message and ai_response:
            await self.ingest_interaction_to_rag(user_message, ai_response, user_id)
        
        # 2. 提交学习系统
        if self.valves.enable_interaction_learning:
            await self.submit_to_learning(user_message, ai_response, user_id)
        
        # 3. 触发自我进化
        if self.valves.enable_self_evolution:
            await self.trigger_self_evolution(user_message, ai_response)
        
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
        """RAG自动检索"""
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
                            source = r.get("metadata", {}).get("source", "知识库")
                            context += f"{i}. {text}... (来源: {source})\n"
                        
                        return context
        except:
            pass
        
        return None

    async def call_system(self, system: str, message: str) -> Optional[str]:
        """调用相应系统"""
        try:
            if system == "erp":
                return await self.query_erp(message)
            elif system == "stock":
                return await self.query_stock(message)
            elif system == "rag":
                return await self.query_rag(message)
            elif system == "content":
                return await self.query_content(message)
        except:
            pass
        
        return None

    async def query_erp(self, message: str) -> Optional[str]:
        """查询ERP系统"""
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
        """查询股票系统"""
        code_match = re.search(r'\d{6}', message)
        if not code_match:
            if "茅台" in message:
                code = "600519"
            elif "平安" in message:
                code = "000001"
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
                    return f"{data.get('name')} ({code})\n当前价格: ¥{data.get('price', 0):.2f}\n涨跌幅: {data.get('change_percent', 0):+.2f}%"
        except:
            pass
        
        return None

    async def query_rag(self, message: str) -> Optional[str]:
        """查询RAG"""
        return await self.auto_rag_search(message)

    async def query_content(self, message: str) -> Optional[str]:
        """查询内容创作系统"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.content_api}/api/content/suggestions",
                    params={"query": message},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"创作建议: {data.get('suggestion', '暂无建议')}"
        except:
            pass
        
        return None

    async def get_expert_analysis(
        self, 
        system: str, 
        user_question: str, 
        system_data: Optional[str]
    ) -> Optional[str]:
        """获取专家分析建议"""
        
        expert_name = self.expert_map.get(system, "AI专家")
        
        try:
            templates = {
                "erp": "💡 财务建议：关注收支平衡，建议优化成本结构。如利润下降，需分析具体原因并制定改进措施。",
                "stock": "💡 投资建议：注意风险控制，建议分散投资。价格波动较大时谨慎操作，设置止损点。",
                "rag": "💡 知识建议：建议结合多个知识来源，交叉验证信息准确性，确保信息时效性。",
                "content": "💡 创作建议：注意原创性和差异化，避免AI痕迹过重，保持内容的人性化和情感化。"
            }
            
            return templates.get(system, "💡 专业建议：请谨慎决策，建议咨询专业人士。")
        except:
            return None

    async def ingest_interaction_to_rag(
        self, 
        user_msg: str, 
        ai_response: str, 
        user_id: str
    ) -> bool:
        """自动将对话入库到RAG"""
        
        if not self.valves.enable_auto_rag_ingest:
            return False
        
        try:
            knowledge_entry = f"""
【用户提问】{user_msg}

【AI回答】{ai_response}

【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
【用户】{user_id}
【来源】OpenWebUI交互记录
"""
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.rag_api}/rag/ingest/text",
                    json={
                        "text": knowledge_entry,
                        "metadata": {
                            "type": "interaction",
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat(),
                            "source": "openwebui_chat"
                        },
                        "save_index": True
                    },
                    timeout=10.0
                )
                
                return response.status_code == 200
        except:
            return False

    async def submit_to_learning(
        self, 
        user_msg: str, 
        ai_response: str, 
        user_id: str
    ) -> bool:
        """提交到自我学习系统"""
        
        if not self.valves.enable_interaction_learning:
            return False
        
        try:
            learning_sample = {
                "input": user_msg,
                "output": ai_response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "detected_intent": self.detect_intent(user_msg),
                    "user_satisfaction": None,
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.learning_api}/api/learning/submit",
                    json=learning_sample,
                    timeout=10.0
                )
                
                return response.status_code == 200
        except:
            return False

    async def trigger_self_evolution(
        self, 
        user_msg: str, 
        ai_response: str
    ) -> bool:
        """触发自我进化"""
        
        if not self.valves.enable_self_evolution:
            return False
        
        try:
            quality_metrics = {
                "user_question_length": len(user_msg),
                "ai_response_length": len(ai_response),
                "detected_system": self.detect_intent(user_msg),
                "timestamp": datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.learning_api}/api/evolution/optimize",
                    json=quality_metrics,
                    timeout=5.0
                )
                
                return response.status_code == 200
        except:
            return False

    async def system_status(self) -> str:
        """系统状态检查"""
        try:
            services = {
                "RAG": self.valves.rag_api,
                "ERP": self.valves.erp_api,
                "Stock": self.valves.stock_api,
                "Content": self.valves.content_api,
            }
            
            result = "🏥 **AI Stack 系统状态**\n\n"
            running = 0
            
            async with httpx.AsyncClient() as client:
                for name, url in services.items():
                    try:
                        response = await client.get(f"{url}/health", timeout=2.0)
                        if response.status_code == 200:
                            result += f"✅ {name}\n"
                            running += 1
                        else:
                            result += f"❌ {name}\n"
                    except:
                        result += f"❌ {name}\n"
            
            result += f"\n**可用**: {running}/{len(services)}"
            return result
        except:
            return "❌ 状态检查失败"


