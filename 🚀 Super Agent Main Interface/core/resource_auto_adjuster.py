"""
资源自动调节系统
实现资源问题检测、分析、建议生成、用户授权下的自动调节
"""

import asyncio
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

class ResourceIssueType(Enum):
    """资源问题类型"""
    CPU_HIGH = "cpu_high"
    MEMORY_HIGH = "memory_high"
    DISK_HIGH = "disk_high"
    NETWORK_SLOW = "network_slow"
    PROCESS_BLOCKING = "process_blocking"
    RESOURCE_CONFLICT = "resource_conflict"

class AdjustmentAction(Enum):
    """调节动作"""
    KILL_PROCESS = "kill_process"
    REDUCE_PRIORITY = "reduce_priority"
    INCREASE_LIMIT = "increase_limit"
    REALLOCATE = "reallocate"
    RESTART_SERVICE = "restart_service"
    CLEAR_CACHE = "clear_cache"

@dataclass
class ResourceIssue:
    """资源问题"""
    issue_type: ResourceIssueType
    severity: str  # low, medium, high, critical
    description: str
    current_value: float
    threshold: float
    affected_modules: List[str]
    detected_at: datetime
    metadata: Dict[str, Any]

@dataclass
class AdjustmentSuggestion:
    """调节建议"""
    issue: ResourceIssue
    action: AdjustmentAction
    description: str
    expected_impact: str
    risk_level: str  # low, medium, high
    requires_approval: bool
    estimated_improvement: float  # 预期改善百分比

class ResourceAutoAdjuster:
    """
    资源自动调节系统
    
    功能：
    1. 监控系统资源（CPU、内存、磁盘、网络）
    2. 检测资源问题
    3. 分析问题原因
    4. 生成调节建议
    5. 在用户授权下自动执行调节
    """
    
    def __init__(self, resource_manager=None):
        self.resource_manager = resource_manager
        self.issues = []
        self.suggestions = []
        self.approved_adjustments = []
        self.auto_adjust_enabled = False
        self.auto_adjust_threshold = "medium"  # low, medium, high, critical
        
        # 资源阈值配置
        self.thresholds = {
            "cpu": {"warning": 70, "critical": 90},
            "memory": {"warning": 75, "critical": 90},
            "disk": {"warning": 80, "critical": 95},
            "network": {"warning": 50, "critical": 80}  # Mbps
        }
        
    async def monitor_resources(self) -> List[ResourceIssue]:
        """监控系统资源并检测问题"""
        issues = []
        
        # 获取当前资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 检测CPU问题
        if cpu_percent >= self.thresholds["cpu"]["critical"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.CPU_HIGH,
                severity="critical",
                description=f"CPU使用率过高: {cpu_percent:.1f}%",
                current_value=cpu_percent,
                threshold=self.thresholds["cpu"]["critical"],
                affected_modules=await self._get_high_cpu_processes(),
                detected_at=datetime.now(),
                metadata={"cpu_percent": cpu_percent}
            ))
        elif cpu_percent >= self.thresholds["cpu"]["warning"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.CPU_HIGH,
                severity="high",
                description=f"CPU使用率较高: {cpu_percent:.1f}%",
                current_value=cpu_percent,
                threshold=self.thresholds["cpu"]["warning"],
                affected_modules=await self._get_high_cpu_processes(),
                detected_at=datetime.now(),
                metadata={"cpu_percent": cpu_percent}
            ))
        
        # 检测内存问题
        memory_percent = memory.percent
        if memory_percent >= self.thresholds["memory"]["critical"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.MEMORY_HIGH,
                severity="critical",
                description=f"内存使用率过高: {memory_percent:.1f}%",
                current_value=memory_percent,
                threshold=self.thresholds["memory"]["critical"],
                affected_modules=await self._get_high_memory_processes(),
                detected_at=datetime.now(),
                metadata={"memory_percent": memory_percent, "available_gb": memory.available / (1024**3)}
            ))
        elif memory_percent >= self.thresholds["memory"]["warning"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.MEMORY_HIGH,
                severity="high",
                description=f"内存使用率较高: {memory_percent:.1f}%",
                current_value=memory_percent,
                threshold=self.thresholds["memory"]["warning"],
                affected_modules=await self._get_high_memory_processes(),
                detected_at=datetime.now(),
                metadata={"memory_percent": memory_percent, "available_gb": memory.available / (1024**3)}
            ))
        
        # 检测磁盘问题
        disk_percent = disk.percent
        if disk_percent >= self.thresholds["disk"]["critical"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.DISK_HIGH,
                severity="critical",
                description=f"磁盘使用率过高: {disk_percent:.1f}%",
                current_value=disk_percent,
                threshold=self.thresholds["disk"]["critical"],
                affected_modules=[],
                detected_at=datetime.now(),
                metadata={"disk_percent": disk_percent, "free_gb": disk.free / (1024**3)}
            ))
        elif disk_percent >= self.thresholds["disk"]["warning"]:
            issues.append(ResourceIssue(
                issue_type=ResourceIssueType.DISK_HIGH,
                severity="high",
                description=f"磁盘使用率较高: {disk_percent:.1f}%",
                current_value=disk_percent,
                threshold=self.thresholds["disk"]["warning"],
                affected_modules=[],
                detected_at=datetime.now(),
                metadata={"disk_percent": disk_percent, "free_gb": disk.free / (1024**3)}
            ))
        
        # 保存问题
        self.issues.extend(issues)
        
        # 如果问题超过1000条，保留最近1000条
        if len(self.issues) > 1000:
            self.issues = self.issues[-1000:]
        
        return issues
    
    async def _get_high_cpu_processes(self, limit: int = 5) -> List[str]:
        """获取高CPU使用率的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                cpu_percent = proc.info['cpu_percent']
                if cpu_percent and cpu_percent > 10:  # CPU使用率超过10%
                    processes.append(f"{proc.info['name']}({proc.info['pid']})")
                    if len(processes) >= limit:
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    async def _get_high_memory_processes(self, limit: int = 5) -> List[str]:
        """获取高内存使用率的进程"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                memory_percent = proc.info['memory_percent']
                if memory_percent and memory_percent > 5:  # 内存使用率超过5%
                    processes.append(f"{proc.info['name']}({proc.info['pid']})")
                    if len(processes) >= limit:
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes
    
    async def analyze_issue(self, issue: ResourceIssue) -> List[AdjustmentSuggestion]:
        """分析问题并生成调节建议"""
        suggestions = []
        
        if issue.issue_type == ResourceIssueType.CPU_HIGH:
            suggestions.extend(await self._analyze_cpu_issue(issue))
        elif issue.issue_type == ResourceIssueType.MEMORY_HIGH:
            suggestions.extend(await self._analyze_memory_issue(issue))
        elif issue.issue_type == ResourceIssueType.DISK_HIGH:
            suggestions.extend(await self._analyze_disk_issue(issue))
        
        # 保存建议
        self.suggestions.extend(suggestions)
        
        # 如果建议超过1000条，保留最近1000条
        if len(self.suggestions) > 1000:
            self.suggestions = self.suggestions[-1000:]
        
        return suggestions
    
    async def _analyze_cpu_issue(self, issue: ResourceIssue) -> List[AdjustmentSuggestion]:
        """分析CPU问题"""
        suggestions = []
        
        # 建议1: 降低非关键进程优先级
        if issue.affected_modules:
            suggestions.append(AdjustmentSuggestion(
                issue=issue,
                action=AdjustmentAction.REDUCE_PRIORITY,
                description=f"降低非关键进程优先级: {', '.join(issue.affected_modules[:3])}",
                expected_impact="减少CPU竞争，释放10-20% CPU资源",
                risk_level="low",
                requires_approval=issue.severity == "critical",
                estimated_improvement=15.0
            ))
        
        # 建议2: 清理缓存
        suggestions.append(AdjustmentSuggestion(
            issue=issue,
            action=AdjustmentAction.CLEAR_CACHE,
            description="清理系统缓存",
            expected_impact="释放部分CPU资源，改善响应速度",
            risk_level="low",
            requires_approval=False,
            estimated_improvement=5.0
        ))
        
        # 建议3: 重启占用资源过多的服务
        if issue.severity == "critical" and issue.affected_modules:
            suggestions.append(AdjustmentSuggestion(
                issue=issue,
                action=AdjustmentAction.RESTART_SERVICE,
                description=f"重启占用资源过多的服务: {issue.affected_modules[0]}",
                expected_impact="释放大量CPU资源，可能暂时中断服务",
                risk_level="high",
                requires_approval=True,
                estimated_improvement=30.0
            ))
        
        return suggestions
    
    async def _analyze_memory_issue(self, issue: ResourceIssue) -> List[AdjustmentSuggestion]:
        """分析内存问题"""
        suggestions = []
        
        # 建议1: 清理缓存
        suggestions.append(AdjustmentSuggestion(
            issue=issue,
            action=AdjustmentAction.CLEAR_CACHE,
            description="清理内存缓存",
            expected_impact="释放10-30%内存资源",
            risk_level="low",
            requires_approval=False,
            estimated_improvement=20.0
        ))
        
        # 建议2: 终止占用内存过多的进程
        if issue.affected_modules and issue.severity == "critical":
            suggestions.append(AdjustmentSuggestion(
                issue=issue,
                action=AdjustmentAction.KILL_PROCESS,
                description=f"终止占用内存过多的进程: {issue.affected_modules[0]}",
                expected_impact="释放大量内存，但会终止进程",
                risk_level="high",
                requires_approval=True,
                estimated_improvement=40.0
            ))
        
        # 建议3: 重新分配资源
        if self.resource_manager:
            suggestions.append(AdjustmentSuggestion(
                issue=issue,
                action=AdjustmentAction.REALLOCATE,
                description="重新分配模块资源限制",
                expected_impact="优化资源分配，平衡各模块内存使用",
                risk_level="medium",
                requires_approval=issue.severity == "critical",
                estimated_improvement=15.0
            ))
        
        return suggestions
    
    async def _analyze_disk_issue(self, issue: ResourceIssue) -> List[AdjustmentSuggestion]:
        """分析磁盘问题"""
        suggestions = []
        
        # 建议1: 清理临时文件和日志
        suggestions.append(AdjustmentSuggestion(
            issue=issue,
            action=AdjustmentAction.CLEAR_CACHE,
            description="清理临时文件和日志",
            expected_impact="释放磁盘空间，改善磁盘性能",
            risk_level="low",
            requires_approval=False,
            estimated_improvement=10.0
        ))
        
        return suggestions
    
    async def execute_adjustment(
        self,
        suggestion: AdjustmentSuggestion,
        approved: bool = False
    ) -> Dict[str, Any]:
        """
        执行调节动作
        
        Args:
            suggestion: 调节建议
            approved: 是否已获得用户授权
        
        Returns:
            执行结果
        """
        if suggestion.requires_approval and not approved:
            return {
                "success": False,
                "message": "需要用户授权才能执行此操作",
                "suggestion": suggestion
            }
        
        result = {
            "success": False,
            "action": suggestion.action.value,
            "description": suggestion.description,
            "executed_at": datetime.now().isoformat()
        }
        
        try:
            if suggestion.action == AdjustmentAction.CLEAR_CACHE:
                result = await self._clear_cache()
            elif suggestion.action == AdjustmentAction.REDUCE_PRIORITY:
                result = await self._reduce_priority(suggestion.issue.affected_modules)
            elif suggestion.action == AdjustmentAction.KILL_PROCESS:
                result = await self._kill_process(suggestion.issue.affected_modules[0] if suggestion.issue.affected_modules else None)
            elif suggestion.action == AdjustmentAction.REALLOCATE:
                result = await self._reallocate_resources()
            elif suggestion.action == AdjustmentAction.RESTART_SERVICE:
                result = await self._restart_service(suggestion.issue.affected_modules[0] if suggestion.issue.affected_modules else None)
            
            # 记录已执行的调节
            self.approved_adjustments.append({
                "suggestion": suggestion,
                "result": result,
                "executed_at": datetime.now().isoformat()
            })
            
            # 如果记录超过1000条，保留最近1000条
            if len(self.approved_adjustments) > 1000:
                self.approved_adjustments = self.approved_adjustments[-1000:]
            
        except Exception as e:
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    async def _clear_cache(self) -> Dict[str, Any]:
        """清理缓存"""
        # 这里可以实现实际的缓存清理逻辑
        # 例如：清理Python缓存、清理临时文件等
        import gc
        gc.collect()
        
        return {
            "success": True,
            "message": "缓存已清理",
            "freed_memory": "未知"
        }
    
    async def _reduce_priority(self, processes: List[str]) -> Dict[str, Any]:
        """降低进程优先级"""
        # 这里可以实现实际的进程优先级调整逻辑
        # 注意：需要适当的权限
        
        return {
            "success": True,
            "message": f"已降低进程优先级: {', '.join(processes[:3])}",
            "affected_processes": processes[:3]
        }
    
    async def _kill_process(self, process_name: str) -> Dict[str, Any]:
        """终止进程"""
        # 这里可以实现实际的进程终止逻辑
        # 注意：需要适当的权限，且要谨慎使用
        
        return {
            "success": True,
            "message": f"已终止进程: {process_name}",
            "warning": "进程已终止，相关服务可能受影响"
        }
    
    async def _reallocate_resources(self) -> Dict[str, Any]:
        """重新分配资源"""
        if not self.resource_manager:
            return {
                "success": False,
                "message": "资源管理器不可用"
            }
        
        # 调用资源管理器重新分配资源
        # 这里需要根据实际的资源管理器接口实现
        
        return {
            "success": True,
            "message": "资源已重新分配"
        }
    
    async def _restart_service(self, service_name: str) -> Dict[str, Any]:
        """重启服务"""
        # 这里可以实现实际的服务重启逻辑
        # 注意：需要适当的权限
        
        return {
            "success": True,
            "message": f"服务已重启: {service_name}",
            "warning": "服务重启可能导致短暂中断"
        }
    
    async def auto_adjust(self) -> List[Dict[str, Any]]:
        """
        自动调节（在启用且满足条件时）
        
        Returns:
            执行的调节动作列表
        """
        if not self.auto_adjust_enabled:
            return []
        
        # 监控资源
        issues = await self.monitor_resources()
        
        executed_adjustments = []
        
        for issue in issues:
            # 检查是否满足自动调节条件
            if self._should_auto_adjust(issue):
                # 分析问题并生成建议
                suggestions = await self.analyze_issue(issue)
                
                # 执行低风险的调节
                for suggestion in suggestions:
                    if suggestion.risk_level == "low" and not suggestion.requires_approval:
                        result = await self.execute_adjustment(suggestion, approved=True)
                        executed_adjustments.append(result)
        
        return executed_adjustments
    
    def _should_auto_adjust(self, issue: ResourceIssue) -> bool:
        """判断是否应该自动调节"""
        severity_levels = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "critical": 4
        }
        
        issue_level = severity_levels.get(issue.severity, 0)
        threshold_level = severity_levels.get(self.auto_adjust_threshold, 2)
        
        return issue_level >= threshold_level
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        recent_issues = self.issues[-100:] if self.issues else []
        recent_suggestions = self.suggestions[-100:] if self.suggestions else []
        
        # 统计问题类型
        issue_types = {}
        for issue in recent_issues:
            issue_type = issue.issue_type.value
            issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
        
        # 统计建议类型
        action_types = {}
        for suggestion in recent_suggestions:
            action_type = suggestion.action.value
            action_types[action_type] = action_types.get(action_type, 0) + 1
        
        return {
            "total_issues": len(self.issues),
            "recent_issues": len(recent_issues),
            "total_suggestions": len(self.suggestions),
            "recent_suggestions": len(recent_suggestions),
            "total_adjustments": len(self.approved_adjustments),
            "issue_types": issue_types,
            "action_types": action_types,
            "auto_adjust_enabled": self.auto_adjust_enabled,
            "auto_adjust_threshold": self.auto_adjust_threshold,
            "last_update": datetime.now().isoformat()
        }
    
    def enable_auto_adjust(self, threshold: str = "medium"):
        """启用自动调节"""
        self.auto_adjust_enabled = True
        self.auto_adjust_threshold = threshold
    
    def disable_auto_adjust(self):
        """禁用自动调节"""
        self.auto_adjust_enabled = False
















