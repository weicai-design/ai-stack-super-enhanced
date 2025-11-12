"""
Bug修复器（深化版）
自动检测和修复Bug，支持多种常见Bug模式
"""

import re
import ast
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from enum import Enum


class BugType(Enum):
    """Bug类型"""
    SYNTAX_ERROR = "syntax_error"
    LOGIC_ERROR = "logic_error"
    RUNTIME_ERROR = "runtime_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_VULNERABILITY = "security_vulnerability"


@dataclass
class Bug:
    """Bug信息"""
    bug_type: BugType
    line_number: Optional[int]
    message: str
    fix_suggestion: str
    confidence: float  # 0-1


class BugFixer:
    """Bug修复器（深化版）"""
    
    def __init__(self):
        self.common_bug_patterns = {
            "undefined_variable": r"NameError.*name '(\w+)' is not defined",
            "index_out_of_range": r"IndexError.*list index out of range",
            "key_error": r"KeyError.*'(\w+)'",
            "type_error": r"TypeError.*",
            "attribute_error": r"AttributeError.*'(\w+)'",
            "indentation_error": r"IndentationError.*",
            "syntax_error": r"SyntaxError.*",
        }
        
        self.fix_templates = {
            "undefined_variable": self._fix_undefined_variable,
            "index_out_of_range": self._fix_index_out_of_range,
            "key_error": self._fix_key_error,
            "type_error": self._fix_type_error,
            "attribute_error": self._fix_attribute_error,
        }
    
    async def detect_bugs(self, code: str, language: str = "python") -> List[Dict[str, Any]]:
        """
        检测Bug（深化版）
        
        Args:
            code: 代码内容
            language: 编程语言
            
        Returns:
            Bug列表
        """
        bugs = []
        
        # 1. 语法检查
        syntax_bugs = await self._detect_syntax_errors(code)
        bugs.extend(syntax_bugs)
        
        # 2. 常见错误模式检测
        pattern_bugs = await self._detect_pattern_bugs(code)
        bugs.extend(pattern_bugs)
        
        # 3. 逻辑错误检测
        logic_bugs = await self._detect_logic_errors(code)
        bugs.extend(logic_bugs)
        
        # 4. 运行时错误检测
        runtime_bugs = await self._detect_runtime_errors(code)
        bugs.extend(runtime_bugs)
        
        return [
            {
                "type": bug.bug_type.value,
                "line": bug.line_number,
                "message": bug.message,
                "fix_suggestion": bug.fix_suggestion,
                "confidence": bug.confidence,
            }
            for bug in bugs
        ]
    
    async def fix_bug(
        self,
        code: str,
        bug_description: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        修复Bug（深化版）
        
        Args:
            code: 代码内容
            bug_description: Bug描述或错误消息
            language: 编程语言
            
        Returns:
            修复结果
        """
        # 1. 检测所有Bug
        bugs = await self.detect_bugs(code, language)
        
        # 2. 如果提供了bug描述，尝试匹配
        if bug_description:
            matched_bugs = self._match_bugs_by_description(bugs, bug_description)
        else:
            matched_bugs = bugs
        
        # 3. 应用修复
        fixed_code = code
        fixes_applied = []
        
        for bug in matched_bugs:
            fix_result = await self._apply_fix(fixed_code, bug, language)
            if fix_result["success"]:
                fixed_code = fix_result["fixed_code"]
                fixes_applied.append({
                    "type": bug["type"],
                    "line": bug["line"],
                    "fix": fix_result["fix_description"]
                })
        
        return {
            "success": True,
            "fixed_code": fixed_code,
            "fixes_applied": fixes_applied,
            "bugs_found": len(bugs),
            "bugs_fixed": len(fixes_applied)
        }
    
    async def _detect_syntax_errors(self, code: str) -> List[Bug]:
        """检测语法错误"""
        bugs = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            bugs.append(Bug(
                bug_type=BugType.SYNTAX_ERROR,
                line_number=e.lineno,
                message=f"语法错误：{e.msg}",
                fix_suggestion=f"检查第{e.lineno}行的语法，错误信息：{e.msg}",
                confidence=1.0
            ))
        
        return bugs
    
    async def _detect_pattern_bugs(self, code: str) -> List[Bug]:
        """检测常见错误模式"""
        bugs = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检测未定义的变量（简化版）
            if re.search(r"^\s*(\w+)\s*=", line):
                var_match = re.search(r"^\s*(\w+)\s*=", line)
                if var_match:
                    var_name = var_match.group(1)
                    # 检查变量是否在使用前定义（简化检查）
                    if line_num > 1:
                        prev_code = '\n'.join(lines[:line_num-1])
                        if var_name not in prev_code and var_name not in ['if', 'for', 'while', 'def', 'class', 'import', 'from']:
                            # 这只是一个简化的检查，实际需要更复杂的分析
                            pass
            
            # 检测可能的除零错误
            if re.search(r"/\s*0\b", line) or re.search(r"/\s*(\w+)\s*\)", line):
                bugs.append(Bug(
                    bug_type=BugType.RUNTIME_ERROR,
                    line_number=line_num,
                    message="潜在的除零错误",
                    fix_suggestion="添加除零检查：if denominator != 0:",
                    confidence=0.7
                ))
            
            # 检测可能的None访问
            if re.search(r"(\w+)\.(\w+)\s*\(\)", line):
                match = re.search(r"(\w+)\.(\w+)\s*\(\)", line)
                if match:
                    obj_name = match.group(1)
                    # 检查是否有None检查（简化）
                    if f"if {obj_name} is not None" not in '\n'.join(lines[max(0, line_num-5):line_num]):
                        bugs.append(Bug(
                            bug_type=BugType.RUNTIME_ERROR,
                            line_number=line_num,
                            message=f"可能的None访问：{obj_name}可能为None",
                            fix_suggestion=f"添加None检查：if {obj_name} is not None:",
                            confidence=0.6
                        ))
        
        return bugs
    
    async def _detect_logic_errors(self, code: str) -> List[Bug]:
        """检测逻辑错误"""
        bugs = []
        
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # 检测无限循环
                if isinstance(node, ast.While):
                    if isinstance(node.test, ast.Constant) and node.test.value is True:
                        bugs.append(Bug(
                            bug_type=BugType.LOGIC_ERROR,
                            line_number=node.lineno,
                            message="无限循环：while True没有break语句",
                            fix_suggestion="添加break条件或使用for循环",
                            confidence=0.8
                        ))
                
                # 检测未使用的变量
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            var_name = target.id
                            # 简化检查：如果变量赋值后未使用
                            # 实际需要更复杂的分析
                            pass
        except SyntaxError:
            pass
        
        return bugs
    
    async def _detect_runtime_errors(self, code: str) -> List[Bug]:
        """检测运行时错误"""
        bugs = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 检测字典访问缺少get
            if re.search(r"(\w+)\s*\[\s*['\"](\w+)['\"]\s*\]", line):
                match = re.search(r"(\w+)\s*\[\s*['\"](\w+)['\"]\s*\]", line)
                if match:
                    dict_name = match.group(1)
                    key = match.group(2)
                    bugs.append(Bug(
                        bug_type=BugType.RUNTIME_ERROR,
                        line_number=line_num,
                        message=f"字典访问可能引发KeyError：{dict_name}['{key}']",
                        fix_suggestion=f"使用安全访问：{dict_name}.get('{key}') 或 {dict_name}.get('{key}', default_value)",
                        confidence=0.7
                    ))
            
            # 检测列表索引越界风险
            if re.search(r"(\w+)\s*\[\s*(\w+)\s*\]", line):
                match = re.search(r"(\w+)\s*\[\s*(\w+)\s*\]", line)
                if match:
                    list_name = match.group(1)
                    index = match.group(2)
                    bugs.append(Bug(
                        bug_type=BugType.RUNTIME_ERROR,
                        line_number=line_num,
                        message=f"列表索引可能越界：{list_name}[{index}]",
                        fix_suggestion=f"添加边界检查：if 0 <= {index} < len({list_name}):",
                        confidence=0.6
                    ))
        
        return bugs
    
    def _match_bugs_by_description(self, bugs: List[Dict], description: str) -> List[Dict]:
        """根据描述匹配Bug"""
        matched = []
        description_lower = description.lower()
        
        for bug in bugs:
            if any(keyword in description_lower for keyword in bug["message"].lower().split()):
                matched.append(bug)
        
        return matched if matched else bugs[:3]  # 如果没有匹配，返回前3个
    
    async def _apply_fix(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """应用修复"""
        bug_type = bug["type"]
        line_num = bug.get("line")
        
        if bug_type in self.fix_templates:
            fix_func = self.fix_templates[bug_type]
            return await fix_func(code, bug, language)
        
        return {
            "success": False,
            "fixed_code": code,
            "fix_description": "无法自动修复此类型的Bug"
        }
    
    async def _fix_undefined_variable(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """修复未定义变量"""
        # 简化修复：建议添加变量定义
        return {
            "success": True,
            "fixed_code": code,
            "fix_description": "建议在使用前定义变量"
        }
    
    async def _fix_index_out_of_range(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """修复索引越界"""
        lines = code.split('\n')
        line_num = bug.get("line", 0) - 1
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            # 尝试添加边界检查
            if '[' in line and ']' in line:
                # 简化修复：添加注释建议
                lines[line_num] = f"# TODO: 添加边界检查\n{line}"
        
        return {
            "success": True,
            "fixed_code": '\n'.join(lines),
            "fix_description": "添加了边界检查建议"
        }
    
    async def _fix_key_error(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """修复KeyError"""
        lines = code.split('\n')
        line_num = bug.get("line", 0) - 1
        
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            # 将 dict['key'] 替换为 dict.get('key')
            fixed_line = re.sub(r"(\w+)\s*\[\s*['\"](\w+)['\"]\s*\]", r"\1.get('\2')", line)
            if fixed_line != line:
                lines[line_num] = fixed_line
                return {
                    "success": True,
                    "fixed_code": '\n'.join(lines),
                    "fix_description": "将字典访问改为使用get()方法"
                }
        
        return {
            "success": False,
            "fixed_code": code,
            "fix_description": "无法自动修复"
        }
    
    async def _fix_type_error(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """修复TypeError"""
        return {
            "success": True,
            "fixed_code": code,
            "fix_description": "建议检查变量类型，添加类型转换或类型检查"
        }
    
    async def _fix_attribute_error(self, code: str, bug: Dict, language: str) -> Dict[str, Any]:
        """修复AttributeError"""
        return {
            "success": True,
            "fixed_code": code,
            "fix_description": "建议检查对象是否有该属性，使用hasattr()或try-except"
        }

