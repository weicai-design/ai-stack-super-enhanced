#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stack Super Enhanced - 数据库文件处理器
功能：处理各种数据库文件格式，提取表结构、数据和关系
支持格式：SQLite, CSV, Excel, JSON, XML等数据库相关文件
"""

import hashlib
import json
import logging
import os
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

import chardet
import pandas as pd

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


class DatabaseFileHandler(FileProcessorBase):
    """
    智能数据库文件处理器
    支持多种数据库文件格式的深度解析和数据提取
    """

    def __init__(self):
        super().__init__()
        self.supported_formats = [
            ".db",
            ".sqlite",
            ".sqlite3",
            ".csv",
            ".xlsx",
            ".xls",
            ".json",
            ".xml",
        ]
        self.processing_strategies = {
            ".db": self._process_sqlite,
            ".sqlite": self._process_sqlite,
            ".sqlite3": self._process_sqlite,
            ".csv": self._process_csv,
            ".xlsx": self._process_excel,
            ".xls": self._process_excel,
            ".json": self._process_json,
            ".xml": self._process_xml,
        }

    async def initialize(self, config: Dict[str, Any], core_services: Dict[str, Any]):
        """初始化处理器"""
        await super().initialize(config, core_services)
        self.max_rows_per_table = config.get("max_rows_per_table", 1000)
        self.include_sample_data = config.get("include_sample_data", True)
        self.extract_schema = config.get("extract_schema", True)
        self.analyze_relationships = config.get("analyze_relationships", True)
        self.data_quality_checks = config.get("data_quality_checks", True)

        logger.info(
            f"数据库文件处理器初始化完成，支持格式: {list(self.processing_strategies.keys())}"
        )

    def get_supported_formats(self) -> List[str]:
        """返回支持的格式列表"""
        return self.supported_formats

    async def process_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        处理数据库文件的主要方法

        Args:
            file_path: 文件路径
            **kwargs: 额外参数

        Returns:
            处理结果字典
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"数据库文件不存在: {file_path}")

            file_ext = file_path.suffix.lower()
            if file_ext not in self.processing_strategies:
                raise ValueError(f"不支持的数据库文件格式: {file_ext}")

            # 调用对应的处理策略
            process_func = self.processing_strategies[file_ext]
            result = await process_func(file_path, **kwargs)

            # 后处理和质量检查
            result = await self._post_process_result(result, file_path)

            logger.info(
                f"数据库文件处理完成: {file_path}, 表数量: {result.get('table_count', 0)}"
            )
            return result

        except Exception as e:
            logger.error(f"数据库文件处理失败 {file_path}: {str(e)}")
            raise

    async def _process_sqlite(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """处理SQLite数据库文件"""
        try:
            conn = sqlite3.connect(file_path)
            conn.row_factory = sqlite3.Row

            result = {
                "database_type": "sqlite",
                "tables": [],
                "schema_info": {},
                "relationships": [],
                "statistics": {},
            }

            # 获取所有表
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            result["table_count"] = len(tables)

            for table_name in tables:
                table_info = await self._extract_table_info(conn, table_name)
                result["tables"].append(table_info)

            # 分析关系
            if self.analyze_relationships:
                result["relationships"] = await self._analyze_sqlite_relationships(conn)

            # 数据库统计信息
            result["statistics"] = await self._calculate_database_statistics(
                conn, tables
            )

            conn.close()
            return result

        except Exception as e:
            logger.error(f"SQLite处理错误: {str(e)}")
            raise

    async def _process_csv(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """处理CSV文件"""
        try:
            # 检测文件编码
            encoding = await self._detect_encoding(file_path)

            # 读取CSV文件
            df = pd.read_csv(
                file_path, encoding=encoding, nrows=self.max_rows_per_table
            )

            result = {
                "database_type": "csv",
                "tables": [
                    {
                        "table_name": file_path.stem,
                        "columns": await self._extract_csv_schema(df),
                        "sample_data": (
                            await self._get_sample_data(df)
                            if self.include_sample_data
                            else []
                        ),
                        "row_count": len(df),
                        "data_quality": await self._check_data_quality(df),
                    }
                ],
                "schema_info": {"file_encoding": encoding, "delimiter": ","},
                "relationships": [],
                "statistics": {"total_rows": len(df), "total_columns": len(df.columns)},
            }

            return result

        except Exception as e:
            logger.error(f"CSV处理错误: {str(e)}")
            raise

    async def _process_excel(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """处理Excel文件"""
        try:
            # 读取Excel文件
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names

            result = {
                "database_type": "excel",
                "tables": [],
                "schema_info": {
                    "sheet_names": sheet_names,
                    "file_format": file_path.suffix,
                },
                "relationships": [],
                "statistics": {},
            }

            total_rows = 0
            total_columns = 0

            for sheet_name in sheet_names:
                df = pd.read_excel(
                    file_path, sheet_name=sheet_name, nrows=self.max_rows_per_table
                )

                table_info = {
                    "table_name": sheet_name,
                    "columns": await self._extract_excel_schema(df),
                    "sample_data": (
                        await self._get_sample_data(df)
                        if self.include_sample_data
                        else []
                    ),
                    "row_count": len(df),
                    "data_quality": await self._check_data_quality(df),
                }

                result["tables"].append(table_info)
                total_rows += len(df)
                total_columns += len(df.columns)

            result["table_count"] = len(sheet_names)
            result["statistics"] = {
                "total_rows": total_rows,
                "total_columns": total_columns,
                "sheet_count": len(sheet_names),
            }

            return result

        except Exception as e:
            logger.error(f"Excel处理错误: {str(e)}")
            raise

    async def _process_json(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """处理JSON文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            result = {
                "database_type": "json",
                "tables": [],
                "schema_info": {
                    "json_structure": await self._analyze_json_structure(data)
                },
                "relationships": [],
                "statistics": {},
            }

            # 根据JSON结构创建虚拟表
            tables = await self._extract_json_tables(data)
            result["tables"] = tables
            result["table_count"] = len(tables)

            # 统计信息
            total_rows = sum(len(table.get("sample_data", [])) for table in tables)
            result["statistics"]["total_rows"] = total_rows
            result["statistics"]["total_columns"] = sum(
                len(table.get("columns", [])) for table in tables
            )

            return result

        except Exception as e:
            logger.error(f"JSON处理错误: {str(e)}")
            raise

    async def _process_xml(self, file_path: Path, **kwargs) -> Dict[str, Any]:
        """处理XML文件"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            result = {
                "database_type": "xml",
                "tables": [],
                "schema_info": {
                    "root_element": root.tag,
                    "xml_structure": await self._analyze_xml_structure(root),
                },
                "relationships": [],
                "statistics": {},
            }

            # 提取XML数据为表格形式
            tables = await self._extract_xml_tables(root)
            result["tables"] = tables
            result["table_count"] = len(tables)

            return result

        except Exception as e:
            logger.error(f"XML处理错误: {str(e)}")
            raise

    async def _extract_table_info(
        self, conn: sqlite3.Connection, table_name: str
    ) -> Dict[str, Any]:
        """提取SQLite表信息"""
        cursor = conn.cursor()

        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append(
                {
                    "name": row[1],
                    "type": row[2],
                    "not_null": bool(row[3]),
                    "default_value": row[4],
                    "primary_key": bool(row[5]),
                }
            )

        # 获取样本数据
        sample_data = []
        if self.include_sample_data:
            try:
                cursor.execute(
                    f"SELECT * FROM {table_name} LIMIT {self.max_rows_per_table}"
                )
                sample_data = [dict(row) for row in cursor.fetchall()]
            except Exception as e:
                logger.warning(f"无法获取表 {table_name} 的样本数据: {str(e)}")

        # 数据质量检查
        data_quality = {}
        if self.data_quality_checks:
            data_quality = await self._check_sqlite_data_quality(
                conn, table_name, columns
            )

        return {
            "table_name": table_name,
            "columns": columns,
            "sample_data": sample_data,
            "row_count": await self._get_table_row_count(conn, table_name),
            "data_quality": data_quality,
            "indexes": await self._get_table_indexes(conn, table_name),
        }

    async def _analyze_sqlite_relationships(
        self, conn: sqlite3.Connection
    ) -> List[Dict[str, Any]]:
        """分析SQLite表关系"""
        relationships = []
        cursor = conn.cursor()

        # 获取外键关系
        cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        tables = [row[1] for row in cursor.fetchall()]

        for table in tables:
            try:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                for fk in cursor.fetchall():
                    relationships.append(
                        {
                            "from_table": table,
                            "from_column": fk[3],
                            "to_table": fk[2],
                            "to_column": fk[4],
                            "relationship_type": "foreign_key",
                        }
                    )
            except:
                continue

        return relationships

    async def _calculate_database_statistics(
        self, conn: sqlite3.Connection, tables: List[str]
    ) -> Dict[str, Any]:
        """计算数据库统计信息"""
        cursor = conn.cursor()

        total_rows = 0
        total_columns = 0

        for table in tables:
            try:
                row_count = await self._get_table_row_count(conn, table)
                total_rows += row_count

                cursor.execute(f"PRAGMA table_info({table})")
                total_columns += len(cursor.fetchall())
            except:
                continue

        return {
            "total_tables": len(tables),
            "total_rows": total_rows,
            "total_columns": total_columns,
            "database_size": await self._get_database_size(conn),
        }

    async def _extract_csv_schema(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """提取CSV文件结构"""
        columns = []

        for col_name, col_type in df.dtypes.items():
            columns.append(
                {
                    "name": col_name,
                    "type": str(col_type),
                    "null_count": df[col_name].isnull().sum(),
                    "unique_count": df[col_name].nunique(),
                }
            )

        return columns

    async def _extract_excel_schema(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """提取Excel工作表结构"""
        return await self._extract_csv_schema(df)

    async def _analyze_json_structure(
        self, data: Any, path: str = ""
    ) -> Dict[str, Any]:
        """分析JSON结构"""
        if isinstance(data, dict):
            structure = {"type": "object", "properties": {}, "path": path}
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                structure["properties"][key] = await self._analyze_json_structure(
                    value, new_path
                )
            return structure
        elif isinstance(data, list):
            if data:
                return {
                    "type": "array",
                    "item_type": await self._analyze_json_structure(
                        data[0], f"{path}[]"
                    ),
                    "path": path,
                    "length": len(data),
                }
            else:
                return {
                    "type": "array",
                    "item_type": "unknown",
                    "path": path,
                    "length": 0,
                }
        else:
            return {
                "type": type(data).__name__,
                "value_sample": str(data)[:100] if data else None,
                "path": path,
            }

    async def _extract_json_tables(self, data: Any) -> List[Dict[str, Any]]:
        """从JSON数据提取表格结构"""
        tables = []

        if isinstance(data, dict):
            # 将字典视为一个表
            table_data = self._flatten_json_dict(data)
            if table_data:
                df = pd.DataFrame([table_data])
                tables.append(
                    {
                        "table_name": "root",
                        "columns": await self._extract_csv_schema(df),
                        "sample_data": (
                            await self._get_sample_data(df)
                            if self.include_sample_data
                            else []
                        ),
                        "row_count": 1,
                        "data_quality": await self._check_data_quality(df),
                    }
                )
        elif isinstance(data, list):
            # 将列表视为多个行
            if data and all(isinstance(item, dict) for item in data):
                # 所有元素都是字典，可以转换为DataFrame
                df = pd.DataFrame(data)
                tables.append(
                    {
                        "table_name": "items",
                        "columns": await self._extract_csv_schema(df),
                        "sample_data": (
                            await self._get_sample_data(df)
                            if self.include_sample_data
                            else []
                        ),
                        "row_count": len(df),
                        "data_quality": await self._check_data_quality(df),
                    }
                )

        return tables

    async def _analyze_xml_structure(self, element, depth: int = 0) -> Dict[str, Any]:
        """分析XML结构"""
        if depth > 10:  # 防止无限递归
            return {"type": "too_deep"}

        structure = {
            "tag": element.tag,
            "attributes": list(element.attrib.keys()),
            "children": {},
            "text": (
                element.text.strip() if element.text and element.text.strip() else None
            ),
        }

        # 分析子元素
        child_tags = {}
        for child in element:
            if child.tag not in child_tags:
                child_tags[child.tag] = await self._analyze_xml_structure(
                    child, depth + 1
                )

        structure["children"] = child_tags
        return structure

    async def _extract_xml_tables(self, root_element) -> List[Dict[str, Any]]:
        """从XML数据提取表格结构"""
        tables = []

        async def extract_elements(element, table_name: str) -> List[Dict]:
            """提取重复元素作为表格行"""
            rows = []

            # 检查是否有重复的子元素
            child_counts = {}
            for child in element:
                child_counts[child.tag] = child_counts.get(child.tag, 0) + 1

            # 如果有重复元素，将其作为表格
            for tag, count in child_counts.items():
                if count > 1:
                    table_rows = []
                    for child in element.findall(tag):
                        row_data = self._flatten_xml_element(child)
                        table_rows.append(row_data)

                    if table_rows:
                        df = pd.DataFrame(table_rows)
                        tables.append(
                            {
                                "table_name": f"{table_name}_{tag}",
                                "columns": await self._extract_csv_schema(df),
                                "sample_data": (
                                    await self._get_sample_data(df)
                                    if self.include_sample_data
                                    else []
                                ),
                                "row_count": len(df),
                                "data_quality": await self._check_data_quality(df),
                            }
                        )

            return rows

        # 从根元素开始提取
        await extract_elements(root_element, "root")
        return tables

    def _flatten_json_dict(self, data: Dict, prefix: str = "") -> Dict:
        """展平JSON字典"""
        flattened = {}
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flattened.update(self._flatten_json_dict(value, full_key))
            elif isinstance(value, list):
                # 处理列表 - 转换为字符串或进一步处理
                flattened[full_key] = str(value)
            else:
                flattened[full_key] = value
        return flattened

    def _flatten_xml_element(self, element) -> Dict:
        """展平XML元素"""
        data = {
            "_tag": element.tag,
            "_text": (
                element.text.strip() if element.text and element.text.strip() else None
            ),
        }

        # 添加属性
        for attr, value in element.attrib.items():
            data[f"@{attr}"] = value

        # 添加子元素（简单处理）
        for child in element:
            if len(child) == 0:  # 没有子元素的简单元素
                data[child.tag] = child.text

        return data

    async def _get_sample_data(
        self, df: pd.DataFrame, sample_size: int = 10
    ) -> List[Dict]:
        """获取样本数据"""
        sample_size = min(sample_size, len(df))
        sample_df = df.head(sample_size)

        # 转换数据类型以便JSON序列化
        sample_data = []
        for _, row in sample_df.iterrows():
            row_dict = {}
            for col, value in row.items():
                # 处理无法序列化的类型
                if pd.isna(value):
                    row_dict[col] = None
                elif isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
                    row_dict[col] = value.isoformat()
                else:
                    row_dict[col] = value
            sample_data.append(row_dict)

        return sample_data

    async def _check_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """检查数据质量"""
        if df.empty:
            return {"status": "empty_dataset"}

        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "completeness": {},
            "uniqueness": {},
            "data_types": {},
        }

        for column in df.columns:
            # 完整性检查
            null_count = df[column].isnull().sum()
            completeness = 1 - (null_count / len(df))

            # 唯一性检查
            unique_count = df[column].nunique()
            uniqueness = unique_count / len(df) if len(df) > 0 else 0

            quality_report["completeness"][column] = completeness
            quality_report["uniqueness"][column] = uniqueness
            quality_report["data_types"][column] = str(df[column].dtype)

        return quality_report

    async def _check_sqlite_data_quality(
        self, conn: sqlite3.Connection, table_name: str, columns: List[Dict]
    ) -> Dict[str, Any]:
        """检查SQLite数据质量"""
        cursor = conn.cursor()
        quality_report = {"table_name": table_name, "column_quality": {}}

        for column in columns:
            col_name = column["name"]
            col_type = column["type"]

            try:
                # 检查空值
                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE {col_name} IS NULL"
                )
                null_count = cursor.fetchone()[0]

                # 检查唯一值
                cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table_name}")
                unique_count = cursor.fetchone()[0]

                # 获取总行数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_count = cursor.fetchone()[0]

                quality_report["column_quality"][col_name] = {
                    "null_count": null_count,
                    "completeness": (
                        1 - (null_count / total_count) if total_count > 0 else 0
                    ),
                    "unique_count": unique_count,
                    "uniqueness": unique_count / total_count if total_count > 0 else 0,
                    "data_type": col_type,
                }

            except Exception as e:
                quality_report["column_quality"][col_name] = {"error": str(e)}

        return quality_report

    async def _get_table_row_count(
        self, conn: sqlite3.Connection, table_name: str
    ) -> int:
        """获取表行数"""
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

    async def _get_table_indexes(
        self, conn: sqlite3.Connection, table_name: str
    ) -> List[Dict]:
        """获取表索引"""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = []

        for row in cursor.fetchall():
            index_info = {"name": row[1], "unique": bool(row[2])}
            indexes.append(index_info)

        return indexes

    async def _get_database_size(self, conn: sqlite3.Connection) -> int:
        """获取数据库文件大小"""
        cursor = conn.cursor()
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]

        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]

        return page_size * page_count

    async def _detect_encoding(self, file_path: Path) -> str:
        """检测文件编码"""
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # 读取前10KB进行检测
                result = chardet.detect(raw_data)
                encoding = result["encoding"] or "utf-8"
                return encoding
        except:
            return "utf-8"

    async def _post_process_result(
        self, result: Dict[str, Any], file_path: Path
    ) -> Dict[str, Any]:
        """后处理结果"""

        # 添加文件信息
        result["file_info"] = {
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "file_format": file_path.suffix,
            "modified_time": file_path.stat().st_mtime,
            "md5_hash": await self._calculate_file_hash(file_path),
        }

        # 添加处理元数据
        result["processing_metadata"] = {
            "max_rows_per_table": self.max_rows_per_table,
            "include_sample_data": self.include_sample_data,
            "extract_schema": self.extract_schema,
            "analyze_relationships": self.analyze_relationships,
            "data_quality_checks": self.data_quality_checks,
            "processing_time": self._get_timestamp(),
            "processing_id": self._generate_processing_id(),
        }

        # 质量评估
        result["quality_assessment"] = await self._assess_quality(result)

        return result

    async def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            hasher = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return "unknown"

    async def _assess_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        quality = {"overall_score": 0, "aspects": {}}

        scores = []

        # 结构完整性
        if result.get("table_count", 0) > 0:
            structure_score = min(1.0, result["table_count"] / 10)  # 标准化
            quality["aspects"]["structure"] = structure_score
            scores.append(structure_score)

        # 数据完整性
        if "statistics" in result:
            total_rows = result["statistics"].get("total_rows", 0)
            data_score = min(1.0, total_rows / 1000)  # 标准化
            quality["aspects"]["data_volume"] = data_score
            scores.append(data_score)

        # 模式质量
        if result.get("tables"):
            schema_scores = []
            for table in result["tables"]:
                if table.get("columns"):
                    schema_scores.append(min(1.0, len(table["columns"]) / 20))
            if schema_scores:
                schema_score = sum(schema_scores) / len(schema_scores)
                quality["aspects"]["schema"] = schema_score
                scores.append(schema_score)

        # 计算总体分数
        if scores:
            quality["overall_score"] = sum(scores) / len(scores)

        return quality

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
        """停止处理器"""
        logger.info("数据库文件处理器停止完成")

    async def reload_config(self, new_config: Dict[str, Any]):
        """重新加载配置"""
        self.max_rows_per_table = new_config.get(
            "max_rows_per_table", self.max_rows_per_table
        )
        self.include_sample_data = new_config.get(
            "include_sample_data", self.include_sample_data
        )
        self.extract_schema = new_config.get("extract_schema", self.extract_schema)
        self.analyze_relationships = new_config.get(
            "analyze_relationships", self.analyze_relationships
        )
        self.data_quality_checks = new_config.get(
            "data_quality_checks", self.data_quality_checks
        )

        logger.info("数据库文件处理器配置已更新")


# 导出类
__all__ = ["DatabaseFileHandler"]
