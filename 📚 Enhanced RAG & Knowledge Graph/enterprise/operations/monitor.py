"""
监控系统
Monitoring System

提供流程监控、问题收集、闭环管理

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .models import BusinessProcess, Issue, ProcessStatus

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """流程监控器"""
    
    def __init__(self):
        """初始化流程监控器"""
        logger.info("✅ 流程监控器已初始化")
    
    def check_process_health(
        self,
        process: BusinessProcess,
        max_duration_days: int = 30
    ) -> Dict[str, Any]:
        """
        检查流程健康状态
        
        Args:
            process: 业务流程
            max_duration_days: 最大允许周期（天）
        
        Returns:
            健康检查结果
        """
        issues = []
        health_score = 100.0
        
        # 检查是否超期
        if process.started_at:
            duration = (datetime.now() - process.started_at).days
            if duration > max_duration_days:
                issues.append({
                    "type": "timeout",
                    "severity": "high",
                    "message": f"流程运行超过{max_duration_days}天"
                })
                health_score -= 30
        
        # 检查是否阻塞
        if process.status == ProcessStatus.BLOCKED:
            issues.append({
                "type": "blocked",
                "severity": "critical",
                "message": "流程被阻塞"
            })
            health_score -= 50
        
        # 检查数据完整性
        if not process.data or len(process.data) < 3:
            issues.append({
                "type": "data_incomplete",
                "severity": "medium",
                "message": "流程数据不完整"
            })
            health_score -= 20
        
        return {
            "process_id": process.id,
            "health_score": max(health_score, 0),
            "status": "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical",
            "issues": issues
        }
    
    def detect_anomalies(
        self,
        processes: List[BusinessProcess]
    ) -> List[Dict[str, Any]]:
        """
        检测异常流程
        
        Args:
            processes: 流程列表
        
        Returns:
            异常列表
        """
        anomalies = []
        
        for process in processes:
            health = self.check_process_health(process)
            
            if health["health_score"] < 80:
                anomalies.append({
                    "process_id": process.id,
                    "process_name": process.name,
                    "health_score": health["health_score"],
                    "status": health["status"],
                    "issues": health["issues"]
                })
        
        return anomalies
    
    def collect_issues(
        self,
        tenant_id: str,
        processes: List[BusinessProcess]
    ) -> List[Issue]:
        """
        收集流程问题
        
        Args:
            tenant_id: 租户ID
            processes: 流程列表
        
        Returns:
            问题列表
        """
        issues = []
        
        # 检测异常
        anomalies = self.detect_anomalies(processes)
        
        for anomaly in anomalies:
            for issue_info in anomaly["issues"]:
                issue = Issue(
                    tenant_id=tenant_id,
                    process_id=anomaly["process_id"],
                    title=f"{anomaly['process_name']}: {issue_info['message']}",
                    description=f"类型: {issue_info['type']}",
                    severity=issue_info["severity"],
                    status="open"
                )
                issues.append(issue)
        
        return issues
    
    def track_issue_resolution(
        self,
        issue: Issue,
        resolution: str
    ) -> Issue:
        """
        跟踪问题解决
        
        Args:
            issue: 问题
            resolution: 解决方案
        
        Returns:
            更新后的问题
        """
        issue.status = "resolved"
        issue.resolution = resolution
        issue.resolved_at = datetime.now()
        
        logger.info(f"问题 {issue.id} 已解决: {resolution}")
        
        return issue
    
    def check_closed_loop(
        self,
        tenant_id: str,
        issues: List[Issue]
    ) -> Dict[str, Any]:
        """
        检查闭环管理状态
        
        Args:
            tenant_id: 租户ID
            issues: 问题列表
        
        Returns:
            闭环状态
        """
        total = len(issues)
        resolved = sum(1 for i in issues if i.status == "resolved")
        open_issues = total - resolved
        
        resolution_rate = (resolved / total * 100) if total > 0 else 100
        
        # 检查超期未解决的问题
        overdue_issues = []
        for issue in issues:
            if issue.status == "open":
                days_open = (datetime.now() - issue.created_at).days
                if days_open > 7:  # 超过7天未解决
                    overdue_issues.append({
                        "issue_id": issue.id,
                        "title": issue.title,
                        "days_open": days_open,
                        "severity": issue.severity
                    })
        
        return {
            "total_issues": total,
            "resolved_issues": resolved,
            "open_issues": open_issues,
            "overdue_issues": len(overdue_issues),
            "resolution_rate": resolution_rate,
            "closed_loop_status": "good" if resolution_rate >= 90 else "warning" if resolution_rate >= 70 else "poor",
            "overdue_details": overdue_issues
        }


# ==================== 导出 ====================

__all__ = [
    "ProcessMonitor",
    "BusinessStage"
]

















