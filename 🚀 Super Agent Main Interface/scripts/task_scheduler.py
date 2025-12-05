#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务调度器（生产级实现）
5.3: Cron任务调度、任务管理、日志
"""

from __future__ import annotations

import os
import sys
import json
import logging
import asyncio
import subprocess
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
from croniter import croniter

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    description: str
    cron_expression: str  # Cron表达式
    command: str  # 执行的命令或脚本
    enabled: bool = True
    last_run_time: Optional[datetime] = None
    next_run_time: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    timeout: int = 3600  # 超时时间（秒）
    retry_on_failure: bool = False
    max_retries: int = 3
    retry_delay: int = 60  # 重试延迟（秒）
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExecution:
    """任务执行记录"""
    execution_id: str
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    exit_code: Optional[int] = None
    output: str = ""
    error: str = ""
    duration: Optional[float] = None


class TaskScheduler:
    """
    任务调度器（生产级实现）
    
    功能：
    1. Cron表达式解析
    2. 任务注册和管理
    3. 任务执行
    4. 任务日志
    5. 错误处理和重试
    """
    
    def __init__(self, config_file: Optional[Path] = None, log_dir: Optional[Path] = None):
        """
        初始化任务调度器
        
        Args:
            config_file: 任务配置文件路径
            log_dir: 日志目录
        """
        self.config_file = config_file or Path("config/tasks.json")
        self.log_dir = log_dir or Path("logs/tasks")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 任务存储
        self.tasks: Dict[str, ScheduledTask] = {}
        self.executions: List[TaskExecution] = []
        self.max_execution_history = 1000
        
        # 调度状态
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        
        # 加载任务配置
        self._load_tasks()
        
        logger.info(f"任务调度器初始化完成，任务数: {len(self.tasks)}")
    
    def _load_tasks(self):
        """加载任务配置"""
        if not self.config_file.exists():
            logger.warning(f"任务配置文件不存在: {self.config_file}")
            return
        
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for task_data in data.get("tasks", []):
                task = ScheduledTask(**task_data)
                # 计算下次运行时间
                task.next_run_time = self._calculate_next_run_time(task.cron_expression)
                self.tasks[task.task_id] = task
            
            logger.info(f"加载任务配置: {len(self.tasks)}个任务")
        except Exception as e:
            logger.error(f"加载任务配置失败: {e}", exc_info=True)
    
    def _save_tasks(self):
        """保存任务配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "tasks": [asdict(task) for task in self.tasks.values()],
                "updated_at": datetime.now().isoformat(),
            }
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务配置失败: {e}", exc_info=True)
    
    def _calculate_next_run_time(self, cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
        """
        计算下次运行时间
        
        Args:
            cron_expression: Cron表达式
            base_time: 基准时间（如果为None，使用当前时间）
            
        Returns:
            下次运行时间
        """
        if base_time is None:
            base_time = datetime.now()
        
        try:
            cron = croniter(cron_expression, base_time)
            return cron.get_next(datetime)
        except Exception as e:
            logger.error(f"计算下次运行时间失败: {cron_expression} - {e}")
            return base_time + timedelta(hours=1)
    
    def register_task(
        self,
        task_id: str,
        name: str,
        cron_expression: str,
        command: str,
        description: str = "",
        **kwargs
    ) -> ScheduledTask:
        """
        注册任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            cron_expression: Cron表达式
            command: 执行的命令
            description: 任务描述
            **kwargs: 其他任务参数
            
        Returns:
            任务对象
        """
        # 验证Cron表达式
        try:
            croniter(cron_expression)
        except Exception as e:
            raise ValueError(f"无效的Cron表达式: {cron_expression} - {e}")
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            description=description,
            cron_expression=cron_expression,
            command=command,
            next_run_time=self._calculate_next_run_time(cron_expression),
            **kwargs
        )
        
        self.tasks[task_id] = task
        self._save_tasks()
        
        logger.info(f"注册任务: {task_id} - {name}")
        
        return task
    
    def unregister_task(self, task_id: str) -> bool:
        """取消注册任务"""
        if task_id not in self.tasks:
            return False
        
        del self.tasks[task_id]
        self._save_tasks()
        
        logger.info(f"取消注册任务: {task_id}")
        
        return True
    
    def enable_task(self, task_id: str) -> bool:
        """启用任务"""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = True
        self._save_tasks()
        
        logger.info(f"启用任务: {task_id}")
        
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """禁用任务"""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = False
        self._save_tasks()
        
        logger.info(f"禁用任务: {task_id}")
        
        return True
    
    async def execute_task(self, task: ScheduledTask) -> TaskExecution:
        """
        执行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行记录
        """
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d%H%M%S')}_{task.task_id}"
        execution = TaskExecution(
            execution_id=execution_id,
            task_id=task.task_id,
            start_time=datetime.now(),
            status=TaskStatus.RUNNING,
        )
        
        self.executions.append(execution)
        
        # 限制执行历史数量
        if len(self.executions) > self.max_execution_history:
            self.executions = self.executions[-self.max_execution_history:]
        
        logger.info(f"执行任务: {task.task_id} - {task.name}")
        
        try:
            # 执行命令
            process = await asyncio.create_subprocess_shell(
                task.command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=task.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError(f"任务执行超时: {task.timeout}秒")
            
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.output = stdout.decode("utf-8", errors="ignore")
            execution.error = stderr.decode("utf-8", errors="ignore")
            execution.exit_code = process.returncode
            
            if process.returncode == 0:
                execution.status = TaskStatus.COMPLETED
                task.success_count += 1
                logger.info(f"任务执行成功: {task.task_id}")
            else:
                execution.status = TaskStatus.FAILED
                task.failure_count += 1
                logger.error(f"任务执行失败: {task.task_id}, 退出码: {process.returncode}")
        
        except TimeoutError as e:
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.exit_code = -1
            task.failure_count += 1
            logger.error(f"任务执行超时: {task.task_id}")
        
        except Exception as e:
            execution.end_time = datetime.now()
            execution.duration = (execution.end_time - execution.start_time).total_seconds()
            execution.status = TaskStatus.FAILED
            execution.error = str(e)
            execution.exit_code = -1
            task.failure_count += 1
            logger.error(f"任务执行异常: {task.task_id} - {e}", exc_info=True)
        
        finally:
            # 更新任务统计
            task.last_run_time = execution.start_time
            task.next_run_time = self._calculate_next_run_time(
                task.cron_expression,
                execution.start_time
            )
            task.run_count += 1
            self._save_tasks()
            
            # 保存执行日志
            self._save_execution_log(execution)
        
        return execution
    
    def _save_execution_log(self, execution: TaskExecution):
        """保存执行日志"""
        try:
            log_file = self.log_dir / f"{execution.task_id}_{execution.execution_id}.log"
            
            log_data = {
                "execution_id": execution.execution_id,
                "task_id": execution.task_id,
                "start_time": execution.start_time.isoformat(),
                "end_time": execution.end_time.isoformat() if execution.end_time else None,
                "status": execution.status.value,
                "exit_code": execution.exit_code,
                "duration": execution.duration,
                "output": execution.output,
                "error": execution.error,
            }
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存执行日志失败: {e}", exc_info=True)
    
    async def _scheduler_loop(self):
        """调度循环"""
        logger.info("任务调度循环已启动")
        
        while self.is_running:
            try:
                now = datetime.now()
                
                # 检查需要执行的任务
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    if task.next_run_time and now >= task.next_run_time:
                        # 执行任务
                        execution = await self.execute_task(task)
                        
                        # 如果失败且启用重试
                        if execution.status == TaskStatus.FAILED and task.retry_on_failure:
                            await self._retry_task(task, execution)
                
                # 等待1分钟后再次检查
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"调度循环错误: {e}", exc_info=True)
                await asyncio.sleep(60)
        
        logger.info("任务调度循环已停止")
    
    async def _retry_task(self, task: ScheduledTask, failed_execution: TaskExecution):
        """重试任务"""
        retry_count = failed_execution.metadata.get("retry_count", 0)
        
        if retry_count >= task.max_retries:
            logger.warning(f"任务重试次数已达上限: {task.task_id}")
            return
        
        logger.info(f"重试任务: {task.task_id}, 重试次数: {retry_count + 1}/{task.max_retries}")
        
        # 等待重试延迟
        await asyncio.sleep(task.retry_delay)
        
        # 执行重试
        retry_execution = await self.execute_task(task)
        retry_execution.metadata["retry_count"] = retry_count + 1
        retry_execution.metadata["original_execution_id"] = failed_execution.execution_id
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return
        
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("任务调度器已启动")
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("任务调度器已停止")
    
    def get_task_status(self, task_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID（如果为None，返回所有任务状态）
            
        Returns:
            任务状态信息
        """
        if task_id:
            if task_id not in self.tasks:
                return {"error": "任务不存在"}
            
            task = self.tasks[task_id]
            recent_executions = [
                asdict(exec) for exec in self.executions
                if exec.task_id == task_id
            ][-10:]  # 最近10次执行
            
            return {
                "task": asdict(task),
                "recent_executions": recent_executions,
            }
        else:
            return {
                "tasks": [asdict(task) for task in self.tasks.values()],
                "total_tasks": len(self.tasks),
                "enabled_tasks": sum(1 for t in self.tasks.values() if t.enabled),
            }
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """列出所有任务"""
        return [asdict(task) for task in self.tasks.values()]
    
    def get_execution_history(self, task_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取执行历史
        
        Args:
            task_id: 任务ID（如果为None，返回所有任务的历史）
            limit: 返回数量限制
            
        Returns:
            执行历史列表
        """
        executions = self.executions
        
        if task_id:
            executions = [exec for exec in executions if exec.task_id == task_id]
        
        executions.sort(key=lambda x: x.start_time, reverse=True)
        
        return [asdict(exec) for exec in executions[:limit]]


# 单例实例
_scheduler_instance: Optional[TaskScheduler] = None


def get_task_scheduler() -> TaskScheduler:
    """获取任务调度器实例（单例模式）"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = TaskScheduler()
    
    return _scheduler_instance


async def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="任务调度器")
    parser.add_argument("--config", help="任务配置文件路径")
    parser.add_argument("--log-dir", help="日志目录路径")
    parser.add_argument("--daemon", action="store_true", help="以守护进程模式运行")
    
    args = parser.parse_args()
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建调度器
    config_file = Path(args.config) if args.config else None
    log_dir = Path(args.log_dir) if args.log_dir else None
    
    scheduler = TaskScheduler(config_file=config_file, log_dir=log_dir)
    
    # 启动调度器
    await scheduler.start()
    
    try:
        if args.daemon:
            # 守护进程模式：持续运行
            while True:
                await asyncio.sleep(60)
        else:
            # 交互模式：运行一段时间后退出
            await asyncio.sleep(3600)  # 运行1小时
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())

