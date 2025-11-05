"""
Semantic Deduplication
语义去重模块

根据需求1.2：增强去重处理
功能：
1. 语义相似度去重
2. 内容相似度检测
3. 重复片段识别
4. 跨文档去重
"""

import hashlib
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticDeduplicator:
    """
    语义去重器
    
    使用向量相似度检测重复或相似内容
    """

    def __init__(
        self,
        embedding_model: Optional[SentenceTransformer] = None,
        similarity_threshold: float = 0.95,
        min_chunk_size: int = 50,
    ):
        """
        初始化语义去重器
        
        Args:
            embedding_model: 嵌入模型（如果为None，将自动加载）
            similarity_threshold: 相似度阈值（0-1），超过此值视为重复
            min_chunk_size: 最小文本块大小（字符数）
        """
        self.similarity_threshold = similarity_threshold
        self.min_chunk_size = min_chunk_size
        
        if embedding_model:
            self.embedding_model = embedding_model
        else:
            # 延迟加载模型
            self.embedding_model = None
            self._model_name = "all-MiniLM-L6-v2"

        # 文档指纹缓存（用于快速去重）
        self.doc_fingerprints: Dict[str, str] = {}
        # 语义指纹缓存（向量hash）
        self.semantic_fingerprints: Dict[str, np.ndarray] = {}

    def _load_model(self):
        """延迟加载嵌入模型"""
        if self.embedding_model is None:
            try:
                model_path = os.getenv(
                    "LOCAL_ST_MODEL_PATH",
                    f"./models/{self._model_name}"
                )
                if os.path.exists(model_path):
                    self.embedding_model = SentenceTransformer(model_path)
                else:
                    self.embedding_model = SentenceTransformer(self._model_name)
                logger.info(f"语义去重模型加载成功: {self._model_name}")
            except Exception as e:
                logger.error(f"模型加载失败: {e}")
                raise

    def compute_text_hash(self, text: str) -> str:
        """
        计算文本的MD5哈希值（用于精确匹配）
        
        Args:
            text: 文本内容
            
        Returns:
            MD5哈希值
        """
        text_bytes = text.encode("utf-8", errors="ignore")
        return hashlib.md5(text_bytes).hexdigest()

    def compute_semantic_fingerprint(self, text: str) -> np.ndarray:
        """
        计算文本的语义指纹（向量嵌入）
        
        Args:
            text: 文本内容
            
        Returns:
            嵌入向量
        """
        self._load_model()
        if not text or len(text.strip()) < self.min_chunk_size:
            # 对于太短的文本，返回零向量
            return np.zeros(self.embedding_model.get_sentence_embedding_dimension())
        
        try:
            embedding = self.embedding_model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            return embedding
        except Exception as e:
            logger.warning(f"语义指纹计算失败: {e}")
            return np.zeros(self.embedding_model.get_sentence_embedding_dimension())

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
            
        Returns:
            相似度值（0-1）
        """
        if vec1.size == 0 or vec2.size == 0:
            return 0.0
        
        # 确保向量已归一化
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
        
        similarity = np.dot(vec1_norm, vec2_norm)
        return float(np.clip(similarity, -1.0, 1.0))

    def is_duplicate(
        self,
        text: str,
        existing_texts: Optional[List[str]] = None,
        existing_embeddings: Optional[List[np.ndarray]] = None,
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        检查文本是否为重复内容
        
        Args:
            text: 待检查的文本
            existing_texts: 已有文本列表（可选）
            existing_embeddings: 已有嵌入向量列表（可选）
            
        Returns:
            (是否为重复, 匹配的文本, 相似度)
        """
        if not text or len(text.strip()) < self.min_chunk_size:
            return False, None, None

        # 1. 快速检查：精确匹配（MD5）
        text_hash = self.compute_text_hash(text)
        if text_hash in self.doc_fingerprints.values():
            for doc_id, doc_hash in self.doc_fingerprints.items():
                if doc_hash == text_hash:
                    return True, doc_id, 1.0

        # 2. 语义相似度检查
        current_embedding = self.compute_semantic_fingerprint(text)
        
        # 如果提供了已有文本，计算它们的嵌入
        if existing_texts and not existing_embeddings:
            existing_embeddings = [
                self.compute_semantic_fingerprint(t) for t in existing_texts
            ]
        
        if existing_embeddings:
            max_similarity = 0.0
            best_match_idx = None
            
            for idx, existing_emb in enumerate(existing_embeddings):
                similarity = self.cosine_similarity(current_embedding, existing_emb)
                if similarity > max_similarity:
                    max_similarity = similarity
                    best_match_idx = idx
            
            if max_similarity >= self.similarity_threshold:
                matched_text = existing_texts[best_match_idx] if existing_texts else None
                return True, matched_text, max_similarity

        # 3. 检查语义指纹缓存
        for doc_id, cached_embedding in self.semantic_fingerprints.items():
            similarity = self.cosine_similarity(current_embedding, cached_embedding)
            if similarity >= self.similarity_threshold:
                return True, doc_id, similarity

        return False, None, None

    def deduplicate_batch(
        self,
        texts: List[str],
        keep_first: bool = True,
    ) -> Dict[str, Any]:
        """
        批量去重
        
        Args:
            texts: 文本列表
            keep_first: 是否保留第一个出现的文本
            
        Returns:
            去重结果字典
        """
        if not texts:
            return {
                "original_count": 0,
                "deduplicated_count": 0,
                "removed_count": 0,
                "kept_indices": [],
                "removed_indices": [],
            }

        kept_indices = []
        removed_indices = []
        seen_hashes: Set[str] = set()
        seen_embeddings: List[np.ndarray] = []

        for idx, text in enumerate(texts):
            if not text or len(text.strip()) < self.min_chunk_size:
                removed_indices.append(idx)
                continue

            # 检查精确重复
            text_hash = self.compute_text_hash(text)
            if text_hash in seen_hashes:
                removed_indices.append(idx)
                continue

            # 检查语义重复
            is_dup, matched_text, similarity = self.is_duplicate(
                text,
                existing_embeddings=seen_embeddings,
            )

            if is_dup:
                removed_indices.append(idx)
                logger.debug(f"发现重复内容 (相似度: {similarity:.3f}): 索引 {idx}")
            else:
                kept_indices.append(idx)
                seen_hashes.add(text_hash)
                embedding = self.compute_semantic_fingerprint(text)
                seen_embeddings.append(embedding)

        return {
            "original_count": len(texts),
            "deduplicated_count": len(kept_indices),
            "removed_count": len(removed_indices),
            "kept_indices": kept_indices,
            "removed_indices": removed_indices,
            "kept_texts": [texts[i] for i in kept_indices],
            "removed_texts": [texts[i] for i in removed_indices],
        }

    def register_document(self, doc_id: str, text: str):
        """
        注册文档到去重索引
        
        Args:
            doc_id: 文档ID
            text: 文档文本
        """
        text_hash = self.compute_text_hash(text)
        self.doc_fingerprints[doc_id] = text_hash
        
        if len(text.strip()) >= self.min_chunk_size:
            embedding = self.compute_semantic_fingerprint(text)
            self.semantic_fingerprints[doc_id] = embedding

    def remove_document(self, doc_id: str):
        """
        从去重索引中移除文档
        
        Args:
            doc_id: 文档ID
        """
        self.doc_fingerprints.pop(doc_id, None)
        self.semantic_fingerprints.pop(doc_id, None)


# 全局去重器实例（可选）
_global_deduplicator: Optional[SemanticDeduplicator] = None


def get_deduplicator(
    similarity_threshold: float = 0.95,
    min_chunk_size: int = 50,
) -> SemanticDeduplicator:
    """
    获取全局去重器实例（单例模式）
    
    Args:
        similarity_threshold: 相似度阈值
        min_chunk_size: 最小文本块大小
        
    Returns:
        SemanticDeduplicator实例
    """
    global _global_deduplicator
    
    if _global_deduplicator is None:
        _global_deduplicator = SemanticDeduplicator(
            similarity_threshold=similarity_threshold,
            min_chunk_size=min_chunk_size,
        )
    
    return _global_deduplicator

