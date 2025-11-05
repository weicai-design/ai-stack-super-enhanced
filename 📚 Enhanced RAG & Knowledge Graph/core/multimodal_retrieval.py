"""
Multimodal Retrieval Module
多模态检索模块

根据需求1.5：多模态检索功能
实现：
1. 图像检索
2. 音频检索
3. 混合模态检索（文本+图像联合检索）
4. 多模态相关性排序
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class MultimodalRetrievalResult:
    """多模态检索结果"""
    document_id: str
    content: str
    content_type: str  # 'text', 'image', 'audio', 'video'
    similarity_score: float
    metadata: Dict[str, Any]
    source: str
    modality_specific_data: Optional[Dict[str, Any]] = None  # 模态特定数据（如图像URL、音频时长等）


class MultimodalRetriever:
    """
    多模态检索器
    
    支持图像、音频、文本的联合检索
    """

    def __init__(
        self,
        text_retriever: Any = None,  # 文本检索器
        image_retriever: Any = None,  # 图像检索器
        audio_retriever: Any = None,  # 音频检索器
        enable_parallel: bool = True,
        max_workers: int = 4,
    ):
        """
        初始化多模态检索器
        
        Args:
            text_retriever: 文本检索器实例
            image_retriever: 图像检索器实例
            audio_retriever: 音频检索器实例
            enable_parallel: 是否启用并行检索
            max_workers: 并行检索的最大工作线程数
        """
        self.text_retriever = text_retriever
        self.image_retriever = image_retriever
        self.audio_retriever = audio_retriever
        self.enable_parallel = enable_parallel
        self.executor = ThreadPoolExecutor(max_workers=max_workers) if enable_parallel else None

    async def retrieve_images(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MultimodalRetrievalResult]:
        """
        图像检索
        
        基于图像内容搜索：
        - 如果查询是文本，使用图像描述匹配
        - 如果查询是图像，使用图像相似度匹配
        
        Args:
            query: 查询文本或图像路径
            top_k: 返回Top K结果
            filters: 过滤条件
            
        Returns:
            图像检索结果列表
        """
        try:
            if not self.image_retriever:
                logger.warning("图像检索器未配置，无法执行图像检索")
                return []
            
            # 调用图像检索器
            results = await self.image_retriever.retrieve(
                query=query,
                filters=filters or {},
                top_k=top_k,
            )
            
            # 转换为多模态结果格式
            multimodal_results = []
            for result in results:
                multimodal_results.append(
                    MultimodalRetrievalResult(
                        document_id=result.get("document_id", ""),
                        content=result.get("content", ""),
                        content_type="image",
                        similarity_score=result.get("score", 0.0),
                        metadata=result.get("metadata", {}),
                        source=result.get("source", ""),
                        modality_specific_data={
                            "image_url": result.get("image_url"),
                            "image_size": result.get("image_size"),
                            "thumbnail_url": result.get("thumbnail_url"),
                        },
                    )
                )
            
            return multimodal_results
            
        except Exception as e:
            logger.error(f"图像检索失败: {e}")
            return []

    async def retrieve_audio(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MultimodalRetrievalResult]:
        """
        音频检索
        
        音频内容搜索：
        - 如果查询是文本，使用语音转文本匹配
        - 如果查询是音频，使用音频相似度匹配
        
        Args:
            query: 查询文本或音频路径
            top_k: 返回Top K结果
            filters: 过滤条件
            
        Returns:
            音频检索结果列表
        """
        try:
            if not self.audio_retriever:
                logger.warning("音频检索器未配置，无法执行音频检索")
                return []
            
            # 调用音频检索器
            results = await self.audio_retriever.retrieve(
                query=query,
                filters=filters or {},
                top_k=top_k,
            )
            
            # 转换为多模态结果格式
            multimodal_results = []
            for result in results:
                multimodal_results.append(
                    MultimodalRetrievalResult(
                        document_id=result.get("document_id", ""),
                        content=result.get("content", ""),
                        content_type="audio",
                        similarity_score=result.get("score", 0.0),
                        metadata=result.get("metadata", {}),
                        source=result.get("source", ""),
                        modality_specific_data={
                            "audio_url": result.get("audio_url"),
                            "duration": result.get("duration"),
                            "transcript": result.get("transcript"),  # 语音转文本
                        },
                    )
                )
            
            return multimodal_results
            
        except Exception as e:
            logger.error(f"音频检索失败: {e}")
            return []

    async def hybrid_retrieve(
        self,
        query: str,
        modalities: List[str] = ["text", "image", "audio"],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        fusion_strategy: str = "weighted",
    ) -> List[MultimodalRetrievalResult]:
        """
        混合模态检索（文本+图像+音频联合检索）
        
        Args:
            query: 查询文本
            modalities: 要检索的模态列表 ['text', 'image', 'audio']
            top_k: 每种模态返回Top K结果
            filters: 过滤条件
            fusion_strategy: 融合策略
                - 'weighted': 加权融合
                - 'rank_fusion': 排序融合
                - 'early_fusion': 早期融合（向量空间融合）
                
        Returns:
            融合后的检索结果列表
        """
        try:
            tasks = []
            
            # 并行检索各种模态
            if "text" in modalities and self.text_retriever:
                tasks.append(("text", self._retrieve_text(query, top_k, filters)))
            
            if "image" in modalities and self.image_retriever:
                tasks.append(("image", self.retrieve_images(query, top_k, filters)))
            
            if "audio" in modalities and self.audio_retriever:
                tasks.append(("audio", self.retrieve_audio(query, top_k, filters)))
            
            # 执行检索
            if self.enable_parallel and len(tasks) > 1:
                # 并行执行
                results_dict = {}
                async def run_task(name, coro):
                    results_dict[name] = await coro
                
                await asyncio.gather(*[run_task(name, coro) for name, coro in tasks])
                text_results = results_dict.get("text", [])
                image_results = results_dict.get("image", [])
                audio_results = results_dict.get("audio", [])
            else:
                # 串行执行
                text_results = []
                image_results = []
                audio_results = []
                
                for name, coro in tasks:
                    if name == "text":
                        text_results = await coro
                    elif name == "image":
                        image_results = await coro
                    elif name == "audio":
                        audio_results = await coro
            
            # 融合结果
            if fusion_strategy == "weighted":
                return self._weighted_fusion(text_results, image_results, audio_results, top_k)
            elif fusion_strategy == "rank_fusion":
                return self._rank_fusion(text_results, image_results, audio_results, top_k)
            else:
                return self._simple_fusion(text_results, image_results, audio_results, top_k)
                
        except Exception as e:
            logger.error(f"混合模态检索失败: {e}")
            return []

    async def _retrieve_text(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]],
    ) -> List[MultimodalRetrievalResult]:
        """文本检索"""
        try:
            if not self.text_retriever:
                return []
            
            results = await self.text_retriever.retrieve(
                query=query,
                filters=filters or {},
                top_k=top_k,
            )
            
            multimodal_results = []
            for result in results:
                multimodal_results.append(
                    MultimodalRetrievalResult(
                        document_id=result.get("document_id", ""),
                        content=result.get("content", ""),
                        content_type="text",
                        similarity_score=result.get("score", 0.0),
                        metadata=result.get("metadata", {}),
                        source=result.get("source", ""),
                    )
                )
            
            return multimodal_results
        except Exception as e:
            logger.error(f"文本检索失败: {e}")
            return []

    def _weighted_fusion(
        self,
        text_results: List[MultimodalRetrievalResult],
        image_results: List[MultimodalRetrievalResult],
        audio_results: List[MultimodalRetrievalResult],
        top_k: int,
    ) -> List[MultimodalRetrievalResult]:
        """
        加权融合
        
        不同模态的结果按权重加权融合
        """
        weights = {
            "text": 0.5,
            "image": 0.3,
            "audio": 0.2,
        }
        
        all_results = []
        
        # 加权分数
        for result in text_results:
            result.similarity_score *= weights["text"]
            all_results.append(result)
        
        for result in image_results:
            result.similarity_score *= weights["image"]
            all_results.append(result)
        
        for result in audio_results:
            result.similarity_score *= weights["audio"]
            all_results.append(result)
        
        # 按分数排序
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return all_results[:top_k]

    def _rank_fusion(
        self,
        text_results: List[MultimodalRetrievalResult],
        image_results: List[MultimodalRetrievalResult],
        audio_results: List[MultimodalRetrievalResult],
        top_k: int,
    ) -> List[MultimodalRetrievalResult]:
        """
        排序融合（Reciprocal Rank Fusion）
        
        基于排名而非分数进行融合
        """
        all_results = {}
        
        # 收集所有结果
        for idx, result in enumerate(text_results):
            doc_id = result.document_id
            if doc_id not in all_results:
                all_results[doc_id] = result
                all_results[doc_id].similarity_score = 0.0
            # RRF: 1 / (k + rank)
            all_results[doc_id].similarity_score += 1.0 / (60 + idx + 1)
        
        for idx, result in enumerate(image_results):
            doc_id = result.document_id
            if doc_id not in all_results:
                all_results[doc_id] = result
                all_results[doc_id].similarity_score = 0.0
            all_results[doc_id].similarity_score += 1.0 / (60 + idx + 1)
        
        for idx, result in enumerate(audio_results):
            doc_id = result.document_id
            if doc_id not in all_results:
                all_results[doc_id] = result
                all_results[doc_id].similarity_score = 0.0
            all_results[doc_id].similarity_score += 1.0 / (60 + idx + 1)
        
        # 按融合分数排序
        fused_results = list(all_results.values())
        fused_results.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return fused_results[:top_k]

    def _simple_fusion(
        self,
        text_results: List[MultimodalRetrievalResult],
        image_results: List[MultimodalRetrievalResult],
        audio_results: List[MultimodalRetrievalResult],
        top_k: int,
    ) -> List[MultimodalRetrievalResult]:
        """简单融合（直接合并，按分数排序）"""
        all_results = text_results + image_results + audio_results
        all_results.sort(key=lambda x: x.similarity_score, reverse=True)
        return all_results[:top_k]


# 全局多模态检索器实例
_global_multimodal_retriever: Optional[MultimodalRetriever] = None


def get_multimodal_retriever(
    text_retriever: Any = None,
    image_retriever: Any = None,
    audio_retriever: Any = None,
) -> MultimodalRetriever:
    """
    获取多模态检索器实例（单例模式）
    
    Args:
        text_retriever: 文本检索器
        image_retriever: 图像检索器
        audio_retriever: 音频检索器
        
    Returns:
        MultimodalRetriever实例
    """
    global _global_multimodal_retriever
    
    if _global_multimodal_retriever is None:
        _global_multimodal_retriever = MultimodalRetriever(
            text_retriever=text_retriever,
            image_retriever=image_retriever,
            audio_retriever=audio_retriever,
        )
    
    return _global_multimodal_retriever

