"""
title: AI Stack Master Plugin
author: AI Stack Team
author_url: https://github.com/ai-stack
funding_url: https://github.com/sponsors/ai-stack
version: 1.0.0
license: MIT
required_open_webui_version: 0.3.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable
import httpx
import re
import json


class Plugin:
    class Valves(BaseModel):
        """配置项"""
        # 服务地址配置
        rag_api: str = Field(
            default="http://host.docker.internal:8011",
            description="RAG系统API地址"
        )
        erp_api: str = Field(
            default="http://host.docker.internal:8013",
            description="ERP系统API地址"
        )
        stock_api: str = Field(
            default="http://host.docker.internal:8014",
            description="股票系统API地址"
        )
        trend_api: str = Field(
            default="http://host.docker.internal:8015",
            description="趋势分析API地址"
        )
        content_api: str = Field(
            default="http://host.docker.internal:8016",
            description="内容创作API地址"
        )
        task_api: str = Field(
            default="http://host.docker.internal:8017",
            description="任务代理API地址"
        )
        resource_api: str = Field(
            default="http://host.docker.internal:8018",
            description="资源管理API地址"
        )
        learning_api: str = Field(
            default="http://host.docker.internal:8019",
            description="自我学习API地址"
        )
        
        # 功能开关
        enable_auto_rag: bool = Field(
            default=True,
            description="启用自动RAG增强（所有问题自动检索知识库）"
        )
        enable_smart_routing: bool = Field(
            default=True,
            description="启用智能路由（自动识别意图调用相应系统）"
        )
        enable_voice: bool = Field(
            default=True,
            description="启用语音触发"
        )

    def __init__(self):
        self.valves = self.Valves()
        
        # 关键词映射 - 用于智能路由
        self.keyword_map = {
            "rag": ["知识", "搜索", "查询知识", "文档", "知识库", "知识图谱"],
            "erp": ["财务", "订单", "客户", "生产", "库存", "仓库", "采购", "经营", "管理"],
            "stock": ["股票", "股价", "行情", "交易", "买入", "卖出", "持仓", "投资", "茅台", "平安"],
            "trend": ["趋势", "热点", "资讯", "新闻", "行业", "分析"],
            "content": ["创作", "内容", "文案", "发布", "素材", "写文章"],
            "task": ["任务", "代理", "执行", "调度"],
            "resource": ["资源", "性能", "CPU", "内存", "监控", "系统状态"],
            "learning": ["学习", "训练", "模型", "优化"]
        }

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> dict:
        """
        inlet过滤器 - 处理用户输入，在发送给AI前拦截处理
        这里实现聊天触发AI Stack功能
        """
        
        if not body.get("messages"):
            return body
        
        user_message = body["messages"][-1]["content"]
        
        # 发送处理状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "🔍 AI Stack智能分析中...", "done": False},
                }
            )
        
        # 1. 检查是否是直接命令
        if user_message.startswith("/"):
            result = await self.handle_command(user_message, __event_emitter__)
            if result:
                # 替换用户消息为处理结果
                body["messages"][-1]["content"] = result
                return body
        
        # 2. 智能路由 - 自动识别应该调用哪个系统
        if self.valves.enable_smart_routing:
            detected_system = self.detect_intent(user_message)
            
            if detected_system:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"🎯 检测到{detected_system}相关问题，正在查询...",
                                "done": False
                            },
                        }
                    )
                
                # 调用相应系统
                enhanced_content = await self.call_system(detected_system, user_message, __event_emitter__)
                
                if enhanced_content:
                    # 将系统返回的信息添加到上下文
                    body["messages"].insert(-1, {
                        "role": "system",
                        "content": f"【来自{detected_system}系统的信息】\n{enhanced_content}\n\n请基于以上信息回答用户问题。"
                    })
        
        # 3. 自动RAG增强 - 对所有问题检索知识库
        if self.valves.enable_auto_rag:
            rag_context = await self.auto_rag_search(user_message, __event_emitter__)
            
            if rag_context:
                # 注入RAG上下文
                body["messages"].insert(-1, {
                    "role": "system",
                    "content": f"【知识库检索结果】\n{rag_context}\n\n请参考以上知识库信息回答问题。"
                })
        
        # 清除状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "处理完成", "done": True},
                }
            )
        
        return body

    def detect_intent(self, message: str) -> Optional[str]:
        """检测用户意图，判断应该调用哪个系统"""
        # 计算每个系统的匹配分数
        scores = {}
        
        for system, keywords in self.keyword_map.items():
            score = 0
            for keyword in keywords:
                if keyword in message:
                    score += 1
            if score > 0:
                scores[system] = score
        
        # 返回得分最高的系统
        if scores:
            return max(scores, key=scores.get)
        
        return None

    async def handle_command(
        self, 
        command: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[str]:
        """处理直接命令"""
        
        # RAG命令
        if command.startswith("/rag"):
            query = command.replace("/rag", "").replace("search", "").strip()
            return await self.rag_search(query, event_emitter)
        
        # ERP命令
        elif command.startswith("/erp"):
            return await self.erp_query(command, event_emitter)
        
        # 股票命令
        elif command.startswith("/stock"):
            return await self.stock_query(command, event_emitter)
        
        # 系统状态
        elif command.startswith("/status"):
            return await self.system_status(event_emitter)
        
        # 帮助
        elif command.startswith("/help"):
            return self.show_help()
        
        return None

    async def auto_rag_search(
        self, 
        query: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[str]:
        """自动RAG检索"""
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
                        # 提取知识
                        context = ""
                        for r in results[:2]:
                            text = r.get("text", "")
                            source = r.get("metadata", {}).get("source", "")
                            context += f"- {text[:150]}... (来源: {source})\n"
                        
                        return context
        except:
            pass
        
        return None

    async def call_system(
        self, 
        system: str, 
        message: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[str]:
        """调用指定系统"""
        
        if system == "erp":
            return await self.auto_erp_query(message, event_emitter)
        elif system == "stock":
            return await self.auto_stock_query(message, event_emitter)
        elif system == "rag":
            return await self.rag_search(message, event_emitter)
        
        return None

    async def rag_search(
        self, 
        query: str, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """RAG搜索"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api}/rag/search",
                    params={"query": query, "top_k": 5},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    formatted = "📚 **RAG知识库搜索结果**\n\n"
                    for i, r in enumerate(results[:5], 1):
                        text = r.get("text", "")
                        score = r.get("score", 0)
                        formatted += f"{i}. (相关度{score:.2f}) {text[:200]}...\n\n"
                    
                    return formatted
                else:
                    return f"❌ RAG搜索失败: HTTP {response.status_code}"
        except Exception as e:
            return f"❌ RAG搜索错误: {str(e)}"

    async def erp_query(
        self, 
        command: str, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """ERP查询"""
        try:
            # 解析命令类型
            if "financial" in command or "财务" in command:
                endpoint = "/api/finance/dashboard"
            elif "order" in command or "订单" in command:
                endpoint = "/api/business/orders"
            else:
                endpoint = "/api/finance/summary"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api}{endpoint}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"💼 **ERP系统数据**\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)[:500]}\n```"
                else:
                    return f"❌ ERP查询失败: HTTP {response.status_code}"
        except Exception as e:
            return f"❌ ERP查询错误: {str(e)}"

    async def auto_erp_query(
        self, 
        message: str, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """自动ERP查询"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.erp_api}/api/finance/summary",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"ERP财务数据：收入 ¥{data.get('revenue', 0):,.0f}，支出 ¥{data.get('expenses', 0):,.0f}"
        except:
            pass
        
        return None

    async def stock_query(
        self, 
        command: str, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """股票查询"""
        try:
            # 提取股票代码
            code_match = re.search(r'\d{6}', command)
            code = code_match.group() if code_match else "600519"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api}/api/stock/price/{code}",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"📈 **{data.get('name')} ({code})**\n价格: ¥{data.get('price', 0):.2f}\n涨跌: {data.get('change_percent', 0):+.2f}%"
                else:
                    return f"❌ 股票查询失败: HTTP {response.status_code}"
        except Exception as e:
            return f"❌ 股票查询错误: {str(e)}"

    async def auto_stock_query(
        self, 
        message: str, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """自动股票查询"""
        # 提取可能的股票代码或名称
        code_match = re.search(r'\d{6}', message)
        if code_match:
            code = code_match.group()
        elif "茅台" in message:
            code = "600519"
        elif "平安" in message:
            code = "000001"
        else:
            return None
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.stock_api}/api/stock/price/{code}",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return f"股票信息：{data.get('name')} 当前价格 ¥{data.get('price', 0):.2f}"
        except:
            pass
        
        return None

    async def system_status(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> str:
        """系统状态检查"""
        try:
            services = {
                "RAG": self.valves.rag_api,
                "ERP": self.valves.erp_api,
                "Stock": self.valves.stock_api,
                "Trend": self.valves.trend_api,
                "Content": self.valves.content_api,
                "Task": self.valves.task_api,
                "Resource": self.valves.resource_api,
                "Learning": self.valves.learning_api,
            }
            
            result = "🏥 **AI Stack 系统状态**\n\n"
            running = 0
            
            async with httpx.AsyncClient() as client:
                for name, url in services.items():
                    try:
                        response = await client.get(f"{url}/health", timeout=3.0)
                        if response.status_code == 200:
                            result += f"✅ {name} - 运行中\n"
                            running += 1
                        else:
                            result += f"❌ {name} - 异常\n"
                    except:
                        result += f"❌ {name} - 未运行\n"
            
            result += f"\n**可用率**: {running}/{len(services)} ({running/len(services)*100:.0f}%)"
            
            return result
        except Exception as e:
            return f"❌ 状态检查错误: {str(e)}"

    def show_help(self) -> str:
        """显示帮助"""
        return """
🌟 **AI Stack Master Plugin - 使用帮助**

### 🎯 自动触发（直接提问）

**RAG知识库**:
- "什么是机器学习？" → 自动检索知识库
- "深度学习的原理" → 自动RAG增强

**ERP系统**:
- "今天的财务数据" → 自动查询ERP
- "订单情况" → 自动查询订单

**股票系统**:
- "贵州茅台价格" → 自动查询600519
- "平安银行行情" → 自动查询000001

### 📝 直接命令

- `/rag <关键词>` - RAG搜索
- `/erp financial` - ERP财务
- `/stock <代码>` - 股票查询
- `/status` - 系统状态
- `/help` - 显示帮助

### ✨ 特性

- ✅ 文字输入触发
- ✅ 语音输入触发
- ✅ 智能意图识别
- ✅ 自动RAG增强
- ✅ 实时状态反馈

---

💡 直接提问即可，AI Stack会自动响应！
"""



