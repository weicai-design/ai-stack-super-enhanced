#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Stack Super Enhanced - 60格式处理器注册表
功能：统一管理所有文件格式处理器，提供格式检测、处理器路由、统计等功能
支持格式：60+ 种常见文件格式
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

try:
    from .file_processor_base import FileProcessorBase, FileType, FileMetadata, ProcessingResult, ProcessingStatus
    from .universal_file_parser import UniversalFileParser
except ImportError:
    # 兼容性导入
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from file_processor_base import FileProcessorBase, FileType, FileMetadata, ProcessingResult, ProcessingStatus
    from universal_file_parser import UniversalFileParser

logger = logging.getLogger(__name__)


class FormatCategory(Enum):
    """格式分类"""
    OFFICE = "office"
    EBOOK = "ebook"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MINDMAP = "mindmap"
    DATABASE = "database"
    TEXT = "text"
    ARCHIVE = "archive"
    OTHER = "other"


class FormatProcessorRegistry:
    """
    60格式处理器注册表
    统一管理所有文件格式的处理器，提供格式检测、处理器路由、统计等功能
    """
    
    def __init__(self):
        self.parser = UniversalFileParser()
        self.parser.initialize()
        
        # 60+ 格式映射表（扩展自 UniversalFileParser）
        self._format_registry: Dict[str, Dict[str, Any]] = {
            # 办公文档 (15种)
            "doc": {"category": FormatCategory.OFFICE, "mime": "application/msword", "processor": "OfficeDocumentHandler"},
            "docx": {"category": FormatCategory.OFFICE, "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "processor": "OfficeDocumentHandler"},
            "docm": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-word.document.macroEnabled.12", "processor": "OfficeDocumentHandler"},
            "dot": {"category": FormatCategory.OFFICE, "mime": "application/msword", "processor": "OfficeDocumentHandler"},
            "dotx": {"category": FormatCategory.OFFICE, "mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.template", "processor": "OfficeDocumentHandler"},
            "xls": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-excel", "processor": "OfficeDocumentHandler"},
            "xlsx": {"category": FormatCategory.OFFICE, "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "processor": "OfficeDocumentHandler"},
            "xlsm": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-excel.sheet.macroEnabled.12", "processor": "OfficeDocumentHandler"},
            "xlsb": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-excel.sheet.binary.macroEnabled.12", "processor": "OfficeDocumentHandler"},
            "xlt": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-excel", "processor": "OfficeDocumentHandler"},
            "xltx": {"category": FormatCategory.OFFICE, "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.template", "processor": "OfficeDocumentHandler"},
            "ppt": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-powerpoint", "processor": "OfficeDocumentHandler"},
            "pptx": {"category": FormatCategory.OFFICE, "mime": "application/vnd.openxmlformats-officedocument.presentationml.presentation", "processor": "OfficeDocumentHandler"},
            "pptm": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-powerpoint.presentation.macroEnabled.12", "processor": "OfficeDocumentHandler"},
            "pdf": {"category": FormatCategory.OFFICE, "mime": "application/pdf", "processor": "OfficeDocumentHandler"},
            "odt": {"category": FormatCategory.OFFICE, "mime": "application/vnd.oasis.opendocument.text", "processor": "OfficeDocumentHandler"},
            "ods": {"category": FormatCategory.OFFICE, "mime": "application/vnd.oasis.opendocument.spreadsheet", "processor": "OfficeDocumentHandler"},
            "odp": {"category": FormatCategory.OFFICE, "mime": "application/vnd.oasis.opendocument.presentation", "processor": "OfficeDocumentHandler"},
            "rtf": {"category": FormatCategory.OFFICE, "mime": "application/rtf", "processor": "OfficeDocumentHandler"},
            "msg": {"category": FormatCategory.OFFICE, "mime": "application/vnd.ms-outlook", "processor": "OfficeDocumentHandler"},
            "eml": {"category": FormatCategory.OFFICE, "mime": "message/rfc822", "processor": "OfficeDocumentHandler"},
            
            # 电子书 (8种)
            "epub": {"category": FormatCategory.EBOOK, "mime": "application/epub+zip", "processor": "EbookExtractor"},
            "mobi": {"category": FormatCategory.EBOOK, "mime": "application/x-mobipocket-ebook", "processor": "EbookExtractor"},
            "azw": {"category": FormatCategory.EBOOK, "mime": "application/vnd.amazon.ebook", "processor": "EbookExtractor"},
            "azw3": {"category": FormatCategory.EBOOK, "mime": "application/vnd.amazon.ebook", "processor": "EbookExtractor"},
            "fb2": {"category": FormatCategory.EBOOK, "mime": "application/x-fictionbook+xml", "processor": "EbookExtractor"},
            "lit": {"category": FormatCategory.EBOOK, "mime": "application/x-ms-reader", "processor": "EbookExtractor"},
            "prc": {"category": FormatCategory.EBOOK, "mime": "application/x-palm-database", "processor": "EbookExtractor"},
            "txt": {"category": FormatCategory.EBOOK, "mime": "text/plain", "processor": "EbookExtractor"},
            
            # 编程文件 (30种)
            "py": {"category": FormatCategory.CODE, "mime": "text/x-python", "processor": "CodeAnalyzer"},
            "js": {"category": FormatCategory.CODE, "mime": "application/javascript", "processor": "CodeAnalyzer"},
            "jsx": {"category": FormatCategory.CODE, "mime": "text/jsx", "processor": "CodeAnalyzer"},
            "ts": {"category": FormatCategory.CODE, "mime": "application/typescript", "processor": "CodeAnalyzer"},
            "tsx": {"category": FormatCategory.CODE, "mime": "text/tsx", "processor": "CodeAnalyzer"},
            "java": {"category": FormatCategory.CODE, "mime": "text/x-java-source", "processor": "CodeAnalyzer"},
            "c": {"category": FormatCategory.CODE, "mime": "text/x-c", "processor": "CodeAnalyzer"},
            "cpp": {"category": FormatCategory.CODE, "mime": "text/x-c++", "processor": "CodeAnalyzer"},
            "h": {"category": FormatCategory.CODE, "mime": "text/x-c", "processor": "CodeAnalyzer"},
            "hpp": {"category": FormatCategory.CODE, "mime": "text/x-c++", "processor": "CodeAnalyzer"},
            "html": {"category": FormatCategory.CODE, "mime": "text/html", "processor": "CodeAnalyzer"},
            "htm": {"category": FormatCategory.CODE, "mime": "text/html", "processor": "CodeAnalyzer"},
            "css": {"category": FormatCategory.CODE, "mime": "text/css", "processor": "CodeAnalyzer"},
            "php": {"category": FormatCategory.CODE, "mime": "text/x-php", "processor": "CodeAnalyzer"},
            "rb": {"category": FormatCategory.CODE, "mime": "text/x-ruby", "processor": "CodeAnalyzer"},
            "go": {"category": FormatCategory.CODE, "mime": "text/x-go", "processor": "CodeAnalyzer"},
            "rs": {"category": FormatCategory.CODE, "mime": "text/x-rust", "processor": "CodeAnalyzer"},
            "cs": {"category": FormatCategory.CODE, "mime": "text/x-csharp", "processor": "CodeAnalyzer"},
            "swift": {"category": FormatCategory.CODE, "mime": "text/x-swift", "processor": "CodeAnalyzer"},
            "kt": {"category": FormatCategory.CODE, "mime": "text/x-kotlin", "processor": "CodeAnalyzer"},
            "scala": {"category": FormatCategory.CODE, "mime": "text/x-scala", "processor": "CodeAnalyzer"},
            "dart": {"category": FormatCategory.CODE, "mime": "text/x-dart", "processor": "CodeAnalyzer"},
            "lua": {"category": FormatCategory.CODE, "mime": "text/x-lua", "processor": "CodeAnalyzer"},
            "pl": {"category": FormatCategory.CODE, "mime": "text/x-perl", "processor": "CodeAnalyzer"},
            "pm": {"category": FormatCategory.CODE, "mime": "text/x-perl", "processor": "CodeAnalyzer"},
            "sh": {"category": FormatCategory.CODE, "mime": "application/x-sh", "processor": "CodeAnalyzer"},
            "bash": {"category": FormatCategory.CODE, "mime": "application/x-sh", "processor": "CodeAnalyzer"},
            "ps1": {"category": FormatCategory.CODE, "mime": "application/x-powershell", "processor": "CodeAnalyzer"},
            "r": {"category": FormatCategory.CODE, "mime": "text/x-r", "processor": "CodeAnalyzer"},
            "m": {"category": FormatCategory.CODE, "mime": "text/x-matlab", "processor": "CodeAnalyzer"},
            "sql": {"category": FormatCategory.CODE, "mime": "application/sql", "processor": "CodeAnalyzer"},
            "dockerfile": {"category": FormatCategory.CODE, "mime": "text/plain", "processor": "CodeAnalyzer"},
            "makefile": {"category": FormatCategory.CODE, "mime": "text/x-makefile", "processor": "CodeAnalyzer"},
            
            # 图片 (15种)
            "jpg": {"category": FormatCategory.IMAGE, "mime": "image/jpeg", "processor": "ImageOCRProcessor"},
            "jpeg": {"category": FormatCategory.IMAGE, "mime": "image/jpeg", "processor": "ImageOCRProcessor"},
            "png": {"category": FormatCategory.IMAGE, "mime": "image/png", "processor": "ImageOCRProcessor"},
            "gif": {"category": FormatCategory.IMAGE, "mime": "image/gif", "processor": "ImageOCRProcessor"},
            "bmp": {"category": FormatCategory.IMAGE, "mime": "image/bmp", "processor": "ImageOCRProcessor"},
            "tiff": {"category": FormatCategory.IMAGE, "mime": "image/tiff", "processor": "ImageOCRProcessor"},
            "tif": {"category": FormatCategory.IMAGE, "mime": "image/tiff", "processor": "ImageOCRProcessor"},
            "webp": {"category": FormatCategory.IMAGE, "mime": "image/webp", "processor": "ImageOCRProcessor"},
            "svg": {"category": FormatCategory.IMAGE, "mime": "image/svg+xml", "processor": "ImageOCRProcessor"},
            "heic": {"category": FormatCategory.IMAGE, "mime": "image/heic", "processor": "ImageOCRProcessor"},
            "heif": {"category": FormatCategory.IMAGE, "mime": "image/heif", "processor": "ImageOCRProcessor"},
            "ico": {"category": FormatCategory.IMAGE, "mime": "image/x-icon", "processor": "ImageOCRProcessor"},
            "psd": {"category": FormatCategory.IMAGE, "mime": "image/vnd.adobe.photoshop", "processor": "ImageOCRProcessor"},
            "ai": {"category": FormatCategory.IMAGE, "mime": "application/postscript", "processor": "ImageOCRProcessor"},
            "raw": {"category": FormatCategory.IMAGE, "mime": "image/x-raw", "processor": "ImageOCRProcessor"},
            
            # 音频 (10种)
            "mp3": {"category": FormatCategory.AUDIO, "mime": "audio/mpeg", "processor": "AudioTranscriber"},
            "wav": {"category": FormatCategory.AUDIO, "mime": "audio/wav", "processor": "AudioTranscriber"},
            "flac": {"category": FormatCategory.AUDIO, "mime": "audio/flac", "processor": "AudioTranscriber"},
            "aac": {"category": FormatCategory.AUDIO, "mime": "audio/aac", "processor": "AudioTranscriber"},
            "ogg": {"category": FormatCategory.AUDIO, "mime": "audio/ogg", "processor": "AudioTranscriber"},
            "m4a": {"category": FormatCategory.AUDIO, "mime": "audio/mp4", "processor": "AudioTranscriber"},
            "wma": {"category": FormatCategory.AUDIO, "mime": "audio/x-ms-wma", "processor": "AudioTranscriber"},
            "opus": {"category": FormatCategory.AUDIO, "mime": "audio/opus", "processor": "AudioTranscriber"},
            "amr": {"category": FormatCategory.AUDIO, "mime": "audio/amr", "processor": "AudioTranscriber"},
            "3gp": {"category": FormatCategory.AUDIO, "mime": "audio/3gpp", "processor": "AudioTranscriber"},
            
            # 视频 (10种)
            "mp4": {"category": FormatCategory.VIDEO, "mime": "video/mp4", "processor": "VideoFrameExtractor"},
            "avi": {"category": FormatCategory.VIDEO, "mime": "video/x-msvideo", "processor": "VideoFrameExtractor"},
            "mkv": {"category": FormatCategory.VIDEO, "mime": "video/x-matroska", "processor": "VideoFrameExtractor"},
            "mov": {"category": FormatCategory.VIDEO, "mime": "video/quicktime", "processor": "VideoFrameExtractor"},
            "wmv": {"category": FormatCategory.VIDEO, "mime": "video/x-ms-wmv", "processor": "VideoFrameExtractor"},
            "flv": {"category": FormatCategory.VIDEO, "mime": "video/x-flv", "processor": "VideoFrameExtractor"},
            "webm": {"category": FormatCategory.VIDEO, "mime": "video/webm", "processor": "VideoFrameExtractor"},
            "mpeg": {"category": FormatCategory.VIDEO, "mime": "video/mpeg", "processor": "VideoFrameExtractor"},
            "mpg": {"category": FormatCategory.VIDEO, "mime": "video/mpeg", "processor": "VideoFrameExtractor"},
            "rm": {"category": FormatCategory.VIDEO, "mime": "video/vnd.rn-realvideo", "processor": "VideoFrameExtractor"},
            "rmvb": {"category": FormatCategory.VIDEO, "mime": "video/vnd.rn-realvideo", "processor": "VideoFrameExtractor"},
            "vob": {"category": FormatCategory.VIDEO, "mime": "video/dvd", "processor": "VideoFrameExtractor"},
            
            # 思维导图 (5种)
            "mm": {"category": FormatCategory.MINDMAP, "mime": "application/x-freemind", "processor": "MindmapParser"},
            "xmind": {"category": FormatCategory.MINDMAP, "mime": "application/x-xmind", "processor": "MindmapParser"},
            "freemind": {"category": FormatCategory.MINDMAP, "mime": "application/x-freemind", "processor": "MindmapParser"},
            "mmap": {"category": FormatCategory.MINDMAP, "mime": "application/x-mindmanager", "processor": "MindmapParser"},
            "opml": {"category": FormatCategory.MINDMAP, "mime": "application/x-opml+xml", "processor": "MindmapParser"},
            
            # 数据库 (8种)
            "db": {"category": FormatCategory.DATABASE, "mime": "application/x-sqlite3", "processor": "DatabaseFileHandler"},
            "sqlite": {"category": FormatCategory.DATABASE, "mime": "application/x-sqlite3", "processor": "DatabaseFileHandler"},
            "sqlite3": {"category": FormatCategory.DATABASE, "mime": "application/x-sqlite3", "processor": "DatabaseFileHandler"},
            "mdb": {"category": FormatCategory.DATABASE, "mime": "application/x-msaccess", "processor": "DatabaseFileHandler"},
            "accdb": {"category": FormatCategory.DATABASE, "mime": "application/x-msaccess", "processor": "DatabaseFileHandler"},
            "fdb": {"category": FormatCategory.DATABASE, "mime": "application/x-firebird", "processor": "DatabaseFileHandler"},
            "odb": {"category": FormatCategory.DATABASE, "mime": "application/vnd.oasis.opendocument.database", "processor": "DatabaseFileHandler"},
            "csv": {"category": FormatCategory.DATABASE, "mime": "text/csv", "processor": "DatabaseFileHandler"},
            
            # 文本 (10种)
            "json": {"category": FormatCategory.TEXT, "mime": "application/json", "processor": "TextProcessor"},
            "xml": {"category": FormatCategory.TEXT, "mime": "application/xml", "processor": "TextProcessor"},
            "yaml": {"category": FormatCategory.TEXT, "mime": "application/x-yaml", "processor": "TextProcessor"},
            "yml": {"category": FormatCategory.TEXT, "mime": "application/x-yaml", "processor": "TextProcessor"},
            "md": {"category": FormatCategory.TEXT, "mime": "text/markdown", "processor": "TextProcessor"},
            "markdown": {"category": FormatCategory.TEXT, "mime": "text/markdown", "processor": "TextProcessor"},
            "rst": {"category": FormatCategory.TEXT, "mime": "text/x-rst", "processor": "TextProcessor"},
            "conf": {"category": FormatCategory.TEXT, "mime": "text/plain", "processor": "TextProcessor"},
            "ini": {"category": FormatCategory.TEXT, "mime": "text/plain", "processor": "TextProcessor"},
            "toml": {"category": FormatCategory.TEXT, "mime": "application/toml", "processor": "TextProcessor"},
            "properties": {"category": FormatCategory.TEXT, "mime": "text/plain", "processor": "TextProcessor"},
            "log": {"category": FormatCategory.TEXT, "mime": "text/plain", "processor": "TextProcessor"},
            
            # 压缩文件 (7种)
            "zip": {"category": FormatCategory.ARCHIVE, "mime": "application/zip", "processor": "ArchiveExtractor"},
            "rar": {"category": FormatCategory.ARCHIVE, "mime": "application/x-rar-compressed", "processor": "ArchiveExtractor"},
            "7z": {"category": FormatCategory.ARCHIVE, "mime": "application/x-7z-compressed", "processor": "ArchiveExtractor"},
            "tar": {"category": FormatCategory.ARCHIVE, "mime": "application/x-tar", "processor": "ArchiveExtractor"},
            "gz": {"category": FormatCategory.ARCHIVE, "mime": "application/gzip", "processor": "ArchiveExtractor"},
            "bz2": {"category": FormatCategory.ARCHIVE, "mime": "application/x-bzip2", "processor": "ArchiveExtractor"},
            "xz": {"category": FormatCategory.ARCHIVE, "mime": "application/x-xz", "processor": "ArchiveExtractor"},
        }
        
        # 统计信息
        self._stats = {
            "total_formats": len(self._format_registry),
            "by_category": {},
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
        }
        
        # 按分类统计
        for fmt, info in self._format_registry.items():
            cat = info["category"].value
            self._stats["by_category"][cat] = self._stats["by_category"].get(cat, 0) + 1
    
    def get_supported_formats(self) -> List[str]:
        """获取所有支持的格式列表"""
        return list(self._format_registry.keys())
    
    def get_format_info(self, extension: str) -> Optional[Dict[str, Any]]:
        """获取格式信息"""
        ext = extension.lstrip('.').lower()
        return self._format_registry.get(ext)
    
    def is_supported(self, extension: str) -> bool:
        """检查格式是否支持"""
        ext = extension.lstrip('.').lower()
        return ext in self._format_registry
    
    def get_formats_by_category(self, category: FormatCategory) -> List[str]:
        """按分类获取格式列表"""
        return [
            fmt for fmt, info in self._format_registry.items()
            if info["category"] == category
        ]
    
    def process_file(self, filepath: str) -> ProcessingResult:
        """处理文件（委托给 UniversalFileParser）"""
        try:
            result = self.parser.process(filepath)
            self._stats["processed_count"] += 1
            if result.success:
                self._stats["success_count"] += 1
            else:
                self._stats["failed_count"] += 1
            return result
        except Exception as e:
            logger.error(f"FormatProcessorRegistry.process_file failed: {e}")
            self._stats["processed_count"] += 1
            self._stats["failed_count"] += 1
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=str(e)
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            "success_rate": (
                self._stats["success_count"] / self._stats["processed_count"]
                if self._stats["processed_count"] > 0 else 0.0
            )
        }
    
    def get_registry_summary(self) -> Dict[str, Any]:
        """获取注册表摘要"""
        return {
            "total_formats": len(self._format_registry),
            "categories": {
                cat.value: self._stats["by_category"].get(cat.value, 0)
                for cat in FormatCategory
            },
            "processors": list(set(
                info["processor"] for info in self._format_registry.values()
            ))
        }


# 全局单例
_format_registry_instance: Optional[FormatProcessorRegistry] = None


def get_format_registry() -> FormatProcessorRegistry:
    """获取格式处理器注册表单例"""
    global _format_registry_instance
    if _format_registry_instance is None:
        _format_registry_instance = FormatProcessorRegistry()
    return _format_registry_instance

