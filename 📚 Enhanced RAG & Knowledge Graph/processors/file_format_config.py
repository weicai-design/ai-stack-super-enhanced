"""
AI-STACK V5.0 - 60种文件格式处理配置
策略：优先使用已有库，网络问题时使用完整处理器代码
作者：AI-STACK Team
日期：2025-11-09
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import importlib
import logging

logger = logging.getLogger(__name__)


class FileCategory(str, Enum):
    """文件类别"""
    DOCUMENT = "文档"
    SPREADSHEET = "表格"
    PRESENTATION = "演示"
    IMAGE = "图片"
    AUDIO = "音频"
    VIDEO = "视频"
    EBOOK = "电子书"
    ARCHIVE = "压缩包"
    CODE = "代码"
    DATA = "数据"


class ProcessorStrategy(str, Enum):
    """处理器策略"""
    LIBRARY = "使用库"  # 优先策略
    FALLBACK = "完整代码"  # 备选策略（网络问题时）


# ==================== 60种文件格式配置 ====================

FILE_FORMATS = {
    # 文档类（15种）
    "pdf": {
        "category": FileCategory.DOCUMENT,
        "description": "PDF文档",
        "library": "PyPDF2",
        "fallback": "pdfplumber",
        "mime_types": ["application/pdf"],
        "extensions": [".pdf"],
        "processor": "pdf_processor"
    },
    "docx": {
        "category": FileCategory.DOCUMENT,
        "description": "Word文档",
        "library": "python-docx",
        "fallback": "docx2txt",
        "mime_types": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
        "extensions": [".docx"],
        "processor": "docx_processor"
    },
    "doc": {
        "category": FileCategory.DOCUMENT,
        "description": "Word文档（旧版）",
        "library": "antiword",
        "fallback": "textract",
        "mime_types": ["application/msword"],
        "extensions": [".doc"],
        "processor": "doc_processor"
    },
    "txt": {
        "category": FileCategory.DOCUMENT,
        "description": "纯文本",
        "library": "built-in",
        "fallback": "built-in",
        "mime_types": ["text/plain"],
        "extensions": [".txt", ".text"],
        "processor": "txt_processor"
    },
    "md": {
        "category": FileCategory.DOCUMENT,
        "description": "Markdown文档",
        "library": "markdown",
        "fallback": "built-in",
        "mime_types": ["text/markdown"],
        "extensions": [".md", ".markdown"],
        "processor": "md_processor"
    },
    "rtf": {
        "category": FileCategory.DOCUMENT,
        "description": "富文本格式",
        "library": "striprtf",
        "fallback": "textract",
        "mime_types": ["application/rtf"],
        "extensions": [".rtf"],
        "processor": "rtf_processor"
    },
    "odt": {
        "category": FileCategory.DOCUMENT,
        "description": "OpenDocument文本",
        "library": "odfpy",
        "fallback": "textract",
        "mime_types": ["application/vnd.oasis.opendocument.text"],
        "extensions": [".odt"],
        "processor": "odt_processor"
    },
    "pages": {
        "category": FileCategory.DOCUMENT,
        "description": "Apple Pages",
        "library": "textract",
        "fallback": "zipfile",
        "mime_types": ["application/x-iwork-pages-sffpages"],
        "extensions": [".pages"],
        "processor": "pages_processor"
    },
    "tex": {
        "category": FileCategory.DOCUMENT,
        "description": "LaTeX文档",
        "library": "built-in",
        "fallback": "built-in",
        "mime_types": ["application/x-tex"],
        "extensions": [".tex", ".latex"],
        "processor": "tex_processor"
    },
    "html": {
        "category": FileCategory.DOCUMENT,
        "description": "HTML文档",
        "library": "beautifulsoup4",
        "fallback": "html.parser",
        "mime_types": ["text/html"],
        "extensions": [".html", ".htm"],
        "processor": "html_processor"
    },
    "xml": {
        "category": FileCategory.DOCUMENT,
        "description": "XML文档",
        "library": "lxml",
        "fallback": "xml.etree.ElementTree",
        "mime_types": ["application/xml", "text/xml"],
        "extensions": [".xml"],
        "processor": "xml_processor"
    },
    "json": {
        "category": FileCategory.DATA,
        "description": "JSON数据",
        "library": "built-in",
        "fallback": "built-in",
        "mime_types": ["application/json"],
        "extensions": [".json"],
        "processor": "json_processor"
    },
    "yaml": {
        "category": FileCategory.DATA,
        "description": "YAML配置",
        "library": "pyyaml",
        "fallback": "ruamel.yaml",
        "mime_types": ["application/x-yaml"],
        "extensions": [".yaml", ".yml"],
        "processor": "yaml_processor"
    },
    "csv": {
        "category": FileCategory.DATA,
        "description": "CSV数据",
        "library": "pandas",
        "fallback": "csv",
        "mime_types": ["text/csv"],
        "extensions": [".csv"],
        "processor": "csv_processor"
    },
    "log": {
        "category": FileCategory.DOCUMENT,
        "description": "日志文件",
        "library": "built-in",
        "fallback": "built-in",
        "mime_types": ["text/plain"],
        "extensions": [".log"],
        "processor": "log_processor"
    },
    
    # 表格类（8种）
    "xlsx": {
        "category": FileCategory.SPREADSHEET,
        "description": "Excel表格",
        "library": "openpyxl",
        "fallback": "pandas",
        "mime_types": ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "extensions": [".xlsx"],
        "processor": "xlsx_processor"
    },
    "xls": {
        "category": FileCategory.SPREADSHEET,
        "description": "Excel表格（旧版）",
        "library": "xlrd",
        "fallback": "pandas",
        "mime_types": ["application/vnd.ms-excel"],
        "extensions": [".xls"],
        "processor": "xls_processor"
    },
    "xlsm": {
        "category": FileCategory.SPREADSHEET,
        "description": "Excel宏表格",
        "library": "openpyxl",
        "fallback": "pandas",
        "mime_types": ["application/vnd.ms-excel.sheet.macroEnabled.12"],
        "extensions": [".xlsm"],
        "processor": "xlsm_processor"
    },
    "ods": {
        "category": FileCategory.SPREADSHEET,
        "description": "OpenDocument电子表格",
        "library": "odfpy",
        "fallback": "pandas",
        "mime_types": ["application/vnd.oasis.opendocument.spreadsheet"],
        "extensions": [".ods"],
        "processor": "ods_processor"
    },
    "numbers": {
        "category": FileCategory.SPREADSHEET,
        "description": "Apple Numbers",
        "library": "textract",
        "fallback": "zipfile",
        "mime_types": ["application/x-iwork-numbers-sffnumbers"],
        "extensions": [".numbers"],
        "processor": "numbers_processor"
    },
    "tsv": {
        "category": FileCategory.DATA,
        "description": "制表符分隔",
        "library": "pandas",
        "fallback": "csv",
        "mime_types": ["text/tab-separated-values"],
        "extensions": [".tsv"],
        "processor": "tsv_processor"
    },
    "dbf": {
        "category": FileCategory.DATA,
        "description": "dBase数据库",
        "library": "dbfread",
        "fallback": "simpledbf",
        "mime_types": ["application/x-dbf"],
        "extensions": [".dbf"],
        "processor": "dbf_processor"
    },
    "sqlite": {
        "category": FileCategory.DATA,
        "description": "SQLite数据库",
        "library": "sqlite3",
        "fallback": "built-in",
        "mime_types": ["application/x-sqlite3"],
        "extensions": [".sqlite", ".db", ".sqlite3"],
        "processor": "sqlite_processor"
    },
    
    # 演示类（6种）
    "pptx": {
        "category": FileCategory.PRESENTATION,
        "description": "PowerPoint演示",
        "library": "python-pptx",
        "fallback": "textract",
        "mime_types": ["application/vnd.openxmlformats-officedocument.presentationml.presentation"],
        "extensions": [".pptx"],
        "processor": "pptx_processor"
    },
    "ppt": {
        "category": FileCategory.PRESENTATION,
        "description": "PowerPoint演示（旧版）",
        "library": "textract",
        "fallback": "comtypes",
        "mime_types": ["application/vnd.ms-powerpoint"],
        "extensions": [".ppt"],
        "processor": "ppt_processor"
    },
    "odp": {
        "category": FileCategory.PRESENTATION,
        "description": "OpenDocument演示",
        "library": "odfpy",
        "fallback": "textract",
        "mime_types": ["application/vnd.oasis.opendocument.presentation"],
        "extensions": [".odp"],
        "processor": "odp_processor"
    },
    "key": {
        "category": FileCategory.PRESENTATION,
        "description": "Apple Keynote",
        "library": "textract",
        "fallback": "zipfile",
        "mime_types": ["application/x-iwork-keynote-sffkey"],
        "extensions": [".key"],
        "processor": "key_processor"
    },
    "pps": {
        "category": FileCategory.PRESENTATION,
        "description": "PowerPoint幻灯片放映",
        "library": "textract",
        "fallback": "comtypes",
        "mime_types": ["application/vnd.ms-powerpoint"],
        "extensions": [".pps"],
        "processor": "pps_processor"
    },
    "ppsx": {
        "category": FileCategory.PRESENTATION,
        "description": "PowerPoint幻灯片放映",
        "library": "python-pptx",
        "fallback": "textract",
        "mime_types": ["application/vnd.openxmlformats-officedocument.presentationml.slideshow"],
        "extensions": [".ppsx"],
        "processor": "ppsx_processor"
    },
    
    # 图片类（10种）
    "jpg": {
        "category": FileCategory.IMAGE,
        "description": "JPEG图片",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/jpeg"],
        "extensions": [".jpg", ".jpeg"],
        "processor": "jpg_processor",
        "ocr": True
    },
    "png": {
        "category": FileCategory.IMAGE,
        "description": "PNG图片",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/png"],
        "extensions": [".png"],
        "processor": "png_processor",
        "ocr": True
    },
    "gif": {
        "category": FileCategory.IMAGE,
        "description": "GIF图片",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/gif"],
        "extensions": [".gif"],
        "processor": "gif_processor",
        "ocr": True
    },
    "bmp": {
        "category": FileCategory.IMAGE,
        "description": "BMP位图",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/bmp"],
        "extensions": [".bmp"],
        "processor": "bmp_processor",
        "ocr": True
    },
    "tiff": {
        "category": FileCategory.IMAGE,
        "description": "TIFF图片",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/tiff"],
        "extensions": [".tiff", ".tif"],
        "processor": "tiff_processor",
        "ocr": True
    },
    "webp": {
        "category": FileCategory.IMAGE,
        "description": "WebP图片",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/webp"],
        "extensions": [".webp"],
        "processor": "webp_processor",
        "ocr": True
    },
    "svg": {
        "category": FileCategory.IMAGE,
        "description": "SVG矢量图",
        "library": "cairosvg",
        "fallback": "svglib",
        "mime_types": ["image/svg+xml"],
        "extensions": [".svg"],
        "processor": "svg_processor"
    },
    "ico": {
        "category": FileCategory.IMAGE,
        "description": "图标文件",
        "library": "Pillow",
        "fallback": "PIL",
        "mime_types": ["image/x-icon"],
        "extensions": [".ico"],
        "processor": "ico_processor"
    },
    "heic": {
        "category": FileCategory.IMAGE,
        "description": "HEIC图片",
        "library": "pyheif",
        "fallback": "pillow-heif",
        "mime_types": ["image/heic"],
        "extensions": [".heic", ".heif"],
        "processor": "heic_processor",
        "ocr": True
    },
    "raw": {
        "category": FileCategory.IMAGE,
        "description": "RAW相机格式",
        "library": "rawpy",
        "fallback": "imageio",
        "mime_types": ["image/x-raw"],
        "extensions": [".raw", ".cr2", ".nef"],
        "processor": "raw_processor"
    },
    
    # 音频类（6种）
    "mp3": {
        "category": FileCategory.AUDIO,
        "description": "MP3音频",
        "library": "pydub",
        "fallback": "librosa",
        "mime_types": ["audio/mpeg"],
        "extensions": [".mp3"],
        "processor": "mp3_processor",
        "transcribe": True
    },
    "wav": {
        "category": FileCategory.AUDIO,
        "description": "WAV音频",
        "library": "wave",
        "fallback": "soundfile",
        "mime_types": ["audio/wav"],
        "extensions": [".wav"],
        "processor": "wav_processor",
        "transcribe": True
    },
    "flac": {
        "category": FileCategory.AUDIO,
        "description": "FLAC无损音频",
        "library": "pydub",
        "fallback": "soundfile",
        "mime_types": ["audio/flac"],
        "extensions": [".flac"],
        "processor": "flac_processor",
        "transcribe": True
    },
    "aac": {
        "category": FileCategory.AUDIO,
        "description": "AAC音频",
        "library": "pydub",
        "fallback": "librosa",
        "mime_types": ["audio/aac"],
        "extensions": [".aac"],
        "processor": "aac_processor",
        "transcribe": True
    },
    "ogg": {
        "category": FileCategory.AUDIO,
        "description": "OGG音频",
        "library": "pydub",
        "fallback": "soundfile",
        "mime_types": ["audio/ogg"],
        "extensions": [".ogg"],
        "processor": "ogg_processor",
        "transcribe": True
    },
    "m4a": {
        "category": FileCategory.AUDIO,
        "description": "M4A音频",
        "library": "pydub",
        "fallback": "librosa",
        "mime_types": ["audio/m4a"],
        "extensions": [".m4a"],
        "processor": "m4a_processor",
        "transcribe": True
    },
    
    # 视频类（6种）
    "mp4": {
        "category": FileCategory.VIDEO,
        "description": "MP4视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/mp4"],
        "extensions": [".mp4"],
        "processor": "mp4_processor",
        "extract_audio": True
    },
    "avi": {
        "category": FileCategory.VIDEO,
        "description": "AVI视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/x-msvideo"],
        "extensions": [".avi"],
        "processor": "avi_processor",
        "extract_audio": True
    },
    "mov": {
        "category": FileCategory.VIDEO,
        "description": "MOV视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/quicktime"],
        "extensions": [".mov"],
        "processor": "mov_processor",
        "extract_audio": True
    },
    "mkv": {
        "category": FileCategory.VIDEO,
        "description": "MKV视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/x-matroska"],
        "extensions": [".mkv"],
        "processor": "mkv_processor",
        "extract_audio": True
    },
    "webm": {
        "category": FileCategory.VIDEO,
        "description": "WebM视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/webm"],
        "extensions": [".webm"],
        "processor": "webm_processor",
        "extract_audio": True
    },
    "flv": {
        "category": FileCategory.VIDEO,
        "description": "FLV视频",
        "library": "moviepy",
        "fallback": "opencv-python",
        "mime_types": ["video/x-flv"],
        "extensions": [".flv"],
        "processor": "flv_processor",
        "extract_audio": True
    },
    
    # 电子书类（5种）
    "epub": {
        "category": FileCategory.EBOOK,
        "description": "EPUB电子书",
        "library": "ebooklib",
        "fallback": "epub",
        "mime_types": ["application/epub+zip"],
        "extensions": [".epub"],
        "processor": "epub_processor"
    },
    "mobi": {
        "category": FileCategory.EBOOK,
        "description": "MOBI电子书",
        "library": "mobi",
        "fallback": "textract",
        "mime_types": ["application/x-mobipocket-ebook"],
        "extensions": [".mobi"],
        "processor": "mobi_processor"
    },
    "azw3": {
        "category": FileCategory.EBOOK,
        "description": "AZW3电子书",
        "library": "DeDRM",
        "fallback": "calibre",
        "mime_types": ["application/vnd.amazon.ebook"],
        "extensions": [".azw3"],
        "processor": "azw3_processor"
    },
    "fb2": {
        "category": FileCategory.EBOOK,
        "description": "FB2电子书",
        "library": "fb2",
        "fallback": "xml.etree.ElementTree",
        "mime_types": ["application/x-fictionbook+xml"],
        "extensions": [".fb2"],
        "processor": "fb2_processor"
    },
    "djvu": {
        "category": FileCategory.EBOOK,
        "description": "DjVu文档",
        "library": "python-djvulibre",
        "fallback": "djvulibre",
        "mime_types": ["image/vnd.djvu"],
        "extensions": [".djvu"],
        "processor": "djvu_processor"
    },
    
    # 压缩包类（4种）
    "zip": {
        "category": FileCategory.ARCHIVE,
        "description": "ZIP压缩包",
        "library": "zipfile",
        "fallback": "built-in",
        "mime_types": ["application/zip"],
        "extensions": [".zip"],
        "processor": "zip_processor"
    },
    "rar": {
        "category": FileCategory.ARCHIVE,
        "description": "RAR压缩包",
        "library": "rarfile",
        "fallback": "unrar",
        "mime_types": ["application/x-rar-compressed"],
        "extensions": [".rar"],
        "processor": "rar_processor"
    },
    "7z": {
        "category": FileCategory.ARCHIVE,
        "description": "7Z压缩包",
        "library": "py7zr",
        "fallback": "libarchive",
        "mime_types": ["application/x-7z-compressed"],
        "extensions": [".7z"],
        "processor": "7z_processor"
    },
    "tar": {
        "category": FileCategory.ARCHIVE,
        "description": "TAR归档",
        "library": "tarfile",
        "fallback": "built-in",
        "mime_types": ["application/x-tar"],
        "extensions": [".tar", ".tar.gz", ".tgz", ".tar.bz2"],
        "processor": "tar_processor"
    }
}


# ==================== 格式查询函数 ====================

def get_format_info(file_extension: str) -> Optional[Dict[str, Any]]:
    """根据文件扩展名获取格式信息"""
    ext = file_extension.lower().lstrip('.')
    return FILE_FORMATS.get(ext)


def get_supported_formats() -> List[str]:
    """获取所有支持的格式列表"""
    return list(FILE_FORMATS.keys())


def get_formats_by_category(category: FileCategory) -> List[str]:
    """根据类别获取格式列表"""
    return [fmt for fmt, info in FILE_FORMATS.items() if info["category"] == category]


def get_format_statistics() -> Dict[str, Any]:
    """获取格式统计信息"""
    total = len(FILE_FORMATS)
    by_category = {}
    for fmt, info in FILE_FORMATS.items():
        cat = info["category"]
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return {
        "total": total,
        "by_category": by_category,
        "categories": len(by_category)
    }


def check_library_available(library_name: str) -> bool:
    """检查库是否可用"""
    if library_name == "built-in":
        return True
    
    try:
        importlib.import_module(library_name.replace('-', '_'))
        return True
    except ImportError:
        return False


def get_processor_strategy(file_extension: str) -> ProcessorStrategy:
    """获取处理器策略"""
    format_info = get_format_info(file_extension)
    if not format_info:
        return None
    
    # 检查主库是否可用
    if check_library_available(format_info["library"]):
        return ProcessorStrategy.LIBRARY
    
    # 检查备选库是否可用
    if check_library_available(format_info["fallback"]):
        logger.warning(f"主库不可用，使用备选库: {format_info['fallback']}")
        return ProcessorStrategy.FALLBACK
    
    # 都不可用，需要完整代码处理器
    logger.error(f"库均不可用，需要完整代码处理器")
    return None


# ==================== 导出配置 ====================

def export_config_summary():
    """导出配置摘要"""
    stats = get_format_statistics()
    
    summary = f"""
AI-STACK V5.0 文件格式支持配置
==========================================

总计支持: {stats['total']} 种格式

按类别分类:
"""
    for category, count in stats['by_category'].items():
        summary += f"  • {category}: {count}种\n"
    
    summary += "\n策略: 优先使用库，网络问题时使用完整代码\n"
    
    return summary


if __name__ == "__main__":
    print(export_config_summary())
    print("\n支持的所有格式:")
    for fmt in get_supported_formats():
        info = get_format_info(fmt)
        print(f"  .{fmt} - {info['description']} ({info['category']})")


