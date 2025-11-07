"""
检索器 - 知识检索功能

实现多种检索策略：
1. 向量检索（语义检索）
2. 关键词检索（BM25）
3. 混合检索
4. 重排序
"""

from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Retriever:
    """
    检索器
    
    负责：
    1. 向量检索
    2. 关键词检索  
    3. 混合检索
    4. 结果重排序
    """
    
    def __init__(self, vector_store=None, config: Optional[Dict] = None):
        """初始化检索器"""
        self.vector_store = vector_store
        self.config = config or self._get_default_config()
        
        logger.info("🔍 检索器初始化完成")
        logger.info(f"   检索模式: {self.config['retrieval_mode']}")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "retrieval_mode": "hybrid",  # vector, keyword, hybrid
            "top_k": 5,
            "similarity_threshold": 0.7,
            "enable_rerank": True,
            "rerank_top_k": 10,
            "keyword_weight": 0.3,  # 混合检索时关键词权重
            "vector_weight": 0.7    # 混合检索时向量权重
        }
    
    def retrieve(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        top_k: Optional[int] = None,
        mode: Optional[str] = None,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            query_embedding: 查询向量
            top_k: 返回结果数量
            mode: 检索模式 (vector, keyword, hybrid)
            filters: 过滤条件
            
        Returns:
            检索结果
        """
        top_k = top_k or self.config["top_k"]
        mode = mode or self.config["retrieval_mode"]
        
        logger.info(f"\n🔍 开始检索")
        logger.info(f"   查询: {query[:50]}...")
        logger.info(f"   模式: {mode}")
        logger.info(f"   返回: top-{top_k}")
        
        # 根据模式选择检索方法
        if mode == "vector":
            results = self._vector_retrieve(query_embedding, top_k, filters)
        elif mode == "keyword":
            results = self._keyword_retrieve(query, top_k, filters)
        elif mode == "hybrid":
            results = self._hybrid_retrieve(query, query_embedding, top_k, filters)
        else:
            logger.warning(f"⚠️  未知检索模式: {mode}，使用向量检索")
            results = self._vector_retrieve(query_embedding, top_k, filters)
        
        # 重排序（如果启用）
        if self.config["enable_rerank"] and len(results) > 0:
            results = self._rerank(query, results)
        
        # 过滤低分结果
        threshold = self.config["similarity_threshold"]
        results = [r for r in results if r.get("score", 0) >= threshold]
        
        logger.info(f"✅ 检索完成: 找到{len(results)}个结果")
        
        return {
            "success": True,
            "query": query,
            "mode": mode,
            "results": results[:top_k],
            "total_results": len(results)
        }
    
    def _vector_retrieve(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """向量检索"""
        logger.info("   执行向量检索...")
        
        if not self.vector_store:
            logger.warning("   ⚠️  未配置向量存储，返回空结果")
            return []
        
        if not query_embedding:
            logger.warning("   ⚠️  未提供查询向量，返回空结果")
            return []
        
        # 查询向量库
        query_result = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k * 2,  # 多取一些，用于后续重排序
            where=filters
        )
        
        if not query_result.get("success"):
            return []
        
        return query_result.get("results", [])
    
    def _keyword_retrieve(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """关键词检索（BM25）"""
        logger.info("   执行关键词检索...")
        
        # TODO: 实现BM25检索
        # 需要：
        # 1. 分词
        # 2. 计算TF-IDF
        # 3. BM25评分
        
        logger.warning("   ⚠️  关键词检索功能待实现")
        return []
    
    def _hybrid_retrieve(
        self,
        query: str,
        query_embedding: Optional[List[float]],
        top_k: int,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """混合检索"""
        logger.info("   执行混合检索...")
        
        # 1. 向量检索
        vector_results = self._vector_retrieve(query_embedding, top_k * 2, filters)
        
        # 2. 关键词检索
        keyword_results = self._keyword_retrieve(query, top_k * 2, filters)
        
        # 3. 合并结果
        if not keyword_results:
            # 如果关键词检索没有结果，只用向量检索
            return vector_results
        
        # 融合两种检索结果（简单实现：加权平均）
        vector_weight = self.config["vector_weight"]
        keyword_weight = self.config["keyword_weight"]
        
        # 构建文档ID到分数的映射
        scores = {}
        
        # 向量检索分数
        for result in vector_results:
            doc_id = result["id"]
            scores[doc_id] = {
                "vector_score": result.get("score", 0),
                "keyword_score": 0,
                "result": result
            }
        
        # 关键词检索分数
        for result in keyword_results:
            doc_id = result["id"]
            if doc_id in scores:
                scores[doc_id]["keyword_score"] = result.get("score", 0)
            else:
                scores[doc_id] = {
                    "vector_score": 0,
                    "keyword_score": result.get("score", 0),
                    "result": result
                }
        
        # 计算综合分数
        hybrid_results = []
        for doc_id, score_data in scores.items():
            final_score = (
                score_data["vector_score"] * vector_weight +
                score_data["keyword_score"] * keyword_weight
            )
            
            result = score_data["result"].copy()
            result["score"] = final_score
            result["vector_score"] = score_data["vector_score"]
            result["keyword_score"] = score_data["keyword_score"]
            hybrid_results.append(result)
        
        # 按综合分数排序
        hybrid_results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"   混合了{len(vector_results)}个向量结果和{len(keyword_results)}个关键词结果")
        
        return hybrid_results
    
    def _rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        重排序
        
        使用更精确的方法重新排序结果
        """
        logger.info("   执行结果重排序...")
        
        # TODO: 实现重排序
        # 可以使用：
        # 1. 交叉编码器（Cross-encoder）
        # 2. 基于规则的重排序
        # 3. 多因素综合评分
        
        # 简单实现：基于查询长度和文档长度的调整
        for result in results:
            doc_text = result.get("document", "")
            
            # 考虑文档长度（不要太短也不要太长）
            ideal_length = 500
            length_score = 1 - abs(len(doc_text) - ideal_length) / ideal_length
            length_score = max(0, min(1, length_score))
            
            # 调整分数
            original_score = result.get("score", 0)
            result["score"] = original_score * 0.8 + length_score * 0.2
            result["reranked"] = True
        
        # 重新排序
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return results
    
    def get_context(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        max_length: int = 2000
    ) -> str:
        """
        获取检索上下文（用于RAG）
        
        Args:
            query: 查询文本
            query_embedding: 查询向量
            max_length: 最大上下文长度
            
        Returns:
            组合的上下文文本
        """
        # 检索相关文档
        retrieval_result = self.retrieve(
            query=query,
            query_embedding=query_embedding
        )
        
        if not retrieval_result.get("success"):
            return ""
        
        # 组合上下文
        context_parts = []
        current_length = 0
        
        for result in retrieval_result.get("results", []):
            doc_text = result.get("document", "")
            
            if current_length + len(doc_text) > max_length:
                # 截断
                remaining = max_length - current_length
                if remaining > 100:  # 至少保留100字符
                    context_parts.append(doc_text[:remaining])
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        context = "\n\n".join(context_parts)
        
        logger.info(f"   生成上下文: {len(context)}字符")
        
        return context


def test_retriever():
    """测试检索器"""
    print("="*70)
    print("  检索器测试")
    print("="*70)
    
    # 模拟向量存储
    class MockVectorStore:
        def query(self, query_embedding, n_results, where=None):
            # 返回模拟结果
            return {
                "success": True,
                "results": [
                    {
                        "id": "doc_1",
                        "document": "人工智能是计算机科学的一个分支，致力于创建智能机器。",
                        "metadata": {"topic": "AI"},
                        "score": 0.95
                    },
                    {
                        "id": "doc_2",
                        "document": "机器学习是人工智能的子集，专注于让机器从数据中学习。",
                        "metadata": {"topic": "ML"},
                        "score": 0.88
                    },
                    {
                        "id": "doc_3",
                        "document": "深度学习使用多层神经网络进行学习。",
                        "metadata": {"topic": "DL"},
                        "score": 0.82
                    }
                ]
            }
    
    # 创建模拟向量
    def create_mock_embedding():
        import random
        return [random.random() for _ in range(384)]
    
    # 初始化检索器
    mock_store = MockVectorStore()
    retriever = Retriever(vector_store=mock_store)
    
    # 测试向量检索
    print("\n1. 测试向量检索:")
    query_embedding = create_mock_embedding()
    
    result = retriever.retrieve(
        query="什么是人工智能？",
        query_embedding=query_embedding,
        mode="vector",
        top_k=3
    )
    
    print(f"   检索成功: {result['success']}")
    print(f"   找到结果: {result['total_results']}个")
    
    for i, res in enumerate(result['results'], 1):
        print(f"\n   结果{i}:")
        print(f"     文档: {res['document']}")
        print(f"     分数: {res['score']:.3f}")
    
    # 测试获取上下文
    print("\n2. 测试获取上下文:")
    context = retriever.get_context(
        query="什么是机器学习？",
        query_embedding=query_embedding,
        max_length=500
    )
    
    print(f"   上下文长度: {len(context)}字符")
    print(f"   上下文预览: {context[:100]}...")
    
    print("\n✅ 检索器测试完成！")


if __name__ == "__main__":
    test_retriever()



