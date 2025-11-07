"""
Chroma向量存储 - 向量数据库集成

使用ChromaDB作为向量数据库，提供：
1. 向量存储
2. 向量检索
3. 元数据过滤
4. 批量操作
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaStore:
    """
    Chroma向量存储
    
    负责：
    1. 初始化ChromaDB客户端
    2. 存储向量和元数据
    3. 向量检索
    4. 集合管理
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """初始化Chroma存储"""
        self.config = config or self._get_default_config()
        self.client = None
        self.collection = None
        
        logger.info("🗄️  初始化Chroma向量存储...")
        self._initialize_client()
        logger.info("✅ Chroma向量存储初始化完成")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "persist_directory": "./data/chroma",
            "collection_name": "ai_stack_knowledge",
            "distance_function": "cosine",  # cosine, l2, ip
            "embedding_dimension": 384  # MiniLM模型维度
        }
    
    def _initialize_client(self):
        """初始化ChromaDB客户端"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # 创建持久化目录
            persist_dir = self.config["persist_directory"]
            os.makedirs(persist_dir, exist_ok=True)
            
            # 初始化客户端
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 获取或创建集合
            collection_name = self.config["collection_name"]
            distance_func = self.config["distance_function"]
            
            try:
                self.collection = self.client.get_collection(
                    name=collection_name
                )
                logger.info(f"   ✅ 加载已存在的集合: {collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=collection_name,
                    metadata={
                        "hnsw:space": distance_func,
                        "description": "AI-Stack知识库"
                    }
                )
                logger.info(f"   ✅ 创建新集合: {collection_name}")
            
        except ImportError:
            logger.error("❌ ChromaDB未安装，请运行: pip install chromadb")
            logger.info("   使用模拟模式运行...")
            self._use_mock_mode()
        except Exception as e:
            logger.error(f"❌ ChromaDB初始化失败: {e}")
            logger.info("   使用模拟模式运行...")
            self._use_mock_mode()
    
    def _use_mock_mode(self):
        """使用模拟模式"""
        self.client = None
        self.collection = None
        self._mock_storage = []  # 简单列表存储
        logger.warning("⚠️  运行在模拟模式，数据不会持久化")
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        添加文档到向量库
        
        Args:
            documents: 文档文本列表
            embeddings: 向量列表
            metadatas: 元数据列表
            ids: 文档ID列表
            
        Returns:
            添加结果
        """
        logger.info(f"\n📥 添加文档到向量库")
        logger.info(f"   数量: {len(documents)}")
        
        if not ids:
            # 自动生成ID
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            ids = [f"doc_{timestamp}_{i}" for i in range(len(documents))]
        
        if not metadatas:
            metadatas = [{} for _ in documents]
        
        # 添加时间戳
        for metadata in metadatas:
            metadata["added_at"] = datetime.now().isoformat()
        
        try:
            if self.collection:
                # 使用ChromaDB
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                
                result = {
                    "success": True,
                    "count": len(documents),
                    "ids": ids,
                    "storage": "chromadb"
                }
            else:
                # 模拟模式
                for i, doc in enumerate(documents):
                    self._mock_storage.append({
                        "id": ids[i],
                        "document": doc,
                        "embedding": embeddings[i],
                        "metadata": metadatas[i]
                    })
                
                result = {
                    "success": True,
                    "count": len(documents),
                    "ids": ids,
                    "storage": "mock",
                    "warning": "模拟模式，数据不会持久化"
                }
            
            logger.info(f"✅ 添加成功: {len(documents)}个文档")
            return result
            
        except Exception as e:
            logger.error(f"❌ 添加失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None,
        include_distances: bool = True
    ) -> Dict[str, Any]:
        """
        查询相似文档
        
        Args:
            query_embedding: 查询向量
            n_results: 返回结果数量
            where: 元数据过滤条件
            include_distances: 是否包含距离
            
        Returns:
            查询结果
        """
        logger.info(f"\n🔍 查询向量库")
        logger.info(f"   返回数量: {n_results}")
        
        try:
            if self.collection:
                # 使用ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results,
                    where=where,
                    include=["documents", "metadatas", "distances"]
                )
                
                # 格式化结果
                formatted_results = []
                for i in range(len(results["ids"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if include_distances else None,
                        "score": 1 - results["distances"][0][i]  # 转换为相似度分数
                    })
                
                result = {
                    "success": True,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "storage": "chromadb"
                }
                
            else:
                # 模拟模式 - 简单返回所有文档
                mock_results = []
                for item in self._mock_storage[:n_results]:
                    mock_results.append({
                        "id": item["id"],
                        "document": item["document"],
                        "metadata": item["metadata"],
                        "distance": 0.1,  # 模拟距离
                        "score": 0.9  # 模拟相似度
                    })
                
                result = {
                    "success": True,
                    "results": mock_results,
                    "count": len(mock_results),
                    "storage": "mock",
                    "warning": "模拟模式，返回的是随机结果"
                }
            
            logger.info(f"✅ 查询完成: 找到{result['count']}个结果")
            return result
            
        except Exception as e:
            logger.error(f"❌ 查询失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def delete(self, ids: List[str]) -> Dict[str, Any]:
        """
        删除文档
        
        Args:
            ids: 要删除的文档ID列表
            
        Returns:
            删除结果
        """
        logger.info(f"\n🗑️  删除文档: {len(ids)}个")
        
        try:
            if self.collection:
                self.collection.delete(ids=ids)
                result = {
                    "success": True,
                    "deleted_count": len(ids)
                }
            else:
                # 模拟模式
                self._mock_storage = [
                    item for item in self._mock_storage 
                    if item["id"] not in ids
                ]
                result = {
                    "success": True,
                    "deleted_count": len(ids),
                    "storage": "mock"
                }
            
            logger.info(f"✅ 删除成功")
            return result
            
        except Exception as e:
            logger.error(f"❌ 删除失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            if self.collection:
                count = self.collection.count()
                return {
                    "total_documents": count,
                    "collection_name": self.config["collection_name"],
                    "distance_function": self.config["distance_function"],
                    "storage": "chromadb"
                }
            else:
                return {
                    "total_documents": len(self._mock_storage),
                    "storage": "mock",
                    "warning": "模拟模式"
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_documents": 0,
                "error": str(e)
            }
    
    def reset(self):
        """重置集合（删除所有数据）"""
        logger.warning("⚠️  重置向量库...")
        
        try:
            if self.client and self.collection:
                # 删除集合
                self.client.delete_collection(self.config["collection_name"])
                # 重新创建
                self._initialize_client()
            else:
                # 模拟模式
                self._mock_storage = []
            
            logger.info("✅ 重置完成")
            return {"success": True}
            
        except Exception as e:
            logger.error(f"❌ 重置失败: {e}")
            return {"success": False, "error": str(e)}


def test_chroma_store():
    """测试ChromaStore"""
    print("="*70)
    print("  ChromaStore测试")
    print("="*70)
    
    # 初始化
    store = ChromaStore()
    
    # 模拟向量（384维）
    def create_mock_embedding(seed: int = 0) -> List[float]:
        """创建模拟嵌入向量"""
        import random
        random.seed(seed)
        return [random.random() for _ in range(384)]
    
    # 测试添加文档
    print("\n1. 测试添加文档:")
    documents = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的子集",
        "深度学习使用神经网络"
    ]
    
    embeddings = [create_mock_embedding(i) for i in range(len(documents))]
    
    metadatas = [
        {"topic": "AI", "language": "zh"},
        {"topic": "ML", "language": "zh"},
        {"topic": "DL", "language": "zh"}
    ]
    
    add_result = store.add_documents(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    
    print(f"   添加结果: {add_result.get('success')}")
    print(f"   文档数量: {add_result.get('count')}")
    
    # 测试查询
    print("\n2. 测试查询:")
    query_embedding = create_mock_embedding(0)  # 与第一个文档相似
    
    query_result = store.query(
        query_embedding=query_embedding,
        n_results=2
    )
    
    print(f"   查询结果: {query_result.get('success')}")
    print(f"   找到数量: {query_result.get('count')}")
    
    for i, result in enumerate(query_result.get('results', []), 1):
        print(f"\n   结果{i}:")
        print(f"     文档: {result['document'][:50]}...")
        print(f"     相似度: {result['score']:.3f}")
    
    # 测试统计
    print("\n3. 统计信息:")
    stats = store.get_statistics()
    print(f"   总文档数: {stats.get('total_documents')}")
    print(f"   存储类型: {stats.get('storage')}")
    
    print("\n✅ ChromaStore测试完成！")


if __name__ == "__main__":
    test_chroma_store()



