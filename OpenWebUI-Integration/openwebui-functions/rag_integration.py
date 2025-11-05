"""
title: RAG Knowledge Integration
author: AI Stack Team
version: 1.0.0
description: Deep integration with AI Stack RAG and Knowledge Graph system
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any
import httpx
import json


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        rag_api_endpoint: str = Field(
            default="http://localhost:8011",
            description="RAG系统API端点"
        )
        rag_api_key: Optional[str] = Field(
            default=None,
            description="RAG API密钥（如需要）"
        )
        search_top_k: int = Field(
            default=5,
            description="搜索返回结果数量"
        )
        enable_kg_query: bool = Field(
            default=True,
            description="启用知识图谱查询"
        )
    
    def __init__(self):
        self.valves = self.Valves()
        self.citation = True  # 启用引用
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> Optional[dict]:
        """
        RAG集成动作
        
        支持的命令：
        - /rag search <query> - 搜索知识库
        - /rag ingest <file_path> - 摄入文档
        - /kg query <entity> - 查询知识图谱
        - /kg visualize - 知识图谱可视化
        """
        
        user_message = body["messages"][-1]["content"]
        
        # 发送状态
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "正在处理RAG请求...", "done": False},
                }
            )
        
        # 解析命令
        if user_message.startswith("/rag search"):
            query = user_message.replace("/rag search", "").strip()
            return await self.search_knowledge(query, __event_emitter__)
        
        elif user_message.startswith("/rag ingest"):
            file_path = user_message.replace("/rag ingest", "").strip()
            return await self.ingest_document(file_path, __event_emitter__)
        
        elif user_message.startswith("/kg query"):
            entity = user_message.replace("/kg query", "").strip()
            return await self.query_knowledge_graph(entity, __event_emitter__)
        
        elif user_message.startswith("/kg visualize"):
            return await self.get_kg_visualization(__event_emitter__)
        
        # 自动RAG增强
        else:
            return await self.auto_rag_enhancement(user_message, __event_emitter__)
    
    async def search_knowledge(
        self, 
        query: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """搜索知识库"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api_endpoint}/rag/search",
                    params={"query": query, "top_k": self.valves.search_top_k},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    # 格式化结果
                    formatted_results = self.format_search_results(results)
                    
                    if event_emitter:
                        await event_emitter__(
                            {
                                "type": "status",
                                "data": {"description": "RAG搜索完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted_results
                            }
                        ]
                    }
                else:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"❌ RAG搜索失败: HTTP {response.status_code}"
                            }
                        ]
                    }
        
        except Exception as e:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"❌ RAG搜索错误: {str(e)}"
                    }
                ]
            }
    
    async def ingest_document(
        self, 
        file_path: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """摄入文档到RAG"""
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"正在摄入文档: {file_path}", "done": False},
                    }
                )
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.valves.rag_api_endpoint}/rag/ingest",
                    json={"path": file_path, "save_index": True},
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "文档摄入完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"✅ 文档已成功摄入RAG库\n\n**文档ID**: {result.get('doc_id', 'N/A')}\n**分块数**: {result.get('num_chunks', 0)}"
                            }
                        ]
                    }
                else:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"❌ 文档摄入失败: HTTP {response.status_code}"
                            }
                        ]
                    }
        
        except Exception as e:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"❌ 文档摄入错误: {str(e)}"
                    }
                ]
            }
    
    async def query_knowledge_graph(
        self, 
        entity: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """查询知识图谱"""
        if not self.valves.enable_kg_query:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "⚠️ 知识图谱查询功能未启用"
                    }
                ]
            }
        
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"查询知识图谱: {entity}", "done": False},
                    }
                )
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api_endpoint}/kg/query",
                    params={"query": entity, "query_type": "entity"},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # 格式化知识图谱结果
                    formatted_kg = self.format_kg_results(result)
                    
                    if event_emitter:
                        await event_emitter(
                            {
                                "type": "status",
                                "data": {"description": "知识图谱查询完成", "done": True},
                            }
                        )
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": formatted_kg
                            }
                        ]
                    }
                else:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"❌ 知识图谱查询失败: HTTP {response.status_code}"
                            }
                        ]
                    }
        
        except Exception as e:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"❌ 知识图谱查询错误: {str(e)}"
                    }
                ]
            }
    
    async def get_kg_visualization(
        self, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """获取知识图谱可视化"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api_endpoint}/kg/snapshot",
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    kg_data = response.json()
                    
                    # 生成可视化HTML
                    viz_html = self.generate_kg_visualization_html(kg_data)
                    
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"📊 知识图谱可视化\n\n**节点数**: {len(kg_data.get('nodes', {}))}\n**边数**: {len(kg_data.get('edges', {}))}\n\n[查看完整可视化](http://localhost:8011/kg/visualize)"
                            }
                        ]
                    }
                else:
                    return {
                        "messages": [
                            {
                                "role": "assistant",
                                "content": f"❌ 知识图谱可视化失败: HTTP {response.status_code}"
                            }
                        ]
                    }
        
        except Exception as e:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"❌ 知识图谱可视化错误: {str(e)}"
                    }
                ]
            }
    
    async def auto_rag_enhancement(
        self, 
        user_message: str, 
        event_emitter: Optional[Callable] = None
    ) -> Optional[dict]:
        """自动RAG增强 - 对用户问题自动检索知识库"""
        try:
            # 自动搜索相关知识
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.valves.rag_api_endpoint}/rag/search",
                    params={"query": user_message, "top_k": 3},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    results = response.json()
                    
                    if results and len(results) > 0:
                        # 提取相关上下文
                        context = "\n\n".join([
                            f"[来源: {r.get('metadata', {}).get('source', 'unknown')}]\n{r.get('text', '')[:200]}..."
                            for r in results[:3]
                        ])
                        
                        # 将上下文注入到对话中
                        return {
                            "messages": [
                                {
                                    "role": "system",
                                    "content": f"以下是从知识库检索到的相关信息：\n\n{context}\n\n请基于这些信息回答用户问题。"
                                }
                            ]
                        }
            
            return None  # 没有找到相关知识，继续正常对话
        
        except Exception as e:
            # 静默失败，不影响正常对话
            return None
    
    def format_search_results(self, results: list) -> str:
        """格式化搜索结果"""
        if not results:
            return "🔍 未找到相关知识"
        
        formatted = "🔍 **RAG搜索结果**\n\n"
        
        for i, result in enumerate(results[:self.valves.search_top_k], 1):
            text = result.get("text", "")
            score = result.get("score", 0.0)
            metadata = result.get("metadata", {})
            source = metadata.get("source", "unknown")
            
            formatted += f"### 结果 {i} (相似度: {score:.3f})\n"
            formatted += f"**来源**: {source}\n\n"
            formatted += f"{text[:300]}...\n\n"
            formatted += "---\n\n"
        
        return formatted
    
    def format_kg_results(self, kg_result: dict) -> str:
        """格式化知识图谱结果"""
        if not kg_result or not kg_result.get("entities"):
            return "🌐 未找到相关实体"
        
        formatted = "🌐 **知识图谱查询结果**\n\n"
        
        entities = kg_result.get("entities", [])
        relations = kg_result.get("relations", [])
        
        formatted += f"**找到实体**: {len(entities)} 个\n\n"
        
        for entity in entities[:5]:
            formatted += f"- **{entity.get('value')}** ({entity.get('type')})\n"
        
        if relations:
            formatted += f"\n**关联关系**: {len(relations)} 个\n\n"
            for rel in relations[:5]:
                formatted += f"- {rel.get('source')} → {rel.get('type')} → {rel.get('target')}\n"
        
        return formatted
    
    def generate_kg_visualization_html(self, kg_data: dict) -> str:
        """生成知识图谱可视化HTML"""
        # 简化版，返回链接
        return f"<a href='http://localhost:8011/kg/visualize' target='_blank'>点击查看知识图谱可视化</a>"



