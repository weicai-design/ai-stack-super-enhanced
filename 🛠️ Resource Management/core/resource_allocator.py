"""
资源调配器
动态调配系统资源给各个服务
"""

import psutil
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ResourceAllocator:
    """资源调配器"""
    
    def __init__(self):
        # 服务资源配置
        self.service_configs = {
            "docker": {
                "priority": 10,  # 最高优先级
                "min_memory_gb": 2,
                "max_memory_gb": 8,
                "min_cpu_percent": 10,
                "max_cpu_percent": 50
            },
            "ollama": {
                "priority": 9,
                "min_memory_gb": 4,
                "max_memory_gb": 12,
                "min_cpu_percent": 20,
                "max_cpu_percent": 60
            },
            "open-webui": {
                "priority": 8,
                "min_memory_gb": 1,
                "max_memory_gb": 4,
                "min_cpu_percent": 5,
                "max_cpu_percent": 30
            },
            "rag-service": {
                "priority": 7,
                "min_memory_gb": 2,
                "max_memory_gb": 6,
                "min_cpu_percent": 10,
                "max_cpu_percent": 40
            },
            "erp-backend": {
                "priority": 6,
                "min_memory_gb": 1,
                "max_memory_gb": 3,
                "min_cpu_percent": 5,
                "max_cpu_percent": 25
            },
            "erp-frontend": {
                "priority": 6,
                "min_memory_gb": 0.5,
                "max_memory_gb": 2,
                "min_cpu_percent": 5,
                "max_cpu_percent": 20
            },
            "stock-service": {
                "priority": 5,
                "min_memory_gb": 1,
                "max_memory_gb": 3,
                "min_cpu_percent": 5,
                "max_cpu_percent": 25
            },
            "trend-service": {
                "priority": 5,
                "min_memory_gb": 1,
                "max_memory_gb": 3,
                "min_cpu_percent": 5,
                "max_cpu_percent": 25
            },
            "content-service": {
                "priority": 4,
                "min_memory_gb": 1,
                "max_memory_gb": 3,
                "min_cpu_percent": 5,
                "max_cpu_percent": 25
            },
            "task-agent": {
                "priority": 6,
                "min_memory_gb": 1,
                "max_memory_gb": 3,
                "min_cpu_percent": 5,
                "max_cpu_percent": 25
            }
        }
        
        # 当前资源分配
        self.current_allocation = {}
        
        logger.info("资源调配器初始化完成")
    
    def calculate_resource_allocation(
        self,
        available_memory_gb: float,
        available_cpu_percent: float,
        active_services: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """
        计算资源分配方案
        
        Args:
            available_memory_gb: 可用内存(GB)
            available_cpu_percent: 可用CPU百分比
            active_services: 活跃服务列表
            
        Returns:
            资源分配方案
        """
        allocation = {}
        
        # 按优先级排序服务
        sorted_services = sorted(
            active_services,
            key=lambda s: self.service_configs.get(s, {}).get("priority", 0),
            reverse=True
        )
        
        remaining_memory = available_memory_gb
        remaining_cpu = available_cpu_percent
        
        for service in sorted_services:
            config = self.service_configs.get(service, {})
            
            if not config:
                logger.warning(f"服务 {service} 没有配置信息")
                continue
            
            # 分配内存
            allocated_memory = min(
                config.get("max_memory_gb", 2),
                max(config.get("min_memory_gb", 0.5), remaining_memory * 0.3)
            )
            
            # 分配CPU
            allocated_cpu = min(
                config.get("max_cpu_percent", 20),
                max(config.get("min_cpu_percent", 5), remaining_cpu * 0.3)
            )
            
            allocation[service] = {
                "memory_gb": allocated_memory,
                "cpu_percent": allocated_cpu,
                "priority": config.get("priority", 5)
            }
            
            remaining_memory -= allocated_memory
            remaining_cpu -= allocated_cpu
            
            # 如果资源不足，记录警告
            if remaining_memory < 1 or remaining_cpu < 10:
                logger.warning(f"资源不足，可能影响后续服务: {service}")
        
        self.current_allocation = allocation
        
        return allocation
    
    def adjust_allocation_for_service(
        self,
        service_name: str,
        target_memory_gb: Optional[float] = None,
        target_cpu_percent: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        调整特定服务的资源分配
        
        Args:
            service_name: 服务名称
            target_memory_gb: 目标内存(GB)
            target_cpu_percent: 目标CPU百分比
            
        Returns:
            调整结果
        """
        config = self.service_configs.get(service_name, {})
        
        if not config:
            return {
                "success": False,
                "message": f"服务 {service_name} 不存在"
            }
        
        adjusted = {}
        
        # 调整内存
        if target_memory_gb is not None:
            if target_memory_gb < config.get("min_memory_gb", 0):
                adjusted["memory_gb"] = config.get("min_memory_gb", 0.5)
                adjusted["memory_warning"] = "内存不能低于最小值"
            elif target_memory_gb > config.get("max_memory_gb", 10):
                adjusted["memory_gb"] = config.get("max_memory_gb", 2)
                adjusted["memory_warning"] = "内存不能超过最大值"
            else:
                adjusted["memory_gb"] = target_memory_gb
        
        # 调整CPU
        if target_cpu_percent is not None:
            if target_cpu_percent < config.get("min_cpu_percent", 0):
                adjusted["cpu_percent"] = config.get("min_cpu_percent", 5)
                adjusted["cpu_warning"] = "CPU不能低于最小值"
            elif target_cpu_percent > config.get("max_cpu_percent", 100):
                adjusted["cpu_percent"] = config.get("max_cpu_percent", 50)
                adjusted["cpu_warning"] = "CPU不能超过最大值"
            else:
                adjusted["cpu_percent"] = target_cpu_percent
        
        # 更新当前分配
        if service_name in self.current_allocation:
            self.current_allocation[service_name].update(adjusted)
        
        return {
            "success": True,
            "service": service_name,
            "adjusted": adjusted
        }
    
    def get_allocation_recommendation(
        self,
        service_name: str,
        current_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        获取资源分配建议
        
        Args:
            service_name: 服务名称
            current_usage: 当前使用情况
            
        Returns:
            分配建议
        """
        config = self.service_configs.get(service_name, {})
        current_memory = current_usage.get("memory_gb", 0)
        current_cpu = current_usage.get("cpu_percent", 0)
        
        recommendation = {
            "service": service_name,
            "current": current_usage,
            "suggestions": []
        }
        
        # 内存建议
        max_memory = config.get("max_memory_gb", 2)
        if current_memory > max_memory * 0.9:
            recommendation["suggestions"].append({
                "type": "memory",
                "action": "increase",
                "reason": "内存使用接近上限",
                "suggested_value": max_memory * 1.2
            })
        elif current_memory < config.get("min_memory_gb", 0.5) * 0.5:
            recommendation["suggestions"].append({
                "type": "memory",
                "action": "decrease",
                "reason": "内存使用过低，可以降低分配",
                "suggested_value": current_memory * 1.2
            })
        
        # CPU建议
        max_cpu = config.get("max_cpu_percent", 50)
        if current_cpu > max_cpu * 0.9:
            recommendation["suggestions"].append({
                "type": "cpu",
                "action": "increase",
                "reason": "CPU使用接近上限",
                "suggested_value": min(max_cpu * 1.2, 100)
            })
        elif current_cpu < config.get("min_cpu_percent", 5) * 0.5:
            recommendation["suggestions"].append({
                "type": "cpu",
                "action": "decrease",
                "reason": "CPU使用过低，可以降低分配",
                "suggested_value": current_cpu * 1.2
            })
        
        return recommendation
    
    def balance_resources(
        self,
        all_services_usage: Dict[str, Dict[str, float]]
    ) -> Dict[str, Any]:
        """
        平衡所有服务的资源分配
        
        Args:
            all_services_usage: 所有服务的资源使用情况
            
        Returns:
            平衡结果
        """
        adjustments = []
        
        # 找出资源使用过高的服务
        high_usage_services = []
        low_usage_services = []
        
        for service, usage in all_services_usage.items():
            config = self.service_configs.get(service, {})
            
            memory_ratio = usage.get("memory_gb", 0) / config.get("max_memory_gb", 2)
            cpu_ratio = usage.get("cpu_percent", 0) / config.get("max_cpu_percent", 50)
            
            if memory_ratio > 0.85 or cpu_ratio > 0.85:
                high_usage_services.append({
                    "service": service,
                    "memory_ratio": memory_ratio,
                    "cpu_ratio": cpu_ratio,
                    "priority": config.get("priority", 5)
                })
            elif memory_ratio < 0.3 and cpu_ratio < 0.3:
                low_usage_services.append({
                    "service": service,
                    "memory_ratio": memory_ratio,
                    "cpu_ratio": cpu_ratio,
                    "priority": config.get("priority", 5)
                })
        
        # 从低使用率服务转移资源到高使用率服务
        for high_service in sorted(high_usage_services, key=lambda x: x["priority"], reverse=True):
            for low_service in sorted(low_usage_services, key=lambda x: x["priority"]):
                if high_service["priority"] > low_service["priority"]:
                    adjustments.append({
                        "from": low_service["service"],
                        "to": high_service["service"],
                        "action": "transfer_resources",
                        "reason": f"优先级{high_service['priority']}的服务需要更多资源"
                    })
        
        return {
            "adjustments": adjustments,
            "high_usage_count": len(high_usage_services),
            "low_usage_count": len(low_usage_services)
        }
    
    def apply_resource_limits(
        self,
        service_name: str,
        memory_limit_gb: float,
        cpu_limit_percent: float
    ) -> Dict[str, Any]:
        """
        应用资源限制（通过Docker或系统命令）
        
        Args:
            service_name: 服务名称
            memory_limit_gb: 内存限制(GB)
            cpu_limit_percent: CPU限制百分比
            
        Returns:
            应用结果
        """
        try:
            # 这里可以通过Docker API或系统命令应用限制
            # 示例：使用Docker update命令
            
            memory_bytes = int(memory_limit_gb * 1024 * 1024 * 1024)
            cpu_quota = int(cpu_limit_percent * 1000)  # Docker CPU配额
            
            logger.info(f"为服务 {service_name} 应用资源限制: "
                       f"内存={memory_limit_gb}GB, CPU={cpu_limit_percent}%")
            
            # 实际应用时需要执行Docker命令
            # cmd = f"docker update --memory {memory_bytes} --cpu-quota {cpu_quota} {service_name}"
            # subprocess.run(cmd, shell=True, check=True)
            
            return {
                "success": True,
                "service": service_name,
                "memory_limit_gb": memory_limit_gb,
                "cpu_limit_percent": cpu_limit_percent,
                "message": "资源限制已应用（模拟）"
            }
            
        except Exception as e:
            logger.error(f"应用资源限制失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取服务配置"""
        return self.service_configs.get(service_name, {})
    
    def update_service_config(
        self,
        service_name: str,
        config_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新服务配置
        
        Args:
            service_name: 服务名称
            config_updates: 配置更新
            
        Returns:
            更新结果
        """
        if service_name not in self.service_configs:
            self.service_configs[service_name] = {}
        
        self.service_configs[service_name].update(config_updates)
        
        return {
            "success": True,
            "service": service_name,
            "updated_config": self.service_configs[service_name]
        }

