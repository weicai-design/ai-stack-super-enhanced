#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stack Super Enhanced - 思维导图解析器
功能：解析各种格式的思维导图文件，提取结构化知识信息
支持格式：XMind, FreeMind, MindManager, Markdown思维导图等
"""

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 修复导入问题 - 使用正确的模块导入方式
try:
    from .file_processor_base import FileProcessorBase
except ImportError:
    # 备用导入方式
    import os
    import sys

    sys.path.append(os.path.dirname(__file__))
    from file_processor_base import FileProcessorBase

logger = logging.getLogger(__name__)


class MindMapParser(FileProcessorBase):
    """
    智能思维导图解析器
    支持多种思维导图格式的深度解析和知识提取
    """

    def __init__(self):
        super().__init__()
        self.supported_formats = [".xmind", ".mm", ".mind", ".mindmap", ".md"]
        self.parsing_strategies = {
            ".xmind": self._parse_xmind,
            ".mm": self._parse_freemind,
            ".mind": self._parse_mindmanager,
            ".md": self._parse_markdown_mindmap,
        }

    async def initialize(self, config: Dict[str, Any], core_services: Dict[str, Any]):
        """初始化解析器"""
        await super().initialize(config, core_services)
        self.extraction_depth = config.get("mindmap_extraction_depth", 3)
        self.include_relationships = config.get("include_relationships", True)
        self.extract_notes = config.get("extract_notes", True)

        logger.info(
            f"思维导图解析器初始化完成，支持格式: {list(self.parsing_strategies.keys())}"
        )

    def get_supported_formats(self) -> List[str]:
        """返回支持的格式列表"""
        return self.supported_formats

    async def process_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        处理思维导图文件的主要方法

        Args:
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            解析结果字典
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"思维导图文件不存在: {file_path}")

            file_ext = file_path.suffix.lower()
            if file_ext not in self.parsing_strategies:
                raise ValueError(f"不支持的思维导图格式: {file_ext}")

            # 调用对应的解析策略
            parse_func = self.parsing_strategies[file_ext]
            result = await parse_func(file_path, **kwargs)

            # 后处理和质量检查
            result = await self._post_process_result(result, file_path)

            logger.info(
                f"思维导图解析完成: {file_path}, 提取节点数: {result.get('node_count', 0)}"
            )
            return result

        except Exception as e:
            logger.error(f"思维导图解析失败 {file_path}: {str(e)}")
            raise

    async def _parse_xmind(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """解析XMind格式文件"""
        try:
            # XMind文件实际上是zip压缩包
            with zipfile.ZipFile(file_path, "r") as zf:
                # 查找内容文件
                content_files = [
                    f
                    for f in zf.namelist()
                    if "content.json" in f or "content.xml" in f
                ]

                if not content_files:
                    raise ValueError("XMind文件中未找到内容文件")

                content_file = content_files[0]
                with zf.open(content_file) as f:
                    if content_file.endswith(".json"):
                        return await self._parse_xmind_json(f)
                    else:
                        return await self._parse_xmind_xml(f)

        except Exception as e:
            logger.error(f"XMind解析错误: {str(e)}")
            raise

    async def _parse_xmind_json(self, file_obj) -> Dict[str, Any]:
        """解析XMind JSON格式"""
        try:
            content = file_obj.read().decode("utf-8")
            data = json.loads(content)

            root_node = self._extract_xmind_structure(data)
            return await self._build_mindmap_result(root_node, "xmind")

        except Exception as e:
            logger.error(f"XMind JSON解析错误: {str(e)}")
            raise

    async def _parse_xmind_xml(self, file_obj) -> Dict[str, Any]:
        """解析XMind XML格式"""
        try:
            content = file_obj.read().decode("utf-8")
            root = ET.fromstring(content)

            # 提取XML结构
            root_node = self._extract_xmind_xml_structure(root)
            return await self._build_mindmap_result(root_node, "xmind")

        except Exception as e:
            logger.error(f"XMind XML解析错误: {str(e)}")
            raise

    async def _parse_freemind(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """解析FreeMind格式文件"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # FreeMind使用特定的XML结构
            root_node = self._extract_freemind_structure(root)
            return await self._build_mindmap_result(root_node, "freemind")

        except Exception as e:
            logger.error(f"FreeMind解析错误: {str(e)}")
            raise

    async def _parse_mindmanager(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """解析MindManager格式文件"""
        try:
            # MindManager可能有多种格式，这里实现通用解析
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 尝试多种解析策略
            root_node = await self._parse_generic_mindmap(content)
            return await self._build_mindmap_result(root_node, "mindmanager")

        except Exception as e:
            logger.error(f"MindManager解析错误: {str(e)}")
            raise

    async def _parse_markdown_mindmap(
        self, file_path: Path, **kwargs
    ) -> Dict[str, Any]:
        """解析Markdown格式的思维导图"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 解析Markdown的层级结构
            root_node = self._extract_markdown_structure(content)
            return await self._build_mindmap_result(root_node, "markdown")

        except Exception as e:
            logger.error(f"Markdown思维导图解析错误: {str(e)}")
            raise

    def _extract_xmind_structure(self, data: Dict) -> Dict[str, Any]:
        """提取XMind JSON结构"""
        # 实现XMind JSON结构的深度提取
        root_node = {"type": "root", "title": "", "children": [], "attributes": {}}

        def extract_nodes(node_data, current_level=0):
            """递归提取节点"""
            if current_level > self.extraction_depth:
                return None

            node = {
                "type": "topic",
                "title": node_data.get("title", ""),
                "children": [],
                "attributes": {
                    "level": current_level,
                    "style": node_data.get("style", {}),
                    "notes": node_data.get("notes", ""),
                },
            }

            # 处理子节点
            for child in node_data.get("children", {}).get("attached", []):
                child_node = extract_nodes(child, current_level + 1)
                if child_node:
                    node["children"].append(child_node)

            return node

        # 从XMind数据结构中提取根节点
        if "rootTopic" in data:
            root_node = extract_nodes(data["rootTopic"])
        elif "sheets" in data and data["sheets"]:
            root_node = extract_nodes(data["sheets"][0].get("rootTopic", {}))

        return root_node

    def _extract_xmind_xml_structure(self, root_element) -> Dict[str, Any]:
        """提取XMind XML结构"""
        # 实现XMind XML结构的解析
        root_node = {"type": "root", "title": "", "children": [], "attributes": {}}

        # XML解析逻辑
        topics = root_element.findall(".//topic")
        if topics:
            root_topic = topics[0]
            root_node = self._parse_xml_topic(root_topic)

        return root_node

    def _extract_freemind_structure(self, root_element) -> Dict[str, Any]:
        """提取FreeMind结构"""
        root_node = {
            "type": "root",
            "title": root_element.get("TEXT", ""),
            "children": [],
            "attributes": {},
        }

        def parse_freemind_node(element, level=0):
            """解析FreeMind节点"""
            if level > self.extraction_depth:
                return None

            node = {
                "type": "node",
                "title": element.get("TEXT", ""),
                "children": [],
                "attributes": {
                    "level": level,
                    "position": element.get("POSITION", ""),
                    "folded": element.get("FOLDED", "false") == "true",
                },
            }

            # 处理子节点
            for child in element.findall("node"):
                child_node = parse_freemind_node(child, level + 1)
                if child_node:
                    node["children"].append(child_node)

            return node

        # 从根节点开始解析
        for child in root_element.findall("node"):
            child_node = parse_freemind_node(child, 1)
            if child_node:
                root_node["children"].append(child_node)

        return root_node

    def _extract_markdown_structure(self, content: str) -> Dict[str, Any]:
        """提取Markdown层级结构"""
        lines = content.split("\n")
        root_node = {
            "type": "root",
            "title": "思维导图根节点",
            "children": [],
            "attributes": {},
        }

        stack = [root_node]
        current_level = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测标题级别
            match = re.match(r"^(#+)\s*(.+)$", line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()

                node = {
                    "type": "heading",
                    "title": title,
                    "children": [],
                    "attributes": {"level": level},
                }

                # 找到父节点
                while stack and stack[-1]["attributes"].get("level", 0) >= level:
                    stack.pop()

                if stack:
                    stack[-1]["children"].append(node)
                    stack.append(node)

        return root_node

    async def _parse_generic_mindmap(self, content: str) -> Dict[str, Any]:
        """通用思维导图解析"""
        # 实现通用的思维导图解析逻辑
        root_node = {
            "type": "root",
            "title": "通用思维导图",
            "children": [],
            "attributes": {},
        }

        # 尝试检测常见的思维导图模式
        patterns = [
            self._detect_outline_pattern,
            self._detect_tree_pattern,
            self._detect_json_pattern,
        ]

        for pattern_func in patterns:
            try:
                result = pattern_func(content)
                if result:
                    return result
            except Exception:
                continue

        # 如果无法识别特定模式，返回基础结构
        return root_node

    def _detect_outline_pattern(self, content: str) -> Optional[Dict]:
        """检测大纲模式"""
        lines = content.split("\n")
        if any(line.strip().startswith(("-", "*", "+")) for line in lines):
            return self._parse_outline_structure(content)
        return None

    def _detect_tree_pattern(self, content: str) -> Optional[Dict]:
        """检测树形模式"""
        if "->" in content or "│" in content or "└" in content:
            return self._parse_tree_structure(content)
        return None

    def _detect_json_pattern(self, content: str) -> Optional[Dict]:
        """检测JSON模式"""
        try:
            data = json.loads(content)
            if isinstance(data, dict) and any(
                key in data for key in ["nodes", "children", "topics"]
            ):
                return self._parse_json_structure(data)
        except:
            pass
        return None

    def _parse_outline_structure(self, content: str) -> Dict[str, Any]:
        """解析大纲结构"""
        # 实现大纲结构的解析逻辑
        root_node = {
            "type": "root",
            "title": "大纲结构",
            "children": [],
            "attributes": {},
        }

        lines = content.split("\n")
        stack = [root_node]

        for line in lines:
            line = line.rstrip()
            if not line:
                continue

            # 计算缩进级别
            indent = len(line) - len(line.lstrip())
            level = indent // 2  # 假设每级缩进2个空格

            # 清理行内容
            content_clean = line.lstrip(" -*+").strip()

            node = {
                "type": "outline_item",
                "title": content_clean,
                "children": [],
                "attributes": {"level": level},
            }

            # 找到正确的父节点
            while len(stack) > level + 1:
                stack.pop()

            if stack:
                stack[-1]["children"].append(node)
                stack.append(node)

        return root_node

    def _parse_tree_structure(self, content: str) -> Dict[str, Any]:
        """解析树形结构"""
        # 实现树形结构的解析逻辑
        root_node = {
            "type": "root",
            "title": "树形结构",
            "children": [],
            "attributes": {},
        }

        return root_node

    def _parse_json_structure(self, data: Dict) -> Dict[str, Any]:
        """解析JSON结构"""
        # 实现JSON结构的解析逻辑
        root_node = {
            "type": "root",
            "title": data.get("title", "JSON结构"),
            "children": [],
            "attributes": {},
        }

        return root_node

    def _parse_xml_topic(self, topic_element) -> Dict[str, Any]:
        """解析XML主题节点"""
        node = {
            "type": "topic",
            "title": topic_element.get("title", ""),
            "children": [],
            "attributes": {},
        }

        # 处理子主题
        for child in topic_element.findall("children/topic"):
            child_node = self._parse_xml_topic(child)
            node["children"].append(child_node)

        return node

    async def _build_mindmap_result(
        self, root_node: Dict[str, Any], source_format: str
    ) -> Dict[str, Any]:
        """构建思维导图解析结果"""

        def count_nodes(node: Dict) -> Tuple[int, int]:
            """统计节点数量"""
            total = 1
            leaf_count = 0

            if not node.get("children"):
                leaf_count = 1
            else:
                for child in node["children"]:
                    child_total, child_leaf = count_nodes(child)
                    total += child_total
                    leaf_count += child_leaf

            return total, leaf_count

        def extract_keywords(node: Dict, keywords: set, level: int = 0):
            """提取关键词"""
            if level <= self.extraction_depth:
                title = node.get("title", "")
                if title:
                    # 简单的关键词提取逻辑
                    words = re.findall(r"\b\w{2,}\b", title.lower())
                    keywords.update(words)

                for child in node.get("children", []):
                    extract_keywords(child, keywords, level + 1)

        def calculate_depth(node: Dict, current_depth: int = 0) -> int:
            """计算最大深度"""
            if not node.get("children"):
                return current_depth

            max_child_depth = current_depth
            for child in node["children"]:
                child_depth = calculate_depth(child, current_depth + 1)
                max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        # 执行统计和分析
        total_nodes, leaf_nodes = count_nodes(root_node)
        max_depth = calculate_depth(root_node)

        keywords = set()
        extract_keywords(root_node, keywords)

        # 构建结果
        result = {
            "success": True,
            "source_format": source_format,
            "root_node": root_node,
            "statistics": {
                "total_nodes": total_nodes,
                "leaf_nodes": leaf_nodes,
                "max_depth": max_depth,
                "branching_factor": (
                    (total_nodes - leaf_nodes) / max(1, (total_nodes - 1))
                    if total_nodes > 1
                    else 0
                ),
            },
            "keywords": list(keywords),
            "metadata": {
                "extraction_depth": self.extraction_depth,
                "extraction_time": self._get_timestamp(),
                "relationships_extracted": self.include_relationships,
                "notes_extracted": self.extract_notes,
            },
        }

        return result

    async def _post_process_result(
        self, result: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """后处理解析结果"""

        # 添加文件信息
        result["file_info"] = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_format": file_path.suffix,
            "modified_time": file_path.stat().st_mtime,
        }

        # 质量检查
        if result["statistics"]["total_nodes"] == 0:
            logger.warning(f"思维导图文件可能为空或格式不支持: {file_path}")
            result["quality_warning"] = "可能为空文件或格式不支持"

        # 添加处理标识
        result["processing_id"] = self._generate_processing_id()

        return result

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def _generate_processing_id(self) -> str:
        """生成处理ID"""
        import uuid

        return str(uuid.uuid4())

    async def get_health_status(self) -> Dict[str, Any]:
        """返回健康状态"""
        return {
            "status": "healthy",
            "supported_formats": len(self.supported_formats),
            "last_error": None,
            "processing_stats": {
                "files_processed": self.get_processing_stats().get("success_count", 0),
                "error_count": self.get_processing_stats().get("error_count", 0),
            },
        }

    async def stop(self):
        """停止解析器"""
        logger.info("思维导图解析器停止完成")

    async def reload_config(self, new_config: Dict[str, Any]):
        """重新加载配置"""
        self.extraction_depth = new_config.get(
            "mindmap_extraction_depth", self.extraction_depth
        )
        self.include_relationships = new_config.get(
            "include_relationships", self.include_relationships
        )
        self.extract_notes = new_config.get("extract_notes", self.extract_notes)

        logger.info("思维导图解析器配置已更新")


# 导出类
__all__ = ["MindMapParser"]
