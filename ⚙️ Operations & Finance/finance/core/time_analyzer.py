"""
工时分析器⭐深化版
工时统计、效率分析、成本分析、优化建议、瓶颈识别
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import statistics
import math

class TimeAnalyzer:
    """
    工时分析器⭐深化版
    
    功能：
    1. 工时统计（多维度）
    2. 工时效率分析（深化）
    3. 工时成本分析（深化）
    4. 瓶颈识别
    5. 工时优化建议（深化）
    6. 资源利用率分析
    7. 工时预测
    """
    
    def __init__(self, erp_connector=None):
        """
        初始化工时分析器
        
        Args:
            erp_connector: ERP连接器（用于获取数据）
        """
        self.erp_connector = erp_connector
    
    async def analyze_work_hours(
        self,
        project_id: Optional[int] = None,
        period: str = "30d"
    ) -> Dict[str, Any]:
        """
        分析工时⭐深化版
        
        分析维度：
        - 总工时统计
        - 日均工时
        - 工时分布
        - 工时趋势
        - 异常工时检测
        - 资源利用率
        """
        # 从ERP获取工时数据
        work_hours_data = await self._get_work_hours_data(project_id, period)
        
        if not work_hours_data:
            return {
                "project_id": project_id,
                "period": period,
                "total_hours": 0.0,
                "average_daily": 0.0,
                "efficiency": 0.0,
                "cost": 0.0,
                "message": "工时数据不足"
            }
        
        # 提取工时数据
        hours_list = [item["hours"] for item in work_hours_data]
        dates = [item["date"] for item in work_hours_data]
        
        # 基础统计
        total_hours = sum(hours_list)
        avg_daily = statistics.mean(hours_list) if hours_list else 0.0
        max_daily = max(hours_list) if hours_list else 0.0
        min_daily = min(hours_list) if hours_list else 0.0
        
        # 工时分布分析
        distribution = self._analyze_hours_distribution(hours_list)
        
        # 工时趋势分析
        trend = self._analyze_hours_trend(hours_list, dates)
        
        # 异常检测
        anomalies = self._detect_hours_anomalies(hours_list, dates)
        
        # 效率分析
        efficiency = self._calculate_efficiency(hours_list, work_hours_data)
        
        # 成本分析
        cost_analysis = self._analyze_hours_cost(hours_list, work_hours_data)
        
        # 资源利用率
        resource_utilization = self._analyze_resource_utilization(work_hours_data)
        
        return {
            "project_id": project_id,
            "period": period,
            "total_hours": round(total_hours, 2),
            "average_daily": round(avg_daily, 2),
            "max_daily": round(max_daily, 2),
            "min_daily": round(min_daily, 2),
            "hours_distribution": distribution,
            "trend": trend,
            "anomalies": anomalies,
            "efficiency": efficiency,
            "cost_analysis": cost_analysis,
            "resource_utilization": resource_utilization,
            "recommendations": self._generate_hours_recommendations(
                total_hours, avg_daily, efficiency, anomalies
            )
        }
    
    async def analyze_efficiency(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        分析效率⭐深化版
        
        分析维度：
        - 平均效率
        - 效率分布
        - 瓶颈任务识别
        - 效率趋势
        - 影响因素分析
        """
        if not tasks:
            return {
                "average_efficiency": 0.0,
                "bottlenecks": [],
                "recommendations": [],
                "message": "任务数据为空"
            }
        
        # 提取效率数据
        efficiencies = []
        task_details = []
        
        for task in tasks:
            planned_hours = task.get("planned_hours", 0)
            actual_hours = task.get("actual_hours", 0)
            
            if planned_hours > 0:
                efficiency = planned_hours / actual_hours if actual_hours > 0 else 0
                efficiencies.append(efficiency)
                task_details.append({
                    "task_id": task.get("id"),
                    "task_name": task.get("name", ""),
                    "efficiency": efficiency,
                    "planned_hours": planned_hours,
                    "actual_hours": actual_hours,
                    "variance": actual_hours - planned_hours
                })
        
        if not efficiencies:
            return {
                "average_efficiency": 0.0,
                "bottlenecks": [],
                "recommendations": []
            }
        
        # 平均效率
        avg_efficiency = statistics.mean(efficiencies)
        
        # 效率分布
        efficiency_distribution = {
            "high": len([e for e in efficiencies if e >= 0.9]),
            "medium": len([e for e in efficiencies if 0.7 <= e < 0.9]),
            "low": len([e for e in efficiencies if e < 0.7])
        }
        
        # 识别瓶颈（效率低的任务）
        bottlenecks = [
            task for task in task_details
            if task["efficiency"] < 0.7 or task["variance"] > task["planned_hours"] * 0.3
        ]
        
        # 效率趋势分析
        efficiency_trend = self._analyze_efficiency_trend(task_details)
        
        # 影响因素分析
        factors = self._analyze_efficiency_factors(task_details)
        
        # 生成建议
        recommendations = self._generate_efficiency_recommendations(
            avg_efficiency, bottlenecks, factors
        )
        
        return {
            "average_efficiency": round(avg_efficiency, 4),
            "efficiency_distribution": efficiency_distribution,
            "bottlenecks": bottlenecks[:10],  # 返回前10个瓶颈
            "efficiency_trend": efficiency_trend,
            "factors": factors,
            "recommendations": recommendations,
            "task_count": len(tasks),
            "high_efficiency_tasks": len([e for e in efficiencies if e >= 0.9]),
            "low_efficiency_tasks": len([e for e in efficiencies if e < 0.7])
        }
    
    async def optimize_work_hours(
        self,
        project_id: int,
        current_hours: float,
        target_hours: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        优化工时⭐深化版
        
        优化维度：
        - 工时削减方案
        - 效率提升方案
        - 资源重新分配
        - 流程优化建议
        - 预期节省
        """
        # 获取项目详细信息
        project_data = await self._get_project_data(project_id)
        
        # 计算目标工时
        if not target_hours:
            # 默认目标：减少10%
            target_hours = current_hours * 0.9
        else:
            target_hours = min(target_hours, current_hours)
        
        reduction_target = current_hours - target_hours
        reduction_rate = reduction_target / current_hours if current_hours > 0 else 0
        
        # 生成优化方案
        optimization_plans = []
        
        # 方案1：提升效率
        efficiency_plan = self._generate_efficiency_plan(
            project_data, current_hours, reduction_target
        )
        if efficiency_plan:
            optimization_plans.append(efficiency_plan)
        
        # 方案2：资源重新分配
        resource_plan = self._generate_resource_plan(
            project_data, current_hours, reduction_target
        )
        if resource_plan:
            optimization_plans.append(resource_plan)
        
        # 方案3：流程优化
        process_plan = self._generate_process_plan(
            project_data, current_hours, reduction_target
        )
        if process_plan:
            optimization_plans.append(process_plan)
        
        # 方案4：自动化建议
        automation_plan = self._generate_automation_plan(
            project_data, current_hours, reduction_target
        )
        if automation_plan:
            optimization_plans.append(automation_plan)
        
        # 计算预期节省
        expected_savings = self._calculate_expected_savings(
            optimization_plans, current_hours
        )
        
        return {
            "project_id": project_id,
            "current_hours": round(current_hours, 2),
            "target_hours": round(target_hours, 2),
            "reduction_target": round(reduction_target, 2),
            "reduction_rate": round(reduction_rate * 100, 2),
            "optimization_plans": optimization_plans,
            "expected_savings": expected_savings,
            "feasibility": self._assess_feasibility(optimization_plans, reduction_target),
            "implementation_priority": self._prioritize_plans(optimization_plans)
        }
    
    # ============ 辅助方法 ============
    
    async def _get_work_hours_data(
        self,
        project_id: Optional[int],
        period: str
    ) -> List[Dict[str, Any]]:
        """从ERP获取工时数据"""
        if self.erp_connector:
            # TODO: 调用ERP API获取工时数据
            pass
        
        # 模拟数据
        days = 30 if period == "30d" else 7 if period == "7d" else 90 if period == "90d" else 365
        return [
            {
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "hours": 8.0 + (i % 5) * 0.5 - 1.0,  # 模拟工时波动
                "employee_id": f"EMP{(i % 10) + 1}",
                "task_type": ["开发", "测试", "设计"][i % 3]
            }
            for i in range(days, 0, -1)
        ]
    
    def _analyze_hours_distribution(
        self,
        hours_list: List[float]
    ) -> Dict[str, Any]:
        """分析工时分布"""
        if not hours_list:
            return {}
        
        return {
            "mean": round(statistics.mean(hours_list), 2),
            "median": round(statistics.median(hours_list), 2),
            "std": round(statistics.stdev(hours_list) if len(hours_list) > 1 else 0, 2),
            "range": {
                "min": round(min(hours_list), 2),
                "max": round(max(hours_list), 2)
            }
        }
    
    def _analyze_hours_trend(
        self,
        hours_list: List[float],
        dates: List[str]
    ) -> Dict[str, Any]:
        """分析工时趋势"""
        if len(hours_list) < 2:
            return {"direction": "数据不足", "strength": 0.0}
        
        # 计算趋势（类似价格趋势）
        n = len(hours_list)
        x = list(range(n))
        y = hours_list
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        hours_range = max(hours_list) - min(hours_list)
        if hours_range > 0:
            strength = abs(slope * n) / hours_range
            strength = min(strength, 1.0)
        else:
            strength = 0.0
        
        if slope > 0.1:
            direction = "上升"
        elif slope < -0.1:
            direction = "下降"
        else:
            direction = "平稳"
        
        return {
            "direction": direction,
            "strength": round(strength, 4),
            "slope": round(slope, 4)
        }
    
    def _detect_hours_anomalies(
        self,
        hours_list: List[float],
        dates: List[str]
    ) -> List[Dict[str, Any]]:
        """检测工时异常"""
        if len(hours_list) < 3:
            return []
        
        anomalies = []
        mean_hours = statistics.mean(hours_list)
        std_hours = statistics.stdev(hours_list) if len(hours_list) > 1 else 0
        
        if std_hours == 0:
            return []
        
        for i, hours in enumerate(hours_list):
            z_score = abs((hours - mean_hours) / std_hours)
            if z_score > 2:  # 2倍标准差
                anomalies.append({
                    "date": dates[i] if i < len(dates) else "",
                    "hours": round(hours, 2),
                    "deviation": round(z_score, 2),
                    "type": "异常高" if hours > mean_hours else "异常低"
                })
        
        return anomalies
    
    def _calculate_efficiency(
        self,
        hours_list: List[float],
        work_hours_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """计算效率"""
        # 简化实现：基于标准工时（8小时/天）
        standard_hours_per_day = 8.0
        avg_hours = statistics.mean(hours_list) if hours_list else 0.0
        
        if avg_hours > 0:
            efficiency = min(standard_hours_per_day / avg_hours, 1.0) if avg_hours > standard_hours_per_day else avg_hours / standard_hours_per_day
        else:
            efficiency = 0.0
        
        return {
            "efficiency": round(efficiency, 4),
            "level": "高" if efficiency >= 0.9 else "中" if efficiency >= 0.7 else "低"
        }
    
    def _analyze_hours_cost(
        self,
        hours_list: List[float],
        work_hours_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析工时成本"""
        total_hours = sum(hours_list)
        avg_hourly_rate = 100.0  # 假设每小时100元
        total_cost = total_hours * avg_hourly_rate
        
        return {
            "total_cost": round(total_cost, 2),
            "average_hourly_rate": avg_hourly_rate,
            "cost_per_day": round(statistics.mean(hours_list) * avg_hourly_rate, 2) if hours_list else 0.0
        }
    
    def _analyze_resource_utilization(
        self,
        work_hours_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析资源利用率"""
        # 统计不同资源的使用情况
        resource_usage = {}
        for item in work_hours_data:
            resource_id = item.get("employee_id", "unknown")
            hours = item.get("hours", 0)
            resource_usage[resource_id] = resource_usage.get(resource_id, 0) + hours
        
        if not resource_usage:
            return {"utilization": 0.0, "resources": []}
        
        # 计算平均利用率
        max_hours = max(resource_usage.values())
        avg_hours = statistics.mean(resource_usage.values())
        utilization = avg_hours / max_hours if max_hours > 0 else 0.0
        
        return {
            "utilization": round(utilization, 4),
            "resources": [
                {"resource_id": k, "total_hours": round(v, 2)}
                for k, v in resource_usage.items()
            ],
            "resource_count": len(resource_usage)
        }
    
    def _generate_hours_recommendations(
        self,
        total_hours: float,
        avg_daily: float,
        efficiency: Dict[str, Any],
        anomalies: List[Dict[str, Any]]
    ) -> List[str]:
        """生成工时分析建议"""
        recommendations = []
        
        if avg_daily > 10:
            recommendations.append("日均工时超过10小时，建议优化工作安排")
        
        if efficiency.get("level") == "低":
            recommendations.append("工时效率较低，建议分析原因并改进")
        
        if anomalies:
            recommendations.append(f"检测到{len(anomalies)}个工时异常，建议调查原因")
        
        return recommendations
    
    def _analyze_efficiency_trend(
        self,
        task_details: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析效率趋势"""
        if len(task_details) < 2:
            return {"trend": "数据不足"}
        
        efficiencies = [t["efficiency"] for t in task_details]
        trend = self._analyze_hours_trend(efficiencies, [])
        
        return {
            "direction": trend["direction"],
            "strength": trend["strength"]
        }
    
    def _analyze_efficiency_factors(
        self,
        task_details: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析效率影响因素"""
        factors = []
        
        # 分析工时偏差
        high_variance_tasks = [
            t for t in task_details
            if abs(t["variance"]) > t["planned_hours"] * 0.3
        ]
        
        if high_variance_tasks:
            factors.append({
                "factor": "工时偏差",
                "impact": "高",
                "description": f"{len(high_variance_tasks)}个任务工时偏差超过30%",
                "recommendation": "改进工时估算准确性"
            })
        
        return factors
    
    def _generate_efficiency_recommendations(
        self,
        avg_efficiency: float,
        bottlenecks: List[Dict[str, Any]],
        factors: List[Dict[str, Any]]
    ) -> List[str]:
        """生成效率分析建议"""
        recommendations = []
        
        if avg_efficiency < 0.7:
            recommendations.append("整体效率偏低，建议全面优化")
        
        if bottlenecks:
            recommendations.append(f"发现{len(bottlenecks)}个瓶颈任务，建议优先处理")
        
        for factor in factors:
            recommendations.append(factor["recommendation"])
        
        return recommendations
    
    async def _get_project_data(self, project_id: int) -> Dict[str, Any]:
        """获取项目数据"""
        return {
            "id": project_id,
            "name": f"项目{project_id}",
            "tasks": []
        }
    
    def _generate_efficiency_plan(
        self,
        project_data: Dict[str, Any],
        current_hours: float,
        reduction_target: float
    ) -> Optional[Dict[str, Any]]:
        """生成效率提升方案"""
        if reduction_target <= 0:
            return None
        
        # 假设通过提升效率可以减少15%工时
        efficiency_savings = current_hours * 0.15
        
        return {
            "plan_type": "效率提升",
            "description": "通过优化工作流程、提升技能、减少返工等方式提升效率",
            "expected_savings": round(min(efficiency_savings, reduction_target), 2),
            "implementation_difficulty": "中等",
            "time_to_implement": "2-4周",
            "actions": [
                "优化工作流程",
                "提升员工技能",
                "减少返工",
                "改进工具和方法"
            ]
        }
    
    def _generate_resource_plan(
        self,
        project_data: Dict[str, Any],
        current_hours: float,
        reduction_target: float
    ) -> Optional[Dict[str, Any]]:
        """生成资源重新分配方案"""
        if reduction_target <= 0:
            return None
        
        # 假设通过资源优化可以减少10%工时
        resource_savings = current_hours * 0.10
        
        return {
            "plan_type": "资源优化",
            "description": "通过重新分配资源、平衡工作负载、减少资源浪费",
            "expected_savings": round(min(resource_savings, reduction_target), 2),
            "implementation_difficulty": "低",
            "time_to_implement": "1-2周",
            "actions": [
                "重新分配工作任务",
                "平衡团队工作负载",
                "减少资源闲置",
                "优化人员配置"
            ]
        }
    
    def _generate_process_plan(
        self,
        project_data: Dict[str, Any],
        current_hours: float,
        reduction_target: float
    ) -> Optional[Dict[str, Any]]:
        """生成流程优化方案"""
        if reduction_target <= 0:
            return None
        
        # 假设通过流程优化可以减少8%工时
        process_savings = current_hours * 0.08
        
        return {
            "plan_type": "流程优化",
            "description": "通过简化流程、消除冗余步骤、并行处理等方式优化流程",
            "expected_savings": round(min(process_savings, reduction_target), 2),
            "implementation_difficulty": "中等",
            "time_to_implement": "3-6周",
            "actions": [
                "简化工作流程",
                "消除冗余步骤",
                "并行处理任务",
                "标准化操作"
            ]
        }
    
    def _generate_automation_plan(
        self,
        project_data: Dict[str, Any],
        current_hours: float,
        reduction_target: float
    ) -> Optional[Dict[str, Any]]:
        """生成自动化方案"""
        if reduction_target <= 0:
            return None
        
        # 假设通过自动化可以减少5%工时
        automation_savings = current_hours * 0.05
        
        return {
            "plan_type": "自动化",
            "description": "通过自动化工具和脚本减少重复性工作",
            "expected_savings": round(min(automation_savings, reduction_target), 2),
            "implementation_difficulty": "高",
            "time_to_implement": "4-8周",
            "actions": [
                "识别可自动化任务",
                "开发自动化工具",
                "部署自动化脚本",
                "培训员工使用"
            ]
        }
    
    def _calculate_expected_savings(
        self,
        optimization_plans: List[Dict[str, Any]],
        current_hours: float
    ) -> Dict[str, Any]:
        """计算预期节省"""
        total_savings = sum(plan.get("expected_savings", 0) for plan in optimization_plans)
        
        # 考虑方案重叠，实际节省可能小于总和
        realistic_savings = total_savings * 0.8  # 假设80%的实际效果
        
        return {
            "total_potential_savings": round(total_savings, 2),
            "realistic_savings": round(realistic_savings, 2),
            "savings_rate": round(realistic_savings / current_hours * 100, 2) if current_hours > 0 else 0.0
        }
    
    def _assess_feasibility(
        self,
        optimization_plans: List[Dict[str, Any]],
        reduction_target: float
    ) -> str:
        """评估可行性"""
        total_savings = sum(plan.get("expected_savings", 0) for plan in optimization_plans)
        
        if total_savings >= reduction_target * 1.2:
            return "高"
        elif total_savings >= reduction_target * 0.8:
            return "中等"
        else:
            return "低"
    
    def _prioritize_plans(
        self,
        optimization_plans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """优先级排序"""
        # 按实施难度和预期节省排序
        prioritized = sorted(
            optimization_plans,
            key=lambda x: (
                {"低": 1, "中等": 2, "高": 3}.get(x.get("implementation_difficulty", "中等"), 2),
                -x.get("expected_savings", 0)
            )
        )
        
        return prioritized

