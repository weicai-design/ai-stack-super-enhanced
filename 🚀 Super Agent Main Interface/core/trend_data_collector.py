#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势数据采集与处理可视化
功能：记录数据采集过程、处理步骤、可视化采集统计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TrendDataCollector:
    """
    趋势数据采集器
    记录数据采集和处理过程
    """
    
    def __init__(self):
        """初始化采集器"""
        self.collection_logs: List[Dict[str, Any]] = []
        self.processing_logs: List[Dict[str, Any]] = []
        self.source_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_collected": 0,
            "total_processed": 0,
            "success_count": 0,
            "error_count": 0,
            "last_collection": None,
            "avg_processing_time": 0.0,
        })
    
    def record_collection(
        self,
        source: str,
        data_type: str,
        count: int,
        status: str = "success",
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录数据采集
        
        Args:
            source: 数据源（policy/tech/industry/hot）
            data_type: 数据类型
            count: 采集数量
            status: 状态（success/error/partial）
            error: 错误信息（如果有）
            metadata: 元数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "data_type": data_type,
            "count": count,
            "status": status,
            "error": error,
            "metadata": metadata or {},
        }
        
        self.collection_logs.append(log_entry)
        self.collection_logs = self.collection_logs[-1000:]  # 保留最近1000条
        
        # 更新统计
        stats = self.source_stats[source]
        stats["total_collected"] += count
        if status == "success":
            stats["success_count"] += 1
        else:
            stats["error_count"] += 1
        stats["last_collection"] = log_entry["timestamp"]
    
    def record_processing(
        self,
        source: str,
        step: str,
        input_count: int,
        output_count: int,
        processing_time: float,
        status: str = "success",
        error: Optional[str] = None
    ):
        """
        记录数据处理
        
        Args:
            source: 数据源
            step: 处理步骤（clean/classify/summarize/analyze）
            input_count: 输入数量
            output_count: 输出数量
            processing_time: 处理时间（秒）
            status: 状态
            error: 错误信息
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "step": step,
            "input_count": input_count,
            "output_count": output_count,
            "processing_time": processing_time,
            "status": status,
            "error": error,
            "efficiency": round(output_count / input_count * 100, 2) if input_count > 0 else 0.0,
        }
        
        self.processing_logs.append(log_entry)
        self.processing_logs = self.processing_logs[-1000:]  # 保留最近1000条
        
        # 更新统计
        stats = self.source_stats[source]
        stats["total_processed"] += output_count
        
        # 更新平均处理时间
        recent_times = [
            log["processing_time"]
            for log in self.processing_logs[-10:]
            if log["source"] == source and log["status"] == "success"
        ]
        if recent_times:
            stats["avg_processing_time"] = round(sum(recent_times) / len(recent_times), 2)
    
    def get_collection_stats(
        self,
        source: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取采集统计
        
        Args:
            source: 数据源（None表示全部）
            days: 时间范围（天）
            
        Returns:
            采集统计
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # 筛选采集日志
        collection_logs = [
            log for log in self.collection_logs
            if datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]
        
        if source:
            collection_logs = [log for log in collection_logs if log["source"] == source]
        
        # 筛选处理日志
        processing_logs = [
            log for log in self.processing_logs
            if datetime.fromisoformat(log["timestamp"]) >= cutoff
        ]
        
        if source:
            processing_logs = [log for log in processing_logs if log["source"] == source]
        
        # 按数据源统计
        source_summary = {}
        for src in (source,) if source else set(log["source"] for log in collection_logs):
            src_logs = [log for log in collection_logs if log["source"] == src]
            src_processing = [log for log in processing_logs if log["source"] == src]
            
            total_collected = sum(log["count"] for log in src_logs)
            total_processed = sum(log["output_count"] for log in src_processing)
            success_rate = (
                len([log for log in src_logs if log["status"] == "success"]) / len(src_logs) * 100
                if src_logs else 0.0
            )
            
            source_summary[src] = {
                "total_collected": total_collected,
                "total_processed": total_processed,
                "success_rate": round(success_rate, 2),
                "collection_count": len(src_logs),
                "processing_count": len(src_processing),
                "avg_processing_time": self.source_stats[src]["avg_processing_time"],
            }
        
        # 按处理步骤统计
        step_summary = defaultdict(lambda: {
            "count": 0,
            "total_input": 0,
            "total_output": 0,
            "total_time": 0.0,
        })
        
        for log in processing_logs:
            step = log["step"]
            step_summary[step]["count"] += 1
            step_summary[step]["total_input"] += log["input_count"]
            step_summary[step]["total_output"] += log["output_count"]
            step_summary[step]["total_time"] += log["processing_time"]
        
        # 计算平均效率
        for step, stats in step_summary.items():
            if stats["count"] > 0:
                stats["avg_efficiency"] = round(
                    stats["total_output"] / stats["total_input"] * 100 if stats["total_input"] > 0 else 0.0,
                    2
                )
                stats["avg_time"] = round(stats["total_time"] / stats["count"], 2)
        
        return {
            "period": {
                "days": days,
                "start": cutoff.isoformat(),
                "end": datetime.now().isoformat()
            },
            "source_summary": source_summary,
            "step_summary": dict(step_summary),
            "total_collections": len(collection_logs),
            "total_processings": len(processing_logs),
        }
    
    def get_processing_pipeline(
        self,
        source: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        获取处理流水线可视化数据
        
        Args:
            source: 数据源（None表示全部）
            limit: 返回数量限制
            
        Returns:
            处理流水线数据
        """
        logs = self.processing_logs[-limit:]
        
        if source:
            logs = [log for log in logs if log["source"] == source]
        
        # 按时间排序
        logs.sort(key=lambda x: x["timestamp"])
        
        # 构建流水线视图
        pipeline = []
        current_batch = None
        
        for log in logs:
            if not current_batch or current_batch["source"] != log["source"]:
                if current_batch:
                    pipeline.append(current_batch)
                current_batch = {
                    "source": log["source"],
                    "timestamp": log["timestamp"],
                    "steps": [],
                }
            
            current_batch["steps"].append({
                "step": log["step"],
                "input_count": log["input_count"],
                "output_count": log["output_count"],
                "processing_time": log["processing_time"],
                "efficiency": log["efficiency"],
                "status": log["status"],
            })
        
        if current_batch:
            pipeline.append(current_batch)
        
        return {
            "pipeline": pipeline,
            "total_batches": len(pipeline),
        }


# 全局实例
trend_data_collector = TrendDataCollector()

