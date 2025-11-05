"""
Truth Verification Integration
真实性验证集成模块

将真实性验证集成到RAG摄入流程中
根据需求1.3：所有进入RAG库的信息都会进行去伪的处理
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .enhanced_truth_verification import get_truth_verifier, EnhancedTruthVerification

logger = logging.getLogger(__name__)


class TruthVerificationIntegration:
    """
    真实性验证集成器
    
    负责将真实性验证集成到文档摄入流程
    """

    def __init__(
        self,
        min_credibility: float = 0.65,
        auto_filter: bool = True,
        verify_on_ingest: bool = True,
    ):
        """
        初始化真实性验证集成器
        
        Args:
            min_credibility: 最低可信度阈值（0-1）
            auto_filter: 是否自动过滤低可信度内容
            verify_on_ingest: 是否在摄入时验证
        """
        self.verifier = get_truth_verifier()
        self.min_credibility = min_credibility
        self.auto_filter = auto_filter
        self.verify_on_ingest = verify_on_ingest

    def verify_before_ingest(
        self,
        text: str,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        existing_docs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        在摄入前验证内容
        
        Args:
            text: 要验证的文本
            source: 信息来源
            metadata: 元数据
            existing_docs: 已有文档文本列表（用于一致性检查）
            
        Returns:
            验证结果，包含是否应该接受
        """
        if not self.verify_on_ingest:
            return {
                "verified": True,
                "credibility_score": 1.0,
                "skipped": True,
                "reason": "verification_disabled",
            }

        try:
            result = self.verifier.verify_content(
                text=text,
                source=source,
                metadata=metadata,
                existing_texts=existing_docs,
                min_credibility=self.min_credibility,
            )

            logger.info(
                f"Content verification: {'accepted' if result['verified'] else 'rejected'}, "
                f"credibility: {result['credibility']['credibility_score']:.3f}"
            )

            return {
                "verified": result["verified"],
                "credibility_score": result["credibility"]["credibility_score"],
                "action": result["action"],
                "reason": result["reason"],
                "details": result["credibility"],
            }

        except Exception as e:
            logger.error(f"Truth verification failed: {e}")
            # 验证失败时，根据配置决定是否接受
            return {
                "verified": not self.auto_filter,  # 如果自动过滤，验证失败则拒绝
                "credibility_score": 0.0,
                "error": str(e),
                "reason": "verification_error",
            }

    def process_chunks(
        self,
        chunks: List[Dict[str, Any]],
        source: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        处理文档块，验证并过滤
        
        Args:
            chunks: 文档块列表，每个包含 text 和 metadata
            source: 来源路径/URL
            
        Returns:
            (accepted_chunks, rejected_chunks) 元组
        """
        if not self.auto_filter:
            # 不自动过滤，只添加验证信息
            for chunk in chunks:
                result = self.verify_before_ingest(
                    text=chunk.get("text", ""),
                    source=source,
                    metadata=chunk.get("metadata", {}),
                )
                chunk["verification"] = {
                    "credibility_score": result["credibility_score"],
                    "verified": result["verified"],
                }
            return chunks, []

        # 自动过滤
        content_list = [
            {
                "text": chunk.get("text", ""),
                "source": source,
                "metadata": chunk.get("metadata", {}),
            }
            for chunk in chunks
        ]

        accepted, rejected = self.verifier.filter_content(
            content_list, min_credibility=self.min_credibility
        )

        # 转换回chunk格式
        accepted_chunks = []
        for item in accepted:
            # 找到对应的原始chunk
            for chunk in chunks:
                if chunk.get("text") == item["text"]:
                    chunk["verification"] = item["verification"]
                    accepted_chunks.append(chunk)
                    break

        rejected_chunks = []
        for item in rejected:
            for chunk in chunks:
                if chunk.get("text") == item["text"]:
                    chunk["verification"] = item["verification"]
                    chunk["rejection_reason"] = item.get("rejection_reason")
                    rejected_chunks.append(chunk)
                    break

        logger.info(
            f"Truth verification filter: {len(accepted_chunks)} accepted, "
            f"{len(rejected_chunks)} rejected"
        )

        return accepted_chunks, rejected_chunks

    def get_existing_docs_for_consistency(
        self, doc_store_path: Optional[Path] = None
    ) -> List[str]:
        """
        获取已有文档用于一致性检查
        
        Args:
            doc_store_path: 文档存储路径
            
        Returns:
            已有文档文本列表（采样，用于一致性检查）
        """
        # 这里可以从RAG索引或文档存储中获取已有文档
        # 为了性能，只获取部分文档用于检查
        # 简化实现，实际应从索引中获取
        return []


# 全局集成器实例
_integration_instance: Optional[TruthVerificationIntegration] = None


def get_truth_verification_integration(
    min_credibility: float = 0.65,
    auto_filter: bool = True,
) -> TruthVerificationIntegration:
    """
    获取真实性验证集成器实例
    
    Args:
        min_credibility: 最低可信度阈值
        auto_filter: 是否自动过滤
        
    Returns:
        TruthVerificationIntegration实例
    """
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = TruthVerificationIntegration(
            min_credibility=min_credibility,
            auto_filter=auto_filter,
        )
    return _integration_instance

