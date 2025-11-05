"""
RAG Integration Service
RAG集成服务 - 核心集成逻辑

负责与RAG API的通信和数据交换
"""

import os
import logging
from typing import Dict, List, Optional, Any
import httpx
from pathlib import Path

logger = logging.getLogger(__name__)


class RAGIntegrationService:
    """
    RAG集成服务
    
    提供与RAG API交互的核心方法
    """

    def __init__(
        self,
        rag_api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        初始化RAG集成服务
        
        Args:
            rag_api_url: RAG API地址，默认从环境变量获取或使用默认值
            api_key: API密钥（如果设置了RAG_API_KEY）
            timeout: 请求超时时间（秒）
        """
        self.rag_api_url = rag_api_url or os.getenv(
            "RAG_API_URL", "http://127.0.0.1:8011"
        )
        self.api_key = api_key or os.getenv("RAG_API_KEY", "")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def health_check(self) -> Dict[str, Any]:
        """
        检查RAG服务健康状态
        
        Returns:
            包含服务状态的字典
        """
        try:
            response = await self.client.get(f"{self.rag_api_url}/readyz")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RAG服务健康检查失败: {e}")
            return {"status": "error", "error": str(e)}

    async def ingest_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        save_index: bool = True,
    ) -> Dict[str, Any]:
        """
        将文本摄入到RAG库
        
        Args:
            text: 要摄入的文本内容
            doc_id: 可选的文档ID
            metadata: 可选的元数据
            save_index: 是否保存索引
            
        Returns:
            包含摄入结果的字典
        """
        try:
            payload = {
                "text": text,
                "save_index": save_index,
            }
            if doc_id:
                payload["doc_id"] = doc_id

            headers = self._get_headers()
            response = await self.client.post(
                f"{self.rag_api_url}/rag/ingest",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"文本摄入失败: {e}")
            return {"success": False, "error": str(e)}

    async def ingest_file(
        self,
        file_path: str,
        doc_id: Optional[str] = None,
        save_index: bool = True,
    ) -> Dict[str, Any]:
        """
        将文件摄入到RAG库
        
        Args:
            file_path: 文件路径
            doc_id: 可选的文档ID
            save_index: 是否保存索引
            
        Returns:
            包含摄入结果的字典
        """
        try:
            payload = {
                "path": file_path,
                "save_index": save_index,
            }
            if doc_id:
                payload["doc_id"] = doc_id

            headers = self._get_headers()
            response = await self.client.post(
                f"{self.rag_api_url}/rag/ingest",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"文件摄入失败: {e}")
            return {"success": False, "error": str(e)}

    async def search(
        self, query: str, top_k: int = 5
    ) -> Dict[str, Any]:
        """
        在RAG库中搜索
        
        Args:
            query: 搜索查询
            top_k: 返回结果数量
            
        Returns:
            包含搜索结果的字典
        """
        try:
            params = {"query": query, "top_k": top_k}
            response = await self.client.get(
                f"{self.rag_api_url}/rag/search",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return {"items": [], "error": str(e)}

    async def get_kg_snapshot(self) -> Dict[str, Any]:
        """
        获取知识图谱快照
        
        Returns:
            包含知识图谱数据的字典
        """
        try:
            response = await self.client.get(
                f"{self.rag_api_url}/kg/snapshot"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取知识图谱快照失败: {e}")
            return {"success": False, "error": str(e)}

    async def query_kg(
        self, entity_type: str, entity_value: str
    ) -> Dict[str, Any]:
        """
        查询知识图谱中的实体
        
        Args:
            entity_type: 实体类型（如email, url, phone等）
            entity_value: 实体值
            
        Returns:
            包含查询结果的字典
        """
        try:
            params = {"type": entity_type, "value": entity_value}
            response = await self.client.get(
                f"{self.rag_api_url}/kg/query",
                params=params,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"知识图谱查询失败: {e}")
            return {"success": False, "error": str(e)}

    async def get_index_info(self) -> Dict[str, Any]:
        """
        获取索引信息
        
        Returns:
            包含索引信息的字典
        """
        try:
            response = await self.client.get(
                f"{self.rag_api_url}/index/info"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取索引信息失败: {e}")
            return {"error": str(e)}

    def _get_headers(self) -> Dict[str, str]:
        """
        获取请求头（包含API Key如果设置了）
        
        Returns:
            请求头字典
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()


# 全局服务实例
_rag_service: Optional[RAGIntegrationService] = None


def get_rag_service() -> RAGIntegrationService:
    """
    获取全局RAG集成服务实例（单例模式）
    
    Returns:
        RAGIntegrationService实例
    """
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGIntegrationService()
    return _rag_service

