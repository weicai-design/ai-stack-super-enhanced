"""
批量操作系统
Batch Operations System

支持批量文档上传、后台任务队列、进度追踪

版本: 1.0.0 (v2.6.0新增)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/batch", tags=["Batch Operations"])


# ==================== 数据模型 ====================

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


class BatchTask(BaseModel):
    """批量任务"""
    task_id: str = Field(..., description="任务ID")
    task_type: str = Field(..., description="任务类型")
    status: TaskStatus = Field(TaskStatus.PENDING, description="任务状态")
    total_items: int = Field(0, description="总项目数")
    processed_items: int = Field(0, description="已处理项目数")
    failed_items: int = Field(0, description="失败项目数")
    progress: float = Field(0.0, ge=0, le=100, description="进度百分比")
    created_at: str = Field(..., description="创建时间")
    started_at: Optional[str] = Field(None, description="开始时间")
    completed_at: Optional[str] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误消息")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")


class BatchUploadRequest(BaseModel):
    """批量上传请求"""
    files: List[str] = Field(..., description="文件路径列表")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="上传选项")


class BatchIngestRequest(BaseModel):
    """批量导入请求"""
    texts: List[str] = Field(..., description="文本列表")
    metadata: Optional[List[Dict]] = Field(None, description="元数据列表")


# ==================== 任务存储 ====================

class TaskStore:
    """任务存储（内存存储，生产环境建议使用数据库）"""
    
    def __init__(self):
        self.tasks: Dict[str, BatchTask] = {}
        self.max_tasks = 1000  # 最多保存1000个任务
    
    def create_task(self, task_type: str, total_items: int = 0) -> str:
        """创建任务"""
        task_id = str(uuid.uuid4())
        task = BatchTask(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            total_items=total_items,
            processed_items=0,
            failed_items=0,
            progress=0.0,
            created_at=datetime.now().isoformat()
        )
        
        self.tasks[task_id] = task
        
        # 限制任务数量
        if len(self.tasks) > self.max_tasks:
            # 删除最老的已完成任务
            completed_tasks = [
                (tid, t) for tid, t in self.tasks.items()
                if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
            ]
            if completed_tasks:
                oldest_task_id = min(completed_tasks, key=lambda x: x[1].created_at)[0]
                del self.tasks[oldest_task_id]
        
        logger.info(f"创建任务: {task_id} (类型: {task_type}, 项目数: {total_items})")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[BatchTask]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def update_task(self, task_id: str, **updates):
        """更新任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        
        # 自动计算进度
        if task.total_items > 0:
            task.progress = (task.processed_items / task.total_items) * 100
        
        return True
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[str] = None,
        limit: int = 50
    ) -> List[BatchTask]:
        """列出任务"""
        tasks = list(self.tasks.values())
        
        # 过滤
        if status:
            tasks = [t for t in tasks if t.status == status]
        if task_type:
            tasks = [t for t in tasks if t.task_type == task_type]
        
        # 按创建时间排序（最新的在前）
        tasks.sort(key=lambda x: x.created_at, reverse=True)
        
        return tasks[:limit]
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False


# 全局任务存储
task_store = TaskStore()


# ==================== 批量处理逻辑 ====================

async def process_batch_upload(
    task_id: str,
    files: List[str],
    options: Dict[str, Any]
):
    """
    批量上传处理（后台任务）
    
    Args:
        task_id: 任务ID
        files: 文件路径列表
        options: 处理选项
    """
    try:
        # 更新任务状态
        task_store.update_task(
            task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        results = []
        
        for idx, file_path in enumerate(files):
            try:
                # TODO: 实际的文件处理逻辑
                # 这里使用模拟处理
                await asyncio.sleep(0.1)  # 模拟处理时间
                
                result = {
                    "file": file_path,
                    "status": "success",
                    "doc_id": f"doc_{uuid.uuid4().hex[:8]}"
                }
                results.append(result)
                
                # 更新进度
                task_store.update_task(
                    task_id,
                    processed_items=idx + 1
                )
                
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                results.append({
                    "file": file_path,
                    "status": "failed",
                    "error": str(e)
                })
                task_store.update_task(
                    task_id,
                    failed_items=task_store.get_task(task_id).failed_items + 1,
                    processed_items=idx + 1
                )
        
        # 任务完成
        task_store.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now().isoformat(),
            result={
                "success_count": len([r for r in results if r["status"] == "success"]),
                "failed_count": len([r for r in results if r["status"] == "failed"]),
                "results": results
            }
        )
        
        logger.info(f"批量上传任务完成: {task_id}")
    
    except Exception as e:
        logger.error(f"批量上传任务失败 {task_id}: {e}")
        task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            completed_at=datetime.now().isoformat(),
            error_message=str(e)
        )


async def process_batch_ingest(
    task_id: str,
    texts: List[str],
    metadata: Optional[List[Dict]] = None
):
    """
    批量导入处理（后台任务）
    
    Args:
        task_id: 任务ID
        texts: 文本列表
        metadata: 元数据列表
    """
    try:
        task_store.update_task(
            task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now().isoformat()
        )
        
        results = []
        
        for idx, text in enumerate(texts):
            try:
                # TODO: 实际的导入逻辑
                await asyncio.sleep(0.05)  # 模拟处理
                
                doc_id = f"doc_{uuid.uuid4().hex[:8]}"
                results.append({
                    "text_preview": text[:50] + "..." if len(text) > 50 else text,
                    "status": "success",
                    "doc_id": doc_id
                })
                
                task_store.update_task(
                    task_id,
                    processed_items=idx + 1
                )
                
            except Exception as e:
                logger.error(f"导入文本失败: {e}")
                results.append({
                    "text_preview": text[:50],
                    "status": "failed",
                    "error": str(e)
                })
                task_store.update_task(
                    task_id,
                    failed_items=task_store.get_task(task_id).failed_items + 1,
                    processed_items=idx + 1
                )
        
        # 任务完成
        task_store.update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            completed_at=datetime.now().isoformat(),
            result={
                "success_count": len([r for r in results if r["status"] == "success"]),
                "failed_count": len([r for r in results if r["status"] == "failed"]),
                "results": results[:100]  # 限制结果数量
            }
        )
        
        logger.info(f"批量导入任务完成: {task_id}")
    
    except Exception as e:
        logger.error(f"批量导入任务失败 {task_id}: {e}")
        task_store.update_task(
            task_id,
            status=TaskStatus.FAILED,
            completed_at=datetime.now().isoformat(),
            error_message=str(e)
        )


# ==================== API端点 ====================

@router.post("/upload", response_model=Dict[str, Any])
async def batch_upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="上传的文件列表")
):
    """
    批量上传文件
    
    将多个文件作为后台任务进行处理
    
    Args:
        files: 上传的文件列表
    
    Returns:
        任务ID和初始状态
    """
    try:
        # 保存上传的文件（临时）
        file_paths = []
        temp_dir = Path("/tmp/ai-stack-uploads")
        temp_dir.mkdir(exist_ok=True)
        
        for file in files:
            file_path = temp_dir / f"{uuid.uuid4().hex}_{file.filename}"
            content = await file.read()
            file_path.write_bytes(content)
            file_paths.append(str(file_path))
        
        # 创建任务
        task_id = task_store.create_task("batch_upload", total_items=len(files))
        
        # 添加后台任务
        background_tasks.add_task(
            process_batch_upload,
            task_id,
            file_paths,
            {}
        )
        
        return {
            "task_id": task_id,
            "message": f"批量上传任务已创建，共{len(files)}个文件",
            "files": [f.filename for f in files],
            "status_url": f"/batch/tasks/{task_id}"
        }
    
    except Exception as e:
        logger.error(f"批量上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=Dict[str, Any])
async def batch_ingest_texts(
    background_tasks: BackgroundTasks,
    request: BatchIngestRequest
):
    """
    批量导入文本
    
    将多个文本作为后台任务导入到RAG系统
    
    Args:
        request: 批量导入请求
    
    Returns:
        任务ID和初始状态
    """
    try:
        # 创建任务
        task_id = task_store.create_task("batch_ingest", total_items=len(request.texts))
        
        # 添加后台任务
        background_tasks.add_task(
            process_batch_ingest,
            task_id,
            request.texts,
            request.metadata
        )
        
        return {
            "task_id": task_id,
            "message": f"批量导入任务已创建，共{len(request.texts)}条文本",
            "total_texts": len(request.texts),
            "status_url": f"/batch/tasks/{task_id}"
        }
    
    except Exception as e:
        logger.error(f"批量导入失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=BatchTask)
async def get_task_status(task_id: str):
    """
    获取任务状态
    
    查询批量任务的进度和结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务详细信息
    """
    try:
        task = task_store.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        return task
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[BatchTask])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[str] = None,
    limit: int = 50
):
    """
    列出批量任务
    
    查询所有批量任务（支持过滤）
    
    Args:
        status: 按状态过滤
        task_type: 按类型过滤
        limit: 最大返回数
    
    Returns:
        任务列表
    """
    try:
        tasks = task_store.list_tasks(status=status, task_type=task_type, limit=limit)
        return tasks
    
    except Exception as e:
        logger.error(f"列出任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def cancel_task(task_id: str):
    """
    取消任务
    
    取消正在运行或等待中的批量任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        操作结果
    """
    try:
        task = task_store.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise HTTPException(status_code=400, detail="任务已完成，无法取消")
        
        # 更新状态为已取消
        task_store.update_task(
            task_id,
            status=TaskStatus.CANCELLED,
            completed_at=datetime.now().isoformat()
        )
        
        return {
            "message": "任务已取消",
            "task_id": task_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_batch_statistics():
    """
    获取批量操作统计
    
    返回任务数量、成功率等统计信息
    
    Returns:
        统计数据
    """
    try:
        all_tasks = list(task_store.tasks.values())
        
        total = len(all_tasks)
        by_status = {}
        by_type = {}
        
        for task in all_tasks:
            # 按状态统计
            status = task.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            # 按类型统计
            task_type = task.task_type
            by_type[task_type] = by_type.get(task_type, 0) + 1
        
        # 成功率
        completed = by_status.get("completed", 0)
        failed = by_status.get("failed", 0)
        total_finished = completed + failed
        success_rate = (completed / max(total_finished, 1)) * 100
        
        return {
            "total_tasks": total,
            "by_status": by_status,
            "by_type": by_type,
            "success_rate": f"{success_rate:.1f}%",
            "completed_tasks": completed,
            "running_tasks": by_status.get("running", 0),
            "pending_tasks": by_status.get("pending", 0),
            "failed_tasks": failed
        }
    
    except Exception as e:
        logger.error(f"获取批量统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def batch_operations_health():
    """批量操作模块健康检查"""
    return {
        "status": "healthy",
        "module": "batch-operations",
        "version": "1.0.0",
        "task_store": "memory",
        "background_tasks": "enabled",
        "features": [
            "batch-file-upload",
            "batch-text-ingest",
            "background-processing",
            "progress-tracking",
            "task-management",
            "statistics"
        ]
    }


# ==================== 辅助端点 ====================

@router.post("/clear-completed")
async def clear_completed_tasks():
    """
    清理已完成的任务
    
    删除所有已完成和失败的任务记录
    
    Returns:
        清理结果
    """
    try:
        completed_tasks = [
            tid for tid, task in task_store.tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
        ]
        
        for task_id in completed_tasks:
            task_store.delete_task(task_id)
        
        return {
            "message": "已清理完成的任务",
            "cleared_count": len(completed_tasks),
            "remaining_count": len(task_store.tasks)
        }
    
    except Exception as e:
        logger.error(f"清理任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

