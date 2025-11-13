"""
模块执行器
调用各模块功能执行任务
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import httpx

class ModuleExecutor:
    """
    模块执行器
    
    功能：
    1. 调用各模块API
    2. 执行任务
    3. 返回结果
    4. 错误处理
    """
    
    def __init__(self):
        # 模块API映射
        self.module_apis = {
            "rag": "http://localhost:8011/api/v5/rag",
            "erp": "http://localhost:8013/api",
            "content": "http://localhost:8016/api",
            "trend": "http://localhost:8015/api",
            "stock": "http://localhost:8014/api",
            "operations": "http://localhost:8000/api/operations",
            "finance": "http://localhost:8000/api/finance",
            "coding": "http://localhost:8000/api/coding-assistant",
            "task": "http://localhost:8000/api/task-planning"
        }
        self.timeout = 30.0
    
    async def execute(
        self,
        expert: Dict[str, Any],
        input: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行模块功能
        
        Args:
            expert: 专家信息
            input: 用户输入
            context: 上下文（包含RAG检索结果）
            
        Returns:
            执行结果
        """
        module = expert.get("module", "rag")
        expert_name = expert.get("expert", "default_expert")
        
        try:
            # 根据模块调用不同的API
            if module == "rag":
                result = await self._execute_rag(input, context)
            elif module == "erp":
                result = await self._execute_erp(input, context)
            elif module == "content":
                result = await self._execute_content(input, context)
            elif module == "trend":
                result = await self._execute_trend(input, context)
            elif module == "stock":
                result = await self._execute_stock(input, context)
            elif module == "operations":
                result = await self._execute_operations(input, context)
            elif module == "finance":
                result = await self._execute_finance(input, context)
            elif module == "coding":
                result = await self._execute_coding(input, context)
            elif module == "task":
                result = await self._execute_task(input, context)
            else:
                result = {
                    "success": False,
                    "error": f"未知模块: {module}"
                }
            
            return {
                "success": True,
                "module": module,
                "expert": expert_name,
                "result": result,
                "executed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "module": module,
                "expert": expert_name,
                "error": str(e),
                "executed_at": datetime.now().isoformat()
            }
    
    async def _call_module_api(
        self,
        module: str,
        endpoint: str,
        method: str = "POST",
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        调用模块API的通用方法
        
        Args:
            module: 模块名称
            endpoint: API端点路径
            method: HTTP方法
            params: URL参数（GET请求）
            json_data: JSON数据（POST请求）
            
        Returns:
            API响应结果
        """
        base_url = self.module_apis.get(module)
        if not base_url:
            raise ValueError(f"未知模块: {module}")
        
        url = f"{base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, params=params)
                else:
                    response = await client.post(url, json=json_data or {})
                
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            raise Exception(f"API调用失败 ({module}): HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            raise Exception(f"API连接失败 ({module}): {str(e)}")
    
    async def _execute_rag(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行RAG模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "rag",
                "/retrieve",
                method="POST",
                json_data={
                    "query": input,
                    "top_k": 5,
                    "context": context
                }
            )
            return {
                "type": "rag",
                "message": "RAG检索完成",
                "knowledge": result.get("knowledge", result.get("results", []))
            }
        except Exception as e:
            return {
                "type": "rag",
                "message": f"RAG检索失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_erp(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行ERP模块⭐真实实现"""
        try:
            # 根据输入内容判断调用哪个ERP端点
            if "订单" in input or "order" in input.lower():
                endpoint = "/erp/orders"
            elif "项目" in input or "project" in input.lower():
                endpoint = "/erp/projects"
            elif "财务" in input or "finance" in input.lower():
                endpoint = "/erp/finance/dashboard"
            else:
                endpoint = "/erp/assistant/ask"
            
            result = await self._call_module_api(
                "erp",
                endpoint,
                method="POST" if "ask" in endpoint else "GET",
                json_data={"query": input} if "ask" in endpoint else None,
                params={"query": input} if "ask" not in endpoint else None
            )
            return {
                "type": "erp",
                "message": "ERP功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "erp",
                "message": f"ERP功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_content(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行内容创作模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "content",
                "/content/assistant/ask",
                method="POST",
                json_data={"query": input, "context": context}
            )
            return {
                "type": "content",
                "message": "内容创作功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "content",
                "message": f"内容创作功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_trend(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行趋势分析模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "trend",
                "/trend/assistant/ask",
                method="POST",
                json_data={"query": input, "context": context}
            )
            return {
                "type": "trend",
                "message": "趋势分析功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "trend",
                "message": f"趋势分析功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_stock(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行股票量化模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "stock",
                "/stock/assistant/ask",
                method="POST",
                json_data={"query": input, "context": context}
            )
            return {
                "type": "stock",
                "message": "股票量化功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "stock",
                "message": f"股票量化功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_operations(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行运营管理模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "operations",
                "/operations/query",
                method="POST",
                json_data={"query": input, "context": context}
            )
            return {
                "type": "operations",
                "message": "运营管理功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "operations",
                "message": f"运营管理功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_finance(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行财务管理模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "finance",
                "/finance/query",
                method="POST",
                json_data={"query": input, "context": context}
            )
            return {
                "type": "finance",
                "message": "财务管理功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "finance",
                "message": f"财务管理功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_coding(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行编程助手模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "coding",
                "/generate",
                method="POST",
                json_data={"prompt": input, "context": context}
            )
            return {
                "type": "coding",
                "message": "编程助手功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "coding",
                "message": f"编程助手功能执行失败: {str(e)}",
                "error": str(e)
            }
    
    async def _execute_task(self, input: str, context: Dict) -> Dict[str, Any]:
        """执行任务管理模块⭐真实实现"""
        try:
            result = await self._call_module_api(
                "task",
                "/tasks/create",
                method="POST",
                json_data={"description": input, "context": context}
            )
            return {
                "type": "task",
                "message": "任务管理功能执行完成",
                "data": result
            }
        except Exception as e:
            return {
                "type": "task",
                "message": f"任务管理功能执行失败: {str(e)}",
                "error": str(e)
            }

