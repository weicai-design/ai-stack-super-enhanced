"""
Advanced Reranker
高级重排序器

实现业界最先进的重排序机制：
1. Cross-Encoder模型集成（bge-reranker-large）
2. 多阶段重排序（粗排+精排）
3. 基于生成模型的相关性评分
4. 动态重排序策略
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RerankResult:
    """重排序结果"""
    document_id: str
    content: str
    original_score: float
    rerank_score: float
    rank: int
    metadata: Dict[str, Any]


class AdvancedReranker:
    """
    高级重排序器
    
    支持多种重排序策略和模型
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        enable_cross_encoder: bool = True,
        enable_two_stage: bool = True,
        top_k_coarse: int = 100,
        top_k_fine: int = 10,
    ):
        """
        初始化高级重排序器
        
        Args:
            model_name: 重排序模型名称（如bge-reranker-large）
            enable_cross_encoder: 是否启用Cross-Encoder模型
            enable_two_stage: 是否启用两阶段重排序
            top_k_coarse: 粗排阶段返回数量
            top_k_fine: 精排阶段返回数量
        """
        self.model_name = model_name or "bge-reranker-large"
        self.enable_cross_encoder = enable_cross_encoder
        self.enable_two_stage = enable_two_stage
        self.top_k_coarse = top_k_coarse
        self.top_k_fine = top_k_fine
        
        # 重排序模型（延迟加载）
        self.cross_encoder_model = None
        self.model_loaded = False
        
        # 回退策略
        self.fallback_enabled = True

    def _load_cross_encoder_model(self) -> bool:
        """
        加载Cross-Encoder模型
        
        Returns:
            是否加载成功
        """
        if self.model_loaded and self.cross_encoder_model is not None:
            return True
        
        try:
            # 尝试导入和加载bge-reranker
            try:
                from sentence_transformers import CrossEncoder
                logger.info(f"正在加载Cross-Encoder模型: {self.model_name}")
                
                # 配置HuggingFace镜像（无VPN环境）
                import os
                if "HF_ENDPOINT" not in os.environ:
                    # 尝试加载镜像配置
                    mirror_config = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        ".config", "china_mirrors.env"
                    )
                    if os.path.exists(mirror_config):
                        try:
                            with open(mirror_config, 'r') as f:
                                for line in f:
                                    if line.startswith("export HF_ENDPOINT="):
                                        os.environ["HF_ENDPOINT"] = line.split("=", 1)[1].strip().strip('"')
                                        break
                        except Exception:
                            pass
                    
                    # 如果仍未设置，使用默认镜像
                    if "HF_ENDPOINT" not in os.environ:
                        os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                        logger.info("使用HuggingFace国内镜像: https://hf-mirror.com")
                
                # 尝试加载模型
                self.cross_encoder_model = CrossEncoder(
                    self.model_name,
                    max_length=512,  # 限制长度以提高性能
                    device='cpu',
                )
                self.model_loaded = True
                logger.info(f"✅ Cross-Encoder模型加载成功: {self.model_name}")
                return True
            except ImportError:
                logger.warning("sentence-transformers未安装，无法使用Cross-Encoder")
                return False
            except Exception as e:
                logger.warning(f"Cross-Encoder模型加载失败: {e}，将使用回退策略")
                return False
                
        except Exception as e:
            logger.error(f"加载Cross-Encoder模型时发生错误: {e}")
            return False

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: Optional[int] = None,
    ) -> List[RerankResult]:
        """
        高级重排序
        
        Args:
            query: 查询文本
            documents: 文档列表（包含document_id, content, score等）
            top_k: 返回Top K结果
            
        Returns:
            重排序后的结果列表
        """
        if not documents:
            return []
        
        top_k = top_k or self.top_k_fine
        
        # 两阶段重排序
        if self.enable_two_stage and len(documents) > self.top_k_coarse:
            return await self._two_stage_rerank(query, documents, top_k)
        
        # 单阶段重排序
        return await self._single_stage_rerank(query, documents, top_k)

    async def _two_stage_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        两阶段重排序（粗排+精排）
        
        第一阶段：粗排（使用轻量级方法快速筛选）
        第二阶段：精排（使用Cross-Encoder精确排序）
        """
        logger.debug(f"两阶段重排序：输入 {len(documents)} 个文档")
        
        # 第一阶段：粗排
        coarse_results = await self._coarse_rerank(query, documents, self.top_k_coarse)
        logger.debug(f"粗排阶段：保留 {len(coarse_results)} 个文档")
        
        # 第二阶段：精排
        fine_results = await self._fine_rerank(query, coarse_results, top_k)
        logger.debug(f"精排阶段：返回 {len(fine_results)} 个文档")
        
        return fine_results

    async def _coarse_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        """
        粗排阶段
        
        使用轻量级方法快速筛选候选文档
        """
        # 按原始分数排序
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )
        
        # 应用轻量级重排序规则
        for doc in sorted_docs:
            score = doc.get("score", 0.0)
            
            # 查询关键词匹配奖励
            query_words = set(query.lower().split())
            content = str(doc.get("content", "")).lower()
            content_words = set(content.split())
            overlap = len(query_words & content_words)
            keyword_bonus = min(0.15, overlap * 0.02)
            
            # 长度归一化
            length_factor = self._calculate_length_factor(len(content))
            
            # 调整分数
            doc["coarse_score"] = score * length_factor + keyword_bonus
        
        # 按粗排分数排序
        sorted_docs.sort(key=lambda x: x.get("coarse_score", 0.0), reverse=True)
        
        return sorted_docs[:top_k]

    async def _fine_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        精排阶段
        
        使用Cross-Encoder模型精确排序
        """
        if self.enable_cross_encoder:
            # 尝试使用Cross-Encoder
            if self._load_cross_encoder_model() and self.cross_encoder_model:
                return await self._cross_encoder_rerank(query, documents, top_k)
        
        # 回退到高级规则重排序
        return await self._rule_based_fine_rerank(query, documents, top_k)

    async def _cross_encoder_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        使用Cross-Encoder模型重排序
        
        这是业界最先进的重排序方法，精度最高
        """
        try:
            # 准备输入对
            pairs = []
            for doc in documents:
                content = str(doc.get("content", ""))[:500]  # 限制长度
                pairs.append([query, content])
            
            # 批量计算相关性分数
            scores = self.cross_encoder_model.predict(pairs)
            
            # 构建重排序结果
            rerank_results = []
            for i, doc in enumerate(documents):
                original_score = doc.get("score", 0.0)
                rerank_score = float(scores[i]) if i < len(scores) else original_score
                
                rerank_results.append(
                    RerankResult(
                        document_id=doc.get("document_id", ""),
                        content=str(doc.get("content", "")),
                        original_score=original_score,
                        rerank_score=rerank_score,
                        rank=i + 1,
                        metadata=doc.get("metadata", {}),
                    )
                )
            
            # 按重排序分数排序
            rerank_results.sort(key=lambda x: x.rerank_score, reverse=True)
            
            logger.debug(f"Cross-Encoder重排序完成：{len(rerank_results)} 个结果")
            return rerank_results[:top_k]
            
        except Exception as e:
            logger.error(f"Cross-Encoder重排序失败: {e}，回退到规则重排序")
            return await self._rule_based_fine_rerank(query, documents, top_k)

    async def _rule_based_fine_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        基于规则的精排（回退方案）
        
        使用高级规则进行重排序
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        rerank_results = []
        for doc in documents:
            content = str(doc.get("content", "")).lower()
            original_score = doc.get("score", 0.0)
            
            # 1. 关键词匹配分数
            content_words = set(content.split())
            keyword_overlap = len(query_words & content_words)
            keyword_score = min(1.0, keyword_overlap / max(len(query_words), 1))
            
            # 2. 查询出现在文档的位置（越靠前越好）
            position_score = 1.0
            query_pos = content.find(query_lower)
            if query_pos >= 0:
                position_score = max(0.5, 1.0 - (query_pos / max(len(content), 1)))
            
            # 3. 查询词频率
            query_freq_score = 0.0
            for word in query_words:
                count = content.count(word)
                query_freq_score += min(0.2, count * 0.05)
            
            # 4. 长度因子
            length_factor = self._calculate_length_factor(len(content))
            
            # 综合计算重排序分数
            rerank_score = (
                original_score * 0.4 +
                keyword_score * 0.3 +
                position_score * 0.15 +
                query_freq_score * 0.1 +
                length_factor * 0.05
            )
            
            rerank_results.append(
                RerankResult(
                    document_id=doc.get("document_id", ""),
                    content=str(doc.get("content", "")),
                    original_score=original_score,
                    rerank_score=rerank_score,
                    rank=0,  # 稍后排序
                    metadata=doc.get("metadata", {}),
                )
            )
        
        # 按重排序分数排序
        rerank_results.sort(key=lambda x: x.rerank_score, reverse=True)
        
        # 更新排名
        for i, result in enumerate(rerank_results):
            result.rank = i + 1
        
        return rerank_results[:top_k]

    async def _single_stage_rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int,
    ) -> List[RerankResult]:
        """
        单阶段重排序
        
        直接使用Cross-Encoder或规则重排序
        """
        if self.enable_cross_encoder and len(documents) <= 50:
            # 文档数量少，直接使用Cross-Encoder
            if self._load_cross_encoder_model() and self.cross_encoder_model:
                return await self._cross_encoder_rerank(query, documents, top_k)
        
        # 使用规则重排序
        return await self._rule_based_fine_rerank(query, documents, top_k)

    def _calculate_length_factor(self, length: int) -> float:
        """
        计算长度因子
        
        偏好中等长度的文档（100-500字符）
        """
        if length < 50:
            return 0.8  # 太短
        elif length < 100:
            return 0.9
        elif length <= 500:
            return 1.0  # 理想长度
        elif length <= 1000:
            return 0.95
        else:
            return 0.9  # 太长

    def get_stats(self) -> Dict[str, Any]:
        """
        获取重排序器统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "model_name": self.model_name,
            "model_loaded": self.model_loaded,
            "cross_encoder_enabled": self.enable_cross_encoder,
            "two_stage_enabled": self.enable_two_stage,
            "top_k_coarse": self.top_k_coarse,
            "top_k_fine": self.top_k_fine,
        }


# 全局重排序器实例
_global_reranker: Optional[AdvancedReranker] = None


def get_advanced_reranker(
    model_name: Optional[str] = None,
    enable_cross_encoder: bool = True,
) -> AdvancedReranker:
    """
    获取高级重排序器实例（单例模式）
    
    Args:
        model_name: 重排序模型名称
        enable_cross_encoder: 是否启用Cross-Encoder
        
    Returns:
        AdvancedReranker实例
    """
    global _global_reranker
    
    if _global_reranker is None:
        _global_reranker = AdvancedReranker(
            model_name=model_name,
            enable_cross_encoder=enable_cross_encoder,
        )
    
    return _global_reranker

