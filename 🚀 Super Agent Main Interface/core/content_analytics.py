#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容运营分析闭环
功能：内容发布后的数据追踪、分析、优化建议
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ContentAnalytics:
    """
    内容运营分析闭环
    追踪内容发布后的表现，提供优化建议
    """
    
    def __init__(self):
        """初始化分析器"""
        self.content_records: Dict[str, Dict[str, Any]] = {}
        self.performance_metrics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.optimization_suggestions: Dict[str, List[str]] = {}
    
    def record_publication(
        self,
        content_id: str,
        platform: str,
        title: str,
        tags: List[str],
        published_at: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        记录内容发布
        
        Args:
            content_id: 内容ID
            platform: 平台（douyin/xiaohongshu等）
            title: 标题
            tags: 标签
            published_at: 发布时间
            metadata: 元数据
            
        Returns:
            记录结果
        """
        record = {
            "content_id": content_id,
            "platform": platform,
            "title": title,
            "tags": tags,
            "published_at": published_at.isoformat(),
            "metadata": metadata or {},
            "stats": {
                "views": 0,
                "likes": 0,
                "comments": 0,
                "shares": 0,
                "followers_gained": 0,
            },
            "last_updated": published_at.isoformat(),
        }
        
        self.content_records[content_id] = record
        return record
    
    def update_stats(
        self,
        content_id: str,
        stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新内容统计数据
        
        Args:
            content_id: 内容ID
            stats: 统计数据
            
        Returns:
            更新结果
        """
        if content_id not in self.content_records:
            return {"success": False, "error": "内容不存在"}
        
        record = self.content_records[content_id]
        record["stats"].update(stats)
        record["last_updated"] = datetime.now().isoformat()
        
        # 记录历史数据点
        self.performance_metrics[content_id].append({
            "timestamp": datetime.now().isoformat(),
            "stats": stats.copy()
        })
        
        # 生成优化建议
        suggestions = self._generate_suggestions(content_id, record)
        self.optimization_suggestions[content_id] = suggestions
        
        return {
            "success": True,
            "content_id": content_id,
            "stats": record["stats"],
            "suggestions": suggestions
        }
    
    def get_analytics(
        self,
        content_id: Optional[str] = None,
        platform: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取分析报告
        
        Args:
            content_id: 内容ID（None表示所有）
            platform: 平台筛选
            days: 时间范围（天）
            
        Returns:
            分析报告
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        if content_id:
            records = [self.content_records.get(content_id)] if content_id in self.content_records else []
        else:
            records = [
                r for r in self.content_records.values()
                if datetime.fromisoformat(r["published_at"]) >= cutoff
            ]
        
        if platform:
            records = [r for r in records if r["platform"] == platform]
        
        if not records:
            return {
                "success": True,
                "total": 0,
                "analytics": {}
            }
        
        # 计算总体指标
        total_views = sum(r["stats"]["views"] for r in records)
        total_likes = sum(r["stats"]["likes"] for r in records)
        total_comments = sum(r["stats"]["comments"] for r in records)
        total_shares = sum(r["stats"]["shares"] for r in records)
        
        # 计算平均指标
        avg_engagement_rate = (
            (total_likes + total_comments + total_shares) / total_views * 100
            if total_views > 0 else 0.0
        )
        
        # 找出表现最好和最差的内容
        best_content = max(records, key=lambda r: r["stats"]["views"])
        worst_content = min(records, key=lambda r: r["stats"]["views"])
        
        # 标签分析
        tag_performance = defaultdict(lambda: {"count": 0, "total_views": 0, "total_likes": 0})
        for r in records:
            for tag in r["tags"]:
                tag_performance[tag]["count"] += 1
                tag_performance[tag]["total_views"] += r["stats"]["views"]
                tag_performance[tag]["total_likes"] += r["stats"]["likes"]
        
        # 计算标签平均表现
        tag_avg = {}
        for tag, perf in tag_performance.items():
            tag_avg[tag] = {
                "usage_count": perf["count"],
                "avg_views": perf["total_views"] / perf["count"] if perf["count"] > 0 else 0,
                "avg_likes": perf["total_likes"] / perf["count"] if perf["count"] > 0 else 0,
            }
        
        return {
            "success": True,
            "period": {
                "days": days,
                "start": cutoff.isoformat(),
                "end": datetime.now().isoformat()
            },
            "total": len(records),
            "summary": {
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "avg_engagement_rate": round(avg_engagement_rate, 2),
            },
            "best_content": {
                "content_id": best_content["content_id"],
                "title": best_content["title"],
                "views": best_content["stats"]["views"],
                "engagement_rate": round(
                    (best_content["stats"]["likes"] + best_content["stats"]["comments"] + best_content["stats"]["shares"])
                    / best_content["stats"]["views"] * 100 if best_content["stats"]["views"] > 0 else 0,
                    2
                )
            },
            "worst_content": {
                "content_id": worst_content["content_id"],
                "title": worst_content["title"],
                "views": worst_content["stats"]["views"],
            },
            "tag_performance": tag_avg,
            "optimization_suggestions": self._generate_global_suggestions(records, tag_avg),
        }
    
    def _generate_suggestions(
        self,
        content_id: str,
        record: Dict[str, Any]
    ) -> List[str]:
        """生成单个内容的优化建议"""
        suggestions = []
        stats = record["stats"]
        
        # 基于互动率
        if stats["views"] > 0:
            engagement_rate = (stats["likes"] + stats["comments"] + stats["shares"]) / stats["views"] * 100
            if engagement_rate < 2.0:
                suggestions.append("互动率较低，建议优化标题和封面图，增加吸引力")
            elif engagement_rate > 10.0:
                suggestions.append("互动率优秀，可考虑增加类似内容或扩展话题")
        
        # 基于评论数
        if stats["views"] > 1000 and stats["comments"] < 10:
            suggestions.append("评论数偏少，建议在内容中设置互动问题，引导用户评论")
        
        # 基于分享数
        if stats["likes"] > 100 and stats["shares"] < 5:
            suggestions.append("分享数偏低，建议增加价值点，让用户愿意分享给朋友")
        
        return suggestions
    
    def _generate_global_suggestions(
        self,
        records: List[Dict[str, Any]],
        tag_performance: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """生成全局优化建议"""
        suggestions = []
        
        if not records:
            return suggestions
        
        # 标签建议
        if tag_performance:
            best_tag = max(tag_performance.items(), key=lambda x: x[1]["avg_views"])
            worst_tag = min(tag_performance.items(), key=lambda x: x[1]["avg_views"])
            
            suggestions.append(
                f"表现最佳标签：{best_tag[0]}（平均{best_tag[1]['avg_views']:.0f}次浏览），"
                f"建议增加使用频率"
            )
            suggestions.append(
                f"表现较差标签：{worst_tag[0]}（平均{worst_tag[1]['avg_views']:.0f}次浏览），"
                f"建议优化或减少使用"
            )
        
        # 发布时间建议
        hour_performance = defaultdict(lambda: {"count": 0, "total_views": 0})
        for r in records:
            pub_time = datetime.fromisoformat(r["published_at"])
            hour = pub_time.hour
            hour_performance[hour]["count"] += 1
            hour_performance[hour]["total_views"] += r["stats"]["views"]
        
        if hour_performance:
            best_hour = max(
                hour_performance.items(),
                key=lambda x: x[1]["total_views"] / x[1]["count"] if x[1]["count"] > 0 else 0
            )
            suggestions.append(
                f"最佳发布时间：{best_hour[0]}:00（平均{best_hour[1]['total_views']/best_hour[1]['count']:.0f}次浏览），"
                f"建议在此时间段发布"
            )
        
        return suggestions
    
    def get_content_timeline(
        self,
        content_id: str
    ) -> Dict[str, Any]:
        """获取内容生命周期时间线"""
        if content_id not in self.content_records:
            return {"success": False, "error": "内容不存在"}
        
        record = self.content_records[content_id]
        metrics = self.performance_metrics.get(content_id, [])
        
        timeline = [
            {
                "event": "published",
                "timestamp": record["published_at"],
                "description": f"内容发布到{record['platform']}",
                "stats": record["stats"].copy()
            }
        ]
        
        for metric in metrics:
            timeline.append({
                "event": "stats_updated",
                "timestamp": metric["timestamp"],
                "description": "统计数据更新",
                "stats": metric["stats"]
            })
        
        return {
            "success": True,
            "content_id": content_id,
            "timeline": sorted(timeline, key=lambda x: x["timestamp"]),
            "current_stats": record["stats"],
            "suggestions": self.optimization_suggestions.get(content_id, [])
        }


# 全局实例
content_analytics = ContentAnalytics()

