"""
title: AI Stack System Monitor
author: AI Stack Team
version: 1.0.0
description: Monitor all AI Stack systems status and performance
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Dict
import httpx
import asyncio


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        services: Dict[str, str] = Field(
            default={
                "RAG": "http://localhost:8011",
                "ERP": "http://localhost:8013",
                "Stock": "http://localhost:8014",
                "Trend": "http://localhost:8015",
                "Content": "http://localhost:8016",
                "Task": "http://localhost:8017",
                "Resource": "http://localhost:8018",
                "Learning": "http://localhost:8019",
            },
            description="所有服务地址"
        )
        check_timeout: int = Field(
            default=5,
            description="健康检查超时时间（秒）"
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
        系统监控动作
        
        支持的命令：
        - /system status - 所有系统状态
        - /system health - 健康检查
        - /system performance - 性能数据
        - /system restart <service> - 重启服务
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 解析命令
        if user_message.startswith("/system status"):
            return await self.check_all_services(__event_emitter__)
        
        elif user_message.startswith("/system health"):
            return await self.health_check(__event_emitter__)
        
        elif user_message.startswith("/system performance"):
            return await self.get_performance(__event_emitter__)
        
        elif user_message.startswith("/system restart"):
            service = user_message.replace("/system restart", "").strip()
            return await self.restart_service(service, __event_emitter__)
        
        return None
    
    async def check_all_services(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """检查所有服务状态"""
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "正在检查所有服务...", "done": False},
                    }
                )
            
            # 并发检查所有服务
            tasks = []
            async with httpx.AsyncClient() as client:
                for name, url in self.valves.services.items():
                    tasks.append(self.check_service(client, name, url))
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 格式化结果
            formatted = "🏥 **系统状态检查**\n\n"
            
            running = 0
            total = len(results)
            
            for result in results:
                if isinstance(result, dict):
                    status_icon = "✅" if result["running"] else "❌"
                    response_time = f" ({result['response_time']:.1f}ms)" if result.get('response_time') else ""
                    formatted += f"{status_icon} **{result['name']}**{response_time}\n"
                    if result["running"]:
                        running += 1
                else:
                    formatted += f"❌ 检查错误: {str(result)}\n"
            
            formatted += f"\n**运行中**: {running}/{total}\n"
            formatted += f"**可用率**: {(running/total*100):.1f}%\n"
            
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "系统检查完成", "done": True},
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
    
    async def check_service(
        self, 
        client: httpx.AsyncClient, 
        name: str, 
        url: str
    ) -> dict:
        """检查单个服务"""
        try:
            import time
            start = time.time()
            
            response = await client.get(
                f"{url}/health",
                timeout=self.valves.check_timeout
            )
            
            response_time = (time.time() - start) * 1000  # ms
            
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
        # 调用系统健康检查脚本
        try:
            result = subprocess.run(
                ["python3", "scripts/system_health_check.py"],
                cwd="/Users/ywc/ai-stack-super-enhanced",
                capture_output=True,
                text=True,
                timeout=30
            )
            
            formatted = "🏥 **系统健康检查**\n\n"
            formatted += "```\n"
            formatted += result.stdout[:1500]
            formatted += "\n```"
            
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "健康检查完成", "done": True},
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
    
    async def get_performance(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """获取性能数据"""
        try:
            # 调用资源管理API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "http://localhost:8018/api/resources/stats",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = "📊 **系统性能数据**\n\n"
                    formatted += f"**CPU使用率**: {data.get('cpu_usage', 0):.1f}%\n"
                    formatted += f"**内存使用率**: {data.get('memory_usage', 0):.1f}%\n"
                    formatted += f"**磁盘使用率**: {data.get('disk_usage', 0):.1f}%\n"
                    formatted += f"**网络速度**: {data.get('network_speed', 'N/A')}\n"
                    
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
                    "content": f"⚠️ 服务重启功能暂未实现。请使用终端命令手动重启 {service}。"
                }
            ]
        }
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ 系统监控错误: {error}"
                }
            ]
        }



