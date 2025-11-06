"""
任务性能分析器
实现任务执行效率、瓶颈识别、成功率分析等深度分析功能
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class TaskPerformanceAnalyzer:
    """任务性能分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.task_metrics = []
        self.bottleneck_records = []
        self.efficiency_trends = {}
    
    def analyze_task_efficiency(
        self,
        task_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析任务执行效率
        
        Args:
            task_id: 任务ID
            task_data: 任务数据（包含执行时间、步骤等）
        
        Returns:
            效率分析报告
        """
        # 计算关键指标
        planned_time = task_data.get("planned_duration", 0)
        actual_time = task_data.get("actual_duration", 0)
        
        # 效率指标
        if planned_time > 0:
            efficiency_ratio = (planned_time / actual_time) * 100 if actual_time > 0 else 0
            time_variance = ((actual_time - planned_time) / planned_time) * 100
        else:
            efficiency_ratio = 100
            time_variance = 0
        
        # 步骤分析
        steps = task_data.get("steps", [])
        total_steps = len(steps)
        completed_steps = sum(1 for s in steps if s.get("status") == "completed")
        failed_steps = sum(1 for s in steps if s.get("status") == "failed")
        
        completion_rate = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        
        # 识别最慢的步骤
        slowest_step = None
        if steps:
            steps_with_time = [s for s in steps if s.get("duration")]
            if steps_with_time:
                slowest_step = max(steps_with_time, key=lambda x: x.get("duration", 0))
        
        analysis = {
            "task_id": task_id,
            "efficiency_metrics": {
                "planned_time_minutes": planned_time,
                "actual_time_minutes": actual_time,
                "efficiency_ratio": round(efficiency_ratio, 2),
                "time_variance_percent": round(time_variance, 2),
                "time_saved_minutes": round(planned_time - actual_time, 2)
            },
            "completion_metrics": {
                "total_steps": total_steps,
                "completed_steps": completed_steps,
                "failed_steps": failed_steps,
                "completion_rate": round(completion_rate, 2)
            },
            "bottleneck_analysis": {
                "slowest_step": slowest_step.get("name") if slowest_step else None,
                "slowest_step_duration": slowest_step.get("duration") if slowest_step else 0,
                "bottleneck_percentage": round((slowest_step.get("duration", 0) / actual_time * 100), 2) if actual_time > 0 and slowest_step else 0
            },
            "performance_grade": self._calculate_performance_grade(efficiency_ratio, completion_rate)
        }
        
        # 记录指标
        self.task_metrics.append({
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        })
        
        return {
            "success": True,
            "analysis": analysis
        }
    
    def identify_bottlenecks(
        self,
        task_id: str,
        execution_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        识别任务瓶颈
        
        Args:
            task_id: 任务ID
            execution_data: 执行数据
        
        Returns:
            瓶颈分析
        """
        bottlenecks = []
        
        steps = execution_data.get("steps", [])
        
        # 分析1: 时间瓶颈
        if steps:
            total_time = sum(s.get("duration", 0) for s in steps)
            avg_time = total_time / len(steps) if steps else 0
            
            for step in steps:
                step_time = step.get("duration", 0)
                if step_time > avg_time * 2:  # 超过平均时间2倍
                    bottlenecks.append({
                        "type": "time_bottleneck",
                        "step_name": step.get("name"),
                        "step_id": step.get("step_id"),
                        "duration": step_time,
                        "average_duration": avg_time,
                        "severity": "high" if step_time > avg_time * 3 else "medium",
                        "impact": f"占总时间的{round((step_time / total_time * 100), 2)}%"
                    })
        
        # 分析2: 资源瓶颈
        resource_usage = execution_data.get("resource_usage", {})
        for resource, usage in resource_usage.items():
            if usage > 80:  # 使用率超过80%
                bottlenecks.append({
                    "type": "resource_bottleneck",
                    "resource": resource,
                    "usage_percent": usage,
                    "severity": "high" if usage > 90 else "medium",
                    "recommendation": f"建议优化{resource}使用或增加资源"
                })
        
        # 分析3: 依赖瓶颈
        dependencies = execution_data.get("dependencies", [])
        for dep in dependencies:
            if dep.get("wait_time", 0) > 60:  # 等待时间超过60秒
                bottlenecks.append({
                    "type": "dependency_bottleneck",
                    "dependency": dep.get("name"),
                    "wait_time_seconds": dep.get("wait_time"),
                    "severity": "medium",
                    "recommendation": "建议并行化或优化依赖任务"
                })
        
        # 分析4: 错误瓶颈
        errors = execution_data.get("errors", [])
        if len(errors) > 3:
            bottlenecks.append({
                "type": "error_bottleneck",
                "error_count": len(errors),
                "severity": "high",
                "common_errors": self._find_common_errors(errors),
                "recommendation": "需要修复频繁出现的错误"
            })
        
        # 记录瓶颈
        bottleneck_record = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "bottlenecks": bottlenecks,
            "total_bottlenecks": len(bottlenecks)
        }
        
        self.bottleneck_records.append(bottleneck_record)
        
        return {
            "success": True,
            "task_id": task_id,
            "bottlenecks": bottlenecks,
            "total_count": len(bottlenecks),
            "severity_distribution": self._get_severity_distribution(bottlenecks)
        }
    
    def analyze_success_rate(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        分析任务成功率
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            成功率分析
        """
        # 筛选时间范围内的任务
        tasks_in_range = [
            m for m in self.task_metrics
            if start_date <= m["timestamp"][:10] <= end_date
        ]
        
        if not tasks_in_range:
            return {
                "success": True,
                "message": "该时期内无任务数据"
            }
        
        # 计算成功率
        total_tasks = len(tasks_in_range)
        successful_tasks = sum(
            1 for m in tasks_in_range
            if m["analysis"]["completion_metrics"]["completion_rate"] == 100
        )
        
        success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # 按日期统计
        daily_stats = defaultdict(lambda: {"total": 0, "success": 0})
        for metric in tasks_in_range:
            date = metric["timestamp"][:10]
            daily_stats[date]["total"] += 1
            if metric["analysis"]["completion_metrics"]["completion_rate"] == 100:
                daily_stats[date]["success"] += 1
        
        # 计算每日成功率
        daily_success_rates = {
            date: round((stats["success"] / stats["total"] * 100), 2)
            for date, stats in daily_stats.items()
        }
        
        # 趋势分析
        sorted_dates = sorted(daily_success_rates.keys())
        if len(sorted_dates) >= 2:
            first_week_avg = statistics.mean([daily_success_rates[d] for d in sorted_dates[:7]])
            last_week_avg = statistics.mean([daily_success_rates[d] for d in sorted_dates[-7:]])
            trend = "上升" if last_week_avg > first_week_avg else "下降"
        else:
            trend = "数据不足"
        
        return {
            "success": True,
            "period": {"start": start_date, "end": end_date},
            "overall": {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": total_tasks - successful_tasks,
                "success_rate": round(success_rate, 2)
            },
            "daily_statistics": dict(daily_stats),
            "daily_success_rates": daily_success_rates,
            "trend": trend
        }
    
    def analyze_failure_reasons(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        分析失败原因
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            失败原因分析
        """
        # 筛选失败的任务
        failed_tasks = [
            m for m in self.task_metrics
            if start_date <= m["timestamp"][:10] <= end_date
            and m["analysis"]["completion_metrics"]["completion_rate"] < 100
        ]
        
        if not failed_tasks:
            return {
                "success": True,
                "message": "该时期内无失败任务"
            }
        
        # 统计失败原因（从瓶颈记录中提取）
        failure_reasons = defaultdict(int)
        
        for task_metric in failed_tasks:
            task_id = task_metric["task_id"]
            
            # 查找对应的瓶颈记录
            bottleneck = next(
                (b for b in self.bottleneck_records if b["task_id"] == task_id),
                None
            )
            
            if bottleneck:
                for b in bottleneck["bottlenecks"]:
                    reason_key = f"{b['type']}_{b.get('severity', 'unknown')}"
                    failure_reasons[reason_key] += 1
        
        # 找出Top失败原因
        top_reasons = sorted(
            failure_reasons.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            "success": True,
            "period": {"start": start_date, "end": end_date},
            "total_failed_tasks": len(failed_tasks),
            "failure_reasons": dict(failure_reasons),
            "top_reasons": dict(top_reasons),
            "recommendations": self._generate_improvement_recommendations(dict(top_reasons))
        }
    
    def generate_efficiency_trend_report(
        self,
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """
        生成效率趋势报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            趋势报告
        """
        # 筛选任务
        tasks_in_range = [
            m for m in self.task_metrics
            if start_date <= m["timestamp"][:10] <= end_date
        ]
        
        if not tasks_in_range:
            return {
                "success": True,
                "message": "该时期内无任务数据"
            }
        
        # 按周统计
        weekly_stats = defaultdict(lambda: {
            "tasks": [],
            "avg_efficiency": 0,
            "avg_completion_rate": 0
        })
        
        for metric in tasks_in_range:
            # 计算周数
            date = datetime.fromisoformat(metric["timestamp"])
            week_key = date.strftime('%Y-W%W')
            
            weekly_stats[week_key]["tasks"].append(metric)
        
        # 计算每周平均指标
        for week, stats in weekly_stats.items():
            tasks = stats["tasks"]
            
            avg_efficiency = statistics.mean([
                t["analysis"]["efficiency_metrics"]["efficiency_ratio"]
                for t in tasks
            ])
            
            avg_completion = statistics.mean([
                t["analysis"]["completion_metrics"]["completion_rate"]
                for t in tasks
            ])
            
            stats["avg_efficiency"] = round(avg_efficiency, 2)
            stats["avg_completion_rate"] = round(avg_completion, 2)
            stats["task_count"] = len(tasks)
        
        # 计算趋势
        sorted_weeks = sorted(weekly_stats.keys())
        if len(sorted_weeks) >= 2:
            first_week_efficiency = weekly_stats[sorted_weeks[0]]["avg_efficiency"]
            last_week_efficiency = weekly_stats[sorted_weeks[-1]]["avg_efficiency"]
            
            if last_week_efficiency > first_week_efficiency:
                trend = "持续改善"
                trend_percentage = round(
                    ((last_week_efficiency - first_week_efficiency) / first_week_efficiency * 100),
                    2
                )
            else:
                trend = "需要关注"
                trend_percentage = round(
                    ((first_week_efficiency - last_week_efficiency) / first_week_efficiency * 100),
                    2
                )
        else:
            trend = "数据不足"
            trend_percentage = 0
        
        return {
            "success": True,
            "period": {"start": start_date, "end": end_date},
            "weekly_statistics": dict(weekly_stats),
            "trend_analysis": {
                "overall_trend": trend,
                "improvement_percentage": trend_percentage,
                "total_weeks": len(sorted_weeks)
            },
            "recommendations": self._generate_trend_recommendations(trend, trend_percentage)
        }
    
    def identify_optimization_opportunities(
        self,
        task_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        识别优化机会
        
        Args:
            task_type: 任务类型（可选）
        
        Returns:
            优化机会列表
        """
        opportunities = []
        
        # 从瓶颈记录中识别
        bottleneck_types = defaultdict(int)
        for record in self.bottleneck_records:
            for bottleneck in record["bottlenecks"]:
                bottleneck_types[bottleneck["type"]] += 1
        
        # 找出最常见的瓶颈
        top_bottlenecks = sorted(
            bottleneck_types.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        for bottleneck_type, count in top_bottlenecks:
            opportunity = {
                "type": bottleneck_type,
                "occurrence_count": count,
                "priority": "high" if count > 10 else "medium",
                "optimization_suggestion": self._get_optimization_suggestion(bottleneck_type),
                "estimated_improvement": self._estimate_improvement(bottleneck_type, count)
            }
            opportunities.append(opportunity)
        
        return {
            "success": True,
            "total_opportunities": len(opportunities),
            "opportunities": opportunities,
            "estimated_total_improvement": sum(o["estimated_improvement"] for o in opportunities)
        }
    
    def _calculate_performance_grade(
        self,
        efficiency_ratio: float,
        completion_rate: float
    ) -> str:
        """
        计算性能等级
        
        Args:
            efficiency_ratio: 效率比
            completion_rate: 完成率
        
        Returns:
            等级
        """
        score = (efficiency_ratio * 0.6 + completion_rate * 0.4)
        
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 60:
            return "及格"
        else:
            return "需改进"
    
    def _find_common_errors(self, errors: List[Dict[str, Any]]) -> List[str]:
        """找出常见错误"""
        error_types = defaultdict(int)
        for error in errors:
            error_type = error.get("type", "unknown")
            error_types[error_type] += 1
        
        return [
            error_type for error_type, count in 
            sorted(error_types.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
    
    def _get_severity_distribution(
        self,
        bottlenecks: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """获取严重度分布"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        for b in bottlenecks:
            severity = b.get("severity", "medium")
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _generate_improvement_recommendations(
        self,
        top_reasons: Dict[str, int]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        for reason, count in top_reasons.items():
            if "time_bottleneck" in reason:
                recommendations.append(f"优化耗时步骤，{count}个任务受影响")
            elif "resource_bottleneck" in reason:
                recommendations.append(f"增加资源配置，{count}个任务受影响")
            elif "dependency_bottleneck" in reason:
                recommendations.append(f"优化依赖关系，{count}个任务受影响")
            elif "error_bottleneck" in reason:
                recommendations.append(f"修复常见错误，{count}个任务受影响")
        
        return recommendations
    
    def _generate_trend_recommendations(
        self,
        trend: str,
        percentage: float
    ) -> List[str]:
        """生成趋势建议"""
        recommendations = []
        
        if trend == "持续改善":
            recommendations.append(f"效率提升{percentage}%，继续保持当前优化策略")
        elif trend == "需要关注":
            recommendations.append(f"效率下降{percentage}%，需要识别并解决问题")
        else:
            recommendations.append("数据不足，建议持续监控")
        
        return recommendations
    
    def _get_optimization_suggestion(self, bottleneck_type: str) -> str:
        """获取优化建议"""
        suggestions = {
            "time_bottleneck": "考虑并行化处理、优化算法或增加缓存",
            "resource_bottleneck": "增加资源配置或优化资源使用",
            "dependency_bottleneck": "重新设计依赖关系或实现异步处理",
            "error_bottleneck": "修复bug、增加错误处理、提升代码质量"
        }
        return suggestions.get(bottleneck_type, "需要详细分析")
    
    def _estimate_improvement(self, bottleneck_type: str, count: int) -> float:
        """估算改进潜力（百分比）"""
        base_improvement = {
            "time_bottleneck": 20,
            "resource_bottleneck": 15,
            "dependency_bottleneck": 10,
            "error_bottleneck": 25
        }
        
        base = base_improvement.get(bottleneck_type, 5)
        # 出现次数越多，改进潜力越大
        return min(base * (1 + count / 10), 50)


# 创建默认实例
default_task_analyzer = TaskPerformanceAnalyzer()

