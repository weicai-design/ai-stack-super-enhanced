"""
Network Information Handler
网络信息处理器

根据需求1.4: open webui聊天框搜索到的网络信息、数据、人与AI的交互信息
和其他智能体产生的业务信息、数据会将有用、有效信息经过预处理后进入RAG库

功能：
1. 捕获OpenWebUI的网络搜索结果
2. 捕获网络数据
3. 捕获智能体业务信息
4. 预处理后保存到RAG库
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from rag_integration import get_rag_service

logger = logging.getLogger(__name__)


class NetworkInfoExtractor:
    """
    网络信息提取器
    从OpenWebUI的网络搜索结果中提取有用信息
    """

    def __init__(self, use_enhanced_extraction: bool = True):
        """
        初始化提取器
        
        Args:
            use_enhanced_extraction: 是否使用增强提取（需要web_content_extractor）
        """
        self.min_content_length = 50  # 最小内容长度
        self.max_content_length = 50000  # 最大内容长度
        self.use_enhanced_extraction = use_enhanced_extraction
        
        # 尝试导入增强提取器
        self.web_extractor = None
        if use_enhanced_extraction:
            try:
                from .web_content_extractor import WebContentExtractor
                self.web_extractor = WebContentExtractor()
                logger.info("启用增强网页内容提取")
            except ImportError:
                try:
                    from web_content_extractor import WebContentExtractor
                    self.web_extractor = WebContentExtractor()
                    logger.info("启用增强网页内容提取")
                except ImportError:
                    logger.warning("增强网页内容提取器不可用，使用简单提取")
                    self.use_enhanced_extraction = False

    def extract_from_web_search_result(
        self, search_result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        从网络搜索结果中提取信息（增强版）
        
        Args:
            search_result: 搜索结果字典，可能包含：
                - title: 标题
                - url: URL
                - snippet: 摘要
                - content: 内容
                - html_content: HTML内容（增强提取）
                
        Returns:
            提取的信息字典，如果无效则返回None
        """
        if not search_result:
            return None

        title = search_result.get("title", "").strip()
        url = search_result.get("url", "").strip()
        snippet = search_result.get("snippet", "").strip()
        content = search_result.get("content", "").strip()
        html_content = search_result.get("html_content") or search_result.get("html", "")

        # 如果使用增强提取且有HTML内容
        if self.use_enhanced_extraction and self.web_extractor and html_content:
            try:
                extracted = self.web_extractor.extract_content(html_content, url)
                if extracted.get("success"):
                    formatted_text = extracted["text"]
                    metadata = extracted.get("metadata", {})
                    
                    # 合并元数据
                    metadata.update({
                        "type": "web_search_result",
                        "title": title or metadata.get("title", ""),
                        "url": url,
                        "snippet": snippet[:200] if snippet else "",
                        "source_type": "network",
                        "extraction_method": "enhanced",
                    })
                    
                    return {
                        "text": formatted_text,
                        "source": url,
                        "metadata": metadata,
                    }
            except Exception as e:
                logger.warning(f"增强提取失败，回退到简单提取: {e}")

        # 回退到简单提取
        # 优先使用content，其次snippet
        text_content = content if content else snippet

        if not text_content or len(text_content) < self.min_content_length:
            return None

        # 限制长度
        if len(text_content) > self.max_content_length:
            text_content = text_content[:self.max_content_length]

        # 构建格式化文本
        formatted_text = self._format_network_info(title, url, text_content)

        return {
            "text": formatted_text,
            "source": url,
            "metadata": {
                "type": "web_search_result",
                "title": title,
                "url": url,
                "snippet": snippet[:200] if snippet else "",
                "timestamp": datetime.now().isoformat(),
                "source_type": "network",
                "extraction_method": "simple",
            },
        }

    def extract_from_api_response(
        self, api_response: Dict[str, Any], api_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        从API响应中提取信息
        
        Args:
            api_response: API响应数据
            api_name: API名称
            
        Returns:
            提取的信息字典
        """
        if not api_response:
            return None

        # 尝试提取文本内容
        text_content = None

        # 常见API响应格式
        if isinstance(api_response, dict):
            # 尝试多个可能的字段
            for key in ["data", "result", "content", "text", "message"]:
                if key in api_response:
                    value = api_response[key]
                    if isinstance(value, str):
                        text_content = value
                        break
                    elif isinstance(value, dict):
                        # 递归提取
                        text_content = self._extract_text_from_dict(value)
                        break
                    elif isinstance(value, list):
                        # 从列表中提取文本
                        text_content = self._extract_text_from_list(value)
                        break

        if not text_content or len(text_content) < self.min_content_length:
            return None

        # 限制长度
        if len(text_content) > self.max_content_length:
            text_content = text_content[:self.max_content_length]

        # 构建格式化文本
        formatted_text = f"[API: {api_name}]\n{text_content}"

        return {
            "text": formatted_text,
            "source": f"api:{api_name}",
            "metadata": {
                "type": "api_response",
                "api_name": api_name,
                "timestamp": datetime.now().isoformat(),
                "source_type": "network",
            },
        }

    def _format_network_info(self, title: str, url: str, content: str) -> str:
        """
        格式化网络信息
        
        Args:
            title: 标题
            url: URL
            content: 内容
            
        Returns:
            格式化后的文本
        """
        parts = []
        
        if title:
            parts.append(f"标题: {title}")
        if url:
            parts.append(f"来源: {url}")
        
        parts.append("")
        parts.append(content)
        
        return "\n".join(parts)

    def _extract_text_from_dict(self, data: Dict[str, Any]) -> Optional[str]:
        """从字典中提取文本"""
        texts = []
        for key, value in data.items():
            if isinstance(value, str) and len(value) > 10:
                texts.append(value)
            elif isinstance(value, dict):
                sub_text = self._extract_text_from_dict(value)
                if sub_text:
                    texts.append(sub_text)
        return " ".join(texts) if texts else None

    def _extract_text_from_list(self, data: List[Any]) -> Optional[str]:
        """从列表中提取文本"""
        texts = []
        for item in data:
            if isinstance(item, str) and len(item) > 10:
                texts.append(item)
            elif isinstance(item, dict):
                sub_text = self._extract_text_from_dict(item)
                if sub_text:
                    texts.append(sub_text)
        return " ".join(texts) if texts else None


class AgentInfoHandler:
    """
    智能体信息处理器
    处理智能体产生的业务信息和数据
    """

    def __init__(self):
        self.rag_service = get_rag_service()

    def process_agent_output(
        self,
        agent_name: str,
        output: Any,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理智能体输出
        
        Args:
            agent_name: 智能体名称
            output: 智能体输出（可能是字符串、字典等）
            task_id: 任务ID
            metadata: 额外元数据
            
        Returns:
            处理结果
        """
        try:
            # 转换为文本
            if isinstance(output, str):
                text = output
            elif isinstance(output, dict):
                # 提取字典中的文本信息
                text = self._extract_text_from_agent_output(output)
            else:
                text = str(output)

            if not text or len(text.strip()) < 50:
                return {
                    "saved": False,
                    "reason": "content_too_short",
                }

            # 格式化文本
            formatted_text = self._format_agent_info(agent_name, text, task_id)

            # 准备元数据
            doc_metadata = {
                "source": "agent_output",
                "agent_name": agent_name,
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {}),
            }

            # 生成文档ID
            doc_id = self._generate_agent_doc_id(agent_name, task_id)

            # 注意：这里需要导入chat_handler或直接使用rag_service
            # 为了简化，直接使用rag_service
            result = self.rag_service.ingest_text(
                text=formatted_text,
                doc_id=doc_id,
                metadata=doc_metadata,
                save_index=True,
            )

            if result.get("success", False):
                logger.info(
                    f"智能体信息已保存: agent={agent_name}, task={task_id}"
                )
                return {
                    "saved": True,
                    "doc_id": result.get("ids", [doc_id])[0],
                    "size": result.get("size", 0),
                }
            else:
                return {
                    "saved": False,
                    "error": result.get("error"),
                }

        except Exception as e:
            logger.error(f"处理智能体输出失败: {e}")
            return {"saved": False, "error": str(e)}

    def _extract_text_from_agent_output(self, output: Dict[str, Any]) -> str:
        """从智能体输出字典中提取文本"""
        texts = []
        
        # 常见字段
        for key in ["result", "output", "content", "message", "data", "summary"]:
            if key in output:
                value = output[key]
                if isinstance(value, str):
                    texts.append(value)
                elif isinstance(value, dict):
                    texts.append(str(value))

        # 如果没有找到，序列化整个字典
        if not texts:
            import json
            texts.append(json.dumps(output, ensure_ascii=False))

        return " ".join(texts)

    def _format_agent_info(
        self, agent_name: str, output: str, task_id: Optional[str]
    ) -> str:
        """格式化智能体信息"""
        parts = [f"[智能体: {agent_name}]"]
        if task_id:
            parts.append(f"[任务ID: {task_id}]")
        parts.append("")
        parts.append(output)
        return "\n".join(parts)

    def _generate_agent_doc_id(
        self, agent_name: str, task_id: Optional[str]
    ) -> str:
        """生成智能体文档ID"""
        import uuid
        parts = ["agent", agent_name]
        if task_id:
            parts.append(task_id[:8])
        parts.append(uuid.uuid4().hex[:8])
        return "_".join(parts)


class NetworkInfoHandler:
    """
    网络信息处理器
    统一处理所有网络信息和智能体信息
    """

    def __init__(self, auto_save: bool = True):
        """
        初始化网络信息处理器
        
        Args:
            auto_save: 是否自动保存
        """
        self.auto_save = auto_save
        self.extractor = NetworkInfoExtractor()
        self.agent_handler = AgentInfoHandler()
        self.rag_service = get_rag_service()

    async def process_web_search_results(
        self,
        search_results: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """
        处理网络搜索结果（增强版，支持重试机制）
        
        Args:
            search_results: 搜索结果列表
            user_id: 用户ID
            session_id: 会话ID
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            
        Returns:
            处理结果
        """
        if not self.auto_save:
            return {"saved": False, "reason": "auto_save_disabled"}

        saved_count = 0
        failed_count = 0
        skipped_count = 0

        for result in search_results:
            # 重试机制
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    extracted = self.extractor.extract_from_web_search_result(result)
                    if not extracted:
                        skipped_count += 1
                        break  # 跳过无效结果，不重试

                    # 添加用户和会话信息
                    extracted["metadata"]["user_id"] = user_id
                    extracted["metadata"]["session_id"] = session_id

                    # 保存到RAG库
                    doc_id = self._generate_doc_id(extracted["source"], "web_search")
                    
                    # 使用同步方式（rag_service.ingest_text是同步的）
                    # 需要通过httpx异步客户端调用API
                    import asyncio
                    loop = asyncio.get_event_loop()
                    save_result = await loop.run_in_executor(
                        None,
                        lambda: self._sync_ingest_text(
                            text=extracted["text"],
                            doc_id=doc_id,
                            metadata=extracted["metadata"],
                        ),
                    )

                    if save_result.get("success", False):
                        saved_count += 1
                        success = True
                    else:
                        if retry_count < max_retries - 1:
                            retry_count += 1
                            await asyncio.sleep(retry_delay * retry_count)  # 指数退避
                        else:
                            failed_count += 1
                            logger.warning(
                                f"保存搜索结果失败（已重试{retry_count}次）: {save_result.get('error', '未知错误')}"
                            )

                except Exception as e:
                    if retry_count < max_retries - 1:
                        retry_count += 1
                        await asyncio.sleep(retry_delay * retry_count)
                        logger.debug(f"处理搜索结果失败，准备重试 ({retry_count}/{max_retries}): {e}")
                    else:
                        logger.error(f"处理搜索结果失败（已重试{retry_count}次）: {e}")
                        failed_count += 1

        return {
            "saved": saved_count > 0,
            "saved_count": saved_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "total": len(search_results),
            "retry_enabled": True,
        }

    async def process_agent_info(
        self,
        agent_name: str,
        output: Any,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理智能体信息
        
        Args:
            agent_name: 智能体名称
            output: 智能体输出
            task_id: 任务ID
            metadata: 额外元数据
            
        Returns:
            处理结果
        """
        if not self.auto_save:
            return {"saved": False, "reason": "auto_save_disabled"}

        # 注意：AgentInfoHandler的方法可能不是async
        # 这里需要适配
        try:
            # 同步调用（AgentInfoHandler内部会处理）
            result = self.agent_handler.process_agent_output(
                agent_name=agent_name,
                output=output,
                task_id=task_id,
                metadata=metadata,
            )
            return result
        except Exception as e:
            logger.error(f"处理智能体信息失败: {e}")
            return {"saved": False, "error": str(e)}

    def _generate_doc_id(self, source: str, prefix: str) -> str:
        """生成文档ID"""
        import uuid
        import hashlib
        source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
        return f"{prefix}_{source_hash}_{uuid.uuid4().hex[:8]}"

    def _sync_ingest_text(
        self,
        text: str,
        doc_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        同步方式摄入文本（内部方法，增强错误处理）
        
        Args:
            text: 文本内容
            doc_id: 文档ID
            metadata: 元数据
            
        Returns:
            摄入结果
        """
        import httpx
        try:
            # 使用同步客户端调用API
            payload = {
                "text": text,
                "doc_id": doc_id,
                "save_index": True,
                "metadata": metadata,  # 确保元数据被传递
            }
            
            # 获取headers（如果rag_service有这个方法）
            headers = {}
            if hasattr(self.rag_service, "_get_headers"):
                headers = self.rag_service._get_headers()
            elif hasattr(self.rag_service, "api_key") and self.rag_service.api_key:
                headers = {"X-API-Key": self.rag_service.api_key}
            
            headers.setdefault("Content-Type", "application/json")
            
            # 获取API URL和超时设置
            api_url = getattr(self.rag_service, "rag_api_url", "http://127.0.0.1:8011")
            timeout = getattr(self.rag_service, "timeout", 30.0)
            
            response = httpx.post(
                f"{api_url}/rag/ingest",
                json=payload,
                headers=headers,
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP错误 {e.response.status_code}: {e}")
            return {"success": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except httpx.RequestError as e:
            logger.error(f"请求错误: {e}")
            return {"success": False, "error": f"请求失败: {str(e)}"}
        except Exception as e:
            logger.error(f"同步摄入文本失败: {e}")
            return {"success": False, "error": str(e)}


# 全局实例
_network_handler: Optional[NetworkInfoHandler] = None


def get_network_info_handler() -> NetworkInfoHandler:
    """获取网络信息处理器实例（单例）"""
    global _network_handler
    if _network_handler is None:
        _network_handler = NetworkInfoHandler(auto_save=True)
    return _network_handler

