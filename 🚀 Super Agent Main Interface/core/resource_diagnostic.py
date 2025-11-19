"""
资源诊断系统
P0-014: 资源诊断与调度建议 + 授权执行（联动主界面资源面板）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class DiagnosticSeverity(Enum):
    """诊断严重程度"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ResourceIssueCategory(Enum):
    """资源问题类别"""
    CPU_BOTTLENECK = "cpu_bottleneck"
    MEMORY_PRESSURE = "memory_pressure"
    DISK_SPACE = "disk_space"
    NETWORK_LATENCY = "network_latency"
    PROCESS_CONFLICT = "process_conflict"
    RESOURCE_LEAK = "resource_leak"
    SCHEDULING_INEFFICIENCY = "scheduling_inefficiency"


@dataclass
class ResourceDiagnostic:
    """资源诊断结果"""
    category: ResourceIssueCategory
    severity: DiagnosticSeverity
    title: str
    description: str
    current_value: float
    threshold: float
    affected_modules: List[str] = field(default_factory=list)
    root_cause: Optional[str] = None
    impact: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SchedulingSuggestion:
    """调度建议"""
    diagnostic: ResourceDiagnostic
    action_type: str  # reallocate, scale_down, scale_up, migrate, optimize
    description: str
    expected_improvement: str
    risk_level: str  # low, medium, high
    requires_approval: bool
    estimated_impact: Dict[str, float]  # 预期影响指标
    implementation_steps: List[str] = field(default_factory=list)
    rollback_plan: Optional[str] = None


class ResourceDiagnosticEngine:
    """
    资源诊断引擎
    
    功能：
    1. 深度资源诊断（CPU、内存、磁盘、网络）
    2. 问题根因分析
    3. 影响评估
    4. 生成调度建议
    """
    
    def __init__(
        self,
        resource_monitor=None,
        resource_auto_adjuster=None
    ):
        self.resource_monitor = resource_monitor
        self.resource_auto_adjuster = resource_auto_adjuster
        self.diagnostics: List[ResourceDiagnostic] = []
        self.suggestions: List[SchedulingSuggestion] = []
        self.diagnostic_history: List[Dict[str, Any]] = []
        
        # 诊断阈值配置
        self.thresholds = {
            "cpu": {
                "warning": 70.0,
                "error": 85.0,
                "critical": 95.0
            },
            "memory": {
                "warning": 75.0,
                "error": 85.0,
                "critical": 95.0
            },
            "disk": {
                "warning": 80.0,
                "error": 90.0,
                "critical": 95.0
            },
            "network": {
                "warning": 50.0,  # Mbps
                "error": 70.0,
                "critical": 85.0
            }
        }
    
    async def run_diagnostic(
        self,
        resource_data: Optional[Dict[str, Any]] = None
    ) -> List[ResourceDiagnostic]:
        """
        运行资源诊断
        
        Args:
            resource_data: 资源数据（可选，不提供则从monitor获取）
            
        Returns:
            诊断结果列表
        """
        if not resource_data:
            if self.resource_monitor:
                resource_data = self.resource_monitor.get_current_status()
            else:
                logger.warning("资源监控器不可用，无法获取资源数据")
                return []
        
        diagnostics = []
        
        # CPU诊断
        cpu_diag = await self._diagnose_cpu(resource_data.get("cpu", {}))
        if cpu_diag:
            diagnostics.append(cpu_diag)
        
        # 内存诊断
        memory_diag = await self._diagnose_memory(resource_data.get("memory", {}))
        if memory_diag:
            diagnostics.append(memory_diag)
        
        # 磁盘诊断
        disk_diag = await self._diagnose_disk(resource_data.get("disk", {}))
        if disk_diag:
            diagnostics.append(disk_diag)
        
        # 网络诊断
        network_diag = await self._diagnose_network(resource_data.get("network", {}))
        if network_diag:
            diagnostics.append(network_diag)
        
        # 进程冲突诊断
        process_diag = await self._diagnose_process_conflicts(resource_data)
        if process_diag:
            diagnostics.extend(process_diag)
        
        # 资源泄漏诊断
        leak_diag = await self._diagnose_resource_leaks(resource_data)
        if leak_diag:
            diagnostics.append(leak_diag)
        
        # 调度效率诊断
        scheduling_diag = await self._diagnose_scheduling_efficiency(resource_data)
        if scheduling_diag:
            diagnostics.append(scheduling_diag)
        
        # 保存诊断结果
        self.diagnostics.extend(diagnostics)
        
        # 保留最近1000条
        if len(self.diagnostics) > 1000:
            self.diagnostics = self.diagnostics[-1000:]
        
        # 记录诊断历史
        self.diagnostic_history.append({
            "timestamp": datetime.now().isoformat(),
            "diagnostics_count": len(diagnostics),
            "severity_summary": self._summarize_severity(diagnostics)
        })
        
        return diagnostics
    
    async def _diagnose_cpu(self, cpu_data: Dict[str, Any]) -> Optional[ResourceDiagnostic]:
        """诊断CPU问题"""
        cpu_percent = cpu_data.get("percent", 0)
        
        if cpu_percent >= self.thresholds["cpu"]["critical"]:
            severity = DiagnosticSeverity.CRITICAL
            title = "CPU使用率严重过高"
            description = f"CPU使用率达到 {cpu_percent:.1f}%，系统响应可能严重延迟"
        elif cpu_percent >= self.thresholds["cpu"]["error"]:
            severity = DiagnosticSeverity.ERROR
            title = "CPU使用率过高"
            description = f"CPU使用率达到 {cpu_percent:.1f}%，可能影响系统性能"
        elif cpu_percent >= self.thresholds["cpu"]["warning"]:
            severity = DiagnosticSeverity.WARNING
            title = "CPU使用率较高"
            description = f"CPU使用率达到 {cpu_percent:.1f}%，建议关注"
        else:
            return None
        
        # 分析根因
        root_cause = await self._analyze_cpu_root_cause(cpu_data)
        
        # 获取受影响模块
        affected_modules = await self._get_affected_modules("cpu", cpu_data)
        
        return ResourceDiagnostic(
            category=ResourceIssueCategory.CPU_BOTTLENECK,
            severity=severity,
            title=title,
            description=description,
            current_value=cpu_percent,
            threshold=self.thresholds["cpu"].get("warning", 70.0),
            affected_modules=affected_modules,
            root_cause=root_cause,
            impact=f"可能导致响应时间增加 {(cpu_percent - 70) * 0.5:.1f}%",
            metadata={"cpu_data": cpu_data}
        )
    
    async def _diagnose_memory(self, memory_data: Dict[str, Any]) -> Optional[ResourceDiagnostic]:
        """诊断内存问题"""
        memory_percent = memory_data.get("percent", 0)
        available_gb = memory_data.get("available", 0) / (1024 ** 3)
        
        if memory_percent >= self.thresholds["memory"]["critical"]:
            severity = DiagnosticSeverity.CRITICAL
            title = "内存使用率严重过高"
            description = f"内存使用率达到 {memory_percent:.1f}%，可用内存仅 {available_gb:.2f}GB，可能出现OOM"
        elif memory_percent >= self.thresholds["memory"]["error"]:
            severity = DiagnosticSeverity.ERROR
            title = "内存使用率过高"
            description = f"内存使用率达到 {memory_percent:.1f}%，可用内存 {available_gb:.2f}GB"
        elif memory_percent >= self.thresholds["memory"]["warning"]:
            severity = DiagnosticSeverity.WARNING
            title = "内存使用率较高"
            description = f"内存使用率达到 {memory_percent:.1f}%，建议关注"
        else:
            return None
        
        root_cause = await self._analyze_memory_root_cause(memory_data)
        affected_modules = await self._get_affected_modules("memory", memory_data)
        
        return ResourceDiagnostic(
            category=ResourceIssueCategory.MEMORY_PRESSURE,
            severity=severity,
            title=title,
            description=description,
            current_value=memory_percent,
            threshold=self.thresholds["memory"].get("warning", 75.0),
            affected_modules=affected_modules,
            root_cause=root_cause,
            impact=f"可能导致内存不足，影响系统稳定性",
            metadata={"memory_data": memory_data, "available_gb": available_gb}
        )
    
    async def _diagnose_disk(self, disk_data: Dict[str, Any]) -> Optional[ResourceDiagnostic]:
        """诊断磁盘问题"""
        disk_percent = disk_data.get("percent", 0)
        free_gb = disk_data.get("free", 0) / (1024 ** 3)
        
        if disk_percent >= self.thresholds["disk"]["critical"]:
            severity = DiagnosticSeverity.CRITICAL
            title = "磁盘空间严重不足"
            description = f"磁盘使用率达到 {disk_percent:.1f}%，剩余空间仅 {free_gb:.2f}GB"
        elif disk_percent >= self.thresholds["disk"]["error"]:
            severity = DiagnosticSeverity.ERROR
            title = "磁盘空间不足"
            description = f"磁盘使用率达到 {disk_percent:.1f}%，剩余空间 {free_gb:.2f}GB"
        elif disk_percent >= self.thresholds["disk"]["warning"]:
            severity = DiagnosticSeverity.WARNING
            title = "磁盘空间紧张"
            description = f"磁盘使用率达到 {disk_percent:.1f}%，建议清理"
        else:
            return None
        
        root_cause = await self._analyze_disk_root_cause(disk_data)
        
        return ResourceDiagnostic(
            category=ResourceIssueCategory.DISK_SPACE,
            severity=severity,
            title=title,
            description=description,
            current_value=disk_percent,
            threshold=self.thresholds["disk"].get("warning", 80.0),
            affected_modules=[],
            root_cause=root_cause,
            impact="可能影响日志写入、数据存储等功能",
            metadata={"disk_data": disk_data, "free_gb": free_gb}
        )
    
    async def _diagnose_network(self, network_data: Dict[str, Any]) -> Optional[ResourceDiagnostic]:
        """诊断网络问题"""
        # 这里简化处理，实际应该分析网络延迟、带宽等
        return None
    
    async def _diagnose_process_conflicts(
        self,
        resource_data: Dict[str, Any]
    ) -> List[ResourceDiagnostic]:
        """诊断进程冲突"""
        diagnostics = []
        
        # 检查是否有多个高CPU进程同时运行
        cpu_data = resource_data.get("cpu", {})
        if cpu_data.get("percent", 0) > 80:
            per_cpu = cpu_data.get("per_cpu", [])
            if per_cpu and max(per_cpu) > 90:
                diagnostics.append(ResourceDiagnostic(
                    category=ResourceIssueCategory.PROCESS_CONFLICT,
                    severity=DiagnosticSeverity.WARNING,
                    title="检测到进程资源竞争",
                    description="多个进程同时占用高CPU，可能存在资源竞争",
                    current_value=max(per_cpu),
                    threshold=90.0,
                    affected_modules=[],
                    root_cause="多个高优先级进程同时运行",
                    impact="可能导致系统响应变慢",
                    metadata={"per_cpu": per_cpu}
                ))
        
        return diagnostics
    
    async def _diagnose_resource_leaks(
        self,
        resource_data: Dict[str, Any]
    ) -> Optional[ResourceDiagnostic]:
        """诊断资源泄漏"""
        # 检查资源历史趋势，判断是否有泄漏
        if self.resource_monitor and hasattr(self.resource_monitor, "resource_history"):
            history = self.resource_monitor.resource_history
            if len(history) >= 10:
                # 检查内存是否持续增长
                recent_memory = [h.get("memory", {}).get("percent", 0) for h in history[-10:]]
                if all(recent_memory[i] < recent_memory[i+1] for i in range(len(recent_memory)-1)):
                    return ResourceDiagnostic(
                        category=ResourceIssueCategory.RESOURCE_LEAK,
                        severity=DiagnosticSeverity.WARNING,
                        title="检测到可能的资源泄漏",
                        description="内存使用率持续上升，可能存在资源泄漏",
                        current_value=recent_memory[-1],
                        threshold=recent_memory[0],
                        affected_modules=[],
                        root_cause="内存持续增长，可能存在未释放的资源",
                        impact="长期运行可能导致内存耗尽",
                        metadata={"trend": recent_memory}
                    )
        
        return None
    
    async def _diagnose_scheduling_efficiency(
        self,
        resource_data: Dict[str, Any]
    ) -> Optional[ResourceDiagnostic]:
        """诊断调度效率"""
        # 检查资源分配是否均衡
        cpu_percent = resource_data.get("cpu", {}).get("percent", 0)
        memory_percent = resource_data.get("memory", {}).get("percent", 0)
        
        # 如果CPU和内存使用率差异很大，可能存在调度不均衡
        diff = abs(cpu_percent - memory_percent)
        if diff > 30:
            return ResourceDiagnostic(
                category=ResourceIssueCategory.SCHEDULING_INEFFICIENCY,
                severity=DiagnosticSeverity.INFO,
                title="资源调度不均衡",
                description=f"CPU和内存使用率差异较大（{diff:.1f}%），可能存在调度优化空间",
                current_value=diff,
                threshold=30.0,
                affected_modules=[],
                root_cause="资源分配策略可能不够优化",
                impact="可能影响整体系统效率",
                metadata={"cpu_percent": cpu_percent, "memory_percent": memory_percent}
            )
        
        return None
    
    async def _analyze_cpu_root_cause(self, cpu_data: Dict[str, Any]) -> str:
        """分析CPU问题根因"""
        cpu_percent = cpu_data.get("percent", 0)
        per_cpu = cpu_data.get("per_cpu", [])
        
        if per_cpu and max(per_cpu) > 95:
            return "单个核心过载，可能存在单线程瓶颈"
        elif cpu_percent > 90:
            return "整体CPU负载过高，可能是计算密集型任务过多"
        else:
            return "CPU使用率较高，建议优化任务调度"
    
    async def _analyze_memory_root_cause(self, memory_data: Dict[str, Any]) -> str:
        """分析内存问题根因"""
        available_gb = memory_data.get("available", 0) / (1024 ** 3)
        
        if available_gb < 1:
            return "可用内存严重不足，可能存在内存泄漏或任务过多"
        elif available_gb < 2:
            return "可用内存较少，建议清理缓存或减少并发任务"
        else:
            return "内存使用率较高，建议优化内存分配"
    
    async def _analyze_disk_root_cause(self, disk_data: Dict[str, Any]) -> str:
        """分析磁盘问题根因"""
        free_gb = disk_data.get("free", 0) / (1024 ** 3)
        
        if free_gb < 5:
            return "磁盘空间严重不足，建议立即清理或扩展存储"
        elif free_gb < 10:
            return "磁盘空间紧张，建议清理临时文件和日志"
        else:
            return "磁盘使用率较高，建议定期清理"
    
    async def _get_affected_modules(
        self,
        resource_type: str,
        resource_data: Dict[str, Any]
    ) -> List[str]:
        """获取受影响的模块"""
        # 这里可以调用资源监控器获取高资源占用的进程/模块
        # 简化实现
        return []
    
    def _summarize_severity(self, diagnostics: List[ResourceDiagnostic]) -> Dict[str, int]:
        """汇总严重程度"""
        summary = {
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        for diag in diagnostics:
            severity = diag.severity.value
            if severity in summary:
                summary[severity] += 1
        return summary
    
    async def generate_scheduling_suggestions(
        self,
        diagnostics: List[ResourceDiagnostic]
    ) -> List[SchedulingSuggestion]:
        """
        生成调度建议
        
        Args:
            diagnostics: 诊断结果列表
            
        Returns:
            调度建议列表
        """
        suggestions = []
        
        for diagnostic in diagnostics:
            if diagnostic.category == ResourceIssueCategory.CPU_BOTTLENECK:
                suggestions.extend(await self._suggest_cpu_optimization(diagnostic))
            elif diagnostic.category == ResourceIssueCategory.MEMORY_PRESSURE:
                suggestions.extend(await self._suggest_memory_optimization(diagnostic))
            elif diagnostic.category == ResourceIssueCategory.DISK_SPACE:
                suggestions.extend(await self._suggest_disk_optimization(diagnostic))
            elif diagnostic.category == ResourceIssueCategory.PROCESS_CONFLICT:
                suggestions.extend(await self._suggest_process_optimization(diagnostic))
            elif diagnostic.category == ResourceIssueCategory.RESOURCE_LEAK:
                suggestions.extend(await self._suggest_leak_fix(diagnostic))
            elif diagnostic.category == ResourceIssueCategory.SCHEDULING_INEFFICIENCY:
                suggestions.extend(await self._suggest_scheduling_optimization(diagnostic))
        
        # 保存建议
        self.suggestions.extend(suggestions)
        
        # 保留最近1000条
        if len(self.suggestions) > 1000:
            self.suggestions = self.suggestions[-1000:]
        
        return suggestions
    
    async def _suggest_cpu_optimization(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成CPU优化建议"""
        suggestions = []
        
        # 建议1: 重新分配CPU资源
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="reallocate",
            description="重新分配CPU资源，降低高负载模块的CPU配额",
            expected_improvement="CPU使用率降低15-25%",
            risk_level="low",
            requires_approval=diagnostic.severity == DiagnosticSeverity.CRITICAL,
            estimated_impact={"cpu_reduction": 20.0},
            implementation_steps=[
                "识别高CPU占用模块",
                "调整模块CPU配额",
                "监控调整效果"
            ]
        ))
        
        # 建议2: 优化任务调度
        if diagnostic.severity in [DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL]:
            suggestions.append(SchedulingSuggestion(
                diagnostic=diagnostic,
                action_type="optimize",
                description="优化任务调度策略，错峰执行高CPU任务",
                expected_improvement="减少CPU峰值，提升系统稳定性",
                risk_level="medium",
                requires_approval=True,
                estimated_impact={"cpu_peak_reduction": 30.0},
                implementation_steps=[
                    "分析任务执行模式",
                    "调整任务调度时间",
                    "实施错峰策略"
                ]
            ))
        
        return suggestions
    
    async def _suggest_memory_optimization(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成内存优化建议"""
        suggestions = []
        
        # 建议1: 清理内存缓存
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="optimize",
            description="清理内存缓存，释放可用内存",
            expected_improvement="释放10-30%内存",
            risk_level="low",
            requires_approval=False,
            estimated_impact={"memory_freed_percent": 20.0},
            implementation_steps=[
                "识别可清理的缓存",
                "执行缓存清理",
                "验证内存释放效果"
            ]
        ))
        
        # 建议2: 重新分配内存
        if diagnostic.severity in [DiagnosticSeverity.ERROR, DiagnosticSeverity.CRITICAL]:
            suggestions.append(SchedulingSuggestion(
                diagnostic=diagnostic,
                action_type="reallocate",
                description="重新分配模块内存配额，限制高内存占用模块",
                expected_improvement="内存使用率降低20-30%",
                risk_level="medium",
                requires_approval=True,
                estimated_impact={"memory_reduction": 25.0},
                implementation_steps=[
                    "识别高内存占用模块",
                    "调整内存配额",
                    "监控调整效果"
                ],
                rollback_plan="恢复原始内存配额"
            ))
        
        return suggestions
    
    async def _suggest_disk_optimization(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成磁盘优化建议"""
        suggestions = []
        
        # 建议: 清理临时文件和日志
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="optimize",
            description="清理临时文件、日志和缓存，释放磁盘空间",
            expected_improvement="释放5-15%磁盘空间",
            risk_level="low",
            requires_approval=False,
            estimated_impact={"disk_freed_percent": 10.0},
            implementation_steps=[
                "扫描临时文件",
                "清理过期日志",
                "清理系统缓存",
                "验证空间释放"
            ]
        ))
        
        return suggestions
    
    async def _suggest_process_optimization(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成进程优化建议"""
        suggestions = []
        
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="optimize",
            description="调整进程优先级，避免资源竞争",
            expected_improvement="减少进程冲突，提升系统响应",
            risk_level="low",
            requires_approval=False,
            estimated_impact={"conflict_reduction": 50.0},
            implementation_steps=[
                "识别竞争进程",
                "调整进程优先级",
                "监控资源使用"
            ]
        ))
        
        return suggestions
    
    async def _suggest_leak_fix(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成资源泄漏修复建议"""
        suggestions = []
        
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="optimize",
            description="检查并修复资源泄漏，重启相关服务",
            expected_improvement="停止内存泄漏，稳定内存使用",
            risk_level="medium",
            requires_approval=True,
            estimated_impact={"leak_stopped": 100.0},
            implementation_steps=[
                "定位泄漏源",
                "修复泄漏问题",
                "重启相关服务",
                "验证修复效果"
            ],
            rollback_plan="回滚到修复前版本"
        ))
        
        return suggestions
    
    async def _suggest_scheduling_optimization(
        self,
        diagnostic: ResourceDiagnostic
    ) -> List[SchedulingSuggestion]:
        """生成调度优化建议"""
        suggestions = []
        
        suggestions.append(SchedulingSuggestion(
            diagnostic=diagnostic,
            action_type="optimize",
            description="优化资源调度策略，平衡CPU和内存使用",
            expected_improvement="提升资源利用率，减少资源浪费",
            risk_level="low",
            requires_approval=False,
            estimated_impact={"efficiency_improvement": 15.0},
            implementation_steps=[
                "分析资源使用模式",
                "调整调度策略",
                "监控优化效果"
            ]
        ))
        
        return suggestions
    
    def get_diagnostic_summary(
        self,
        hours: int = 24
    ) -> Dict[str, Any]:
        """获取诊断摘要"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_diagnostics = [
            d for d in self.diagnostics
            if d.detected_at >= cutoff_time
        ]
        
        severity_summary = self._summarize_severity(recent_diagnostics)
        
        category_summary = {}
        for diag in recent_diagnostics:
            category = diag.category.value
            category_summary[category] = category_summary.get(category, 0) + 1
        
        return {
            "period_hours": hours,
            "total_diagnostics": len(recent_diagnostics),
            "severity_summary": severity_summary,
            "category_summary": category_summary,
            "recent_diagnostics": [
                {
                    "category": d.category.value,
                    "severity": d.severity.value,
                    "title": d.title,
                    "detected_at": d.detected_at.isoformat()
                }
                for d in recent_diagnostics[-10:]
            ]
        }



