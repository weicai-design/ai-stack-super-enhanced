"""
title: AI Stack Unified Interface
author: AI Stack Team
version: 1.0.0
description: Unified interface for all AI Stack systems with intelligent routing
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Dict, List
import httpx
import re


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        auto_routing: bool = Field(
            default=True,
            description="启用智能路由（自动识别用户意图）"
        )
        services: Dict[str, str] = Field(
            default={
                "rag": "http://host.docker.internal:8011",
                "erp": "http://host.docker.internal:8013",
                "stock": "http://host.docker.internal:8014",
                "trend": "http://host.docker.internal:8015",
                "content": "http://host.docker.internal:8016",
                "task": "http://host.docker.internal:8017",
                "resource": "http://host.docker.internal:8018",
                "learning": "http://host.docker.internal:8019",
            },
            description="所有AI Stack服务地址"
        )
    
    def __init__(self):
        self.valves = self.Valves()
        
        # 关键词映射
        self.keyword_mapping = {
            "rag": ["知识", "搜索", "文档", "知识库", "知识图谱"],
            "erp": ["财务", "订单", "客户", "生产", "库存", "仓库", "采购"],
            "stock": ["股票", "股价", "行情", "交易", "持仓", "买入", "卖出"],
            "trend": ["趋势", "热点", "资讯", "新闻", "行业"],
            "content": ["内容", "创作", "文案", "发布", "素材"],
            "task": ["任务", "代理", "执行", "调度"],
            "resource": ["资源", "性能", "CPU", "内存", "监控"],
            "learning": ["学习", "训练", "模型", "优化"],
        }
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> Optional[dict]:
        """
        统一接口动作
        
        支持的命令：
        - /aistack help - 查看帮助
        - /aistack status - 系统状态
        - /aistack <service> <action> - 调用指定服务
        
        自动路由：
        - 直接提问，自动识别应该调用哪个系统
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 帮助命令
        if user_message.startswith("/aistack help"):
            return self.show_help()
        
        # 状态命令
        if user_message.startswith("/aistack status"):
            return await self.check_status(__event_emitter__)
        
        # 智能路由
        if self.valves.auto_routing:
            return await self.intelligent_routing(user_message, __event_emitter__)
        
        return None
    
    def show_help(self) -> dict:
        """显示帮助信息"""
        help_text = """
🌟 **AI Stack 统一接口**

### 可用命令

**系统管理**:
- `/aistack status` - 查看所有系统状态
- `/aistack help` - 显示此帮助

**直接提问** (自动路由):
- "搜索AI技术" → RAG系统
- "今天的财务数据" → ERP系统
- "贵州茅台价格" → 股票系统
- "最新科技趋势" → 趋势分析
- "创作一篇文章" → 内容创作

### 专用Functions

如需更精确控制，使用专用Functions:
- RAG Knowledge Integration
- ERP Business Query
- Stock Trading & Analysis
- Content Creation & Publishing
- Terminal Command Executor
- System Monitor

### 访问系统界面

- ERP: http://localhost:8012
- RAG: http://localhost:8011
- 股票: http://localhost:8014
- 其他: http://localhost:8015-8019

---

💡 **提示**: 直接提问即可，AI Stack会自动识别并调用相应系统！
"""
        
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": help_text
                }
            ]
        }
    
    async def check_status(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """检查系统状态"""
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "正在检查系统状态...", "done": False},
                    }
                )
            
            # 并发检查所有服务
            tasks = []
            async with httpx.AsyncClient() as client:
                for name, url in self.valves.services.items():
                    tasks.append(self.ping_service(client, name, url))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 格式化结果
            formatted = "🏥 **AI Stack 系统状态**\n\n"
            
            running_count = 0
            total_count = len(results)
            
            for result in results:
                if isinstance(result, dict) and result.get("running"):
                    running_count += 1
                    formatted += f"✅ **{result['name']}** - 运行中 ({result.get('response_time', 0):.1f}ms)\n"
                elif isinstance(result, dict):
                    formatted += f"❌ **{result['name']}** - 未运行\n"
                else:
                    formatted += f"⚠️ 检查错误\n"
            
            formatted += f"\n**运行状态**: {running_count}/{total_count}\n"
            formatted += f"**可用率**: {(running_count/total_count*100):.1f}%\n"
            
            if running_count == total_count:
                formatted += "\n🎉 **所有系统运行正常！**"
            elif running_count > 0:
                formatted += "\n⚠️ **部分系统需要启动**"
            else:
                formatted += "\n❌ **系统未启动，请运行**: `./scripts/start_all_final.sh`"
            
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "状态检查完成", "done": True},
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
    
    async def ping_service(
        self, 
        client: httpx.AsyncClient, 
        name: str, 
        url: str
    ) -> dict:
        """Ping单个服务"""
        try:
            import time
            start = time.time()
            
            response = await client.get(
                f"{url}/health",
                timeout=self.valves.check_timeout
            )
            
            response_time = (time.time() - start) * 1000
            
            return {
                "name": name,
                "running": response.status_code == 200,
                "response_time": response_time
            }
        
        except Exception:
            return {
                "name": name,
                "running": False
            }
    
    async def health_check(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """详细健康检查"""
        return await self.check_status(event_emitter)
    
    async def get_performance(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """获取性能数据"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.services['resource']}/api/resources/stats",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = "📊 **系统性能**\n\n"
                    formatted += f"**CPU**: {data.get('cpu_usage', 0):.1f}%\n"
                    formatted += f"**内存**: {data.get('memory_usage', 0):.1f}%\n"
                    formatted += f"**磁盘**: {data.get('disk_usage', 0):.1f}%\n"
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted
                            }
                        ]
                    }
                else:
                    return self.error_response("无法获取性能数据")
        
        except Exception as e:
            return self.error_response(str(e))
    
    async def intelligent_routing(
        self, 
        user_message: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[dict]:
        """智能路由 - 自动识别应该调用哪个系统"""
        
        # 分析用户消息，识别关键词
        detected_services = []
        
        for service, keywords in self.keyword_mapping.items():
            for keyword in keywords:
                if keyword in user_message:
                    detected_services.append(service)
                    break
        
        # 如果检测到明确的服务意图
        if len(detected_services) == 1:
            service = detected_services[0]
            
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"路由到{service}系统...", "done": False},
                    }
                )
            
            # 根据服务类型调用相应API
            return await self.route_to_service(service, user_message, event_emitter)
        
        return None  # 无明确意图，继续正常对话
    
    async def route_to_service(
        self, 
        service: str, 
        message: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[dict]:
        """路由到指定服务"""
        
        # 这里可以调用具体的API
        # 简化版：返回提示信息
        
        service_info = {
            "rag": "知识库搜索",
            "erp": "ERP查询",
            "stock": "股票分析",
            "content": "内容创作",
        }
        
        return {
            "messages": [
                {
                    "role": "system",
                    "content": f"🔀 已路由到{service_info.get(service, service)}系统。使用专用Function可获得更好效果。"
                }
            ]
        }
    
    async def restart_service(
        self, 
        service: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """重启服务"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"⚠️ 服务重启功能需要管理员权限。\n\n请使用终端执行:\n```bash\n./scripts/restart_service.sh {service}\n```"
                }
            ]
        }
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ 系统错误: {error}"
                }
            ]
        }



