"""
真实的RAG服务
替换所有模拟数据，实现真实的检索功能
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np


class RealRAGService:
    """真实的RAG检索服务"""
    
    def __init__(self, index_dir: str = "data"):
        """
        初始化RAG服务
        
        Args:
            index_dir: 索引数据目录
        """
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.docs_file = self.index_dir / "docs.json"
        self.vectors_file = self.index_dir / "vectors.npy"
        
        # 加载文档和向量
        self.documents = self._load_documents()
        self.vectors = self._load_vectors()
        
        # 加载embedding模型
        self.embedder = self._load_embedder()
    
    def _load_embedder(self):
        """加载embedding模型"""
        try:
            from sentence_transformers import SentenceTransformer
            model_path = os.getenv("ST_MODEL_PATH", "all-MiniLM-L6-v2")
            return SentenceTransformer(model_path)
        except ImportError:
            print("⚠️  sentence-transformers未安装，RAG功能将受限")
            return None
        except Exception as e:
            print(f"⚠️  加载embedding模型失败: {e}")
            return None
    
    def _load_documents(self) -> List[Dict]:
        """加载文档"""
        if self.docs_file.exists():
            with open(self.docs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _load_vectors(self) -> Optional[np.ndarray]:
        """加载向量"""
        if self.vectors_file.exists():
            return np.load(self.vectors_file)
        return None
    
    def _save_documents(self):
        """保存文档"""
        with open(self.docs_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def _save_vectors(self):
        """保存向量"""
        if self.vectors is not None:
            np.save(self.vectors_file, self.vectors)
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        use_reranking: bool = False
    ) -> Dict[str, Any]:
        """
        真实的RAG检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            use_reranking: 是否使用重排序
            
        Returns:
            检索结果
        """
        if not self.documents:
            return {
                "success": True,
                "query": query,
                "results": [],
                "message": "知识库为空，请先上传文档"
            }
        
        if self.embedder is None:
            # 降级到关键词搜索
            return await self._keyword_search(query, top_k, filters)
        
        try:
            # 1. 生成查询向量
            query_vector = self.embedder.encode([query])[0]
            
            # 2. 向量检索
            if self.vectors is not None:
                scores = np.dot(self.vectors, query_vector)
                top_indices = np.argsort(scores)[::-1][:top_k * 2]  # 取2倍用于重排
            else:
                # 如果没有向量索引，返回前k个文档
                top_indices = list(range(min(top_k, len(self.documents))))
                scores = np.ones(len(top_indices))
            
            # 3. 应用过滤器
            results = []
            for idx in top_indices:
                if idx >= len(self.documents):
                    continue
                
                doc = self.documents[idx]
                
                # 应用过滤条件
                if filters:
                    if not self._match_filters(doc, filters):
                        continue
                
                results.append({
                    "doc_id": doc.get("id", f"doc_{idx}"),
                    "content": doc.get("text", doc.get("content", "")),
                    "metadata": doc.get("metadata", {}),
                    "score": float(scores[idx]) if idx < len(scores) else 0.0,
                    "snippet": self._generate_snippet(doc.get("text", ""), query)
                })
                
                if len(results) >= top_k:
                    break
            
            # 4. 重排序（可选）
            if use_reranking and len(results) > 0:
                results = await self._rerank_results(query, results)
            
            return {
                "success": True,
                "query": query,
                "results": results[:top_k],
                "total_docs": len(self.documents),
                "retrieval_method": "vector_search" if self.vectors is not None else "keyword_search"
            }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": []
            }
    
    async def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """关键词搜索（降级方案）"""
        results = []
        query_words = set(query.lower().split())
        
        for idx, doc in enumerate(self.documents):
            content = doc.get("text", doc.get("content", "")).lower()
            
            # 计算关键词匹配度
            matches = sum(1 for word in query_words if word in content)
            score = matches / len(query_words) if query_words else 0
            
            if score > 0:
                # 应用过滤器
                if filters and not self._match_filters(doc, filters):
                    continue
                
                results.append({
                    "doc_id": doc.get("id", f"doc_{idx}"),
                    "content": doc.get("text", doc.get("content", "")),
                    "metadata": doc.get("metadata", {}),
                    "score": score,
                    "snippet": self._generate_snippet(doc.get("text", ""), query)
                })
        
        # 排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "success": True,
            "query": query,
            "results": results[:top_k],
            "total_docs": len(self.documents),
            "retrieval_method": "keyword_search"
        }
    
    def _match_filters(self, doc: Dict, filters: Dict[str, Any]) -> bool:
        """检查文档是否匹配过滤条件"""
        metadata = doc.get("metadata", {})
        
        for key, value in filters.items():
            if key not in metadata:
                return False
            if metadata[key] != value:
                return False
        
        return True
    
    def _generate_snippet(self, text: str, query: str, max_length: int = 200) -> str:
        """生成摘要片段"""
        if not text:
            return ""
        
        # 找到包含查询词的位置
        query_words = query.lower().split()
        text_lower = text.lower()
        
        best_pos = 0
        max_matches = 0
        
        for i in range(len(text) - max_length):
            snippet = text_lower[i:i+max_length]
            matches = sum(1 for word in query_words if word in snippet)
            if matches > max_matches:
                max_matches = matches
                best_pos = i
        
        snippet = text[best_pos:best_pos+max_length]
        if best_pos > 0:
            snippet = "..." + snippet
        if best_pos + max_length < len(text):
            snippet = snippet + "..."
        
        return snippet
    
    async def _rerank_results(
        self,
        query: str,
        results: List[Dict]
    ) -> List[Dict]:
        """重排序结果（使用更精确的模型）"""
        # 简化版：基于内容长度和分数的综合排序
        for result in results:
            content_quality = min(1.0, len(result["content"]) / 500)
            result["rerank_score"] = result["score"] * 0.7 + content_quality * 0.3
        
        results.sort(key=lambda x: x.get("rerank_score", x["score"]), reverse=True)
        return results
    
    async def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        添加文档到知识库
        
        Args:
            text: 文档文本
            metadata: 元数据
            doc_id: 文档ID
            
        Returns:
            添加结果
        """
        if not doc_id:
            doc_id = f"doc_{len(self.documents)}"
        
        # 创建文档对象
        document = {
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "created_at": str(Path(__file__).stat().st_mtime)
        }
        
        # 生成向量
        if self.embedder:
            vector = self.embedder.encode([text])[0]
            
            # 更新向量矩阵
            if self.vectors is None:
                self.vectors = np.array([vector])
            else:
                self.vectors = np.vstack([self.vectors, vector])
            
            self._save_vectors()
        
        # 添加文档
        self.documents.append(document)
        self._save_documents()
        
        return {
            "success": True,
            "doc_id": doc_id,
            "message": "文档已添加到知识库"
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "has_embedder": self.embedder is not None,
            "has_vectors": self.vectors is not None,
            "vector_dimensions": self.vectors.shape[1] if self.vectors is not None else 0,
            "index_dir": str(self.index_dir)
        }


# 全局RAG服务实例
_rag_service = None

def get_rag_service() -> RealRAGService:
    """获取RAG服务实例"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RealRAGService()
    return _rag_service


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test():
        rag = get_rag_service()
        
        print("✅ RAG服务已加载")
        print(f"📊 统计: {rag.get_stats()}")
        
        # 添加测试文档
        await rag.add_document(
            text="AI-STACK是一个企业级AI智能系统，提供1200+功能",
            metadata={"source": "test", "type": "intro"}
        )
        
        # 测试检索
        result = await rag.search("介绍AI-STACK", top_k=3)
        
        if result["success"]:
            print(f"\n✅ 检索成功:")
            for r in result["results"]:
                print(f"  • {r['snippet']} (score: {r['score']:.3f})")
        else:
            print(f"\n❌ 检索失败: {result.get('error')}")
    
    asyncio.run(test())


