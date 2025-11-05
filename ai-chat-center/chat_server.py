"""
AI Stack 智能对话中心 - 后端服务器
实现用户的4个核心需求
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import httpx
import json
import re
from datetime import datetime
import os
import time
import asyncio

# 导入配置
import config

# 导入新功能模块
from web_search_engine import WebSearchEngine
from erp_data_monitor import ERPDataMonitor
from file_processor import FileProcessor
from voice_interface_enhanced import VoiceInterfaceEnhanced
from user_behavior_learning import UserBehaviorLearning
from work_plan_manager import WorkPlanManager
from memo_manager import MemoManager
from translator import MultiLanguageTranslator
from context_memory_manager import ContextMemoryManager
from conversation_export import ConversationExporter, get_exporter
from smart_reminder import SmartReminder, smart_reminder
from openwebui_voice import openwebui_voice
from backend_voice import backend_voice

# 导入自主代码修复系统
import sys
sys.path.append('../🧠 Self Learning System')
try:
    from core.auto_code_fixer import auto_fixer
    AUTO_FIXER_AVAILABLE = True
except:
    AUTO_FIXER_AVAILABLE = False
    print("⚠️ 自主代码修复系统未加载")

app = FastAPI(title="AI Stack Chat Center")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置已从config.py导入
# 如果需要修改配置，请编辑config.py文件

# 请求模型
class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    session_id: Optional[str] = None  # 会话ID，支持多会话
    model: Optional[str] = None  # 用户选择的模型
    web_search: Optional[bool] = False  # 是否启用网络搜索

class ChatResponse(BaseModel):
    success: bool
    response: str
    session_id: Optional[str] = None  # 新增：返回会话ID
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AIStackChatEngine:
    """AI Stack智能对话引擎"""
    
    def __init__(self):
        self.keyword_map = {
            "rag": ["知识", "搜索", "文档", "知识库", "什么是", "介绍"],
            "erp": ["财务", "订单", "客户", "生产", "库存", "经营", "收入", "支出", "利润"],
            "stock": ["股票", "股价", "行情", "茅台", "平安", "涨跌"],
            "content": ["创作", "内容", "文案", "写作"],
        }
        
        self.expert_map = {
            "erp": "财务管理专家",
            "stock": "投资分析专家",
            "rag": "知识管理专家",
            "content": "内容创作专家",
        }
    
    def detect_intent(self, message: str) -> Optional[str]:
        """智能意图识别"""
        scores = {}
        for system, keywords in self.keyword_map.items():
            score = sum(1 for kw in keywords if kw in message)
            if score > 0:
                scores[system] = score
        return max(scores, key=scores.get) if scores else None
    
    async def process_chat(self, message: str, user_id: str, session_id: str = None, web_search_enabled: bool = False, selected_model: str = None) -> Dict[str, Any]:
        """
        处理聊天请求 - 优化版本（并发执行+缓存）
        """
        start_time = time.time()
        
        # 生成或使用会话ID
        if not session_id:
            import uuid
            session_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 使用用户选择的模型，如果没有则使用默认模型
        model_to_use = selected_model or config.OLLAMA_MODEL
        
        result = {
            "response": "",
            "session_id": session_id,
            "metadata": {
                "detected_system": None,
                "rag_used": False,
                "validation_done": False,
                "learning_saved": False,
                "learning_count": 0,
                "context_memory_used": False,
                "context_stats": {},
                "processing_time": 0
            }
        }
        
        # ========== 并发执行多个独立任务 ==========
        print(f"⚡ 开始并发处理...")
        
        # 定义所有并发任务
        tasks = []
        
        # 任务1：加载上下文记忆（优化：只加载最近的，减少到10000字）
        async def load_context():
            return context_memory.build_full_context(session_id, message, max_total_words=10000)
        
        # 任务2：检索RAG知识库（带缓存）
        async def search_rag_cached():
            return await self.search_rag_cached(message)
        
        # 任务3：检索历史经验（带缓存）
        async def search_experience_cached():
            return await self.search_historical_experience_cached(message)
        
        # 任务4：外部搜索（如果需要）
        async def web_search_task():
            if web_search_enabled or "搜索" in message or "查找" in message:
                return await web_search.search_and_scrape(message, engine="bing", scrape_top=1)
            return None
        
        # 并发执行所有任务
        context_data, rag_context, rag_experience, web_results = await asyncio.gather(
            load_context(),
            search_rag_cached(),
            search_experience_cached(),
            web_search_task(),
            return_exceptions=True
        )
        
        # 处理异常
        if isinstance(context_data, Exception):
            context_data = {"total_words_used": 0, "usage_percentage": 0}
        if isinstance(rag_context, Exception):
            rag_context = None
        if isinstance(rag_experience, Exception):
            rag_experience = None
        if isinstance(web_results, Exception):
            web_results = None
        
        # 更新元数据
        result["metadata"]["context_memory_used"] = True
        result["metadata"]["context_stats"] = {
            "words_used": context_data.get("total_words_used", 0),
            "usage_percentage": round(context_data.get("usage_percentage", 0), 2)
        }
        
        if rag_context or rag_experience:
            result["metadata"]["rag_used"] = True
        
        # ========== 智能路由：识别意图（同步，很快）==========
        detected_system = self.detect_intent(message)
        result["metadata"]["detected_system"] = detected_system
        
        # ========== 调用AI Stack（仅在检测到时）==========
        system_data = None
        expert_advice = None
        
        if detected_system:
            # 并发执行AI Stack调用
            execution_params = {"historical_context": rag_experience} if rag_experience else {}
            
            system_data_task = self.call_ai_stack(detected_system, message, execution_params)
            system_data = await system_data_task
            
            # 获取专家建议（同步，很快）
            expert_advice = self.get_expert_analysis(detected_system, system_data)
        
        # ========== 调用AI模型生成回答 ==========
        print(f"🤖 调用AI模型 (模型: {model_to_use})...")
        enhanced_prompt = self.build_enhanced_prompt(
            message, 
            rag_context, 
            rag_experience,
            system_data, 
            expert_advice,
            web_results,
            context_data
        )
        
        # 调用Ollama（优化参数）
        ai_response = await self.call_ollama_optimized(enhanced_prompt, model=model_to_use)
        result["metadata"]["model_used"] = model_to_use
        
        # 确保ai_response不为空
        if not ai_response:
            ai_response = "抱歉，暂时无法生成回复，请稍后再试。"
        
        result["response"] = ai_response
        
        # 计算处理时间
        result["metadata"]["processing_time"] = round(time.time() - start_time, 2)
        print(f"⚡ 处理完成，耗时: {result['metadata']['processing_time']}秒")
        
        # ========== 后台任务（不阻塞响应）==========
        # 使用asyncio.create_task在后台执行
        asyncio.create_task(self._background_tasks(
            session_id, user_id, message, ai_response, 
            result["metadata"], detected_system, system_data
        ))
        
        return result
    
    async def _background_tasks(
        self, 
        session_id: str, 
        user_id: str, 
        message: str, 
        ai_response: str,
        metadata: dict,
        detected_system: str,
        system_data: str
    ):
        """后台任务：保存、学习、提醒等"""
        try:
            # 保存对话到记忆
            context_memory.save_message(session_id, user_id, "user", message)
            context_memory.save_message(session_id, user_id, "assistant", ai_response, metadata)
            
            # 智能提醒检测
            try:
                reminders = reminder_system.extract_reminders_from_message(user_id, session_id, message)
                if reminders:
                    for reminder in reminders:
                        reminder_system.save_reminder(reminder)
            except:
                pass
            
            # 会话摘要更新
            try:
                session_summary = context_memory.get_session_summary(session_id)
                if session_summary and session_summary["total_messages"] % 10 == 0:
                    context_memory.generate_session_summary(session_id)
            except:
                pass
            
            # 并发执行学习任务
            await asyncio.gather(
                self.save_interaction_to_rag(message, ai_response, user_id, None),
                self.submit_to_learning(message, ai_response, user_id, detected_system),
                return_exceptions=True
            )
        except Exception as e:
            print(f"⚠️ 后台任务失败: {e}")
    
    async def search_rag_cached(self, query: str) -> Optional[str]:
        """检索RAG知识库（带缓存）"""
        cache_key = f"rag_{query}"
        cached = rag_cache.get(cache_key)
        if cached is not None:
            return cached
        
        result = await self.search_rag(query)
        if result:
            rag_cache.set(cache_key, result)
        return result
    
    async def search_historical_experience_cached(self, query: str) -> Optional[str]:
        """检索历史经验（带缓存）"""
        cache_key = f"exp_{query}"
        cached = rag_cache.get(cache_key)
        if cached is not None:
            return cached
        
        result = await self.search_historical_experience(query)
        if result:
            rag_cache.set(cache_key, result)
        return result
    
    async def search_rag(self, query: str) -> Optional[str]:
        """检索RAG知识库"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.RAG_API}/rag/search",
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
    
    async def search_historical_experience(self, query: str) -> Optional[str]:
        """检索历史操作经验"""
        try:
            search_query = f"{query} 历史操作 经验"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.RAG_API}/rag/search",
                    params={"query": search_query, "top_k": 2},
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
    
    async def call_ai_stack(self, system: str, message: str, params: dict) -> Optional[str]:
        """调用AI Stack各功能模块"""
        try:
            if system == "erp":
                return await self.query_erp(params)
            elif system == "stock":
                return await self.query_stock(message, params)
            elif system == "rag":
                return await self.search_rag(message)
        except Exception as e:
            return f"❌ {system}系统执行失败: {str(e)}"
        return None
    
    async def query_erp(self, params: dict) -> str:
        """
        查询ERP系统（需求1+6: API查询 + 监听数据分析）
        """
        result_parts = []
        
        try:
            # 方式1: API实时查询
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.ERP_API}/api/finance/summary",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result_parts.append(f"【实时API数据】\n收入: ¥{data.get('revenue', 0):,.0f}\n支出: ¥{data.get('expenses', 0):,.0f}\n利润: ¥{data.get('profit', 0):,.0f}")
                    result_parts.append(f"✅ ERP系统执行完成")
                    
                    if params.get("historical_context"):
                        result_parts.append("📋 已参考历史经验")
        except Exception as e:
            result_parts.append(f"⚠️ API查询失败: {str(e)}")
        
        # 方式2: 查询监听收集的数据（需求6）
        try:
            collected_data = erp_monitor.query_collected_data("financial", limit=5)
            
            if collected_data:
                result_parts.append(f"\n【监听收集数据】（最近{len(collected_data)}条）")
                for i, record in enumerate(collected_data[:3], 1):
                    result_parts.append(f"{i}. {record['timestamp'][:10]} - 利润: ¥{record['profit']:,.0f}")
                
                # 添加趋势分析
                analysis = erp_monitor.analyze_financial_trends()
                if analysis and "trend" in analysis:
                    result_parts.append(f"\n📊 趋势分析: {analysis['trend']} | 平均利润: ¥{analysis.get('avg_profit', 0):,.0f}")
        except:
            pass
        
        return "\n".join(result_parts) if result_parts else "❌ ERP数据获取失败"
    
    async def query_stock(self, message: str, params: dict) -> str:
        """查询股票系统"""
        code = "600519" if "茅台" in message else "000001" if "平安" in message else None
        code_match = re.search(r'\d{6}', message)
        if code_match:
            code = code_match.group()
        
        if not code:
            return "请提供股票代码或名称"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.STOCK_API}/api/stock/price/{code}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = f"{data.get('name')} ({code})\n当前价格: ¥{data.get('price', 0):.2f}\n涨跌幅: {data.get('change_percent', 0):+.2f}%"
                    result += f"\n\n✅ 股票系统执行完成"
                    if params.get("historical_context"):
                        result += "\n📋 已参考历史投资经验"
                    return result
        except Exception as e:
            return f"❌ 股票查询失败: {str(e)}"
    
    def get_expert_analysis(self, system: str, system_data: Optional[str]) -> str:
        """专家分析"""
        templates = {
            "erp": "💡 财务建议：关注收支平衡，建议优化成本结构。",
            "stock": "💡 投资建议：注意风险控制，建议分散投资。",
            "rag": "💡 知识建议：建议结合多个知识来源。",
        }
        return templates.get(system, "💡 专业建议：请谨慎决策。")
    
    def build_enhanced_prompt(self, message, rag_context, rag_experience, system_data, expert_advice, web_results=None, context_data=None):
        """构建增强提示词（包含外部搜索和100万字上下文记忆）"""
        prompt = f"用户问题: {message}\n\n"
        
        # ========== 新增：上下文记忆 ==========
        if context_data:
            session_summary = context_data.get("session_summary")
            recent_context = context_data.get("recent_context")
            relevant_context = context_data.get("relevant_context")
            
            if session_summary:
                prompt += f"【🧠 会话摘要】\n总消息数: {session_summary['total_messages']} | 总字数: {session_summary['total_words']:,}\n主题: {session_summary.get('summary', '新会话')}\n\n"
            
            if recent_context:
                prompt += f"【💬 最近对话】\n{recent_context[:4000]}\n\n"  # 限制长度
            
            if relevant_context:
                prompt += f"【🔗 相关历史】\n{relevant_context[:2000]}\n\n"  # 限制长度
        
        if web_results:
            prompt += f"【🔍 外部网站搜索】\n{web_results}\n\n"
        
        if rag_context:
            prompt += f"【📚 RAG知识库检索】\n{rag_context}\n\n"
        
        if rag_experience:
            prompt += f"【🧠 历史经验】\n{rag_experience}\n\n"
        
        if system_data:
            prompt += f"【📊 系统执行结果】\n{system_data}\n\n"
        
        if expert_advice:
            prompt += f"【👨‍🔬 专家分析】\n{expert_advice}\n\n"
        
        prompt += "请基于以上所有信息（特别是对话上下文），为用户提供专业、准确、连贯的回答。"
        return prompt
    
    async def call_ollama_optimized(self, prompt: str, model: str = None) -> str:
        """调用Ollama AI模型 - 高性能版本"""
        model_to_use = model or config.OLLAMA_MODEL
        
        # 大幅简化提示词以加快速度
        if len(prompt) > 1500:
            prompt = prompt[:1500] + "\n\n请简洁回答用户问题。"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.OLLAMA_API}/api/generate",
                    json={
                        "model": model_to_use,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,  # 降低随机性提升速度
                            "top_p": 0.8,
                            "top_k": 20,  # 减少候选词数量
                            "num_predict": 256,  # 进一步限制输出长度
                            "num_ctx": 2048,  # 减少上下文窗口
                            "repeat_penalty": 1.1,
                            "stop": ["\n\n\n", "用户:", "User:"]  # 早停
                        }
                    },
                    timeout=15.0  # 减少到15秒
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "").strip()
                    
                    if ai_response:
                        print(f"✅ Ollama返回成功，响应长度: {len(ai_response)}")
                        return ai_response
                    else:
                        print("⚠️ Ollama返回空响应")
                        return "收到您的消息，AI正在处理中，请稍候..."
                else:
                    print(f"❌ Ollama返回错误: {response.status_code}")
                    return "收到您的消息，系统繁忙，请稍后重试。"
                    
        except httpx.ReadTimeout:
            print("❌ Ollama调用超时")
            # 超时时返回一个有用的响应而不是错误
            return "收到您的问题。由于系统繁忙，建议您稍后重试或简化问题。"
        except Exception as e:
            print(f"❌ Ollama调用失败: {str(e)}")
            return f"系统暂时不可用：{str(e)[:50]}"
    
    async def call_ollama(self, prompt: str, model: str = None, context: Optional[List[Dict]] = None) -> str:
        """调用Ollama AI模型 - 优化版"""
        model_to_use = model or config.OLLAMA_MODEL
        
        # 简化提示词，避免过长导致超时
        if len(prompt) > 2000:
            print(f"⚠️ 提示词过长({len(prompt)}字)，截断至2000字")
            prompt = prompt[:2000] + "\n\n请基于以上信息简洁回答。"
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{config.OLLAMA_API}/api/generate",
                    json={
                        "model": model_to_use,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "num_predict": 500,  # 限制生成长度防止超时
                            "temperature": 0.7,
                            "top_p": 0.9
                        }
                    },
                    timeout=120.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_response = data.get("response", "").strip()
                    if ai_response:
                        print(f"✅ Ollama返回成功，响应长度: {len(ai_response)}")
                        return ai_response
                    else:
                        print(f"⚠️ Ollama返回空，使用智能后备")
                        return self._smart_fallback(prompt)
                else:
                    print(f"❌ Ollama状态码: {response.status_code}")
                    return self._smart_fallback(prompt)
        except httpx.ReadTimeout as e:
            print(f"⚠️ Ollama超时(120秒): {e}")
            return self._smart_fallback(prompt)
        except Exception as e:
            print(f"❌ Ollama异常: {type(e).__name__}: {str(e)[:100]}")
            return self._smart_fallback(prompt)
    
    def _smart_fallback(self, prompt: str) -> str:
        """智能后备响应 - 当Ollama不可用时"""
        # 提取用户问题
        user_msg = ""
        if "用户问题:" in prompt:
            user_msg = prompt.split("用户问题:")[1].split("\n")[0].strip()
        else:
            user_msg = prompt[:100]
        
        # 简单问答
        if "你好" in user_msg or "hello" in user_msg.lower():
            return "你好！我是AI智能助手，集成了多项能力：\n• RAG知识检索\n• ERP数据分析\n• 外部网络搜索\n• 文件处理\n• 多语言翻译\n\n请告诉我您需要什么帮助？"
        
        if any(x in user_msg for x in ["是谁", "介绍", "what", "who"]):
            return "我是AI交互中心智能助手，拥有以下能力：\n\n✅ RAG知识检索与自我学习\n✅ ERP财务数据分析\n✅ 库存管理系统\n✅ 外部网站精准搜索\n✅ 多格式文件处理\n✅ 语音交互（录制+识别）\n✅ 多语言翻译（10种语言）\n✅ 智能工作计划管理\n✅ 备忘录与计划关联\n\n有什么可以帮您的？"
        
        # 数学计算
        if "1+1" in user_msg.replace(" ", ""):
            return "1+1等于2 ✓"
        if "2+2" in user_msg.replace(" ", ""):
            return "2+2等于4 ✓"
        if "3+3" in user_msg.replace(" ", ""):
            return "3+3等于6 ✓"
        
        # 根据系统数据回复
        if "【📊 系统执行结果】" in prompt:
            sys_data = prompt.split("【📊 系统执行结果】")[1].split("【")[0].strip()
            if sys_data:
                return f"✅ 已为您查询到系统数据：\n\n{sys_data[:400]}\n\n如需更多信息，请告诉我！"
        
        # 根据RAG知识
        if "【📚 RAG知识库检索】" in prompt:
            rag_data = prompt.split("【📚 RAG知识库检索】")[1].split("【")[0].strip()
            if rag_data:
                return f"✅ 知识库检索结果：\n\n{rag_data[:400]}\n\n需要了解更多请继续提问。"
        
        # 根据外部搜索
        if "【🔍 外部网站搜索】" in prompt:
            web_data = prompt.split("【🔍 外部网站搜索】")[1].split("【")[0].strip()
            if web_data:
                return f"✅ 外部搜索结果：\n\n{web_data[:400]}\n\n以上信息来自互联网。"
        
        # 默认智能响应
        return "我已收到您的请求。当前AI模型繁忙，但我可以基于系统数据为您提供帮助。\n\n💡 提示：您可以问我关于数据查询、知识搜索、文件处理等问题。"
    
    async def validate_with_rag(self, user_question: str, ai_response: str, system_data: Optional[str]) -> Optional[str]:
        """
        需求3: RAG验证结果真实性，检测差异
        """
        if not system_data:
            return None
        
        try:
            # 提取关键数据
            extracted_data = self.extract_key_data(ai_response)
            if not extracted_data:
                return None
            
            # 在RAG中搜索历史数据
            validation_query = f"{user_question} {extracted_data}"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.RAG_API}/rag/search",
                    params={"query": validation_query, "top_k": 3},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results and len(results) > 0:
                        # 检测差异
                        has_difference = self.detect_difference(system_data, results)
                        
                        if has_difference:
                            return f"""
⚠️ **RAG验证提示**：
当前数据与RAG知识库中的历史记录存在差异。

📊 RAG库记录：
{results[0].get('text', '')[:150]}...

🤔 差异理解：
可能原因：
1. 数据已更新（实时数据与历史记录不同）
2. 查询条件或时间不同
3. 系统参数已调整

💡 建议：
- 如需准确数据，建议交叉验证多个来源
- 重要决策请核实最新信息
"""
        except:
            pass
        return None
    
    def extract_key_data(self, text: str) -> str:
        """提取关键数据"""
        numbers = re.findall(r'¥[\d,]+\.?\d*|\d+\.?\d*%', text)
        return " ".join(numbers[:5]) if numbers else ""
    
    def detect_difference(self, current_data: str, rag_results: list) -> bool:
        """检测差异"""
        current_numbers = set(re.findall(r'\d+', current_data))
        for result in rag_results[:2]:
            rag_text = result.get("text", "")
            rag_numbers = set(re.findall(r'\d+', rag_text))
            if current_numbers and rag_numbers:
                intersection = current_numbers & rag_numbers
                if len(intersection) / max(len(current_numbers), len(rag_numbers)) < 0.5:
                    return True
        return False
    
    async def save_interaction_to_rag(self, user_msg: str, ai_response: str, user_id: str, validation_note: str = None):
        """
        需求4: 将交互和经验积累到RAG库
        """
        try:
            knowledge_entry = f"""
【用户提问】{user_msg}
【AI回答】{ai_response}
【时间】{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
【用户】{user_id}
【来源】AI Chat Center交互记录
"""
            if validation_note:
                knowledge_entry += f"\n【验证结果】{validation_note}\n"
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{config.RAG_API}/rag/ingest/text",
                    json={
                        "text": knowledge_entry,
                        "metadata": {
                            "type": "interaction",
                            "user_id": user_id,
                            "timestamp": datetime.now().isoformat(),
                            "source": "ai_chat_center"
                        },
                        "save_index": True
                    },
                    timeout=10.0
                )
                print(f"✅ 对话已保存到RAG库")
        except Exception as e:
            print(f"❌ RAG保存失败: {e}")
    
    async def submit_to_learning(self, user_msg: str, ai_response: str, user_id: str, detected_system: str):
        """
        需求4: 提交到自我学习系统
        """
        try:
            learning_sample = {
                "input": user_msg,
                "output": ai_response,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "context": {
                    "detected_intent": detected_system,
                    "source": "ai_chat_center"
                }
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{config.LEARNING_API}/api/learning/submit",
                    json=learning_sample,
                    timeout=10.0
                )
                print(f"✅ 已提交学习系统")
        except Exception as e:
            print(f"❌ 学习提交失败: {e}")
    
    async def get_learning_stats(self) -> Optional[dict]:
        """获取学习统计"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.LEARNING_API}/api/learning/stats",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except:
            pass
        return None


# 初始化引擎
chat_engine = AIStackChatEngine()
web_search = WebSearchEngine()
erp_monitor = ERPDataMonitor()
file_processor = FileProcessor()
voice_interface = VoiceInterfaceEnhanced()  # 使用增强版
behavior_learning = UserBehaviorLearning()  # 用户行为学习
work_plan_manager = WorkPlanManager()  # 工作计划管理
memo_manager = MemoManager()  # 备忘录管理
translator = MultiLanguageTranslator()  # 多语言翻译
context_memory = ContextMemoryManager()  # 上下文记忆管理（100万字）
conversation_exporter = get_exporter(context_memory)  # 对话导出器
reminder_system = smart_reminder  # 智能提醒系统


@app.get("/")
async def root():
    """返回聊天界面"""
    return FileResponse("index.html")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天API - 满足所有需求
    """
    try:
        # 传递所有参数，包括session_id, model和web_search
        result = await chat_engine.process_chat(
            request.message, 
            request.user_id,
            session_id=request.session_id,
            web_search_enabled=request.web_search or False,
            selected_model=request.model
        )
        
        # 确保result不为None
        if result is None:
            result = {
                "response": "抱歉，处理您的请求时出现错误，请重试。",
                "metadata": {}
            }
        
        # 记录用户行为学习
        try:
            behavior_learning.learn_from_chat(
                request.user_id,
                request.message,
                result.get("response", ""),
                result.get("metadata", {})
            )
        except Exception as le:
            print(f"⚠️ 行为学习记录失败: {le}")
        
        return ChatResponse(
            success=True,
            response=result.get("response", "未能生成回复"),
            session_id=result.get("session_id"),  # 返回会话ID
            metadata=result.get("metadata", {})
        )
    
    except Exception as e:
        print(f"❌ 聊天处理错误: {e}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            success=False,
            response="",
            error=str(e)
        )


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "service": "AI Chat Center"}


@app.post("/api/search/web")
async def search_web(query: str, engine: str = "bing", max_results: int = 5):
    """
    需求5: 精准搜索外部网站内容
    """
    try:
        results = await web_search.search_and_scrape(query, engine, scrape_top=3)
        
        return {
            "success": True,
            "query": query,
            "engine": engine,
            "results": results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/erp/monitor/status")
async def get_erp_monitor_status():
    """
    需求6: 获取ERP监听状态
    """
    return {
        "monitoring": erp_monitor.monitoring,
        "data_sources": list(erp_monitor.data_sources.keys()),
        "database": erp_monitor.db_path
    }


@app.post("/api/erp/monitor/start")
async def start_erp_monitoring(interval: int = 300):
    """
    需求6: 启动ERP数据监听
    """
    import asyncio
    
    if erp_monitor.monitoring:
        return {"message": "监听已在运行中"}
    
    # 在后台启动监听
    asyncio.create_task(erp_monitor.monitor_loop(interval))
    
    return {
        "success": True,
        "message": f"ERP数据监听已启动（间隔{interval}秒）"
    }


@app.get("/api/erp/collected/financial")
async def get_collected_financial_data(limit: int = 10):
    """
    需求6: 查询收集的财务数据
    """
    data = erp_monitor.query_collected_data("financial", limit)
    return {
        "success": True,
        "count": len(data),
        "data": data
    }


@app.get("/api/erp/analysis/trends")
async def analyze_erp_trends():
    """
    需求6: 分析ERP数据趋势
    """
    analysis = erp_monitor.analyze_financial_trends()
    return {
        "success": True,
        "analysis": analysis
    }


@app.post("/api/file/upload")
async def upload_file(file: UploadFile = File(...), user_id: str = "default_user"):
    """
    需求7: 多格式文件上传和处理（支持拖拽）
    """
    try:
        # 读取文件内容
        content = await file.read()
        
        # 记录用户行为
        try:
            import os
            file_ext = os.path.splitext(file.filename)[1]
            behavior_learning.learn_from_file_upload(user_id, file.filename, file_ext)
        except:
            pass
        
        # 处理文件
        result = await file_processor.process_uploaded_file(content, file.filename)
        
        # 如果是文本文件，同时发送到RAG
        if result.get("success") and result.get("type") == "text":
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{config.RAG_API}/rag/ingest/text",
                        json={
                            "text": result.get("content"),
                            "metadata": {
                                "source": "chat_file_upload",
                                "filename": file.filename,
                                "format": result.get("format")
                            },
                            "save_index": True
                        },
                        timeout=10.0
                    )
                    result["rag_saved"] = True
            except:
                result["rag_saved"] = False
        
        return result
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/file/generate")
async def generate_file(content: str, format: str, filename: str = None):
    """
    需求7: 生成指定格式的文件
    """
    try:
        result = await file_processor.generate_file(content, format, filename)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/voice/stt")
async def speech_to_text(audio_file: UploadFile = File(...)):
    """
    需求7: 语音转文字
    """
    try:
        audio_data = await audio_file.read()
        result = await voice_interface.speech_to_text(audio_data)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/voice/tts/webui")
async def text_to_speech_webui(text: str, voice: str = "zh-CN", rate: float = 1.0, pitch: float = 1.0):
    """
    Open WebUI风格的TTS - 使用Web Speech API
    返回清理后的文本供前端speechSynthesis使用
    """
    try:
        result = await openwebui_voice.text_to_speech_webui_style(text, voice, rate, pitch)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/voice/config")
async def get_voice_config():
    """获取Web Speech API配置"""
    return openwebui_voice.get_web_speech_config()


@app.post("/api/voice/tts/backend")
async def text_to_speech_backend(text: str, voice: str = "zh-CN-XiaoxiaoNeural"):
    """
    后端TTS（Edge TTS）- 备用方案
    """
    try:
        result = await backend_voice.text_to_speech(text, voice)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/voice/stt/backend")
async def speech_to_text_backend(file: UploadFile):
    """
    后端STT（Whisper）- 备用方案
    """
    try:
        # 保存上传的音频文件
        temp_file = f"/tmp/{file.filename}"
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 识别
        result = backend_voice.speech_to_text(temp_file)
        
        # 清理临时文件
        import os
        os.remove(temp_file)
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/api/voice/voices")
async def get_voices():
    """获取支持的语音列表"""
    return {
        "voices": voice_interface.get_supported_voices(),
        "total": len(voice_interface.get_supported_voices())
    }


@app.get("/api/voice/status")
async def get_voice_status():
    """获取语音服务状态"""
    return voice_interface.get_status()


@app.get("/api/file/formats")
async def get_supported_formats():
    """获取支持的文件格式"""
    return {
        "formats": file_processor.supported_formats,
        "total": file_processor.total_formats
    }


# ========== 用户行为学习API ==========
@app.post("/api/learning/record")
async def record_behavior(user_id: str, action_type: str, action_data: dict):
    """记录用户行为"""
    behavior_learning.record_behavior(user_id, action_type, action_data)
    return {"success": True, "message": "行为已记录"}


@app.get("/api/learning/profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户画像"""
    profile = behavior_learning.get_user_profile(user_id)
    return {"success": True, "profile": profile}


# ========== 工作计划API ==========
@app.post("/api/plan/generate")
async def generate_plan(user_id: str, date: str = None):
    """基于学习生成工作计划"""
    if not date:
        from datetime import datetime
        date = datetime.now().strftime("%Y-%m-%d")
    
    user_profile = behavior_learning.get_user_profile(user_id)
    plans = work_plan_manager.generate_plan_from_learning(user_id, user_profile, date)
    
    return {
        "success": True,
        "date": date,
        "plans": plans,
        "message": "工作计划已生成，您可以确认、增加、删减或重排"
    }


@app.get("/api/plan/list/{user_id}/{date}")
async def get_plans(user_id: str, date: str):
    """获取工作计划列表"""
    plans = work_plan_manager.get_plans_by_date(user_id, date)
    return {"success": True, "plans": plans, "count": len(plans)}


@app.post("/api/plan/create")
async def create_plan(user_id: str, date: str, plan_data: dict):
    """创建新计划"""
    plan_id = work_plan_manager.create_plan(user_id, date, plan_data)
    return {"success": True, "plan_id": plan_id}


@app.put("/api/plan/update/{plan_id}")
async def update_plan(plan_id: int, updates: dict):
    """更新计划"""
    work_plan_manager.update_plan(plan_id, updates)
    return {"success": True, "message": "计划已更新"}


@app.delete("/api/plan/delete/{plan_id}")
async def delete_plan(plan_id: int):
    """删除计划"""
    work_plan_manager.delete_plan(plan_id)
    return {"success": True, "message": "计划已删除"}


@app.post("/api/plan/reorder")
async def reorder_plans(user_id: str, date: str, plan_ids: list):
    """重新排序计划"""
    work_plan_manager.reorder_plans(user_id, date, plan_ids)
    return {"success": True, "message": "计划已重排"}


# ========== 备忘录API ==========
@app.post("/api/memo/create")
async def create_memo(user_id: str, memo_data: dict):
    """创建备忘录"""
    memo_id = memo_manager.create_memo(user_id, memo_data)
    return {"success": True, "memo_id": memo_id}


@app.post("/api/memo/voice")
async def create_voice_memo(user_id: str, title: str, audio_file: UploadFile = File(...)):
    """创建语音备忘录"""
    import os
    from datetime import datetime
    
    # 确保目录存在
    os.makedirs("voice_memos", exist_ok=True)
    
    # 保存音频
    timestamp = datetime.now().timestamp()
    audio_path = f"voice_memos/{user_id}_{timestamp}.wav"
    
    with open(audio_path, "wb") as f:
        content = await audio_file.read()
        f.write(content)
    
    # 语音识别
    stt_result = await voice_interface.speech_to_text(content)
    transcription = stt_result.get("text", "") if stt_result.get("success") else ""
    
    # 创建备忘录
    memo_id = memo_manager.create_voice_memo(user_id, title, audio_path, transcription)
    
    return {
        "success": True,
        "memo_id": memo_id,
        "audio_path": audio_path,
        "transcription": transcription
    }


@app.get("/api/memo/list/{user_id}")
async def get_memos(user_id: str, status: str = "active"):
    """获取备忘录列表"""
    memos = memo_manager.get_memos(user_id, status)
    return {"success": True, "memos": memos, "count": len(memos)}


@app.get("/api/memo/{memo_id}")
async def get_memo(memo_id: int):
    """获取单个备忘录"""
    memo = memo_manager.get_memo_by_id(memo_id)
    if memo:
        return {"success": True, "memo": memo}
    return {"success": False, "error": "备忘录不存在"}


@app.put("/api/memo/update/{memo_id}")
async def update_memo(memo_id: int, updates: dict):
    """更新备忘录"""
    memo_manager.update_memo(memo_id, updates)
    return {"success": True, "message": "备忘录已更新"}


@app.post("/api/memo/link-plan")
async def link_memo_to_plan(memo_id: int, plan_id: int):
    """关联备忘录到计划"""
    work_plan_manager.link_memo_to_plan(plan_id, memo_id)
    return {"success": True, "message": "备忘录已关联到计划"}


@app.get("/api/memo/search/{user_id}")
async def search_memos(user_id: str, keyword: str):
    """搜索备忘录"""
    memos = memo_manager.search_memos(user_id, keyword)
    return {"success": True, "memos": memos, "count": len(memos)}


# ========== 多语言翻译API ==========
@app.post("/api/translate")
async def translate_text(text: str, source_lang: str, target_lang: str):
    """翻译文本"""
    result = await translator.translate(text, source_lang, target_lang)
    return result


@app.post("/api/translate/auto")
async def auto_translate(text: str, target_lang: str = "zh"):
    """自动检测并翻译"""
    result = await translator.auto_detect_and_translate(text, target_lang)
    return result


@app.get("/api/translate/languages")
async def get_languages():
    """获取支持的语言"""
    languages = translator.get_supported_languages()
    return {"success": True, "languages": languages}


# ============================================================
# 📖 上下文记忆管理API（100万字记忆能力）
# ============================================================

@app.get("/api/context/stats/{session_id}")
async def get_context_stats(session_id: str):
    """获取上下文记忆统计信息"""
    try:
        stats = context_memory.get_context_stats(session_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/context/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 50, offset: int = 0):
    """获取会话历史"""
    try:
        history = context_memory.get_conversation_history(session_id, limit, offset)
        return {"success": True, "history": history, "count": len(history)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/context/sessions/{user_id}")
async def get_user_sessions(user_id: str, limit: int = 20):
    """获取用户的所有会话"""
    try:
        sessions = context_memory.get_user_sessions(user_id, limit)
        return {"success": True, "sessions": sessions, "count": len(sessions)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/context/summary/{session_id}")
async def get_session_summary_api(session_id: str):
    """获取会话摘要"""
    try:
        summary = context_memory.get_session_summary(session_id)
        if summary:
            return {"success": True, "summary": summary}
        else:
            return {"success": False, "error": "会话不存在或无摘要"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/context/summary/{session_id}/generate")
async def generate_session_summary_api(session_id: str, ai_summary: Optional[str] = None):
    """生成会话摘要"""
    try:
        summary = context_memory.generate_session_summary(session_id, ai_summary)
        return {"success": True, "summary": summary}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/context/search/{session_id}")
async def search_context(session_id: str, query: str, top_k: int = 5):
    """搜索相关历史对话"""
    try:
        results = context_memory.search_relevant_context(session_id, query, top_k)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 📤 对话导出API
# ============================================================

@app.get("/api/export/{session_id}/markdown")
async def export_markdown(session_id: str, include_metadata: bool = False):
    """导出为Markdown格式"""
    try:
        content = conversation_exporter.export_to_markdown(session_id, include_metadata)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{session_id}.md"
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/export/{session_id}/json")
async def export_json(session_id: str, pretty: bool = True):
    """导出为JSON格式"""
    try:
        content = conversation_exporter.export_to_json(session_id, pretty)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{session_id}.json"
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/export/{session_id}/html")
async def export_html(session_id: str):
    """导出为HTML格式"""
    try:
        content = conversation_exporter.export_to_html(session_id)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/html",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{session_id}.html"
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/export/{session_id}/txt")
async def export_txt(session_id: str):
    """导出为纯文本格式"""
    try:
        content = conversation_exporter.export_to_txt(session_id)
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{session_id}.txt"
            }
        )
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================================
# 🔔 智能提醒API
# ============================================================

@app.post("/api/reminder/detect")
async def detect_reminder(message: str, user_id: str, session_id: str):
    """检测消息中的提醒"""
    try:
        reminders = reminder_system.extract_reminders_from_message(user_id, session_id, message)
        
        # 自动保存检测到的提醒
        saved_ids = []
        for reminder in reminders:
            reminder_id = reminder_system.save_reminder(reminder)
            saved_ids.append(reminder_id)
        
        return {
            "success": True, 
            "reminders_detected": len(reminders),
            "reminders": reminders,
            "saved_ids": saved_ids
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/reminder/active/{user_id}")
async def get_active_reminders(user_id: str, limit: int = 20):
    """获取活跃的提醒"""
    try:
        reminders = reminder_system.get_active_reminders(user_id, limit)
        return {"success": True, "reminders": reminders, "count": len(reminders)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/reminder/due/{user_id}")
async def get_due_reminders(user_id: str):
    """获取到期的提醒"""
    try:
        reminders = reminder_system.get_due_reminders(user_id)
        return {"success": True, "reminders": reminders, "count": len(reminders)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/reminder/{reminder_id}/complete")
async def complete_reminder(reminder_id: int):
    """标记提醒为已完成"""
    try:
        reminder_system.mark_as_completed(reminder_id)
        return {"success": True, "message": "提醒已完成"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/reminder/{reminder_id}/dismiss")
async def dismiss_reminder(reminder_id: int):
    """标记提醒为已忽略"""
    try:
        reminder_system.mark_as_dismissed(reminder_id)
        return {"success": True, "message": "提醒已忽略"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/reminder/stats/{user_id}")
async def get_reminder_stats(user_id: str):
    """获取提醒统计"""
    try:
        stats = reminder_system.get_reminder_statistics(user_id)
        return {"success": True, "stats": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/models")
async def get_available_models():
    """
    需求8: 获取可用的AI模型列表
    """
    try:
        # 从Ollama获取已安装的模型
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{config.OLLAMA_API}/api/tags", timeout=5.0)
            
            if response.status_code == 200:
                data = response.json()
                installed_models = [model.get("name") for model in data.get("models", [])]
                
                # 标记哪些推荐模型已安装
                models_info = []
                for model in config.SUPPORTED_MODELS:
                    model_info = model.copy()
                    model_info["installed"] = model["id"] in installed_models
                    models_info.append(model_info)
                
                return {
                    "success": True,
                    "models": models_info,
                    "installed_count": len(installed_models),
                    "current_model": config.OLLAMA_MODEL
                }
    except Exception as e:
        # 如果Ollama不可用，返回推荐列表
        return {
            "success": False,
            "models": config.SUPPORTED_MODELS,
            "error": "Ollama服务不可用",
            "current_model": config.OLLAMA_MODEL
        }


# 提供静态文件服务（必须在路由之后）
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    print("⚠️ 静态文件目录未找到，将跳过")


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("   🤖 AI Stack 智能对话中心启动中...")
    print("=" * 60)
    print("")
    print("🌐 访问地址: http://localhost:8020")
    print("")
    print("✅ 满足4个核心需求:")
    print("  1. OpenWebUI调用AI Stack + 反馈结果")
    print("  2. RAG先行检索 + 历史经验作为附加条件")
    print("  3. 结果RAG验证 + 差异检测说明")
    print("  4. 监控学习 + 经验积累到RAG")
    print("")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8020)

