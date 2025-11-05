"""
OpenWebUI RAG Integration Plugin
OpenWebUI RAG集成插件

功能：
1. 聊天内容自动保存到RAG
2. 调用RAG检索增强回答
3. 文件上传自动处理
"""

import requests
import json
from typing import Optional, Dict, Any, List
from datetime import datetime


class RAGIntegrationPlugin:
    """RAG集成插件"""
    
    def __init__(self, rag_api_url: str = "http://localhost:8011"):
        """
        初始化RAG集成插件
        
        Args:
            rag_api_url: RAG API地址
        """
        self.rag_api_url = rag_api_url
        self.enabled = True
    
    async def on_chat_message(
        self, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        聊天消息钩子 - 自动保存到RAG
        
        根据需求1.4: OpenWebUI聊天内容自动保存
        
        Args:
            message: 用户消息
            user_id: 用户ID
            conversation_id: 对话ID
            metadata: 元数据
            
        Returns:
            处理结果
        """
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            # 构造文档数据
            doc_data = {
                "content": message,
                "metadata": {
                    "source": "openwebui_chat",
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {})
                },
                "chunk_size": 500,
                "chunk_overlap": 50
            }
            
            # 调用RAG摄入API
            response = requests.post(
                f"{self.rag_api_url}/rag/ingest",
                json=doc_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message": "聊天内容已保存到RAG",
                    "doc_id": result.get("id")
                }
            else:
                return {
                    "status": "error",
                    "message": f"保存失败: {response.text}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"RAG保存异常: {str(e)}"
            }
    
    async def enhance_response(
        self,
        query: str,
        context: Optional[List[str]] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        增强回答 - 使用RAG检索相关知识
        
        根据需求1.5: 检索利用RAG库
        
        Args:
            query: 查询问题
            context: 上下文
            top_k: 返回结果数量
            
        Returns:
            增强的上下文和答案
        """
        if not self.enabled:
            return {"enhanced": False}
        
        try:
            # 调用RAG搜索API
            params = {
                "query": query,
                "top_k": top_k
            }
            
            response = requests.get(
                f"{self.rag_api_url}/rag/search",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # 提取相关文档
                relevant_docs = [
                    doc.get("content", "") 
                    for doc in results.get("results", [])
                ]
                
                return {
                    "enhanced": True,
                    "relevant_context": relevant_docs,
                    "sources": results.get("results", []),
                    "query": query
                }
            else:
                return {"enhanced": False, "error": response.text}
                
        except Exception as e:
            return {
                "enhanced": False,
                "error": f"RAG检索异常: {str(e)}"
            }
    
    async def on_file_upload(
        self,
        file_path: str,
        file_name: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        文件上传钩子 - 自动处理并保存到RAG
        
        根据需求5.2: 上传所有格式文件自动处理
        
        Args:
            file_path: 文件路径
            file_name: 文件名
            user_id: 用户ID
            metadata: 元数据
            
        Returns:
            处理结果
        """
        if not self.enabled:
            return {"status": "disabled"}
        
        try:
            # 读取文件
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f)}
                data = {
                    'metadata': json.dumps({
                        "source": "openwebui_upload",
                        "user_id": user_id,
                        "upload_time": datetime.now().isoformat(),
                        **(metadata or {})
                    })
                }
                
                # 调用RAG文件上传API
                response = requests.post(
                    f"{self.rag_api_url}/rag/upload",
                    files=files,
                    data=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "status": "success",
                        "message": f"文件已处理并保存到RAG",
                        "doc_id": result.get("id"),
                        "chunks": result.get("num_chunks", 0)
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"文件处理失败: {response.text}"
                    }
                    
        except Exception as e:
            return {
                "status": "error",
                "message": f"文件处理异常: {str(e)}"
            }
    
    async def search_knowledge(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        知识搜索 - 直接搜索RAG库
        
        Args:
            query: 搜索查询
            filters: 过滤条件
            top_k: 返回数量
            
        Returns:
            搜索结果
        """
        if not self.enabled:
            return []
        
        try:
            params = {
                "query": query,
                "top_k": top_k
            }
            
            if filters:
                params.update(filters)
            
            response = requests.get(
                f"{self.rag_api_url}/rag/search",
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json()
                return results.get("results", [])
            else:
                return []
                
        except Exception as e:
            print(f"RAG搜索异常: {e}")
            return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取插件状态
        
        Returns:
            插件状态信息
        """
        try:
            response = requests.get(
                f"{self.rag_api_url}/readyz",
                timeout=2
            )
            
            return {
                "enabled": self.enabled,
                "rag_api": self.rag_api_url,
                "rag_status": "online" if response.status_code == 200 else "offline",
                "version": "1.0.0"
            }
        except:
            return {
                "enabled": self.enabled,
                "rag_api": self.rag_api_url,
                "rag_status": "offline",
                "version": "1.0.0"
            }


# 全局插件实例
rag_plugin = RAGIntegrationPlugin()


# OpenWebUI插件接口函数
async def on_startup():
    """插件启动时调用"""
    print("🚀 RAG集成插件已启动")
    status = rag_plugin.get_status()
    print(f"📊 RAG状态: {status}")


async def on_shutdown():
    """插件关闭时调用"""
    print("👋 RAG集成插件已关闭")


async def inlet(body: dict, __user__: dict) -> dict:
    """
    请求前处理 - 增强用户查询
    
    Args:
        body: 请求体
        __user__: 用户信息
        
    Returns:
        处理后的请求体
    """
    # 获取用户消息
    messages = body.get("messages", [])
    if not messages:
        return body
    
    last_message = messages[-1]
    user_query = last_message.get("content", "")
    
    # 保存聊天内容到RAG
    await rag_plugin.on_chat_message(
        message=user_query,
        user_id=__user__.get("id", ""),
        conversation_id=body.get("chat_id", ""),
        metadata={"role": last_message.get("role", "user")}
    )
    
    # 使用RAG增强回答
    enhanced = await rag_plugin.enhance_response(
        query=user_query,
        context=[m.get("content") for m in messages[:-1]],
        top_k=3
    )
    
    # 如果有相关知识，添加到系统提示
    if enhanced.get("enhanced") and enhanced.get("relevant_context"):
        system_message = {
            "role": "system",
            "content": f"参考以下知识库内容：\n" + "\n".join(enhanced["relevant_context"][:2])
        }
        body["messages"].insert(0, system_message)
    
    return body


async def outlet(body: dict, __user__: dict) -> dict:
    """
    响应后处理 - 保存AI回答
    
    Args:
        body: 响应体
        __user__: 用户信息
        
    Returns:
        处理后的响应体
    """
    # 保存AI回答到RAG
    messages = body.get("messages", [])
    if messages:
        last_message = messages[-1]
        if last_message.get("role") == "assistant":
            await rag_plugin.on_chat_message(
                message=last_message.get("content", ""),
                user_id="assistant",
                conversation_id=body.get("chat_id", ""),
                metadata={"role": "assistant"}
            )
    
    return body

