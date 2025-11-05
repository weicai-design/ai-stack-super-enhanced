"""
OpenWebUI Functions - RAG知识库工具
这些函数会在OpenWebUI聊天界面中作为工具使用
用户可以直接在聊天中调用RAG的所有功能
"""

import requests
import json
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class Tools:
    """OpenWebUI工具类 - RAG操作"""
    
    def __init__(self):
        self.valves = self.Valves()
    
    class Valves(BaseModel):
        """配置参数"""
        RAG_API_URL: str = Field(
            default="http://localhost:8011",
            description="RAG API地址"
        )
        RAG_API_KEY: str = Field(
            default="",
            description="RAG API密钥（如果需要）"
        )
    
    async def search_knowledge(
        self,
        query: str,
        top_k: int = 5,
        __user__: dict = {}
    ) -> str:
        """
        搜索知识库
        
        在OpenWebUI聊天中使用：
        "搜索知识库关于Python的内容"
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            搜索结果的格式化文本
        """
        try:
            response = requests.get(
                f"{self.valves.RAG_API_URL}/rag/search",
                params={"query": query, "top_k": top_k},
                timeout=10
            )
            
            if response.status_code != 200:
                return f"❌ 搜索失败: {response.text}"
            
            results = response.json().get("results", [])
            
            if not results:
                return "📭 未找到相关知识"
            
            # 格式化结果
            formatted = f"🔍 找到 {len(results)} 条相关知识：\n\n"
            
            for i, result in enumerate(results, 1):
                score = result.get("score", 0) * 100
                content = result.get("content", "")[:200]
                source = result.get("metadata", {}).get("source", "未知")
                
                formatted += f"**{i}. 相关度 {score:.1f}%**\n"
                formatted += f"{content}...\n"
                formatted += f"_来源: {source}_\n\n"
            
            return formatted
            
        except Exception as e:
            return f"❌ 搜索错误: {str(e)}"
    
    async def upload_text_to_rag(
        self,
        text: str,
        source: str = "manual_input",
        __user__: dict = {}
    ) -> str:
        """
        上传文本到RAG知识库
        
        在OpenWebUI聊天中使用：
        "将这段文本保存到知识库：[你的文本]"
        
        Args:
            text: 要保存的文本
            source: 来源标识
            
        Returns:
            保存结果
        """
        try:
            data = {
                "content": text,
                "metadata": {
                    "source": source,
                    "user_id": __user__.get("id", "unknown"),
                    "added_from": "openwebui_chat"
                }
            }
            
            response = requests.post(
                f"{self.valves.RAG_API_URL}/rag/ingest",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return f"✅ 文本已保存到知识库\n文档ID: {result.get('id')}\n知识块数: {result.get('num_chunks', 0)}"
            else:
                return f"❌ 保存失败: {response.text}"
                
        except Exception as e:
            return f"❌ 保存错误: {str(e)}"
    
    async def get_rag_stats(
        self,
        __user__: dict = {}
    ) -> str:
        """
        获取RAG知识库统计信息
        
        在OpenWebUI聊天中使用：
        "查看知识库统计"
        
        Returns:
            统计信息
        """
        try:
            response = requests.get(
                f"{self.valves.RAG_API_URL}/rag/stats",
                timeout=5
            )
            
            if response.status_code != 200:
                return "❌ 无法获取统计信息"
            
            stats = response.json()
            
            formatted = "📊 **RAG知识库统计**\n\n"
            formatted += f"📄 文档总数: {stats.get('total_documents', 0)}\n"
            formatted += f"🧩 知识块数: {stats.get('total_chunks', 0)}\n"
            formatted += f"🔍 检索次数: {stats.get('total_queries', 0)}\n"
            formatted += f"💾 存储大小: {(stats.get('storage_bytes', 0) / 1024 / 1024):.2f} MB\n"
            formatted += f"📈 知识图谱节点: {stats.get('graph_nodes', 0)}\n"
            formatted += f"🔗 知识图谱关系: {stats.get('graph_edges', 0)}\n"
            
            return formatted
            
        except Exception as e:
            return f"❌ 获取统计错误: {str(e)}"
    
    async def list_documents(
        self,
        limit: int = 10,
        __user__: dict = {}
    ) -> str:
        """
        列出最近的文档
        
        在OpenWebUI聊天中使用：
        "列出最近上传的文档"
        
        Args:
            limit: 返回数量
            
        Returns:
            文档列表
        """
        try:
            response = requests.get(
                f"{self.valves.RAG_API_URL}/rag/documents",
                params={"limit": limit},
                timeout=5
            )
            
            if response.status_code != 200:
                return "❌ 无法获取文档列表"
            
            docs = response.json().get("documents", [])
            
            if not docs:
                return "📭 知识库中暂无文档"
            
            formatted = f"📚 **最近的 {len(docs)} 个文档**\n\n"
            
            for i, doc in enumerate(docs, 1):
                title = doc.get("title", "未命名")
                source = doc.get("metadata", {}).get("source", "未知")
                chunks = doc.get("num_chunks", 0)
                
                formatted += f"{i}. **{title}**\n"
                formatted += f"   来源: {source} | 知识块: {chunks}\n\n"
            
            return formatted
            
        except Exception as e:
            return f"❌ 获取列表错误: {str(e)}"
    
    async def delete_document(
        self,
        document_id: str,
        __user__: dict = {}
    ) -> str:
        """
        删除文档
        
        在OpenWebUI聊天中使用：
        "删除文档 [文档ID]"
        
        Args:
            document_id: 文档ID
            
        Returns:
            删除结果
        """
        try:
            response = requests.delete(
                f"{self.valves.RAG_API_URL}/rag/documents/{document_id}",
                timeout=5
            )
            
            if response.status_code == 200:
                return f"✅ 文档 {document_id} 已删除"
            else:
                return f"❌ 删除失败: {response.text}"
                
        except Exception as e:
            return f"❌ 删除错误: {str(e)}"
    
    async def query_knowledge_graph(
        self,
        entity: str,
        relation_type: Optional[str] = None,
        __user__: dict = {}
    ) -> str:
        """
        查询知识图谱
        
        在OpenWebUI聊天中使用：
        "查询知识图谱中关于'人工智能'的关系"
        
        Args:
            entity: 实体名称
            relation_type: 关系类型（可选）
            
        Returns:
            知识图谱查询结果
        """
        try:
            params = {"entity": entity}
            if relation_type:
                params["relation_type"] = relation_type
            
            response = requests.get(
                f"{self.valves.RAG_API_URL}/knowledge-graph/query",
                params=params,
                timeout=5
            )
            
            if response.status_code != 200:
                return "❌ 查询失败"
            
            result = response.json()
            relations = result.get("relations", [])
            
            if not relations:
                return f"📭 未找到实体 '{entity}' 的相关信息"
            
            formatted = f"🕸️ **知识图谱 - {entity}**\n\n"
            
            for rel in relations[:10]:  # 最多显示10条
                subject = rel.get("subject", "")
                predicate = rel.get("predicate", "")
                obj = rel.get("object", "")
                
                formatted += f"• {subject} **{predicate}** {obj}\n"
            
            if len(relations) > 10:
                formatted += f"\n_...还有 {len(relations) - 10} 条关系_"
            
            return formatted
            
        except Exception as e:
            return f"❌ 查询错误: {str(e)}"
    
    async def get_document_summary(
        self,
        document_id: str,
        __user__: dict = {}
    ) -> str:
        """
        获取文档摘要
        
        在OpenWebUI聊天中使用：
        "获取文档摘要 [文档ID]"
        
        Args:
            document_id: 文档ID
            
        Returns:
            文档摘要
        """
        try:
            response = requests.get(
                f"{self.valves.RAG_API_URL}/rag/documents/{document_id}/summary",
                timeout=5
            )
            
            if response.status_code != 200:
                return "❌ 无法获取摘要"
            
            summary = response.json()
            
            formatted = f"📄 **文档摘要**\n\n"
            formatted += f"标题: {summary.get('title', '未知')}\n"
            formatted += f"字数: {summary.get('word_count', 0)}\n"
            formatted += f"知识块: {summary.get('chunks', 0)}\n\n"
            formatted += f"**内容摘要**:\n{summary.get('summary', '暂无摘要')}\n\n"
            formatted += f"**关键词**: {', '.join(summary.get('keywords', []))}"
            
            return formatted
            
        except Exception as e:
            return f"❌ 获取摘要错误: {str(e)}"


