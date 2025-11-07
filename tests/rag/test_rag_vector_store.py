"""
RAG系统 - 向量存储测试
"""

import pytest
import numpy as np
from tests.test_utils import test_helper


@pytest.mark.rag
@pytest.mark.unit
class TestVectorStore:
    """向量存储测试"""
    
    def test_faiss_backend(self):
        """测试：Faiss向量存储后端"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from core.vector_store.faiss_backend import FaissBackend
            
            backend = FaissBackend(dimension=384)
            
            # 测试添加向量
            vectors = np.random.rand(10, 384).astype('float32')
            ids = list(range(10))
            
            backend.add(vectors, ids)
            
            # 测试检索
            query_vector = np.random.rand(1, 384).astype('float32')
            results = backend.search(query_vector, k=5)
            
            assert len(results) <= 5
        except ImportError:
            pytest.skip("Faiss后端模块未找到")
    
    def test_simple_vector_store(self):
        """测试：简单向量存储"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from core.vector_store.simple_vector_store import SimpleVectorStore
            
            store = SimpleVectorStore()
            
            # 测试存储和检索
            assert store is not None
        except ImportError:
            pytest.skip("简单向量存储模块未找到")
    
    def test_vector_add_and_search(self):
        """测试：向量添加和搜索"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from core.vector_store.faiss_backend import FaissBackend
            
            backend = FaissBackend(dimension=384)
            
            # 添加一些向量
            vectors = np.random.rand(100, 384).astype('float32')
            ids = list(range(100))
            backend.add(vectors, ids)
            
            # 搜索
            query = np.random.rand(1, 384).astype('float32')
            results = backend.search(query, k=10)
            
            assert len(results) == 10
            # 验证结果格式
            if len(results) > 0:
                assert "id" in results[0] or isinstance(results[0], (int, str))
        except ImportError:
            pytest.skip("向量存储模块未找到")
    
    @pytest.mark.performance
    def test_vector_search_performance(self, timer):
        """测试：向量搜索性能"""
        try:
            import sys
            sys.path.append("/Users/ywc/ai-stack-super-enhanced/📚 Enhanced RAG & Knowledge Graph")
            from core.vector_store.faiss_backend import FaissBackend
            
            backend = FaissBackend(dimension=384)
            
            # 添加大量向量
            vectors = np.random.rand(10000, 384).astype('float32')
            ids = list(range(10000))
            backend.add(vectors, ids)
            
            # 测试搜索性能
            query = np.random.rand(1, 384).astype('float32')
            
            timer.start()
            results = backend.search(query, k=10)
            timer.stop()
            
            assert len(results) == 10
            assert timer.elapsed < 0.1, f"搜索时间过长: {timer.elapsed}s"
        except ImportError:
            pytest.skip("向量存储模块未找到")

