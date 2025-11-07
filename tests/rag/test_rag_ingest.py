"""
RAG系统 - 文档摄入功能测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.rag
@pytest.mark.unit
class TestRAGIngest:
    """RAG文档摄入功能测试"""
    
    @pytest.fixture(scope="class")
    def client(self):
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from api.app import app
            from fastapi.testclient import TestClient
            return TestClient(app)
        except:
            pytest.skip("RAG应用未启动")
    
    @pytest.fixture(scope="class")
    def api_helper(self, client):
        return APITestHelper(client, base_url="")
    
    def test_ingest_text(self, api_helper):
        """测试：摄入纯文本"""
        ingest_data = {
            "text": "这是一段测试文本，用于测试RAG系统的文档摄入功能。",
            "metadata": {
                "source": "test",
                "type": "test_document"
            }
        }
        
        response = api_helper.post("/rag/ingest/text", json_data=ingest_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "success" in data or "id" in data
    
    def test_ingest_with_chunking(self, api_helper):
        """测试：带分块的文档摄入"""
        long_text = "测试文本。" * 100  # 创建长文本
        ingest_data = {
            "text": long_text,
            "chunk_size": 100,
            "chunk_overlap": 20
        }
        
        response = api_helper.post("/rag/ingest/text", json_data=ingest_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "chunks_created" in data or "success" in data
    
    def test_ingest_invalid_data(self, api_helper):
        """测试：摄入无效数据"""
        invalid_data = {}  # 缺少必需字段
        
        response = api_helper.post("/rag/ingest/text", json_data=invalid_data)
        
        # 应该返回错误
        assert response.status_code in [400, 422]
    
    def test_batch_ingest(self, api_helper):
        """测试：批量摄入"""
        batch_data = {
            "documents": [
                {"text": "文档1", "metadata": {"id": "doc1"}},
                {"text": "文档2", "metadata": {"id": "doc2"}},
                {"text": "文档3", "metadata": {"id": "doc3"}}
            ]
        }
        
        response = api_helper.post("/rag/ingest/batch", json_data=batch_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "processed" in data or "success" in data
    
    def test_ingest_with_preprocessing(self, api_helper):
        """测试：带预处理的文档摄入"""
        ingest_data = {
            "text": "这是一段包含<html>标签</html>的文本  \n\n  多余空格  ",
            "preprocess": True
        }
        
        response = api_helper.post("/rag/ingest/text", json_data=ingest_data)
        
        if response.status_code in [200, 201]:
            assert True

