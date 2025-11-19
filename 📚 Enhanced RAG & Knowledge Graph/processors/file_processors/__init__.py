"""
 processors.file_processors public API
 提供 UniversalFileParser 依赖的核心数据结构与基类（FileMetadata、FileType等）
 这些定义在很多模块中被引用，但原始文件内容为空，导致运行时 ImportError。
 这里补全轻量实现，保证在缺少真实底层实现的情况下也能正常初始化 Web 服务。
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FileType(Enum):
    """标准化的文件类型枚举"""

    OFFICE_DOCUMENT = "office_document"
    EBOOK = "ebook"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MINDMAP = "mindmap"
    DATABASE = "database"
    TEXT = "text"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """文件处理状态"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FileMetadata:
    """文件元数据的通用结构"""

    filename: str
    filepath: str
    file_type: FileType = FileType.UNKNOWN
    file_size: int = 0
    file_extension: str = ""
    mime_type: str = "application/octet-stream"
    created_time: float = 0
    modified_time: float = 0
    checksum: str = ""
    language: str = "unknown"
    page_count: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """文件处理后的标准返回结构"""

    success: bool
    status: ProcessingStatus
    content: Optional[str] = None
    metadata: Optional[FileMetadata] = None
    chunks: Optional[List[str]] = None
    word_count: Optional[int] = None
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """便于序列化/调试"""
        return {
            "success": self.success,
            "status": self.status.value if isinstance(self.status, ProcessingStatus) else self.status,
            "content": self.content,
            "metadata": self.metadata.__dict__ if self.metadata else None,
            "chunks": self.chunks,
            "word_count": self.word_count,
            "chunk_count": self.chunk_count,
            "error_message": self.error_message,
            "extras": self.extras,
        }


class FileProcessorBase:
    """
    为 UniversalFileParser 提供的同步处理基类。
    真实实现可以更复杂；这里提供最小可用逻辑，便于框架启动运行。
    """

    def __init__(self):
        self.processor_name = self.__class__.__name__
        self.supported_extensions: List[str] = []
        self.supported_mime_types: List[str] = []
        self._initialized: bool = False

    def initialize(self) -> bool:
        """子类可覆盖，默认直接标记为初始化完成"""
        self._initialized = True
        return True

    def can_process(self, filepath: str, metadata: FileMetadata) -> bool:
        """判断是否支持该文件"""
        extension = metadata.file_extension.lower()
        return (
            extension in self.supported_extensions
            or metadata.mime_type in self.supported_mime_types
        )

    def process(self, filepath: str, metadata: Optional[FileMetadata] = None) -> ProcessingResult:
        """统一的处理入口"""
        if metadata is None:
            path_obj = Path(filepath)
            metadata = FileMetadata(
                filename=path_obj.name,
                filepath=str(path_obj),
                file_extension=path_obj.suffix.lstrip(".").lower(),
                file_size=path_obj.stat().st_size if path_obj.exists() else 0,
            )

        if not self._initialized:
            try:
                self.initialize()
            except Exception as exc:  # pragma: no cover - 防御性
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message=f"Processor init failed: {exc}",
                    metadata=metadata,
                )

        try:
            return self._process_file(filepath, metadata)
        except NotImplementedError:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message="Processor not implemented",
                metadata=metadata,
            )
        except Exception as exc:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=str(exc),
                metadata=metadata,
            )

    def _process_file(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:  # pragma: no cover
        """子类必须实现"""
        raise NotImplementedError("Subclasses must implement _process_file")
