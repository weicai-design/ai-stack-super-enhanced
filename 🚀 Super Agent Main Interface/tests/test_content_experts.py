"""
内容创作专家模块集成测试
测试内容策划、生成、去AI化、发布、运营、版权专家及协作功能
"""

import pytest
import asyncio
import time
from typing import Dict, Any

from core.experts import (
    ContentPlanningExpert, ContentGenerationExpert, ContentDeAIExpert,
    ContentPublishExpert, ContentOperationExpert, ContentCopyrightExpert,
    ContentDataConnector, ContentExpertCollaboration, ContentAnalysis,
    get_content_experts
)


class TestContentDataConnector:
    """测试内容数据连接器"""
    
    def test_connector_initialization(self):
        """测试连接器初始化"""
        connector = ContentDataConnector()
        assert connector is not None
        assert hasattr(connector, 'platforms')
        assert isinstance(connector.platforms, list)
    
    def test_connection_status(self):
        """测试连接状态"""
        connector = ContentDataConnector()
        status = connector.get_connection_status()
        assert isinstance(status, dict)
        assert 'total_platforms' in status
        assert 'connected_platforms' in status
        assert 'connections' in status
        # 验证平台数量
        assert status['total_platforms'] == 5
        assert status['connected_platforms'] == 0
        assert isinstance(status['connections'], dict)
    
    @pytest.mark.asyncio
    async def test_data_retrieval(self):
        """测试数据获取"""
        connector = ContentDataConnector()
        # 首先连接平台
        await connector.connect_to_platform("wechat", {"api_key": "test"})
        # 然后获取数据
        data = await connector.fetch_content_data("wechat", {"start_date": "2024-01-01", "end_date": "2024-01-31"})
        assert isinstance(data, dict)
        assert 'platform' in data
        assert 'content_count' in data
        assert 'engagement_rate' in data


class TestContentPlanningExpert:
    """测试内容策划专家"""
    
    @pytest.fixture
    def expert(self):
        return ContentPlanningExpert()
    
    @pytest.mark.asyncio
    async def test_planning_analysis(self, expert):
        """测试内容策划分析"""
        planning_data = {
            "topics": ["人工智能", "机器学习"],
            "target_audience": {"description": "技术爱好者", "size": 10000},
            "publish_plan": {"frequency": 3, "platforms": ["wechat", "weibo"]}
        }
        
        result = await expert.analyze_planning(planning_data)
        
        assert result.score >= 0
        assert result.score <= 100
        assert result.confidence >= 0
        assert result.confidence <= 1
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.metadata, dict)


class TestContentGenerationExpert:
    """测试内容生成专家"""
    
    @pytest.fixture
    def expert(self):
        connector = ContentDataConnector()
        return ContentGenerationExpert(connector)
    
    @pytest.mark.asyncio
    async def test_generation_analysis(self, expert):
        """测试内容生成分析"""
        generation_data = {
            "content": "这是一篇关于人工智能的专业文章",
            "has_title": True,
            "has_intro": True,
            "has_conclusion": True,
            "multimodal": {"images": ["cover.jpg"], "coordination": 0.8}
        }
        
        result = await expert.analyze_generation(generation_data)
        
        assert result.score >= 0
        assert result.score <= 100
        assert result.confidence >= 0
        assert result.confidence <= 1
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_multimodal_generation(self, expert):
        """测试多模态内容生成"""
        content = "人工智能技术发展趋势"
        
        result = await expert.generate_multimodal_content(content)
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'content' in result
        assert isinstance(result['content'], dict)
        assert 'text' in result['content']
        assert 'images' in result['content']
    
    def test_generation_dashboard(self, expert):
        """测试生成仪表板"""
        dashboard = expert.get_generation_dashboard()
        assert isinstance(dashboard, dict)
        assert 'total_generations' in dashboard
        assert 'average_score' in dashboard


class TestContentDeAIExpert:
    """测试去AI化专家"""
    
    @pytest.fixture
    def expert(self):
        connector = ContentDataConnector()
        return ContentDeAIExpert(connector)
    
    @pytest.mark.asyncio
    async def test_deai_analysis(self, expert):
        """测试去AI化分析"""
        deai_data = {
            "ai_detection_rate": 2.5,
            "naturalness": 0.85,
            "originality": 92.0
        }
        
        result = await expert.analyze_deai(deai_data)
        
        assert result.score >= 0
        assert result.score <= 100
        assert result.confidence >= 0
        assert result.confidence <= 1
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_naturalness_enhancement(self, expert):
        """测试自然度增强"""
        result = await expert.enhance_naturalness("测试内容", "medium")
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'enhanced_content' in result
        assert 'techniques_applied' in result
    
    def test_detection_dashboard(self, expert):
        """测试检测仪表板"""
        dashboard = expert.get_detection_dashboard()
        assert isinstance(dashboard, dict)
        assert 'total_detections' in dashboard
        assert 'average_detection_rate' in dashboard


class TestContentPublishExpert:
    """测试内容发布专家"""
    
    @pytest.fixture
    def expert(self):
        return ContentPublishExpert()
    
    @pytest.mark.asyncio
    async def test_publish_analysis(self, expert):
        """测试发布分析"""
        publish_data = {
            "platforms": ["wechat", "douyin"],
            "publish_time": {"optimal_hours": [10, 14, 18]},
            "frequency": 3
        }
        
        result = await expert.analyze_publish(publish_data)
        
        assert isinstance(result, ContentAnalysis)
        assert result.score >= 0
        assert result.score <= 100
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestContentOperationExpert:
    """测试内容运营专家"""
    
    @pytest.fixture
    def expert(self):
        return ContentOperationExpert()
    
    @pytest.mark.asyncio
    async def test_operation_analysis(self, expert):
        """测试运营分析"""
        operation_data = {
            "read_data": {"total_reads": 10000, "avg_read_time": 120},
            "interaction_data": {"likes": 500, "comments": 100, "shares": 200},
            "conversion_data": {"conversion_rate": 0.05, "leads": 50}
        }
        
        result = await expert.analyze_operation(operation_data)
        
        assert result.score >= 0
        assert result.score <= 100
        assert result.confidence >= 0
        assert result.confidence <= 1
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestContentCopyrightExpert:
    """测试内容版权专家"""
    
    @pytest.fixture
    def expert(self):
        return ContentCopyrightExpert()
    
    @pytest.mark.asyncio
    async def test_copyright_analysis(self, expert):
        """测试版权分析"""
        copyright_data = {
            "originality_score": 95.0,
            "similarity_analysis": {"max_similarity": 0.15, "sources": []},
            "risk_assessment": {"risk_level": "低", "factors": []}
        }
        
        result = await expert.analyze_copyright(copyright_data)
        
        assert result.score >= 0
        assert result.score <= 100
        assert result.confidence >= 0
        assert result.confidence <= 1
        assert isinstance(result.insights, list)
        assert isinstance(result.recommendations, list)


class TestContentExpertCollaboration:
    """测试内容专家协作"""
    
    @pytest.fixture
    def collaboration(self):
        return ContentExpertCollaboration()
    
    @pytest.mark.asyncio
    async def test_collaborative_analysis(self, collaboration):
        """测试协作分析"""
        content_data = {
            "planning": {
                "topics": ["AI技术"],
                "target_audience": {"description": "开发者", "size": 5000},
                "publish_plan": {"frequency": 2, "platforms": ["wechat"]}
            },
            "generation": {
                "content": "AI技术发展趋势分析",
                "has_title": True,
                "has_intro": True,
                "has_conclusion": True
            },
            "deai": {
                "ai_detection_rate": 1.8,
                "naturalness": 0.92,
                "originality": 96.0
            }
        }
        
        result = await collaboration.collaborative_analysis(content_data)
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'overall_score' in result
        assert 'expert_results' in result
        assert 'expert_count' in result
    
    @pytest.mark.asyncio
    async def test_content_workflow(self, collaboration):
        """测试内容工作流"""
        result = await collaboration.generate_content_workflow(
            "人工智能",
            "技术爱好者",
            "text"
        )
        
        assert isinstance(result, dict)
        assert 'success' in result
        assert 'workflow_data' in result
        assert 'workflow_id' in result
    
    def test_collaboration_dashboard(self, collaboration):
        """测试协作仪表板"""
        dashboard = collaboration.get_collaboration_dashboard()
        
        assert isinstance(dashboard, dict)
        assert 'total_collaborations' in dashboard
        assert 'average_score' in dashboard
        assert 'success_rate' in dashboard
        assert 'average_expert_count' in dashboard
    
    def test_expert_list(self, collaboration):
        """测试专家列表"""
        experts = collaboration.get_expert_list()
        
        assert isinstance(experts, list)
        assert len(experts) == 6  # 6个内容专家
        
        for expert in experts:
            assert 'expert_id' in expert
            assert 'name' in expert
            assert 'stage' in expert
            assert 'capabilities' in expert


class TestContentExpertsIntegration:
    """测试内容专家集成功能"""
    
    def test_get_content_experts(self):
        """测试获取所有内容专家"""
        experts = get_content_experts()
        
        assert isinstance(experts, dict)
        assert len(experts) == 6
        
        expected_experts = [
            "planning_expert", "generation_expert", "deai_expert",
            "publish_expert", "operation_expert", "copyright_expert"
        ]
        
        for expert_name in expected_experts:
            assert expert_name in experts
    
    @pytest.mark.asyncio
    async def test_performance_benchmark(self):
        """测试性能基准"""
        # 测试单个专家分析性能
        start_time = time.time()
        
        expert = ContentPlanningExpert()
        planning_data = {
            "topics": ["测试主题"],
            "target_audience": {"description": "测试受众", "size": 1000},
            "publish_plan": {"frequency": 1, "platforms": ["test"]}
        }
        
        result = await expert.analyze_planning(planning_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 2.0  # 2秒SLO要求
        assert result.score >= 0
    
    @pytest.mark.asyncio
    async def test_concurrent_analysis(self):
        """测试并发分析"""
        experts = get_content_experts()
        
        # 创建多个分析任务
        tasks = []
        
        # 策划专家分析
        planning_data = {
            "topics": ["并发测试"],
            "target_audience": {"description": "测试用户", "size": 1000},
            "publish_plan": {"frequency": 1, "platforms": ["test"]}
        }
        tasks.append(experts["planning_expert"].analyze_planning(planning_data))
        
        # 生成专家分析
        generation_data = {
            "content": "并发测试内容",
            "has_title": True,
            "has_intro": True,
            "has_conclusion": True
        }
        tasks.append(experts["generation_expert"].analyze_generation(generation_data))
        
        # 去AI化专家分析
        deai_data = {
            "ai_detection_rate": 1.0,
            "naturalness": 0.95,
            "originality": 98.0
        }
        tasks.append(experts["deai_expert"].analyze_deai(deai_data))
        
        # 并行执行
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 3.0  # 并发执行应在3秒内完成
        assert len(results) == 3
        
        for result in results:
            assert result.score >= 0
            assert result.score <= 100


if __name__ == "__main__":
    # 运行性能测试
    import asyncio
    
    async def run_performance_tests():
        """运行性能测试"""
        test_instance = TestContentExpertsIntegration()
        
        print("运行单个专家性能测试...")
        await test_instance.test_performance_benchmark()
        
        print("运行并发分析测试...")
        await test_instance.test_concurrent_analysis()
        
        print("所有性能测试通过!")
    
    asyncio.run(run_performance_tests())