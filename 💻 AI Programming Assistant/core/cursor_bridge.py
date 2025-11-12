"""
Cursor桥接器
与Cursor编辑器集成
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import json
import os

class CursorBridge:
    """
    Cursor桥接器
    
    功能：
    1. 检测Cursor是否安装
    2. 打开文件到Cursor
    3. 同步代码变更
    4. 执行Cursor命令
    """
    
    def __init__(self):
        self.cursor_installed = self._check_cursor_installed()
        self.cursor_path = self._find_cursor_path()
    
    def _check_cursor_installed(self) -> bool:
        """检查Cursor是否安装"""
        try:
            # 检查macOS上的Cursor
            if os.path.exists("/Applications/Cursor.app"):
                return True
            # 检查命令行工具
            result = subprocess.run(
                ["which", "cursor"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _find_cursor_path(self) -> Optional[str]:
        """查找Cursor路径"""
        if os.path.exists("/Applications/Cursor.app"):
            return "/Applications/Cursor.app/Contents/MacOS/Cursor"
        
        try:
            result = subprocess.run(
                ["which", "cursor"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return None
    
    async def open_in_cursor(
        self,
        file_path: str,
        line_number: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        在Cursor中打开文件
        
        Args:
            file_path: 文件路径
            line_number: 行号（可选）
            
        Returns:
            操作结果
        """
        if not self.cursor_installed:
            return {
                "success": False,
                "error": "Cursor未安装",
                "suggestion": "请先安装Cursor编辑器"
            }
        
        try:
            if self.cursor_path:
                cmd = [self.cursor_path, file_path]
                if line_number:
                    cmd.extend(["--goto", f"{file_path}:{line_number}"])
                
                subprocess.Popen(cmd)
                return {
                    "success": True,
                    "message": f"已在Cursor中打开: {file_path}",
                    "opened_at": datetime.now().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "无法找到Cursor可执行文件"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_code(
        self,
        file_path: str,
        code: str
    ) -> Dict[str, Any]:
        """
        同步代码到文件
        
        Args:
            file_path: 文件路径
            code: 代码内容
            
        Returns:
            同步结果
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            return {
                "success": True,
                "file_path": file_path,
                "synced_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def edit_code(
        self,
        file_path: str,
        edits: List[Dict[str, Any]],
        edit_type: str = "replace"  # replace, insert, delete
    ) -> Dict[str, Any]:
        """
        编辑代码（支持插入、删除、替换）
        
        Args:
            file_path: 文件路径
            edits: 编辑操作列表 [{"type": "replace/insert/delete", "start_line": 1, "end_line": 2, "content": "..."}]
            edit_type: 编辑类型
            
        Returns:
            编辑结果
        """
        try:
            # 读取原文件
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # 应用编辑（从后往前，避免行号变化）
            edits_sorted = sorted(edits, key=lambda x: x.get("start_line", 0), reverse=True)
            
            for edit in edits_sorted:
                edit_type = edit.get("type", "replace")
                start_line = edit.get("start_line", 1) - 1  # 转为0索引
                end_line = edit.get("end_line", start_line + 1) - 1
                content = edit.get("content", "")
                
                if edit_type == "replace":
                    # 替换指定行
                    new_lines = content.split('\n')
                    if not content.endswith('\n') and new_lines:
                        new_lines[-1] += '\n'
                    lines[start_line:end_line+1] = new_lines
                elif edit_type == "insert":
                    # 在指定位置插入
                    new_lines = content.split('\n')
                    if not content.endswith('\n') and new_lines:
                        new_lines[-1] += '\n'
                    lines.insert(start_line, '\n'.join(new_lines) + '\n')
                elif edit_type == "delete":
                    # 删除指定行
                    del lines[start_line:end_line+1]
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                "success": True,
                "file_path": file_path,
                "edits_applied": len(edits),
                "message": f"成功应用 {len(edits)} 个编辑操作"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_code_completion(
        self,
        file_path: str,
        line_number: int,
        column: int,
        context_lines: int = 5
    ) -> Dict[str, Any]:
        """
        获取代码补全建议
        
        Args:
            file_path: 文件路径
            line_number: 行号
            column: 列号
            context_lines: 上下文行数
            
        Returns:
            补全建议
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            # 读取文件上下文
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            context = ''.join(lines[start_line:end_line])
            
            # 提取当前行的部分内容
            current_line = lines[line_number - 1] if line_number <= len(lines) else ""
            prefix = current_line[:column]
            
            # 简单的补全建议（可以集成AI补全）
            suggestions = self._generate_suggestions(prefix, context)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "context": context,
                "line_number": line_number,
                "column": column
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_suggestions(self, prefix: str, context: str) -> List[Dict[str, Any]]:
        """生成补全建议（简化版）"""
        suggestions = []
        
        # Python关键字补全
        python_keywords = ["def", "class", "import", "from", "if", "elif", "else", "for", "while", "try", "except", "finally", "with", "as", "return", "yield", "async", "await"]
        
        for keyword in python_keywords:
            if keyword.startswith(prefix.lower()):
                suggestions.append({
                    "text": keyword,
                    "type": "keyword",
                    "priority": 1
                })
        
        # 常见函数补全
        common_functions = ["print", "len", "str", "int", "float", "list", "dict", "set", "tuple"]
        for func in common_functions:
            if func.startswith(prefix.lower()):
                suggestions.append({
                    "text": func + "()",
                    "type": "function",
                    "priority": 2
                })
        
        return suggestions[:10]  # 返回前10个建议
    
    async def detect_errors(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        检测代码错误
        
        Args:
            file_path: 文件路径
            
        Returns:
            错误列表
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            errors = []
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Python语法检查
            if file_path.endswith('.py'):
                import ast
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    errors.append({
                        "type": "syntax_error",
                        "line": e.lineno,
                        "column": e.offset or 0,
                        "message": e.msg,
                        "severity": "error"
                    })
            
            # 简单的代码风格检查
            for i, line in enumerate(lines, 1):
                # 检查行长度
                if len(line) > 120:
                    errors.append({
                        "type": "style",
                        "line": i,
                        "column": 0,
                        "message": f"行长度超过120字符（当前{len(line)}字符）",
                        "severity": "warning"
                    })
                
                # 检查未使用的导入（简化版）
                if line.strip().startswith("import ") or line.strip().startswith("from "):
                    # 这里可以添加更复杂的检查逻辑
                    pass
            
            return {
                "success": True,
                "errors": errors,
                "error_count": len([e for e in errors if e["severity"] == "error"]),
                "warning_count": len([e for e in errors if e["severity"] == "warning"])
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def sync_project(
        self,
        project_path: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        同步项目到Cursor
        
        Args:
            project_path: 项目路径
            files: 要同步的文件列表（None表示同步整个项目）
            
        Returns:
            同步结果
        """
        try:
            if not os.path.exists(project_path):
                return {
                    "success": False,
                    "error": "项目路径不存在"
                }
            
            # 在Cursor中打开项目
            if self.cursor_path:
                cmd = [self.cursor_path, project_path]
                subprocess.Popen(cmd)
                
                return {
                    "success": True,
                    "project_path": project_path,
                    "files_synced": files or "all",
                    "message": f"项目已在Cursor中打开: {project_path}"
                }
            else:
                return {
                    "success": False,
                    "error": "无法找到Cursor可执行文件"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """获取Cursor状态"""
        return {
            "installed": self.cursor_installed,
            "path": self.cursor_path,
            "available": self.cursor_installed and self.cursor_path is not None
        }

