"""
RAG专家模块集成测试

测试RAG专家模块的功能完整性、API接口和协作能力
"""

import pytest
import asyncio
from typing import Dict, List, Any

from core.experts.rag_experts import (
    KnowledgeExpert,
    RetrievalExpert,
    GraphExpert,
    ExpertCollaboration,
    ExpertAnalysis
)


class TestKnowledgeExpert:
    """知识专家测试类"""
    
    def setup_method(self):
        """测试前初始化"""
        self.expert = KnowledgeExpert()
    
    @pytest.mark.asyncio
    async def test_analyze_knowledge_basic(self):
        """测试基础知识分析"""
        knowledge_items = [
            {
                "content": "人工智能是计算机科学的一个分支，旨在创造能够执行智能任务的机器。",
                "title": "人工智能定义",
                "category": "technology",
                "score": 0.6  # 降低分数以触发质量建议
            },
            {
                "content": "机器学习是人工智能的重要分支，通过算法让计算机从数据中学习。",
                "title": "机器学习定义",
                "category": "technology",
                "score": 0.7
            }
        ]
        
        result = await self.expert.analyze_knowledge(
            knowledge_items=knowledge_items
        )
        
        assert isinstance(result, ExpertAnalysis)
        assert result.domain.value == "knowledge"
        assert result.confidence > 0.5
        assert len(result.insights) > 0
        assert len(result.recommendations) > 0
        assert "total_items" in result.metadata
        assert result.metadata["total_items"] == 2
    
    @pytest.mark.asyncio
    async def test_suggest_knowledge_organization(self):
        """测试知识组织建议"""
        knowledge_items = [
            {
                "content": "机器学习、深度学习、自然语言处理是人工智能的重要分支。",
                "title": "AI技术分支",
                "category": "technology",
                "tags": ["机器学习", "深度学习", "自然语言处理"]
            }
        ]
        
        result = await self.expert.suggest_knowledge_organization(knowledge_items)
        
        assert isinstance(result, dict)
        assert "suggested_tags" in result
        assert "suggested_categories" in result
        assert "metadata" in result
        assert len(result["suggested_tags"]) > 0
    
    @pytest.mark.asyncio
    async def test_evaluate_knowledge_quality(self):
        """测试知识质量评估"""
        knowledge_item = {
            "content": "这是一个高质量的知识条目，包含详细的信息和清晰的描述。",
            "title": "高质量知识示例",
            "category": "general",
            "author": "系统",
            "created_at": "2024-01-01"
        }
        
        result = await self.expert.evaluate_knowledge_quality(knowledge_item)
        
        assert isinstance(result, dict)
        assert "quality_score" in result
        assert "quality_level" in result
        assert "quality_factors" in result
        assert result["quality_score"] >= 0 and result["quality_score"] <= 1


class TestRetrievalExpert:
    """检索专家测试类"""
    
    def setup_method(self):
        """测试前初始化"""
        self.expert = RetrievalExpert()
    
    @pytest.mark.asyncio
    async def test_optimize_retrieval_basic(self):
        """测试基础检索优化"""
        query = "人工智能的发展历史"
        retrieval_results = [
            {
                "title": "人工智能简史",
                "content": "人工智能起源于20世纪50年代...",
                "relevance": 0.8
            },
            {
                "title": "机器学习发展",
                "content": "机器学习是人工智能的重要分支...",
                "relevance": 0.6
            }
        ]
        
        result = await self.expert.optimize_retrieval(
            query=query,
            retrieval_results=retrieval_results
        )
        
        assert isinstance(result, ExpertAnalysis)
        assert result.domain.value == "retrieval"
        assert result.confidence > 0.5
        assert len(result.insights) > 0
    
    @pytest.mark.asyncio
    async def test_optimize_query(self):
        """测试查询优化"""
        query = "如何学习人工智能技术"
        
        result = await self.expert.optimize_query(query)
        
        assert isinstance(result, dict)
        assert "optimized_query" in result
        assert "query_analysis" in result
        assert "optimization_suggestions" in result
        assert len(result["optimization_suggestions"]) > 0


class TestGraphExpert:
    """图谱专家测试类"""
    
    def setup_method(self):
        """测试前初始化"""
        self.expert = GraphExpert()
    
    @pytest.mark.asyncio
    async def test_analyze_knowledge_graph(self):
        """测试知识图谱分析"""
        entities = [
            {"id": "e1", "type": "概念", "name": "人工智能"},
            {"id": "e2", "type": "概念", "name": "机器学习"},
            {"id": "e3", "type": "技术", "name": "深度学习"}
        ]
        
        relationships = [
            {"id": "r1", "type": "包含", "source": "e1", "target": "e2"},
            {"id": "r2", "type": "包含", "source": "e1", "target": "e3"}
        ]
        
        result = await self.expert.analyze_knowledge_graph(
            entities=entities,
            relationships=relationships
        )
        
        assert isinstance(result, ExpertAnalysis)
        assert result.domain.value == "graph"
        assert result.confidence > 0.5
        assert len(result.insights) > 0
        assert "entity_count" in result.metadata
        assert result.metadata["entity_count"] == 3
    
    @pytest.mark.asyncio
    async def test_suggest_graph_enhancement(self):
        """测试图谱增强建议"""
        entities = [
            {"id": "e1", "type": "概念", "name": "人工智能"},
            {"id": "e2", "type": "概念", "name": "机器学习"}
        ]
        
        relations = [
            {"id": "r1", "type": "包含", "source": "e1", "target": "e2"}
        ]
        
        result = await self.expert.suggest_graph_enhancement(
            entities=entities,
            relations=relations
        )
        
        assert isinstance(result, dict)
        assert "suggestions" in result
        assert "recommendations" in result


class TestExpertCollaboration:
    """专家协作测试类"""
    
    def setup_method(self):
        """测试前初始化"""
        self.collaboration = ExpertCollaboration()
        
        # 注册测试专家
        self.knowledge_expert = KnowledgeExpert()
        self.retrieval_expert = RetrievalExpert()
        
        self.collaboration.register_expert("knowledge_expert", self.knowledge_expert)
        self.collaboration.register_expert("retrieval_expert", self.retrieval_expert)
    
    @pytest.mark.asyncio
    async def test_collaborative_analysis(self):
        """测试协作分析"""
        data = {
            "content": "人工智能技术包括机器学习和深度学习",
            "query": "人工智能技术"
        }
        
        result = await self.collaboration.collaborative_analysis(
            expert_ids=["knowledge_expert", "retrieval_expert"],
            data=data
        )
        
        assert isinstance(result, dict)
        assert "individual_results" in result
        assert "combined_insights" in result
        assert "combined_recommendations" in result
        assert len(result["individual_results"]) >= 1
    
    def test_get_collaboration_stats(self):
        """测试协作统计"""
        stats = self.collaboration.get_collaboration_stats()
        
        assert isinstance(stats, dict)
        assert "total_collaborations" in stats
        assert "registered_experts" in stats
        assert stats["registered_experts"] == 2


class TestPerformance:
    """性能测试类"""
    
    def setup_method(self):
        """测试前初始化"""
        self.expert = KnowledgeExpert()
    
    @pytest.mark.asyncio
    async def test_analysis_performance(self):
        """测试分析性能（2秒SLO要求）"""
        knowledge_items = [
            {
                "content": "人工智能是计算机科学的一个分支。" * 10,
                "title": "人工智能概述",
                "category": "technology"
            }
        ]
        
        start_time = asyncio.get_event_loop().time()
        
        result = await self.expert.analyze_knowledge(
            knowledge_items=knowledge_items
        )
        
        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time
        
        assert execution_time < 2.0, f"分析耗时 {execution_time:.3f} 秒，超过2秒SLO要求"
        assert isinstance(result, ExpertAnalysis)


@pytest.mark.asyncio
async def test_integration_workflow():
    """集成工作流测试"""
    # 创建专家实例
    knowledge_expert = KnowledgeExpert()
    retrieval_expert = RetrievalExpert()
    graph_expert = GraphExpert()
    
    # 创建协作管理器
    collaboration = ExpertCollaboration()
    collaboration.register_expert("knowledge", knowledge_expert)
    collaboration.register_expert("retrieval", retrieval_expert)
    collaboration.register_expert("graph", graph_expert)
    
    # 测试数据
    test_data = {
        "knowledge_content": [{"content": "人工智能技术发展迅速", "title": "AI发展", "category": "technology"}],
        "query": "人工智能",
        "retrieval_results": [
            {"title": "AI发展", "content": "人工智能技术发展迅速", "relevance": 0.8}
        ],
        "entities": [{"id": "e1", "type": "概念", "name": "人工智能"}],
        "relationships": []
    }
    
    # 执行协作分析
    result = await collaboration.collaborative_analysis(
        expert_ids=["knowledge", "retrieval", "graph"],
        data=test_data
    )
    
    # 验证结果
    assert isinstance(result, dict)
    assert "individual_results" in result
    assert "combined_insights" in result
    assert len(result["individual_results"]) >= 1  # 至少有1个专家成功分析
    
    # 验证协作统计
    stats = collaboration.get_collaboration_stats()
    assert stats["total_collaborations"] == 1
    assert stats["registered_experts"] == 3


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])