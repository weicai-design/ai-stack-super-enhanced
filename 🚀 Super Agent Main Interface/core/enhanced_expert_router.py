#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强专家路由系统
P0-002: 基于RAG检索结果和意图分析的智能专家路由
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExpertRoutingResult:
    """专家路由结果"""
    expert: str
    domain: str
    module: str
    confidence: float
    intent: Dict[str, Any]
    routing_time: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "expert": self.expert,
            "domain": self.domain,
            "module": self.module,
            "confidence": self.confidence,
            "intent": self.intent,
            "routing_time": self.routing_time,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class EnhancedExpertRouter:
    """
    增强专家路由系统
    
    功能：
    1. 基于RAG检索结果分析用户意图
    2. 识别领域（支持多领域识别）
    3. 智能路由到对应专家
    4. 支持专家能力评估
    """
    
    def __init__(self):
        # 专家领域映射（增强版）
        self.expert_domains = {
            "rag": {
                "keywords": ["知识", "文档", "检索", "RAG", "知识库", "知识图谱", "搜索", "查找"],
                "expert": "rag_expert",
                "module": "rag",
                "priority": 1,
                "capabilities": ["knowledge_retrieval", "document_search", "kg_query"],
            },
            "erp": {
                "keywords": ["订单", "客户", "项目", "采购", "生产", "库存", "ERP", "企业", "业务流程"],
                "expert": "erp_expert",
                "module": "erp",
                "priority": 2,
                "capabilities": ["order_management", "inventory", "production"],
            },
            "content": {
                "keywords": ["内容", "创作", "文章", "视频", "脚本", "发布", "抖音", "文案", "编辑"],
                "expert": "content_expert",
                "module": "content",
                "priority": 2,
                "capabilities": ["content_generation", "video_script", "copyright_check"],
            },
            "trend": {
                "keywords": ["趋势", "分析", "预测", "市场", "行业", "数据", "洞察"],
                "expert": "trend_expert",
                "module": "trend",
                "priority": 2,
                "capabilities": ["trend_analysis", "prediction", "market_research"],
            },
            "stock": {
                "keywords": ["股票", "交易", "投资", "量化", "策略", "行情", "分析"],
                "expert": "stock_expert",
                "module": "stock",
                "priority": 2,
                "capabilities": ["trading", "quantitative_analysis", "risk_management"],
            },
            "operations": {
                "keywords": ["运营", "管理", "数据分析", "图表", "报表", "KPI"],
                "expert": "operations_expert",
                "module": "operations",
                "priority": 2,
                "capabilities": ["data_analysis", "dashboard", "kpi_tracking"],
            },
            "finance": {
                "keywords": ["财务", "价格", "成本", "工时", "预算", "会计", "账务"],
                "expert": "finance_expert",
                "module": "finance",
                "priority": 2,
                "capabilities": ["cost_analysis", "budget_planning", "financial_reporting"],
            },
            "coding": {
                "keywords": ["代码", "编程", "开发", "函数", "类", "API", "bug", "调试", "测试"],
                "expert": "coding_expert",
                "module": "coding",
                "priority": 1,
                "capabilities": ["code_review", "debugging", "documentation"],
            },
            "task": {
                "keywords": ["任务", "计划", "工作", "待办", "执行", "安排", "调度"],
                "expert": "task_expert",
                "module": "task",
                "priority": 1,
                "capabilities": ["task_planning", "scheduling", "execution"],
            },
        }
        
        # 意图类型映射
        self.intent_patterns = {
            "query": [r"什么", r"如何", r"为什么", r"？", r"\?"],
            "command": [r"帮我", r"请", r"执行", r"做", r"生成", r"创建"],
            "question": [r"？", r"\?", r"什么", r"如何", r"为什么", r"怎么"],
            "request": [r"生成", r"创建", r"制作", r"提供", r"给"],
        }
        
        # 统计
        self.stats = {
            "total_routings": 0,
            "by_domain": {},
            "avg_confidence": 0.0,
            "avg_routing_time": 0.0,
        }
    
    async def route(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
        timeout: float = 0.5,
    ) -> ExpertRoutingResult:
        """
        路由到对应专家（增强版）
        
        Args:
            user_input: 用户输入
            rag_result: 第1次RAG检索结果
            timeout: 超时时间（秒）
            
        Returns:
            专家路由结果
        """
        start_time = datetime.utcnow()
        
        try:
            # 执行路由（带超时）
            routing_task = asyncio.create_task(
                self._execute_routing(user_input, rag_result)
            )
            result = await asyncio.wait_for(routing_task, timeout=timeout)
            
            routing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新统计
            self.stats["total_routings"] += 1
            self._update_stats(result.domain, result.confidence, routing_time)
            
            result.routing_time = routing_time
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"专家路由超时: {user_input[:50]}")
            return ExpertRoutingResult(
                expert="default_expert",
                domain="general",
                module="rag",
                confidence=0.5,
                intent={"type": "query", "confidence": 0.5, "error": "timeout"},
                routing_time=timeout,
                metadata={"error": "timeout"},
            )
        except Exception as e:
            logger.error(f"专家路由失败: {e}", exc_info=True)
            return ExpertRoutingResult(
                expert="default_expert",
                domain="general",
                module="rag",
                confidence=0.5,
                intent={"type": "query", "confidence": 0.5, "error": str(e)},
                routing_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={"error": str(e)},
            )
    
    async def _execute_routing(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
    ) -> ExpertRoutingResult:
        """执行路由逻辑"""
        # 分析用户意图
        intent = await self._analyze_intent(user_input, rag_result)
        
        # 识别领域（支持多领域）
        domain_result = await self._identify_domain(user_input, rag_result, intent)
        
        # 获取专家信息
        expert_info = self.expert_domains.get(
            domain_result["domain"],
            self.expert_domains["rag"]
        )
        
        # 计算置信度（基于多个因素）
        confidence = self._calculate_confidence(
            domain_result["score"],
            intent["confidence"],
            rag_result,
        )
        
        return ExpertRoutingResult(
            expert=expert_info["expert"],
            domain=domain_result["domain"],
            module=expert_info["module"],
            confidence=confidence,
            intent=intent,
            metadata={
                "domain_scores": domain_result["scores"],
                "matched_keywords": domain_result["matched_keywords"],
                "capabilities": expert_info["capabilities"],
            },
        )
    
    async def _analyze_intent(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """分析用户意图（增强版）"""
        # 从RAG结果中提取理解
        understanding = rag_result.get("understanding", {})
        
        # 意图类型识别
        intent_type = "query"  # 默认
        intent_confidence = 0.7
        
        # 模式匹配
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input):
                    intent_type = intent
                    intent_confidence = 0.8
                    break
            if intent_type != "query":
                break
        
        # 关键词匹配
        if any(keyword in user_input for keyword in ["帮我", "请", "执行", "做"]):
            intent_type = "command"
            intent_confidence = 0.85
        elif user_input.endswith("?") or user_input.endswith("？"):
            intent_type = "question"
            intent_confidence = 0.9
        elif any(keyword in user_input for keyword in ["生成", "创建", "制作"]):
            intent_type = "request"
            intent_confidence = 0.85
        
        # 从RAG理解中增强
        if isinstance(understanding, dict):
            rag_intent = understanding.get("intent", "")
            if rag_intent:
                intent_type = rag_intent
                intent_confidence = max(intent_confidence, understanding.get("confidence", 0.7))
        
        return {
            "type": intent_type,
            "confidence": intent_confidence,
            "understanding": understanding,
            "keywords": self._extract_keywords(user_input),
        }
    
    async def _identify_domain(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
        intent: Dict[str, Any],
    ) -> Dict[str, Any]:
        """识别领域（增强版，支持多领域）"""
        domain_scores = {}
        matched_keywords_map = {}
        
        # 从用户输入中匹配关键词
        for domain, config in self.expert_domains.items():
            score = 0
            matched_keywords = []
            
            for keyword in config["keywords"]:
                if keyword in user_input:
                    score += 2  # 用户输入中的关键词权重更高
                    matched_keywords.append(keyword)
            
            domain_scores[domain] = score
            matched_keywords_map[domain] = matched_keywords
        
        # 从RAG结果中提取领域信息
        knowledge = rag_result.get("knowledge", [])
        if not knowledge:
            knowledge = rag_result.get("knowledge_items", [])
        
        for item in knowledge:
            content = item.get("content", "")
            metadata = item.get("metadata", {})
            
            # 检查内容中的关键词
            for domain, config in self.expert_domains.items():
                for keyword in config["keywords"]:
                    if keyword in content:
                        domain_scores[domain] = domain_scores.get(domain, 0) + 0.5
                        if keyword not in matched_keywords_map.get(domain, []):
                            matched_keywords_map.setdefault(domain, []).append(keyword)
            
            # 检查元数据中的领域信息
            if "domain" in metadata:
                domain_scores[metadata["domain"]] = domain_scores.get(metadata["domain"], 0) + 1
            elif "module" in metadata:
                domain_scores[metadata["module"]] = domain_scores.get(metadata["module"], 0) + 1
        
        # 从理解中提取领域
        understanding = rag_result.get("understanding", {})
        if isinstance(understanding, dict):
            domains = understanding.get("domains", [])
            for domain in domains:
                domain_scores[domain] = domain_scores.get(domain, 0) + 1
        
        # 选择得分最高的领域
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            if best_domain[1] > 0:
                return {
                    "domain": best_domain[0],
                    "score": best_domain[1],
                    "scores": domain_scores,
                    "matched_keywords": matched_keywords_map.get(best_domain[0], []),
                }
        
        # 默认返回RAG
        return {
            "domain": "rag",
            "score": 0.5,
            "scores": domain_scores,
            "matched_keywords": [],
        }
    
    def _calculate_confidence(
        self,
        domain_score: float,
        intent_confidence: float,
        rag_result: Dict[str, Any],
    ) -> float:
        """计算路由置信度"""
        # 基础置信度（基于领域得分）
        base_confidence = min(0.95, domain_score / 5.0)  # 归一化到0-0.95
        
        # 意图置信度加权
        intent_weight = 0.3
        base_confidence = base_confidence * (1 - intent_weight) + intent_confidence * intent_weight
        
        # RAG结果增强
        knowledge = rag_result.get("knowledge", [])
        if not knowledge:
            knowledge = rag_result.get("knowledge_items", [])
        
        if knowledge:
            # 有知识结果，增加置信度
            base_confidence = min(0.95, base_confidence + 0.1)
        
        return round(base_confidence, 2)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词（简单实现）"""
        # 移除标点符号
        text = re.sub(r'[^\w\s]', ' ', text)
        # 分词（简单按空格）
        words = text.split()
        # 过滤短词
        keywords = [w for w in words if len(w) > 1]
        return keywords[:10]  # 最多返回10个关键词
    
    def _update_stats(self, domain: str, confidence: float, routing_time: float):
        """更新统计信息"""
        # 领域统计
        if domain not in self.stats["by_domain"]:
            self.stats["by_domain"][domain] = 0
        self.stats["by_domain"][domain] += 1
        
        # 平均置信度
        total = self.stats["total_routings"]
        current_avg = self.stats["avg_confidence"]
        self.stats["avg_confidence"] = (current_avg * (total - 1) + confidence) / total
        
        # 平均路由时间
        current_avg_time = self.stats["avg_routing_time"]
        self.stats["avg_routing_time"] = (current_avg_time * (total - 1) + routing_time) / total
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "expert_count": len(self.expert_domains),
        }

