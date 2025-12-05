#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能任务系统与超级Agent集成模块
实现聊天框识别重要信息→备忘录→任务提炼→用户确认→执行的完整流程
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

from .task_planning import TaskPlanning
from .task_lifecycle_manager import TaskLifecycleManager, TaskStatus, TaskPriority
from .task_templates import TaskTemplateLibrary

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """聊天消息模型"""
    role: str  # user/assistant
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskExtractionResult:
    """任务提取结果"""
    has_tasks: bool
    tasks: List[Dict[str, Any]]
    confidence: float
    needs_confirmation: bool
    extracted_info: Dict[str, Any]


class TaskIntegrationSystem:
    """
    智能任务系统与超级Agent集成系统
    
    功能：
    1. 聊天消息智能识别
    2. 重要信息提取
    3. 自动创建备忘录
    4. 任务提炼和确认
    5. 任务执行和监控
    """
    
    def __init__(self, task_planning: TaskPlanning, lifecycle_manager: TaskLifecycleManager):
        self.task_planning = task_planning
        self.lifecycle_manager = lifecycle_manager
        
        # 任务识别关键词
        self.task_keywords = [
            # 中文任务关键词
            "需要", "应该", "记得", "要", "必须", "完成", "处理", "执行",
            "计划", "安排", "准备", "检查", "审核", "确认", "开发", "实现",
            "创建", "编写", "测试", "部署", "优化", "修复", "分析", "设计",
            "整理", "更新", "升级", "重构", "迁移", "集成", "打通", "连接",
            # 英文任务关键词
            "need", "should", "remember", "must", "complete", "handle", "execute",
            "plan", "arrange", "prepare", "check", "review", "confirm", "develop",
            "implement", "create", "write", "test", "deploy", "optimize", "fix",
            "analyze", "design", "organize", "update", "upgrade", "refactor", "migrate"
        ]
        
        # 时间表达式模式
        self.time_patterns = [
            r"(明天|后天|大后天|下周|下个月|下个季度|明年)",
            r"(\d{1,2}月\d{1,2}日|\d{1,2}日|\d{1,2}号)",
            r"(上午|下午|晚上|凌晨)\s*(\d{1,2})点",
            r"(\d{1,2}):(\d{2})",
            r"(today|tomorrow|next week|next month|next year)",
            r"(\d{1,2}/\d{1,2}/\d{4})",
            r"(\d{4}-\d{2}-\d{2})"
        ]
        
        # 优先级关键词
        self.priority_keywords = {
            "high": ["紧急", "重要", "优先", "马上", "立即", "urgent", "important", "priority"],
            "medium": ["一般", "中等", "常规", "normal", "medium"],
            "low": ["不紧急", "低优先级", "有空", "low", "not urgent"]
        }
        
        # 回调函数注册
        self.callbacks = {
            "on_task_extracted": [],
            "on_task_confirmed": [],
            "on_task_started": [],
            "on_task_completed": []
        }
    
    def register_callback(self, event: str, callback: Callable):
        """注册回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    async def _trigger_callbacks(self, event: str, data: Dict[str, Any]):
        """触发回调函数"""
        for callback in self.callbacks[event]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Callback error for event {event}: {e}")
    
    async def process_chat_message(self, message: ChatMessage) -> TaskExtractionResult:
        """
        处理聊天消息，提取任务信息
        
        Args:
            message: 聊天消息
            
        Returns:
            任务提取结果
        """
        logger.info(f"处理聊天消息: {message.content[:100]}...")
        
        # 1. 判断是否包含任务信息
        has_tasks = self._contains_task_info(message.content)
        
        if not has_tasks:
            return TaskExtractionResult(
                has_tasks=False,
                tasks=[],
                confidence=0.0,
                needs_confirmation=False,
                extracted_info={}
            )
        
        # 2. 提取任务信息
        extracted_info = self._extract_task_info(message.content)
        
        # 3. 创建临时备忘录
        memo_data = self._create_task_memo(message, extracted_info)
        
        # 4. 提炼任务
        tasks = await self._refine_tasks_from_memo(memo_data)
        
        # 5. 计算置信度
        confidence = self._calculate_extraction_confidence(message.content, extracted_info, tasks)
        
        # 6. 判断是否需要用户确认
        needs_confirmation = confidence < 0.8 or len(tasks) > 1
        
        result = TaskExtractionResult(
            has_tasks=True,
            tasks=tasks,
            confidence=confidence,
            needs_confirmation=needs_confirmation,
            extracted_info=extracted_info
        )
        
        # 触发任务提取回调
        await self._trigger_callbacks("on_task_extracted", {
            "message": message,
            "result": result
        })
        
        return result
    
    def _contains_task_info(self, content: str) -> bool:
        """判断内容是否包含任务信息"""
        # 检查是否包含任务关键词
        content_lower = content.lower()
        
        for keyword in self.task_keywords:
            if keyword in content_lower:
                return True
        
        # 检查是否包含时间表达式
        for pattern in self.time_patterns:
            if re.search(pattern, content):
                return True
        
        return False
    
    def _extract_task_info(self, content: str) -> Dict[str, Any]:
        """从内容中提取任务信息"""
        extracted = {
            "title": "",
            "description": content,
            "priority": "medium",
            "due_date": None,
            "estimated_duration": 60,  # 默认60分钟
            "tags": [],
            "dependencies": []
        }
        
        # 提取标题（第一句话或前50个字符）
        sentences = re.split(r'[。！？.!?]', content)
        if sentences:
            extracted["title"] = sentences[0].strip()[:50]
        
        # 提取优先级
        content_lower = content.lower()
        for priority, keywords in self.priority_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    extracted["priority"] = priority
                    break
            if extracted["priority"] != "medium":
                break
        
        # 提取时间信息
        for pattern in self.time_patterns:
            matches = re.findall(pattern, content)
            if matches:
                extracted["due_date"] = matches[0] if isinstance(matches[0], str) else "".join(matches[0])
                break
        
        # 提取标签（关键词）
        for keyword in self.task_keywords:
            if keyword in content_lower:
                extracted["tags"].append(keyword)
        
        return extracted
    
    def _create_task_memo(self, message: ChatMessage, extracted_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建任务备忘录"""
        return {
            "source": "chat_message",
            "message_id": f"msg_{int(message.timestamp.timestamp())}",
            "content": message.content,
            "extracted_info": extracted_info,
            "timestamp": message.timestamp,
            "metadata": message.metadata
        }
    
    async def _refine_tasks_from_memo(self, memo_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从备忘录中提炼任务"""
        try:
            # 使用任务规划器提炼任务
            tasks = await self.task_planning.refine_tasks_from_memo(memo_data)
            
            if not tasks:
                # 如果规划器没有返回任务，创建默认任务
                extracted_info = memo_data.get("extracted_info", {})
                task = {
                    "id": f"task_{int(datetime.now().timestamp())}",
                    "title": extracted_info.get("title", "未命名任务"),
                    "description": extracted_info.get("description", ""),
                    "priority": extracted_info.get("priority", "medium"),
                    "due_date": extracted_info.get("due_date"),
                    "estimated_duration": extracted_info.get("estimated_duration", 60),
                    "tags": extracted_info.get("tags", []),
                    "status": "pending",
                    "needs_confirmation": True
                }
                tasks = [task]
            
            return tasks
            
        except Exception as e:
            logger.error(f"从备忘录提炼任务失败: {e}")
            # 返回一个默认任务
            return [{
                "id": f"task_{int(datetime.now().timestamp())}",
                "title": "提取的任务",
                "description": memo_data.get("content", ""),
                "priority": "medium",
                "status": "pending",
                "needs_confirmation": True
            }]
    
    def _calculate_extraction_confidence(self, content: str, extracted_info: Dict[str, Any], tasks: List[Dict[str, Any]]) -> float:
        """计算任务提取置信度"""
        confidence = 0.0
        
        # 基于关键词数量
        keyword_count = len([k for k in self.task_keywords if k in content.lower()])
        confidence += min(keyword_count * 0.1, 0.3)
        
        # 基于时间表达式
        if extracted_info.get("due_date"):
            confidence += 0.2
        
        # 基于优先级识别
        if extracted_info.get("priority") != "medium":
            confidence += 0.1
        
        # 基于任务数量和质量
        if tasks:
            confidence += 0.2
            if len(tasks) == 1:
                confidence += 0.1
            if any(task.get("title") for task in tasks):
                confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def confirm_task(self, task_id: str, user_confirmation: bool = True) -> bool:
        """用户确认任务"""
        try:
            # 在实际系统中，这里应该更新任务状态
            logger.info(f"用户{'确认' if user_confirmation else '拒绝'}任务: {task_id}")
            
            if user_confirmation:
                # 触发任务确认回调
                await self._trigger_callbacks("on_task_confirmed", {
                    "task_id": task_id,
                    "confirmed": True
                })
            
            return True
            
        except Exception as e:
            logger.error(f"确认任务失败: {e}")
            return False
    
    async def execute_task(self, task_id: str) -> bool:
        """执行任务"""
        try:
            logger.info(f"开始执行任务: {task_id}")
            
            # 触发任务开始回调
            await self._trigger_callbacks("on_task_started", {
                "task_id": task_id,
                "start_time": datetime.now()
            })
            
            # 模拟任务执行（实际系统中应调用具体的执行逻辑）
            await asyncio.sleep(2)  # 模拟执行时间
            
            # 触发任务完成回调
            await self._trigger_callbacks("on_task_completed", {
                "task_id": task_id,
                "completion_time": datetime.now(),
                "success": True
            })
            
            logger.info(f"任务执行完成: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"执行任务失败: {e}")
            return False
    
    def get_task_keywords(self) -> List[str]:
        """获取任务关键词列表"""
        return self.task_keywords
    
    def get_time_patterns(self) -> List[str]:
        """获取时间表达式模式"""
        return self.time_patterns
    
    def get_priority_keywords(self) -> Dict[str, List[str]]:
        """获取优先级关键词"""
        return self.priority_keywords


# 全局实例管理
_task_integration_system: Optional[TaskIntegrationSystem] = None


def get_task_integration_system() -> TaskIntegrationSystem:
    """获取任务集成系统实例"""
    global _task_integration_system
    
    if _task_integration_system is None:
        # 初始化依赖组件
        task_planning = TaskPlanning()
        lifecycle_manager = TaskLifecycleManager()
        
        _task_integration_system = TaskIntegrationSystem(
            task_planning=task_planning,
            lifecycle_manager=lifecycle_manager
        )
        
        logger.info("✅ 任务集成系统初始化完成")
    
    return _task_integration_system