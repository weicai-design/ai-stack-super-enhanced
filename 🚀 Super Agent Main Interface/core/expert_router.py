"""
专家路由系统
根据用户输入和RAG检索结果，路由到对应的专家
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import re

class ExpertRouter:
    """
    专家路由系统
    
    功能：
    1. 分析用户意图
    2. 识别领域
    3. 路由到对应专家
    4. 专家分散到各模块
    """
    
    def __init__(self):
        # 专家领域映射
        self.expert_domains = {
            "rag": {
                "keywords": ["知识", "文档", "检索", "RAG", "知识库", "知识图谱"],
                "expert": "rag_expert",
                "module": "rag"
            },
            "erp": {
                "keywords": ["订单", "客户", "项目", "采购", "生产", "库存", "ERP", "企业"],
                "expert": "erp_expert",
                "module": "erp"
            },
            "content": {
                "keywords": ["内容", "创作", "文章", "视频", "脚本", "发布", "抖音"],
                "expert": "content_expert",
                "module": "content"
            },
            "trend": {
                "keywords": ["趋势", "分析", "预测", "市场", "行业"],
                "expert": "trend_expert",
                "module": "trend"
            },
            "stock": {
                "keywords": ["股票", "交易", "投资", "量化", "策略"],
                "expert": "stock_expert",
                "module": "stock"
            },
            "operations": {
                "keywords": ["运营", "管理", "数据分析", "图表"],
                "expert": "operations_expert",
                "module": "operations"
            },
            "finance": {
                "keywords": ["财务", "价格", "成本", "工时", "预算"],
                "expert": "finance_expert",
                "module": "finance"
            },
            "coding": {
                "keywords": ["代码", "编程", "开发", "函数", "类", "API", "bug"],
                "expert": "coding_expert",
                "module": "coding"
            },
            "task": {
                "keywords": ["任务", "计划", "工作", "待办", "执行"],
                "expert": "task_expert",
                "module": "task"
            }
        }
    
    async def route(
        self,
        user_input: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        路由到对应专家
        
        Args:
            user_input: 用户输入
            rag_result: 第1次RAG检索结果
            
        Returns:
            专家信息
        """
        # 分析用户意图
        intent = await self._analyze_intent(user_input, rag_result)
        
        # 识别领域
        domain = await self._identify_domain(user_input, rag_result, intent)
        
        # 获取专家信息
        expert_info = self.expert_domains.get(domain, self.expert_domains["rag"])
        
        return {
            "expert": expert_info["expert"],
            "domain": domain,
            "module": expert_info["module"],
            "confidence": intent.get("confidence", 0.7),
            "intent": intent,
            "routed_at": datetime.now().isoformat()
        }
    
    async def _analyze_intent(
        self,
        user_input: str,
        rag_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析用户意图"""
        # 从RAG结果中提取理解
        understanding = rag_result.get("understanding", {})
        
        # 简单关键词匹配
        intent_type = "query"  # query, command, question, request
        
        if any(keyword in user_input for keyword in ["帮我", "请", "执行", "做"]):
            intent_type = "command"
        elif user_input.endswith("?") or any(keyword in user_input for keyword in ["什么", "如何", "为什么"]):
            intent_type = "question"
        elif any(keyword in user_input for keyword in ["生成", "创建", "制作"]):
            intent_type = "request"
        
        return {
            "type": intent_type,
            "confidence": 0.8,
            "understanding": understanding
        }
    
    async def _identify_domain(
        self,
        user_input: str,
        rag_result: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> str:
        """识别领域"""
        # 从RAG结果中提取领域信息
        knowledge = rag_result.get("knowledge", [])
        
        # 关键词匹配
        domain_scores = {}
        for domain, config in self.expert_domains.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in user_input:
                    score += 1
            # 检查知识库中的领域信息
            for item in knowledge:
                content = item.get("content", "")
                for keyword in config["keywords"]:
                    if keyword in content:
                        score += 0.5
            domain_scores[domain] = score
        
        # 返回得分最高的领域
        if domain_scores:
            best_domain = max(domain_scores.items(), key=lambda x: x[1])
            if best_domain[1] > 0:
                return best_domain[0]
        
        # 默认返回RAG
        return "rag"

