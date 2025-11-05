"""
title: Content Creation & Publishing
author: AI Stack Team
version: 1.0.0
description: AI-powered content creation and multi-platform publishing
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, List
import httpx
import json


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        content_api_endpoint: str = Field(
            default="http://localhost:8016",
            description="内容创作系统API端点"
        )
        enable_auto_publish: bool = Field(
            default=False,
            description="启用自动发布（谨慎开启）"
        )
        supported_platforms: List[str] = Field(
            default=["wechat", "weibo", "zhihu", "toutiao"],
            description="支持的发布平台"
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
        内容创作动作
        
        支持的命令：
        - /content create <topic> - AI创作内容
        - /content plan - 查看创作计划
        - /content publish <platform> - 发布内容
        - /content analyze - 爆款分析
        - /content materials <topic> - 收集素材
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 发送状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "正在处理内容创作请求...", "done": False},
                }
            )
        
        # 解析命令
        if user_message.startswith("/content create"):
            topic = user_message.replace("/content create", "").strip()
            return await self.create_content(topic, __event_emitter__)
        
        elif user_message.startswith("/content plan"):
            return await self.get_content_plan(__event_emitter__)
        
        elif user_message.startswith("/content publish"):
            parts = user_message.split()
            platform = parts[2] if len(parts) > 2 else "wechat"
            return await self.publish_content(platform, __event_emitter__)
        
        elif user_message.startswith("/content analyze"):
            return await self.analyze_hot_content(__event_emitter__)
        
        elif user_message.startswith("/content materials"):
            topic = user_message.replace("/content materials", "").strip()
            return await self.collect_materials(topic, __event_emitter__)
        
        return None
    
    async def create_content(
        self, 
        topic: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """AI创作内容"""
        if not topic:
            return self.error_response("请提供创作主题")
        
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"AI正在创作: {topic}", "done": False},
                    }
                )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.content_api_endpoint}/api/content/generate",
                    json={"topic": topic, "content_type": "article"},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    content = data.get("content", "")
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "内容创作完成", "done": True},
                            }
                        )
                    
                    formatted = f"✨ **AI创作完成**\n\n"
                    formatted += f"**主题**: {topic}\n"
                    formatted += f"**字数**: {len(content)}\n\n"
                    formatted += "---\n\n"
                    formatted += content[:500] + "...\n\n"
                    formatted += f"[查看完整内容](http://localhost:8016)"
                    
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
    
    async def get_content_plan(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查看创作计划"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.content_api_endpoint}/api/content/plan",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_content_plan(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "创作计划加载完成", "done": True},
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
    
    async def publish_content(
        self, 
        platform: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """发布内容到平台"""
        if not self.valves.enable_auto_publish:
            return self.error_response("自动发布功能未启用")
        
        if platform not in self.valves.supported_platforms:
            return self.error_response(f"不支持的平台: {platform}")
        
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"正在发布到{platform}...", "done": False},
                    }
                )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.content_api_endpoint}/api/content/publish",
                    json={"platform": platform},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = f"✅ **发布成功**\n\n"
                    formatted += f"**平台**: {platform}\n"
                    formatted += f"**链接**: {data.get('url', 'N/A')}\n"
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "发布完成", "done": True},
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
    
    async def analyze_hot_content(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """爆款内容分析"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.content_api_endpoint}/api/content/hot",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = self.format_hot_content(data)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "爆款分析完成", "done": True},
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
    
    async def collect_materials(
        self, 
        topic: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """收集素材"""
        if not topic:
            return self.error_response("请提供主题")
        
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"正在收集素材: {topic}", "done": False},
                    }
                )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.content_api_endpoint}/api/materials/collect",
                    json={"topic": topic},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    formatted = f"📦 **素材收集完成**\n\n"
                    formatted += f"**主题**: {topic}\n"
                    formatted += f"**收集数量**: {data.get('count', 0)}\n\n"
                    
                    materials = data.get("materials", [])
                    for mat in materials[:5]:
                        formatted += f"- {mat.get('title', 'N/A')} ({mat.get('source', 'N/A')})\n"
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "素材收集完成", "done": True},
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
    
    def format_content_plan(self, data: dict) -> str:
        """格式化创作计划"""
        plans = data.get("plans", [])
        
        formatted = "📅 **内容创作计划**\n\n"
        
        for plan in plans[:10]:
            status = "✅" if plan.get("status") == "completed" else "⏳"
            formatted += f"{status} {plan.get('date')}: {plan.get('topic')} → {plan.get('platform')}\n"
        
        return formatted
    
    def format_hot_content(self, data: dict) -> str:
        """格式化爆款内容"""
        hot_list = data.get("hot_content", [])
        
        formatted = "🔥 **爆款内容分析**\n\n"
        
        for item in hot_list[:5]:
            formatted += f"### {item.get('title')}\n"
            formatted += f"- 阅读: {item.get('views', 0):,}\n"
            formatted += f"- 点赞: {item.get('likes', 0):,}\n"
            formatted += f"- 互动率: {item.get('engagement', 0):.1f}%\n\n"
        
        return formatted
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ 内容创作错误: {error}"
                }
            ]
        }



