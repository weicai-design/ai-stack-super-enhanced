"""
代码审查器
规范性、安全性、性能审查
深化版：支持多维度深度审查
"""

import re
import ast
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"  # 严重问题，必须修复
    HIGH = "high"  # 高优先级问题
    MEDIUM = "medium"  # 中等问题
    LOW = "low"  # 低优先级问题
    INFO = "info"  # 信息提示


@dataclass
class CodeIssue:
    """代码问题"""
    severity: IssueSeverity
    category: str  # style, security, performance, maintainability, best_practice
    line_number: Optional[int]
    column: Optional[int]
    message: str
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None


class CodeReviewer:
    """代码审查器（深化版）"""
    
    def __init__(self):
        self.security_patterns = {
            "sql_injection": [
                r"execute\s*\(\s*['\"].*%.*['\"]",
                r"query\s*\(\s*['\"].*%.*['\"]",
                r"cursor\.execute\s*\(\s*['\"].*%.*['\"]",
            ],
            "xss": [
                r"innerHTML\s*=",
                r"document\.write\s*\(",
                r"eval\s*\(",
            ],
            "path_traversal": [
                r"open\s*\(\s*['\"].*\.\./",
                r"file\s*\(\s*['\"].*\.\./",
            ],
            "hardcoded_secrets": [
                r"password\s*=\s*['\"][^'\"]+['\"]",
                r"api_key\s*=\s*['\"][^'\"]+['\"]",
                r"secret\s*=\s*['\"][^'\"]+['\"]",
            ],
        }
        
        self.performance_patterns = {
            "n_plus_one": [
                r"for\s+\w+\s+in\s+\w+:\s*\n\s*.*\.query\(",
            ],
            "inefficient_loop": [
                r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(",
            ],
            "unnecessary_computation": [
                r"\.append\s*\(\s*.*\s*\+\s*.*\s*\)",
            ],
        }
        
        self.style_patterns = {
            "long_line": 120,  # 最大行长度
            "complex_function": 50,  # 最大函数复杂度
            "too_many_parameters": 5,  # 最大参数数量
        }
    
    async def review_code(
        self,
        code: str,
        language: str = "python",
        review_types: Optional[List[str]] = None  # style, security, performance, maintainability
    ) -> Dict[str, Any]:
        """
        审查代码（深化版）
        
        Args:
            code: 代码内容
            language: 编程语言
            review_types: 审查类型列表
            
        Returns:
            审查结果
        """
        review_types = review_types or ["style", "security", "performance", "maintainability"]
        
        issues: List[CodeIssue] = []
        suggestions: List[str] = []
        
        # 1. 安全性审查
        if "security" in review_types:
            security_issues = await self._review_security(code, language)
            issues.extend(security_issues)
        
        # 2. 性能审查
        if "performance" in review_types:
            performance_issues = await self._review_performance(code, language)
            issues.extend(performance_issues)
        
        # 3. 规范性审查
        if "style" in review_types:
            style_issues = await self._review_style(code, language)
            issues.extend(style_issues)
        
        # 4. 可维护性审查
        if "maintainability" in review_types:
            maintainability_issues = await self._review_maintainability(code, language)
            issues.extend(maintainability_issues)
        
        # 5. 最佳实践审查
        best_practice_issues = await self._review_best_practices(code, language)
        issues.extend(best_practice_issues)
        
        # 生成建议
        suggestions = self._generate_suggestions(issues)
        
        # 计算评分
        score = self._calculate_score(issues)
        
        return {
            "success": True,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "category": issue.category,
                    "line": issue.line_number,
                    "column": issue.column,
                    "message": issue.message,
                    "suggestion": issue.suggestion,
                    "rule_id": issue.rule_id,
                }
                for issue in issues
            ],
            "suggestions": suggestions,
            "score": score,
            "summary": {
                "total_issues": len(issues),
                "critical": len([i for i in issues if i.severity == IssueSeverity.CRITICAL]),
                "high": len([i for i in issues if i.severity == IssueSeverity.HIGH]),
                "medium": len([i for i in issues if i.severity == IssueSeverity.MEDIUM]),
                "low": len([i for i in issues if i.severity == IssueSeverity.LOW]),
            }
        }
    
    async def _review_security(self, code: str, language: str) -> List[CodeIssue]:
        """安全性审查"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # SQL注入检测
            for pattern in self.security_patterns.get("sql_injection", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.CRITICAL,
                        category="security",
                        line_number=line_num,
                        column=None,
                        message="潜在的SQL注入漏洞：使用字符串格式化构建SQL查询",
                        suggestion="使用参数化查询或ORM框架",
                        rule_id="SEC001"
                    ))
            
            # XSS检测
            for pattern in self.security_patterns.get("xss", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.HIGH,
                        category="security",
                        line_number=line_num,
                        column=None,
                        message="潜在的XSS漏洞：直接操作DOM",
                        suggestion="使用安全的DOM操作方法，对用户输入进行转义",
                        rule_id="SEC002"
                    ))
            
            # 路径遍历检测
            for pattern in self.security_patterns.get("path_traversal", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.CRITICAL,
                        category="security",
                        line_number=line_num,
                        column=None,
                        message="潜在的路径遍历漏洞：使用相对路径访问文件",
                        suggestion="使用绝对路径并验证路径合法性",
                        rule_id="SEC003"
                    ))
            
            # 硬编码密钥检测
            for pattern in self.security_patterns.get("hardcoded_secrets", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.CRITICAL,
                        category="security",
                        line_number=line_num,
                        column=None,
                        message="硬编码密钥：密码或API密钥直接写在代码中",
                        suggestion="使用环境变量或密钥管理服务",
                        rule_id="SEC004"
                    ))
        
        return issues
    
    async def _review_performance(self, code: str, language: str) -> List[CodeIssue]:
        """性能审查"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # N+1查询检测
            for pattern in self.performance_patterns.get("n_plus_one", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.HIGH,
                        category="performance",
                        line_number=line_num,
                        column=None,
                        message="潜在的N+1查询问题：在循环中执行数据库查询",
                        suggestion="使用批量查询或预加载（eager loading）",
                        rule_id="PERF001"
                    ))
            
            # 低效循环检测
            for pattern in self.performance_patterns.get("inefficient_loop", []):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        severity=IssueSeverity.MEDIUM,
                        category="performance",
                        line_number=line_num,
                        column=None,
                        message="低效循环：使用range(len())遍历列表",
                        suggestion="直接遍历列表元素：for item in list",
                        rule_id="PERF002"
                    ))
        
        # 检查函数复杂度
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > 20:
                        issues.append(CodeIssue(
                            severity=IssueSeverity.MEDIUM,
                            category="performance",
                            line_number=node.lineno,
                            column=None,
                            message=f"函数复杂度较高：{complexity}（建议<20）",
                            suggestion="将函数拆分为更小的函数",
                            rule_id="PERF003"
                        ))
        except SyntaxError:
            pass
        
        return issues
    
    async def _review_style(self, code: str, language: str) -> List[CodeIssue]:
        """规范性审查"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查行长度
            if len(line) > self.style_patterns["long_line"]:
                issues.append(CodeIssue(
                    severity=IssueSeverity.LOW,
                    category="style",
                    line_number=line_num,
                    column=None,
                    message=f"行长度过长：{len(line)}字符（建议<{self.style_patterns['long_line']}）",
                    suggestion="将长行拆分为多行",
                    rule_id="STYLE001"
                ))
            
            # 检查未使用的导入
            if line.strip().startswith("import ") or line.strip().startswith("from "):
                # 简化检查：如果导入的模块在代码中未使用
                pass  # 需要更复杂的AST分析
        
        return issues
    
    async def _review_maintainability(self, code: str, language: str) -> List[CodeIssue]:
        """可维护性审查"""
        issues = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # 检查参数数量
                    if len(node.args.args) > self.style_patterns["too_many_parameters"]:
                        issues.append(CodeIssue(
                            severity=IssueSeverity.MEDIUM,
                            category="maintainability",
                            line_number=node.lineno,
                            column=None,
                            message=f"函数参数过多：{len(node.args.args)}个（建议<{self.style_patterns['too_many_parameters']}）",
                            suggestion="考虑使用配置对象或数据类",
                            rule_id="MAIN001"
                        ))
                    
                    # 检查函数长度
                    if node.end_lineno and node.lineno:
                        func_length = node.end_lineno - node.lineno
                        if func_length > 50:
                            issues.append(CodeIssue(
                                severity=IssueSeverity.MEDIUM,
                                category="maintainability",
                                line_number=node.lineno,
                                column=None,
                                message=f"函数过长：{func_length}行（建议<50）",
                                suggestion="将函数拆分为更小的函数",
                                rule_id="MAIN002"
                            ))
        except SyntaxError:
            pass
        
        return issues
    
    async def _review_best_practices(self, code: str, language: str) -> List[CodeIssue]:
        """最佳实践审查"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检查使用print而不是logging
            if re.search(r"^\s*print\s*\(", line):
                issues.append(CodeIssue(
                    severity=IssueSeverity.LOW,
                    category="best_practice",
                    line_number=line_num,
                    column=None,
                    message="使用print而不是logging",
                    suggestion="使用logging模块进行日志记录",
                    rule_id="BP001"
                ))
            
            # 检查使用==比较None
            if re.search(r"==\s*None", line):
                issues.append(CodeIssue(
                    severity=IssueSeverity.LOW,
                    category="best_practice",
                    line_number=line_num,
                    column=None,
                    message="使用==比较None",
                    suggestion="使用'is None'或'is not None'",
                    rule_id="BP002"
                ))
            
            # 检查使用bare except
            if re.search(r"^\s*except\s*:", line):
                issues.append(CodeIssue(
                    severity=IssueSeverity.MEDIUM,
                    category="best_practice",
                    line_number=line_num,
                    column=None,
                    message="使用bare except捕获所有异常",
                    suggestion="明确指定要捕获的异常类型",
                    rule_id="BP003"
                ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """计算函数复杂度（简化版）"""
        complexity = 1  # 基础复杂度
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _generate_suggestions(self, issues: List[CodeIssue]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        critical_issues = [i for i in issues if i.severity == IssueSeverity.CRITICAL]
        if critical_issues:
            suggestions.append(f"发现{len(critical_issues)}个严重安全问题，建议立即修复")
        
        security_issues = [i for i in issues if i.category == "security"]
        if security_issues:
            suggestions.append("建议进行安全审计，修复所有安全问题")
        
        performance_issues = [i for i in issues if i.category == "performance"]
        if performance_issues:
            suggestions.append("建议优化性能问题，特别是N+1查询和低效循环")
        
        return suggestions
    
    def _calculate_score(self, issues: List[CodeIssue]) -> int:
        """计算代码质量评分（0-100）"""
        base_score = 100
        
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                base_score -= 10
            elif issue.severity == IssueSeverity.HIGH:
                base_score -= 5
            elif issue.severity == IssueSeverity.MEDIUM:
                base_score -= 2
            elif issue.severity == IssueSeverity.LOW:
                base_score -= 1
        
        return max(0, min(100, base_score))

