#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
团队协作管理工具
支持代码审查、任务分配、知识库管理
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import smtplib
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import aiohttp
import yaml

logger = logging.getLogger(__name__)


class ReviewStatus(str, Enum):
    """代码审查状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """任务状态"""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class TeamMember:
    """团队成员"""
    member_id: str
    name: str
    email: str
    role: str
    skills: List[str] = field(default_factory=list)
    availability: float = 1.0  # 0-1 表示可用性
    current_tasks: int = 0
    max_tasks: int = 5


@dataclass
class CodeReview:
    """代码审查"""
    review_id: str
    pull_request_url: str
    title: str
    description: str
    author: str
    reviewers: List[str]
    status: ReviewStatus
    created_at: str
    updated_at: str
    comments: List[ReviewComment] = field(default_factory=list)
    files_changed: List[str] = field(default_factory=list)
    mergeable: bool = True


@dataclass
class ReviewComment:
    """审查评论"""
    comment_id: str
    reviewer: str
    content: str
    file_path: str
    line_number: int
    created_at: str
    resolved: bool = False
    severity: str = "info"  # info, warning, error


@dataclass
class TeamTask:
    """团队任务"""
    task_id: str
    title: str
    description: str
    assignee: str
    priority: TaskPriority
    status: TaskStatus
    estimated_hours: float
    actual_hours: float = 0.0
    created_at: str
    due_date: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    progress: float = 0.0
    blockers: List[str] = field(default_factory=list)


@dataclass
class KnowledgeArticle:
    """知识库文章"""
    article_id: str
    title: str
    content: str
    author: str
    category: str
    tags: List[str] = field(default_factory=list)
    created_at: str
    updated_at: str
    views: int = 0
    helpful_votes: int = 0
    status: str = "published"  # draft, published, archived


class NotificationChannel(ABC):
    """通知渠道接口"""
    
    @abstractmethod
    async def send_notification(self, recipient: str, message: str, subject: str = "") -> bool:
        """发送通知"""
        pass


class EmailNotification(NotificationChannel):
    """邮件通知"""
    
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send_notification(self, recipient: str, message: str, subject: str = "") -> bool:
        """发送邮件通知"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient
            msg['Subject'] = subject or "团队协作通知"
            
            msg.attach(MIMEText(message, 'html'))
            
            # 使用线程池执行同步操作
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_sync, recipient, msg)
            
            logger.info(f"邮件通知发送成功: {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"邮件通知发送失败: {e}")
            return False
    
    def _send_sync(self, recipient: str, msg: MIMEMultipart) -> None:
        """同步发送邮件"""
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)


class SlackNotification(NotificationChannel):
    """Slack通知"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def send_notification(self, recipient: str, message: str, subject: str = "") -> bool:
        """发送Slack通知"""
        try:
            payload = {
                "text": f"{subject}\n{message}",
                "channel": recipient
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack通知发送成功: {recipient}")
                        return True
                    else:
                        logger.error(f"Slack通知发送失败: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Slack通知发送失败: {e}")
            return False


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self) -> None:
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建团队成员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                member_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                skills TEXT,
                availability REAL DEFAULT 1.0,
                current_tasks INTEGER DEFAULT 0,
                max_tasks INTEGER DEFAULT 5
            )
        ''')
        
        # 创建任务表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                priority TEXT NOT NULL,
                status TEXT NOT NULL,
                estimated_hours REAL,
                actual_hours REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                due_date TEXT,
                dependencies TEXT,
                tags TEXT,
                progress REAL DEFAULT 0.0,
                blockers TEXT
            )
        ''')
        
        # 创建知识库表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                article_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                author TEXT NOT NULL,
                category TEXT NOT NULL,
                tags TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                views INTEGER DEFAULT 0,
                helpful_votes INTEGER DEFAULT 0,
                status TEXT DEFAULT 'published'
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_member(self, member: TeamMember) -> None:
        """保存团队成员"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO team_members 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            member.member_id, member.name, member.email, member.role,
            json.dumps(member.skills), member.availability,
            member.current_tasks, member.max_tasks
        ))
        
        conn.commit()
        conn.close()
    
    def get_member(self, member_id: str) -> Optional[TeamMember]:
        """获取团队成员"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM team_members WHERE member_id = ?', (member_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return TeamMember(
                member_id=row[0], name=row[1], email=row[2], role=row[3],
                skills=json.loads(row[4] or '[]'), availability=row[5],
                current_tasks=row[6], max_tasks=row[7]
            )
        return None
    
    def save_task(self, task: TeamTask) -> None:
        """保存任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO tasks 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            task.task_id, task.title, task.description, task.assignee,
            task.priority.value, task.status.value, task.estimated_hours,
            task.actual_hours, task.created_at, task.due_date,
            json.dumps(task.dependencies), json.dumps(task.tags),
            task.progress, json.dumps(task.blockers)
        ))
        
        conn.commit()
        conn.close()
    
    def get_tasks_by_assignee(self, assignee: str) -> List[TeamTask]:
        """获取成员的任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM tasks WHERE assignee = ?', (assignee,))
        rows = cursor.fetchall()
        conn.close()
        
        tasks = []
        for row in rows:
            tasks.append(TeamTask(
                task_id=row[0], title=row[1], description=row[2], assignee=row[3],
                priority=TaskPriority(row[4]), status=TaskStatus(row[5]),
                estimated_hours=row[6], actual_hours=row[7], created_at=row[8],
                due_date=row[9], dependencies=json.loads(row[10] or '[]'),
                tags=json.loads(row[11] or '[]'), progress=row[12],
                blockers=json.loads(row[13] or '[]')
            ))
        
        return tasks


class TeamCollaborationManager:
    """团队协作管理器"""
    
    def __init__(self, db_path: str, notification_channels: List[NotificationChannel] = None):
        self.db_manager = DatabaseManager(db_path)
        self.notification_channels = notification_channels or []
        self._task_lock = threading.Lock()
    
    def add_team_member(self, member: TeamMember) -> bool:
        """添加团队成员"""
        try:
            self.db_manager.save_member(member)
            logger.info(f"团队成员添加成功: {member.name}")
            return True
        except Exception as e:
            logger.error(f"添加团队成员失败: {e}")
            return False
    
    def create_task(self, task: TeamTask) -> bool:
        """创建任务"""
        try:
            with self._task_lock:
                # 检查分配成员是否存在
                member = self.db_manager.get_member(task.assignee)
                if not member:
                    logger.error(f"成员不存在: {task.assignee}")
                    return False
                
                # 检查成员是否超负荷
                if member.current_tasks >= member.max_tasks:
                    logger.warning(f"成员 {member.name} 任务已满")
                    return False
                
                self.db_manager.save_task(task)
                
                # 发送通知
                asyncio.create_task(self._send_task_notification(task, member))
                
                logger.info(f"任务创建成功: {task.title}")
                return True
                
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return False
    
    def assign_task(self, task_id: str, assignee: str) -> bool:
        """分配任务"""
        # 实现任务分配逻辑
        pass
    
    def update_task_progress(self, task_id: str, progress: float, notes: str = "") -> bool:
        """更新任务进度"""
        # 实现进度更新逻辑
        pass
    
    def get_team_workload(self) -> Dict[str, Any]:
        """获取团队工作负载"""
        # 实现工作负载分析
        pass
    
    def create_code_review(self, review: CodeReview) -> bool:
        """创建代码审查"""
        # 实现代码审查创建
        pass
    
    def add_review_comment(self, review_id: str, comment: ReviewComment) -> bool:
        """添加审查评论"""
        # 实现评论添加
        pass
    
    def complete_review(self, review_id: str, status: ReviewStatus) -> bool:
        """完成审查"""
        # 实现审查完成
        pass
    
    def add_knowledge_article(self, article: KnowledgeArticle) -> bool:
        """添加知识库文章"""
        # 实现知识库添加
        pass
    
    def search_knowledge(self, query: str, category: str = None) -> List[KnowledgeArticle]:
        """搜索知识库"""
        # 实现知识库搜索
        pass
    
    def generate_team_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """生成团队报告"""
        # 实现团队报告生成
        pass
    
    async def _send_task_notification(self, task: TeamTask, member: TeamMember) -> None:
        """发送任务通知"""
        message = f"""
        <h3>新任务分配</h3>
        <p><strong>任务标题:</strong> {task.title}</p>
        <p><strong>优先级:</strong> {task.priority.value}</p>
        <p><strong>预估时间:</strong> {task.estimated_hours} 小时</p>
        <p><strong>截止日期:</strong> {task.due_date or '未设置'}</p>
        <p><strong>描述:</strong> {task.description}</p>
        """
        
        subject = f"新任务: {task.title}"
        
        for channel in self.notification_channels:
            await channel.send_notification(member.email, message, subject)


class WorkflowAutomation:
    """工作流自动化"""
    
    def __init__(self, collaboration_manager: TeamCollaborationManager):
        self.collaboration_manager = collaboration_manager
    
    def automate_code_review_assignment(self, pull_request: Dict[str, Any]) -> bool:
        """自动化代码审查分配"""
        # 基于代码变更、成员技能等自动分配审查者
        pass
    
    def automate_task_prioritization(self) -> List[TeamTask]:
        """自动化任务优先级排序"""
        # 基于截止日期、依赖关系等自动排序任务
        pass
    
    def send_daily_standup_reminders(self) -> bool:
        """发送每日站会提醒"""
        # 发送站会进度提醒
        pass
    
    def generate_sprint_report(self, sprint_id: str) -> Dict[str, Any]:
        """生成迭代报告"""
        # 生成迭代进度报告
        pass


def main():
    """主函数"""
    # 示例用法
    db_path = "team_collaboration.db"
    manager = TeamCollaborationManager(db_path)
    
    # 添加团队成员
    member = TeamMember(
        member_id=str(uuid4()),
        name="张三",
        email="zhangsan@example.com",
        role="开发工程师",
        skills=["Python", "Docker", "Kubernetes"],
        availability=0.8
    )
    
    manager.add_team_member(member)
    
    # 创建任务
    task = TeamTask(
        task_id=str(uuid4()),
        title="实现用户认证模块",
        description="开发基于JWT的用户认证系统",
        assignee=member.member_id,
        priority=TaskPriority.HIGH,
        status=TaskStatus.TODO,
        estimated_hours=16.0,
        created_at=datetime.utcnow().isoformat(),
        due_date=(datetime.utcnow() + timedelta(days=7)).isoformat()
    )
    
    manager.create_task(task)
    
    print("团队协作管理工具初始化完成")


if __name__ == "__main__":
    main()