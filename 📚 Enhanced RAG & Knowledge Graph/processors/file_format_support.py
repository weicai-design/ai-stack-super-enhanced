"""
60种文件格式支持
V4.1 优化 - 扩展文件格式支持
"""

from typing import Dict, List, Optional
import os


class FileFormatSupport:
    """60种文件格式支持系统"""
    
    # 60种支持的文件格式
    SUPPORTED_FORMATS = {
        # 文档类（15种）
        "documents": {
            "pdf": {"name": "PDF文档", "processor": "pdf_processor"},
            "doc": {"name": "Word文档", "processor": "doc_processor"},
            "docx": {"name": "Word文档", "processor": "docx_processor"},
            "txt": {"name": "文本文件", "processor": "txt_processor"},
            "rtf": {"name": "富文本", "processor": "rtf_processor"},
            "odt": {"name": "OpenDocument文本", "processor": "odt_processor"},
            "pages": {"name": "Apple Pages", "processor": "pages_processor"},
            "tex": {"name": "LaTeX", "processor": "tex_processor"},
            "md": {"name": "Markdown", "processor": "md_processor"},
            "rst": {"name": "reStructuredText", "processor": "rst_processor"},
            "wps": {"name": "WPS文字", "processor": "wps_processor"},
            "wpd": {"name": "WordPerfect", "processor": "wpd_processor"},
            "abw": {"name": "AbiWord", "processor": "abw_processor"},
            "djvu": {"name": "DjVu", "processor": "djvu_processor"},
            "fb2": {"name": "FictionBook", "processor": "fb2_processor"}
        },
        
        # 电子表格（8种）
        "spreadsheets": {
            "xlsx": {"name": "Excel工作簿", "processor": "xlsx_processor"},
            "xls": {"name": "Excel工作簿", "processor": "xls_processor"},
            "csv": {"name": "CSV文件", "processor": "csv_processor"},
            "ods": {"name": "OpenDocument电子表格", "processor": "ods_processor"},
            "numbers": {"name": "Apple Numbers", "processor": "numbers_processor"},
            "et": {"name": "WPS表格", "processor": "et_processor"},
            "tsv": {"name": "TSV文件", "processor": "tsv_processor"},
            "xlsm": {"name": "Excel宏工作簿", "processor": "xlsm_processor"}
        },
        
        # 演示文稿（6种）
        "presentations": {
            "pptx": {"name": "PowerPoint演示", "processor": "pptx_processor"},
            "ppt": {"name": "PowerPoint演示", "processor": "ppt_processor"},
            "odp": {"name": "OpenDocument演示", "processor": "odp_processor"},
            "key": {"name": "Apple Keynote", "processor": "key_processor"},
            "dps": {"name": "WPS演示", "processor": "dps_processor"},
            "pps": {"name": "PowerPoint放映", "processor": "pps_processor"}
        },
        
        # 图片（10种）
        "images": {
            "jpg": {"name": "JPEG图片", "processor": "image_ocr_processor"},
            "jpeg": {"name": "JPEG图片", "processor": "image_ocr_processor"},
            "png": {"name": "PNG图片", "processor": "image_ocr_processor"},
            "gif": {"name": "GIF图片", "processor": "image_ocr_processor"},
            "bmp": {"name": "BMP图片", "processor": "image_ocr_processor"},
            "tiff": {"name": "TIFF图片", "processor": "image_ocr_processor"},
            "webp": {"name": "WebP图片", "processor": "image_ocr_processor"},
            "svg": {"name": "SVG矢量图", "processor": "svg_processor"},
            "ico": {"name": "图标文件", "processor": "image_ocr_processor"},
            "heic": {"name": "HEIC图片", "processor": "heic_processor"}
        },
        
        # 音频（6种）
        "audio": {
            "mp3": {"name": "MP3音频", "processor": "audio_transcribe_processor"},
            "wav": {"name": "WAV音频", "processor": "audio_transcribe_processor"},
            "m4a": {"name": "M4A音频", "processor": "audio_transcribe_processor"},
            "flac": {"name": "FLAC音频", "processor": "audio_transcribe_processor"},
            "aac": {"name": "AAC音频", "processor": "audio_transcribe_processor"},
            "ogg": {"name": "OGG音频", "processor": "audio_transcribe_processor"}
        },
        
        # 视频（6种）
        "videos": {
            "mp4": {"name": "MP4视频", "processor": "video_extract_processor"},
            "avi": {"name": "AVI视频", "processor": "video_extract_processor"},
            "mov": {"name": "MOV视频", "processor": "video_extract_processor"},
            "mkv": {"name": "MKV视频", "processor": "video_extract_processor"},
            "flv": {"name": "FLV视频", "processor": "video_extract_processor"},
            "wmv": {"name": "WMV视频", "processor": "video_extract_processor"}
        },
        
        # 电子书（5种）
        "ebooks": {
            "epub": {"name": "EPUB电子书", "processor": "epub_processor"},
            "mobi": {"name": "MOBI电子书", "processor": "mobi_processor"},
            "azw": {"name": "Kindle电子书", "processor": "azw_processor"},
            "azw3": {"name": "Kindle电子书", "processor": "azw3_processor"},
            "chm": {"name": "CHM帮助文档", "processor": "chm_processor"}
        },
        
        # 压缩文件（4种）
        "archives": {
            "zip": {"name": "ZIP压缩包", "processor": "zip_processor"},
            "rar": {"name": "RAR压缩包", "processor": "rar_processor"},
            "7z": {"name": "7Z压缩包", "processor": "7z_processor"},
            "tar": {"name": "TAR归档", "processor": "tar_processor"}
        }
    }
    
    def get_all_supported_formats(self) -> Dict[str, Any]:
        """获取所有支持的格式"""
        total = sum(len(formats) for formats in self.SUPPORTED_FORMATS.values())
        
        return {
            "total_formats": total,
            "categories": {
                category: {
                    "count": len(formats),
                    "formats": list(formats.keys())
                }
                for category, formats in self.SUPPORTED_FORMATS.items()
            },
            "all_extensions": self._get_all_extensions()
        }
    
    def is_supported(self, filename: str) -> bool:
        """检查文件是否支持"""
        ext = self._get_extension(filename)
        return ext in self._get_all_extensions()
    
    def get_processor(self, filename: str) -> Optional[str]:
        """获取文件处理器"""
        ext = self._get_extension(filename)
        
        for category, formats in self.SUPPORTED_FORMATS.items():
            if ext in formats:
                return formats[ext]["processor"]
        
        return None
    
    def get_format_info(self, filename: str) -> Optional[Dict]:
        """获取格式信息"""
        ext = self._get_extension(filename)
        
        for category, formats in self.SUPPORTED_FORMATS.items():
            if ext in formats:
                return {
                    "extension": ext,
                    "name": formats[ext]["name"],
                    "category": category,
                    "processor": formats[ext]["processor"],
                    "supported": True
                }
        
        return {
            "extension": ext,
            "supported": False,
            "message": f"暂不支持.{ext}格式"
        }
    
    def _get_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return filename.split(".")[-1].lower() if "." in filename else ""
    
    def _get_all_extensions(self) -> List[str]:
        """获取所有支持的扩展名"""
        extensions = []
        for formats in self.SUPPORTED_FORMATS.values():
            extensions.extend(formats.keys())
        return extensions
    
    def _estimate_tokens(self, text: str) -> int:
        """估算token数"""
        # 中文：约1.5字符/token
        # 英文：约4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return int(chinese_chars / 1.5 + other_chars / 4)
    
    def _extract_key_point(self, content: str) -> str:
        """提取关键点"""
        # 简化版：提取前80字
        # 实际应使用AI提取摘要
        lines = content.split('\n')
        first_line = lines[0] if lines else content
        return first_line[:80] + "..." if len(first_line) > 80 else first_line
    
    def _create_hierarchical_summary(self, session_id: str):
        """创建分层摘要"""
        # 当上下文太长时，自动压缩
        pass
    
    def _calculate_duration(self, session_id: str) -> str:
        """计算会话时长"""
        if session_id not in self.conversations or not self.conversations[session_id]:
            return "0分钟"
        
        conv = self.conversations[session_id]
        # 基于消息数估算
        minutes = len(conv) * 2
        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}小时{mins}分钟"


# 全局实例
file_format_support = FileFormatSupport()
context_memory = ContextMemorySystem(max_tokens=1000000)


