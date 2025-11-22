"""
运营分析系统
Operations Analytics

提供数据查询、统计分析、看板生成

版本: v1.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

from .models import BusinessProcess, Workflow, Issue, Dashboard, ProcessStatus

logger = logging.getLogger(__name__)


class OperationsAnalytics:
    """运营分析系统"""
    
    def __init__(self):
        """初始化运营分析系统"""
        logger.info("✅ 运营分析系统已初始化")
    
    def query_processes(
        self,
        tenant_id: str,
        processes: List[BusinessProcess],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[BusinessProcess]:
        """
        查询业务流程
        
        Args:
            tenant_id: 租户ID
            processes: 流程列表
            filters: 过滤条件
        
        Returns:
            过滤后的流程列表
        """
        result = [p for p in processes if p.tenant_id == tenant_id]
        
        if not filters:
            return result
        
        # 按状态过滤
        if "status" in filters:
            result = [p for p in result if p.status == filters["status"]]
        
        # 按日期范围过滤
        if "start_date" in filters:
            start_date = datetime.fromisoformat(filters["start_date"])
            result = [p for p in result if p.created_at >= start_date]
        
        if "end_date" in filters:
            end_date = datetime.fromisoformat(filters["end_date"])
            result = [p for p in result if p.created_at <= end_date]
        
        # 按名称搜索
        if "name" in filters:
            keyword = filters["name"].lower()
            result = [p for p in result if keyword in p.name.lower()]
        
        return result
    
    def generate_statistics(
        self,
        tenant_id: str,
        processes: List[BusinessProcess],
        period: str = "month"
    ) -> Dict[str, Any]:
        """
        生成统计分析
        
        Args:
            tenant_id: 租户ID
            processes: 流程列表
            period: 统计周期（day/week/month/quarter/year）
        
        Returns:
            统计数据
        """
        # 确定时间范围
        end_date = datetime.now()
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "quarter":
            start_date = end_date - timedelta(days=90)
        else:  # year
            start_date = end_date - timedelta(days=365)
        
        # 过滤时间范围内的流程
        period_processes = [
            p for p in processes
            if p.tenant_id == tenant_id and p.created_at >= start_date
        ]
        
        # 按状态统计
        status_stats = defaultdict(int)
        for process in period_processes:
            status_stats[process.status.value] += 1
        
        # 计算完成率
        completed = status_stats.get("completed", 0)
        total = len(period_processes)
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        # 计算平均周期
        completed_list = [
            p for p in period_processes
            if p.status == ProcessStatus.COMPLETED and p.started_at and p.completed_at
        ]
        
        avg_cycle = 0
        if completed_list:
            cycles = [(p.completed_at - p.started_at).days for p in completed_list]
            avg_cycle = sum(cycles) / len(cycles)
        
        return {
            "period": period,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_processes": total,
            "status_breakdown": dict(status_stats),
            "completion_rate": completion_rate,
            "avg_cycle_days": avg_cycle,
            "completed_count": completed,
            "in_progress_count": status_stats.get("in_progress", 0),
            "blocked_count": status_stats.get("blocked", 0)
        }
    
    def generate_dashboard(
        self,
        tenant_id: str,
        processes: List[BusinessProcess],
        issues: List[Issue]
    ) -> Dashboard:
        """
        生成运营看板
        
        Args:
            tenant_id: 租户ID
            processes: 流程列表
            issues: 问题列表
        
        Returns:
            运营看板
        """
        tenant_processes = [p for p in processes if p.tenant_id == tenant_id]
        tenant_issues = [i for i in issues if i.tenant_id == tenant_id]
        
        # 今日完成数
        today = date.today()
        completed_today = sum(
            1 for p in tenant_processes
            if p.status == ProcessStatus.COMPLETED
            and p.completed_at
            and p.completed_at.date() == today
        )
        
        # 活跃流程
        active_processes = sum(
            1 for p in tenant_processes
            if p.status == ProcessStatus.IN_PROGRESS
        )
        
        # 阻塞流程
        blocked_processes = sum(
            1 for p in tenant_processes
            if p.status == ProcessStatus.BLOCKED
        )
        
        # 未解决问题
        open_issues = sum(
            1 for i in tenant_issues
            if i.status == "open"
        )
        
        # KPI指标
        kpi_metrics = self.generate_statistics(tenant_id, processes, "month")
        
        return Dashboard(
            tenant_id=tenant_id,
            active_processes=active_processes,
            completed_today=completed_today,
            blocked_processes=blocked_processes,
            open_issues=open_issues,
            kpi_metrics=kpi_metrics
        )
    
    def generate_trend_chart(
        self,
        tenant_id: str,
        processes: List[BusinessProcess],
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        生成趋势图表数据
        
        Args:
            tenant_id: 租户ID
            processes: 流程列表
            days: 天数
        
        Returns:
            趋势数据
        """
        tenant_processes = [p for p in processes if p.tenant_id == tenant_id]
        
        # 按日期统计
        daily_stats = defaultdict(lambda: {"created": 0, "completed": 0})
        
        for process in tenant_processes:
            # 统计创建
            created_date = process.created_at.date()
            daily_stats[created_date]["created"] += 1
            
            # 统计完成
            if process.completed_at:
                completed_date = process.completed_at.date()
                daily_stats[completed_date]["completed"] += 1
        
        # 生成最近N天的数据
        trend_data = []
        for i in range(days):
            target_date = date.today() - timedelta(days=days - i - 1)
            stats = daily_stats.get(target_date, {"created": 0, "completed": 0})
            
            trend_data.append({
                "date": target_date.isoformat(),
                "created": stats["created"],
                "completed": stats["completed"]
            })
        
        return trend_data


# ==================== 导出 ====================

__all__ = [
    "ProcessMonitor",
    "OperationsAnalytics"
]

































