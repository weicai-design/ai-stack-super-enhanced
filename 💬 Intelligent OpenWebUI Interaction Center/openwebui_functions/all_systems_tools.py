"""
OpenWebUI Functions - AI Stack 所有系统统一工具集
用户可以在OpenWebUI聊天中通过自然语言操作所有9大系统

根据需求5.3：聊天窗口与所有功能关联调用
"""

import requests
import json
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class Tools:
    """AI Stack 统一工具集"""
    
    def __init__(self):
        self.valves = self.Valves()
    
    class Valves(BaseModel):
        """配置参数"""
        RAG_API: str = Field(default="http://host.docker.internal:8011", description="RAG API地址")
        ERP_API: str = Field(default="http://host.docker.internal:8013", description="ERP API地址")
        STOCK_API: str = Field(default="http://host.docker.internal:8014", description="股票API地址")
        TREND_API: str = Field(default="http://host.docker.internal:8015", description="趋势分析API地址")
        CONTENT_API: str = Field(default="http://host.docker.internal:8016", description="内容创作API地址")
        TASK_API: str = Field(default="http://host.docker.internal:8017", description="任务代理API地址")
        RESOURCE_API: str = Field(default="http://host.docker.internal:8018", description="资源管理API地址")
        LEARNING_API: str = Field(default="http://host.docker.internal:8019", description="自我学习API地址")
    
    # ==================== RAG 知识库功能 ====================
    
    async def search_rag(
        self,
        query: str,
        top_k: int = 5,
        __user__: dict = {}
    ) -> str:
        """
        搜索RAG知识库
        
        示例: "搜索知识库中关于Python的内容"
        """
        try:
            response = requests.get(
                f"{self.valves.RAG_API}/rag/search",
                params={"query": query, "top_k": top_k},
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json().get("results", [])
                if not results:
                    return "📭 未找到相关知识"
                
                formatted = f"🔍 找到 {len(results)} 条知识：\n\n"
                for i, r in enumerate(results, 1):
                    formatted += f"{i}. {r.get('content', '')[:150]}...\n"
                return formatted
            else:
                return "❌ 搜索失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== ERP 企业管理功能 ====================
    
    async def get_erp_financial_dashboard(
        self,
        period_type: str = "monthly",
        __user__: dict = {}
    ) -> str:
        """
        查看ERP财务看板
        
        示例: "查看本月财务情况"
        参数: period_type可以是 daily, weekly, monthly, quarterly, yearly
        """
        try:
            response = requests.get(
                f"{self.valves.ERP_API}/api/finance/dashboard",
                params={"period_type": period_type},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get("summary", {})
                
                formatted = f"📊 **{period_type.upper()} 财务看板**\n\n"
                formatted += f"💰 总收入: ¥{summary.get('total_income', 0):,.2f}\n"
                formatted += f"💸 总支出: ¥{summary.get('total_expense', 0):,.2f}\n"
                formatted += f"📈 利润: ¥{summary.get('profit', 0):,.2f}\n"
                formatted += f"📊 利润率: {summary.get('profit_margin', 0):.1f}%\n"
                
                return formatted
            else:
                return "❌ 获取财务数据失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_erp_customer_list(
        self,
        limit: int = 10,
        __user__: dict = {}
    ) -> str:
        """
        查看ERP客户列表
        
        示例: "查看客户列表"
        """
        try:
            response = requests.get(
                f"{self.valves.ERP_API}/api/business/customers",
                params={"limit": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                customers = data.get("customers", [])
                
                formatted = f"👥 **客户列表** (共{len(customers)}个)\n\n"
                for i, c in enumerate(customers, 1):
                    formatted += f"{i}. **{c.get('name', '未知')}**\n"
                    formatted += f"   类型: {c.get('category', '未知')} | "
                    formatted += f"级别: {c.get('level', '普通')}\n"
                
                return formatted
            else:
                return "❌ 获取客户列表失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_erp_order_status(
        self,
        order_id: Optional[str] = None,
        __user__: dict = {}
    ) -> str:
        """
        查看订单状态
        
        示例: "查看订单 ORD001 的状态"
        """
        try:
            if order_id:
                url = f"{self.valves.ERP_API}/api/business/orders/{order_id}"
            else:
                url = f"{self.valves.ERP_API}/api/business/orders"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if order_id:
                    order = data.get("order", {})
                    formatted = f"📦 **订单 {order_id}**\n\n"
                    formatted += f"客户: {order.get('customer_name', '未知')}\n"
                    formatted += f"产品: {order.get('product_name', '未知')}\n"
                    formatted += f"数量: {order.get('quantity', 0)}\n"
                    formatted += f"金额: ¥{order.get('amount', 0):,.2f}\n"
                    formatted += f"状态: {order.get('status', '未知')}\n"
                else:
                    orders = data.get("orders", [])
                    formatted = f"📦 **订单列表** (共{len(orders)}个)\n\n"
                    for o in orders[:10]:
                        formatted += f"• {o.get('order_no', '')} - {o.get('status', '')}\n"
                
                return formatted
            else:
                return "❌ 获取订单失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 股票交易功能 ====================
    
    async def get_stock_quote(
        self,
        symbol: str,
        __user__: dict = {}
    ) -> str:
        """
        获取股票行情
        
        示例: "查看AAPL的股票价格"
        """
        try:
            response = requests.get(
                f"{self.valves.STOCK_API}/api/stock/quote/{symbol}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json().get("quote", {})
                
                formatted = f"📈 **{symbol} 股票行情**\n\n"
                formatted += f"💵 当前价: ${data.get('price', 0):.2f}\n"
                formatted += f"📊 涨跌: {data.get('change', 0):+.2f} ({data.get('change_percent', 0):+.2f}%)\n"
                formatted += f"📈 最高: ${data.get('high', 0):.2f}\n"
                formatted += f"📉 最低: ${data.get('low', 0):.2f}\n"
                formatted += f"📊 成交量: {data.get('volume', 0):,}\n"
                
                return formatted
            else:
                return f"❌ 无法获取 {symbol} 的行情"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def analyze_stock_strategy(
        self,
        symbol: str,
        strategy: str = "trend_following",
        __user__: dict = {}
    ) -> str:
        """
        分析股票交易策略
        
        示例: "用趋势跟踪策略分析AAPL"
        策略: trend_following, mean_reversion, momentum
        """
        try:
            response = requests.post(
                f"{self.valves.STOCK_API}/api/strategy/analyze",
                json={"symbol": symbol, "strategy": strategy},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json().get("analysis", {})
                
                formatted = f"📊 **{symbol} - {strategy} 策略分析**\n\n"
                formatted += f"信号: {result.get('signal', '无')}\n"
                formatted += f"置信度: {result.get('confidence', 0):.1%}\n"
                formatted += f"建议: {result.get('recommendation', '观望')}\n"
                formatted += f"理由: {result.get('reason', '暂无')}\n"
                
                return formatted
            else:
                return "❌ 策略分析失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 趋势分析功能 ====================
    
    async def start_news_crawl(
        self,
        category: str = "technology",
        max_items: int = 20,
        __user__: dict = {}
    ) -> str:
        """
        启动新闻爬取
        
        示例: "爬取最新的科技新闻"
        类别: technology, finance, politics, sports
        """
        try:
            response = requests.post(
                f"{self.valves.TREND_API}/api/crawl/news",
                json={"category": category, "max_items": max_items},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                formatted = f"📰 **新闻爬取已启动**\n\n"
                formatted += f"类别: {category}\n"
                formatted += f"目标数量: {max_items}\n"
                formatted += f"任务ID: {result.get('task_id', 'unknown')}\n"
                formatted += f"预计完成: {result.get('estimated_time', '未知')}\n"
                
                return formatted
            else:
                return "❌ 启动爬取失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_trend_report(
        self,
        topic: str,
        __user__: dict = {}
    ) -> str:
        """
        获取趋势分析报告
        
        示例: "生成AI行业的趋势分析报告"
        """
        try:
            response = requests.post(
                f"{self.valves.TREND_API}/api/analyze/generate-report",
                json={"topic": topic},
                timeout=30
            )
            
            if response.status_code == 200:
                report = response.json().get("report", {})
                
                formatted = f"📊 **{topic} 趋势分析报告**\n\n"
                formatted += f"**热度指数**: {report.get('热度', 0)}/100\n"
                formatted += f"**情感倾向**: {report.get('情感', '中性')}\n"
                formatted += f"**趋势方向**: {report.get('趋势', '稳定')}\n\n"
                formatted += f"**关键发现**:\n{report.get('summary', '正在分析...')}\n"
                
                return formatted
            else:
                return "❌ 生成报告失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 内容创作功能 ====================
    
    async def generate_content(
        self,
        topic: str,
        content_type: str = "article",
        platform: str = "xiaohongshu",
        __user__: dict = {}
    ) -> str:
        """
        生成内容
        
        示例: "生成一篇关于AI技术的小红书文章"
        类型: article, video_script, short_post
        平台: xiaohongshu, douyin, zhihu, toutiao
        """
        try:
            response = requests.post(
                f"{self.valves.CONTENT_API}/api/content/generate",
                json={
                    "topic": topic,
                    "type": content_type,
                    "platform": platform
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("content", "")
                
                formatted = f"✍️ **{platform} - {content_type}**\n\n"
                formatted += f"主题: {topic}\n"
                formatted += f"字数: {result.get('word_count', 0)}\n\n"
                formatted += f"**生成内容**:\n{content[:500]}...\n\n"
                formatted += f"_已去AI化处理，原创度: {result.get('uniqueness', 0):.1%}_"
                
                return formatted
            else:
                return "❌ 内容生成失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def collect_materials(
        self,
        platform: str,
        topic: str,
        count: int = 10,
        __user__: dict = {}
    ) -> str:
        """
        收集创作素材
        
        示例: "从小红书收集关于旅游的素材"
        """
        try:
            response = requests.post(
                f"{self.valves.CONTENT_API}/api/materials/collect",
                json={
                    "platform": platform,
                    "topic": topic,
                    "count": count
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                materials = result.get("materials", [])
                
                formatted = f"📦 **素材收集完成**\n\n"
                formatted += f"平台: {platform}\n"
                formatted += f"主题: {topic}\n"
                formatted += f"收集数量: {len(materials)}\n\n"
                formatted += "**热门素材**:\n"
                
                for m in materials[:5]:
                    formatted += f"• {m.get('title', '未知')} (👍 {m.get('likes', 0)})\n"
                
                return formatted
            else:
                return "❌ 素材收集失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 任务代理功能 ====================
    
    async def create_task(
        self,
        task_name: str,
        task_type: str,
        description: str = "",
        __user__: dict = {}
    ) -> str:
        """
        创建任务
        
        示例: "创建一个每日数据采集任务"
        类型: data_collection, data_analysis, content_generation, monitoring
        """
        try:
            response = requests.post(
                f"{self.valves.TASK_API}/api/tasks/create",
                json={
                    "name": task_name,
                    "description": description,
                    "task_type": task_type,
                    "priority": 5
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                task = result.get("task", {})
                
                formatted = f"✅ **任务创建成功**\n\n"
                formatted += f"任务ID: {task.get('id', 'unknown')}\n"
                formatted += f"名称: {task_name}\n"
                formatted += f"类型: {task_type}\n"
                formatted += f"状态: {task.get('status', 'pending')}\n"
                formatted += f"预计步骤: {len(task.get('execution_plan', {}).get('steps', []))}\n"
                
                return formatted
            else:
                return "❌ 任务创建失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def execute_task(
        self,
        task_id: int,
        __user__: dict = {}
    ) -> str:
        """
        执行任务
        
        示例: "执行任务1"
        """
        try:
            response = requests.post(
                f"{self.valves.TASK_API}/api/tasks/{task_id}/execute",
                timeout=10
            )
            
            if response.status_code == 200:
                return f"✅ 任务 {task_id} 已提交执行，请稍后查看进度"
            else:
                return f"❌ 任务执行失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_running_tasks(
        self,
        __user__: dict = {}
    ) -> str:
        """
        查看运行中的任务
        
        示例: "查看正在运行的任务"
        """
        try:
            response = requests.get(
                f"{self.valves.TASK_API}/api/tasks/monitoring/active",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                tasks = data.get("tasks", [])
                
                if not tasks:
                    return "📭 当前没有运行中的任务"
                
                formatted = f"⚙️ **运行中的任务** (共{len(tasks)}个)\n\n"
                for t in tasks:
                    formatted += f"• **{t.get('task_name', '未知')}**\n"
                    formatted += f"  进度: {t.get('progress', 0):.0f}% | "
                    formatted += f"当前步骤: {t.get('current_step', '未知')}\n"
                
                return formatted
            else:
                return "❌ 获取任务列表失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 资源管理功能 ====================
    
    async def get_system_resources(
        self,
        __user__: dict = {}
    ) -> str:
        """
        查看系统资源使用情况
        
        示例: "查看系统资源使用情况"
        """
        try:
            response = requests.get(
                f"{self.valves.RESOURCE_API}/api/resources/system",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                resources = data.get("resources", {})
                status = data.get("status", {})
                
                cpu = resources.get("cpu", {})
                memory = resources.get("memory", {})
                
                formatted = f"⚙️ **系统资源状态**\n\n"
                formatted += f"🖥️ CPU: {cpu.get('total_percent', 0):.1f}%\n"
                formatted += f"🧠 内存: {memory.get('used_gb', 0):.1f}GB / {memory.get('total_gb', 32):.1f}GB "
                formatted += f"({memory.get('percent', 0):.1f}%)\n"
                formatted += f"💾 磁盘: {len(resources.get('disk', []))}个\n\n"
                formatted += f"**状态**: {status.get('overall', 'unknown')}\n"
                
                if status.get('warnings'):
                    formatted += f"\n⚠️ 警告:\n"
                    for w in status.get('warnings', [])[:3]:
                        formatted += f"  • {w}\n"
                
                return formatted
            else:
                return "❌ 获取资源信息失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def detect_resource_conflicts(
        self,
        services: List[str],
        __user__: dict = {}
    ) -> str:
        """
        检测资源冲突
        
        示例: "检测系统资源冲突"
        """
        try:
            params = "&".join([f"services={s}" for s in services])
            response = requests.get(
                f"{self.valves.RESOURCE_API}/api/resources/conflicts/detect?{params}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                conflicts = data.get("conflicts", {})
                
                if not conflicts.get("has_conflict"):
                    return "✅ 当前系统资源正常，无冲突"
                
                formatted = f"⚠️ **检测到资源冲突**\n\n"
                formatted += f"严重程度: {conflicts.get('severity', 'unknown')}\n"
                formatted += f"冲突类型: {', '.join(conflicts.get('conflict_type', []))}\n\n"
                formatted += f"受影响服务: {len(conflicts.get('affected_services', []))}个\n"
                
                return formatted
            else:
                return "❌ 冲突检测失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_services_status(
        self,
        __user__: dict = {}
    ) -> str:
        """
        查看所有服务状态
        
        示例: "查看所有服务运行状态"
        """
        try:
            response = requests.get(
                f"{self.valves.RESOURCE_API}/api/resources/startup/status",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                services = data.get("services", [])
                
                running = sum(1 for s in services if s.get("running"))
                
                formatted = f"🌐 **服务状态** ({running}/{len(services)} 运行中)\n\n"
                
                for s in services:
                    status_icon = "✅" if s.get("running") else "❌"
                    formatted += f"{status_icon} {s.get('service', 'unknown')}\n"
                
                return formatted
            else:
                return "❌ 获取服务状态失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 自我学习功能 ====================
    
    async def get_system_analysis(
        self,
        __user__: dict = {}
    ) -> str:
        """
        获取系统自我分析
        
        示例: "系统运行情况如何？"
        """
        try:
            response = requests.get(
                f"{self.valves.LEARNING_API}/api/learning/analyze/all",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                analysis = data.get("analysis", {})
                overall = analysis.get("overall", {})
                
                formatted = f"🧠 **系统自我分析**\n\n"
                formatted += f"总功能数: {overall.get('total_functions', 0)}\n"
                formatted += f"总使用次数: {overall.get('total_usage', 0)}\n"
                formatted += f"整体成功率: {overall.get('overall_success_rate', 0):.1%}\n"
                formatted += f"已分析模块: {overall.get('modules_analyzed', 0)}个\n"
                
                return formatted
            else:
                return "❌ 获取分析失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    async def get_optimization_suggestions(
        self,
        __user__: dict = {}
    ) -> str:
        """
        获取优化建议
        
        示例: "给我一些系统优化建议"
        """
        try:
            response = requests.get(
                f"{self.valves.LEARNING_API}/api/learning/suggestions/system",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                suggestions = data.get("suggestions", [])
                
                if not suggestions:
                    return "✅ 系统运行良好，暂无优化建议"
                
                formatted = f"💡 **系统优化建议** (共{len(suggestions)}条)\n\n"
                
                for i, s in enumerate(suggestions[:5], 1):
                    formatted += f"{i}. **{s.get('title', '未知')}**\n"
                    formatted += f"   {s.get('description', '')}\n"
                    formatted += f"   优先级: {s.get('priority', 'medium')}\n\n"
                
                return formatted
            else:
                return "❌ 获取建议失败"
        except Exception as e:
            return f"❌ 错误: {str(e)}"
    
    # ==================== 统一控制功能 ====================
    
    async def get_all_systems_status(
        self,
        __user__: dict = {}
    ) -> str:
        """
        查看所有系统状态（总览）
        
        示例: "查看整个AI Stack的运行状态"
        """
        systems = [
            ("RAG", self.valves.RAG_API),
            ("ERP", self.valves.ERP_API),
            ("股票", self.valves.STOCK_API),
            ("趋势", self.valves.TREND_API),
            ("内容", self.valves.CONTENT_API),
            ("任务", self.valves.TASK_API),
            ("资源", self.valves.RESOURCE_API),
            ("学习", self.valves.LEARNING_API)
        ]
        
        formatted = "🌐 **AI Stack 系统状态**\n\n"
        online_count = 0
        
        for name, api_url in systems:
            try:
                response = requests.get(f"{api_url}/health", timeout=2)
                if response.status_code == 200:
                    formatted += f"✅ {name}系统 - 运行中\n"
                    online_count += 1
                else:
                    formatted += f"❌ {name}系统 - 异常\n"
            except:
                formatted += f"⭕ {name}系统 - 离线\n"
        
        formatted += f"\n**总计**: {online_count}/{len(systems)} 系统在线"
        
        return formatted
    
    async def help_commands(
        self,
        __user__: dict = {}
    ) -> str:
        """
        显示所有可用命令
        
        示例: "有哪些功能可以使用？"
        """
        return """
🎯 **AI Stack 可用功能清单**

📚 **RAG知识库**
• "搜索知识库..." - 搜索知识
• "保存到知识库..." - 保存文本
• "查看知识库统计" - 统计信息
• "查询知识图谱..." - 图谱查询

💼 **ERP企业管理**
• "查看财务情况" - 财务看板
• "查看客户列表" - 客户管理
• "查看订单状态" - 订单查询

📈 **股票交易**
• "查看AAPL股票价格" - 获取行情
• "分析AAPL的交易策略" - 策略分析

🔍 **趋势分析**
• "爬取科技新闻" - 启动爬虫
• "生成AI行业趋势报告" - 分析报告

✍️ **内容创作**
• "生成关于...的文章" - 内容生成
• "从小红书收集素材" - 素材收集

🤖 **任务管理**
• "创建数据采集任务" - 创建任务
• "查看运行中的任务" - 任务状态
• "执行任务1" - 执行任务

⚙️ **资源管理**
• "查看系统资源" - 资源监控
• "检测资源冲突" - 冲突检测
• "查看服务状态" - 服务监控

🧠 **系统分析**
• "系统运行情况" - 自我分析
• "系统优化建议" - 优化建议

🌐 **总览**
• "查看所有系统状态" - 系统总览
• "帮助" - 显示本列表

💡 **提示**: 直接用自然语言描述你的需求即可！
        """


