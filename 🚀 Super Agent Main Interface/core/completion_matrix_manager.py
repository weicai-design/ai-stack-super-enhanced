#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局完成度矩阵管理器
P2-301: 建立"功能×需求"矩阵，标注实现/缺失/证据链接；与八项指标对应
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .database_persistence import DatabasePersistence, get_persistence
from .evidence_recorder import EvidenceRecorder, EvidenceType, get_evidence_recorder

logger = logging.getLogger(__name__)


class CompletionStatus(str, Enum):
    """完成状态"""
    IMPLEMENTED = "implemented"  # 已实现
    MISSING = "missing"  # 缺失
    PARTIAL = "partial"  # 部分实现
    PENDING = "pending"  # 待实现
    DEPRECATED = "deprecated"  # 已废弃


class EvidenceCategory(str, Enum):
    """证据类别"""
    CODE = "code"  # 代码证据
    TEST = "test"  # 测试证据
    DOCUMENTATION = "documentation"  # 文档证据
    SCREENSHOT = "screenshot"  # 截图证据
    LOG = "log"  # 运行日志
    CI_OUTPUT = "ci_output"  # CI输出
    API_RESPONSE = "api_response"  # API响应
    PERFORMANCE = "performance"  # 性能数据


@dataclass
class EvidenceLink:
    """证据链接"""
    evidence_id: str
    category: EvidenceCategory
    file_path: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FunctionRequirementMapping:
    """功能×需求映射"""
    mapping_id: str
    function_id: str
    function_name: str
    requirement_id: str
    requirement_name: str
    status: CompletionStatus
    completion_percentage: float = 0.0  # 完成百分比 0-100
    evidence_links: List[EvidenceLink] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["evidence_links"] = [link.to_dict() for link in self.evidence_links]
        return data


class EightMetrics(str, Enum):
    """八项指标"""
    FUNCTIONALITY = "functionality"  # 功能性
    RELIABILITY = "reliability"  # 可靠性
    USABILITY = "usability"  # 可用性
    EFFICIENCY = "efficiency"  # 效率
    MAINTAINABILITY = "maintainability"  # 可维护性
    PORTABILITY = "portability"  # 可移植性
    SECURITY = "security"  # 安全性
    COMPLIANCE = "compliance"  # 合规性


@dataclass
class MetricScore:
    """指标评分"""
    metric: EightMetrics
    score: float  # 0-100
    evidence_links: List[EvidenceLink] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["metric"] = self.metric.value
        data["evidence_links"] = [link.to_dict() for link in self.evidence_links]
        return data


@dataclass
class CompletionMatrix:
    """完成度矩阵"""
    matrix_id: str
    function_id: str
    function_name: str
    requirement_id: str
    requirement_name: str
    status: CompletionStatus
    completion_percentage: float
    metric_scores: Dict[str, MetricScore] = field(default_factory=dict)  # 八项指标评分
    evidence_links: List[EvidenceLink] = field(default_factory=list)
    notes: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["metric_scores"] = {
            k: v.to_dict() for k, v in self.metric_scores.items()
        }
        data["evidence_links"] = [link.to_dict() for link in self.evidence_links]
        return data


class CompletionMatrixManager:
    """
    全局完成度矩阵管理器
    
    功能：
    1. 管理功能×需求矩阵
    2. 标注实现/缺失/证据链接
    3. 与八项指标对应
    4. 提供完成度确认
    """
    
    def __init__(
        self,
        persistence: Optional[DatabasePersistence] = None,
        evidence_recorder: Optional[EvidenceRecorder] = None,
    ):
        self.persistence = persistence or get_persistence()
        self.evidence_recorder = evidence_recorder or get_evidence_recorder()
        
        self.table_name = "completion_matrix"
        self.mapping_table = "function_requirement_mapping"
        
        # 内存缓存
        self.matrices: Dict[str, CompletionMatrix] = {}
        self.mappings: Dict[str, FunctionRequirementMapping] = {}
        
        # 加载现有数据
        self._load_existing_data()
        
        logger.info("全局完成度矩阵管理器初始化完成")
    
    def _load_existing_data(self):
        """加载现有数据"""
        try:
            # 加载矩阵数据
            records = self.persistence.query(
                table_name=self.table_name,
                limit=10000,
            )
            for record in records:
                matrix_id = record.get("matrix_id")
                if matrix_id:
                    matrix = self._deserialize_matrix(record)
                    self.matrices[matrix_id] = matrix
            
            # 加载映射数据
            records = self.persistence.query(
                table_name=self.mapping_table,
                limit=10000,
            )
            for record in records:
                mapping_id = record.get("mapping_id")
                if mapping_id:
                    mapping = self._deserialize_mapping(record)
                    self.mappings[mapping_id] = mapping
        except Exception as e:
            logger.warning(f"加载现有数据失败: {e}")
    
    def create_or_update_matrix(
        self,
        function_id: str,
        function_name: str,
        requirement_id: str,
        requirement_name: str,
        status: CompletionStatus,
        completion_percentage: float = 0.0,
        evidence_links: Optional[List[EvidenceLink]] = None,
        metric_scores: Optional[Dict[str, MetricScore]] = None,
        notes: Optional[str] = None,
    ) -> CompletionMatrix:
        """
        创建或更新完成度矩阵
        
        Args:
            function_id: 功能ID
            function_name: 功能名称
            requirement_id: 需求ID
            requirement_name: 需求名称
            status: 完成状态
            completion_percentage: 完成百分比
            evidence_links: 证据链接列表
            metric_scores: 八项指标评分
            notes: 备注
            
        Returns:
            完成度矩阵
        """
        # 查找现有矩阵
        matrix_id = None
        for mid, matrix in self.matrices.items():
            if (matrix.function_id == function_id and 
                matrix.requirement_id == requirement_id):
                matrix_id = mid
                break
        
        if not matrix_id:
            matrix_id = f"matrix_{uuid4()}"
        
        # 创建或更新矩阵
        matrix = CompletionMatrix(
            matrix_id=matrix_id,
            function_id=function_id,
            function_name=function_name,
            requirement_id=requirement_id,
            requirement_name=requirement_name,
            status=status,
            completion_percentage=completion_percentage,
            evidence_links=evidence_links or [],
            metric_scores=metric_scores or {},
            notes=notes,
            updated_at=datetime.utcnow().isoformat() + "Z",
        )
        
        self.matrices[matrix_id] = matrix
        
        # 持久化
        self._persist_matrix(matrix)
        
        return matrix
    
    def add_evidence_link(
        self,
        function_id: str,
        requirement_id: str,
        evidence_link: EvidenceLink,
    ) -> bool:
        """
        添加证据链接
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            evidence_link: 证据链接
            
        Returns:
            是否成功
        """
        # 查找矩阵
        matrix = None
        for m in self.matrices.values():
            if m.function_id == function_id and m.requirement_id == requirement_id:
                matrix = m
                break
        
        if not matrix:
            return False
        
        # 添加证据链接
        matrix.evidence_links.append(evidence_link)
        matrix.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 持久化
        self._persist_matrix(matrix)
        
        return True
    
    def update_metric_score(
        self,
        function_id: str,
        requirement_id: str,
        metric: EightMetrics,
        score: float,
        evidence_links: Optional[List[EvidenceLink]] = None,
        notes: Optional[str] = None,
    ) -> bool:
        """
        更新指标评分
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            metric: 指标
            score: 评分（0-100）
            evidence_links: 证据链接
            notes: 备注
            
        Returns:
            是否成功
        """
        # 查找矩阵
        matrix = None
        for m in self.matrices.values():
            if m.function_id == function_id and m.requirement_id == requirement_id:
                matrix = m
                break
        
        if not matrix:
            return False
        
        # 更新指标评分
        metric_score = MetricScore(
            metric=metric,
            score=score,
            evidence_links=evidence_links or [],
            notes=notes,
        )
        matrix.metric_scores[metric.value] = metric_score
        matrix.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 持久化
        self._persist_matrix(matrix)
        
        return True
    
    def get_matrix(
        self,
        function_id: str,
        requirement_id: str,
    ) -> Optional[CompletionMatrix]:
        """获取完成度矩阵"""
        for matrix in self.matrices.values():
            if matrix.function_id == function_id and matrix.requirement_id == requirement_id:
                return matrix
        return None
    
    def query_matrices(
        self,
        function_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
        status: Optional[CompletionStatus] = None,
        min_completion: Optional[float] = None,
        limit: int = 100,
    ) -> List[CompletionMatrix]:
        """
        查询完成度矩阵
        
        Args:
            function_id: 功能ID
            requirement_id: 需求ID
            status: 状态
            min_completion: 最小完成度
            limit: 返回数量限制
            
        Returns:
            完成度矩阵列表
        """
        results = []
        
        for matrix in self.matrices.values():
            # 过滤条件
            if function_id and matrix.function_id != function_id:
                continue
            if requirement_id and matrix.requirement_id != requirement_id:
                continue
            if status and matrix.status != status:
                continue
            if min_completion and matrix.completion_percentage < min_completion:
                continue
            
            results.append(matrix)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_completion_summary(
        self,
        function_id: Optional[str] = None,
        requirement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取完成度摘要
        
        Args:
            function_id: 功能ID（可选）
            requirement_id: 需求ID（可选）
            
        Returns:
            完成度摘要
        """
        matrices = self.query_matrices(
            function_id=function_id,
            requirement_id=requirement_id,
            limit=10000,
        )
        
        total = len(matrices)
        implemented = sum(1 for m in matrices if m.status == CompletionStatus.IMPLEMENTED)
        missing = sum(1 for m in matrices if m.status == CompletionStatus.MISSING)
        partial = sum(1 for m in matrices if m.status == CompletionStatus.PARTIAL)
        
        avg_completion = sum(m.completion_percentage for m in matrices) / total if total > 0 else 0
        
        # 八项指标平均分
        metric_averages = {}
        for metric in EightMetrics:
            scores = [
                m.metric_scores.get(metric.value, MetricScore(metric=metric, score=0)).score
                for m in matrices
                if metric.value in m.metric_scores
            ]
            metric_averages[metric.value] = sum(scores) / len(scores) if scores else 0
        
        return {
            "total": total,
            "by_status": {
                "implemented": implemented,
                "missing": missing,
                "partial": partial,
                "pending": sum(1 for m in matrices if m.status == CompletionStatus.PENDING),
            },
            "average_completion": avg_completion,
            "completion_rate": (implemented / total * 100) if total > 0 else 0,
            "metric_averages": metric_averages,
        }
    
    def generate_matrix_report(
        self,
        output_format: str = "json",  # json, html, excel
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        生成矩阵报告
        
        Args:
            output_format: 输出格式
            output_path: 输出路径
            
        Returns:
            输出文件路径
        """
        if output_path is None:
            project_root = Path(__file__).parent.parent.parent
            output_path = project_root / "artifacts" / "evidence" / "completion_matrix"
            output_path.mkdir(parents=True, exist_ok=True)
        
        output_path = Path(output_path)
        
        if output_format == "json":
            file_path = output_path / f"completion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            data = {
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "summary": self.get_completion_summary(),
                "matrices": [m.to_dict() for m in self.matrices.values()],
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return file_path
        elif output_format == "html":
            # TODO: 生成HTML报告
            file_path = output_path / f"completion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_content = self._generate_html_report()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            return file_path
        else:
            raise ValueError(f"不支持的输出格式: {output_format}")
    
    def _generate_html_report(self) -> str:
        """生成HTML报告"""
        summary = self.get_completion_summary()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>全局完成度矩阵报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .status-implemented {{ color: green; font-weight: bold; }}
        .status-missing {{ color: red; font-weight: bold; }}
        .status-partial {{ color: orange; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>全局完成度矩阵报告</h1>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>摘要</h2>
    <ul>
        <li>总计: {summary['total']}</li>
        <li>已实现: {summary['by_status']['implemented']}</li>
        <li>缺失: {summary['by_status']['missing']}</li>
        <li>部分实现: {summary['by_status']['partial']}</li>
        <li>平均完成度: {summary['average_completion']:.2f}%</li>
        <li>完成率: {summary['completion_rate']:.2f}%</li>
    </ul>
    
    <h2>八项指标平均分</h2>
    <table>
        <tr>
            <th>指标</th>
            <th>平均分</th>
        </tr>
"""
        for metric, score in summary['metric_averages'].items():
            html += f"""
        <tr>
            <td>{metric}</td>
            <td>{score:.2f}</td>
        </tr>
"""
        html += """
    </table>
    
    <h2>完成度矩阵</h2>
    <table>
        <tr>
            <th>功能ID</th>
            <th>功能名称</th>
            <th>需求ID</th>
            <th>需求名称</th>
            <th>状态</th>
            <th>完成度</th>
            <th>证据数量</th>
        </tr>
"""
        for matrix in sorted(self.matrices.values(), key=lambda x: x.function_id):
            status_class = f"status-{matrix.status.value}"
            html += f"""
        <tr>
            <td>{matrix.function_id}</td>
            <td>{matrix.function_name}</td>
            <td>{matrix.requirement_id}</td>
            <td>{matrix.requirement_name}</td>
            <td class="{status_class}">{matrix.status.value}</td>
            <td>{matrix.completion_percentage:.2f}%</td>
            <td>{len(matrix.evidence_links)}</td>
        </tr>
"""
        html += """
    </table>
</body>
</html>
"""
        return html
    
    def _persist_matrix(self, matrix: CompletionMatrix):
        """持久化矩阵"""
        try:
            self.persistence.save(
                table_name=self.table_name,
                data=matrix.to_dict(),
                record_id=matrix.matrix_id,
                metadata={
                    "function_id": matrix.function_id,
                    "requirement_id": matrix.requirement_id,
                    "status": matrix.status.value,
                },
            )
        except Exception as e:
            logger.error(f"持久化矩阵失败: {e}")
    
    def _deserialize_matrix(self, record: Dict[str, Any]) -> CompletionMatrix:
        """反序列化矩阵"""
        metric_scores = {}
        for metric_key, score_data in record.get("metric_scores", {}).items():
            metric = EightMetrics(metric_key)
            metric_scores[metric_key] = MetricScore(
                metric=metric,
                score=score_data.get("score", 0),
                evidence_links=[
                    EvidenceLink(**link) for link in score_data.get("evidence_links", [])
                ],
                notes=score_data.get("notes"),
            )
        
        evidence_links = [
            EvidenceLink(**link) for link in record.get("evidence_links", [])
        ]
        
        return CompletionMatrix(
            matrix_id=record.get("matrix_id"),
            function_id=record.get("function_id"),
            function_name=record.get("function_name"),
            requirement_id=record.get("requirement_id"),
            requirement_name=record.get("requirement_name"),
            status=CompletionStatus(record.get("status", "pending")),
            completion_percentage=record.get("completion_percentage", 0),
            metric_scores=metric_scores,
            evidence_links=evidence_links,
            notes=record.get("notes"),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
        )
    
    def _deserialize_mapping(self, record: Dict[str, Any]) -> FunctionRequirementMapping:
        """反序列化映射"""
        evidence_links = [
            EvidenceLink(**link) for link in record.get("evidence_links", [])
        ]
        
        return FunctionRequirementMapping(
            mapping_id=record.get("mapping_id"),
            function_id=record.get("function_id"),
            function_name=record.get("function_name"),
            requirement_id=record.get("requirement_id"),
            requirement_name=record.get("requirement_name"),
            status=CompletionStatus(record.get("status", "pending")),
            completion_percentage=record.get("completion_percentage", 0),
            evidence_links=evidence_links,
            notes=record.get("notes"),
            created_at=record.get("created_at"),
            updated_at=record.get("updated_at"),
        )


_completion_matrix_manager: Optional[CompletionMatrixManager] = None


def get_completion_matrix_manager() -> CompletionMatrixManager:
    """获取全局完成度矩阵管理器实例"""
    global _completion_matrix_manager
    if _completion_matrix_manager is None:
        _completion_matrix_manager = CompletionMatrixManager()
    return _completion_matrix_manager

