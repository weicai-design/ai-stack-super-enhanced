"""
File Upload Handler
文件上传处理器 - 处理OpenWebUI文件上传

功能：
1. 自动处理上传的文件
2. 将文件内容摄入到RAG库
3. 支持多种文件格式
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Any

try:
    from .rag_integration import get_rag_service
except ImportError:
    current_dir = Path(__file__).parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    from rag_integration import get_rag_service

logger = logging.getLogger(__name__)


class FileUploadHandler:
    """
    文件上传处理器
    
    处理从OpenWebUI上传的文件，自动摄入到RAG库
    """

    def __init__(self, auto_process: bool = True, temp_dir: Optional[str] = None):
        """
        初始化文件上传处理器
        
        Args:
            auto_process: 是否自动处理上传的文件
            temp_dir: 临时文件目录
        """
        self.auto_process = auto_process
        self.temp_dir = temp_dir or os.path.join(
            tempfile.gettempdir(), "openwebui_rag_uploads"
        )
        os.makedirs(self.temp_dir, exist_ok=True)
        self.rag_service = get_rag_service()

    async def process_uploaded_file(
        self,
        file_path: str,
        filename: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理上传的文件
        
        Args:
            file_path: 文件路径
            filename: 文件名（可选）
            user_id: 用户ID
            session_id: 会话ID
            metadata: 额外元数据
            
        Returns:
            处理结果字典
        """
        if not self.auto_process:
            return {"processed": False, "reason": "auto_process_disabled"}

        try:
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                return {"processed": False, "error": "文件不存在"}

            # 生成文档ID
            doc_id = self._generate_doc_id(
                file_path_obj.stem, user_id, session_id
            )

            # 准备元数据
            doc_metadata = {
                "source": "openwebui_file_upload",
                "filename": filename or file_path_obj.name,
                "file_path": str(file_path),
                "user_id": user_id,
                "session_id": session_id,
                **(metadata or {}),
            }

            # 摄入文件到RAG库
            result = await self.rag_service.ingest_file(
                file_path=str(file_path),
                doc_id=doc_id,
                save_index=True,
            )

            if result.get("success", False):
                logger.info(
                    f"文件已成功摄入RAG库: {filename}, doc_id={doc_id}"
                )
                return {
                    "processed": True,
                    "doc_id": result.get("ids", [doc_id])[0],
                    "size": result.get("size", 0),
                    "filename": filename or file_path_obj.name,
                }
            else:
                logger.warning(
                    f"文件摄入失败: {result.get('error')}, file={filename}"
                )
                return {
                    "processed": False,
                    "error": result.get("error"),
                    "filename": filename,
                }

        except Exception as e:
            logger.error(f"处理上传文件时出错: {e}")
            return {"processed": False, "error": str(e)}

    async def process_uploaded_files(
        self,
        file_paths: list[str],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        批量处理上传的文件
        
        Args:
            file_paths: 文件路径列表
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            批量处理结果字典
        """
        results = []
        success_count = 0
        fail_count = 0

        for file_path in file_paths:
            result = await self.process_uploaded_file(
                file_path, user_id=user_id, session_id=session_id
            )
            results.append(result)
            if result.get("processed", False):
                success_count += 1
            else:
                fail_count += 1

        return {
            "total": len(file_paths),
            "success": success_count,
            "failed": fail_count,
            "results": results,
        }

    def _generate_doc_id(
        self,
        filename_stem: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        生成文档ID
        
        Args:
            filename_stem: 文件名（不含扩展名）
            user_id: 用户ID
            session_id: 会话ID
            
        Returns:
            文档ID
        """
        parts = ["file", filename_stem]
        if user_id:
            parts.append(user_id)
        if session_id:
            parts.append(session_id)
        return "_".join(parts)

    def is_supported_file(self, filename: str) -> bool:
        """
        检查文件是否支持
        
        Args:
            filename: 文件名
            
        Returns:
            是否支持该文件格式
        """
        # RAG API支持的文件格式（可以根据实际支持情况扩展）
        supported_extensions = {
            ".txt",
            ".md",
            ".pdf",
            ".docx",
            ".pptx",
            ".xlsx",
            ".html",
            ".json",
            ".csv",
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".xml",
            ".yaml",
            ".yml",
        }

        file_ext = Path(filename).suffix.lower()
        return file_ext in supported_extensions

