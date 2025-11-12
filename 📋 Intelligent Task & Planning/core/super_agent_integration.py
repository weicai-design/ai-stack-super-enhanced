"""
超级Agent集成
与超级Agent打通底层逻辑
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import httpx

class SuperAgentIntegration:
    """
    超级Agent集成
    
    功能：
    1. 从超级Agent接收任务识别结果
    2. 从备忘录系统获取任务
    3. 将任务发送给超级Agent确认
    4. 执行结果反馈给超级Agent
    """
    
    def __init__(self, super_agent_url: str = "http://localhost:8000"):
        self.super_agent_url = super_agent_url
        self.api_base = f"{super_agent_url}/api/super-agent"
        self.timeout = 30.0
    
    async def sync_with_super_agent(
        self,
        memos: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        与超级Agent同步
        
        Args:
            memos: 备忘录列表（可选）
            
        Returns:
            同步结果
        """
        try:
            # 从超级Agent获取备忘录（如果未提供）
            if not memos:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(f"{self.api_base}/memos")
                    if response.status_code == 200:
                        data = response.json()
                        memos = data.get("memos", [])
            
            # 提取任务
            tasks = []
            for memo in memos:
                if memo.get("type") == "task":
                    tasks.append({
                        "content": memo.get("content", ""),
                        "importance": memo.get("importance", 3),
                        "tags": memo.get("tags", []),
                        "source": "super_agent_memo",
                        "source_id": memo.get("id")
                    })
            
            return {
                "success": True,
                "tasks_extracted": len(tasks),
                "tasks": tasks,
                "synced_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_tasks_for_confirmation(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        发送任务给超级Agent确认
        
        Args:
            tasks: 任务列表
            
        Returns:
            确认结果
        """
        try:
            # 提取任务
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/tasks/extract",
                    json={"tasks": tasks}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def notify_task_completion(
        self,
        task_id: int,
        result: Dict[str, Any]
    ) -> bool:
        """
        通知超级Agent任务完成
        
        Args:
            task_id: 任务ID
            result: 执行结果
            
        Returns:
            是否成功
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.api_base}/tasks/{task_id}/complete",
                    json={"result": result}
                )
                return response.status_code == 200
        except Exception:
            return False

