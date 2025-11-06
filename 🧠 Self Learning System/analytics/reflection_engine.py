"""
效果反思引擎
为所有模块提供统一的效果反思和自我改进功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class ReflectionEngine:
    """效果反思引擎"""
    
    def __init__(self):
        """初始化反思引擎"""
        self.module_reflections = {}
        self.improvement_suggestions = []
        self.performance_baselines = {}
    
    def reflect_on_module_performance(
        self,
        module_name: str,
        metrics: Dict[str, Any],
        time_period: str = "daily"
    ) -> Dict[str, Any]:
        """
        对模块性能进行反思
        
        Args:
            module_name: 模块名称
            metrics: 性能指标
            time_period: 时间周期
        
        Returns:
            反思结果
        """
        # 创建反思记录
        reflection_id = f"REF_{module_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 与基线对比
        baseline = self._get_or_create_baseline(module_name, metrics)
        comparison = self._compare_with_baseline(metrics, baseline)
        
        # 识别问题
        issues = self._identify_issues(module_name, metrics, comparison)
        
        # 生成改进建议
        suggestions = self._generate_suggestions(module_name, issues, comparison)
        
        # 评估整体健康度
        health_score = self._calculate_health_score(metrics, issues)
        
        reflection = {
            "reflection_id": reflection_id,
            "module_name": module_name,
            "time_period": time_period,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "baseline_comparison": comparison,
            "identified_issues": issues,
            "improvement_suggestions": suggestions,
            "health_score": health_score,
            "overall_assessment": self._get_assessment(health_score)
        }
        
        # 保存反思记录
        if module_name not in self.module_reflections:
            self.module_reflections[module_name] = []
        self.module_reflections[module_name].append(reflection)
        
        # 保存改进建议
        for suggestion in suggestions:
            self.improvement_suggestions.append({
                "module": module_name,
                "suggestion": suggestion,
                "priority": suggestion.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "implemented": False
            })
        
        return {
            "success": True,
            "reflection": reflection
        }
    
    def _get_or_create_baseline(
        self,
        module_name: str,
        current_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        获取或创建性能基线
        
        Args:
            module_name: 模块名称
            current_metrics: 当前指标
        
        Returns:
            基线指标
        """
        if module_name not in self.performance_baselines:
            # 首次创建基线
            self.performance_baselines[module_name] = {
                "created_at": datetime.now().isoformat(),
                "metrics": current_metrics,
                "update_count": 1
            }
        
        return self.performance_baselines[module_name]["metrics"]
    
    def _compare_with_baseline(
        self,
        current: Dict[str, Any],
        baseline: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        与基线对比
        
        Args:
            current: 当前指标
            baseline: 基线指标
        
        Returns:
            对比结果
        """
        comparison = {}
        
        for key, value in current.items():
            if key in baseline:
                baseline_value = baseline[key]
                
                # 如果是数值，计算变化
                if isinstance(value, (int, float)) and isinstance(baseline_value, (int, float)):
                    if baseline_value != 0:
                        change_percent = ((value - baseline_value) / baseline_value) * 100
                    else:
                        change_percent = 100 if value > 0 else 0
                    
                    comparison[key] = {
                        "current": value,
                        "baseline": baseline_value,
                        "change": value - baseline_value,
                        "change_percent": round(change_percent, 2),
                        "trend": "improving" if change_percent > 0 else "declining" if change_percent < 0 else "stable"
                    }
        
        return comparison
    
    def _identify_issues(
        self,
        module_name: str,
        metrics: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        识别问题
        
        Args:
            module_name: 模块名称
            metrics: 指标
            comparison: 对比结果
        
        Returns:
            问题列表
        """
        issues = []
        
        # 定义阈值规则
        thresholds = {
            "success_rate": {"min": 90, "severity": "high"},
            "response_time": {"max": 5000, "severity": "medium"},
            "error_rate": {"max": 5, "severity": "high"},
            "utilization_rate": {"min": 60, "max": 95, "severity": "medium"},
            "completion_rate": {"min": 85, "severity": "high"}
        }
        
        # 检查指标是否在正常范围
        for metric_name, threshold in thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                
                if "min" in threshold and value < threshold["min"]:
                    issues.append({
                        "type": "below_threshold",
                        "metric": metric_name,
                        "current_value": value,
                        "threshold": threshold["min"],
                        "severity": threshold["severity"],
                        "description": f"{metric_name}低于阈值{threshold['min']}"
                    })
                
                if "max" in threshold and value > threshold["max"]:
                    issues.append({
                        "type": "above_threshold",
                        "metric": metric_name,
                        "current_value": value,
                        "threshold": threshold["max"],
                        "severity": threshold["severity"],
                        "description": f"{metric_name}超过阈值{threshold['max']}"
                    })
        
        # 检查趋势
        for metric_name, comp in comparison.items():
            if comp.get("trend") == "declining" and abs(comp.get("change_percent", 0)) > 10:
                issues.append({
                    "type": "declining_trend",
                    "metric": metric_name,
                    "change_percent": comp["change_percent"],
                    "severity": "medium",
                    "description": f"{metric_name}下降{abs(comp['change_percent'])}%"
                })
        
        return issues
    
    def _generate_suggestions(
        self,
        module_name: str,
        issues: List[Dict[str, Any]],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        生成改进建议
        
        Args:
            module_name: 模块名称
            issues: 问题列表
            comparison: 对比结果
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 根据问题生成建议
        for issue in issues:
            metric = issue["metric"]
            severity = issue["severity"]
            
            suggestion = {
                "issue": issue["description"],
                "metric": metric,
                "priority": severity,
                "actions": []
            }
            
            # 根据指标类型生成具体建议
            if metric == "success_rate":
                suggestion["actions"] = [
                    "检查失败原因日志",
                    "优化错误处理机制",
                    "增加重试逻辑",
                    "完善输入验证"
                ]
            
            elif metric == "response_time":
                suggestion["actions"] = [
                    "添加缓存机制",
                    "优化数据库查询",
                    "使用异步处理",
                    "减少不必要的计算"
                ]
            
            elif metric == "error_rate":
                suggestion["actions"] = [
                    "分析错误类型",
                    "修复常见bug",
                    "增强异常捕获",
                    "改进测试覆盖"
                ]
            
            elif metric == "utilization_rate":
                if issue["type"] == "below_threshold":
                    suggestion["actions"] = [
                        "提升用户培训",
                        "优化功能可发现性",
                        "改进用户体验",
                        "增加使用提示"
                    ]
                else:
                    suggestion["actions"] = [
                        "增加资源配置",
                        "优化负载均衡",
                        "考虑横向扩展"
                    ]
            
            suggestions.append(suggestion)
        
        # 添加趋势改进建议
        for metric_name, comp in comparison.items():
            if comp.get("trend") == "improving" and comp.get("change_percent", 0) > 20:
                suggestions.append({
                    "type": "best_practice",
                    "metric": metric_name,
                    "priority": "low",
                    "description": f"{metric_name}表现优秀，提升{comp['change_percent']}%",
                    "actions": ["总结成功经验", "应用到其他模块"]
                })
        
        return suggestions
    
    def _calculate_health_score(
        self,
        metrics: Dict[str, Any],
        issues: List[Dict[str, Any]]
    ) -> float:
        """
        计算健康度分数
        
        Args:
            metrics: 指标
            issues: 问题列表
        
        Returns:
            健康度分数（0-100）
        """
        score = 100
        
        # 每个高严重度问题扣15分
        high_severity = sum(1 for i in issues if i.get("severity") == "high")
        score -= high_severity * 15
        
        # 每个中严重度问题扣8分
        medium_severity = sum(1 for i in issues if i.get("severity") == "medium")
        score -= medium_severity * 8
        
        # 每个低严重度问题扣3分
        low_severity = sum(1 for i in issues if i.get("severity") == "low")
        score -= low_severity * 3
        
        return max(0, min(100, score))
    
    def _get_assessment(self, health_score: float) -> str:
        """
        获取整体评估
        
        Args:
            health_score: 健康分数
        
        Returns:
            评估结果
        """
        if health_score >= 90:
            return "优秀：模块运行健康，继续保持"
        elif health_score >= 75:
            return "良好：总体正常，有小幅改进空间"
        elif health_score >= 60:
            return "一般：存在一些问题，需要关注和改进"
        else:
            return "需改进：存在较多问题，需要优先处理"
    
    def get_module_reflection_history(
        self,
        module_name: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        获取模块反思历史
        
        Args:
            module_name: 模块名称
            limit: 返回数量限制
        
        Returns:
            反思历史
        """
        if module_name not in self.module_reflections:
            return {
                "success": True,
                "module_name": module_name,
                "message": "暂无反思记录"
            }
        
        reflections = self.module_reflections[module_name][-limit:]
        
        # 分析趋势
        if len(reflections) >= 2:
            first_score = reflections[0]["health_score"]
            last_score = reflections[-1]["health_score"]
            trend = "improving" if last_score > first_score else "declining" if last_score < first_score else "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "success": True,
            "module_name": module_name,
            "total_reflections": len(reflections),
            "reflections": reflections,
            "trend": trend
        }
    
    def get_all_modules_health(self) -> Dict[str, Any]:
        """
        获取所有模块健康度
        
        Returns:
            所有模块健康度
        """
        health_summary = {}
        
        for module_name, reflections in self.module_reflections.items():
            if reflections:
                latest = reflections[-1]
                health_summary[module_name] = {
                    "health_score": latest["health_score"],
                    "assessment": latest["overall_assessment"],
                    "issue_count": len(latest["identified_issues"]),
                    "last_reflection": latest["timestamp"]
                }
        
        # 计算整体健康度
        if health_summary:
            overall_health = statistics.mean([
                h["health_score"] for h in health_summary.values()
            ])
        else:
            overall_health = 100
        
        return {
            "success": True,
            "overall_health_score": round(overall_health, 2),
            "modules": health_summary,
            "total_modules": len(health_summary)
        }
    
    def get_pending_improvements(
        self,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取待实施的改进建议
        
        Args:
            priority: 优先级过滤
        
        Returns:
            改进建议列表
        """
        pending = [s for s in self.improvement_suggestions if not s["implemented"]]
        
        if priority:
            pending = [s for s in pending if s["priority"] == priority]
        
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        pending.sort(key=lambda x: priority_order.get(x["priority"], 999))
        
        return {
            "success": True,
            "total_pending": len(pending),
            "suggestions": pending
        }
    
    def mark_suggestion_implemented(
        self,
        suggestion_index: int,
        implementation_note: str = ""
    ) -> Dict[str, Any]:
        """
        标记建议已实施
        
        Args:
            suggestion_index: 建议索引
            implementation_note: 实施说明
        
        Returns:
            更新结果
        """
        if suggestion_index >= len(self.improvement_suggestions):
            return {"success": False, "error": "建议不存在"}
        
        suggestion = self.improvement_suggestions[suggestion_index]
        suggestion["implemented"] = True
        suggestion["implemented_at"] = datetime.now().isoformat()
        suggestion["implementation_note"] = implementation_note
        
        return {
            "success": True,
            "message": "建议已标记为已实施",
            "suggestion": suggestion
        }


# 创建默认实例
reflection_engine = ReflectionEngine()

