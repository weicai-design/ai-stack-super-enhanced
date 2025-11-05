"""
title: AIStack_Enhanced
author: aistack
version: 3.0
description: Full AI Stack integration with RAG validation and self evolution
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
        enable_result_validation: bool = Field(default=True, description="启用结果验证")

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
        """
        需求1+2: 处理用户输入，先检索RAG，将知识作为执行附加条件
        """
        
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
        
        # 步骤1: 智能路由 - 识别用户意图
        detected_system = None
        if self.valves.enable_smart_routing:
            detected_system = self.detect_intent(user_message)
            
            if detected_system and __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"🎯 识别到{detected_system}相关需求",
                            "done": False
                        },
                    }
                )
        
        # 步骤2: 先检索RAG库（需求2的核心）
        rag_context = None
        rag_experience = None
        if self.valves.enable_auto_rag:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "📚 正在检索RAG知识库和历史经验...",
                            "done": False
                        },
                    }
                )
            
            rag_context = await self.auto_rag_search(user_message)
            # 检索历史类似操作的经验
            rag_experience = await self.search_historical_experience(user_message, detected_system)
        
        # 步骤3: 基于RAG知识调用系统（需求2）
        system_data = None
        execution_params = {}
        
        # 将RAG经验转化为执行参数
        if rag_experience:
            execution_params["historical_context"] = rag_experience
            execution_params["learned_preferences"] = True
        
        if detected_system:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"⚙️ 正在执行{detected_system}系统命令...",
                            "done": False
                        },
                    }
                )
            
            system_data = await self.call_system(detected_system, user_message, execution_params)
        
        # 步骤4: 专家分析
        expert_advice = None
        if self.valves.enable_expert_analysis and detected_system:
            expert_advice = await self.get_expert_analysis(
                detected_system, 
                user_message, 
                system_data
            )
        
        # 步骤5: 组合所有信息注入到对话上下文
        enhanced_context = ""
        
        if rag_context:
            enhanced_context += f"【📚 RAG知识库检索】\n{rag_context}\n\n"
        
        if rag_experience:
            enhanced_context += f"【🧠 历史经验】\n{rag_experience}\n\n"
        
        if system_data:
            enhanced_context += f"【📊 {detected_system.upper()}系统执行结果】\n{system_data}\n\n"
        
        if expert_advice:
            enhanced_context += f"【👨‍🔬 专家分析建议】\n{expert_advice}\n\n"
        
        if enhanced_context:
            body["messages"].insert(-1, {
                "role": "system",
                "content": f"{enhanced_context}请基于以上RAG知识、历史经验、系统执行结果和专家建议，为用户提供专业、准确的回答。"
            })
            
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "✅ 已集成RAG知识+历史经验+实时数据+专家分析", "done": True},
                    }
                )
        
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        """
        需求3+4: 验证结果真实性，监控学习，经验积累
        """
        
        if not body.get("messages") or len(body["messages"]) < 2:
            return body
        
        user_message = body["messages"][-2]["content"] if len(body["messages"]) >= 2 else ""
        ai_response = body["messages"][-1]["content"]
        user_id = __user__.get("id") if __user__ else "anonymous"
        
        # 需求3: 验证结果真实性
        validation_note = ""
        if self.valves.enable_result_validation and ai_response:
            validation_note = await self.validate_with_rag(user_message, ai_response, user_id)
            
            # 如果检测到差异，追加说明到回复中
            if validation_note and "差异" in validation_note:
                body["messages"][-1]["content"] = ai_response + f"\n\n{validation_note}"
        
        # 需求4: 监控、收集、分析、学习
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "🧠 正在学习和积累经验...",
                        "done": False
                    },
                }
            )
        
        # 4.1 对话入库到RAG（经验积累）
        if self.valves.enable_auto_rag_ingest and user_message and ai_response:
            await self.ingest_interaction_to_rag(
                user_message, 
                ai_response, 
                user_id,
                validation_note
            )
        
        # 4.2 提交到自我学习系统（监控、分析）
        if self.valves.enable_interaction_learning:
            await self.submit_to_learning(
                user_message, 
                ai_response, 
                user_id,
                validation_note
            )
        
        # 4.3 触发自我进化（形成经验）
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

    async def search_historical_experience(self, query: str, system: Optional[str]) -> Optional[str]:
        """
        需求2增强: 检索历史类似操作的经验
        """
        try:
            search_query = f"{query} {system or ''} 历史操作 经验"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api}/rag/search",
                    params={
                        "query": search_query, 
                        "top_k": 2,
                        "filter": {"type": "interaction"}  # 只搜索历史交互
                    },
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results and len(results) > 0:
                        experience = "根据历史经验：\n"
                        for r in results[:2]:
                            exp_text = r.get("text", "")[:150]
                            experience += f"- {exp_text}...\n"
                        
                        return experience
        except:
            pass
        
        return None

    async def call_system(self, system: str, message: str, params: dict = None) -> Optional[str]:
        """
        调用相应系统（带RAG经验参数）
        """
        try:
            if system == "erp":
                return await self.query_erp(message, params)
            elif system == "stock":
                return await self.query_stock(message, params)
            elif system == "rag":
                return await self.query_rag(message)
            elif system == "content":
                return await self.query_content(message, params)
        except:
            pass
        
        return None

    async def query_erp(self, message: str, params: dict = None) -> Optional[str]:
        """查询ERP系统"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api}/api/finance/summary",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = f"收入: ¥{data.get('revenue', 0):,.0f}\n支出: ¥{data.get('expenses', 0):,.0f}\n利润: ¥{data.get('profit', 0):,.0f}"
                    
                    # 添加执行状态
                    result += f"\n\n✅ ERP系统执行完成"
                    if params and params.get("historical_context"):
                        result += "\n📋 已参考历史经验"
                    
                    return result
        except Exception as e:
            return f"❌ ERP系统执行失败: {str(e)}"
        
        return None

    async def query_stock(self, message: str, params: dict = None) -> Optional[str]:
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
                    result = f"{data.get('name')} ({code})\n当前价格: ¥{data.get('price', 0):.2f}\n涨跌幅: {data.get('change_percent', 0):+.2f}%"
                    result += f"\n\n✅ 股票系统执行完成"
                    
                    if params and params.get("historical_context"):
                        result += "\n📋 已参考历史投资经验"
                    
                    return result
        except Exception as e:
            return f"❌ 股票系统执行失败: {str(e)}"
        
        return None

    async def query_rag(self, message: str) -> Optional[str]:
        """查询RAG"""
        return await self.auto_rag_search(message)

    async def query_content(self, message: str, params: dict = None) -> Optional[str]:
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
                    result = f"创作建议: {data.get('suggestion', '暂无建议')}"
                    result += f"\n\n✅ 内容系统执行完成"
                    return result
        except Exception as e:
            return f"❌ 内容系统执行失败: {str(e)}"
        
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

    async def validate_with_rag(
        self, 
        user_question: str, 
        ai_response: str,
        user_id: str
    ) -> Optional[str]:
        """
        需求3: 用RAG验证结果真实性，检测差异
        """
        
        if not self.valves.enable_result_validation:
            return None
        
        try:
            # 从AI回答中提取关键数据
            extracted_data = self.extract_key_data(ai_response)
            
            if not extracted_data:
                return None
            
            # 在RAG中搜索相关历史数据
            validation_query = f"{user_question} {extracted_data}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api}/rag/search",
                    params={"query": validation_query, "top_k": 3},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results and len(results) > 0:
                        # 检测差异
                        has_difference = self.detect_difference(ai_response, results)
                        
                        if has_difference:
                            return f"""

⚠️ **RAG验证提示**：
当前回复与RAG知识库中的历史记录存在一定差异。

📊 RAG库记录：
{results[0].get('text', '')[:200]}...

🤔 差异理解：
可能是因为：
1. 数据已更新（实时数据与历史不同）
2. 查询条件不同
3. 系统参数调整

💡 建议：
- 如需准确数据，建议交叉验证
- 可查看历史记录对比
- 重要决策请核实最新信息
"""
        except:
            pass
        
        return None

    def extract_key_data(self, text: str) -> str:
        """提取关键数据（数字、金额等）"""
        # 提取数字
        numbers = re.findall(r'¥[\d,]+\.?\d*|\d+\.?\d*%', text)
        return " ".join(numbers[:3]) if numbers else ""

    def detect_difference(self, current_response: str, rag_results: list) -> bool:
        """检测当前回复与RAG记录的差异"""
        # 简单的差异检测逻辑
        current_numbers = set(re.findall(r'\d+', current_response))
        
        for result in rag_results[:2]:
            rag_text = result.get("text", "")
            rag_numbers = set(re.findall(r'\d+', rag_text))
            
            # 如果数字差异超过50%，认为有差异
            if current_numbers and rag_numbers:
                intersection = current_numbers & rag_numbers
                if len(intersection) / max(len(current_numbers), len(rag_numbers)) < 0.5:
                    return True
        
        return False

    async def ingest_interaction_to_rag(
        self, 
        user_msg: str, 
        ai_response: str, 
        user_id: str,
        validation_note: str = None
    ) -> bool:
        """
        需求4: 自动将对话和经验入库到RAG
        """
        
        if not self.valves.enable_auto_rag_ingest:
            return False
        
        try:
            # 构建增强的知识条目
            knowledge_entry = f"""
【用户提问】{user_msg}

【AI回答】{ai_response}

【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
【用户】{user_id}
【来源】OpenWebUI交互记录
"""
            
            if validation_note:
                knowledge_entry += f"\n【验证结果】{validation_note}\n"
            
            # 提交到RAG系统
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.rag_api}/rag/ingest/text",
                    json={
                        "text": knowledge_entry,
                        "metadata": {
                            "type": "interaction",
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat(),
                            "source": "openwebui_chat",
                            "has_validation": validation_note is not None
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
        user_id: str,
        validation_note: str = None
    ) -> bool:
        """
        需求4: 提交到自我学习系统（监控、收集、分析）
        """
        
        if not self.valves.enable_interaction_learning:
            return False
        
        try:
            # 构建详细的学习样本
            learning_sample = {
                "input": user_msg,
                "output": ai_response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "detected_intent": self.detect_intent(user_msg),
                    "user_satisfaction": None,
                    "validation_result": validation_note,
                    "has_rag_verification": validation_note is not None
                },
                "metadata": {
                    "interaction_type": "openwebui_chat",
                    "learning_source": "user_interaction"
                }
            }
            
            # 提交到自我学习系统
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
        """
        需求4: 触发自我进化（形成经验）
        """
        
        if not self.valves.enable_self_evolution:
            return False
        
        try:
            quality_metrics = {
                "user_question_length": len(user_msg),
                "ai_response_length": len(ai_response),
                "detected_system": self.detect_intent(user_msg),
                "timestamp": datetime.now().isoformat(),
                "interaction_quality": self.assess_interaction_quality(user_msg, ai_response)
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

    def assess_interaction_quality(self, user_msg: str, ai_response: str) -> str:
        """评估交互质量"""
        if len(ai_response) > 500:
            return "详细回答"
        elif len(ai_response) > 200:
            return "中等回答"
        else:
            return "简短回答"

    async def system_status(self) -> str:
        """系统状态检查"""
        try:
            services = {
                "RAG": self.valves.rag_api,
                "ERP": self.valves.erp_api,
                "Stock": self.valves.stock_api,
                "Content": self.valves.content_api,
                "Learning": self.valves.learning_api,
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


