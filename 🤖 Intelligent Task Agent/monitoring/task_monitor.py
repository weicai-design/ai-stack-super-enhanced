"""
任务监控系统
负责任务的监控、性能跟踪、告警
"""

import psutil
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import deque
import logging

logger = logging.getLogger(__name__)


class TaskMonitor:
    """任务监控系统"""
    
    def __init__(self, db_session=None, alert_threshold=None):
        self.db_session = db_session
        self.alert_threshold = alert_threshold or {
            "cpu_percent": 80,
            "memory_percent": 80,
            "task_duration_multiplier": 2.0
        }
        
        # 监控数据缓存
        self.monitoring_data = {}
        self.performance_history = deque(maxlen=1000)
        self.alerts = []
        
        # 系统资源监控
        self.system_metrics = {
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total
        }
    
    async def on_task_started(self, execution_record: Dict[str, Any]):
        """任务开始时的回调"""
        execution_id = execution_record["execution_id"]
        
        logger.info(f"监控任务开始: {execution_id}")
        
        self.monitoring_data[execution_id] = {
            "execution_record": execution_record,
            "start_time": datetime.now(),
            "metrics_history": [],
            "alerts": [],
            "resource_snapshots": []
        }
        
        # 记录初始资源快照
        await self._record_resource_snapshot(execution_id)
    
    async def on_step_completed(
        self,
        execution_id: str,
        step: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """步骤完成时的回调"""
        if execution_id not in self.monitoring_data:
            return
        
        logger.debug(f"步骤完成: {execution_id} - {step['name']}")
        
        # 记录步骤指标
        step_metrics = {
            "timestamp": datetime.now().isoformat(),
            "step_name": step["name"],
            "step_order": step["order"],
            "duration": result.get("duration", 0),
            "success": result.get("success", False)
        }
        
        self.monitoring_data[execution_id]["metrics_history"].append(step_metrics)
        
        # 检查是否需要告警
        await self._check_step_alerts(execution_id, step, result)
        
        # 记录资源快照
        await self._record_resource_snapshot(execution_id)
    
    async def on_task_completed(self, execution_id: str, result: Dict[str, Any]):
        """任务完成时的回调"""
        if execution_id not in self.monitoring_data:
            return
        
        logger.info(f"监控任务完成: {execution_id}")
        
        monitoring_data = self.monitoring_data[execution_id]
        end_time = datetime.now()
        duration = (end_time - monitoring_data["start_time"]).total_seconds()
        
        # 计算性能指标
        performance_metrics = self._calculate_performance_metrics(
            monitoring_data,
            duration
        )
        
        # 保存到历史记录
        self.performance_history.append({
            "execution_id": execution_id,
            "task_name": result.get("task_id"),
            "completed_at": end_time.isoformat(),
            "duration": duration,
            "success": result.get("success", False),
            "metrics": performance_metrics
        })
        
        # 清理监控数据
        del self.monitoring_data[execution_id]
    
    async def on_task_failed(self, execution_id: str, result: Dict[str, Any]):
        """任务失败时的回调"""
        if execution_id not in self.monitoring_data:
            return
        
        logger.warning(f"监控任务失败: {execution_id}")
        
        # 生成失败告警
        alert = {
            "severity": "high",
            "type": "task_failed",
            "execution_id": execution_id,
            "message": f"任务执行失败: {result.get('error', '未知错误')}",
            "timestamp": datetime.now().isoformat()
        }
        
        self.alerts.append(alert)
        
        # 保存失败记录
        monitoring_data = self.monitoring_data[execution_id]
        end_time = datetime.now()
        duration = (end_time - monitoring_data["start_time"]).total_seconds()
        
        self.performance_history.append({
            "execution_id": execution_id,
            "task_name": result.get("task_id"),
            "failed_at": end_time.isoformat(),
            "duration": duration,
            "success": False,
            "error": result.get("error"),
            "alerts": monitoring_data.get("alerts", [])
        })
        
        # 清理监控数据
        del self.monitoring_data[execution_id]
    
    async def _record_resource_snapshot(self, execution_id: str):
        """记录资源快照"""
        if execution_id not in self.monitoring_data:
            return
        
        try:
            # 获取当前系统资源使用
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取网络IO
            net_io = psutil.net_io_counters()
            
            snapshot = {
                "timestamp": datetime.now().isoformat(),
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "memory_percent": memory.percent,
                "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                "disk_percent": disk.percent,
                "network_sent_mb": net_io.bytes_sent / (1024 * 1024),
                "network_recv_mb": net_io.bytes_recv / (1024 * 1024)
            }
            
            self.monitoring_data[execution_id]["resource_snapshots"].append(snapshot)
            
            # 检查资源告警
            await self._check_resource_alerts(execution_id, snapshot)
            
        except Exception as e:
            logger.warning(f"获取资源快照失败: {e}")
    
    async def _check_step_alerts(
        self,
        execution_id: str,
        step: Dict[str, Any],
        result: Dict[str, Any]
    ):
        """检查步骤告警"""
        monitoring_data = self.monitoring_data[execution_id]
        
        # 检查步骤执行时间
        duration = result.get("duration", 0)
        estimated_duration = step.get("estimated_duration", 0)
        
        if estimated_duration > 0 and duration > estimated_duration * self.alert_threshold["task_duration_multiplier"]:
            alert = {
                "severity": "medium",
                "type": "step_duration_exceeded",
                "execution_id": execution_id,
                "step_name": step["name"],
                "message": f"步骤执行时间超出预期 ({duration:.1f}s vs {estimated_duration}s)",
                "timestamp": datetime.now().isoformat()
            }
            
            monitoring_data["alerts"].append(alert)
            self.alerts.append(alert)
            logger.warning(alert["message"])
        
        # 检查步骤失败
        if not result.get("success", False):
            alert = {
                "severity": "high",
                "type": "step_failed",
                "execution_id": execution_id,
                "step_name": step["name"],
                "message": f"步骤执行失败: {result.get('error', '未知错误')}",
                "timestamp": datetime.now().isoformat()
            }
            
            monitoring_data["alerts"].append(alert)
            self.alerts.append(alert)
            logger.error(alert["message"])
    
    async def _check_resource_alerts(self, execution_id: str, snapshot: Dict[str, Any]):
        """检查资源告警"""
        monitoring_data = self.monitoring_data[execution_id]
        
        # 检查CPU使用率
        if snapshot["cpu_percent"] > self.alert_threshold["cpu_percent"]:
            alert = {
                "severity": "medium",
                "type": "high_cpu_usage",
                "execution_id": execution_id,
                "message": f"CPU使用率过高: {snapshot['cpu_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            }
            
            monitoring_data["alerts"].append(alert)
            self.alerts.append(alert)
        
        # 检查内存使用率
        if snapshot["memory_percent"] > self.alert_threshold["memory_percent"]:
            alert = {
                "severity": "medium",
                "type": "high_memory_usage",
                "execution_id": execution_id,
                "message": f"内存使用率过高: {snapshot['memory_percent']:.1f}%",
                "timestamp": datetime.now().isoformat()
            }
            
            monitoring_data["alerts"].append(alert)
            self.alerts.append(alert)
    
    def _calculate_performance_metrics(
        self,
        monitoring_data: Dict[str, Any],
        total_duration: float
    ) -> Dict[str, Any]:
        """计算性能指标"""
        metrics_history = monitoring_data["metrics_history"]
        resource_snapshots = monitoring_data["resource_snapshots"]
        
        if not metrics_history:
            return {}
        
        # 计算步骤平均耗时
        step_durations = [m["duration"] for m in metrics_history if "duration" in m]
        avg_step_duration = sum(step_durations) / len(step_durations) if step_durations else 0
        
        # 计算成功率
        successful_steps = sum(1 for m in metrics_history if m.get("success", False))
        success_rate = successful_steps / len(metrics_history) if metrics_history else 0
        
        # 计算资源使用统计
        if resource_snapshots:
            cpu_usages = [s["cpu_percent"] for s in resource_snapshots]
            memory_usages = [s["memory_used_mb"] for s in resource_snapshots]
            
            avg_cpu = sum(cpu_usages) / len(cpu_usages)
            max_cpu = max(cpu_usages)
            avg_memory = sum(memory_usages) / len(memory_usages)
            max_memory = max(memory_usages)
        else:
            avg_cpu = max_cpu = avg_memory = max_memory = 0
        
        return {
            "total_duration": total_duration,
            "avg_step_duration": avg_step_duration,
            "total_steps": len(metrics_history),
            "successful_steps": successful_steps,
            "success_rate": success_rate,
            "avg_cpu_percent": avg_cpu,
            "max_cpu_percent": max_cpu,
            "avg_memory_mb": avg_memory,
            "max_memory_mb": max_memory,
            "alert_count": len(monitoring_data.get("alerts", []))
        }
    
    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取活跃任务列表"""
        active_tasks = []
        
        for execution_id, data in self.monitoring_data.items():
            execution_record = data["execution_record"]
            current_time = datetime.now()
            duration = (current_time - data["start_time"]).total_seconds()
            
            # 获取最新资源快照
            latest_snapshot = data["resource_snapshots"][-1] if data["resource_snapshots"] else {}
            
            active_tasks.append({
                "execution_id": execution_id,
                "task_name": execution_record.get("task_name", "未知"),
                "status": execution_record.get("status", "unknown"),
                "progress": execution_record.get("progress", 0),
                "current_step": execution_record.get("current_step"),
                "duration": duration,
                "steps_completed": execution_record.get("steps_completed", 0),
                "total_steps": execution_record.get("total_steps", 0),
                "cpu_percent": latest_snapshot.get("cpu_percent", 0),
                "memory_percent": latest_snapshot.get("memory_percent", 0),
                "alert_count": len(data.get("alerts", []))
            })
        
        return active_tasks
    
    def get_recent_alerts(self, count: int = 10) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        return self.alerts[-count:]
    
    def get_performance_history(self, count: int = 50) -> List[Dict[str, Any]]:
        """获取性能历史"""
        return list(self.performance_history)[-count:]
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "count": self.system_metrics["cpu_count"],
                    "percent": cpu_percent,
                    "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
                },
                "memory": {
                    "total_gb": self.system_metrics["memory_total"] / (1024 ** 3),
                    "used_gb": memory.used / (1024 ** 3),
                    "available_gb": memory.available / (1024 ** 3),
                    "percent": memory.percent
                },
                "disk": {
                    "total_gb": disk.total / (1024 ** 3),
                    "used_gb": disk.used / (1024 ** 3),
                    "free_gb": disk.free / (1024 ** 3),
                    "percent": disk.percent
                },
                "active_tasks": len(self.monitoring_data)
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}
    
    def clear_old_alerts(self, hours: int = 24):
        """清理旧告警"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
        
        logger.info(f"清理了 {hours} 小时前的告警")

