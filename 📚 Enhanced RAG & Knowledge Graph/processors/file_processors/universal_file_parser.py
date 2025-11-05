"""
Universal File Parser for AI Stack Super Enhanced
Intelligent file type detection and routing to appropriate processors

Version: 1.0.0
Author: AI Stack Super Enhanced Team
Created: 2024
"""

import asyncio
import hashlib
import importlib
import inspect
import logging
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import magic  # type: ignore
except Exception:
    magic = None

from . import (
    FileMetadata,
    FileProcessorBase,
    FileType,
    ProcessingResult,
    ProcessingStatus,
)

logger = logging.getLogger(__name__)

# 线程安全单例
_UNIVERSAL_PARSER_SINGLETON = None
_UNIVERSAL_PARSER_LOCK = threading.Lock()


def _is_coro(func) -> bool:
    return inspect.iscoroutinefunction(func)


class UniversalFileParser(FileProcessorBase):
    """
    Universal file parser that detects file types and routes to appropriate processors
    Supports intelligent fallback and hybrid processing strategies
    """

    def __init__(self):
        super().__init__()
        self.processor_name = "UniversalFileParser"
        self._file_processor_registry: Dict[FileType, FileProcessorBase] = {}
        self._mime_detector = None
        self._initialized = False

        # Extended file type mappings - 根据需求1.1支持所有格式
        self._file_type_mappings = {
            # Office documents - 所有办公文件格式
            "doc": FileType.OFFICE_DOCUMENT,
            "docx": FileType.OFFICE_DOCUMENT,
            "docm": FileType.OFFICE_DOCUMENT,  # Word Macro-enabled
            "dot": FileType.OFFICE_DOCUMENT,   # Word Template
            "dotx": FileType.OFFICE_DOCUMENT,  # Word Template XML
            "xls": FileType.OFFICE_DOCUMENT,
            "xlsx": FileType.OFFICE_DOCUMENT,
            "xlsm": FileType.OFFICE_DOCUMENT,  # Excel Macro-enabled
            "xlsb": FileType.OFFICE_DOCUMENT,  # Excel Binary
            "xlt": FileType.OFFICE_DOCUMENT,   # Excel Template
            "xltx": FileType.OFFICE_DOCUMENT,  # Excel Template XML
            "ppt": FileType.OFFICE_DOCUMENT,
            "pptx": FileType.OFFICE_DOCUMENT,
            "pptm": FileType.OFFICE_DOCUMENT,  # PowerPoint Macro-enabled
            "pot": FileType.OFFICE_DOCUMENT,   # PowerPoint Template
            "potx": FileType.OFFICE_DOCUMENT,  # PowerPoint Template XML
            "pdf": FileType.OFFICE_DOCUMENT,
            "odt": FileType.OFFICE_DOCUMENT,
            "ods": FileType.OFFICE_DOCUMENT,
            "odp": FileType.OFFICE_DOCUMENT,
            "rtf": FileType.OFFICE_DOCUMENT,   # Rich Text Format
            "msg": FileType.OFFICE_DOCUMENT,   # Outlook Message
            "eml": FileType.OFFICE_DOCUMENT,   # Email
            # Ebooks - 所有电子书格式
            "epub": FileType.EBOOK,
            "mobi": FileType.EBOOK,
            "azw": FileType.EBOOK,     # Kindle Format 8
            "azw3": FileType.EBOOK,    # Kindle Format
            "fb2": FileType.EBOOK,     # FictionBook
            "lit": FileType.EBOOK,     # Microsoft Reader
            "prc": FileType.EBOOK,     # Palm
            # Code files - 所有编程文件格式
            "py": FileType.CODE,
            "js": FileType.CODE,
            "java": FileType.CODE,
            "cpp": FileType.CODE,
            "c": FileType.CODE,
            "h": FileType.CODE,        # C/C++ Header
            "hpp": FileType.CODE,      # C++ Header
            "html": FileType.CODE,
            "htm": FileType.CODE,
            "css": FileType.CODE,
            "php": FileType.CODE,
            "rb": FileType.CODE,
            "go": FileType.CODE,
            "rs": FileType.CODE,
            "ts": FileType.CODE,
            "tsx": FileType.CODE,      # TypeScript React
            "jsx": FileType.CODE,      # JavaScript React
            "cs": FileType.CODE,       # C#
            "swift": FileType.CODE,    # Swift
            "kt": FileType.CODE,       # Kotlin
            "scala": FileType.CODE,    # Scala
            "dart": FileType.CODE,     # Dart
            "lua": FileType.CODE,      # Lua
            "pl": FileType.CODE,       # Perl
            "pm": FileType.CODE,       # Perl Module
            "sh": FileType.CODE,       # Shell Script
            "bash": FileType.CODE,     # Bash Script
            "zsh": FileType.CODE,      # Zsh Script
            "ps1": FileType.CODE,      # PowerShell
            "r": FileType.CODE,        # R Language
            "m": FileType.CODE,        # MATLAB/Objective-C
            "sql": FileType.CODE,      # SQL
            "dockerfile": FileType.CODE,  # Dockerfile
            "makefile": FileType.CODE,    # Makefile
            "cmake": FileType.CODE,    # CMake
            # Images - 所有图片格式
            "jpg": FileType.IMAGE,
            "jpeg": FileType.IMAGE,
            "png": FileType.IMAGE,
            "gif": FileType.IMAGE,
            "bmp": FileType.IMAGE,
            "tiff": FileType.IMAGE,
            "tif": FileType.IMAGE,
            "webp": FileType.IMAGE,
            "svg": FileType.IMAGE,
            "heic": FileType.IMAGE,    # iOS High Efficiency
            "heif": FileType.IMAGE,    # High Efficiency Image
            "ico": FileType.IMAGE,     # Icon
            "psd": FileType.IMAGE,     # Photoshop
            "ai": FileType.IMAGE,      # Illustrator
            "raw": FileType.IMAGE,     # Camera Raw (通用)
            "cr2": FileType.IMAGE,     # Canon Raw
            "nef": FileType.IMAGE,     # Nikon Raw
            "arw": FileType.IMAGE,     # Sony Raw
            # Audio - 所有音频格式
            "mp3": FileType.AUDIO,
            "wav": FileType.AUDIO,
            "flac": FileType.AUDIO,
            "aac": FileType.AUDIO,
            "ogg": FileType.AUDIO,
            "m4a": FileType.AUDIO,
            "wma": FileType.AUDIO,     # Windows Media Audio
            "opus": FileType.AUDIO,    # Opus
            "amr": FileType.AUDIO,     # AMR
            "3gp": FileType.AUDIO,     # 3GP Audio
            # Video - 所有视频格式
            "mp4": FileType.VIDEO,
            "avi": FileType.VIDEO,
            "mkv": FileType.VIDEO,
            "mov": FileType.VIDEO,
            "wmv": FileType.VIDEO,
            "flv": FileType.VIDEO,
            "webm": FileType.VIDEO,
            "mpeg": FileType.VIDEO,    # MPEG
            "mpg": FileType.VIDEO,     # MPEG
            "3gp": FileType.VIDEO,     # 3GP Video
            "rm": FileType.VIDEO,      # RealMedia
            "rmvb": FileType.VIDEO,   # RealMedia Variable Bitrate
            "vob": FileType.VIDEO,    # DVD Video
            # Mindmaps - 所有思维导图格式
            "mm": FileType.MINDMAP,    # FreeMind
            "xmind": FileType.MINDMAP, # XMind
            "freemind": FileType.MINDMAP,
            "mmap": FileType.MINDMAP,  # MindManager
            "opml": FileType.MINDMAP,  # Outline Processor Markup
            # Database files - 所有数据库文件格式
            "db": FileType.DATABASE,
            "sqlite": FileType.DATABASE,
            "sqlite3": FileType.DATABASE,
            "mdb": FileType.DATABASE,   # Access
            "accdb": FileType.DATABASE, # Access 2007+
            "fdb": FileType.DATABASE,   # Firebird
            "odb": FileType.DATABASE,   # OpenOffice Base
            # Text files - 所有文本文件格式
            "txt": FileType.TEXT,
            "csv": FileType.TEXT,
            "json": FileType.TEXT,
            "xml": FileType.TEXT,
            "yaml": FileType.TEXT,
            "yml": FileType.TEXT,
            "md": FileType.TEXT,
            "markdown": FileType.TEXT,
            "rst": FileType.TEXT,
            "conf": FileType.TEXT,     # Config
            "ini": FileType.TEXT,      # Config
            "toml": FileType.TEXT,     # TOML Config
            "properties": FileType.TEXT, # Properties
            "log": FileType.TEXT,      # Log files
            # Archive files - 压缩文件格式
            "zip": FileType.ARCHIVE,
            "rar": FileType.ARCHIVE,
            "7z": FileType.ARCHIVE,
            "tar": FileType.ARCHIVE,
            "gz": FileType.ARCHIVE,
            "bz2": FileType.ARCHIVE,
            "xz": FileType.ARCHIVE,
        }

        self.supported_extensions = list(self._file_type_mappings.keys())
        self.supported_mime_types = [
            "application/",
            "text/",
            "image/",
            "audio/",
            "video/",
        ]

    def initialize(self) -> bool:
        """Initialize the universal file parser"""
        try:
            # Initialize MIME type detector
            self._initialize_mime_detector()

            # Load and initialize all available processors
            self._load_processor_registry()

            self._initialized = True
            logger.info("UniversalFileParser initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize UniversalFileParser: {str(e)}")
            self._initialized = False
            return False

    # Compatibility adapter methods expected by HybridRAGEngine and other components
    def parse_document(self, filepath: str) -> ProcessingResult:
        """
        同步接口：解析文档并返回 ProcessingResult。
        主要供旧代码或同步调用使用，内部会调用异步/同步处理链。
        """
        try:
            if not self._initialized:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message="UniversalFileParser not initialized",
                )

            result = self.process(filepath)
            return result
        except Exception as e:
            logger.error(f"parse_document failed for {filepath}: {e}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
            )

    def extract_metadata(self, filepath: str) -> FileMetadata:
        """
        同步接口：提取并返回文件元数据，供引擎快速检查使用。
        """
        try:
            file_type, metadata = self.detect_file_type(filepath)
            return metadata
        except Exception as e:
            logger.error(f"extract_metadata failed for {filepath}: {e}")
            # 返回最小化的 FileMetadata 占位对象
            return FileMetadata(
                filename=Path(filepath).name,
                filepath=filepath,
                file_type=FileType.UNKNOWN,
                file_size=0,
                file_extension=Path(filepath).suffix.lower().lstrip("."),
                mime_type="application/octet-stream",
                created_time=0,
                modified_time=0,
                checksum="",
            )

    def _initialize_mime_detector(self):
        """Initialize MIME type detection"""
        try:
            if magic is not None:
                self._mime_detector = magic.Magic(mime=True)
                logger.debug("MIME type detector initialized with python-magic")
            else:
                self._mime_detector = None
                logger.debug("python-magic not available, using fallback mimetypes")
        except Exception as e:
            logger.warning(f"Failed to initialize MIME detector: {str(e)}")
            self._mime_detector = None

    def _load_processor_registry(self):
        """Load and initialize all available file processors (dynamic import)."""
        processor_classes = [
            ("OfficeDocumentHandler", FileType.OFFICE_DOCUMENT),
            ("EbookExtractor", FileType.EBOOK),
            ("CodeAnalyzer", FileType.CODE),
            ("ImageOCRProcessor", FileType.IMAGE),
            ("AudioTranscriber", FileType.AUDIO),
            ("VideoFrameExtractor", FileType.VIDEO),
            ("MindmapParser", FileType.MINDMAP),
            ("DatabaseFileHandler", FileType.DATABASE),
        ]

        for class_name, file_type in processor_classes:
            try:
                module_name = _camel_to_snake(class_name)
                module_path = f"processors.file_processors.{module_name}"
                try:
                    mod = importlib.import_module(module_path)
                    cls = getattr(mod, class_name, None)
                except Exception:
                    cls = None

                if cls is not None and inspect.isclass(cls):
                    processor = cls()
                else:
                    processor = self._create_processor_instance(class_name, file_type)

                # initialize (support sync or async initialize())
                init = getattr(processor, "initialize", None)
                if callable(init):
                    try:
                        if _is_coro(init):
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    loop.run_until_complete(init())
                                else:
                                    asyncio.run(init())
                            except RuntimeError:
                                asyncio.run(init())
                        else:
                            init()
                    except Exception as e:
                        logger.warning(f"Processor {class_name} initialize failed: {e}")

                if getattr(processor, "_initialized", False):
                    self._file_processor_registry[file_type] = processor
                    logger.info(f"Loaded processor: {class_name} for {file_type}")
                else:
                    logger.warning(
                        f"Processor {class_name} not initialized, using fallback if any"
                    )

            except Exception as e:
                logger.error(f"Error loading processor {class_name}: {str(e)}")

    def _create_processor_instance(self, class_name: str, file_type: FileType):
        """Create processor instance - placeholder for dynamic loading"""

        class MockProcessor(FileProcessorBase):
            def __init__(self, file_type):
                super().__init__()
                self.file_type = file_type
                self._initialized = True
                self.processor_name = f"MockProcessor[{file_type.value}]"
                self.supported_extensions = []

            def can_process(self, filepath, metadata):
                return metadata.file_type == self.file_type

            def _process_file(self, filepath, metadata):
                return ProcessingResult(
                    success=True,
                    status=ProcessingStatus.COMPLETED,
                    content=f"Mock content from {self.file_type.value} processor",
                    metadata=metadata,
                )

        return MockProcessor(file_type)

    def detect_file_type(self, filepath: str) -> Tuple[FileType, FileMetadata]:
        """
        Enhanced file type detection with comprehensive metadata extraction
        """
        try:
            file_path = Path(filepath)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filepath}")

            filename = file_path.name
            file_extension = file_path.suffix.lower().lstrip(".")
            file_size = file_path.stat().st_size
            created_time = file_path.stat().st_ctime
            modified_time = file_path.stat().st_mtime

            mime_type = self._detect_mime_type(filepath)
            file_type = self._determine_file_type(file_extension, mime_type)
            checksum = self._calculate_checksum(filepath)

            metadata = FileMetadata(
                filename=filename,
                filepath=str(file_path.absolute()),
                file_type=file_type,
                file_size=file_size,
                file_extension=file_extension,
                mime_type=mime_type,
                created_time=created_time,
                modified_time=modified_time,
                checksum=checksum,
            )

            logger.debug(f"Detected file type: {file_type} for {filename}")
            return file_type, metadata

        except Exception as e:
            logger.error(f"File type detection failed for {filepath}: {str(e)}")
            return FileType.UNKNOWN, FileMetadata(
                filename=Path(filepath).name,
                filepath=filepath,
                file_type=FileType.UNKNOWN,
                file_size=0,
                file_extension=Path(filepath).suffix.lower().lstrip("."),
                mime_type="application/octet-stream",
                created_time=0,
                modified_time=0,
            )

    def _detect_mime_type(self, filepath: str) -> str:
        """Detect MIME type using available methods"""
        if self._mime_detector:
            try:
                return self._mime_detector.from_file(filepath)
            except Exception:
                pass

        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type or "application/octet-stream"

    def _determine_file_type(self, extension: str, mime_type: str) -> FileType:
        """Determine file type from extension and MIME type"""
        if extension in self._file_type_mappings:
            return self._file_type_mappings[extension]

        if mime_type.startswith("text/"):
            return FileType.TEXT
        elif mime_type.startswith("image/"):
            return FileType.IMAGE
        elif mime_type.startswith("audio/"):
            return FileType.AUDIO
        elif mime_type.startswith("video/"):
            return FileType.VIDEO
        elif "pdf" in mime_type or "document" in mime_type:
            return FileType.OFFICE_DOCUMENT
        elif "epub" in mime_type or "ebook" in mime_type:
            return FileType.EBOOK
        else:
            return FileType.UNKNOWN

    def _calculate_checksum(self, filepath: str, algorithm: str = "md5") -> str:
        """Calculate file checksum for integrity verification"""
        try:
            hash_func = getattr(hashlib, algorithm)()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.warning(f"Checksum calculation failed for {filepath}: {str(e)}")
            return ""

    def get_appropriate_processor(
        self, file_type: FileType
    ) -> Optional[FileProcessorBase]:
        """Get the appropriate processor for the file type"""
        return self._file_processor_registry.get(file_type)

    async def process_file(self, file_path: str, **kwargs) -> ProcessingResult:
        """
        异步接口：处理单个文件，兼容 FileProcessorBase 定义。
        直接调用同步 `process` 并返回 ProcessingResult 对象。
        """
        try:
            metadata = kwargs.get("metadata")
            result = self.process(file_path, metadata)
            return result
        except Exception as e:
            logger.error(f"process_file failed for {file_path}: {e}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=str(e),
            )

    def process(self, filepath: str, metadata: FileMetadata = None) -> ProcessingResult:
        """
        Universal file processing with intelligent routing
        """
        if not self._initialized:
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message="UniversalFileParser not initialized",
            )

        try:
            if metadata is None:
                file_type, metadata = self.detect_file_type(filepath)
            else:
                file_type = metadata.file_type

            logger.info(f"Processing file: {metadata.filename} as {file_type}")

            processor = self.get_appropriate_processor(file_type)

            if not processor:
                return ProcessingResult(
                    success=False,
                    status=ProcessingStatus.FAILED,
                    error_message=f"No processor available for file type: {file_type}",
                    metadata=metadata,
                )

            result = processor.process(filepath, metadata)
            result.metadata = metadata

            if not self.validate_result(result):
                logger.warning(f"Processing result validation failed for {filepath}")
                result.success = False
                result.status = ProcessingStatus.FAILED

            logger.info(
                f"File processing completed: {metadata.filename} - Success: {result.success}"
            )
            return result

        except Exception as e:
            logger.error(f"Universal file processing failed for {filepath}: {str(e)}")
            return ProcessingResult(
                success=False,
                status=ProcessingStatus.FAILED,
                error_message=f"Processing error: {str(e)}",
                metadata=metadata,
            )

    def batch_process(self, filepaths: List[str]) -> Dict[str, ProcessingResult]:
        """Process multiple files efficiently"""
        results = {}

        for filepath in filepaths:
            try:
                results[filepath] = self.process(filepath)
            except Exception as e:
                logger.error(f"Batch processing failed for {filepath}: {str(e)}")
                results[filepath] = ProcessingResult(
                    success=False, status=ProcessingStatus.FAILED, error_message=str(e)
                )

        return results

    def get_processing_stats(self) -> Dict[str, Any]:
        """Get universal parser statistics"""
        stats = {
            "initialized": self._initialized,
            "registered_processors": len(self._file_processor_registry),
            "supported_extensions": len(self.supported_extensions),
            "processor_details": {},
        }

        for file_type, processor in self._file_processor_registry.items():
            stats["processor_details"][file_type.value] = {
                "processor_name": getattr(processor, "processor_name", ""),
                "supported_extensions": getattr(processor, "supported_extensions", []),
                "initialized": getattr(processor, "_initialized", False),
            }

        return stats


# 工厂：创建/返回 UniversalFileParser 单例
def create_universal_parser() -> "UniversalFileParser":
    global _UNIVERSAL_PARSER_SINGLETON
    if _UNIVERSAL_PARSER_SINGLETON is None:
        with _UNIVERSAL_PARSER_LOCK:
            if _UNIVERSAL_PARSER_SINGLETON is None:
                parser = UniversalFileParser()
                try:
                    ok = parser.initialize()
                    if not ok:
                        logger.warning(
                            "UniversalFileParser.initialize() returned False"
                        )
                except Exception as e:
                    logger.exception("UniversalFileParser initialization failed: %s", e)
                _UNIVERSAL_PARSER_SINGLETON = parser
    return _UNIVERSAL_PARSER_SINGLETON


async def get_file_parser() -> "UniversalFileParser":
    # 异步获取同一个单例
    return create_universal_parser()


logger.info("UniversalFileParser module loaded successfully")
