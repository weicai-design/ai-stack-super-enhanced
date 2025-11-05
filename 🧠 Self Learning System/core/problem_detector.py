"""
问题检测引擎
自动识别系统运行中的问题
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class ProblemDetector:
    """问题检测引擎"""
    
    def __init__(self):
        # 问题类型定义
        self.problem_types = {
            "performance": "性能问题",
            "reliability": "可靠性问题",
            "usability": "易用性问题",
            "compatibility": "兼容性问题",
            "security": "安全问题",
            "other": "其他问题"
        }
        
        # 问题严重程度
        self.severity_levels = {
            "critical": 10,   # 致命问题
            "high": 7,        # 高优先级
            "medium": 5,      # 中等优先级
            "low": 3,         # 低优先级
            "trivial": 1      # 微小问题
        }
        
        # 检测到的问题
        self.detected_problems = []
        
        # 问题模式库（常见问题特征）
        self.problem_patterns = {
            "timeout": {
                "keywords": ["timeout", "超时", "time out"],
                "type": "performance",
                "severity": "high"
            },
            "memory_leak": {
                "keywords": ["memory", "内存泄漏", "OOM"],
                "type": "performance",
                "severity": "critical"
            },
            "connection_failed": {
                "keywords": ["connection", "连接失败", "refused"],
                "type": "reliability",
                "severity": "high"
            },
            "permission_denied": {
                "keywords": ["permission", "denied", "权限"],
                "type": "security",
                "severity": "medium"
            },
            "slow_response": {
                "keywords": ["slow", "慢", "延迟"],
                "type": "performance",
                "severity": "medium"
            }
        }
        
        logger.info("问题检测引擎初始化完成")
    
    def detect_problems_from_metrics(
        self,
        function_metrics: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从功能指标中检测问题
        
        Args:
            function_metrics: 功能运行指标
            
        Returns:
            检测到的问题列表
        """
        problems = []
        
        for func_key, metrics in function_metrics.items():
            # 检查失败率
            if metrics["usage_count"] > 0:
                failure_rate = metrics["failure_count"] / metrics["usage_count"]
                
                if failure_rate > 0.5:
                    problems.append({
                        "id": f"prob_{len(problems)}",
                        "function": func_key,
                        "type": "reliability",
                        "severity": "critical",
                        "description": f"功能失败率过高 ({failure_rate:.1%})",
                        "impact": "严重影响用户体验",
                        "detected_at": datetime.now().isoformat()
                    })
                elif failure_rate > 0.2:
                    problems.append({
                        "id": f"prob_{len(problems)}",
                        "function": func_key,
                        "type": "reliability",
                        "severity": "high",
                        "description": f"功能失败率偏高 ({failure_rate:.1%})",
                        "impact": "影响用户体验",
                        "detected_at": datetime.now().isoformat()
                    })
            
            # 检查响应时间
            if metrics["avg_response_time"] > 5.0:
                problems.append({
                    "id": f"prob_{len(problems)}",
                    "function": func_key,
                    "type": "performance",
                    "severity": "high",
                    "description": f"响应时间过长 ({metrics['avg_response_time']:.2f}秒)",
                    "impact": "用户体验差",
                    "detected_at": datetime.now().isoformat()
                })
            elif metrics["avg_response_time"] > 2.0:
                problems.append({
                    "id": f"prob_{len(problems)}",
                    "function": func_key,
                    "type": "performance",
                    "severity": "medium",
                    "description": f"响应时间较长 ({metrics['avg_response_time']:.2f}秒)",
                    "impact": "用户等待时间长",
                    "detected_at": datetime.now().isoformat()
                })
            
            # 检查错误模式
            for error_msg, count in metrics.get("error_types", {}).items():
                if count > 5:  # 同一错误出现多次
                    pattern = self._match_error_pattern(error_msg)
                    problems.append({
                        "id": f"prob_{len(problems)}",
                        "function": func_key,
                        "type": pattern.get("type", "other"),
                        "severity": pattern.get("severity", "medium"),
                        "description": f"重复错误: {error_msg} (出现{count}次)",
                        "impact": "需要修复",
                        "detected_at": datetime.now().isoformat()
                    })
        
        # 保存检测到的问题
        self.detected_problems.extend(problems)
        
        return problems
    
    def _match_error_pattern(self, error_msg: str) -> Dict[str, str]:
        """匹配错误模式"""
        error_lower = error_msg.lower()
        
        for pattern_name, pattern in self.problem_patterns.items():
            if any(keyword in error_lower for keyword in pattern["keywords"]):
                return pattern
        
        return {"type": "other", "severity": "medium"}
    
    def detect_resource_problems(
        self,
        resource_status: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        检测资源相关问题
        
        Args:
            resource_status: 资源状态
            
        Returns:
            检测到的问题列表
        """
        problems = []
        
        # 检查内存问题
        memory_percent = resource_status.get("memory", {}).get("percent", 0)
        if memory_percent > 90:
            problems.append({
                "id": f"res_prob_{len(problems)}",
                "type": "performance",
                "severity": "critical",
                "description": f"内存使用率过高 ({memory_percent:.1f}%)",
                "impact": "可能导致系统崩溃",
                "suggestion": "需要立即释放内存或增加内存",
                "detected_at": datetime.now().isoformat()
            })
        elif memory_percent > 80:
            problems.append({
                "id": f"res_prob_{len(problems)}",
                "type": "performance",
                "severity": "high",
                "description": f"内存使用率偏高 ({memory_percent:.1f}%)",
                "impact": "系统性能下降",
                "suggestion": "建议优化内存使用",
                "detected_at": datetime.now().isoformat()
            })
        
        # 检查CPU问题
        cpu_percent = resource_status.get("cpu", {}).get("total_percent", 0)
        if cpu_percent > 90:
            problems.append({
                "id": f"res_prob_{len(problems)}",
                "type": "performance",
                "severity": "high",
                "description": f"CPU使用率过高 ({cpu_percent:.1f}%)",
                "impact": "系统响应变慢",
                "suggestion": "需要优化CPU密集型操作",
                "detected_at": datetime.now().isoformat()
            })
        
        # 检查磁盘问题
        for disk in resource_status.get("disk", []):
            disk_percent = disk.get("percent", 0)
            if disk_percent > 95:
                problems.append({
                    "id": f"res_prob_{len(problems)}",
                    "type": "reliability",
                    "severity": "critical",
                    "description": f"磁盘空间严重不足 ({disk['mountpoint']}: {disk_percent:.1f}%)",
                    "impact": "可能导致数据丢失",
                    "suggestion": "立即清理磁盘空间",
                    "detected_at": datetime.now().isoformat()
                })
        
        return problems
    
    def analyze_problem_trends(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        分析问题趋势
        
        Args:
            time_window_hours: 时间窗口（小时）
            
        Returns:
            趋势分析
        """
        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)
        
        # 筛选时间窗口内的问题
        recent_problems = [
            p for p in self.detected_problems
            if datetime.fromisoformat(p["detected_at"]) > cutoff_time
        ]
        
        if not recent_problems:
            return {
                "time_window_hours": time_window_hours,
                "total_problems": 0,
                "trend": "stable",
                "message": "未检测到新问题"
            }
        
        # 按类型统计
        type_counter = Counter(p["type"] for p in recent_problems)
        
        # 按严重程度统计
        severity_counter = Counter(p["severity"] for p in recent_problems)
        
        # 判断趋势
        trend = "stable"
        if len(recent_problems) > 10:
            trend = "increasing"
        elif len(recent_problems) < 3:
            trend = "decreasing"
        
        return {
            "time_window_hours": time_window_hours,
            "total_problems": len(recent_problems),
            "by_type": dict(type_counter),
            "by_severity": dict(severity_counter),
            "trend": trend,
            "most_common_type": type_counter.most_common(1)[0][0] if type_counter else None,
            "critical_count": severity_counter.get("critical", 0),
            "high_count": severity_counter.get("high", 0)
        }
    
    def prioritize_problems(
        self,
        problems: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对问题进行优先级排序
        
        Args:
            problems: 问题列表
            
        Returns:
            排序后的问题列表
        """
        def get_priority_score(problem: Dict[str, Any]) -> int:
            severity = problem.get("severity", "medium")
            type_weight = {
                "reliability": 1.5,
                "security": 1.3,
                "performance": 1.2,
                "usability": 1.0,
                "compatibility": 1.0,
                "other": 0.8
            }
            
            base_score = self.severity_levels.get(severity, 5)
            problem_type = problem.get("type", "other")
            
            return int(base_score * type_weight.get(problem_type, 1.0))
        
        # 添加优先级分数
        for problem in problems:
            problem["priority_score"] = get_priority_score(problem)
        
        # 按优先级排序
        sorted_problems = sorted(
            problems,
            key=lambda p: p["priority_score"],
            reverse=True
        )
        
        return sorted_problems
    
    def get_problem_summary(self) -> Dict[str, Any]:
        """
        获取问题摘要
        
        Returns:
            问题摘要
        """
        if not self.detected_problems:
            return {
                "total_problems": 0,
                "status": "healthy",
                "message": "系统运行良好，未检测到问题"
            }
        
        # 统计各类问题
        type_counter = Counter(p["type"] for p in self.detected_problems)
        severity_counter = Counter(p["severity"] for p in self.detected_problems)
        
        # 确定系统状态
        critical_count = severity_counter.get("critical", 0)
        high_count = severity_counter.get("high", 0)
        
        if critical_count > 0:
            status = "critical"
        elif high_count > 5:
            status = "warning"
        elif high_count > 0:
            status = "attention"
        else:
            status = "good"
        
        return {
            "total_problems": len(self.detected_problems),
            "status": status,
            "by_type": dict(type_counter),
            "by_severity": dict(severity_counter),
            "top_problems": self.prioritize_problems(self.detected_problems)[:5],
            "recommendations": self._generate_overall_recommendations(
                critical_count,
                high_count
            )
        }
    
    def _generate_overall_recommendations(
        self,
        critical_count: int,
        high_count: int
    ) -> List[str]:
        """生成总体建议"""
        recommendations = []
        
        if critical_count > 0:
            recommendations.append(f"发现 {critical_count} 个致命问题，需要立即处理")
        
        if high_count > 0:
            recommendations.append(f"发现 {high_count} 个高优先级问题，建议尽快修复")
        
        if critical_count == 0 and high_count == 0:
            recommendations.append("系统运行良好，继续保持监控")
        
        return recommendations
    
    def get_problem_details(self, problem_id: str) -> Optional[Dict[str, Any]]:
        """获取问题详情"""
        for problem in self.detected_problems:
            if problem.get("id") == problem_id:
                return problem
        return None
    
    def mark_problem_resolved(
        self,
        problem_id: str,
        resolution: str
    ) -> bool:
        """
        标记问题已解决
        
        Args:
            problem_id: 问题ID
            resolution: 解决方案描述
            
        Returns:
            是否成功
        """
        for problem in self.detected_problems:
            if problem.get("id") == problem_id:
                problem["resolved"] = True
                problem["resolved_at"] = datetime.now().isoformat()
                problem["resolution"] = resolution
                logger.info(f"问题 {problem_id} 已标记为解决")
                return True
        
        return False

