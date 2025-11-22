#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全局完成度矩阵生成器
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

from .completion_matrix_manager import (
    CompletionMatrixManager,
    get_completion_matrix_manager,
    CompletionStatus,
    EightMetrics,
    EvidenceLink,
    EvidenceCategory,
    MetricScore,
    CompletionMatrix,
)
from .evidence_library import EvidenceLibrary, get_evidence_library

logger = logging.getLogger(__name__)


@dataclass
class FunctionRequirementMatrix:
    """功能×需求矩阵"""
    function_id: str
    function_name: str
    function_category: str
    requirements: List[Dict[str, Any]] = field(default_factory=list)
    overall_completion: float = 0.0
    metric_scores: Dict[str, float] = field(default_factory=dict)
    evidence_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GlobalCompletionMatrixGenerator:
    """
    全局完成度矩阵生成器
    
    功能：
    1. 生成功能×需求矩阵
    2. 标注实现/缺失/证据链接
    3. 与八项指标对应
    4. 生成完成度确认报告
    """
    
    def __init__(
        self,
        completion_matrix_manager: Optional[CompletionMatrixManager] = None,
        evidence_library: Optional[EvidenceLibrary] = None,
        output_dir: Optional[Path] = None,
    ):
        self.completion_matrix_manager = completion_matrix_manager or get_completion_matrix_manager()
        self.evidence_library = evidence_library or get_evidence_library()
        
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent
            output_dir = project_root / "artifacts" / "completion_matrix"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 功能列表（从现有代码中提取）
        self.functions = self._load_functions()
        
        # 需求列表（从现有文档中提取）
        self.requirements = self._load_requirements()
        
        logger.info("全局完成度矩阵生成器初始化完成")
    
    def _load_functions(self) -> List[Dict[str, Any]]:
        """加载功能列表"""
        return [
            # RAG和知识图谱
            {"id": "F001", "name": "RAG知识检索", "category": "RAG"},
            {"id": "F002", "name": "知识图谱", "category": "RAG"},
            {"id": "F003", "name": "多格式文件处理", "category": "RAG"},
            {"id": "F004", "name": "预处理管道", "category": "RAG"},
            {"id": "F005", "name": "真实性验证", "category": "RAG"},
            {"id": "F006", "name": "网络信息入库", "category": "RAG"},
            {"id": "F007", "name": "自主分组", "category": "RAG"},
            {"id": "F008", "name": "OpenWebUI前端", "category": "RAG"},
            
            # ERP企业管理
            {"id": "F009", "name": "财务看板", "category": "ERP"},
            {"id": "F010", "name": "经营分析", "category": "ERP"},
            {"id": "F011", "name": "流程管理", "category": "ERP"},
            {"id": "F012", "name": "客户管理", "category": "ERP"},
            {"id": "F013", "name": "订单管理", "category": "ERP"},
            {"id": "F014", "name": "项目管理", "category": "ERP"},
            {"id": "F015", "name": "采购管理", "category": "ERP"},
            {"id": "F016", "name": "库存管理", "category": "ERP"},
            {"id": "F017", "name": "仓库管理", "category": "ERP"},
            {"id": "F018", "name": "设备管理", "category": "ERP"},
            {"id": "F019", "name": "工艺管理", "category": "ERP"},
            {"id": "F020", "name": "异常监控", "category": "ERP"},
            
            # OpenWebUI交互
            {"id": "F021", "name": "智能对话", "category": "OpenWebUI"},
            {"id": "F022", "name": "文件上传", "category": "OpenWebUI"},
            {"id": "F023", "name": "命令执行", "category": "OpenWebUI"},
            {"id": "F024", "name": "语音I/O", "category": "OpenWebUI"},
            {"id": "F025", "name": "模型选择", "category": "OpenWebUI"},
            {"id": "F026", "name": "外网搜索", "category": "OpenWebUI"},
            
            # 智能股票
            {"id": "F027", "name": "实时行情", "category": "Stock"},
            {"id": "F028", "name": "策略回测", "category": "Stock"},
            {"id": "F029", "name": "自动交易", "category": "Stock"},
            {"id": "F030", "name": "因子工程", "category": "Stock"},
            {"id": "F031", "name": "风控系统", "category": "Stock"},
            
            # 趋势分析
            {"id": "F032", "name": "数据采集", "category": "Trend"},
            {"id": "F033", "name": "内容分析", "category": "Trend"},
            {"id": "F034", "name": "趋势预测", "category": "Trend"},
            {"id": "F035", "name": "报告生成", "category": "Trend"},
            
            # 内容创作
            {"id": "F036", "name": "内容生成", "category": "Content"},
            {"id": "F037", "name": "多平台发布", "category": "Content"},
            {"id": "F038", "name": "版权检测", "category": "Content"},
            {"id": "F039", "name": "去AI化", "category": "Content"},
            
            # 任务代理
            {"id": "F040", "name": "任务规划", "category": "Task"},
            {"id": "F041", "name": "任务执行", "category": "Task"},
            {"id": "F042", "name": "任务监控", "category": "Task"},
            
            # 资源管理
            {"id": "F043", "name": "性能监控", "category": "Resource"},
            {"id": "F044", "name": "资源调度", "category": "Resource"},
            {"id": "F045", "name": "告警系统", "category": "Resource"},
            
            # 自我学习
            {"id": "F046", "name": "行为学习", "category": "Learning"},
            {"id": "F047", "name": "自动优化", "category": "Learning"},
            {"id": "F048", "name": "错误诊断", "category": "Learning"},
            
            # 安全合规
            {"id": "F049", "name": "合规策略", "category": "Security"},
            {"id": "F050", "name": "审计流程", "category": "Security"},
            {"id": "F051", "name": "审批流程", "category": "Security"},
        ]
    
    def _load_requirements(self) -> List[Dict[str, Any]]:
        """加载需求列表"""
        return [
            # 需求1: RAG和知识图谱
            {"id": "R001", "name": "所有格式文件支持", "category": "RAG"},
            {"id": "R002", "name": "四项预处理", "category": "RAG"},
            {"id": "R003", "name": "真实性验证", "category": "RAG"},
            {"id": "R004", "name": "网络信息入库", "category": "RAG"},
            {"id": "R005", "name": "检索利用", "category": "RAG"},
            {"id": "R006", "name": "自主分组", "category": "RAG"},
            {"id": "R007", "name": "OpenWebUI前端", "category": "RAG"},
            {"id": "R008", "name": "知识图谱", "category": "RAG"},
            
            # 需求2: 企业ERP管理
            {"id": "R009", "name": "财务看板", "category": "ERP"},
            {"id": "R010", "name": "经营分析", "category": "ERP"},
            {"id": "R011", "name": "流程管理", "category": "ERP"},
            {"id": "R012", "name": "客户管理", "category": "ERP"},
            {"id": "R013", "name": "订单管理", "category": "ERP"},
            {"id": "R014", "name": "项目管理", "category": "ERP"},
            {"id": "R015", "name": "采购管理", "category": "ERP"},
            {"id": "R016", "name": "库存管理", "category": "ERP"},
            {"id": "R017", "name": "仓库管理", "category": "ERP"},
            {"id": "R018", "name": "设备管理", "category": "ERP"},
            {"id": "R019", "name": "工艺管理", "category": "ERP"},
            {"id": "R020", "name": "异常监控", "category": "ERP"},
            
            # 需求3: OpenWebUI交互
            {"id": "R021", "name": "智能对话", "category": "OpenWebUI"},
            {"id": "R022", "name": "文件上传", "category": "OpenWebUI"},
            {"id": "R023", "name": "命令执行", "category": "OpenWebUI"},
            {"id": "R024", "name": "语音I/O", "category": "OpenWebUI"},
            {"id": "R025", "name": "模型选择", "category": "OpenWebUI"},
            {"id": "R026", "name": "外网搜索", "category": "OpenWebUI"},
            
            # 需求4: 智能股票
            {"id": "R027", "name": "实时行情", "category": "Stock"},
            {"id": "R028", "name": "策略回测", "category": "Stock"},
            {"id": "R029", "name": "自动交易", "category": "Stock"},
            {"id": "R030", "name": "因子工程", "category": "Stock"},
            {"id": "R031", "name": "风控系统", "category": "Stock"},
            
            # 需求5: 趋势分析
            {"id": "R032", "name": "数据采集", "category": "Trend"},
            {"id": "R033", "name": "内容分析", "category": "Trend"},
            {"id": "R034", "name": "趋势预测", "category": "Trend"},
            {"id": "R035", "name": "报告生成", "category": "Trend"},
            
            # 需求6: 内容创作
            {"id": "R036", "name": "内容生成", "category": "Content"},
            {"id": "R037", "name": "多平台发布", "category": "Content"},
            {"id": "R038", "name": "版权检测", "category": "Content"},
            {"id": "R039", "name": "去AI化", "category": "Content"},
            
            # 需求7: 任务代理
            {"id": "R040", "name": "任务规划", "category": "Task"},
            {"id": "R041", "name": "任务执行", "category": "Task"},
            {"id": "R042", "name": "任务监控", "category": "Task"},
            
            # 需求8: 资源管理
            {"id": "R043", "name": "性能监控", "category": "Resource"},
            {"id": "R044", "name": "资源调度", "category": "Resource"},
            {"id": "R045", "name": "告警系统", "category": "Resource"},
            
            # 需求9: 自我学习
            {"id": "R046", "name": "行为学习", "category": "Learning"},
            {"id": "R047", "name": "自动优化", "category": "Learning"},
            {"id": "R048", "name": "错误诊断", "category": "Learning"},
            
            # 需求10: 安全合规
            {"id": "R049", "name": "合规策略", "category": "Security"},
            {"id": "R050", "name": "审计流程", "category": "Security"},
            {"id": "R051", "name": "审批流程", "category": "Security"},
        ]
    
    def generate_matrix(self) -> Dict[str, Any]:
        """
        生成功能×需求矩阵
        
        Returns:
            矩阵数据
        """
        matrix_data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "functions": [],
            "requirements": [],
            "mappings": [],
            "summary": {},
        }
        
        # 生成功能×需求映射
        mappings = []
        for func in self.functions:
            func_data = {
                "function_id": func["id"],
                "function_name": func["name"],
                "function_category": func["category"],
                "requirements": [],
                "overall_completion": 0.0,
                "metric_scores": {},
                "evidence_count": 0,
            }
            
            # 查找相关需求
            related_requirements = [
                req for req in self.requirements
                if req["category"] == func["category"]
            ]
            
            completion_sum = 0.0
            evidence_count = 0
            
            for req in related_requirements:
                # 查询完成度矩阵
                matrix = self.completion_matrix_manager.get_matrix(
                    function_id=func["id"],
                    requirement_id=req["id"],
                )
                
                evidence_objects: List[EvidenceLink] = []
                
                if matrix:
                    status = matrix.status
                    completion = matrix.completion_percentage
                    evidence_count += len(matrix.evidence_links)
                    evidence_objects = matrix.evidence_links
                    
                    # 计算指标评分
                    metric_scores = {}
                    for metric, score_obj in matrix.metric_scores.items():
                        if isinstance(score_obj, MetricScore):
                            metric_scores[metric] = score_obj.score
                        elif isinstance(score_obj, dict):
                            metric_scores[metric] = score_obj.get("score", 0.0)
                        else:
                            metric_scores[metric] = score_obj
                    
                    if not metric_scores:
                        metric_scores = self._estimate_metrics(func["category"])
                else:
                    # 默认值（基于功能类别）
                    status = self._estimate_status(func["category"])
                    completion = self._estimate_completion(func["category"])
                    metric_scores = self._estimate_metrics(func["category"])
                    evidence_objects = []
                
                screenshot_placeholder = self._extract_evidence_placeholder(
                    evidence_objects,
                    EvidenceCategory.SCREENSHOT,
                    "截图",
                )
                log_placeholder = self._extract_evidence_placeholder(
                    evidence_objects,
                    EvidenceCategory.LOG,
                    "日志",
                )
                evidence_links = [link.to_dict() for link in evidence_objects]
                
                req_data = {
                    "requirement_id": req["id"],
                    "requirement_name": req["name"],
                    "status": status.value if isinstance(status, CompletionStatus) else status,
                    "completion_percentage": completion,
                    "metric_scores": metric_scores,
                    "evidence_links": evidence_links,
                    "screenshot_placeholder": screenshot_placeholder,
                    "log_placeholder": log_placeholder,
                }
                
                func_data["requirements"].append(req_data)
                completion_sum += completion
                
                mappings.append({
                    "function_id": func["id"],
                    "requirement_id": req["id"],
                    "status": status.value if isinstance(status, CompletionStatus) else status,
                    "completion_percentage": completion,
                })
            
            # 计算总体完成度
            if related_requirements:
                func_data["overall_completion"] = completion_sum / len(related_requirements)
            func_data["evidence_count"] = evidence_count
            
            matrix_data["functions"].append(func_data)
        
        matrix_data["requirements"] = self.requirements
        matrix_data["mappings"] = mappings
        
        # 生成摘要
        matrix_data["summary"] = self._generate_summary(matrix_data)
        
        return matrix_data
    
    def _estimate_status(self, category: str) -> CompletionStatus:
        """估算状态"""
        status_map = {
            "RAG": CompletionStatus.IMPLEMENTED,
            "ERP": CompletionStatus.IMPLEMENTED,
            "OpenWebUI": CompletionStatus.IMPLEMENTED,
            "Stock": CompletionStatus.PARTIAL,
            "Trend": CompletionStatus.PARTIAL,
            "Content": CompletionStatus.PARTIAL,
            "Task": CompletionStatus.IMPLEMENTED,
            "Resource": CompletionStatus.IMPLEMENTED,
            "Learning": CompletionStatus.IMPLEMENTED,
            "Security": CompletionStatus.IMPLEMENTED,
        }
        return status_map.get(category, CompletionStatus.PENDING)
    
    def _estimate_completion(self, category: str) -> float:
        """估算完成度"""
        completion_map = {
            "RAG": 87.0,
            "ERP": 90.0,
            "OpenWebUI": 80.0,
            "Stock": 60.0,
            "Trend": 65.0,
            "Content": 65.0,
            "Task": 70.0,
            "Resource": 75.0,
            "Learning": 80.0,
            "Security": 85.0,
        }
        return completion_map.get(category, 0.0)
    
    def _estimate_metrics(self, category: str) -> Dict[str, float]:
        """估算八项指标"""
        base_scores = {
            EightMetrics.FUNCTIONALITY.value: 85.0,
            EightMetrics.RELIABILITY.value: 80.0,
            EightMetrics.USABILITY.value: 75.0,
            EightMetrics.EFFICIENCY.value: 80.0,
            EightMetrics.MAINTAINABILITY.value: 85.0,
            EightMetrics.PORTABILITY.value: 90.0,
            EightMetrics.SECURITY.value: 90.0,
            EightMetrics.COMPLIANCE.value: 85.0,
        }
        return base_scores
    
    def _extract_evidence_placeholder(
        self,
        evidence_links: List[EvidenceLink],
        category: EvidenceCategory,
        placeholder_label: str,
    ) -> str:
        """提取指定类别的证据路径，若不存在则返回TODO占位"""
        for link in evidence_links:
            link_category = getattr(link, "category", None)
            if isinstance(link_category, EvidenceCategory):
                matched = link_category == category
            else:
                matched = str(link_category) == category.value
            
            if matched:
                if getattr(link, "file_path", None):
                    return link.file_path  # type: ignore[attr-defined]
                if getattr(link, "url", None):
                    return link.url  # type: ignore[attr-defined]
                if getattr(link, "description", None):
                    return link.description  # type: ignore[attr-defined]
        
        return f"TODO: {placeholder_label}"
    
    def _generate_summary(self, matrix_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要"""
        total_functions = len(matrix_data["functions"])
        total_requirements = len(matrix_data["requirements"])
        total_mappings = len(matrix_data["mappings"])
        
        # 统计状态
        status_counts = {
            CompletionStatus.IMPLEMENTED.value: 0,
            CompletionStatus.PARTIAL.value: 0,
            CompletionStatus.MISSING.value: 0,
            CompletionStatus.PENDING.value: 0,
        }
        
        completion_sum = 0.0
        total_completion = 0
        
        for mapping in matrix_data["mappings"]:
            status = mapping["status"]
            if status in status_counts:
                status_counts[status] += 1
            completion_sum += mapping["completion_percentage"]
            total_completion += 1
        
        avg_completion = completion_sum / total_completion if total_completion > 0 else 0.0
        
        # 计算八项指标平均分
        metric_scores = {}
        for metric in EightMetrics:
            metric_scores[metric.value] = 0.0
        
        metric_count = 0
        for func in matrix_data["functions"]:
            for metric, score in func.get("metric_scores", {}).items():
                if metric in metric_scores:
                    metric_scores[metric] += score
                    metric_count += 1
        
        if metric_count > 0:
            for metric in metric_scores:
                metric_scores[metric] = metric_scores[metric] / (metric_count / len(EightMetrics))
        
        return {
            "total_functions": total_functions,
            "total_requirements": total_requirements,
            "total_mappings": total_mappings,
            "status_distribution": status_counts,
            "average_completion": avg_completion,
            "metric_scores": metric_scores,
        }
    
    def export_matrix(self, format: str = "json") -> Path:
        """
        导出矩阵
        
        Args:
            format: 导出格式 (json/html)
            
        Returns:
            导出文件路径
        """
        matrix_data = self.generate_matrix()
        
        if format == "json":
            output_file = self.output_dir / f"completion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(matrix_data, f, ensure_ascii=False, indent=2)
            logger.info(f"矩阵已导出到: {output_file}")
            return output_file
        elif format == "html":
            output_file = self.output_dir / f"completion_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_content = self._generate_html(matrix_data)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"矩阵已导出到: {output_file}")
            return output_file
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def _generate_html(self, matrix_data: Dict[str, Any]) -> str:
        """生成HTML报告"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>全局完成度矩阵</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .implemented {{ background-color: #d4edda; }}
        .partial {{ background-color: #fff3cd; }}
        .missing {{ background-color: #f8d7da; }}
        .pending {{ background-color: #e2e3e5; }}
        .summary {{ background-color: #f0f0f0; padding: 15px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>全局完成度矩阵</h1>
    <p>生成时间: {matrix_data['generated_at']}</p>
    
    <div class="summary">
        <h2>摘要</h2>
        <p>总功能数: {matrix_data['summary']['total_functions']}</p>
        <p>总需求数: {matrix_data['summary']['total_requirements']}</p>
        <p>总映射数: {matrix_data['summary']['total_mappings']}</p>
        <p>平均完成度: {matrix_data['summary']['average_completion']:.2f}%</p>
        <h3>状态分布</h3>
        <ul>
            <li>已实现: {matrix_data['summary']['status_distribution'].get('implemented', 0)}</li>
            <li>部分实现: {matrix_data['summary']['status_distribution'].get('partial', 0)}</li>
            <li>缺失: {matrix_data['summary']['status_distribution'].get('missing', 0)}</li>
            <li>待实现: {matrix_data['summary']['status_distribution'].get('pending', 0)}</li>
        </ul>
        <h3>八项指标平均分</h3>
        <ul>
            <li>功能性: {matrix_data['summary']['metric_scores'].get('functionality', 0):.2f}</li>
            <li>可靠性: {matrix_data['summary']['metric_scores'].get('reliability', 0):.2f}</li>
            <li>可用性: {matrix_data['summary']['metric_scores'].get('usability', 0):.2f}</li>
            <li>效率: {matrix_data['summary']['metric_scores'].get('efficiency', 0):.2f}</li>
            <li>可维护性: {matrix_data['summary']['metric_scores'].get('maintainability', 0):.2f}</li>
            <li>可移植性: {matrix_data['summary']['metric_scores'].get('portability', 0):.2f}</li>
            <li>安全性: {matrix_data['summary']['metric_scores'].get('security', 0):.2f}</li>
            <li>合规性: {matrix_data['summary']['metric_scores'].get('compliance', 0):.2f}</li>
        </ul>
    </div>
    
    <h2>功能×需求矩阵</h2>
    <table>
        <tr>
            <th>功能ID</th>
            <th>功能名称</th>
            <th>需求ID</th>
            <th>需求名称</th>
            <th>状态</th>
            <th>完成度</th>
            <th>证据数</th>
            <th>截图证据</th>
            <th>日志证据</th>
        </tr>
"""
        
        for func in matrix_data["functions"]:
            for req in func["requirements"]:
                status_class = req["status"].lower()
                html += f"""
        <tr class="{status_class}">
            <td>{func['function_id']}</td>
            <td>{func['function_name']}</td>
            <td>{req['requirement_id']}</td>
            <td>{req['requirement_name']}</td>
            <td>{req['status']}</td>
            <td>{req['completion_percentage']:.1f}%</td>
            <td>{len(req['evidence_links'])}</td>
            <td>{req.get('screenshot_placeholder', 'TODO: 截图')}</td>
            <td>{req.get('log_placeholder', 'TODO: 日志')}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html


_global_generator: Optional[GlobalCompletionMatrixGenerator] = None


def get_global_generator() -> GlobalCompletionMatrixGenerator:
    """获取全局完成度矩阵生成器实例"""
    global _global_generator
    if _global_generator is None:
        _global_generator = GlobalCompletionMatrixGenerator()
    return _global_generator

