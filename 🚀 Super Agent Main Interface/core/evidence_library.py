#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
证据库系统
P2-301: 提供运行日志、测试截图、CI输出，支撑"完成度确认"
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .database_persistence import DatabasePersistence, get_persistence
from .evidence_recorder import EvidenceRecorder, EvidenceType, get_evidence_recorder
from .completion_matrix_manager import (
    CompletionMatrixManager,
    get_completion_matrix_manager,
    EvidenceLink,
    EvidenceCategory,
)

logger = logging.getLogger(__name__)


class EvidenceSource(str, Enum):
    """证据来源"""
    RUNTIME_LOG = "runtime_log"  # 运行日志
    TEST_SCREENSHOT = "test_screenshot"  # 测试截图
    CI_OUTPUT = "ci_output"  # CI输出
    TEST_REPORT = "test_report"  # 测试报告
    API_RESPONSE = "api_response"  # API响应
    PERFORMANCE_METRIC = "performance_metric"  # 性能指标
    CODE_COVERAGE = "code_coverage"  # 代码覆盖率
    SECURITY_SCAN = "security_scan"  # 安全扫描


@dataclass
class EvidenceItem:
    """证据项"""
    evidence_id: str
    function_id: str
    requirement_id: str
    source: EvidenceSource
    category: EvidenceCategory
    file_path: Optional[str] = None
    url: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["source"] = self.source.value
        data["category"] = self.category.value
        return data


class EvidenceLibrary:
    """
    证据库系统
    
    功能：
    1. 存储运行日志
    2. 存储测试截图
    3. 存储CI输出
    4. 关联完成度矩阵
    5. 提供证据查询
    """
    
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        evidence_recorder: Optional[EvidenceRecorder] = None,
        completion_matrix_manager: Optional[CompletionMatrixManager] = None,
        evidence_dir: Optional[Path] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.evidence_recorder = evidence_recorder or get_evidence_recorder()
        self.completion_matrix_manager = completion_matrix_manager or get_completion_matrix_manager()
        
        # 证据存储目录
        if evidence_dir is None:
            project_root = Path(__file__).parent.parent.parent
            evidence_dir = project_root / "artifacts" / "evidence" / "library"
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        self.logs_dir = self.evidence_dir / "logs"
        self.screenshots_dir = self.evidence_dir / "screenshots"
        self.ci_output_dir = self.evidence_dir / "ci"
        self.test_reports_dir = self.evidence_dir / "test_reports"
        
        for dir_path in [self.logs_dir, self.screenshots_dir, self.ci_output_dir, self.test_reports_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.table_name = "evidence_library"
        
        logger.info(f"证据库系统已初始化，存储目录: {self.evidence_dir}")
    
    def store_runtime_log(
        self,
        function_id: str,
        requirement_id: str,
        log_content: str,
        log_file_path: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceItem:
        """
        存储运行日志
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            log_content: 日志内容
            log_file_path: 日志文件路径（可选）
            metadata: 元数据
            
        Returns:
            证据项
        """
        evidence_id = f"log_{uuid4()}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 保存日志文件
        if log_file_path:
            # 复制现有文件
            source_path = Path(log_file_path)
            if source_path.exists():
                target_path = self.logs_dir / f"{function_id}_{requirement_id}_{timestamp}.log"
                shutil.copy2(source_path, target_path)
                file_path = str(target_path)
            else:
                file_path = None
        else:
            # 创建新文件
            target_path = self.logs_dir / f"{function_id}_{requirement_id}_{timestamp}.log"
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(log_content)
            file_path = str(target_path)
        
        # 创建证据项
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            function_id=function_id,
            requirement_id=requirement_id,
            source=EvidenceSource.RUNTIME_LOG,
            category=EvidenceCategory.LOG,
            file_path=file_path,
            content={"log_length": len(log_content)},
            description=f"运行日志: {function_id}/{requirement_id}",
            metadata=metadata or {},
        )
        
        # 持久化
        self._persist_evidence(evidence)
        
        # 关联到完成度矩阵
        self._link_to_matrix(function_id, requirement_id, evidence)
        
        return evidence
    
    def store_test_screenshot(
        self,
        function_id: str,
        requirement_id: str,
        screenshot_path: str,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceItem:
        """
        存储测试截图
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            screenshot_path: 截图文件路径
            description: 描述
            metadata: 元数据
            
        Returns:
            证据项
        """
        evidence_id = f"screenshot_{uuid4()}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 复制截图文件
        source_path = Path(screenshot_path)
        if not source_path.exists():
            raise FileNotFoundError(f"截图文件不存在: {screenshot_path}")
        
        file_ext = source_path.suffix
        target_path = self.screenshots_dir / f"{function_id}_{requirement_id}_{timestamp}{file_ext}"
        shutil.copy2(source_path, target_path)
        
        # 创建证据项
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            function_id=function_id,
            requirement_id=requirement_id,
            source=EvidenceSource.TEST_SCREENSHOT,
            category=EvidenceCategory.SCREENSHOT,
            file_path=str(target_path),
            description=description or f"测试截图: {function_id}/{requirement_id}",
            metadata=metadata or {},
        )
        
        # 持久化
        self._persist_evidence(evidence)
        
        # 关联到完成度矩阵
        self._link_to_matrix(function_id, requirement_id, evidence)
        
        return evidence
    
    def store_ci_output(
        self,
        function_id: str,
        requirement_id: str,
        ci_output_path: str,
        ci_type: str = "test",  # test, build, deploy, etc.
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceItem:
        """
        存储CI输出
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            ci_output_path: CI输出文件路径
            ci_type: CI类型
            metadata: 元数据
            
        Returns:
            证据项
        """
        evidence_id = f"ci_{uuid4()}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 复制CI输出文件
        source_path = Path(ci_output_path)
        if not source_path.exists():
            raise FileNotFoundError(f"CI输出文件不存在: {ci_output_path}")
        
        file_ext = source_path.suffix if source_path.suffix else ".txt"
        target_path = self.ci_output_dir / f"{function_id}_{requirement_id}_{ci_type}_{timestamp}{file_ext}"
        
        if source_path.is_file():
            shutil.copy2(source_path, target_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        
        # 创建证据项
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            function_id=function_id,
            requirement_id=requirement_id,
            source=EvidenceSource.CI_OUTPUT,
            category=EvidenceCategory.CI_OUTPUT,
            file_path=str(target_path),
            description=f"CI输出 ({ci_type}): {function_id}/{requirement_id}",
            metadata={
                "ci_type": ci_type,
                **(metadata or {}),
            },
        )
        
        # 持久化
        self._persist_evidence(evidence)
        
        # 关联到完成度矩阵
        self._link_to_matrix(function_id, requirement_id, evidence)
        
        return evidence
    
    def store_test_report(
        self,
        function_id: str,
        requirement_id: str,
        test_report_path: str,
        test_result: str = "pass",  # pass, fail, error
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EvidenceItem:
        """
        存储测试报告
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            test_report_path: 测试报告文件路径
            test_result: 测试结果
            metadata: 元数据
            
        Returns:
            证据项
        """
        evidence_id = f"test_{uuid4()}"
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        # 复制测试报告文件
        source_path = Path(test_report_path)
        if not source_path.exists():
            raise FileNotFoundError(f"测试报告文件不存在: {test_report_path}")
        
        file_ext = source_path.suffix if source_path.suffix else ".xml"
        target_path = self.test_reports_dir / f"{function_id}_{requirement_id}_{timestamp}{file_ext}"
        
        if source_path.is_file():
            shutil.copy2(source_path, target_path)
        elif source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        
        # 创建证据项
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            function_id=function_id,
            requirement_id=requirement_id,
            source=EvidenceSource.TEST_REPORT,
            category=EvidenceCategory.TEST,
            file_path=str(target_path),
            description=f"测试报告 ({test_result}): {function_id}/{requirement_id}",
            metadata={
                "test_result": test_result,
                **(metadata or {}),
            },
        )
        
        # 持久化
        self._persist_evidence(evidence)
        
        # 关联到完成度矩阵
        self._link_to_matrix(function_id, requirement_id, evidence)
        
        return evidence
    
    def query_evidence(
        self,
        function_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
        source: Optional[EvidenceSource] = None,
        category: Optional[EvidenceCategory] = None,
        limit: int = 100,
    ) -> List[EvidenceItem]:
        """
        查询证据
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            source: 证据来源
            category: 证据类别
            limit: 返回数量限制
            
        Returns:
            证据项列表
        """
        filters: Dict[str, Any] = {}
        
        if function_id:
            filters["function_id"] = function_id
        if requirement_id:
            filters["requirement_id"] = requirement_id
        if source:
            filters["source"] = source.value
        if category:
            filters["category"] = category.value
        
        try:
            records = self.persistence.query(
                table_name=self.table_name,
                filters=filters or None,
                limit=limit,
                order_by="timestamp",
                order_desc=True,
            )
            
            evidence_items = []
            for record in records:
                evidence = EvidenceItem(
                    evidence_id=record.get("evidence_id"),
                    function_id=record.get("function_id"),
                    requirement_id=record.get("requirement_id"),
                    source=EvidenceSource(record.get("source")),
                    category=EvidenceCategory(record.get("category")),
                    file_path=record.get("file_path"),
                    url=record.get("url"),
                    content=record.get("content"),
                    description=record.get("description"),
                    metadata=record.get("metadata", {}),
                    timestamp=record.get("timestamp"),
                )
                evidence_items.append(evidence)
            
            return evidence_items
        except Exception as e:
            logger.error(f"查询证据失败: {e}")
            return []
    
    def get_evidence_summary(
        self,
        function_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取证据摘要
        
        Args:
            function_id: 功能ID（可选）
            requirement_id: 需求ID（可选）
            
        Returns:
            证据摘要
        """
        evidence_items = self.query_evidence(
            function_id=function_id,
            requirement_id=requirement_id,
            limit=10000,
        )
        
        summary = {
            "total": len(evidence_items),
            "by_source": {},
            "by_category": {},
            "recent_evidence": [],
        }
        
        for evidence in evidence_items:
            # 按来源统计
            source = evidence.source.value
            summary["by_source"][source] = summary["by_source"].get(source, 0) + 1
            
            # 按类别统计
            category = evidence.category.value
            summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
        
        # 最近的证据
        summary["recent_evidence"] = [
            e.to_dict() for e in sorted(
                evidence_items,
                key=lambda x: x.timestamp,
                reverse=True
            )[:10]
        ]
        
        return summary
    
    def _persist_evidence(self, evidence: EvidenceItem):
        """持久化证据"""
        try:
            self.persistence.save(
                table_name=self.table_name,
                data=evidence.to_dict(),
                record_id=evidence.evidence_id,
                metadata={
                    "function_id": evidence.function_id,
                    "requirement_id": evidence.requirement_id,
                    "source": evidence.source.value,
                    "category": evidence.category.value,
                },
            )
        except Exception as e:
            logger.error(f"持久化证据失败: {e}")
    
    def _link_to_matrix(
        self,
        function_id: str,
        requirement_id: str,
        evidence: EvidenceItem,
    ):
        """关联到完成度矩阵"""
        try:
            # 创建证据链接
            evidence_link = EvidenceLink(
                evidence_id=evidence.evidence_id,
                category=evidence.category,
                file_path=evidence.file_path,
                url=evidence.url,
                description=evidence.description,
                timestamp=evidence.timestamp,
            )
            
            # 添加到完成度矩阵
            self.completion_matrix_manager.add_evidence_link(
                function_id=function_id,
                requirement_id=requirement_id,
                evidence_link=evidence_link,
            )
        except Exception as e:
            logger.warning(f"关联到完成度矩阵失败: {e}")


_evidence_library: Optional[EvidenceLibrary] = None


def get_evidence_library() -> EvidenceLibrary:
    """获取证据库实例"""
    global _evidence_library
    if _evidence_library is None:
        _evidence_library = EvidenceLibrary()
    return _evidence_library

