"""资源管理器"""
import logging
from typing import Dict, List
from collections import defaultdict
from .models import ResourceUsage, ResourceConfig, Alert

logger = logging.getLogger(__name__)

class ResourceManager:
    def __init__(self):
        self.configs: Dict[str, ResourceConfig] = {}
        self.alerts: List[Alert] = []
        logger.info("✅ 资源管理器已初始化")
    
    def get_usage(self) -> ResourceUsage:
        """获取当前资源使用情况"""
        # 实际应该调用系统API获取真实数据
        return ResourceUsage(cpu_percent=45.0, memory_percent=60.0, disk_percent=30.0)
    
    def set_config(self, tenant_id: str, config: ResourceConfig) -> ResourceConfig:
        config.tenant_id = tenant_id
        self.configs[tenant_id] = config
        return config
    
    def create_alert(self, alert: Alert) -> Alert:
        self.alerts.append(alert)
        return alert

resource_manager = ResourceManager()












