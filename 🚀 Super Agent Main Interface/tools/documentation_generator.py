#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文档自动生成工具
支持API文档、架构文档、用户手册的自动生成
"""

from __future__ import annotations

import ast
import inspect
import json
import logging
import os
import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type
from uuid import uuid4

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


class DocumentType(str, Enum):
    """文档类型"""
    API_DOCS = "api_docs"
    ARCHITECTURE = "architecture"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    DEPLOYMENT_GUIDE = "deployment_guide"
    TROUBLESHOOTING = "troubleshooting"


class OutputFormat(str, Enum):
    """输出格式"""
    MARKDOWN = "markdown"
    HTML = "html"
    PDF = "pdf"
    JSON = "json"


@dataclass
class APIParameter:
    """API参数"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    default: Any = None
    example: Any = None


@dataclass
class APIResponse:
    """API响应"""
    status_code: int
    description: str
    schema: Optional[Dict[str, Any]] = None
    example: Optional[Dict[str, Any]] = None


@dataclass
class APIEndpoint:
    """API端点"""
    method: str
    path: str
    summary: str
    description: str = ""
    parameters: List[APIParameter] = field(default_factory=list)
    responses: List[APIResponse] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class APIModule:
    """API模块"""
    name: str
    description: str
    endpoints: List[APIEndpoint] = field(default_factory=list)


@dataclass
class CodeExample:
    """代码示例"""
    language: str
    code: str
    description: str = ""


@dataclass
class DocumentationSection:
    """文档章节"""
    title: str
    content: str
    level: int = 2
    subsections: List[DocumentationSection] = field(default_factory=list)
    code_examples: List[CodeExample] = field(default_factory=list)
    images: List[str] = field(default_factory=list)


@dataclass
class GeneratedDocument:
    """生成的文档"""
    document_id: str
    title: str
    document_type: DocumentType
    format: OutputFormat
    content: str
    sections: List[DocumentationSection] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class DocumentationExtractor(ABC):
    """文档提取器接口"""
    
    @abstractmethod
    def extract(self, source_path: str) -> Dict[str, Any]:
        """从源代码提取文档信息"""
        pass


class PythonDocstringExtractor(DocumentationExtractor):
    """Python文档字符串提取器"""
    
    def extract(self, source_path: str) -> Dict[str, Any]:
        """从Python文件提取文档信息"""
        try:
            with open(source_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            modules = []
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Module):
                    module_doc = ast.get_docstring(node)
                    if module_doc:
                        modules.append({
                            "type": "module",
                            "name": Path(source_path).stem,
                            "docstring": module_doc,
                            "file_path": source_path
                        })
                
                elif isinstance(node, ast.ClassDef):
                    class_doc = ast.get_docstring(node)
                    classes.append({
                        "type": "class",
                        "name": node.name,
                        "docstring": class_doc or "",
                        "line_number": node.lineno,
                        "methods": self._extract_methods(node)
                    })
                
                elif isinstance(node, ast.FunctionDef):
                    func_doc = ast.get_docstring(node)
                    functions.append({
                        "type": "function",
                        "name": node.name,
                        "docstring": func_doc or "",
                        "line_number": node.lineno,
                        "parameters": self._extract_parameters(node),
                        "returns": self._extract_return_annotation(node)
                    })
            
            return {
                "modules": modules,
                "classes": classes,
                "functions": functions,
                "file_path": source_path
            }
            
        except Exception as e:
            logger.error(f"提取文档失败 {source_path}: {e}")
            return {}
    
    def _extract_methods(self, class_node: ast.ClassDef) -> List[Dict[str, Any]]:
        """提取类方法"""
        methods = []
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                method_doc = ast.get_docstring(node)
                methods.append({
                    "name": node.name,
                    "docstring": method_doc or "",
                    "parameters": self._extract_parameters(node)
                })
        
        return methods
    
    def _extract_parameters(self, func_node: ast.FunctionDef) -> List[Dict[str, Any]]:
        """提取函数参数"""
        parameters = []
        
        for arg in func_node.args.args:
            param_name = arg.arg
            param_type = "Any"
            
            # 尝试从类型注解获取类型
            if func_node.args.annotations and arg.arg in func_node.args.annotations:
                annotation = func_node.args.annotations[arg.arg]
                if isinstance(annotation, ast.Name):
                    param_type = annotation.id
            
            parameters.append({
                "name": param_name,
                "type": param_type,
                "required": True
            })
        
        return parameters
    
    def _extract_return_annotation(self, func_node: ast.FunctionDef) -> Optional[str]:
        """提取返回类型注解"""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                return func_node.returns.id
        return None


class APIDocumentationGenerator:
    """API文档生成器"""
    
    def __init__(self, template_dir: str = "templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
    
    def generate_openapi_spec(self, endpoints: List[APIEndpoint]) -> Dict[str, Any]:
        """生成OpenAPI规范"""
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "AI Stack API",
                "version": "1.0.0",
                "description": "AI Stack Super Enhanced API Documentation"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        for endpoint in endpoints:
            path_item = openapi_spec["paths"].setdefault(endpoint.path, {})
            
            path_item[endpoint.method.lower()] = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": [
                    {
                        "name": param.name,
                        "in": "query" if "?" in endpoint.path else "path",
                        "required": param.required,
                        "schema": {"type": param.type},
                        "description": param.description
                    }
                    for param in endpoint.parameters
                ],
                "responses": {
                    str(response.status_code): {
                        "description": response.description,
                        "content": {
                            "application/json": {
                                "schema": response.schema or {},
                                "example": response.example or {}
                            }
                        }
                    }
                    for response in endpoint.responses
                },
                "tags": endpoint.tags,
                "deprecated": endpoint.deprecated
            }
        
        return openapi_spec
    
    def generate_markdown_docs(self, modules: List[APIModule]) -> GeneratedDocument:
        """生成Markdown格式API文档"""
        content = "# API 文档\n\n"
        
        for module in modules:
            content += f"## {module.name}\n\n"
            content += f"{module.description}\n\n"
            
            for endpoint in module.endpoints:
                content += f"### {endpoint.method.upper()} {endpoint.path}\n\n"
                content += f"**摘要:** {endpoint.summary}\n\n"
                
                if endpoint.description:
                    content += f"**描述:** {endpoint.description}\n\n"
                
                if endpoint.parameters:
                    content += "**参数:**\n\n"
                    content += "| 参数名 | 类型 | 必需 | 描述 |\n"
                    content += "|--------|------|------|------|\n"
                    
                    for param in endpoint.parameters:
                        content += f"| {param.name} | {param.type} | {'是' if param.required else '否'} | {param.description} |\n"
                    content += "\n"
                
                if endpoint.responses:
                    content += "**响应:**\n\n"
                    for response in endpoint.responses:
                        content += f"- **{response.status_code}:** {response.description}\n"
                    content += "\n"
        
        return GeneratedDocument(
            document_id=str(uuid4()),
            title="API 文档",
            document_type=DocumentType.API_DOCS,
            format=OutputFormat.MARKDOWN,
            content=content
        )


class ArchitectureDocumentationGenerator:
    """架构文档生成器"""
    
    def generate_architecture_docs(self, project_root: str) -> GeneratedDocument:
        """生成架构文档"""
        content = "# 系统架构设计文档\n\n"
        
        # 分析项目结构
        project_structure = self._analyze_project_structure(project_root)
        
        content += "## 项目结构\n\n"
        content += self._format_project_structure(project_structure)
        
        content += "## 核心模块\n\n"
        content += self._analyze_core_modules(project_root)
        
        content += "## 数据流设计\n\n"
        content += self._analyze_data_flow(project_root)
        
        return GeneratedDocument(
            document_id=str(uuid4()),
            title="系统架构设计文档",
            document_type=DocumentType.ARCHITECTURE,
            format=OutputFormat.MARKDOWN,
            content=content
        )
    
    def _analyze_project_structure(self, project_root: str) -> Dict[str, Any]:
        """分析项目结构"""
        structure = {}
        root_path = Path(project_root)
        
        for item in root_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure[item.name] = self._analyze_directory(item)
            elif item.is_file() and item.suffix in ['.py', '.md', '.yaml', '.yml']:
                structure[item.name] = {"type": "file", "size": item.stat().st_size}
        
        return structure
    
    def _analyze_directory(self, directory: Path) -> Dict[str, Any]:
        """分析目录结构"""
        dir_info = {"type": "directory", "files": [], "subdirectories": {}}
        
        for item in directory.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dir_info["subdirectories"][item.name] = self._analyze_directory(item)
            elif item.is_file() and item.suffix in ['.py', '.md', '.yaml', '.yml']:
                dir_info["files"].append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
        
        return dir_info
    
    def _format_project_structure(self, structure: Dict[str, Any]) -> str:
        """格式化项目结构"""
        def format_tree(data: Dict[str, Any], level: int = 0) -> str:
            indent = "  " * level
            result = ""
            
            for name, info in data.items():
                if info["type"] == "directory":
                    result += f"{indent}📁 {name}/\n"
                    result += format_tree(info["subdirectories"], level + 1)
                    
                    for file_info in info["files"]:
                        result += f"{indent}  📄 {file_info['name']}\n"
                else:
                    result += f"{indent}📄 {name}\n"
            
            return result
        
        return f"```\n{format_tree(structure)}\n```\n\n"
    
    def _analyze_core_modules(self, project_root: str) -> str:
        """分析核心模块"""
        content = ""
        
        # 查找主要的Python模块
        python_files = list(Path(project_root).rglob("*.py"))
        core_modules = []
        
        for py_file in python_files:
            if any(part.startswith('.') or part in ['tests', 'venv', '__pycache__'] 
                   for part in py_file.parts):
                continue
            
            # 分析文件内容，识别主要类和函数
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                
                tree = ast.parse(file_content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        core_modules.append({
                            "name": node.name,
                            "file": str(py_file.relative_to(project_root)),
                            "type": "class"
                        })
                    elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                        core_modules.append({
                            "name": node.name,
                            "file": str(py_file.relative_to(project_root)),
                            "type": "function"
                        })
                        
            except Exception as e:
                logger.warning(f"分析文件失败 {py_file}: {e}")
        
        if core_modules:
            content += "| 模块名 | 类型 | 文件路径 |\n"
            content += "|--------|------|----------|\n"
            
            for module in core_modules[:20]:  # 限制显示数量
                content += f"| {module['name']} | {module['type']} | {module['file']} |\n"
            content += "\n"
        
        return content
    
    def _analyze_data_flow(self, project_root: str) -> str:
        """分析数据流"""
        return """
系统采用分层架构设计，数据流遵循以下模式：

1. **表示层**: 用户界面和API端点接收请求
2. **业务逻辑层**: 处理业务规则和数据验证
3. **数据访问层**: 与数据库和外部服务交互
4. **基础设施层**: 提供监控、日志、缓存等支持服务

数据流方向: 请求 → 表示层 → 业务逻辑层 → 数据访问层 → 响应
        """


class UserGuideGenerator:
    """用户手册生成器"""
    
    def generate_user_guide(self, project_root: str) -> GeneratedDocument:
        """生成用户手册"""
        content = "# 用户手册\n\n"
        
        content += "## 快速开始\n\n"
        content += self._generate_quick_start()
        
        content += "## 功能特性\n\n"
        content += self._generate_features()
        
        content += "## 使用示例\n\n"
        content += self._generate_usage_examples(project_root)
        
        content += "## 常见问题\n\n"
        content += self._generate_faq()
        
        return GeneratedDocument(
            document_id=str(uuid4()),
            title="用户手册",
            document_type=DocumentType.USER_GUIDE,
            format=OutputFormat.MARKDOWN,
            content=content
        )
    
    def _generate_quick_start(self) -> str:
        """生成快速开始指南"""
        return """
### 安装
```bash
pip install -r requirements.txt
```

### 配置
1. 复制配置文件模板
2. 修改配置参数
3. 启动服务

### 运行
```bash
python main.py
```
        """
    
    def _generate_features(self) -> str:
        """生成功能特性"""
        return """
- **多租户支持**: 支持多用户环境下的数据隔离
- **安全认证**: 基于JWT的安全认证机制
- **监控告警**: 实时监控和智能告警系统
- **插件架构**: 支持功能扩展的插件化架构
- **高性能缓存**: 多级缓存系统提升性能
        """
    
    def _generate_usage_examples(self, project_root: str) -> str:
        """生成使用示例"""
        examples = ""
        
        # 查找示例文件
        example_files = list(Path(project_root).rglob("*example*.py"))
        example_files.extend(list(Path(project_root).rglob("*demo*.py")))
        
        for example_file in example_files[:5]:  # 限制示例数量
            try:
                with open(example_file, 'r', encoding='utf-8') as f:
                    example_code = f.read()
                
                examples += f"### {example_file.stem}\n\n"
                examples += f"```python\n{example_code}\n```\n\n"
                
            except Exception as e:
                logger.warning(f"读取示例文件失败 {example_file}: {e}")
        
        return examples
    
    def _generate_faq(self) -> str:
        """生成常见问题"""
        return """
### Q: 如何配置数据库连接？
A: 修改config.py中的数据库连接参数

### Q: 如何添加新的API端点？
A: 在api模块中添加新的路由处理函数

### Q: 如何扩展插件功能？
A: 继承SecurityPluginBase类并实现相应方法
        """


class DocumentationGenerator:
    """文档生成器主类"""
    
    def __init__(self, project_root: str, output_dir: str = "docs"):
        self.project_root = Path(project_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.extractors = {
            ".py": PythonDocstringExtractor()
        }
        
        self.generators = {
            DocumentType.API_DOCS: APIDocumentationGenerator(),
            DocumentType.ARCHITECTURE: ArchitectureDocumentationGenerator(),
            DocumentType.USER_GUIDE: UserGuideGenerator()
        }
    
    def generate_all_documents(self) -> List[GeneratedDocument]:
        """生成所有文档"""
        documents = []
        
        # 生成API文档
        api_doc = self.generate_api_documentation()
        if api_doc:
            documents.append(api_doc)
            self._save_document(api_doc)
        
        # 生成架构文档
        arch_doc = self.generate_architecture_documentation()
        if arch_doc:
            documents.append(arch_doc)
            self._save_document(arch_doc)
        
        # 生成用户手册
        user_guide = self.generate_user_guide()
        if user_guide:
            documents.append(user_guide)
            self._save_document(user_guide)
        
        # 生成文档索引
        index_doc = self.generate_document_index(documents)
        if index_doc:
            documents.append(index_doc)
            self._save_document(index_doc)
        
        logger.info(f"生成 {len(documents)} 个文档文件")
        return documents
    
    def generate_api_documentation(self) -> Optional[GeneratedDocument]:
        """生成API文档"""
        try:
            # 提取API信息
            api_modules = self._extract_api_modules()
            
            if api_modules:
                generator = self.generators[DocumentType.API_DOCS]
                return generator.generate_markdown_docs(api_modules)
            
        except Exception as e:
            logger.error(f"生成API文档失败: {e}")
        
        return None
    
    def generate_architecture_documentation(self) -> Optional[GeneratedDocument]:
        """生成架构文档"""
        try:
            generator = self.generators[DocumentType.ARCHITECTURE]
            return generator.generate_architecture_docs(str(self.project_root))
        except Exception as e:
            logger.error(f"生成架构文档失败: {e}")
            return None
    
    def generate_user_guide(self) -> Optional[GeneratedDocument]:
        """生成用户手册"""
        try:
            generator = self.generators[DocumentType.USER_GUIDE]
            return generator.generate_user_guide(str(self.project_root))
        except Exception as e:
            logger.error(f"生成用户手册失败: {e}")
            return None
    
    def generate_document_index(self, documents: List[GeneratedDocument]) -> GeneratedDocument:
        """生成文档索引"""
        content = "# 文档索引\n\n"
        
        for doc in documents:
            filename = f"{doc.document_type.value}.md"
            content += f"- [{doc.title}]({filename})\n"
        
        return GeneratedDocument(
            document_id=str(uuid4()),
            title="文档索引",
            document_type=DocumentType.USER_GUIDE,
            format=OutputFormat.MARKDOWN,
            content=content
        )
    
    def _extract_api_modules(self) -> List[APIModule]:
        """提取API模块信息"""
        # 简化实现，实际项目中需要分析路由定义
        modules = []
        
        # 示例API模块
        auth_module = APIModule(
            name="认证模块",
            description="用户认证和授权相关API"
        )
        
        auth_module.endpoints.append(APIEndpoint(
            method="POST",
            path="/api/auth/login",
            summary="用户登录",
            description="使用用户名密码进行登录认证",
            parameters=[
                APIParameter("username", "string", True, "用户名"),
                APIParameter("password", "string", True, "密码")
            ],
            responses=[
                APIResponse(200, "登录成功", {"token": "string"}),
                APIResponse(401, "认证失败")
            ]
        ))
        
        modules.append(auth_module)
        
        return modules
    
    def _save_document(self, document: GeneratedDocument) -> None:
        """保存文档"""
        filename = f"{document.document_type.value}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(document.content)
        
        logger.info(f"文档已保存: {filepath}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) != 2:
        print("用法: python documentation_generator.py <项目根目录>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    
    if not Path(project_root).exists():
        print(f"项目目录不存在: {project_root}")
        sys.exit(1)
    
    generator = DocumentationGenerator(project_root)
    documents = generator.generate_all_documents()
    
    print(f"\n=== 文档生成完成 ===")
    print(f"生成文档数量: {len(documents)}")
    
    for doc in documents:
        print(f"- {doc.title} ({doc.document_type.value}.md)")


if __name__ == "__main__":
    main()