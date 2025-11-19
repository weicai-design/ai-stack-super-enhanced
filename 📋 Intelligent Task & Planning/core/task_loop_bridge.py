"""
任务闭环桥接器
负责将智能任务系统与超级Agent的备忘录、自学习、模块执行和RAG写回打通
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx

from .task_manager import TaskStatus
from .super_agent_integration import SuperAgentIntegration

logger = logging.getLogger(__name__)


class TaskLoopBridge:
    """
    任务闭环桥接器

    能力：
    1. 将任务生命周期事件写入超级Agent工作流监控
    2. 将任务状态同步到学习事件总线，触发自学习
    3. 记录模块执行结果，形成闭环
    4. 将任务执行与复盘结果写回RAG知识库
    """

    def __init__(
        self,
        super_agent_integration: Optional[SuperAgentIntegration] = None,
        rag_api_url: Optional[str] = None,
    ):
        self.integration = super_agent_integration
        self.super_agent_base = (
            super_agent_integration.super_agent_url.rstrip("/")
            if super_agent_integration and super_agent_integration.super_agent_url
            else None
        )
        self.system_event_endpoint = (
            f"{self.super_agent_base}/api/super-agent/workflow/system-events"
            if self.super_agent_base
            else None
        )
        self.learning_event_endpoint = (
            f"{self.super_agent_base}/api/super-agent/learning/events"
            if self.super_agent_base
            else None
        )
        self.rag_writeback_endpoint = (
            f"{self.super_agent_base}/api/super-agent/task-loop/rag-writeback"
            if self.super_agent_base
            else None
        )
        self.rag_fallback_endpoint = (
            f"{rag_api_url.rstrip('/')}/rag/ingest" if rag_api_url else None
        )

    async def on_stage(
        self,
        task: Dict[str, Any],
        stage: str,
        note: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """记录任务生命周期阶段"""
        payload = {
            "task": self._task_snapshot(task),
            "stage": stage,
            "note": note,
        }
        if extra:
            payload.update(extra)

        await asyncio.gather(
            self._record_system_event(
                event_type="task_lifecycle",
                severity="info",
                data=payload,
            ),
            self._record_learning_event(
                event_type="task_created"
                if stage == TaskStatus.CAPTURED.value
                else "task_updated",
                payload=payload,
            ),
            return_exceptions=True,
        )

    async def record_memo_link(self, task: Dict[str, Any], memo: Dict[str, Any]):
        """记录任务与备忘录的关联"""
        payload = {
            "task": self._task_snapshot(task),
            "memo": {
                "id": memo.get("id"),
                "title": memo.get("title"),
                "importance": memo.get("importance"),
                "tags": memo.get("tags", []),
            },
        }
        await self._record_learning_event("memo_extracted", payload=payload)

    async def on_execution_result(
        self,
        task: Dict[str, Any],
        execution_result: Dict[str, Any],
    ):
        """记录模块执行结果"""
        payload = {
            "task": self._task_snapshot(task),
            "execution_result": execution_result,
        }
        await asyncio.gather(
            self._record_system_event(
                event_type="module_result",
                severity="info" if execution_result.get("success", True) else "warning",
                data=payload,
                success=execution_result.get("success", True),
            ),
            self._record_learning_event(
                "task_updated",
                payload=payload,
                severity="warning"
                if not execution_result.get("success", True)
                else "info",
            ),
            return_exceptions=True,
        )

    async def write_back_rag(self, task: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将任务执行记录写回RAG"""
        base_metadata = task.get("metadata") or {}
        document = {
            "task_id": task.get("id"),
            "title": task.get("title"),
            "summary": self._build_summary(task),
            "metadata": {
                **base_metadata,
                "source": task.get("source"),
                "status": task.get("status"),
                "tags": task.get("tags", []),
                "priority": task.get("priority"),
            },
        }
        result = await self._post_json(self.rag_writeback_endpoint, document, timeout=10)
        if result:
            await self._record_learning_event(
                "task_updated",
                payload={
                    "task": self._task_snapshot(task),
                    "rag": {"status": "stored", "response": result},
                },
            )
            return result

        # 可选：降级到直接调用RAG摄入接口
        fallback_payload = {
            "text": document["summary"],
            "metadata": document["metadata"],
            "save_index": True,
        }
        fallback_result = await self._post_json(
            self.rag_fallback_endpoint, fallback_payload, timeout=10
        )
        if fallback_result:
            await self._record_learning_event(
                "task_updated",
                payload={
                    "task": self._task_snapshot(task),
                    "rag": {"status": "stored_fallback", "response": fallback_result},
                },
            )
        return fallback_result

    async def _record_system_event(
        self,
        event_type: str,
        severity: str = "info",
        data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error: Optional[str] = None,
    ):
        payload = {
            "event_type": event_type,
            "source": "task_loop_bridge",
            "severity": severity,
            "success": success,
            "data": data or {},
            "error": error,
        }
        await self._post_json(self.system_event_endpoint, payload)

    async def _record_learning_event(
        self,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        severity: str = "info",
    ):
        body = {
            "event_type": event_type,
            "source": "task_loop_bridge",
            "severity": severity,
            "payload": payload or {},
        }
        await self._post_json(self.learning_event_endpoint, body)

    async def _post_json(
        self,
        url: Optional[str],
        payload: Dict[str, Any],
        timeout: float = 5.0,
    ) -> Optional[Dict[str, Any]]:
        if not url:
            return None
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                if "application/json" in response.headers.get("content-type", ""):
                    return response.json()
        except Exception as exc:
            logger.debug("任务闭环请求失败: %s (%s)", url, exc)
        return None

    def _task_snapshot(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": task.get("id"),
            "title": task.get("title"),
            "status": task.get("status"),
            "priority": task.get("priority"),
            "source": task.get("source"),
            "tags": task.get("tags", []),
            "needs_confirmation": task.get("needs_confirmation"),
            "created_at": task.get("created_at"),
            "updated_at": task.get("updated_at"),
        }

    def _build_summary(self, task: Dict[str, Any]) -> str:
        lines = [
            f"任务：{task.get('title')}",
            f"描述：{task.get('description')}",
            f"来源：{task.get('source')} 优先级：{task.get('priority')}",
        ]
        if task.get("schedule"):
            lines.append(f"排期：{task['schedule']}")
        execution_result = task.get("execution_result") or {}
        if execution_result:
            lines.append(f"执行结果：{execution_result}")
        if task.get("review_feedback"):
            lines.append(f"复盘：{task['review_feedback']}")
        return "\n".join(lines)


