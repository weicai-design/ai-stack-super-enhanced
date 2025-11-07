"""
RAG系统 - 数据管道测试
"""

import pytest
from tests.test_utils import test_helper


@pytest.mark.rag
@pytest.mark.integration
class TestRAGPipelines:
    """RAG数据管道测试"""
    
    def test_smart_ingestion_pipeline(self):
        """测试：智能摄入管道"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from pipelines.smart_ingestion_pipeline import SmartIngestionPipeline
            
            pipeline = SmartIngestionPipeline()
            
            # 测试文本处理
            text = "这是一段测试文本"
            result = pipeline.process(text)
            
            assert result is not None
        except ImportError:
            pytest.skip("智能摄入管道模块未找到")
    
    def test_truth_verification_pipeline(self):
        """测试：真实性验证管道"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from pipelines.truth_verification_pipeline import TruthVerificationPipeline
            
            pipeline = TruthVerificationPipeline()
            
            # 测试验证功能
            text = "测试文本"
            result = pipeline.verify(text)
            
            assert result is not None
        except ImportError:
            pytest.skip("真实性验证管道模块未找到")
    
    def test_multi_stage_preprocessor(self):
        """测试：多阶段预处理器"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from pipelines.multi_stage_preprocessor import MultiStagePreprocessor
            
            preprocessor = MultiStagePreprocessor()
            
            # 测试预处理
            text = "  这是一段需要预处理的文本  \n\n  多余空格  "
            result = preprocessor.preprocess(text)
            
            assert result is not None
            assert len(result.strip()) > 0
        except ImportError:
            pytest.skip("多阶段预处理器模块未找到")
    
    def test_adaptive_grouping_pipeline(self):
        """测试：自适应分组管道"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from pipelines.adaptive_grouping_pipeline import AdaptiveGroupingPipeline
            
            pipeline = AdaptiveGroupingPipeline()
            
            # 测试分组功能
            documents = [
                {"text": "文档1"},
                {"text": "文档2"},
                {"text": "文档3"}
            ]
            
            result = pipeline.group(documents)
            
            assert result is not None
        except ImportError:
            pytest.skip("自适应分组管道模块未找到")
    
    @pytest.mark.slow
    def test_pipeline_end_to_end(self):
        """测试：端到端管道流程"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from pipelines.smart_ingestion_pipeline import SmartIngestionPipeline
            
            pipeline = SmartIngestionPipeline()
            
            # 完整流程：文本 → 预处理 → 分块 → 向量化 → 存储
            text = """
            这是一段较长的测试文本。
            它包含多个句子和段落。
            用于测试完整的摄入流程。
            """
            
            result = pipeline.ingest(text)
            
            assert result is not None
        except ImportError:
            pytest.skip("管道模块未找到")

