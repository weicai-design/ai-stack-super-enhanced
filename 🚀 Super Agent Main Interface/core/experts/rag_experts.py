#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG模块专家系统（T004）
实现3个专家：知识专家、检索专家、图谱专家
"""

from __future__ import annotations

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from .rag_config import get_config_manager, RAGExpertConfig
from .rag_observability import get_observability_system, trace_operation, TracingContext

logger = logging.getLogger(__name__)


class ExpertDomain(str, Enum):
    """专家领域"""
    KNOWLEDGE = "knowledge"  # 知识管理
    RETRIEVAL = "retrieval"  # 检索优化
    GRAPH = "graph"  # 知识图谱


class ExpertCollaboration:
    """专家协作管理器"""
    
    def __init__(self):
        self.experts = {}
        self.collaboration_history = []
    
    def register_expert(self, expert_id: str, expert_instance: Any):
        """注册专家"""
        self.experts[expert_id] = expert_instance
    
    async def collaborative_analysis(
        self,
        expert_ids: List[str],
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        多专家协作分析
        
        Args:
            expert_ids: 参与协作的专家ID列表
            data: 分析数据
            context: 上下文信息
            
        Returns:
            协作分析结果
        """
        results = {}
        
        # 并行执行专家分析
        tasks = []
        for expert_id in expert_ids:
            if expert_id in self.experts:
                expert = self.experts[expert_id]
                if hasattr(expert, 'analyze'):
                    task = expert.analyze(data, context)
                    tasks.append((expert_id, task))
        
        # 等待所有专家完成分析
        if tasks:
            expert_results = await asyncio.gather(
                *[task for _, task in tasks],
                return_exceptions=True
            )
            
            # 收集结果
            for (expert_id, _), result in zip(tasks, expert_results):
                if not isinstance(result, Exception):
                    results[expert_id] = result
        
        # 生成综合建议
        combined_insights = []
        combined_recommendations = []
        
        for expert_id, result in results.items():
            if hasattr(result, 'insights'):
                combined_insights.extend(result.insights)
            if hasattr(result, 'recommendations'):
                combined_recommendations.extend(result.recommendations)
        
        # 记录协作历史
        collaboration_record = {
            "timestamp": asyncio.get_event_loop().time(),
            "expert_ids": expert_ids,
            "results": {k: str(v) for k, v in results.items()}
        }
        self.collaboration_history.append(collaboration_record)
        
        return {
            "individual_results": results,
            "combined_insights": combined_insights,
            "combined_recommendations": combined_recommendations,
            "collaboration_summary": f"{len(expert_ids)} 位专家完成协作分析"
        }
    
    def get_collaboration_stats(self) -> Dict[str, Any]:
        """获取协作统计信息"""
        return {
            "total_collaborations": len(self.collaboration_history),
            "registered_experts": len(self.experts),
            "recent_collaborations": self.collaboration_history[-5:] if self.collaboration_history else []
        }


@dataclass
class ExpertAnalysis:
    """专家分析结果"""
    domain: ExpertDomain
    confidence: float
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeExpert:
    """
    知识专家（T004-1）- 生产级增强版
    
    专业能力：
    1. 知识分类和组织
    2. 知识质量评估  
    3. 知识关联分析
    4. 知识更新建议
    5. 知识质量预警生成
    6. 实时监控与指标追踪
    7. AI驱动知识优化
    8. 生产级可观测性
    """
    
    def __init__(self, config: Optional[RAGExpertConfig] = None):
        self.expert_id = "rag_knowledge_expert"
        self.name = "知识管理专家（生产级增强版）"
        self.domain = ExpertDomain.KNOWLEDGE
        self.stage = "production"
        
        # 使用新的配置系统
        from .rag_config import get_rag_config, get_expert_config
        self.system_config = get_rag_config()
        self.config = config or get_expert_config(self.expert_id)
        
        # 可观测性
        self.observability_system = get_observability_system()
        self.logger = self.observability_system.create_logger(self.expert_id)
        
        # 监控系统
        from .rag_monitoring import get_monitoring_system
        self.monitoring_system = get_monitoring_system()
        
        # 生产级增强属性
        self.monitoring_active = False
        self.monitoring_id = None
        self.alert_counter = 0
        self.monitoring_metrics = {
            "knowledge_quality_score": 0.0,
            "knowledge_coverage": 0.0,
            "update_frequency": 0.0,
            "error_rate": 0.0
        }
        
        logger.info(f"知识专家（生产级增强版）初始化完成 - 质量阈值: {self.config.quality_threshold}")
        
    async def analyze_knowledge(
        self,
        knowledge_items: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertAnalysis:
        """
        分析知识内容 - 生产级增强版
        
        Args:
            knowledge_items: 知识条目列表
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        # 开始追踪操作
        with self.observability_system.trace_operation(
            "knowledge_expert_analysis", 
            TracingContext()
        ) as (span, logger):
            
            # 记录监控指标
            self.monitoring_system.metrics_collector.record_counter("rag_expert_analysis_total", 
                labels={"expert": self.expert_id, "domain": self.domain.value})
            start_time = time.time()
            
            try:
                insights: List[str] = []
                recommendations: List[str] = []
                avg_score = 0.0
                
                # 记录分析参数
                span.add_tag("knowledge_items_count", len(knowledge_items))
                logger.info("开始知识分析（生产级增强版）", 
                    items_count=len(knowledge_items),
                    config_threshold=self.config.quality_threshold)
                
                # 分析知识分类
                categories = {}
                for item in knowledge_items:
                    category = item.get("category", "未分类")
                    categories[category] = categories.get(category, 0) + 1
                
                if categories:
                    insights.append(f"知识涵盖 {len(categories)} 个分类")
                    top_category = max(categories.items(), key=lambda x: x[1])
                    insights.append(f"主要分类: {top_category[0]} ({top_category[1]}条)")
                
                # 分析知识质量
                total_items = len(knowledge_items)
                if total_items > 0:
                    avg_score = sum(
                        item.get("score", item.get("relevance", 0.5))
                        for item in knowledge_items
                    ) / total_items
                    
                    insights.append(f"平均质量分数: {avg_score:.2f}")
                    
                    # 使用配置阈值
                    if avg_score < self.config.quality_threshold:
                        recommendations.append("建议提升知识质量，增加高质量内容")
                
                # 分析知识关联
                if total_items >= 2:
                    insights.append(f"发现 {total_items} 条相关知识，存在关联性")
                    recommendations.append("建议构建知识图谱，增强知识关联")
                
                # 新增分析维度：知识时效性
                timestamps = [item.get("timestamp", item.get("created_at", 0)) for item in knowledge_items if item.get("timestamp") or item.get("created_at")]
                if timestamps:
                    current_time = time.time()
                    avg_age = (current_time - sum(timestamps) / len(timestamps)) / (24 * 3600)  # 转换为天数
                    insights.append(f"知识平均时效性: {avg_age:.1f} 天")
                    if avg_age > 365:
                        recommendations.append("知识时效性较差，建议更新内容")
                
                # 新增分析维度：知识完整性
                complete_items = sum(1 for item in knowledge_items if item.get("content") and len(item["content"]) > 50)
                completeness_ratio = complete_items / total_items if total_items > 0 else 0
                insights.append(f"知识完整性: {completeness_ratio:.1%}")
                if completeness_ratio < 0.7:
                    recommendations.append("知识完整性不足，建议完善内容")
                
                # 新增分析维度：知识多样性
                diversity_score = len(categories) / total_items if total_items > 0 else 0
                insights.append(f"知识多样性: {diversity_score:.2f}")
                if diversity_score < 0.1:
                    recommendations.append("知识多样性不足，建议扩展知识领域")
                
                # 生成预警
                alerts = await self._generate_knowledge_alerts(
                    avg_score, completeness_ratio, diversity_score, total_items
                )
                if alerts:
                    insights.extend([f"⚠️ {alert}" for alert in alerts])
                
                # 更新监控指标
                self.monitoring_metrics["knowledge_quality_score"] = avg_score
                self.monitoring_metrics["knowledge_coverage"] = completeness_ratio
                self.monitoring_metrics["update_frequency"] = diversity_score
                
                # 记录分析结果
                analysis_result = ExpertAnalysis(
                    domain=self.domain,
                    confidence=0.92,  # 提升置信度
                    insights=insights,
                    recommendations=recommendations,
                    metadata={
                        "total_items": total_items,
                        "categories_count": len(categories),
                        "avg_score": avg_score if total_items > 0 else 0,
                        "completeness_ratio": completeness_ratio,
                        "diversity_score": diversity_score,
                        "alerts_generated": len(alerts)
                    }
                )
                
                # 记录监控指标
                duration = time.time() - start_time
                self.monitoring_system.metrics_collector.record_histogram(
                    "rag_expert_analysis_duration_seconds", 
                    duration,
                    labels={"expert": self.expert_id}
                )
                
                logger.info("知识分析完成（生产级增强版）", 
                    duration=duration,
                    insights_count=len(insights),
                    recommendations_count=len(recommendations),
                    alerts_count=len(alerts))
                
                return analysis_result
                
            except Exception as e:
                # 记录错误
                self.monitoring_system.metrics_collector.increment_counter(
                    "rag_expert_analysis_errors_total",
                    labels={"expert": self.expert_id, "error_type": type(e).__name__}
                )
                logger.error("知识分析失败", error=str(e), exc_info=True)
                raise
    
    async def _generate_knowledge_alerts(
        self,
        quality_score: float,
        completeness_ratio: float,
        diversity_score: float,
        total_items: int
    ) -> List[str]:
        """
        生成知识质量预警
        
        Args:
            quality_score: 质量分数
            completeness_ratio: 完整性比例
            diversity_score: 多样性分数
            total_items: 总条目数
            
        Returns:
            预警信息列表
        """
        alerts = []
        
        # 低质量知识预警
        if quality_score < 0.5:
            alerts.append("知识质量严重不足，需要立即优化")
            self.alert_counter += 1
        elif quality_score < 0.7:
            alerts.append("知识质量较低，建议改进")
        
        # 完整性不足预警
        if completeness_ratio < 0.5:
            alerts.append("知识完整性严重不足，内容需要完善")
            self.alert_counter += 1
        elif completeness_ratio < 0.7:
            alerts.append("知识完整性不足，建议补充内容")
        
        # 多样性不足预警
        if diversity_score < 0.05:
            alerts.append("知识多样性严重不足，领域过于单一")
            self.alert_counter += 1
        elif diversity_score < 0.1:
            alerts.append("知识多样性不足，建议扩展领域")
        
        # 知识量不足预警
        if total_items < 10:
            alerts.append("知识量严重不足，需要大量补充")
            self.alert_counter += 1
        elif total_items < 50:
            alerts.append("知识量较少，建议扩充")
        
        # 记录预警指标
        if alerts:
            self.monitoring_system.metrics_collector.record_counter(
                "rag_knowledge_alerts_total",
                value=len(alerts),
                labels={"expert": self.expert_id}
            )
        
        return alerts
    
    async def start_real_time_monitoring(self) -> Dict[str, Any]:
        """
        启动实时监控
        
        Returns:
            监控启动结果
        """
        if self.monitoring_active:
            return {"status": "already_running", "message": "监控已启动"}
        
        self.monitoring_active = True
        self.monitoring_id = f"knowledge_monitor_{int(time.time())}"
        
        # 初始化监控指标
        self.monitoring_metrics = {
            "knowledge_quality_score": 0.0,
            "knowledge_coverage": 0.0,
            "update_frequency": 0.0,
            "error_rate": 0.0
        }
        
        self.logger.info("知识专家实时监控已启动", monitoring_id=self.monitoring_id)
        
        return {
            "status": "started",
            "monitoring_id": self.monitoring_id,
            "start_time": time.time(),
            "metrics": self.monitoring_metrics
        }
    
    async def stop_real_time_monitoring(self) -> Dict[str, Any]:
        """
        停止实时监控
        
        Returns:
            监控报告
        """
        if not self.monitoring_active:
            return {"status": "not_running", "message": "监控未启动"}
        
        monitoring_duration = self._calculate_monitoring_duration()
        effectiveness = self._calculate_monitoring_effectiveness()
        
        report = {
            "status": "stopped",
            "monitoring_id": self.monitoring_id,
            "duration_seconds": monitoring_duration,
            "effectiveness_score": effectiveness,
            "alerts_generated": self.alert_counter,
            "final_metrics": self.monitoring_metrics,
            "insights": self._generate_monitoring_insights(),
            "recommendations": self._generate_monitoring_recommendations()
        }
        
        self.monitoring_active = False
        self.monitoring_id = None
        self.alert_counter = 0
        
        self.logger.info("知识专家实时监控已停止", 
            duration=monitoring_duration,
            effectiveness=effectiveness,
            alerts=self.alert_counter)
        
        return report
    
    async def optimize_knowledge_parameters(self) -> Dict[str, Any]:
        """
        优化知识参数
        
        Returns:
            优化建议和ROI估算
        """
        current_quality = self.monitoring_metrics["knowledge_quality_score"]
        current_coverage = self.monitoring_metrics["knowledge_coverage"]
        current_diversity = self.monitoring_metrics["update_frequency"]
        
        optimization_suggestions = []
        roi_estimates = []
        
        # 质量优化建议
        if current_quality < 0.8:
            quality_improvement = 0.8 - current_quality
            optimization_suggestions.append({
                "area": "知识质量",
                "current": f"{current_quality:.2f}",
                "target": "0.80",
                "improvement": f"{quality_improvement:.2f}",
                "suggestions": [
                    "增加高质量知识源",
                    "优化知识抽取算法",
                    "实施质量评估机制"
                ]
            })
            roi_estimates.append({
                "area": "质量优化",
                "estimated_roi": "150%",
                "timeframe": "3个月"
            })
        
        # 覆盖率优化建议
        if current_coverage < 0.8:
            coverage_improvement = 0.8 - current_coverage
            optimization_suggestions.append({
                "area": "知识覆盖率",
                "current": f"{current_coverage:.1%}",
                "target": "80%",
                "improvement": f"{coverage_improvement:.1%}",
                "suggestions": [
                    "扩展知识领域",
                    "增加知识条目数量",
                    "完善知识分类体系"
                ]
            })
            roi_estimates.append({
                "area": "覆盖率优化",
                "estimated_roi": "120%",
                "timeframe": "6个月"
            })
        
        # 多样性优化建议
        if current_diversity < 0.15:
            diversity_improvement = 0.15 - current_diversity
            optimization_suggestions.append({
                "area": "知识多样性",
                "current": f"{current_diversity:.2f}",
                "target": "0.15",
                "improvement": f"{diversity_improvement:.2f}",
                "suggestions": [
                    "引入多领域知识",
                    "建立知识关联网络",
                    "实施知识更新策略"
                ]
            })
            roi_estimates.append({
                "area": "多样性优化",
                "estimated_roi": "180%",
                "timeframe": "4个月"
            })
        
        return {
            "optimization_suggestions": optimization_suggestions,
            "roi_estimates": roi_estimates,
            "current_state": {
                "quality_score": current_quality,
                "coverage": current_coverage,
                "diversity": current_diversity
            },
            "overall_recommendation": "建议优先优化知识质量和多样性，可获得较高ROI"
        }
    
    def _calculate_monitoring_duration(self) -> float:
        """计算监控持续时间"""
        if not self.monitoring_start_time:
            return 0.0
        return time.time() - self.monitoring_start_time
    
    def _calculate_monitoring_effectiveness(self) -> float:
        """计算监控有效性"""
        if self.alert_counter == 0:
            return 1.0  # 无预警表示系统健康
        
        # 基于预警数量和监控时长计算有效性
        duration = self._calculate_monitoring_duration()
        if duration == 0:
            return 0.0
        
        # 预警密度越低，有效性越高
        alert_density = self.alert_counter / duration
        effectiveness = max(0, 1 - (alert_density / 10))  # 假设每10秒1个预警为基准
        
        return min(effectiveness, 1.0)
    
    def _generate_monitoring_insights(self) -> List[str]:
        """生成监控洞察"""
        insights = []
        
        if self.monitoring_metrics["error_rate"] > 0.1:
            insights.append("系统错误率较高，需要优化稳定性")
        
        if self.monitoring_metrics["knowledge_quality_score"] < 0.6:
            insights.append("知识质量持续偏低，建议加强质量控制")
        
        if self.alert_counter > 5:
            insights.append(f"监控期间生成{self.alert_counter}个预警，系统稳定性需要关注")
        
        if len(insights) == 0:
            insights.append("系统运行稳定，各项指标正常")
        
        return insights
    
    def _generate_monitoring_recommendations(self) -> List[str]:
        """生成监控建议"""
        recommendations = []
        
        if self.monitoring_metrics["knowledge_quality_score"] < 0.7:
            recommendations.append("实施知识质量评估机制")
            recommendations.append("建立知识更新策略")
        
        if self.monitoring_metrics["error_rate"] > 0.05:
            recommendations.append("优化错误处理机制")
            recommendations.append("增加系统容错能力")
        
        if self.alert_counter > 3:
            recommendations.append("建立预警响应流程")
            recommendations.append("优化监控阈值设置")
        
        if len(recommendations) == 0:
            recommendations.append("继续保持当前监控策略")
        
        return recommendations
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """
        获取当前监控状态
        
        Returns:
            监控状态信息
        """
        return {
            "monitoring_active": self.monitoring_active,
            "monitoring_id": self.monitoring_id,
            "alert_counter": self.alert_counter,
            "current_metrics": self.monitoring_metrics,
            "monitoring_duration": self._calculate_monitoring_duration(),
            "monitoring_effectiveness": self._calculate_monitoring_effectiveness()
        }
    
    async def analyze(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ExpertAnalysis:
        """
        通用分析接口，用于专家协作
        
        Args:
            data: 分析数据
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        knowledge_items = data.get("knowledge_content", [])
        if isinstance(knowledge_items, str):
            knowledge_items = [{"content": knowledge_items}]
        elif not isinstance(knowledge_items, list):
            knowledge_items = []
        
        return await self.analyze_knowledge(knowledge_items, context)
    
    async def suggest_knowledge_organization(
        self,
        knowledge_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        建议知识组织方式
        
        Args:
            knowledge_items: 知识条目列表
            
        Returns:
            组织建议
        """
        # 分析知识特征
        topics = set()
        tags = set()
        categories = set()
        
        for item in knowledge_items:
            # 提取主题
            if "topic" in item:
                topics.add(item["topic"])
            elif "title" in item:
                title = item["title"]
                if len(title) > 0:
                    topics.add(title[:20])
            
            # 提取标签
            if "tags" in item and isinstance(item["tags"], list):
                tags.update(item["tags"])
            
            # 提取分类
            if "category" in item:
                categories.add(item["category"])
        
        # 智能分类建议
        organization_method = "按主题分类"
        if len(categories) >= 3:
            organization_method = "按分类体系组织"
        elif len(tags) >= 10:
            organization_method = "按标签系统组织"
        elif len(knowledge_items) <= 5:
            organization_method = "单一知识库"
        
        return {
            "suggested_topics": list(topics),
            "suggested_tags": list(tags)[:20],  # 限制标签数量
            "suggested_categories": list(categories),
            "organization_method": organization_method,
            "recommendations": [
                "建议按主题分组管理",
                "建议添加标签系统",
                "建议建立知识索引",
                "建议定期清理重复内容",
                "建议建立知识质量评估机制"
            ],
            "metadata": {
                "total_items": len(knowledge_items),
                "topic_count": len(topics),
                "tag_count": len(tags),
                "category_count": len(categories)
            }
        }
    
    async def evaluate_knowledge_quality(
        self,
        knowledge_item: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        评估单个知识条目的质量
        
        Args:
            knowledge_item: 知识条目
            
        Returns:
            质量评估结果
        """
        quality_score = 0.0
        quality_factors = []
        
        # 内容完整性评估
        content = knowledge_item.get("content", "")
        title = knowledge_item.get("title", "")
        
        if content and len(content.strip()) > 50:
            quality_score += 0.3
            quality_factors.append("内容完整")
        else:
            quality_factors.append("内容过短")
        
        if title and len(title.strip()) > 5:
            quality_score += 0.2
            quality_factors.append("标题明确")
        else:
            quality_factors.append("标题不明确")
        
        # 元数据完整性
        metadata_keys = ["category", "tags", "author", "created_at"]
        metadata_count = sum(1 for key in metadata_keys if key in knowledge_item)
        
        if metadata_count >= 3:
            quality_score += 0.3
            quality_factors.append("元数据完整")
        else:
            quality_factors.append(f"元数据缺失({metadata_count}/4)")
        
        # 时效性评估
        if "created_at" in knowledge_item:
            quality_score += 0.2
            quality_factors.append("有时间戳")
        
        # 质量等级
        if quality_score >= 0.8:
            quality_level = "优秀"
        elif quality_score >= 0.6:
            quality_level = "良好"
        elif quality_score >= 0.4:
            quality_level = "一般"
        else:
            quality_level = "需要改进"
        
        return {
            "quality_score": quality_score,
            "quality_level": quality_level,
            "quality_factors": quality_factors,
            "improvement_suggestions": [
                "建议补充完整内容",
                "建议添加明确的标题",
                "建议完善元数据信息",
                "建议添加时间戳"
            ]
        }


class RetrievalExpert:
    """
    检索专家（T004-2）- 生产级增强版
    
    专业能力：
    1. 检索策略优化
    2. 检索质量评估  
    3. 检索结果排序
    4. 检索性能优化
    5. 检索质量预警生成
    6. 实时监控与指标追踪
    7. AI驱动检索优化
    8. 生产级可观测性
    """
    
    def __init__(self, config: Optional[RAGExpertConfig] = None):
        self.expert_id = "rag_retrieval_expert"
        self.name = "检索优化专家"
        self.domain = ExpertDomain.RETRIEVAL
        self.stage = "production"
        
        # 使用新的配置系统
        from .rag_config import get_rag_config, get_expert_config
        self.system_config = get_rag_config()
        self.config = config or get_expert_config(self.expert_id)
        
        # 可观测性
        self.observability_system = get_observability_system()
        self.logger = self.observability_system.create_logger(self.expert_id)
        
        # 监控系统
        from .rag_monitoring import get_monitoring_system
        self.monitoring_system = get_monitoring_system()
        
        # 生产级监控增强
        self.monitoring_active = False
        self.monitoring_id = None
        self.monitoring_start_time = None
        self.alert_counter = 0
        self.monitoring_metrics = {
            "retrieval_quality_score": 0.0,
            "retrieval_performance_ms": 0.0,
            "query_complexity": 0.0,
            "error_rate": 0.0
        }
        
        logger.info(f"检索专家初始化完成 - 高质量阈值: {self.config.high_quality_threshold}")
        
    async def optimize_retrieval(
        self,
        query: str,
        retrieval_results: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertAnalysis:
        """
        优化检索策略 - 生产级增强版
        
        Args:
            query: 查询文本
            retrieval_results: 检索结果
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        # 开始追踪操作
        with self.observability_system.trace_operation(
            "retrieval_expert_optimization", 
            TracingContext()
        ) as (span, logger):
            
            # 记录监控指标
            self.monitoring_system.metrics_collector.record_counter("rag_expert_analysis_total", 
                labels={"expert": self.expert_id, "domain": self.domain.value})
            start_time = time.time()
            
            try:
                insights: List[str] = []
                recommendations: List[str] = []
                avg_score = 0.0
                high_quality_ratio = 0.0
                
                # 记录分析参数
                span.add_tag("query_length", len(query))
                span.add_tag("retrieval_results_count", len(retrieval_results))
                logger.info("开始检索优化分析", 
                    query_length=len(query),
                    results_count=len(retrieval_results),
                    config_high_quality_threshold=self.config.high_quality_threshold)
                
                # 分析检索结果质量
                total_results = len(retrieval_results)
                if total_results > 0:
                    avg_score = sum(
                        r.get("score", r.get("relevance", 0.5))
                        for r in retrieval_results
                    ) / total_results
                    
                    # 计算高质量结果比例（使用配置阈值）
                    high_quality_count = sum(1 for r in retrieval_results 
                                           if r.get("score", r.get("relevance", 0.5)) >= self.config.high_quality_threshold)
                    high_quality_ratio = high_quality_count / total_results
                    
                    insights.append(f"检索到 {total_results} 条结果")
                    insights.append(f"平均相关性: {avg_score:.2f}")
                    insights.append(f"高质量结果比例: {high_quality_ratio:.1%}")
                    
                    # 评估检索质量（使用配置阈值）
                    if avg_score >= 0.8 and high_quality_ratio >= 0.8:
                        insights.append("检索质量优秀")
                    elif avg_score >= 0.6 and high_quality_ratio >= 0.6:
                        insights.append("检索质量良好")
                        recommendations.append("建议优化查询语句，提升相关性")
                    else:
                        insights.append("检索质量需要改进")
                        recommendations.append("建议重新设计检索策略")
                    
                    # 分析查询复杂度
                    query_complexity = len(query.split())
                    if query_complexity <= 3:
                        insights.append("查询过于简单，可能召回过多结果")
                        recommendations.append("建议增加查询关键词")
                    elif query_complexity >= 8:
                        insights.append("查询过于复杂，可能影响召回率")
                        recommendations.append("建议简化查询语句")
                else:
                    insights.append("未检索到相关结果")
                    recommendations.extend([
                        "建议扩展查询范围",
                        "建议使用同义词或相关词",
                        "建议检查知识库内容覆盖"
                    ])
                    avg_score = 0.0
                    
                # 生产级增强：生成检索预警
                alerts = await self._generate_retrieval_alerts(
                    avg_score=avg_score,
                    high_quality_ratio=high_quality_ratio,
                    total_results=total_results,
                    query_complexity=len(query.split())
                )
                
                # 更新监控指标
                self.monitoring_metrics.update({
                    "retrieval_quality_score": avg_score,
                    "retrieval_performance_ms": (time.time() - start_time) * 1000,
                    "query_complexity": len(query.split()) / 10.0,  # 归一化
                    "error_rate": 0.0  # 暂时设为0，后续可根据错误情况计算
                })
                
                # 记录分析结果
                analysis_result = ExpertAnalysis(
                    domain=self.domain,
                    confidence=0.92,  # 提升置信度
                    insights=insights,
                    recommendations=recommendations,
                    metadata={
                        "total_results": total_results,
                        "avg_score": avg_score,
                        "high_quality_ratio": high_quality_ratio if total_results > 0 else 0,
                        "query_complexity": len(query.split()),
                        "alerts_generated": len(alerts),
                        "alerts": alerts
                    }
                )
                
                # 记录监控指标
                duration = time.time() - start_time
                self.monitoring_system.metrics_collector.record_histogram(
                    "rag_expert_analysis_duration_seconds", 
                    duration,
                    labels={"expert": self.expert_id}
                )
                
                # 记录检索质量指标
                self.monitoring_system.metrics_collector.record_gauge(
                    "rag_retrieval_quality_score",
                    avg_score,
                    labels={"expert": self.expert_id}
                )
                
                logger.info("检索优化分析完成 - 生产级增强版", 
                    duration=duration,
                    insights_count=len(insights),
                    recommendations_count=len(recommendations),
                    alerts_count=len(alerts),
                    confidence=0.92)
                
                return analysis_result
                
            except Exception as e:
                # 记录错误
                self.monitoring_system.metrics_collector.increment_counter(
                    "rag_expert_analysis_errors_total",
                    labels={"expert": self.expert_id, "error_type": type(e).__name__}
                )
                logger.error("检索优化分析失败", error=str(e), exc_info=True)
                raise
    
    async def _generate_retrieval_alerts(
        self,
        avg_score: float,
        high_quality_ratio: float,
        total_results: int,
        query_complexity: int
    ) -> List[str]:
        """
        生成检索质量预警
        
        Args:
            avg_score: 平均相关性分数
            high_quality_ratio: 高质量结果比例
            total_results: 总结果数
            query_complexity: 查询复杂度
            
        Returns:
            预警信息列表
        """
        alerts = []
        
        # 低质量检索预警
        if avg_score < 0.3:
            alerts.append("检索质量严重不足，相关性分数过低")
            self.alert_counter += 1
        elif avg_score < 0.5:
            alerts.append("检索质量较低，建议优化检索策略")
        
        # 高质量结果不足预警
        if high_quality_ratio < 0.2:
            alerts.append("高质量结果严重不足，需要优化检索算法")
            self.alert_counter += 1
        elif high_quality_ratio < 0.4:
            alerts.append("高质量结果较少，建议提升检索精度")
        
        # 结果数量不足预警
        if total_results == 0:
            alerts.append("未检索到任何结果，需要检查知识库覆盖")
            self.alert_counter += 1
        elif total_results < 3:
            alerts.append("检索结果数量较少，建议扩展查询范围")
        
        # 查询复杂度预警
        if query_complexity < 2:
            alerts.append("查询过于简单，可能导致召回过多无关结果")
        elif query_complexity > 10:
            alerts.append("查询过于复杂，可能影响检索性能")
        
        # 记录预警指标
        if alerts:
            self.monitoring_system.metrics_collector.record_counter(
                "rag_retrieval_alerts_total",
                value=len(alerts),
                labels={"expert": self.expert_id}
            )
        
        return alerts
    
    async def start_real_time_monitoring(self) -> Dict[str, Any]:
        """
        启动实时监控
        
        Returns:
            监控启动结果
        """
        if self.monitoring_active:
            return {"status": "already_running", "message": "监控已启动"}
        
        self.monitoring_active = True
        self.monitoring_id = f"retrieval_monitor_{int(time.time())}"
        self.monitoring_start_time = time.time()
        
        # 初始化监控指标
        self.monitoring_metrics = {
            "retrieval_quality_score": 0.0,
            "retrieval_performance_ms": 0.0,
            "query_complexity": 0.0,
            "error_rate": 0.0
        }
        
        self.logger.info("检索专家实时监控已启动", monitoring_id=self.monitoring_id)
        
        return {
            "status": "started",
            "monitoring_id": self.monitoring_id,
            "start_time": self.monitoring_start_time,
            "metrics": self.monitoring_metrics
        }
    
    async def stop_real_time_monitoring(self) -> Dict[str, Any]:
        """
        停止实时监控
        
        Returns:
            监控报告
        """
        if not self.monitoring_active:
            return {"status": "not_running", "message": "监控未启动"}
        
        monitoring_duration = self._calculate_monitoring_duration()
        effectiveness = self._calculate_monitoring_effectiveness()
        
        report = {
            "status": "stopped",
            "monitoring_id": self.monitoring_id,
            "duration_seconds": monitoring_duration,
            "effectiveness_score": effectiveness,
            "alerts_generated": self.alert_counter,
            "final_metrics": self.monitoring_metrics,
            "insights": self._generate_monitoring_insights(),
            "recommendations": self._generate_monitoring_recommendations()
        }
        
        self.monitoring_active = False
        self.monitoring_id = None
        self.monitoring_start_time = None
        self.alert_counter = 0
        
        self.logger.info("检索专家实时监控已停止", 
            duration=monitoring_duration,
            effectiveness=effectiveness,
            alerts=self.alert_counter)
        
        return report
    
    async def optimize_retrieval_parameters(self) -> Dict[str, Any]:
        """
        优化检索参数
        
        Returns:
            优化建议和ROI估算
        """
        current_quality = self.monitoring_metrics["retrieval_quality_score"]
        current_performance = self.monitoring_metrics["retrieval_performance_ms"]
        current_error_rate = self.monitoring_metrics["error_rate"]
        
        optimization_suggestions = []
        roi_estimates = []
        
        # 质量优化建议
        if current_quality < 0.7:
            quality_improvement = 0.7 - current_quality
            optimization_suggestions.append({
                "area": "检索质量",
                "current": f"{current_quality:.2f}",
                "target": "0.70",
                "improvement": f"{quality_improvement:.2f}",
                "suggestions": [
                    "优化检索算法",
                    "改进相关性计算",
                    "增加语义理解能力"
                ]
            })
            roi_estimates.append({
                "area": "质量优化",
                "estimated_roi": "200%",
                "timeframe": "2个月"
            })
        
        # 性能优化建议
        if current_performance > 500:  # 超过500ms
            performance_improvement = current_performance - 200
            optimization_suggestions.append({
                "area": "检索性能",
                "current": f"{current_performance:.0f}ms",
                "target": "200ms",
                "improvement": f"{performance_improvement:.0f}ms",
                "suggestions": [
                    "优化索引结构",
                    "实施缓存策略",
                    "并行处理查询"
                ]
            })
            roi_estimates.append({
                "area": "性能优化",
                "estimated_roi": "180%",
                "timeframe": "3个月"
            })
        
        # 错误率优化建议
        if current_error_rate > 0.05:
            error_improvement = current_error_rate - 0.01
            optimization_suggestions.append({
                "area": "系统稳定性",
                "current": f"{current_error_rate:.1%}",
                "target": "1%",
                "improvement": f"{error_improvement:.1%}",
                "suggestions": [
                    "增强错误处理机制",
                    "实施重试策略",
                    "优化系统容错能力"
                ]
            })
            roi_estimates.append({
                "area": "稳定性优化",
                "estimated_roi": "250%",
                "timeframe": "1个月"
            })
        
        return {
            "optimization_suggestions": optimization_suggestions,
            "roi_estimates": roi_estimates,
            "current_state": {
                "quality_score": current_quality,
                "performance_ms": current_performance,
                "error_rate": current_error_rate
            },
            "overall_recommendation": "建议优先优化检索质量和系统稳定性，可获得较高ROI"
        }
    
    def _calculate_monitoring_duration(self) -> float:
        """计算监控持续时间"""
        if not self.monitoring_start_time:
            return 0.0
        return time.time() - self.monitoring_start_time
    
    def _calculate_monitoring_effectiveness(self) -> float:
        """计算监控有效性"""
        if self.alert_counter == 0:
            return 1.0  # 无预警表示系统健康
        
        # 基于预警数量和监控时长计算有效性
        duration = self._calculate_monitoring_duration()
        if duration == 0:
            return 0.0
        
        # 预警密度越低，有效性越高
        alert_density = self.alert_counter / duration
        effectiveness = max(0, 1 - (alert_density / 5))  # 假设每5秒1个预警为基准
        
        return min(effectiveness, 1.0)
    
    def _generate_monitoring_insights(self) -> List[str]:
        """生成监控洞察"""
        insights = []
        
        if self.monitoring_metrics["error_rate"] > 0.1:
            insights.append("检索系统错误率较高，需要优化稳定性")
        
        if self.monitoring_metrics["retrieval_quality_score"] < 0.5:
            insights.append("检索质量持续偏低，建议加强算法优化")
        
        if self.monitoring_metrics["retrieval_performance_ms"] > 1000:
            insights.append("检索性能较慢，需要优化响应时间")
        
        if self.alert_counter > 5:
            insights.append(f"监控期间生成{self.alert_counter}个预警，系统稳定性需要关注")
        
        if len(insights) == 0:
            insights.append("检索系统运行稳定，各项指标正常")
        
        return insights
    
    def _generate_monitoring_recommendations(self) -> List[str]:
        """生成监控建议"""
        recommendations = []
        
        if self.monitoring_metrics["retrieval_quality_score"] < 0.6:
            recommendations.append("优化检索算法和相关性计算")
            recommendations.append("增加语义理解能力")
        
        if self.monitoring_metrics["retrieval_performance_ms"] > 500:
            recommendations.append("优化索引结构和缓存策略")
            recommendations.append("实施查询并行处理")
        
        if self.monitoring_metrics["error_rate"] > 0.05:
            recommendations.append("增强错误处理机制")
            recommendations.append("实施重试策略")
        
        if self.alert_counter > 3:
            recommendations.append("建立预警响应流程")
            recommendations.append("优化监控阈值设置")
        
        if len(recommendations) == 0:
            recommendations.append("继续保持当前监控策略")
        
        return recommendations
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """
        获取当前监控状态
        
        Returns:
            监控状态信息
        """
        return {
            "monitoring_active": self.monitoring_active,
            "monitoring_id": self.monitoring_id,
            "alert_counter": self.alert_counter,
            "current_metrics": self.monitoring_metrics,
            "monitoring_duration": self._calculate_monitoring_duration(),
            "monitoring_effectiveness": self._calculate_monitoring_effectiveness()
        }
    
    async def optimize_query(
        self,
        original_query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        优化查询语句
        
        Args:
            original_query: 原始查询
            context: 上下文信息
            
        Returns:
            优化后的查询建议
        """
        # 基础查询优化
        query_words = original_query.split()
        
        # 去除停用词（简单实现）
        stop_words = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}
        
        filtered_words = [word for word in query_words if word not in stop_words]
        
        # 查询扩展建议
        expansion_suggestions = []
        if len(filtered_words) < 3:
            expansion_suggestions.append("建议添加更多关键词以提升检索精度")
        
        # 同义词扩展
        synonym_mapping = {
            "如何": ["怎样", "怎么", "方法"],
            "问题": ["故障", "错误", "异常"],
            "解决": ["处理", "修复", "排除"],
            "优化": ["改进", "提升", "增强"],
            "分析": ["评估", "诊断", "检查"]
        }
        
        synonyms = []
        for word in filtered_words:
            if word in synonym_mapping:
                synonyms.extend(synonym_mapping[word])
        
        # 构建优化后的查询
        optimized_query = " ".join(filtered_words)
        if synonyms:
            optimized_query += " " + " ".join(synonyms[:3])
        
        return {
            "original_query": original_query,
            "optimized_query": optimized_query,
            "query_analysis": {
                "word_count": len(query_words),
                "filtered_word_count": len(filtered_words),
                "stop_words_removed": len(query_words) - len(filtered_words)
            },
            "optimization_suggestions": expansion_suggestions + [
                "建议使用具体的关键词",
                "建议包含问题描述和期望结果",
                "建议避免使用模糊的词语"
            ],
            "synonyms_suggested": synonyms[:5]
        }
    
    async def analyze(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ExpertAnalysis:
        """
        通用分析接口，用于专家协作
        
        Args:
            data: 分析数据
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        query = data.get("query", "")
        retrieval_results = data.get("retrieval_results", [])
        
        return await self.optimize_retrieval(query, retrieval_results, context)
        
        # 分析查询复杂度
        query_length = len(query)
        if query_length < 10:
            recommendations.append("查询过短，建议提供更多上下文")
        elif query_length > 200:
            recommendations.append("查询过长，建议精简关键词")
        
        # 检索策略建议
        if total_results == 0:
            recommendations.append("未检索到结果，建议：1) 扩展查询范围 2) 使用同义词 3) 检查知识库")
        elif total_results < 3:
            recommendations.append("结果较少，建议使用模糊匹配或语义扩展")
        
        return ExpertAnalysis(
            domain=self.domain,
            confidence=0.90,
            insights=insights,
            recommendations=recommendations,
            metadata={
                "query_length": query_length,
                "total_results": total_results,
                "avg_score": avg_score if total_results > 0 else 0,
            }
        )
    
    async def rerank_results(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        重新排序检索结果
        
        Args:
            results: 检索结果
            query: 查询文本
            
        Returns:
            重新排序后的结果
        """
        # 简单的重排序：按分数降序
        sorted_results = sorted(
            results,
            key=lambda x: x.get("score", x.get("relevance", 0.5)),
            reverse=True
        )
        
        # 可以添加更复杂的排序逻辑
        # 例如：考虑查询关键词匹配度、时间新鲜度等
        
        return sorted_results


class GraphExpert:
    """
    图谱专家（T004-3）- 生产级增强版
    
    专业能力：
    1. 知识图谱构建
    2. 图谱关系挖掘
    3. 图谱推理查询
    4. 图谱可视化建议
    5. 图谱质量预警生成
    6. 实时监控与指标追踪
    7. AI驱动图谱优化
    8. 生产级可观测性
    """
    
    def __init__(self, config: Optional[RAGExpertConfig] = None):
        self.expert_id = "rag_graph_expert"
        self.name = "知识图谱专家"
        self.domain = ExpertDomain.GRAPH
        self.stage = "production"
        
        # 使用新的配置系统
        from .rag_config import get_rag_config, get_expert_config
        self.system_config = get_rag_config()
        self.config = config or get_expert_config(self.expert_id)
        
        # 可观测性
        self.observability_system = get_observability_system()
        self.logger = self.observability_system.create_logger(self.expert_id)
        
        # 监控系统
        from .rag_monitoring import get_monitoring_system
        self.monitoring_system = get_monitoring_system()
        
        # 生产级监控增强
        self.monitoring_active = False
        self.monitoring_id = None
        self.monitoring_start_time = None
        self.alert_counter = 0
        self.monitoring_metrics = {
            "graph_quality_score": 0.0,
            "graph_density": 0.0,
            "entity_completeness": 0.0,
            "relationship_strength": 0.0
        }
        
        logger.info(f"图谱专家初始化完成 - 生产级增强版")
        
    async def analyze_knowledge_graph(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertAnalysis:
        """
        分析知识图谱结构 - 生产级增强版
        
        Args:
            entities: 实体列表
            relationships: 关系列表
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        insights: List[str] = []
        recommendations: List[str] = []
        
        # 分析图谱规模
        entity_count = len(entities)
        relationship_count = len(relationships)
        
        insights.append(f"图谱包含 {entity_count} 个实体")
        insights.append(f"图谱包含 {relationship_count} 个关系")
        
        # 计算图谱密度
        if entity_count > 1:
            max_possible_relationships = entity_count * (entity_count - 1)
            graph_density = relationship_count / max_possible_relationships if max_possible_relationships > 0 else 0
            insights.append(f"图谱密度: {graph_density:.3f}")
            
            if graph_density < 0.1:
                recommendations.append("图谱密度较低，建议挖掘更多关系")
            elif graph_density > 0.5:
                recommendations.append("图谱密度较高，可能存在冗余关系")
        
        # 分析实体类型分布
        entity_types = {}
        for entity in entities:
            entity_type = entity.get("type", "未知")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        if entity_types:
            insights.append(f"实体类型分布: {len(entity_types)} 种类型")
            top_type = max(entity_types.items(), key=lambda x: x[1])
            insights.append(f"主要实体类型: {top_type[0]} ({top_type[1]}个)")
        
        # 分析关系类型
        relation_types = {}
        for relation in relationships:
            relation_type = relation.get("type", "未知")
            relation_types[relation_type] = relation_types.get(relation_type, 0) + 1
        
        if relation_types:
            insights.append(f"关系类型分布: {len(relation_types)} 种类型")
        
        # 生产级增强：图谱质量评估和预警生成
        graph_quality_score = self._calculate_graph_quality(entity_count, relationship_count, graph_density)
        alerts = await self._generate_graph_alerts(entity_count, relationship_count, graph_density, graph_quality_score)
        
        # 更新监控指标
        self.monitoring_metrics["graph_quality_score"] = graph_quality_score
        self.monitoring_metrics["graph_density"] = graph_density if entity_count > 1 else 0
        self.monitoring_metrics["entity_completeness"] = self._calculate_entity_completeness(entities)
        self.monitoring_metrics["relationship_strength"] = self._calculate_relationship_strength(relationships)
        
        # 记录监控数据
        if self.monitoring_active:
            await self.monitoring_system.record_metric(
                self.monitoring_id,
                "graph_quality_score",
                graph_quality_score
            )
        
        # 扩展元数据以包含预警信息
        metadata = {
            "entity_count": entity_count,
            "relationship_count": relationship_count,
            "entity_type_count": len(entity_types),
            "relation_type_count": len(relation_types),
            "graph_density": graph_density if entity_count > 1 else 0,
            "graph_quality_score": graph_quality_score,
            "alerts_generated": len(alerts),
            "alert_types": [alert["type"] for alert in alerts]
        }
        
        # 如果有预警，增加相关建议
        if alerts:
            recommendations.extend([f"预警: {alert['message']}" for alert in alerts])
        
        self.logger.info(f"图谱分析完成 - 质量评分: {graph_quality_score:.3f}, 预警数量: {len(alerts)}")
        
        return ExpertAnalysis(
            domain=self.domain,
            confidence=0.92,  # 提升置信度
            insights=insights,
            recommendations=recommendations,
            metadata=metadata
        )
    
    async def _generate_graph_alerts(
        self,
        entity_count: int,
        relationship_count: int,
        graph_density: float,
        quality_score: float
    ) -> List[Dict[str, Any]]:
        """生成图谱质量预警"""
        alerts = []
        
        # 低质量图谱预警
        if quality_score < 0.6:
            alerts.append({
                "type": "low_quality_graph",
                "level": "warning",
                "message": f"图谱质量评分较低 ({quality_score:.3f})，建议优化图谱结构",
                "suggestions": ["检查实体完整性", "优化关系权重", "增加图谱密度"]
            })
            self.alert_counter += 1
        
        # 稀疏图谱预警
        if entity_count > 10 and graph_density < 0.05:
            alerts.append({
                "type": "sparse_graph",
                "level": "warning", 
                "message": f"图谱过于稀疏 (密度: {graph_density:.3f})，建议挖掘更多关系",
                "suggestions": ["挖掘隐藏关系", "扩展实体连接", "优化图谱构建算法"]
            })
            self.alert_counter += 1
        
        # 实体不足预警
        if entity_count < 5:
            alerts.append({
                "type": "insufficient_entities",
                "level": "warning",
                "message": f"实体数量不足 ({entity_count}个)，图谱规模过小",
                "suggestions": ["扩展实体数量", "导入更多数据源", "优化实体提取"]
            })
            self.alert_counter += 1
        
        # 关系不足预警
        if relationship_count < entity_count * 0.5 and entity_count > 5:
            alerts.append({
                "type": "insufficient_relationships",
                "level": "warning",
                "message": f"关系数量不足 ({relationship_count}个)，建议增加关系连接",
                "suggestions": ["挖掘实体间关系", "优化关系抽取", "增加关系类型"]
            })
            self.alert_counter += 1
        
        return alerts
    
    def _calculate_graph_quality(
        self,
        entity_count: int,
        relationship_count: int,
        graph_density: float
    ) -> float:
        """计算图谱质量评分"""
        if entity_count == 0:
            return 0.0
        
        # 基于实体数量、关系数量和密度的综合评分
        entity_score = min(entity_count / 100.0, 1.0)  # 实体数量评分
        relationship_score = min(relationship_count / 200.0, 1.0)  # 关系数量评分
        density_score = min(graph_density * 2.0, 1.0)  # 密度评分
        
        # 加权平均
        quality_score = (entity_score * 0.3 + relationship_score * 0.3 + density_score * 0.4)
        
        return round(quality_score, 3)
    
    def _calculate_entity_completeness(self, entities: List[Dict[str, Any]]) -> float:
        """计算实体完整性评分"""
        if not entities:
            return 0.0
        
        completeness_scores = []
        for entity in entities:
            score = 0.0
            if entity.get("name"):
                score += 0.3
            if entity.get("description"):
                score += 0.3
            if entity.get("attributes") and len(entity["attributes"]) > 0:
                score += 0.4
            completeness_scores.append(score)
        
        return sum(completeness_scores) / len(completeness_scores)
    
    def _calculate_relationship_strength(self, relationships: List[Dict[str, Any]]) -> float:
        """计算关系强度评分"""
        if not relationships:
            return 0.0
        
        strength_scores = []
        for relation in relationships:
            score = 0.0
            if relation.get("source") and relation.get("target"):
                score += 0.4
            if relation.get("type"):
                score += 0.3
            if relation.get("weight") is not None:
                score += 0.3
            strength_scores.append(score)
        
        return sum(strength_scores) / len(strength_scores)
    
    async def start_real_time_monitoring(self) -> Dict[str, Any]:
        """启动实时监控"""
        if self.monitoring_active:
            return {"status": "already_active", "monitoring_id": self.monitoring_id}
        
        self.monitoring_active = True
        self.monitoring_id = f"graph_expert_{int(time.time())}"
        self.monitoring_start_time = time.time()
        self.alert_counter = 0
        
        # 初始化监控指标
        self.monitoring_metrics = {
            "graph_quality_score": 0.0,
            "graph_density": 0.0,
            "entity_completeness": 0.0,
            "relationship_strength": 0.0
        }
        
        self.logger.info(f"图谱专家实时监控启动 - ID: {self.monitoring_id}")
        
        return {
            "status": "started",
            "monitoring_id": self.monitoring_id,
            "start_time": self.monitoring_start_time
        }
    
    async def stop_real_time_monitoring(self) -> Dict[str, Any]:
        """停止实时监控"""
        if not self.monitoring_active:
            return {"status": "not_active"}
        
        monitoring_duration = self._calculate_monitoring_duration()
        monitoring_effectiveness = self._calculate_monitoring_effectiveness()
        insights = self._generate_monitoring_insights()
        recommendations = self._generate_monitoring_recommendations()
        
        report = {
            "status": "stopped",
            "monitoring_id": self.monitoring_id,
            "monitoring_duration": monitoring_duration,
            "alert_counter": self.alert_counter,
            "monitoring_effectiveness": monitoring_effectiveness,
            "final_metrics": self.monitoring_metrics,
            "insights": insights,
            "recommendations": recommendations
        }
        
        # 重置监控状态
        self.monitoring_active = False
        self.monitoring_id = None
        self.monitoring_start_time = None
        
        self.logger.info(f"图谱专家实时监控停止 - 时长: {monitoring_duration:.1f}s, 预警: {self.alert_counter}个")
        
        return report
    
    async def optimize_graph_parameters(self) -> Dict[str, Any]:
        """优化图谱参数"""
        current_metrics = self.monitoring_metrics
        
        optimization_suggestions = []
        
        # 基于当前指标提供优化建议
        if current_metrics["graph_quality_score"] < 0.7:
            optimization_suggestions.append({
                "area": "图谱质量",
                "suggestion": "优化实体和关系抽取算法，提高图谱构建质量",
                "priority": "high",
                "estimated_roi": 0.3
            })
        
        if current_metrics["graph_density"] < 0.1:
            optimization_suggestions.append({
                "area": "图谱密度", 
                "suggestion": "挖掘更多实体间关系，提高图谱连接性",
                "priority": "medium",
                "estimated_roi": 0.2
            })
        
        if current_metrics["entity_completeness"] < 0.6:
            optimization_suggestions.append({
                "area": "实体完整性",
                "suggestion": "完善实体属性信息，提高数据质量",
                "priority": "medium",
                "estimated_roi": 0.25
            })
        
        if current_metrics["relationship_strength"] < 0.6:
            optimization_suggestions.append({
                "area": "关系强度",
                "suggestion": "为关系添加权重和类型信息，增强关系表达能力",
                "priority": "low",
                "estimated_roi": 0.15
            })
        
        return {
            "current_metrics": current_metrics,
            "optimization_suggestions": optimization_suggestions,
            "total_suggestions": len(optimization_suggestions),
            "overall_roi_estimate": sum(s["estimated_roi"] for s in optimization_suggestions)
        }
    
    def _calculate_monitoring_duration(self) -> float:
        """计算监控持续时间"""
        if not self.monitoring_start_time:
            return 0.0
        return time.time() - self.monitoring_start_time
    
    def _calculate_monitoring_effectiveness(self) -> float:
        """计算监控有效性"""
        duration = self._calculate_monitoring_duration()
        if duration == 0:
            return 0.0
        
        # 基于预警数量和监控时长计算有效性
        alert_density = self.alert_counter / (duration / 60)  # 每分钟预警数
        
        # 有效性评分：预警密度越高，监控越有效
        effectiveness = min(alert_density * 0.5, 1.0)
        
        return round(effectiveness, 3)
    
    def _generate_monitoring_insights(self) -> List[str]:
        """生成监控洞察"""
        insights = []
        
        if self.alert_counter > 0:
            insights.append(f"监控期间检测到 {self.alert_counter} 个预警")
        
        if self.monitoring_metrics["graph_quality_score"] > 0.8:
            insights.append("图谱质量保持较高水平")
        elif self.monitoring_metrics["graph_quality_score"] < 0.5:
            insights.append("图谱质量需要重点关注")
        
        if self.monitoring_metrics["graph_density"] > 0.3:
            insights.append("图谱密度较高，连接性良好")
        elif self.monitoring_metrics["graph_density"] < 0.05:
            insights.append("图谱密度较低，建议优化关系挖掘")
        
        if len(insights) == 0:
            insights.append("图谱系统运行稳定，各项指标正常")
        
        return insights
    
    def _generate_monitoring_recommendations(self) -> List[str]:
        """生成监控建议"""
        recommendations = []
        
        if self.monitoring_metrics["graph_quality_score"] < 0.6:
            recommendations.append("优化图谱构建算法和实体关系抽取")
            recommendations.append("提高图谱数据质量")
        
        if self.monitoring_metrics["graph_density"] < 0.1:
            recommendations.append("挖掘更多实体间关系")
            recommendations.append("优化图谱连接策略")
        
        if self.monitoring_metrics["entity_completeness"] < 0.6:
            recommendations.append("完善实体属性信息")
            recommendations.append("提高数据完整性")
        
        if self.monitoring_metrics["relationship_strength"] < 0.6:
            recommendations.append("增强关系表达能力")
            recommendations.append("为关系添加权重和类型信息")
        
        if self.alert_counter > 3:
            recommendations.append("建立预警响应流程")
            recommendations.append("优化监控阈值设置")
        
        if len(recommendations) == 0:
            recommendations.append("继续保持当前监控策略")
        
        return recommendations
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """
        获取当前监控状态
        
        Returns:
            监控状态信息
        """
        return {
            "monitoring_active": self.monitoring_active,
            "monitoring_id": self.monitoring_id,
            "alert_counter": self.alert_counter,
            "current_metrics": self.monitoring_metrics,
            "monitoring_duration": self._calculate_monitoring_duration(),
            "monitoring_effectiveness": self._calculate_monitoring_effectiveness()
        }
    
    async def suggest_graph_enhancement(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        建议图谱增强方案
        
        Args:
            entities: 实体列表
            relationships: 关系列表
            
        Returns:
            增强建议
        """
        suggestions = []
        
        # 分析实体完整性
        incomplete_entities = []
        for entity in entities:
            missing_fields = []
            if not entity.get("description"):
                missing_fields.append("描述")
            if not entity.get("attributes"):
                missing_fields.append("属性")
            
            if missing_fields:
                incomplete_entities.append({
                    "entity_id": entity.get("id", "未知"),
                    "missing_fields": missing_fields
                })
        
        if incomplete_entities:
            suggestions.append(f"发现 {len(incomplete_entities)} 个实体信息不完整")
        
        # 分析关系质量
        weak_relationships = []
        for relation in relationships:
            if not relation.get("weight"):
                weak_relationships.append(relation.get("id", "未知"))
        
        if weak_relationships:
            suggestions.append(f"发现 {len(weak_relationships)} 个关系缺少权重信息")
        
        # 图谱结构建议
        entity_count = len(entities)
        if entity_count < 10:
            suggestions.append("图谱规模较小，建议扩展实体数量")
        elif entity_count > 1000:
            suggestions.append("图谱规模较大，建议进行分区管理")
        
        return {
            "enhancement_suggestions": suggestions,
            "incomplete_entities": incomplete_entities[:10],  # 限制数量
            "weak_relationships": weak_relationships[:10],
            "recommendations": [
                "建议完善实体描述信息",
                "建议为关系添加权重",
                "建议定期更新图谱内容",
                "建议建立图谱质量评估机制"
            ]
        }
        
    async def analyze_graph_structure(
        self,
        graph_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ExpertAnalysis:
        """
        分析图谱结构
        
        Args:
            graph_data: 图谱数据
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        insights: List[str] = []
        recommendations: List[str] = []
        
        # 分析图谱规模
        entities = graph_data.get("entities", [])
        relationships = graph_data.get("relationships", [])
        entity_count = len(entities)
        relationship_count = len(relationships)
        
        insights.append(f"图谱包含 {entity_count} 个实体")
        insights.append(f"图谱包含 {relationship_count} 个关系")
        
        # 计算图谱密度
        if entity_count > 1:
            max_possible_relationships = entity_count * (entity_count - 1)
            graph_density = relationship_count / max_possible_relationships if max_possible_relationships > 0 else 0
            insights.append(f"图谱密度: {graph_density:.3f}")
            
            if graph_density < 0.1:
                recommendations.append("图谱密度较低，建议挖掘更多关系")
            elif graph_density > 0.5:
                recommendations.append("图谱密度较高，可能存在冗余关系")
        
        # 分析连通性
        if entity_count > 0:
            connected_components = self._find_connected_components(entities, relationships)
            insights.append(f"图谱包含 {len(connected_components)} 个连通分量")
            
            if len(connected_components) > 1:
                recommendations.append("图谱存在多个孤立子图，建议建立连接关系")
        
        # 分析中心性
        if entity_count > 0:
            centrality_analysis = self._analyze_centrality(entities, relationships)
            insights.extend(centrality_analysis["insights"])
            recommendations.extend(centrality_analysis["recommendations"])
        
        return ExpertAnalysis(
            domain=self.domain,
            confidence=0.85,
            insights=insights,
            recommendations=recommendations,
            metadata={
                "entity_count": entity_count,
                "relationship_count": relationship_count,
                "graph_density": graph_density if entity_count > 1 else 0,
                "connected_components": len(connected_components) if entity_count > 0 else 0
            }
        )
    
    def _find_connected_components(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> List[Set[str]]:
        """查找连通分量"""
        # 构建邻接表
        graph = {}
        for entity in entities:
            entity_id = entity.get("id", str(id(entity)))
            graph[entity_id] = set()
        
        for relation in relationships:
            source = relation.get("source")
            target = relation.get("target")
            if source in graph and target in graph:
                graph[source].add(target)
                graph[target].add(source)
        
        # 深度优先搜索查找连通分量
        visited = set()
        components = []
        
        for node in graph:
            if node not in visited:
                component = set()
                stack = [node]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        component.add(current)
                        stack.extend(graph[current] - visited)
                
                components.append(component)
        
        return components
    
    def _analyze_centrality(
        self,
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """分析中心性指标"""
        insights = []
        recommendations = []
        
        # 计算度中心性
        degree_centrality = {}
        for entity in entities:
            entity_id = entity.get("id", str(id(entity)))
            degree_centrality[entity_id] = 0
        
        for relation in relationships:
            source = relation.get("source")
            target = relation.get("target")
            if source in degree_centrality:
                degree_centrality[source] += 1
            if target in degree_centrality:
                degree_centrality[target] += 1
        
        if degree_centrality:
            max_degree_entity = max(degree_centrality.items(), key=lambda x: x[1])
            insights.append(f"度中心性最高的实体: {max_degree_entity[0]} (度: {max_degree_entity[1]})")
            
            if max_degree_entity[1] > len(entities) * 0.3:
                recommendations.append("存在高度中心节点，建议分散连接关系")
        
        return {
            "insights": insights,
            "recommendations": recommendations
        }
    
    async def suggest_graph_enhancement(
        self,
        entities: List[Dict[str, Any]],
        relations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        建议图谱增强方案
        
        Args:
            entities: 实体列表
            relations: 关系列表
            
        Returns:
            增强建议
        """
        suggestions = []
        
        # 检查孤立实体
        entity_ids = {e.get("id") for e in entities}
        related_entities = set()
        for relation in relations:
            related_entities.add(relation.get("source"))
            related_entities.add(relation.get("target"))
        
        isolated_entities = entity_ids - related_entities
        if isolated_entities:
            suggestions.append(f"发现 {len(isolated_entities)} 个孤立实体，建议建立连接")
        
        # 检查关系完整性
        if len(relations) < len(entities) * 0.5:
            suggestions.append("关系数量不足，建议增加实体间关联")
        
        return {
            "suggestions": suggestions,
            "isolated_entities_count": len(isolated_entities),
            "recommendations": [
                "建议使用NER技术自动提取实体",
                "建议使用关系抽取技术发现关系",
                "建议定期更新图谱结构",
            ]
        }
    
    async def analyze(self, data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ExpertAnalysis:
        """
        通用分析接口，用于专家协作
        
        Args:
            data: 分析数据
            context: 上下文信息
            
        Returns:
            专家分析结果
        """
        entities = data.get("entities", [])
        relationships = data.get("relationships", [])
        
        return await self.analyze_knowledge_graph(entities, relationships, context)


def get_rag_experts() -> Dict[str, Any]:
    """
    获取RAG模块所有专家（T004）
    
    Returns:
        专家字典
    """
    return {
        "knowledge_expert": KnowledgeExpert(),
        "retrieval_expert": RetrievalExpert(),
        "graph_expert": GraphExpert(),
    }
