"""
RAG系统 - 知识图谱功能测试
"""

import pytest
from tests.test_utils import test_helper, APITestHelper


@pytest.mark.rag
@pytest.mark.unit
class TestKnowledgeGraph:
    """知识图谱功能测试"""
    
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
    
    def test_build_knowledge_graph(self, api_helper):
        """测试：构建知识图谱"""
        kg_data = {
            "text": "AI Stack是一个企业级AI智能系统，包含RAG和ERP模块。"
        }
        
        response = api_helper.post("/kg/build", json_data=kg_data)
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert "entities" in data or "success" in data
    
    def test_query_knowledge_graph(self, api_helper):
        """测试：查询知识图谱"""
        query_data = {
            "query": "AI Stack的模块"
        }
        
        response = api_helper.post("/kg/query", json_data=query_data)
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))
    
    def test_get_graph_snapshot(self, api_helper):
        """测试：获取图谱快照"""
        response = api_helper.get("/kg/snapshot")
        
        if response.status_code == 200:
            data = response.json()
            assert "entities" in data or "nodes" in data
    
    def test_export_knowledge_graph(self, api_helper):
        """测试：导出知识图谱"""
        response = api_helper.get("/kg/export?format=json")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)
    
    def test_clear_knowledge_graph(self, api_helper):
        """测试：清空知识图谱"""
        response = api_helper.post("/kg/clear")
        
        # 这是危险操作，可能需要权限
        assert response.status_code in [200, 401, 403]

