"""
功能分析器
分析所有功能的运行情况和存在的问题
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class FunctionAnalyzer:
    """功能分析器"""
    
    def __init__(self):
        # 功能模块列表
        self.modules = [
            "RAG和知识图谱",
            "ERP企业管理",
            "OpenWebUI交互",
            "股票交易",
            "趋势分析",
            "内容创作",
            "智能任务代理",
            "资源管理",
            "自我学习"
        ]
        
        # 功能运行数据
        self.function_metrics = defaultdict(lambda: {
            "usage_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "error_types": defaultdict(int),
            "last_used": None
        })
        
        # 问题记录
        self.problems = []
        
        logger.info("功能分析器初始化完成")
    
    def record_function_usage(
        self,
        module_name: str,
        function_name: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ):
        """
        记录功能使用情况
        
        Args:
            module_name: 模块名称
            function_name: 功能名称
            success: 是否成功
            response_time: 响应时间（秒）
            error: 错误信息
        """
        key = f"{module_name}::{function_name}"
        metrics = self.function_metrics[key]
        
        # 更新统计
        metrics["usage_count"] += 1
        if success:
            metrics["success_count"] += 1
        else:
            metrics["failure_count"] += 1
            if error:
                metrics["error_types"][error] += 1
        
        # 更新响应时间
        metrics["total_response_time"] += response_time
        metrics["avg_response_time"] = (
            metrics["total_response_time"] / metrics["usage_count"]
        )
        
        metrics["last_used"] = datetime.now().isoformat()
        
        logger.debug(f"记录功能使用: {key}, 成功={success}, 耗时={response_time:.2f}s")
    
    def analyze_module_performance(self, module_name: str) -> Dict[str, Any]:
        """
        分析模块性能
        
        Args:
            module_name: 模块名称
            
        Returns:
            性能分析结果
        """
        # 获取该模块的所有功能
        module_functions = {
            k: v for k, v in self.function_metrics.items()
            if k.startswith(f"{module_name}::")
        }
        
        if not module_functions:
            return {
                "module": module_name,
                "has_data": False,
                "message": "该模块暂无使用数据"
            }
        
        # 计算统计指标
        total_usage = sum(f["usage_count"] for f in module_functions.values())
        total_success = sum(f["success_count"] for f in module_functions.values())
        total_failure = sum(f["failure_count"] for f in module_functions.values())
        
        success_rate = total_success / total_usage if total_usage > 0 else 0
        avg_response_time = sum(
            f["avg_response_time"] for f in module_functions.values()
        ) / len(module_functions)
        
        # 识别问题功能
        problematic_functions = []
        for func_key, metrics in module_functions.items():
            failure_rate = (
                metrics["failure_count"] / metrics["usage_count"]
                if metrics["usage_count"] > 0 else 0
            )
            
            if failure_rate > 0.2:  # 失败率超过20%
                problematic_functions.append({
                    "function": func_key.split("::")[-1],
                    "failure_rate": failure_rate,
                    "error_types": dict(metrics["error_types"])
                })
        
        analysis = {
            "module": module_name,
            "has_data": True,
            "overall_performance": {
                "total_usage": total_usage,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "function_count": len(module_functions)
            },
            "problematic_functions": problematic_functions,
            "recommendation": self._generate_recommendation(
                success_rate,
                avg_response_time,
                problematic_functions
            )
        }
        
        return analysis
    
    def _generate_recommendation(
        self,
        success_rate: float,
        avg_response_time: float,
        problematic_functions: List[Dict[str, Any]]
    ) -> str:
        """生成优化建议"""
        if success_rate < 0.8:
            return "成功率偏低，建议检查错误日志并修复常见问题"
        elif avg_response_time > 2.0:
            return "响应时间较长，建议优化性能或增加缓存"
        elif problematic_functions:
            return f"发现 {len(problematic_functions)} 个问题功能，建议优先修复"
        else:
            return "性能良好，继续保持"
    
    def analyze_all_modules(self) -> Dict[str, Any]:
        """
        分析所有模块
        
        Returns:
            所有模块的分析结果
        """
        results = {}
        
        for module in self.modules:
            results[module] = self.analyze_module_performance(module)
        
        # 计算总体指标
        all_metrics = list(self.function_metrics.values())
        if all_metrics:
            total_usage = sum(m["usage_count"] for m in all_metrics)
            total_success = sum(m["success_count"] for m in all_metrics)
            
            overall = {
                "total_functions": len(self.function_metrics),
                "total_usage": total_usage,
                "overall_success_rate": total_success / total_usage if total_usage > 0 else 0,
                "modules_analyzed": len(self.modules)
            }
        else:
            overall = {
                "total_functions": 0,
                "total_usage": 0,
                "overall_success_rate": 0,
                "modules_analyzed": len(self.modules)
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall": overall,
            "modules": results
        }
    
    def identify_unused_functions(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        识别未使用的功能
        
        Args:
            days: 天数阈值
            
        Returns:
            未使用功能列表
        """
        unused = []
        cutoff_time = datetime.now() - timedelta(days=days)
        
        for func_key, metrics in self.function_metrics.items():
            if metrics["usage_count"] == 0:
                unused.append({
                    "function": func_key,
                    "reason": "从未使用",
                    "recommendation": "考虑移除或改进易用性"
                })
            elif metrics["last_used"]:
                last_used = datetime.fromisoformat(metrics["last_used"])
                if last_used < cutoff_time:
                    unused.append({
                        "function": func_key,
                        "last_used": metrics["last_used"],
                        "reason": f"超过{days}天未使用",
                        "recommendation": "评估是否仍需保留"
                    })
        
        return unused
    
    def compare_module_performance(
        self,
        module1: str,
        module2: str
    ) -> Dict[str, Any]:
        """
        比较两个模块的性能
        
        Args:
            module1: 模块1名称
            module2: 模块2名称
            
        Returns:
            比较结果
        """
        analysis1 = self.analyze_module_performance(module1)
        analysis2 = self.analyze_module_performance(module2)
        
        if not analysis1.get("has_data") or not analysis2.get("has_data"):
            return {
                "comparison": "无法比较",
                "reason": "其中一个模块无数据"
            }
        
        perf1 = analysis1["overall_performance"]
        perf2 = analysis2["overall_performance"]
        
        comparison = {
            "module1": module1,
            "module2": module2,
            "usage": {
                "module1": perf1["total_usage"],
                "module2": perf2["total_usage"],
                "diff": perf1["total_usage"] - perf2["total_usage"],
                "winner": module1 if perf1["total_usage"] > perf2["total_usage"] else module2
            },
            "success_rate": {
                "module1": perf1["success_rate"],
                "module2": perf2["success_rate"],
                "diff": perf1["success_rate"] - perf2["success_rate"],
                "winner": module1 if perf1["success_rate"] > perf2["success_rate"] else module2
            },
            "response_time": {
                "module1": perf1["avg_response_time"],
                "module2": perf2["avg_response_time"],
                "diff": perf1["avg_response_time"] - perf2["avg_response_time"],
                "winner": module2 if perf1["avg_response_time"] > perf2["avg_response_time"] else module1
            }
        }
        
        return comparison
    
    def get_function_details(self, module_name: str, function_name: str) -> Dict[str, Any]:
        """
        获取功能详细信息
        
        Args:
            module_name: 模块名称
            function_name: 功能名称
            
        Returns:
            功能详情
        """
        key = f"{module_name}::{function_name}"
        
        if key not in self.function_metrics:
            return {
                "exists": False,
                "message": "功能不存在或未被使用"
            }
        
        metrics = self.function_metrics[key]
        
        success_rate = (
            metrics["success_count"] / metrics["usage_count"]
            if metrics["usage_count"] > 0 else 0
        )
        
        return {
            "exists": True,
            "module": module_name,
            "function": function_name,
            "statistics": {
                "usage_count": metrics["usage_count"],
                "success_count": metrics["success_count"],
                "failure_count": metrics["failure_count"],
                "success_rate": success_rate,
                "avg_response_time": metrics["avg_response_time"],
                "last_used": metrics["last_used"]
            },
            "errors": dict(metrics["error_types"]),
            "health_score": self._calculate_health_score(metrics),
            "recommendations": self._generate_function_recommendations(metrics)
        }
    
    def _calculate_health_score(self, metrics: Dict[str, Any]) -> float:
        """计算健康分数（0-100）"""
        if metrics["usage_count"] == 0:
            return 0
        
        success_rate = metrics["success_count"] / metrics["usage_count"]
        
        # 响应时间评分（2秒为标准）
        response_score = max(0, 1 - (metrics["avg_response_time"] / 2.0))
        
        # 综合评分
        health_score = (success_rate * 0.7 + response_score * 0.3) * 100
        
        return round(health_score, 2)
    
    def _generate_function_recommendations(self, metrics: Dict[str, Any]) -> List[str]:
        """生成功能优化建议"""
        recommendations = []
        
        if metrics["usage_count"] == 0:
            recommendations.append("功能从未被使用，考虑改进易用性或移除")
            return recommendations
        
        success_rate = metrics["success_count"] / metrics["usage_count"]
        
        if success_rate < 0.8:
            recommendations.append(f"成功率 {success_rate:.1%} 偏低，建议修复常见错误")
        
        if metrics["avg_response_time"] > 2.0:
            recommendations.append(
                f"平均响应时间 {metrics['avg_response_time']:.2f}秒较长，建议性能优化"
            )
        
        if metrics["error_types"]:
            top_error = max(metrics["error_types"].items(), key=lambda x: x[1])
            recommendations.append(
                f"最常见错误: {top_error[0]} ({top_error[1]}次)，建议优先修复"
            )
        
        if not recommendations:
            recommendations.append("功能运行良好，继续保持")
        
        return recommendations

