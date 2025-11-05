"""
优化建议系统
基于分析结果生成优化建议
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OptimizationSuggester:
    """优化建议系统"""
    
    def __init__(self, rag_client=None):
        self.rag_client = rag_client
        
        # 优化建议模板
        self.suggestion_templates = {
            "performance": {
                "slow_response": "建议优化{function}的响应时间，当前{current}秒，目标<2秒",
                "high_resource": "建议优化{function}的资源使用，当前CPU {cpu}%，内存{memory}GB",
                "caching": "建议为{function}添加缓存机制，减少重复计算",
                "async": "建议将{function}改为异步执行，提高并发性能"
            },
            "reliability": {
                "high_failure": "建议修复{function}的常见错误，当前失败率{rate}%",
                "retry": "建议为{function}添加重试机制，提高可靠性",
                "error_handling": "建议改进{function}的错误处理，避免崩溃"
            },
            "usability": {
                "unused": "建议改进{function}的易用性或考虑移除，{days}天未使用",
                "documentation": "建议完善{function}的文档和示例",
                "interface": "建议简化{function}的接口，降低使用难度"
            },
            "architecture": {
                "coupling": "建议降低{module}与其他模块的耦合度",
                "modularity": "建议将{module}拆分为更小的模块",
                "refactor": "建议重构{function}，提高代码质量"
            }
        }
        
        # 已生成的建议
        self.generated_suggestions = []
        
        logger.info("优化建议系统初始化完成")
    
    def generate_suggestions_for_function(
        self,
        function_details: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为特定功能生成优化建议
        
        Args:
            function_details: 功能详情
            
        Returns:
            优化建议列表
        """
        if not function_details.get("exists"):
            return []
        
        suggestions = []
        stats = function_details.get("statistics", {})
        
        # 性能优化建议
        avg_time = stats.get("avg_response_time", 0)
        if avg_time > 5:
            suggestions.append({
                "type": "performance",
                "priority": "high",
                "title": "严重性能问题",
                "description": f"响应时间{avg_time:.2f}秒过长，严重影响用户体验",
                "suggestion": "建议进行性能分析，优化关键路径",
                "estimated_impact": "响应时间可能降低60-80%"
            })
        elif avg_time > 2:
            suggestions.append({
                "type": "performance",
                "priority": "medium",
                "title": "性能可以优化",
                "description": f"响应时间{avg_time:.2f}秒较长",
                "suggestion": "建议添加缓存或优化数据库查询",
                "estimated_impact": "响应时间可能降低30-50%"
            })
        
        # 可靠性优化建议
        success_rate = stats.get("success_rate", 0)
        if success_rate < 0.8:
            suggestions.append({
                "type": "reliability",
                "priority": "critical",
                "title": "可靠性严重问题",
                "description": f"成功率{success_rate:.1%}过低",
                "suggestion": "建议分析失败原因，修复常见错误",
                "estimated_impact": "成功率可能提升到95%+"
            })
        elif success_rate < 0.95:
            suggestions.append({
                "type": "reliability",
                "priority": "high",
                "title": "可靠性需要改进",
                "description": f"成功率{success_rate:.1%}偏低",
                "suggestion": "建议添加错误处理和重试机制",
                "estimated_impact": "成功率可能提升10-15%"
            })
        
        # 易用性优化建议
        usage_count = stats.get("usage_count", 0)
        if usage_count == 0:
            suggestions.append({
                "type": "usability",
                "priority": "medium",
                "title": "功能未被使用",
                "description": "该功能从未被使用",
                "suggestion": "建议改进易用性、增加文档，或考虑移除",
                "estimated_impact": "提高功能利用率或减少维护成本"
            })
        elif usage_count < 10:
            suggestions.append({
                "type": "usability",
                "priority": "low",
                "title": "使用频率低",
                "description": f"该功能仅使用{usage_count}次",
                "suggestion": "建议评估功能价值，改进易用性",
                "estimated_impact": "提高功能利用率"
            })
        
        # RAG知识库检索相关建议
        if self.rag_client:
            rag_suggestions = self._get_rag_suggestions(function_details)
            suggestions.extend(rag_suggestions)
        
        return suggestions
    
    def _get_rag_suggestions(self, function_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从RAG知识库获取优化建议"""
        try:
            module = function_details.get("module", "")
            function = function_details.get("function", "")
            
            # 查询相关优化经验
            query = f"{module} {function} 优化 改进"
            results = self.rag_client.search(query, top_k=3)
            
            rag_suggestions = []
            for result in results:
                rag_suggestions.append({
                    "type": "knowledge",
                    "priority": "medium",
                    "title": "知识库建议",
                    "description": result.get("content", "")[:200],
                    "source": "RAG知识库",
                    "confidence": result.get("score", 0)
                })
            
            return rag_suggestions
        except Exception as e:
            logger.warning(f"从RAG获取建议失败: {e}")
            return []
    
    def generate_module_suggestions(
        self,
        module_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为整个模块生成优化建议
        
        Args:
            module_analysis: 模块分析结果
            
        Returns:
            优化建议列表
        """
        suggestions = []
        
        if not module_analysis.get("has_data"):
            return suggestions
        
        perf = module_analysis.get("overall_performance", {})
        
        # 整体性能建议
        success_rate = perf.get("success_rate", 0)
        if success_rate < 0.9:
            suggestions.append({
                "type": "reliability",
                "priority": "high",
                "scope": "module",
                "title": f"模块整体可靠性需要改进",
                "description": f"模块成功率{success_rate:.1%}偏低",
                "suggestion": "建议系统性地审查和修复问题功能",
                "estimated_impact": "整体成功率提升10-20%"
            })
        
        # 响应时间建议
        avg_time = perf.get("avg_response_time", 0)
        if avg_time > 2:
            suggestions.append({
                "type": "performance",
                "priority": "medium",
                "scope": "module",
                "title": "模块整体性能可以优化",
                "description": f"平均响应时间{avg_time:.2f}秒",
                "suggestion": "建议添加统一的缓存层或异步处理",
                "estimated_impact": "响应时间降低30-50%"
            })
        
        # 问题功能建议
        problematic = module_analysis.get("problematic_functions", [])
        if len(problematic) > 3:
            suggestions.append({
                "type": "reliability",
                "priority": "critical",
                "scope": "module",
                "title": "多个问题功能需要修复",
                "description": f"发现{len(problematic)}个问题功能",
                "suggestion": "建议优先修复高失败率功能",
                "estimated_impact": "显著提升模块稳定性"
            })
        
        return suggestions
    
    def generate_system_suggestions(
        self,
        all_modules_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        为整个系统生成优化建议
        
        Args:
            all_modules_analysis: 所有模块分析结果
            
        Returns:
            优化建议列表
        """
        suggestions = []
        overall = all_modules_analysis.get("overall", {})
        
        # 系统整体建议
        total_usage = overall.get("total_usage", 0)
        if total_usage < 100:
            suggestions.append({
                "type": "usability",
                "priority": "medium",
                "scope": "system",
                "title": "系统使用率较低",
                "description": f"总使用次数仅{total_usage}次",
                "suggestion": "建议改进用户引导和文档，提高系统使用率",
                "estimated_impact": "提升用户活跃度"
            })
        
        success_rate = overall.get("overall_success_rate", 0)
        if success_rate < 0.9:
            suggestions.append({
                "type": "reliability",
                "priority": "high",
                "scope": "system",
                "title": "系统稳定性需要提升",
                "description": f"整体成功率{success_rate:.1%}",
                "suggestion": "建议实施系统性的质量改进计划",
                "estimated_impact": "显著提升系统可靠性"
            })
        
        # 模块间协同优化
        modules = all_modules_analysis.get("modules", {})
        high_usage_modules = []
        low_usage_modules = []
        
        for module_name, analysis in modules.items():
            if not analysis.get("has_data"):
                continue
            
            perf = analysis.get("overall_performance", {})
            usage = perf.get("total_usage", 0)
            
            if usage > 50:
                high_usage_modules.append(module_name)
            elif usage < 10:
                low_usage_modules.append(module_name)
        
        if high_usage_modules:
            suggestions.append({
                "type": "performance",
                "priority": "high",
                "scope": "system",
                "title": "优先优化高使用率模块",
                "description": f"模块{', '.join(high_usage_modules)}使用频繁",
                "suggestion": "建议优先优化这些模块的性能和可靠性",
                "estimated_impact": "影响大量用户，效果显著"
            })
        
        if len(low_usage_modules) > 3:
            suggestions.append({
                "type": "architecture",
                "priority": "low",
                "scope": "system",
                "title": "评估低使用率模块",
                "description": f"{len(low_usage_modules)}个模块使用率低",
                "suggestion": "建议评估这些模块的必要性，考虑简化或移除",
                "estimated_impact": "降低系统复杂度和维护成本"
            })
        
        return suggestions
    
    def prioritize_suggestions(
        self,
        suggestions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        对优化建议进行优先级排序
        
        Args:
            suggestions: 建议列表
            
        Returns:
            排序后的建议列表
        """
        priority_scores = {
            "critical": 10,
            "high": 7,
            "medium": 5,
            "low": 3,
            "trivial": 1
        }
        
        def get_score(suggestion: Dict[str, Any]) -> int:
            priority = suggestion.get("priority", "medium")
            scope = suggestion.get("scope", "function")
            
            base_score = priority_scores.get(priority, 5)
            
            # 系统级建议加权
            if scope == "system":
                base_score *= 1.5
            elif scope == "module":
                base_score *= 1.2
            
            return int(base_score)
        
        for suggestion in suggestions:
            suggestion["priority_score"] = get_score(suggestion)
        
        return sorted(suggestions, key=lambda s: s["priority_score"], reverse=True)
    
    def generate_improvement_plan(
        self,
        all_suggestions: List[Dict[str, Any]],
        timeframe_weeks: int = 4
    ) -> Dict[str, Any]:
        """
        生成改进计划
        
        Args:
            all_suggestions: 所有建议
            timeframe_weeks: 时间框架（周）
            
        Returns:
            改进计划
        """
        prioritized = self.prioritize_suggestions(all_suggestions)
        
        # 按优先级分配到不同周
        plan = {
            "timeframe_weeks": timeframe_weeks,
            "total_suggestions": len(prioritized),
            "weeks": []
        }
        
        # 分配建议到各周
        suggestions_per_week = max(1, len(prioritized) // timeframe_weeks)
        
        for week in range(1, timeframe_weeks + 1):
            start_idx = (week - 1) * suggestions_per_week
            end_idx = start_idx + suggestions_per_week if week < timeframe_weeks else len(prioritized)
            
            week_suggestions = prioritized[start_idx:end_idx]
            
            plan["weeks"].append({
                "week_number": week,
                "focus": self._get_week_focus(week_suggestions),
                "suggestions": week_suggestions,
                "estimated_effort": self._estimate_effort(week_suggestions)
            })
        
        return plan
    
    def _get_week_focus(self, suggestions: List[Dict[str, Any]]) -> str:
        """确定一周的重点"""
        if not suggestions:
            return "无"
        
        type_counts = {}
        for s in suggestions:
            stype = s.get("type", "other")
            type_counts[stype] = type_counts.get(stype, 0) + 1
        
        main_type = max(type_counts.items(), key=lambda x: x[1])[0]
        
        type_names = {
            "performance": "性能优化",
            "reliability": "可靠性提升",
            "usability": "易用性改进",
            "architecture": "架构优化",
            "knowledge": "知识应用"
        }
        
        return type_names.get(main_type, "综合改进")
    
    def _estimate_effort(self, suggestions: List[Dict[str, Any]]) -> str:
        """估算工作量"""
        total_score = sum(s.get("priority_score", 5) for s in suggestions)
        
        if total_score > 50:
            return "高（需要1-2周）"
        elif total_score > 30:
            return "中（需要3-5天）"
        else:
            return "低（需要1-2天）"
    
    def save_suggestions(self, suggestions: List[Dict[str, Any]]):
        """保存生成的建议"""
        for suggestion in suggestions:
            suggestion["generated_at"] = datetime.now().isoformat()
            self.generated_suggestions.append(suggestion)
        
        logger.info(f"保存了{len(suggestions)}条优化建议")
    
    def get_suggestions_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取建议历史"""
        return self.generated_suggestions[-limit:]

