"""
文件格式处理器
支持60+种文件格式的处理
"""

from typing import Dict, List, Optional, Any, BinaryIO
from datetime import datetime
import mimetypes
import os

class FileFormatHandler:
    """
    文件格式处理器
    
    功能：
    1. 识别文件格式（60+种）
    2. 解析文件内容
    3. 提取文本/元数据
    4. 转换为统一格式
    """
    
    def __init__(self):
        # 支持的文件格式（60+种）
        self.supported_formats = {
            # 办公文档（15种）
            "office": [".doc", ".docx", ".docm", ".dot", ".dotx",
                      ".xls", ".xlsx", ".xlsm", ".xlsb", ".xlt", ".xltx",
                      ".ppt", ".pptx", ".pptm", ".pot", ".potx",
                      ".pdf", ".odt", ".ods", ".odp", ".rtf", ".msg", ".eml"],
            
            # 电子书（8种）
            "ebook": [".epub", ".mobi", ".azw", ".azw3", ".fb2", ".lit", ".prc", ".txt"],
            
            # 编程文件（30+种）
            "code": [".py", ".js", ".java", ".c", ".cpp", ".cs", ".swift", ".kt",
                    ".scala", ".dart", ".lua", ".pl", ".pm", ".sh", ".bash", ".ps1",
                    ".r", ".R", ".m", ".sql", ".md", ".html", ".css", ".php",
                    ".rb", ".go", ".rs", ".ts", ".vue", ".jsx", ".tsx",
                    ".conf", ".ini", ".toml", ".yaml", ".yml", ".json", ".xml"],
            
            # 图片（15种）
            "image": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif",
                     ".webp", ".svg", ".heic", ".heif", ".ico", ".psd", ".ai",
                     ".raw", ".cr2", ".nef", ".arw"],
            
            # 音频（10种）
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma",
                     ".opus", ".amr", ".3gp"],
            
            # 视频（10种）
            "video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm",
                    ".mpeg", ".mpg", ".3gp", ".rm", ".rmvb", ".vob"],
            
            # 思维导图（4种）
            "mindmap": [".xmind", ".mm", ".mmap", ".opml"],
            
            # 数据库（5种）
            "database": [".csv", ".sql", ".db", ".mdb", ".accdb", ".fdb", ".odb"],
            
            # 压缩文件（5种）
            "archive": [".zip", ".rar", ".7z", ".tar", ".gz"],
            
            # 其他（5种）
            "other": [".txt", ".md", ".json", ".xml", ".yaml"]
        }
        
        # 格式处理器映射
        self.processors = {}
        self._initialize_processors()
    
    def _initialize_processors(self):
        """初始化格式处理器"""
        # 办公文档处理器
        self.processors["office"] = self._process_office_document
        # 电子书处理器
        self.processors["ebook"] = self._process_ebook
        # 编程文件处理器
        self.processors["code"] = self._process_code_file
        # 图片处理器
        self.processors["image"] = self._process_image
        # 音频处理器
        self.processors["audio"] = self._process_audio
        # 视频处理器
        self.processors["video"] = self._process_video
        # 思维导图处理器
        self.processors["mindmap"] = self._process_mindmap
        # 数据库处理器
        self.processors["database"] = self._process_database
        # 压缩文件处理器
        self.processors["archive"] = self._process_archive
        # 其他处理器
        self.processors["other"] = self._process_text_file
    
    def detect_format(self, filename: str, mime_type: Optional[str] = None) -> Dict[str, Any]:
        """
        检测文件格式
        
        Args:
            filename: 文件名
            mime_type: MIME类型（可选）
            
        Returns:
            格式信息
        """
        ext = os.path.splitext(filename)[1].lower()
        
        # 检测格式类别
        format_category = None
        for category, extensions in self.supported_formats.items():
            if ext in extensions:
                format_category = category
                break
        
        if not format_category:
            format_category = "unknown"
        
        # 如果没有提供MIME类型，尝试检测
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
        
        return {
            "extension": ext,
            "category": format_category,
            "mime_type": mime_type,
            "is_supported": format_category != "unknown"
        }
    
    async def process_file(
        self,
        file_data: bytes,
        filename: str,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理文件
        
        Args:
            file_data: 文件数据
            filename: 文件名
            mime_type: MIME类型
            
        Returns:
            处理结果
        """
        format_info = self.detect_format(filename, mime_type)
        
        if not format_info["is_supported"]:
            return {
                "success": False,
                "error": f"不支持的文件格式: {format_info['extension']}",
                "format": format_info
            }
        
        category = format_info["category"]
        processor = self.processors.get(category)
        
        if not processor:
            return {
                "success": False,
                "error": f"未找到处理器: {category}",
                "format": format_info
            }
        
        try:
            result = await processor(file_data, filename, format_info)
            result["format"] = format_info
            result["success"] = True
            return result
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "format": format_info
            }
    
    async def _process_office_document(
        self,
        file_data: bytes,
        filename: str,
        format_info: Dict
    ) -> Dict[str, Any]:
        """处理办公文档"""
        ext = format_info["extension"]
        
        # Word文档
        if ext in [".doc", ".docx", ".docm", ".dot", ".dotx"]:
            return await self._extract_word_text(file_data, ext)
        
        # Excel文档
        elif ext in [".xls", ".xlsx", ".xlsm", ".xlsb", ".xlt", ".xltx"]:
            return await self._extract_excel_text(file_data, ext)
        
        # PowerPoint文档
        elif ext in [".ppt", ".pptx", ".pptm", ".pot", ".potx"]:
            return await self._extract_ppt_text(file_data, ext)
        
        # PDF
        elif ext == ".pdf":
            return await self._extract_pdf_text(file_data)
        
        # 其他格式
        else:
            return {
                "text": "",
                "metadata": {"format": ext, "note": "格式支持待完善"}
            }
    
    async def _extract_word_text(self, file_data: bytes, ext: str) -> Dict[str, Any]:
        """提取Word文档文本"""
        try:
            if ext == ".docx":
                # 使用python-docx
                try:
                    from docx import Document
                    import io
                    doc = Document(io.BytesIO(file_data))
                    text = "\n".join([para.text for para in doc.paragraphs])
                    return {"text": text, "metadata": {"format": "docx"}}
                except ImportError:
                    pass
            
            # 备用：返回基本信息
            return {
                "text": "",
                "metadata": {"format": ext, "note": "需要安装python-docx库"}
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _extract_excel_text(self, file_data: bytes, ext: str) -> Dict[str, Any]:
        """提取Excel文档文本"""
        try:
            if ext in [".xlsx", ".xlsm"]:
                # 使用openpyxl
                try:
                    from openpyxl import load_workbook
                    import io
                    wb = load_workbook(io.BytesIO(file_data), read_only=True)
                    text_parts = []
                    for sheet in wb.worksheets:
                        text_parts.append(f"工作表: {sheet.title}")
                        for row in sheet.iter_rows(values_only=True):
                            text_parts.append("\t".join([str(cell) if cell else "" for cell in row]))
                    return {"text": "\n".join(text_parts), "metadata": {"format": ext}}
                except ImportError:
                    pass
            
            return {
                "text": "",
                "metadata": {"format": ext, "note": "需要安装openpyxl库"}
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _extract_ppt_text(self, file_data: bytes, ext: str) -> Dict[str, Any]:
        """提取PPT文档文本⭐实现版"""
        try:
            if ext in [".pptx", ".pptm"]:
                # 使用python-pptx
                try:
                    from pptx import Presentation
                    import io
                    prs = Presentation(io.BytesIO(file_data))
                    text_parts = []
                    for slide_num, slide in enumerate(prs.slides, 1):
                        text_parts.append(f"幻灯片 {slide_num}:")
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text:
                                text_parts.append(shape.text)
                    return {"text": "\n".join(text_parts), "metadata": {"format": ext, "slides": len(prs.slides)}}
                except ImportError:
                    pass
            
            return {
                "text": "",
                "metadata": {"format": ext, "note": "需要安装python-pptx库"}
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _extract_pdf_text(self, file_data: bytes) -> Dict[str, Any]:
        """提取PDF文本"""
        try:
            # 尝试使用PyPDF2或pdfplumber
            try:
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_data))
                text_parts = []
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())
                return {"text": "\n".join(text_parts), "metadata": {"format": "pdf"}}
            except ImportError:
                pass
            
            return {
                "text": "",
                "metadata": {"format": "pdf", "note": "需要安装PyPDF2或pdfplumber库"}
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _process_ebook(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理电子书⭐实现版"""
        ext = format_info["extension"]
        try:
            if ext == ".epub":
                # 使用ebooklib
                try:
                    import ebooklib
                    from ebooklib import epub
                    import io
                    book = epub.read_epub(io.BytesIO(file_data))
                    text_parts = []
                    for item in book.get_items():
                        if item.get_type() == ebooklib.ITEM_DOCUMENT:
                            # 提取HTML内容中的文本（简单实现）
                            content = item.get_content().decode('utf-8', errors='ignore')
                            # 简单去除HTML标签
                            import re
                            text = re.sub(r'<[^>]+>', '', content)
                            if text.strip():
                                text_parts.append(text.strip())
                    return {"text": "\n".join(text_parts), "metadata": {"format": "epub"}}
                except ImportError:
                    pass
            
            elif ext == ".mobi":
                # MOBI格式需要特殊处理
                return {
                    "text": "",
                    "metadata": {"format": ext, "note": "MOBI格式需要mobi库"}
                }
            
            return {
                "text": "",
                "metadata": {"format": ext, "note": "需要安装ebooklib库"}
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _process_code_file(
        self,
        file_data: bytes,
        filename: str,
        format_info: Dict
    ) -> Dict[str, Any]:
        """处理编程文件"""
        try:
            text = file_data.decode('utf-8', errors='ignore')
            return {
                "text": text,
                "metadata": {
                    "format": format_info["extension"],
                    "language": self._detect_language(filename),
                    "lines": len(text.split('\n'))
                }
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    async def _process_image(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理图片⭐实现版（OCR支持）"""
        ext = format_info["extension"]
        try:
            # 尝试OCR提取文本
            try:
                import pytesseract
                from PIL import Image
                import io
                
                # 打开图片
                image = Image.open(io.BytesIO(file_data))
                
                # OCR识别
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                
                return {
                    "text": text,
                    "metadata": {
                        "format": ext,
                        "size": len(file_data),
                        "ocr": True,
                        "dimensions": image.size
                    }
                }
            except ImportError:
                pass
            
            # 如果没有OCR库，返回基本信息
            return {
                "text": "",
                "metadata": {
                    "format": ext,
                    "size": len(file_data),
                    "note": "需要安装pytesseract和Pillow库进行OCR"
                }
            }
        except Exception as e:
            return {
                "text": "",
                "metadata": {"error": str(e), "format": ext}
            }
    
    async def _process_audio(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理音频⭐实现版（语音识别支持）"""
        ext = format_info["extension"]
        try:
            # 尝试语音识别
            try:
                import speech_recognition as sr
                import io
                
                # 创建识别器
                r = sr.Recognizer()
                
                # 根据格式选择处理方式
                if ext in [".wav"]:
                    # WAV格式可以直接使用
                    audio_file = io.BytesIO(file_data)
                    with sr.AudioFile(audio_file) as source:
                        audio = r.record(source)
                        text = r.recognize_google(audio, language='zh-CN')
                        return {
                            "text": text,
                            "metadata": {
                                "format": ext,
                                "size": len(file_data),
                                "speech_recognition": True
                            }
                        }
                else:
                    # 其他格式需要转换
                    return {
                        "text": "",
                        "metadata": {
                            "format": ext,
                            "size": len(file_data),
                            "note": f"{ext}格式需要转换为WAV格式"
                        }
                    }
            except ImportError:
                pass
            
            return {
                "text": "",
                "metadata": {
                    "format": ext,
                    "size": len(file_data),
                    "note": "需要安装SpeechRecognition库进行语音识别"
                }
            }
        except Exception as e:
            return {
                "text": "",
                "metadata": {"error": str(e), "format": ext}
            }
    
    async def _process_video(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理视频"""
        return {
            "text": "",
            "metadata": {
                "format": format_info["extension"],
                "size": len(file_data),
                "note": "视频处理待实现"
            }
        }
    
    async def _process_mindmap(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理思维导图"""
        return {
            "text": "",
            "metadata": {"format": format_info["extension"], "note": "思维导图处理待实现"}
        }
    
    async def _process_database(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理数据库文件"""
        if format_info["extension"] == ".csv":
            try:
                text = file_data.decode('utf-8', errors='ignore')
                return {"text": text, "metadata": {"format": "csv"}}
            except:
                pass
        
        return {
            "text": "",
            "metadata": {"format": format_info["extension"], "note": "数据库文件处理待实现"}
        }
    
    async def _process_archive(self, file_data: bytes, filename: str, format_info: Dict) -> Dict[str, Any]:
        """处理压缩文件"""
        return {
            "text": "",
            "metadata": {
                "format": format_info["extension"],
                "note": "压缩文件需要解压后处理"
            }
        }
    
    async def _process_text_file(
        self,
        file_data: bytes,
        filename: str,
        format_info: Dict
    ) -> Dict[str, Any]:
        """处理文本文件"""
        try:
            text = file_data.decode('utf-8', errors='ignore')
            return {
                "text": text,
                "metadata": {
                    "format": format_info["extension"],
                    "lines": len(text.split('\n')),
                    "chars": len(text)
                }
            }
        except Exception as e:
            return {"text": "", "metadata": {"error": str(e)}}
    
    def _detect_language(self, filename: str) -> str:
        """检测编程语言"""
        ext = os.path.splitext(filename)[1].lower()
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".cs": "csharp",
            ".swift": "swift",
            ".kt": "kotlin",
            ".go": "go",
            ".rs": "rust",
            ".ts": "typescript",
            ".php": "php",
            ".rb": "ruby",
            ".r": "r",
            ".sql": "sql",
            ".html": "html",
            ".css": "css",
            ".sh": "shell",
            ".ps1": "powershell"
        }
        return language_map.get(ext, "unknown")
    
    def get_supported_formats(self) -> List[str]:
        """获取所有支持的文件格式"""
        all_formats = []
        for formats in self.supported_formats.values():
            all_formats.extend(formats)
        return sorted(set(all_formats))

