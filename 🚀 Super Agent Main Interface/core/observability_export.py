"""
可观测性数据导出
支持导出Trace数据用于分析
"""

import json
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ObservabilityExporter:
    """可观测性数据导出器"""
    
    def __init__(self, observability_system, persistence_system=None):
        """
        初始化导出器
        
        Args:
            observability_system: 可观测性系统实例
            persistence_system: 持久化系统实例（可选）
        """
        self.observability = observability_system
        self.persistence = persistence_system
    
    def export_trace_json(self, trace_id: str) -> Dict[str, Any]:
        """导出Trace为JSON格式"""
        trace = self.observability.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace不存在: {trace_id}")
        
        trace_dict = trace.to_dict()
        
        # 获取所有Spans
        spans = [span.to_dict() for span in trace.spans]
        trace_dict["spans"] = spans
        
        # 获取关联的事件
        events = self.observability.get_events(trace_id=trace_id, limit=1000)
        trace_dict["events"] = events
        
        return trace_dict
    
    def export_traces_json(
        self,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """导出多个Traces为JSON格式"""
        traces = []
        
        if self.persistence:
            # 从数据库获取
            db_traces = self.persistence.get_traces(start_time, end_time, limit)
            for db_trace in db_traces:
                trace_id = db_trace["trace_id"]
                trace = self.observability.get_trace(trace_id)
                if trace:
                    trace_dict = trace.to_dict()
                    traces.append(trace_dict)
        else:
            # 从内存获取活跃的Traces
            active_traces = self.observability.get_active_traces()
            for trace_info in active_traces[:limit]:
                trace = self.observability.get_trace(trace_info["trace_id"])
                if trace:
                    trace_dict = trace.to_dict()
                    traces.append(trace_dict)
        
        return traces
    
    def export_trace_csv(self, trace_id: str) -> str:
        """导出Trace为CSV格式"""
        trace = self.observability.get_trace(trace_id)
        if not trace:
            raise ValueError(f"Trace不存在: {trace_id}")
        
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入Trace信息
        writer.writerow(["Type", "ID", "Name", "Start Time", "End Time", "Duration", "Status", "Tags"])
        writer.writerow([
            "Trace",
            trace.trace_id,
            trace.service_name,
            datetime.fromtimestamp(trace.start_time).isoformat(),
            datetime.fromtimestamp(trace.end_time).isoformat() if trace.end_time else "",
            trace.duration or "",
            trace.status,
            json.dumps(trace.tags)
        ])
        
        # 写入Spans
        writer.writerow([])
        writer.writerow(["Spans"])
        writer.writerow(["Span ID", "Parent Span ID", "Name", "Type", "Start Time", "End Time", "Duration", "Status", "Error"])
        
        for span in trace.spans:
            writer.writerow([
                span.span_id,
                span.parent_span_id or "",
                span.name,
                span.type.value,
                datetime.fromtimestamp(span.start_time).isoformat(),
                datetime.fromtimestamp(span.end_time).isoformat() if span.end_time else "",
                span.duration or "",
                span.status.value,
                span.error or ""
            ])
        
        return output.getvalue()
    
    def export_metrics_csv(
        self,
        metric_name: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None
    ) -> str:
        """导出指标为CSV格式"""
        metrics = self.observability.get_metrics(
            name=metric_name,
            start_time=start_time,
            end_time=end_time
        )
        
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Name", "Value", "Timestamp", "Tags", "Metric Type"])
        
        for metric in metrics:
            writer.writerow([
                metric.name,
                metric.value,
                datetime.fromtimestamp(metric.timestamp).isoformat(),
                json.dumps(metric.tags),
                metric.metric_type
            ])
        
        return output.getvalue()
    
    def export_events_csv(
        self,
        event_name: Optional[str] = None,
        trace_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 1000
    ) -> str:
        """导出事件为CSV格式"""
        events = self.observability.get_events(
            event_name=event_name,
            trace_id=trace_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Event ID", "Event Name", "Timestamp", "Trace ID", "Span ID", "Properties", "Level"])
        
        for event in events:
            writer.writerow([
                event["event_id"],
                event["event_name"],
                datetime.fromtimestamp(event["timestamp"]).isoformat(),
                event.get("trace_id") or "",
                event.get("span_id") or "",
                json.dumps(event.get("properties", {})),
                event.get("level", "info")
            ])
        
        return output.getvalue()
    
    def export_long_task_replay_json(self, task_id: str) -> Dict[str, Any]:
        """导出长任务回放数据为JSON"""
        replay_data = self.observability.get_long_task_replay(task_id)
        if not replay_data:
            raise ValueError(f"任务不存在或没有回放数据: {task_id}")
        
        return replay_data
    
    def export_to_file(
        self,
        data: Any,
        file_path: str,
        format: str = "json"
    ):
        """
        导出数据到文件
        
        Args:
            data: 要导出的数据
            file_path: 文件路径
            format: 格式（json, csv）
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        elif format == "csv":
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(data)
        else:
            raise ValueError(f"不支持的格式: {format}")
        
        logger.info(f"数据已导出到: {file_path}")














