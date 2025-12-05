#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运维自动化工具
支持监控、部署、备份、恢复等运维操作
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import aiohttp
import psutil
import yaml

logger = logging.getLogger(__name__)


class OperationStatus(str, Enum):
    """操作状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(str, Enum):
    """资源类型"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    DATABASE = "database"
    APPLICATION = "application"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetric:
    """系统指标"""
    metric_id: str
    resource_type: ResourceType
    metric_name: str
    value: float
    unit: str
    timestamp: str
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class OperationTask:
    """运维任务"""
    task_id: str
    name: str
    description: str
    command: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: OperationStatus = OperationStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output: str = ""
    error: str = ""
    timeout: int = 300  # 秒
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class Alert:
    """告警"""
    alert_id: str
    title: str
    message: str
    level: AlertLevel
    resource_type: ResourceType
    metric_name: str
    threshold: float
    current_value: float
    triggered_at: str
    resolved_at: Optional[str] = None
    acknowledged: bool = False


@dataclass
class BackupConfig:
    """备份配置"""
    backup_id: str
    name: str
    source_path: str
    destination_path: str
    schedule: str  # cron表达式
    retention_days: int = 30
    compression: bool = True
    encryption: bool = False
    enabled: bool = True


@dataclass
class DeploymentConfig:
    """部署配置"""
    deployment_id: str
    name: str
    environment: str
    version: str
    deployment_strategy: str  # blue-green, canary, rolling
    health_check_url: str
    rollback_enabled: bool = True
    max_unavailable: int = 1
    max_surge: int = 1


class MetricCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    async def collect_metrics(self) -> List[SystemMetric]:
        """收集指标"""
        pass


class SystemMetricCollector(MetricCollector):
    """系统指标收集器"""
    
    async def collect_metrics(self) -> List[SystemMetric]:
        """收集系统指标"""
        metrics = []
        timestamp = datetime.utcnow().isoformat()
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics.append(SystemMetric(
            metric_id=str(uuid4()),
            resource_type=ResourceType.CPU,
            metric_name="cpu_usage",
            value=cpu_percent,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost"}
        ))
        
        # 内存使用率
        memory = psutil.virtual_memory()
        metrics.append(SystemMetric(
            metric_id=str(uuid4()),
            resource_type=ResourceType.MEMORY,
            metric_name="memory_usage",
            value=memory.percent,
            unit="percent",
            timestamp=timestamp,
            tags={"host": "localhost"}
        ))
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        metrics.append(SystemMetric(
            metric_id=str(uuid4()),
            resource_type=ResourceType.DISK,
            metric_name="disk_usage",
            value=(disk.used / disk.total) * 100,
            unit="percent",
            timestamp=timestamp,
            tags={"mount": "/", "host": "localhost"}
        ))
        
        # 网络IO
        net_io = psutil.net_io_counters()
        metrics.extend([
            SystemMetric(
                metric_id=str(uuid4()),
                resource_type=ResourceType.NETWORK,
                metric_name="network_bytes_sent",
                value=net_io.bytes_sent,
                unit="bytes",
                timestamp=timestamp,
                tags={"host": "localhost"}
            ),
            SystemMetric(
                metric_id=str(uuid4()),
                resource_type=ResourceType.NETWORK,
                metric_name="network_bytes_recv",
                value=net_io.bytes_recv,
                unit="bytes",
                timestamp=timestamp,
                tags={"host": "localhost"}
            )
        ])
        
        return metrics


class ApplicationMetricCollector(MetricCollector):
    """应用指标收集器"""
    
    def __init__(self, health_check_url: str):
        self.health_check_url = health_check_url
    
    async def collect_metrics(self) -> List[SystemMetric]:
        """收集应用指标"""
        metrics = []
        timestamp = datetime.utcnow().isoformat()
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                
                async with session.get(self.health_check_url, timeout=10) as response:
                    response_time = (time.time() - start_time) * 1000  # 毫秒
                    
                    metrics.append(SystemMetric(
                        metric_id=str(uuid4()),
                        resource_type=ResourceType.APPLICATION,
                        metric_name="response_time",
                        value=response_time,
                        unit="milliseconds",
                        timestamp=timestamp,
                        tags={"endpoint": "health_check"}
                    ))
                    
                    metrics.append(SystemMetric(
                        metric_id=str(uuid4()),
                        resource_type=ResourceType.APPLICATION,
                        metric_name="status_code",
                        value=response.status,
                        unit="count",
                        timestamp=timestamp,
                        tags={"endpoint": "health_check"}
                    ))
                    
                    # 检查应用健康状态
                    if response.status == 200:
                        health_data = await response.json()
                        if isinstance(health_data, dict):
                            # 解析健康检查返回的指标
                            for key, value in health_data.items():
                                if isinstance(value, (int, float)):
                                    metrics.append(SystemMetric(
                                        metric_id=str(uuid4()),
                                        resource_type=ResourceType.APPLICATION,
                                        metric_name=key,
                                        value=value,
                                        unit="count",
                                        timestamp=timestamp,
                                        tags={"component": "application"}
                                    ))
                    
        except Exception as e:
            logger.error(f"收集应用指标失败: {e}")
            
            # 应用不可用指标
            metrics.append(SystemMetric(
                metric_id=str(uuid4()),
                resource_type=ResourceType.APPLICATION,
                metric_name="available",
                value=0,
                unit="boolean",
                timestamp=timestamp,
                tags={"endpoint": "health_check", "error": str(e)}
            ))
        
        return metrics


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.thresholds = {
            "cpu_usage": {"warning": 80, "error": 90},
            "memory_usage": {"warning": 85, "error": 95},
            "disk_usage": {"warning": 80, "error": 90},
            "response_time": {"warning": 1000, "error": 5000}
        }
    
    def check_metrics(self, metrics: List[SystemMetric]) -> List[Alert]:
        """检查指标并生成告警"""
        new_alerts = []
        
        for metric in metrics:
            threshold = self.thresholds.get(metric.metric_name)
            if not threshold:
                continue
            
            alert_level = None
            if metric.value >= threshold.get("error", float('inf')):
                alert_level = AlertLevel.ERROR
            elif metric.value >= threshold.get("warning", float('inf')):
                alert_level = AlertLevel.WARNING
            
            if alert_level:
                alert = Alert(
                    alert_id=str(uuid4()),
                    title=f"{metric.resource_type.value} {metric.metric_name} 告警",
                    message=f"{metric.metric_name} 当前值: {metric.value}{metric.unit}, 阈值: {threshold}",
                    level=alert_level,
                    resource_type=metric.resource_type,
                    metric_name=metric.metric_name,
                    threshold=threshold.get(alert_level.value, 0),
                    current_value=metric.value,
                    triggered_at=datetime.utcnow().isoformat()
                )
                
                # 检查是否已有相同告警
                existing_alert = self._find_existing_alert(alert)
                if not existing_alert:
                    self.alerts[alert.alert_id] = alert
                    new_alerts.append(alert)
                
        return new_alerts
    
    def _find_existing_alert(self, alert: Alert) -> Optional[Alert]:
        """查找相同告警"""
        for existing_alert in self.alerts.values():
            if (existing_alert.metric_name == alert.metric_name and
                existing_alert.resource_type == alert.resource_type and
                not existing_alert.resolved_at):
                return existing_alert
        return None
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        if alert_id in self.alerts:
            self.alerts[alert_id].acknowledged = True
            return True
        return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        if alert_id in self.alerts:
            self.alerts[alert_id].resolved_at = datetime.utcnow().isoformat()
            return True
        return False


class BackupManager:
    """备份管理器"""
    
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(self, config: BackupConfig) -> bool:
        """创建备份"""
        try:
            source_path = Path(config.source_path)
            if not source_path.exists():
                logger.error(f"备份源路径不存在: {config.source_path}")
                return False
            
            # 创建备份文件名
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{config.name}_{timestamp}"
            
            if source_path.is_file():
                # 文件备份
                backup_path = self.backup_dir / f"{backup_filename}{source_path.suffix}"
                shutil.copy2(source_path, backup_path)
            else:
                # 目录备份
                backup_path = self.backup_dir / backup_filename
                shutil.copytree(source_path, backup_path)
            
            # 压缩备份
            if config.compression:
                compressed_path = self.backup_dir / f"{backup_filename}.tar.gz"
                shutil.make_archive(
                    str(compressed_path.with_suffix('')), 
                    'gztar', 
                    str(backup_path)
                )
                # 删除未压缩的备份
                if backup_path.is_file():
                    backup_path.unlink()
                else:
                    shutil.rmtree(backup_path)
            
            logger.info(f"备份创建成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建备份失败: {e}")
            return False
    
    async def cleanup_old_backups(self, config: BackupConfig) -> int:
        """清理旧备份"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=config.retention_days)
            deleted_count = 0
            
            for backup_file in self.backup_dir.glob(f"{config.name}_*"):
                # 解析文件名中的时间戳
                try:
                    timestamp_str = backup_file.stem.split('_')[-1]
                    file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                        logger.info(f"删除旧备份: {backup_file}")
                        
                except ValueError:
                    continue  # 跳过无法解析时间的文件
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
            return 0


class DeploymentManager:
    """部署管理器"""
    
    async def deploy_application(self, config: DeploymentConfig) -> bool:
        """部署应用"""
        try:
            logger.info(f"开始部署 {config.name} 版本 {config.version}")
            
            # 执行部署前检查
            if not await self._pre_deployment_check(config):
                logger.error("部署前检查失败")
                return False
            
            # 根据部署策略执行部署
            if config.deployment_strategy == "blue-green":
                success = await self._blue_green_deploy(config)
            elif config.deployment_strategy == "canary":
                success = await self._canary_deploy(config)
            else:
                success = await self._rolling_deploy(config)
            
            if success:
                logger.info(f"部署成功: {config.name}")
                # 执行部署后检查
                await self._post_deployment_check(config)
            else:
                logger.error(f"部署失败: {config.name}")
                if config.rollback_enabled:
                    await self._rollback_deployment(config)
            
            return success
            
        except Exception as e:
            logger.error(f"部署过程异常: {e}")
            if config.rollback_enabled:
                await self._rollback_deployment(config)
            return False
    
    async def _pre_deployment_check(self, config: DeploymentConfig) -> bool:
        """部署前检查"""
        # 检查依赖服务
        # 检查资源配置
        # 检查版本兼容性
        return True
    
    async def _blue_green_deploy(self, config: DeploymentConfig) -> bool:
        """蓝绿部署"""
        # 实现蓝绿部署逻辑
        logger.info("执行蓝绿部署")
        await asyncio.sleep(2)  # 模拟部署过程
        return True
    
    async def _canary_deploy(self, config: DeploymentConfig) -> bool:
        """金丝雀部署"""
        # 实现金丝雀部署逻辑
        logger.info("执行金丝雀部署")
        await asyncio.sleep(2)
        return True
    
    async def _rolling_deploy(self, config: DeploymentConfig) -> bool:
        """滚动部署"""
        # 实现滚动部署逻辑
        logger.info("执行滚动部署")
        await asyncio.sleep(2)
        return True
    
    async def _post_deployment_check(self, config: DeploymentConfig) -> bool:
        """部署后检查"""
        # 检查应用健康状态
        # 验证功能完整性
        return True
    
    async def _rollback_deployment(self, config: DeploymentConfig) -> bool:
        """回滚部署"""
        logger.info(f"开始回滚部署: {config.name}")
        await asyncio.sleep(1)
        logger.info("回滚完成")
        return True


class OperationsAutomation:
    """运维自动化主类"""
    
    def __init__(self, config_file: str = "ops_config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        
        self.metric_collectors: List[MetricCollector] = [
            SystemMetricCollector()
        ]
        
        if self.config.get('health_check_url'):
            self.metric_collectors.append(
                ApplicationMetricCollector(self.config['health_check_url'])
            )
        
        self.alert_manager = AlertManager()
        self.backup_manager = BackupManager()
        self.deployment_manager = DeploymentManager()
        
        self.metrics_history: List[SystemMetric] = []
        self.max_history_size = 10000
    
    async def start_monitoring(self, interval: int = 60) -> None:
        """开始监控"""
        logger.info(f"开始监控，间隔: {interval}秒")
        
        while True:
            try:
                # 收集指标
                all_metrics = []
                for collector in self.metric_collectors:
                    metrics = await collector.collect_metrics()
                    all_metrics.extend(metrics)
                
                # 保存指标历史
                self.metrics_history.extend(all_metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                # 检查告警
                new_alerts = self.alert_manager.check_metrics(all_metrics)
                for alert in new_alerts:
                    await self._handle_alert(alert)
                
                # 记录指标
                self._log_metrics(all_metrics)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(interval)
    
    async def execute_backup(self, backup_config: BackupConfig) -> bool:
        """执行备份"""
        return await self.backup_manager.create_backup(backup_config)
    
    async def execute_deployment(self, deployment_config: DeploymentConfig) -> bool:
        """执行部署"""
        return await self.deployment_manager.deploy_application(deployment_config)
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        if not self.metrics_history:
            return {"status": "unknown", "message": "无监控数据"}
        
        # 分析最近指标
        recent_metrics = self.metrics_history[-100:]  # 最近100个指标
        
        health_indicators = {}
        for metric in recent_metrics:
            if metric.metric_name in ['cpu_usage', 'memory_usage', 'disk_usage']:
                health_indicators[metric.metric_name] = metric.value
        
        # 评估健康状态
        critical_count = sum(1 for v in health_indicators.values() if v > 90)
        warning_count = sum(1 for v in health_indicators.values() if v > 80)
        
        if critical_count > 0:
            status = "critical"
        elif warning_count > 0:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "indicators": health_indicators,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        default_config = {
            "monitoring": {
                "interval": 60,
                "alert_channels": ["email", "slack"]
            },
            "backup": {
                "enabled": True,
                "schedule": "0 2 * * *"  # 每天凌晨2点
            },
            "deployment": {
                "strategy": "rolling",
                "health_check_timeout": 300
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    default_config.update(user_config or {})
            except Exception as e:
                logger.warning(f"加载配置文件失败: {e}")
        
        return default_config
    
    async def _handle_alert(self, alert: Alert) -> None:
        """处理告警"""
        logger.warning(f"告警触发: {alert.title} - {alert.message}")
        
        # 根据告警级别采取不同措施
        if alert.level == AlertLevel.CRITICAL:
            # 紧急处理：自动扩容、重启服务等
            await self._handle_critical_alert(alert)
        elif alert.level == AlertLevel.ERROR:
            # 错误处理：通知运维人员
            await self._notify_operations_team(alert)
        elif alert.level == AlertLevel.WARNING:
            # 警告处理：记录日志
            logger.info(f"警告处理: {alert.message}")
    
    async def _handle_critical_alert(self, alert: Alert) -> None:
        """处理严重告警"""
        # 根据资源类型采取不同措施
        if alert.resource_type == ResourceType.CPU:
            # CPU使用率过高，尝试重启服务
            await self._restart_service("ai-stack-app")
        elif alert.resource_type == ResourceType.MEMORY:
            # 内存使用率过高，清理缓存
            await self._clear_memory_cache()
    
    async def _notify_operations_team(self, alert: Alert) -> None:
        """通知运维团队"""
        # 实现通知逻辑（邮件、Slack等）
        logger.info(f"通知运维团队: {alert.title}")
    
    async def _restart_service(self, service_name: str) -> None:
        """重启服务"""
        try:
            # 使用系统命令重启服务
            result = subprocess.run(
                ["systemctl", "restart", service_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info(f"服务重启成功: {service_name}")
            else:
                logger.error(f"服务重启失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"重启服务异常: {e}")
    
    async def _clear_memory_cache(self) -> None:
        """清理内存缓存"""
        try:
            # 清理系统缓存
            subprocess.run(["sync"])  # 同步文件系统
            
            with open("/proc/sys/vm/drop_caches", "w") as f:
                f.write("3")  # 清理页缓存、目录项和inode
            
            logger.info("内存缓存清理完成")
            
        except Exception as e:
            logger.error(f"清理内存缓存失败: {e}")
    
    def _log_metrics(self, metrics: List[SystemMetric]) -> None:
        """记录指标"""
        # 可以保存到数据库或文件
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": [
                {
                    "name": m.metric_name,
                    "value": m.value,
                    "unit": m.unit
                }
                for m in metrics
            ]
        }
        
        # 简单记录到日志文件
        logger.debug(f"指标记录: {json.dumps(log_entry)}")


async def main():
    """主函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建运维自动化实例
    ops = OperationsAutomation()
    
    # 启动监控
    monitoring_task = asyncio.create_task(ops.start_monitoring(interval=30))
    
    # 示例：创建备份配置
    backup_config = BackupConfig(
        backup_id=str(uuid4()),
        name="database_backup",
        source_path="/var/lib/postgresql/data",
        destination_path="/backups",
        schedule="0 2 * * *"
    )
    
    # 示例：执行备份
    backup_success = await ops.execute_backup(backup_config)
    print(f"备份执行结果: {'成功' if backup_success else '失败'}")
    
    # 获取系统健康状态
    health_status = ops.get_system_health()
    print(f"系统健康状态: {health_status}")
    
    # 等待监控任务（在实际应用中应该持续运行）
    try:
        await asyncio.wait_for(monitoring_task, timeout=120)
    except asyncio.TimeoutError:
        print("监控任务运行完成")


if __name__ == "__main__":
    asyncio.run(main())