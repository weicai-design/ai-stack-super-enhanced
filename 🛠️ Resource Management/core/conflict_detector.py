"""
资源冲突检测器
检测服务间的资源冲突并提供解决方案
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConflictDetector:
    """资源冲突检测器"""
    
    def __init__(self, resource_monitor, resource_allocator):
        self.resource_monitor = resource_monitor
        self.resource_allocator = resource_allocator
        
        # 冲突阈值
        self.conflict_thresholds = {
            "total_memory_percent": 95,  # 总内存使用超过95%视为冲突
            "total_cpu_percent": 90,     # 总CPU使用超过90%视为冲突
            "disk_percent": 95           # 磁盘使用超过95%视为冲突
        }
        
        # 冲突历史
        self.conflict_history = []
        
        logger.info("资源冲突检测器初始化完成")
    
    def detect_conflicts(
        self,
        active_services: List[str]
    ) -> Dict[str, Any]:
        """
        检测资源冲突
        
        Args:
            active_services: 活跃服务列表
            
        Returns:
            冲突检测结果
        """
        # 获取当前系统资源
        resources = self.resource_monitor.get_system_resources()
        
        conflicts = {
            "has_conflict": False,
            "conflict_type": [],
            "affected_services": [],
            "severity": "none",  # none/low/medium/high/critical
            "details": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # 检查内存冲突
        memory_percent = resources.get("memory", {}).get("percent", 0)
        if memory_percent >= self.conflict_thresholds["total_memory_percent"]:
            conflicts["has_conflict"] = True
            conflicts["conflict_type"].append("memory_shortage")
            conflicts["details"]["memory"] = {
                "current_percent": memory_percent,
                "threshold": self.conflict_thresholds["total_memory_percent"],
                "message": f"系统内存使用率 {memory_percent:.1f}% 超过阈值"
            }
        
        # 检查CPU冲突
        cpu_percent = resources.get("cpu", {}).get("total_percent", 0)
        if cpu_percent >= self.conflict_thresholds["total_cpu_percent"]:
            conflicts["has_conflict"] = True
            conflicts["conflict_type"].append("cpu_shortage")
            conflicts["details"]["cpu"] = {
                "current_percent": cpu_percent,
                "threshold": self.conflict_thresholds["total_cpu_percent"],
                "message": f"系统CPU使用率 {cpu_percent:.1f}% 超过阈值"
            }
        
        # 检查磁盘冲突
        for disk in resources.get("disk", []):
            disk_percent = disk.get("percent", 0)
            if disk_percent >= self.conflict_thresholds["disk_percent"]:
                conflicts["has_conflict"] = True
                conflicts["conflict_type"].append("disk_shortage")
                conflicts["details"][f"disk_{disk['mountpoint']}"] = {
                    "current_percent": disk_percent,
                    "threshold": self.conflict_thresholds["disk_percent"],
                    "message": f"磁盘 {disk['mountpoint']} 使用率 {disk_percent:.1f}% 超过阈值"
                }
        
        # 确定冲突严重程度
        if conflicts["has_conflict"]:
            if memory_percent >= 98 or cpu_percent >= 95:
                conflicts["severity"] = "critical"
            elif memory_percent >= 95 or cpu_percent >= 90:
                conflicts["severity"] = "high"
            elif memory_percent >= 90 or cpu_percent >= 85:
                conflicts["severity"] = "medium"
            else:
                conflicts["severity"] = "low"
            
            # 识别受影响的服务
            conflicts["affected_services"] = self._identify_affected_services(
                active_services,
                conflicts["conflict_type"]
            )
        
        # 记录冲突历史
        if conflicts["has_conflict"]:
            self.conflict_history.append(conflicts)
            logger.warning(f"检测到资源冲突: {conflicts['conflict_type']}")
        
        return conflicts
    
    def _identify_affected_services(
        self,
        active_services: List[str],
        conflict_types: List[str]
    ) -> List[Dict[str, Any]]:
        """
        识别受影响的服务
        
        Args:
            active_services: 活跃服务列表
            conflict_types: 冲突类型列表
            
        Returns:
            受影响的服务列表
        """
        affected = []
        
        for service in active_services:
            # 获取服务配置和优先级
            config = self.resource_allocator.get_service_config(service)
            priority = config.get("priority", 5)
            
            # 优先级低的服务更容易受影响
            impact_score = 10 - priority
            
            affected.append({
                "service": service,
                "priority": priority,
                "impact_score": impact_score,
                "can_pause": priority < 8,  # 优先级低于8的可以暂停
                "can_reduce": priority < 9   # 优先级低于9的可以降低资源
            })
        
        # 按影响分数排序（受影响最大的在前）
        affected.sort(key=lambda x: x["impact_score"], reverse=True)
        
        return affected
    
    def generate_resolution_options(
        self,
        conflict: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成冲突解决方案
        
        Args:
            conflict: 冲突信息
            
        Returns:
            解决方案列表
        """
        if not conflict.get("has_conflict"):
            return []
        
        options = []
        affected_services = conflict.get("affected_services", [])
        conflict_types = conflict.get("conflict_type", [])
        
        # 方案1: 暂停低优先级服务
        pausable_services = [
            s for s in affected_services
            if s.get("can_pause", False)
        ]
        
        if pausable_services:
            options.append({
                "option_id": 1,
                "title": "暂停低优先级服务",
                "description": f"暂停 {len(pausable_services)} 个低优先级服务以释放资源",
                "services_to_pause": [s["service"] for s in pausable_services[:3]],
                "estimated_memory_freed_gb": sum(
                    self.resource_allocator.get_service_config(s["service"]).get("min_memory_gb", 1)
                    for s in pausable_services[:3]
                ),
                "estimated_cpu_freed_percent": sum(
                    self.resource_allocator.get_service_config(s["service"]).get("min_cpu_percent", 10)
                    for s in pausable_services[:3]
                ),
                "impact": "medium",
                "recommended": len(pausable_services) >= 2
            })
        
        # 方案2: 降低资源分配
        reducible_services = [
            s for s in affected_services
            if s.get("can_reduce", False)
        ]
        
        if reducible_services:
            options.append({
                "option_id": 2,
                "title": "降低服务资源分配",
                "description": f"降低 {len(reducible_services)} 个服务的资源分配",
                "services_to_reduce": [s["service"] for s in reducible_services[:5]],
                "reduce_percentage": 30,
                "impact": "low",
                "recommended": True
            })
        
        # 方案3: 重启服务释放内存
        if "memory_shortage" in conflict_types:
            options.append({
                "option_id": 3,
                "title": "重启服务释放内存",
                "description": "重启部分服务以释放内存泄漏",
                "services_to_restart": [s["service"] for s in affected_services[:2]],
                "impact": "high",
                "recommended": False,
                "warning": "服务重启会导致短暂中断"
            })
        
        # 方案4: 什么都不做，继续监控
        options.append({
            "option_id": 4,
            "title": "继续监控",
            "description": "暂不处理，继续监控资源使用情况",
            "impact": "none",
            "recommended": conflict.get("severity") == "low"
        })
        
        return options
    
    def apply_resolution(
        self,
        option_id: int,
        conflict: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        应用冲突解决方案
        
        Args:
            option_id: 方案ID
            conflict: 冲突信息
            
        Returns:
            应用结果
        """
        options = self.generate_resolution_options(conflict)
        selected_option = next((opt for opt in options if opt["option_id"] == option_id), None)
        
        if not selected_option:
            return {
                "success": False,
                "message": "无效的方案ID"
            }
        
        result = {
            "success": True,
            "option_id": option_id,
            "option_title": selected_option["title"],
            "actions_taken": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if option_id == 1:
                # 暂停服务
                for service in selected_option.get("services_to_pause", []):
                    result["actions_taken"].append({
                        "action": "pause",
                        "service": service,
                        "status": "simulated"  # 实际环境需要真正暂停
                    })
                    logger.info(f"模拟暂停服务: {service}")
            
            elif option_id == 2:
                # 降低资源
                reduce_pct = selected_option.get("reduce_percentage", 30)
                for service in selected_option.get("services_to_reduce", []):
                    config = self.resource_allocator.get_service_config(service)
                    new_memory = config.get("max_memory_gb", 2) * (1 - reduce_pct / 100)
                    new_cpu = config.get("max_cpu_percent", 50) * (1 - reduce_pct / 100)
                    
                    result["actions_taken"].append({
                        "action": "reduce",
                        "service": service,
                        "new_memory_gb": new_memory,
                        "new_cpu_percent": new_cpu,
                        "status": "simulated"
                    })
                    logger.info(f"模拟降低服务资源: {service}")
            
            elif option_id == 3:
                # 重启服务
                for service in selected_option.get("services_to_restart", []):
                    result["actions_taken"].append({
                        "action": "restart",
                        "service": service,
                        "status": "simulated"
                    })
                    logger.info(f"模拟重启服务: {service}")
            
            elif option_id == 4:
                # 继续监控
                result["actions_taken"].append({
                    "action": "monitor",
                    "status": "active"
                })
                logger.info("继续监控资源状态")
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
            logger.error(f"应用解决方案失败: {e}")
        
        return result
    
    def get_conflict_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取冲突历史"""
        return self.conflict_history[-limit:]
    
    def predict_conflict(
        self,
        new_service: str,
        current_services: List[str]
    ) -> Dict[str, Any]:
        """
        预测添加新服务后是否会产生冲突
        
        Args:
            new_service: 新服务名称
            current_services: 当前服务列表
            
        Returns:
            预测结果
        """
        # 获取当前资源
        resources = self.resource_monitor.get_system_resources()
        available = self.resource_monitor.estimate_available_resources()
        
        # 获取新服务需求
        new_service_config = self.resource_allocator.get_service_config(new_service)
        required_memory = new_service_config.get("min_memory_gb", 1)
        required_cpu = new_service_config.get("min_cpu_percent", 10)
        
        prediction = {
            "can_start": True,
            "will_cause_conflict": False,
            "confidence": 0.0,
            "warnings": [],
            "recommendations": []
        }
        
        # 检查可用内存
        available_memory = available.get("memory_available_gb", 0)
        if required_memory > available_memory * 0.8:
            prediction["will_cause_conflict"] = True
            prediction["warnings"].append(
                f"新服务需要 {required_memory}GB 内存，但仅有 {available_memory:.1f}GB 可用"
            )
        
        # 检查可用CPU
        available_cpu = available.get("cpu_available_percent", 0)
        if required_cpu > available_cpu * 0.8:
            prediction["will_cause_conflict"] = True
            prediction["warnings"].append(
                f"新服务需要 {required_cpu}% CPU，但仅有 {available_cpu:.1f}% 可用"
            )
        
        # 计算置信度
        if prediction["will_cause_conflict"]:
            prediction["can_start"] = False
            prediction["confidence"] = 0.8
            prediction["recommendations"].append("建议先释放资源或暂停其他服务")
        else:
            prediction["confidence"] = 0.9
            prediction["recommendations"].append("可以安全启动新服务")
        
        return prediction

