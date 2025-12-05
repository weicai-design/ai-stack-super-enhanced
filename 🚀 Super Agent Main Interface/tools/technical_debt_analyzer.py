#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术债务分析工具
自动识别和跟踪代码质量指标、技术债务
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

import yaml

logger = logging.getLogger(__name__)


class DebtSeverity(str, Enum):
    """技术债务严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DebtCategory(str, Enum):
    """技术债务类别"""
    CODE_QUALITY = "code_quality"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TEST_COVERAGE = "test_coverage"
    DOCUMENTATION = "documentation"
    DEPENDENCY = "dependency"


@dataclass
class TechnicalDebt:
    """技术债务项"""
    debt_id: str
    title: str
    description: str
    category: DebtCategory
    severity: DebtSeverity
    file_path: str
    line_number: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    estimated_effort_hours: int = 0
    priority_score: float = 0.0
    status: str = "open"
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeQualityMetrics:
    """代码质量指标"""
    file_path: str
    complexity: int = 0
    lines_of_code: int = 0
    comment_density: float = 0.0
    duplication_rate: float = 0.0
    test_coverage: float = 0.0
    code_smells: int = 0
    security_issues: int = 0
    performance_issues: int = 0
    last_analyzed: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class ProjectHealthReport:
    """项目健康报告"""
    project_id: str
    timestamp: str
    overall_score: float
    metrics: Dict[str, Any]
    debts: List[TechnicalDebt]
    recommendations: List[str]
    trends: Dict[str, Any]


class DebtAnalyzer(ABC):
    """技术债务分析器接口"""
    
    @abstractmethod
    def analyze(self, file_path: str) -> List[TechnicalDebt]:
        """分析文件中的技术债务"""
        pass


class CodeComplexityAnalyzer(DebtAnalyzer):
    """代码复杂度分析器"""
    
    def analyze(self, file_path: str) -> List[TechnicalDebt]:
        """分析代码复杂度"""
        debts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析Python代码
            tree = ast.parse(content)
            
            # 计算复杂度指标
            complexity = self._calculate_complexity(tree)
            
            if complexity > 10:
                debts.append(TechnicalDebt(
                    debt_id=str(uuid4()),
                    title="高复杂度函数",
                    description=f"函数复杂度达到{complexity}，建议重构",
                    category=DebtCategory.CODE_QUALITY,
                    severity=DebtSeverity.MEDIUM,
                    file_path=file_path,
                    estimated_effort_hours=2,
                    priority_score=complexity * 0.1
                ))
                
        except Exception as e:
            logger.warning(f"分析文件复杂度失败 {file_path}: {e}")
        
        return debts
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """计算AST节点的复杂度"""
        complexity = 1  # 基础复杂度
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            complexity += self._calculate_complexity(child)
        
        return complexity


class SecurityAnalyzer(DebtAnalyzer):
    """安全分析器"""
    
    def __init__(self):
        self.patterns = {
            "hardcoded_password": r"(password|pwd|secret)[\s]*=[\s]*['\"][^'\"]*['\"]",
            "sql_injection": r"execute\(.*\+.*\)",
            "eval_usage": r"eval\([^)]*\)",
            "shell_injection": r"os\.system\([^)]*\)|subprocess\.call\([^)]*\)",
        }
    
    def analyze(self, file_path: str) -> List[TechnicalDebt]:
        """分析安全债务"""
        debts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern_name, pattern in self.patterns.items():
                    if re.search(pattern, line, re.IGNORECASE):
                        debts.append(self._create_security_debt(pattern_name, file_path, line_num, line))
                        
        except Exception as e:
            logger.warning(f"分析文件安全失败 {file_path}: {e}")
        
        return debts
    
    def _create_security_debt(self, pattern_name: str, file_path: str, line_num: int, line: str) -> TechnicalDebt:
        """创建安全债务"""
        descriptions = {
            "hardcoded_password": "检测到硬编码密码",
            "sql_injection": "潜在的SQL注入风险",
            "eval_usage": "使用eval函数存在安全风险",
            "shell_injection": "潜在的shell注入风险",
        }
        
        return TechnicalDebt(
            debt_id=str(uuid4()),
            title=f"安全风险: {pattern_name}",
            description=f"{descriptions.get(pattern_name, '安全风险')}: {line.strip()}",
            category=DebtCategory.SECURITY,
            severity=DebtSeverity.HIGH,
            file_path=file_path,
            line_number=line_num,
            estimated_effort_hours=4,
            priority_score=0.8
        )


class DocumentationAnalyzer(DebtAnalyzer):
    """文档分析器"""
    
    def analyze(self, file_path: str) -> List[TechnicalDebt]:
        """分析文档债务"""
        debts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查类和方法是否有文档字符串
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        debts.append(self._create_documentation_debt(file_path, node))
                        
        except Exception as e:
            logger.warning(f"分析文件文档失败 {file_path}: {e}")
        
        return debts
    
    def _create_documentation_debt(self, file_path: str, node: ast.AST) -> TechnicalDebt:
        """创建文档债务"""
        node_type = "类" if isinstance(node, ast.ClassDef) else "函数"
        
        return TechnicalDebt(
            debt_id=str(uuid4()),
            title=f"缺失文档: {node.name}",
            description=f"{node_type} {node.name} 缺少文档字符串",
            category=DebtCategory.DOCUMENTATION,
            severity=DebtSeverity.LOW,
            file_path=file_path,
            line_number=node.lineno,
            estimated_effort_hours=1,
            priority_score=0.3
        )


class PerformanceAnalyzer(DebtAnalyzer):
    """性能分析器"""
    
    def analyze(self, file_path: str) -> List[TechnicalDebt]:
        """分析性能债务"""
        debts = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            patterns = {
                "nested_loops": r"for\s+\w+\s+in\s+\w+:\s*\n\s*for\s+\w+\s+in\s+\w+:",
                "inefficient_string": r'\+=\s*["\'][^"\']*["\']',
                "unnecessary_import": r"import\s+\*",
            }
            
            for line_num, line in enumerate(content.split('\n'), 1):
                for pattern_name, pattern in patterns.items():
                    if re.search(pattern, line):
                        debts.append(self._create_performance_debt(pattern_name, file_path, line_num, line))
                        
        except Exception as e:
            logger.warning(f"分析文件性能失败 {file_path}: {e}")
        
        return debts
    
    def _create_performance_debt(self, pattern_name: str, file_path: str, line_num: int, line: str) -> TechnicalDebt:
        """创建性能债务"""
        descriptions = {
            "nested_loops": "嵌套循环可能导致性能问题",
            "inefficient_string": "低效的字符串操作",
            "unnecessary_import": "不必要的通配符导入",
        }
        
        return TechnicalDebt(
            debt_id=str(uuid4()),
            title=f"性能问题: {pattern_name}",
            description=f"{descriptions.get(pattern_name, '性能问题')}: {line.strip()}",
            category=DebtCategory.PERFORMANCE,
            severity=DebtSeverity.MEDIUM,
            file_path=file_path,
            line_number=line_num,
            estimated_effort_hours=2,
            priority_score=0.5
        )


class TechnicalDebtManager:
    """技术债务管理器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.analyzers: List[DebtAnalyzer] = [
            CodeComplexityAnalyzer(),
            SecurityAnalyzer(),
            DocumentationAnalyzer(),
            PerformanceAnalyzer(),
        ]
        self.debts_file = self.project_root / "technical_debts.json"
        self.metrics_file = self.project_root / "code_metrics.json"
        
    def analyze_project(self) -> ProjectHealthReport:
        """分析整个项目的技术债务"""
        logger.info("开始分析项目技术债务...")
        
        all_debts = []
        code_metrics = []
        
        # 分析所有Python文件
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            if self._should_analyze_file(file_path):
                file_metrics = self._analyze_file_metrics(file_path)
                code_metrics.append(file_metrics)
                
                for analyzer in self.analyzers:
                    debts = analyzer.analyze(str(file_path))
                    all_debts.extend(debts)
        
        # 计算总体评分
        overall_score = self._calculate_overall_score(all_debts, code_metrics)
        
        # 生成报告
        report = ProjectHealthReport(
            project_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            overall_score=overall_score,
            metrics=self._aggregate_metrics(code_metrics),
            debts=all_debts,
            recommendations=self._generate_recommendations(all_debts),
            trends=self._analyze_trends()
        )
        
        # 保存结果
        self._save_debts(all_debts)
        self._save_metrics(code_metrics)
        
        logger.info(f"技术债务分析完成，发现 {len(all_debts)} 个债务项")
        return report
    
    def get_debt_summary(self) -> Dict[str, Any]:
        """获取债务摘要"""
        if not self.debts_file.exists():
            return {}
        
        with open(self.debts_file, 'r', encoding='utf-8') as f:
            debts = json.load(f)
        
        summary = defaultdict(int)
        for debt in debts:
            summary[debt['category']] += 1
            summary[debt['severity']] += 1
            summary['total'] += 1
        
        return dict(summary)
    
    def prioritize_debts(self, debts: List[TechnicalDebt]) -> List[TechnicalDebt]:
        """根据优先级排序债务"""
        return sorted(debts, key=lambda d: d.priority_score, reverse=True)
    
    def create_repayment_plan(self, available_hours: int = 40) -> Dict[str, Any]:
        """创建债务偿还计划"""
        if not self.debts_file.exists():
            return {"message": "未找到技术债务数据"}
        
        with open(self.debts_file, 'r', encoding='utf-8') as f:
            debts_data = json.load(f)
        
        debts = [TechnicalDebt(**debt) for debt in debts_data]
        prioritized_debts = self.prioritize_debts(debts)
        
        plan = {
            "available_hours": available_hours,
            "scheduled_debts": [],
            "total_estimated_hours": 0,
            "remaining_hours": available_hours
        }
        
        for debt in prioritized_debts:
            if debt.estimated_effort_hours <= plan["remaining_hours"]:
                plan["scheduled_debts"].append({
                    "debt_id": debt.debt_id,
                    "title": debt.title,
                    "estimated_hours": debt.estimated_effort_hours,
                    "priority_score": debt.priority_score
                })
                plan["total_estimated_hours"] += debt.estimated_effort_hours
                plan["remaining_hours"] -= debt.estimated_effort_hours
        
        return plan
    
    def _should_analyze_file(self, file_path: Path) -> bool:
        """判断是否应该分析文件"""
        # 忽略测试文件和虚拟环境文件
        ignore_patterns = [
            "*test*", "*__pycache__*", "*.venv*", "*node_modules*",
            "*.git*", "*build*", "*dist*"
        ]
        
        file_str = str(file_path)
        return not any(pattern in file_str for pattern in ignore_patterns)
    
    def _analyze_file_metrics(self, file_path: Path) -> CodeQualityMetrics:
        """分析文件指标"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        loc = len(lines)
        
        # 计算注释密度
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        comment_density = comment_lines / loc if loc > 0 else 0
        
        return CodeQualityMetrics(
            file_path=str(file_path),
            lines_of_code=loc,
            comment_density=comment_density
        )
    
    def _calculate_overall_score(self, debts: List[TechnicalDebt], metrics: List[CodeQualityMetrics]) -> float:
        """计算总体评分"""
        if not debts:
            return 100.0
        
        # 基于债务数量和严重程度计算评分
        severity_weights = {
            DebtSeverity.LOW: 0.1,
            DebtSeverity.MEDIUM: 0.3,
            DebtSeverity.HIGH: 0.6,
            DebtSeverity.CRITICAL: 1.0
        }
        
        total_weight = sum(severity_weights[d.severity] for d in debts)
        max_possible_weight = len(debts) * 1.0
        
        debt_score = 100 - (total_weight / max_possible_weight * 100) if max_possible_weight > 0 else 100
        
        return max(0, min(100, debt_score))
    
    def _aggregate_metrics(self, metrics: List[CodeQualityMetrics]) -> Dict[str, Any]:
        """聚合指标"""
        if not metrics:
            return {}
        
        return {
            "total_files": len(metrics),
            "total_lines": sum(m.lines_of_code for m in metrics),
            "avg_comment_density": sum(m.comment_density for m in metrics) / len(metrics),
            "files_analyzed": [m.file_path for m in metrics]
        }
    
    def _generate_recommendations(self, debts: List[TechnicalDebt]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        debt_by_category = defaultdict(list)
        for debt in debts:
            debt_by_category[debt.category].append(debt)
        
        for category, category_debts in debt_by_category.items():
            if category_debts:
                recommendations.append(
                    f"处理{category}类债务: {len(category_debts)}个问题需要解决"
                )
        
        if not debts:
            recommendations.append("代码质量良好，继续保持!")
        
        return recommendations
    
    def _analyze_trends(self) -> Dict[str, Any]:
        """分析趋势"""
        # 简化实现，实际项目中可以对比历史数据
        return {
            "message": "趋势分析需要历史数据对比"
        }
    
    def _save_debts(self, debts: List[TechnicalDebt]) -> None:
        """保存债务数据"""
        debts_data = [
            {
                "debt_id": d.debt_id,
                "title": d.title,
                "description": d.description,
                "category": d.category.value,
                "severity": d.severity.value,
                "file_path": d.file_path,
                "line_number": d.line_number,
                "created_at": d.created_at,
                "estimated_effort_hours": d.estimated_effort_hours,
                "priority_score": d.priority_score,
                "status": d.status
            }
            for d in debts
        ]
        
        with open(self.debts_file, 'w', encoding='utf-8') as f:
            json.dump(debts_data, f, indent=2, ensure_ascii=False)
    
    def _save_metrics(self, metrics: List[CodeQualityMetrics]) -> None:
        """保存指标数据"""
        metrics_data = [
            {
                "file_path": m.file_path,
                "lines_of_code": m.lines_of_code,
                "comment_density": m.comment_density,
                "last_analyzed": m.last_analyzed
            }
            for m in metrics
        ]
        
        with open(self.metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics_data, f, indent=2, ensure_ascii=False)


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python technical_debt_analyzer.py <项目根目录>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    
    if not Path(project_root).exists():
        print(f"项目目录不存在: {project_root}")
        sys.exit(1)
    
    manager = TechnicalDebtManager(project_root)
    report = manager.analyze_project()
    
    print(f"\n=== 项目健康报告 ===")
    print(f"总体评分: {report.overall_score:.1f}/100")
    print(f"分析文件数: {report.metrics.get('total_files', 0)}")
    print(f"总代码行数: {report.metrics.get('total_lines', 0)}")
    print(f"发现债务项: {len(report.debts)}")
    
    print(f"\n=== 改进建议 ===")
    for rec in report.recommendations:
        print(f"- {rec}")
    
    # 生成偿还计划
    plan = manager.create_repayment_plan(40)
    print(f"\n=== 40小时偿还计划 ===")
    print(f"可安排债务: {len(plan['scheduled_debts'])}")
    print(f"总估算时间: {plan['total_estimated_hours']}小时")
    print(f"剩余时间: {plan['remaining_hours']}小时")


if __name__ == "__main__":
    main()