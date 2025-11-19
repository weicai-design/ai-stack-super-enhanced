#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 编程助手增强版
功能：IDE集成、代码审查、性能优化、文档生成、命令回放、安全沙箱联动
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import ast
import re
import json
import logging

logger = logging.getLogger(__name__)


class DocumentationGenerator:
    """
    文档生成器
    自动生成代码文档、API文档、README等
    """
    
    def __init__(self):
        """初始化文档生成器"""
        pass
    
    def generate_docstring(
        self,
        code: str,
        language: str = "python",
        style: str = "google"  # google, numpy, sphinx
    ) -> Dict[str, Any]:
        """
        生成函数/类的文档字符串
        
        Args:
            code: 代码内容
            language: 编程语言
            style: 文档风格
            
        Returns:
            生成的文档
        """
        try:
            if language == "python":
                return self._generate_python_docstring(code, style)
            else:
                return {
                    "success": False,
                    "error": f"不支持的语言: {language}"
                }
        except Exception as e:
            logger.error(f"生成文档字符串失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_python_docstring(self, code: str, style: str) -> Dict[str, Any]:
        """生成Python文档字符串"""
        try:
            tree = ast.parse(code)
            docstrings = []
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    docstring = self._generate_node_docstring(node, style)
                    if docstring:
                        docstrings.append({
                            "name": node.name,
                            "type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                            "line": node.lineno,
                            "docstring": docstring
                        })
            
            return {
                "success": True,
                "docstrings": docstrings,
                "style": style
            }
        except SyntaxError as e:
            return {
                "success": False,
                "error": f"代码语法错误: {e}"
            }
    
    def _generate_node_docstring(self, node: ast.AST, style: str) -> str:
        """为节点生成文档字符串"""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # 提取参数
            args = [arg.arg for arg in node.args.args if arg.arg != 'self']
            defaults = node.args.defaults
            
            # 生成文档字符串
            if style == "google":
                doc = f'    """\n'
                doc += f'    {self._infer_function_description(node.name)}\n\n'
                if args:
                    doc += '    Args:\n'
                    for arg in args:
                        doc += f'        {arg}: TODO - 参数说明\n'
                doc += '\n    Returns:\n'
                doc += '        TODO - 返回值说明\n'
                doc += '    """'
            elif style == "numpy":
                doc = f'    """\n'
                doc += f'    {self._infer_function_description(node.name)}\n\n'
                if args:
                    doc += '    Parameters\n'
                    doc += '    ----------\n'
                    for arg in args:
                        doc += f'    {arg} : TODO\n'
                        doc += f'        TODO - 参数说明\n'
                doc += '\n    Returns\n'
                doc += '    -------\n'
                doc += '    TODO\n'
                doc += '        TODO - 返回值说明\n'
                doc += '    """'
            else:  # sphinx
                doc = f'    """{self._infer_function_description(node.name)}\n\n'
                if args:
                    for arg in args:
                        doc += f'    :param {arg}: TODO - 参数说明\n'
                doc += '    :return: TODO - 返回值说明\n'
                doc += '    """'
            
            return doc
        elif isinstance(node, ast.ClassDef):
            doc = f'    """{self._infer_class_description(node.name)}\n\n'
            doc += '    TODO - 类说明\n'
            doc += '    """'
            return doc
        
        return ""
    
    def _infer_function_description(self, name: str) -> str:
        """推断函数描述"""
        # 简单的启发式规则
        if name.startswith("get_"):
            return f"获取{name[4:]}"
        elif name.startswith("set_"):
            return f"设置{name[4:]}"
        elif name.startswith("is_") or name.startswith("has_"):
            return f"检查{name[3:]}"
        elif name.startswith("create_"):
            return f"创建{name[7:]}"
        elif name.startswith("delete_") or name.startswith("remove_"):
            return f"删除{name[7:]}"
        else:
            return f"{name}的功能"
    
    def _infer_class_description(self, name: str) -> str:
        """推断类描述"""
        return f"{name}类"
    
    def generate_api_documentation(
        self,
        code: str,
        api_type: str = "rest"  # rest, graphql, grpc
    ) -> Dict[str, Any]:
        """
        生成API文档
        
        Args:
            code: 代码内容（FastAPI路由等）
            api_type: API类型
            
        Returns:
            API文档
        """
        try:
            if api_type == "rest":
                return self._generate_rest_api_doc(code)
            else:
                return {
                    "success": False,
                    "error": f"不支持的API类型: {api_type}"
                }
        except Exception as e:
            logger.error(f"生成API文档失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_rest_api_doc(self, code: str) -> Dict[str, Any]:
        """生成REST API文档"""
        # 查找FastAPI路由装饰器
        routes = []
        
        # 简单的正则匹配
        route_pattern = r'@router\.(get|post|put|delete|patch)\s*\(["\']([^"\']+)["\']'
        matches = re.finditer(route_pattern, code)
        
        for match in matches:
            method = match.group(1).upper()
            path = match.group(2)
            routes.append({
                "method": method,
                "path": path,
                "summary": f"{method} {path}",
                "description": "TODO - API描述"
            })
        
        return {
            "success": True,
            "api_type": "REST",
            "routes": routes,
            "generated_at": datetime.now().isoformat()
        }
    
    def generate_readme(
        self,
        project_info: Dict[str, Any]
    ) -> str:
        """
        生成README文档
        
        Args:
            project_info: 项目信息
            
        Returns:
            README内容
        """
        name = project_info.get("name", "Project")
        description = project_info.get("description", "")
        version = project_info.get("version", "1.0.0")
        author = project_info.get("author", "")
        license_name = project_info.get("license", "MIT")
        
        readme = f"# {name}\n\n"
        readme += f"{description}\n\n" if description else ""
        readme += f"**版本**: {version}\n\n"
        if author:
            readme += f"**作者**: {author}\n\n"
        readme += f"**许可证**: {license_name}\n\n"
        readme += "---\n\n"
        readme += "## 安装\n\n"
        readme += "```bash\npip install -r requirements.txt\n```\n\n"
        readme += "## 使用\n\n"
        readme += "```python\n# TODO - 使用示例\n```\n\n"
        readme += "## 开发\n\n"
        readme += "```bash\n# TODO - 开发说明\n```\n\n"
        
        return readme


class CommandReplay:
    """
    命令回放系统
    记录和回放终端命令
    """
    
    def __init__(self):
        """初始化命令回放系统"""
        self.replay_history: List[Dict[str, Any]] = []
        self.max_history = 1000
    
    def record_command(
        self,
        command: str,
        result: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        记录命令执行
        
        Args:
            command: 执行的命令
            result: 执行结果
            metadata: 元数据
        """
        record = {
            "command": command,
            "result": result,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.replay_history.append(record)
        if len(self.replay_history) > self.max_history:
            self.replay_history = self.replay_history[-self.max_history:]
    
    def get_replay_history(
        self,
        limit: int = 50,
        filter_command: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取回放历史
        
        Args:
            limit: 返回数量限制
            filter_command: 过滤命令（可选）
            
        Returns:
            回放历史记录
        """
        history = self.replay_history[-limit:]
        
        if filter_command:
            history = [
                record for record in history
                if filter_command.lower() in record["command"].lower()
            ]
        
        return history
    
    def replay_command(
        self,
        command_id: Optional[str] = None,
        command: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        回放命令
        
        Args:
            command_id: 命令ID（可选）
            command: 命令内容（可选）
            
        Returns:
            回放结果
        """
        if command_id:
            # 根据ID查找命令
            record = next(
                (r for r in self.replay_history if r.get("id") == command_id),
                None
            )
            if not record:
                return {
                    "success": False,
                    "error": f"未找到命令ID: {command_id}"
                }
            command = record["command"]
        
        if not command:
            return {
                "success": False,
                "error": "需要提供command_id或command"
            }
        
        return {
            "success": True,
            "command": command,
            "replay_at": datetime.now().isoformat(),
            "note": "需要实际执行命令以获取结果"
        }


class CursorIDEIntegration:
    """
    Cursor IDE集成
    与Cursor编辑器集成，提供代码编辑、补全等功能
    """
    
    def __init__(self):
        """初始化Cursor集成"""
        self.cursor_config_path = Path.home() / ".cursor" / "config.json"
        self.is_cursor_available = self._check_cursor_available()
    
    def _check_cursor_available(self) -> bool:
        """检查Cursor是否可用"""
        # 检查Cursor是否安装
        import shutil
        cursor_paths = [
            "/Applications/Cursor.app/Contents/MacOS/Cursor",  # macOS
            shutil.which("cursor"),  # PATH中
        ]
        
        for path in cursor_paths:
            if path and Path(path).exists():
                return True
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """获取Cursor状态"""
        return {
            "available": self.is_cursor_available,
            "config_path": str(self.cursor_config_path),
            "config_exists": self.cursor_config_path.exists()
        }
    
    async def open_file(
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
        if not self.is_cursor_available:
            return {
                "success": False,
                "error": "Cursor不可用"
            }
        
        try:
            import subprocess
            
            cmd = ["cursor", file_path]
            if line_number:
                cmd.extend(["--goto", f"{file_path}:{line_number}"])
            
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            return {
                "success": True,
                "file_path": file_path,
                "line_number": line_number,
                "opened_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"在Cursor中打开文件失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_edits(
        self,
        file_path: str,
        edits: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        应用代码编辑
        
        Args:
            file_path: 文件路径
            edits: 编辑操作列表
            
        Returns:
            操作结果
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 应用编辑（从后往前，避免行号变化）
            edits_sorted = sorted(edits, key=lambda x: x.get('start_line', 0), reverse=True)
            
            for edit in edits_sorted:
                edit_type = edit.get('type', 'replace')
                start_line = edit.get('start_line', 0) - 1  # 转换为0-based
                end_line = edit.get('end_line', start_line + 1) - 1
                content = edit.get('content', '')
                
                if edit_type == 'replace':
                    lines[start_line:end_line] = [content + '\n']
                elif edit_type == 'insert':
                    lines.insert(start_line, content + '\n')
                elif edit_type == 'delete':
                    del lines[start_line:end_line]
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            return {
                "success": True,
                "file_path": file_path,
                "edits_applied": len(edits),
                "applied_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"应用编辑失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 全局实例
documentation_generator = DocumentationGenerator()
command_replay = CommandReplay()
cursor_ide_integration = CursorIDEIntegration()

