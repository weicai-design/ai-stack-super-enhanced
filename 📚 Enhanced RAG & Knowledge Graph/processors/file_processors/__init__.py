"""
Enhanced RAG & Knowledge Graph - File Processors Module
Universal File Processing Infrastructure for AI Stack Super Enhanced

Version: 1.0.0
Author: AI Stack Super Enhanced Team
Created: 2024
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

# Configure module logger
logger = logging.getLogger(__name__)


class FileType(Enum):
    """Supported file types enumeration"""

    OFFICE_DOCUMENT = "office"
    EBOOK = "ebook"
    CODE = "code"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    MINDMAP = "mindmap"
    DATABASE = "database"
    TEXT = "text"
    ARCHIVE = "archive"  # 压缩文件
    UNKNOWN = "unknown"


class ProcessingStatus(Enum):
    """File processing status enumeration"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class FileMetadata:
    """Enhanced file metadata structure"""

    filename: str
    filepath: str
    file_type: FileType
    file_size: int
    file_extension: str
    mime_type: str
    created_time: float
    modified_time: float
    encoding: Optional[str] = None
    language: Optional[str] = None
    page_count: Optional[int] = None
    duration: Optional[float] = None  # for audio/video
    dimensions: Optional[tuple] = None  # for images/video
    checksum: Optional[str] = None


@dataclass
class ProcessingResult:
    """Enhanced processing result structure"""

    success: bool
    status: ProcessingStatus
    content: Optional[str] = None
    metadata: Optional[FileMetadata] = None
    chunks: Optional[List[Dict[str, Any]]] = None
    entities: Optional[List[Dict[str, Any]]] = None
    relationships: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0
    chunk_count: int = 0
    word_count: int = 0


class FileProcessorBase:
    """Base class for all file processors"""

    def __init__(self):
        self.supported_extensions = []
        self.supported_mime_types = []
        self.processor_name = self.__class__.__name__
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the processor"""
        try:
            self._load_dependencies()
            self._initialized = True
            logger.info(f"Processor {self.processor_name} initialized successfully")
            return True
        except Exception as e:
            logger.error(
                f"Failed to initialize processor {self.processor_name}: {str(e)}"
            )
            self._initialized = False
            return False

    def _load_dependencies(self):
        """Load required dependencies - to be implemented by subclasses"""
        pass

    def can_process(self, filepath: str, metadata: FileMetadata) -> bool:
        """Check if processor can handle the file"""
        if not self._initialized:
            return False

        ext = metadata.file_extension.lower()
        mime = metadata.mime_type.lower()

        return ext in self.supported_extensions or any(
            mime_type in mime for mime_type in self.supported_mime_types
        )

    def process(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """Process file - to be implemented by subclasses"""
        if not self._initialized:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message="Processor not initialized",
            )

        if not self.can_process(filepath, metadata):
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.SKIPPED,
                error_message="File type not supported",
            )

        return self._process_file(filepath, metadata)

    def _process_file(self, filepath: str, metadata: FileMetadata) -> ProcessingResult:
        """Actual file processing - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _process_file method")

    def validate_result(self, result: ProcessingResult) -> bool:
        """Validate processing result"""
        if not result.success:
            return False

        # Basic content validation
        if result.content and len(result.content.strip()) == 0:
            logger.warning(f"Processor {self.processor_name} produced empty content")
            return False

        # Metadata validation
        if not result.metadata:
            logger.warning(f"Processor {self.processor_name} produced no metadata")
            return False

        return True


# Import all processor classes for easy access
try:
    from .audio_transcriber import AudioTranscriber
    from .code_analyzer import CodeAnalyzer
    from .database_file_handler import DatabaseFileHandler
    from .ebook_extractor import EbookExtractor
    from .mindmap_parser import MindmapParser
    from .office_document_handler import OfficeDocumentHandler
    from .universal_file_parser import UniversalFileParser
    from .video_frame_extractor import VideoFrameExtractor

    __all__ = [
        "UniversalFileParser",
        "OfficeDocumentHandler",
        "EbookExtractor",
        "CodeAnalyzer",
        "ImageOCRProcessor",
        "AudioTranscriber",
        "VideoFrameExtractor",
        "MindmapParser",
        "DatabaseFileHandler",
        "FileType",
        "ProcessingStatus",
        "FileMetadata",
        "ProcessingResult",
        "FileProcessorBase",
    ]

    logger.info("All file processors imported successfully")

except ImportError as e:
    logger.warning(f"Some file processors could not be imported: {str(e)}")
    __all__ = [
        "FileType",
        "ProcessingStatus",
        "FileMetadata",
        "ProcessingResult",
        "FileProcessorBase",
    ]

logger.info("File processors module initialized successfully")

# Export lightweight parsers if present
try:
    from . import office_handler as _office_handler  # noqa: F401
    from . import pdf_parser as _pdf_parser  # noqa: F401

    __all__.extend(["pdf_parser", "office_handler"])
except Exception:
    # optional parsers may not be available in some environments
    logger.debug("pdf_parser or office_handler not available to export")

# 统一导出 file processors，个别模块可能为可选依赖
__all__ = ["universal_file_parser", "pdf_parser", "office_handler"]

try:
    from . import universal_file_parser  # noqa: F401
except Exception:
    universal_file_parser = None

try:
    from . import pdf_parser  # noqa: F401
except Exception:
    pdf_parser = None

try:
    from . import office_handler  # noqa: F401
except Exception:
    office_handler = None

# 将 OCR 处理器变为容错可选导入，避免依赖缺失时阻断整个 processors 导入
try:
    from .image_ocr_processor import (
        IntelligentOCRProcessor as ImageOCRProcessor,
    )  # noqa: F401
except Exception:
    ImageOCRProcessor = None  # type: ignore
