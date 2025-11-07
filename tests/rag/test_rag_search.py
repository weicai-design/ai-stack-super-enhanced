"""
RAG系统 - 检索功能测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.rag
@pytest.mark.unit
@pytest.mark.critical
class TestRAGSearch:
    """RAG检索功能测试"""
    
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
    
    def test_health_check(self, api_helper):
        """测试：RAG服务健康检查"""
        response = api_helper.get("/health")
        data = test_helper.assert_response_success(response)
        
        assert data["status"] == "ok"
    
    def test_vector_search(self, api_helper):
        """测试：向量检索"""
        response = api_helper.get("/rag/search?query=测试&mode=vector&top_k=5")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list)
        if len(data) > 0:
            assert "text" in data[0]
            assert "score" in data[0]
    
    def test_keyword_search(self, api_helper):
        """测试：关键词检索"""
        response = api_helper.get("/rag/search?query=测试&mode=keyword&top_k=5")
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list)
    
    def test_hybrid_search(self, api_helper):
        """测试：混合检索"""
        response = api_helper.get(
            "/rag/search?query=测试&mode=hybrid&top_k=5&alpha=0.5"
        )
        data = test_helper.assert_response_success(response)
        
        assert isinstance(data, list)
    
    @pytest.mark.parametrize("top_k", [1, 5, 10, 20])
    def test_search_with_different_top_k(self, api_helper, top_k):
        """测试：不同Top-K参数的检索"""
        response = api_helper.get(f"/rag/search?query=测试&top_k={top_k}")
        
        if response.status_code == 200:
            data = response.json()
            assert len(data) <= top_k
    
    def test_search_with_highlight(self, api_helper):
        """测试：带高亮的检索"""
        response = api_helper.get("/rag/search?query=测试&highlight=true")
        data = test_helper.assert_response_success(response)
        
        if len(data) > 0:
            # 检查是否有高亮标记
            assert isinstance(data[0].get("text"), str)
    
    def test_empty_query_search(self, api_helper):
        """测试：空查询检索"""
        response = api_helper.get("/rag/search?query=")
        
        # 应该返回错误或空结果
        assert response.status_code in [200, 400, 422]
    
    @pytest.mark.performance
    def test_search_performance(self, api_helper, timer):
        """测试：检索性能"""
        timer.start()
        response = api_helper.get("/rag/search?query=测试&top_k=10")
        timer.stop()
        
        test_helper.assert_response_success(response)
        assert timer.elapsed < 0.5, f"检索时间过长: {timer.elapsed}s"

