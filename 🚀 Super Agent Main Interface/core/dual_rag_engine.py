#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双RAG检索引擎
P0-002: 实现完整的双RAG检索系统，包括第1次RAG检索（理解需求）和第2次RAG检索（整合经验知识）
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class RAGRetrievalResult:
    """RAG检索结果"""
    retrieval_id: str
    query: str
    knowledge_items: List[Dict[str, Any]]
    understanding: Dict[str, Any]
    retrieval_time: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "retrieval_id": self.retrieval_id,
            "query": self.query,
            "knowledge_items": self.knowledge_items,
            "understanding": self.understanding,
            "retrieval_time": self.retrieval_time,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }


class DualRAGEngine:
    """
    双RAG检索引擎
    
    实现AI工作流的双RAG检索：
    1. 第1次RAG检索：理解需求 + 检索相关知识
    2. 第2次RAG检索：整合经验知识 + 查找类似案例
    """
    
    def __init__(
        self,
        rag_service=None,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
    ):
        self.rag_service = rag_service
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        
        # 缓存
        self.rag1_cache: Dict[str, Dict[str, Any]] = {}
        self.rag2_cache: Dict[str, Dict[str, Any]] = {}
        
        # 统计
        self.stats = {
            "rag1_total": 0,
            "rag1_cache_hits": 0,
            "rag1_avg_time": 0.0,
            "rag2_total": 0,
            "rag2_cache_hits": 0,
            "rag2_avg_time": 0.0,
        }
    
    async def first_rag_retrieval(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        timeout: float = 2.0,
    ) -> RAGRetrievalResult:
        """
        第1次RAG检索：理解需求 + 检索相关知识
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            top_k: 返回数量
            timeout: 超时时间（秒）
            
        Returns:
            RAG检索结果
        """
        start_time = datetime.utcnow()
        retrieval_id = f"rag1_{uuid4()}"
        
        # 检查缓存
        cache_key = self._generate_cache_key("rag1", user_input, context)
        if self.cache_enabled and cache_key in self.rag1_cache:
            cached = self.rag1_cache[cache_key]
            if (datetime.utcnow() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < self.cache_ttl:
                self.stats["rag1_cache_hits"] += 1
                logger.debug(f"第1次RAG检索缓存命中: {cache_key[:50]}")
                return RAGRetrievalResult(
                    retrieval_id=retrieval_id,
                    query=user_input,
                    knowledge_items=cached["knowledge_items"],
                    understanding=cached["understanding"],
                    retrieval_time=0.0,
                    metadata={"from_cache": True},
                )
        
        try:
            # 执行检索（带超时）
            retrieval_task = asyncio.create_task(
                self._execute_first_retrieval(user_input, context, top_k)
            )
            result = await asyncio.wait_for(retrieval_task, timeout=timeout)
            
            retrieval_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新统计
            self.stats["rag1_total"] += 1
            self._update_avg_time("rag1", retrieval_time)
            
            # 缓存结果
            if self.cache_enabled:
                self.rag1_cache[cache_key] = {
                    "knowledge_items": result["knowledge_items"],
                    "understanding": result["understanding"],
                    "cached_at": datetime.utcnow().isoformat(),
                }
                # 限制缓存大小
                if len(self.rag1_cache) > 1000:
                    oldest_key = min(self.rag1_cache.keys(), key=lambda k: self.rag1_cache[k]["cached_at"])
                    del self.rag1_cache[oldest_key]
            
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=result["knowledge_items"],
                understanding=result["understanding"],
                retrieval_time=retrieval_time,
                metadata={"from_cache": False},
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"第1次RAG检索超时: {user_input[:50]}")
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=[],
                understanding={"intent": "query", "confidence": 0.5, "error": "timeout"},
                retrieval_time=timeout,
                metadata={"error": "timeout"},
            )
        except Exception as e:
            logger.error(f"第1次RAG检索失败: {e}", exc_info=True)
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=[],
                understanding={"intent": "query", "confidence": 0.5, "error": str(e)},
                retrieval_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={"error": str(e)},
            )
    
    async def _execute_first_retrieval(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]],
        top_k: int,
    ) -> Dict[str, Any]:
        """执行第1次RAG检索"""
        if not self.rag_service:
            return {
                "knowledge_items": [],
                "understanding": {"intent": "query", "confidence": 0.5},
            }
        
        # 检索相关知识
        knowledge_items = await self.rag_service.retrieve(
            query=user_input,
            top_k=top_k,
            context=context,
        )
        
        # 理解用户意图
        understanding = await self.rag_service.understand_intent(user_input)
        
        # 增强理解（基于检索结果）
        if knowledge_items:
            # 从知识项中提取领域信息
            domains = set()
            for item in knowledge_items:
                metadata = item.get("metadata", {})
                if "domain" in metadata:
                    domains.add(metadata["domain"])
                elif "module" in metadata:
                    domains.add(metadata["module"])
            
            if domains:
                understanding["domains"] = list(domains)
                understanding["confidence"] = min(0.95, understanding.get("confidence", 0.5) + 0.1)
        
        return {
            "knowledge_items": knowledge_items,
            "understanding": understanding,
        }
    
    async def second_rag_retrieval(
        self,
        user_input: str,
        execution_result: Dict[str, Any],
        rag1_result: Optional[RAGRetrievalResult] = None,
        top_k: int = 3,
        timeout: float = 1.0,
    ) -> RAGRetrievalResult:
        """
        第2次RAG检索：整合经验知识 + 查找类似案例
        
        Args:
            user_input: 用户输入
            execution_result: 执行结果
            rag1_result: 第1次RAG检索结果（可选）
            top_k: 返回数量
            timeout: 超时时间（秒）
            
        Returns:
            RAG检索结果
        """
        start_time = datetime.utcnow()
        retrieval_id = f"rag2_{uuid4()}"
        
        # 检查缓存
        cache_key = self._generate_cache_key("rag2", user_input, execution_result)
        if self.cache_enabled and cache_key in self.rag2_cache:
            cached = self.rag2_cache[cache_key]
            if (datetime.utcnow() - datetime.fromisoformat(cached["cached_at"])).total_seconds() < self.cache_ttl:
                self.stats["rag2_cache_hits"] += 1
                logger.debug(f"第2次RAG检索缓存命中: {cache_key[:50]}")
                return RAGRetrievalResult(
                    retrieval_id=retrieval_id,
                    query=user_input,
                    knowledge_items=cached["knowledge_items"],
                    understanding=cached["understanding"],
                    retrieval_time=0.0,
                    metadata={"from_cache": True},
                )
        
        try:
            # 执行检索（带超时）
            retrieval_task = asyncio.create_task(
                self._execute_second_retrieval(user_input, execution_result, rag1_result, top_k)
            )
            result = await asyncio.wait_for(retrieval_task, timeout=timeout)
            
            retrieval_time = (datetime.utcnow() - start_time).total_seconds()
            
            # 更新统计
            self.stats["rag2_total"] += 1
            self._update_avg_time("rag2", retrieval_time)
            
            # 缓存结果
            if self.cache_enabled:
                self.rag2_cache[cache_key] = {
                    "knowledge_items": result["knowledge_items"],
                    "understanding": result["understanding"],
                    "cached_at": datetime.utcnow().isoformat(),
                }
                # 限制缓存大小
                if len(self.rag2_cache) > 1000:
                    oldest_key = min(self.rag2_cache.keys(), key=lambda k: self.rag2_cache[k]["cached_at"])
                    del self.rag2_cache[oldest_key]
            
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=result["knowledge_items"],
                understanding=result["understanding"],
                retrieval_time=retrieval_time,
                metadata={"from_cache": False},
            )
            
        except asyncio.TimeoutError:
            logger.warning(f"第2次RAG检索超时: {user_input[:50]}")
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=[],
                understanding={"intent": "integration", "confidence": 0.5, "error": "timeout"},
                retrieval_time=timeout,
                metadata={"error": "timeout"},
            )
        except Exception as e:
            logger.error(f"第2次RAG检索失败: {e}", exc_info=True)
            return RAGRetrievalResult(
                retrieval_id=retrieval_id,
                query=user_input,
                knowledge_items=[],
                understanding={"intent": "integration", "confidence": 0.5, "error": str(e)},
                retrieval_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={"error": str(e)},
            )
    
    async def _execute_second_retrieval(
        self,
        user_input: str,
        execution_result: Dict[str, Any],
        rag1_result: Optional[RAGRetrievalResult],
        top_k: int,
    ) -> Dict[str, Any]:
        """执行第2次RAG检索"""
        if not self.rag_service:
            return {
                "knowledge_items": [],
                "understanding": {"intent": "integration", "confidence": 0.5},
            }
        
        # 查找类似案例
        similar_cases = await self.rag_service.find_similar_cases(
            execution_result=execution_result,
            top_k=top_k,
        )
        
        # 获取最佳实践
        module = execution_result.get("module", "default")
        best_practices = await self.rag_service.get_best_practices(
            module=module,
            top_k=top_k,
        )
        
        # 整合知识
        knowledge_items = []
        
        # 添加类似案例
        for case in similar_cases:
            knowledge_items.append({
                "id": case.get("id", f"case_{uuid4()}"),
                "content": case.get("content", ""),
                "title": case.get("title", ""),
                "score": case.get("score", 0.8),
                "source": "similar_case",
                "metadata": {
                    **case.get("metadata", {}),
                    "type": "case",
                },
            })
        
        # 添加最佳实践
        for practice in best_practices:
            knowledge_items.append({
                "id": f"practice_{uuid4()}",
                "content": practice,
                "title": f"{module}最佳实践",
                "score": 0.85,
                "source": "best_practice",
                "metadata": {
                    "module": module,
                    "type": "practice",
                },
            })
        
        # 如果有第1次RAG结果，可以基于它进行增强检索
        if rag1_result and rag1_result.knowledge_items:
            # 从第1次结果中提取关键信息进行二次检索
            key_terms = []
            for item in rag1_result.knowledge_items[:3]:  # 只取前3个
                content = item.get("content", "")
                if content:
                    # 提取关键词（简单实现）
                    words = content.split()[:5]  # 取前5个词
                    key_terms.extend(words)
            
            if key_terms:
                enhanced_query = " ".join(key_terms[:10])  # 最多10个词
                enhanced_results = await self.rag_service.retrieve(
                    query=enhanced_query,
                    top_k=2,
                    filter_type="experience",
                )
                knowledge_items.extend(enhanced_results)
        
        # 去重和排序
        knowledge_items = self._deduplicate_and_sort(knowledge_items)
        
        return {
            "knowledge_items": knowledge_items[:top_k],
            "understanding": {
                "intent": "integration",
                "confidence": 0.8 if knowledge_items else 0.5,
                "similar_cases_count": len(similar_cases),
                "best_practices_count": len(best_practices),
            },
        }
    
    def _deduplicate_and_sort(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重和排序"""
        seen_ids = set()
        unique_items = []
        
        for item in items:
            item_id = item.get("id", "")
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)
            elif not item_id:
                # 如果没有ID，使用内容的前50个字符作为唯一标识
                content_hash = hash(item.get("content", "")[:50])
                if content_hash not in seen_ids:
                    seen_ids.add(content_hash)
                    unique_items.append(item)
        
        # 按分数排序
        unique_items.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        return unique_items
    
    def _generate_cache_key(
        self,
        prefix: str,
        user_input: str,
        context_or_result: Optional[Dict[str, Any]],
    ) -> str:
        """生成缓存键"""
        key_parts = [prefix, user_input[:100]]  # 限制长度
        
        if context_or_result:
            # 提取关键信息
            module = context_or_result.get("module", "")
            result_type = context_or_result.get("type", "")
            if module:
                key_parts.append(f"module:{module}")
            if result_type:
                key_parts.append(f"type:{result_type}")
        
        return "|".join(key_parts)
    
    def _update_avg_time(self, rag_type: str, time: float):
        """更新平均时间"""
        key = f"{rag_type}_avg_time"
        total_key = f"{rag_type}_total"
        
        current_avg = self.stats[key]
        total = self.stats[total_key]
        
        # 计算新的平均值
        if total == 1:
            self.stats[key] = time
        else:
            self.stats[key] = (current_avg * (total - 1) + time) / total
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "rag1_cache_size": len(self.rag1_cache),
            "rag2_cache_size": len(self.rag2_cache),
            "rag1_cache_hit_rate": (
                self.stats["rag1_cache_hits"] / self.stats["rag1_total"] * 100
                if self.stats["rag1_total"] > 0
                else 0
            ),
            "rag2_cache_hit_rate": (
                self.stats["rag2_cache_hits"] / self.stats["rag2_total"] * 100
                if self.stats["rag2_total"] > 0
                else 0
            ),
        }
    
    def clear_cache(self):
        """清空缓存"""
        self.rag1_cache.clear()
        self.rag2_cache.clear()
        logger.info("双RAG检索缓存已清空")

