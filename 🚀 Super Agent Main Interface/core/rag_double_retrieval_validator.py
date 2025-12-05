#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG双检索完整验证器（T002）

功能：
1. 验证第1次RAG检索（理解需求）的完整性和质量
2. 验证第2次RAG检索（整合经验知识）的完整性和质量
3. 提供详细的验证报告和性能指标
4. 确保两次检索都有明确的输入输出和可验证的质量

验收标准：
- 两次RAG检索都有明确的输入输出
- 可验证检索质量（相关性、完整性、时效性）
- 第1次检索用于理解需求
- 第2次检索用于整合经验知识
- 检索结果有明确的元数据和来源信息
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import time

logger = logging.getLogger(__name__)


class RetrievalType(Enum):
    """检索类型枚举"""
    FIRST_RETRIEVAL = "first_retrieval"  # 第1次检索：理解需求
    SECOND_RETRIEVAL = "second_retrieval"  # 第2次检索：整合经验知识


class ValidationStatus(Enum):
    """验证状态枚举"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class RetrievalValidationResult:
    """检索验证结果"""
    retrieval_type: RetrievalType
    query: str
    results: List[Dict[str, Any]]
    validation_status: ValidationStatus
    validation_metrics: Dict[str, Any]
    validation_details: Dict[str, Any]
    duration_seconds: float
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "retrieval_type": self.retrieval_type.value,
            "query": self.query,
            "results_count": len(self.results),
            "validation_status": self.validation_status.value,
            "validation_metrics": self.validation_metrics,
            "validation_details": self.validation_details,
            "duration_seconds": self.duration_seconds,
            "timestamp": self.timestamp,
        }


@dataclass
class DoubleRetrievalValidationReport:
    """双检索验证报告"""
    first_retrieval_result: Optional[RetrievalValidationResult] = None
    second_retrieval_result: Optional[RetrievalValidationResult] = None
    overall_status: ValidationStatus = ValidationStatus.PASSED
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    validation_summary: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "first_retrieval": self.first_retrieval_result.to_dict() if self.first_retrieval_result else None,
            "second_retrieval": self.second_retrieval_result.to_dict() if self.second_retrieval_result else None,
            "overall_status": self.overall_status.value,
            "performance_metrics": self.performance_metrics,
            "validation_summary": self.validation_summary,
            "timestamp": self.timestamp,
        }


class RAGDoubleRetrievalValidator:
    """
    RAG双检索完整验证器
    
    实现完整的RAG双检索验证机制，确保两次检索都能正确执行
    """
    
    def __init__(self, rag_service: Any):
        """
        初始化验证器
        
        Args:
            rag_service: RAG服务实例
        """
        self.rag_service = rag_service
        self.validation_history: List[DoubleRetrievalValidationReport] = []
        
        # 验证配置
        self.validation_config = {
            "first_retrieval": {
                "min_results": 1,
                "max_response_time": 2.0,  # 秒
                "required_fields": ["content", "score"],
                "min_avg_score": 0.3,
            },
            "second_retrieval": {
                "min_results": 1,
                "max_response_time": 3.0,  # 秒
                "required_fields": ["content", "score", "metadata"],
                "min_avg_score": 0.4,
            },
        }
    
    async def validate_double_retrieval(
        self,
        query: str,
        execution_result: Optional[Dict[str, Any]] = None,
        top_k_first: int = 5,
        top_k_second: int = 3,
    ) -> DoubleRetrievalValidationReport:
        """
        执行完整的双检索验证
        
        Args:
            query: 用户查询
            execution_result: 执行结果（用于第2次检索）
            top_k_first: 第1次检索返回数量
            top_k_second: 第2次检索返回数量
            
        Returns:
            验证报告
        """
        start_time = time.time()
        
        # 1. 验证第1次RAG检索
        first_retrieval_result = await self._validate_first_retrieval(
            query, top_k_first
        )
        
        # 2. 验证第2次RAG检索（如果有执行结果）
        second_retrieval_result = None
        if execution_result and execution_result.get("success"):
            second_retrieval_result = await self._validate_second_retrieval(
                query, execution_result, top_k_second
            )
        
        # 3. 生成整体验证报告
        report = self._generate_validation_report(
            first_retrieval_result,
            second_retrieval_result,
            time.time() - start_time,
        )
        
        # 4. 保存验证历史
        self.validation_history.append(report)
        if len(self.validation_history) > 50:
            self.validation_history = self.validation_history[-50:]
        
        logger.info(f"双检索验证完成: query='{query[:30]}...', 状态={report.overall_status.value}")
        
        return report
    
    async def _validate_first_retrieval(
        self, query: str, top_k: int
    ) -> RetrievalValidationResult:
        """验证第1次RAG检索（理解需求）"""
        start_time = time.time()
        
        try:
            # 执行第1次RAG检索
            results = await self.rag_service.retrieve(
                query=query,
                top_k=top_k,
                context={"purpose": "understand_intent"},
                filter_type="general"
            )
            
            duration = time.time() - start_time
            
            # 执行验证检查
            validation_checks = self._perform_first_retrieval_validation(results, duration)
            
            # 计算验证状态
            status = self._calculate_validation_status(validation_checks)
            
            # 生成验证指标
            metrics = self._calculate_first_retrieval_metrics(results, duration)
            
            return RetrievalValidationResult(
                retrieval_type=RetrievalType.FIRST_RETRIEVAL,
                query=query,
                results=results,
                validation_status=status,
                validation_metrics=metrics,
                validation_details=validation_checks,
                duration_seconds=duration,
            )
            
        except Exception as e:
            logger.error(f"第1次检索验证失败: {e}")
            return RetrievalValidationResult(
                retrieval_type=RetrievalType.FIRST_RETRIEVAL,
                query=query,
                results=[],
                validation_status=ValidationStatus.FAILED,
                validation_metrics={"error": str(e)},
                validation_details={"exception": str(e)},
                duration_seconds=time.time() - start_time,
            )
    
    async def _validate_second_retrieval(
        self, query: str, execution_result: Dict[str, Any], top_k: int
    ) -> RetrievalValidationResult:
        """验证第2次RAG检索（整合经验知识）"""
        start_time = time.time()
        
        try:
            # 执行第2次RAG检索
            results = await self.rag_service.retrieve_for_integration(
                execution_result=execution_result,
                top_k=top_k,
                context={"purpose": "integrate_experience"},
                filter_type="experience"
            )
            
            duration = time.time() - start_time
            
            # 执行验证检查
            validation_checks = self._perform_second_retrieval_validation(results, duration)
            
            # 计算验证状态
            status = self._calculate_validation_status(validation_checks)
            
            # 生成验证指标
            metrics = self._calculate_second_retrieval_metrics(results, duration, execution_result)
            
            return RetrievalValidationResult(
                retrieval_type=RetrievalType.SECOND_RETRIEVAL,
                query=query,
                results=results,
                validation_status=status,
                validation_metrics=metrics,
                validation_details=validation_checks,
                duration_seconds=duration,
            )
            
        except Exception as e:
            logger.error(f"第2次检索验证失败: {e}")
            return RetrievalValidationResult(
                retrieval_type=RetrievalType.SECOND_RETRIEVAL,
                query=query,
                results=[],
                validation_status=ValidationStatus.FAILED,
                validation_metrics={"error": str(e)},
                validation_details={"exception": str(e)},
                duration_seconds=time.time() - start_time,
            )
    
    def _perform_first_retrieval_validation(
        self, results: List[Dict[str, Any]], duration: float
    ) -> Dict[str, Any]:
        """执行第1次检索验证检查"""
        config = self.validation_config["first_retrieval"]
        
        checks = {
            "has_results": len(results) >= config["min_results"],
            "response_time_ok": duration <= config["max_response_time"],
            "has_required_fields": all(
                all(field in result for field in config["required_fields"])
                for result in results
            ) if results else False,
            "avg_score_ok": False,
        }
        
        # 计算平均分检查
        if results:
            avg_score = sum(result.get("score", 0) for result in results) / len(results)
            checks["avg_score_ok"] = avg_score >= config["min_avg_score"]
        
        return checks
    
    def _perform_second_retrieval_validation(
        self, results: List[Dict[str, Any]], duration: float
    ) -> Dict[str, Any]:
        """执行第2次检索验证检查"""
        config = self.validation_config["second_retrieval"]
        
        checks = {
            "has_results": len(results) >= config["min_results"],
            "response_time_ok": duration <= config["max_response_time"],
            "has_required_fields": all(
                all(field in result for field in config["required_fields"])
                for result in results
            ) if results else False,
            "has_experience_metadata": all(
                "metadata" in result and "experience" in result.get("metadata", {}).get("type", "")
                for result in results
            ) if results else False,
            "avg_score_ok": False,
        }
        
        # 计算平均分检查
        if results:
            avg_score = sum(result.get("score", 0) for result in results) / len(results)
            checks["avg_score_ok"] = avg_score >= config["min_avg_score"]
        
        return checks
    
    def _calculate_validation_status(self, checks: Dict[str, Any]) -> ValidationStatus:
        """计算验证状态"""
        passed = sum(1 for check in checks.values() if check)
        total = len(checks)
        pass_rate = passed / total if total > 0 else 0
        
        if pass_rate >= 0.8:
            return ValidationStatus.PASSED
        elif pass_rate >= 0.5:
            return ValidationStatus.WARNING
        else:
            return ValidationStatus.FAILED
    
    def _calculate_first_retrieval_metrics(
        self, results: List[Dict[str, Any]], duration: float
    ) -> Dict[str, Any]:
        """计算第1次检索指标"""
        metrics = {
            "results_count": len(results),
            "response_time": duration,
            "avg_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
        }
        
        if results:
            scores = [result.get("score", 0) for result in results]
            metrics.update({
                "avg_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
            })
        
        return metrics
    
    def _calculate_second_retrieval_metrics(
        self, results: List[Dict[str, Any]], duration: float, execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """计算第2次检索指标"""
        metrics = {
            "results_count": len(results),
            "response_time": duration,
            "avg_score": 0.0,
            "min_score": 0.0,
            "max_score": 0.0,
            "execution_module": execution_result.get("module", "unknown"),
            "execution_type": execution_result.get("type", "unknown"),
        }
        
        if results:
            scores = [result.get("score", 0) for result in results]
            metrics.update({
                "avg_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
            })
            
            # 计算经验知识相关指标
            experience_count = sum(1 for result in results 
                                 if "experience" in result.get("metadata", {}).get("type", ""))
            metrics["experience_ratio"] = experience_count / len(results) if results else 0
        
        return metrics
    
    def _generate_validation_report(
        self,
        first_result: RetrievalValidationResult,
        second_result: Optional[RetrievalValidationResult],
        total_duration: float,
    ) -> DoubleRetrievalValidationReport:
        """生成验证报告"""
        # 计算整体状态
        statuses = [first_result.validation_status]
        if second_result:
            statuses.append(second_result.validation_status)
        
        if all(s == ValidationStatus.PASSED for s in statuses):
            overall_status = ValidationStatus.PASSED
        elif any(s == ValidationStatus.FAILED for s in statuses):
            overall_status = ValidationStatus.FAILED
        else:
            overall_status = ValidationStatus.WARNING
        
        # 性能指标
        performance_metrics = {
            "total_duration": total_duration,
            "first_retrieval_duration": first_result.duration_seconds,
            "second_retrieval_duration": second_result.duration_seconds if second_result else 0,
        }
        
        # 验证摘要
        validation_summary = {
            "first_retrieval_passed": first_result.validation_status == ValidationStatus.PASSED,
            "second_retrieval_passed": second_result.validation_status == ValidationStatus.PASSED if second_result else True,
            "both_retrievals_passed": overall_status == ValidationStatus.PASSED,
        }
        
        return DoubleRetrievalValidationReport(
            first_retrieval_result=first_result,
            second_retrieval_result=second_result,
            overall_status=overall_status,
            performance_metrics=performance_metrics,
            validation_summary=validation_summary,
        )
    
    async def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        if not self.validation_history:
            return {"total_validations": 0}
        
        total = len(self.validation_history)
        passed = sum(1 for r in self.validation_history 
                    if r.overall_status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.validation_history 
                    if r.overall_status == ValidationStatus.FAILED)
        warning = sum(1 for r in self.validation_history 
                     if r.overall_status == ValidationStatus.WARNING)
        
        return {
            "total_validations": total,
            "passed_validations": passed,
            "failed_validations": failed,
            "warning_validations": warning,
            "pass_rate": passed / total * 100 if total > 0 else 0,
            "last_validation_time": self.validation_history[-1].timestamp,
        }


# 全局验证器实例
_double_retrieval_validator: Optional[RAGDoubleRetrievalValidator] = None


def get_double_retrieval_validator(rag_service: Any = None) -> RAGDoubleRetrievalValidator:
    """获取双检索验证器实例（单例模式）"""
    global _double_retrieval_validator
    
    if _double_retrieval_validator is None:
        if rag_service is None:
            from core.rag_service_adapter import RAGServiceAdapter
            rag_service = RAGServiceAdapter()
        
        _double_retrieval_validator = RAGDoubleRetrievalValidator(rag_service)
    
    return _double_retrieval_validator