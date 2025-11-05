"""
Archive File Extractor
压缩文件提取器

根据需求1.1：支持压缩文件（ZIP, RAR, 7Z等）
功能：
1. 支持多种压缩格式
2. 自动解压并提取内容
3. 处理嵌套压缩文件
4. 安全限制（文件大小、深度等）
"""

import logging
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ArchiveExtractor:
    """
    压缩文件提取器
    
    支持格式：
    - ZIP (.zip)
    - RAR (.rar) - 需要rarfile库
    - 7Z (.7z) - 需要py7zr库
    """

    def __init__(
        self,
        max_size_mb: int = 500,
        max_depth: int = 3,
        max_files: int = 1000,
        extract_to_temp: bool = True,
    ):
        """
        初始化压缩文件提取器
        
        Args:
            max_size_mb: 最大解压大小（MB）
            max_depth: 最大嵌套深度
            max_files: 最大文件数量
            extract_to_temp: 是否解压到临时目录
        """
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_depth = max_depth
        self.max_files = max_files
        self.extract_to_temp = extract_to_temp
        
        # 检查可选依赖
        self.has_rarfile = False
        self.has_py7zr = False
        
        try:
            import rarfile
            self.rarfile = rarfile
            self.has_rarfile = True
        except ImportError:
            logger.warning("rarfile未安装，RAR格式支持受限")
        
        try:
            import py7zr
            self.py7zr = py7zr
            self.has_py7zr = True
        except ImportError:
            logger.warning("py7zr未安装，7Z格式支持受限")

    def extract_archive(
        self, archive_path: str, output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解压压缩文件
        
        Args:
            archive_path: 压缩文件路径
            output_dir: 输出目录（如果为None且extract_to_temp=True，使用临时目录）
            
        Returns:
            解压结果字典
        """
        if not os.path.exists(archive_path):
            return {
                "success": False,
                "error": f"文件不存在: {archive_path}",
            }

        archive_ext = Path(archive_path).suffix.lower()
        
        # 确定输出目录
        if output_dir is None and self.extract_to_temp:
            output_dir = tempfile.mkdtemp(prefix="archive_extract_")
            cleanup_temp = True
        else:
            cleanup_temp = False
            if output_dir is None:
                output_dir = os.path.join(os.path.dirname(archive_path), "extracted")

        try:
            # 根据格式选择解压方法
            if archive_ext == ".zip":
                result = self._extract_zip(archive_path, output_dir)
            elif archive_ext == ".rar":
                result = self._extract_rar(archive_path, output_dir)
            elif archive_ext in [".7z", ".7zip"]:
                result = self._extract_7z(archive_path, output_dir)
            else:
                return {
                    "success": False,
                    "error": f"不支持的压缩格式: {archive_ext}",
                }
            
            result["output_dir"] = output_dir
            result["cleanup_temp"] = cleanup_temp
            
            return result
            
        except Exception as e:
            logger.error(f"解压失败 {archive_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "output_dir": output_dir,
            }

    def _extract_zip(
        self, zip_path: str, output_dir: str
    ) -> Dict[str, Any]:
        """解压ZIP文件"""
        extracted_files = []
        total_size = 0
        file_count = 0
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # 检查总大小
                total_archive_size = sum(info.file_size for info in zip_ref.infolist())
                if total_archive_size > self.max_size_bytes:
                    return {
                        "success": False,
                        "error": f"压缩包过大: {total_archive_size / (1024*1024):.2f}MB > {self.max_size_bytes / (1024*1024)}MB",
                    }
                
                # 解压文件
                for member_info in zip_ref.infolist():
                    if file_count >= self.max_files:
                        logger.warning(f"达到最大文件数量限制: {self.max_files}")
                        break
                    
                    # 安全检查：防止路径遍历攻击
                    member_path = member_info.filename
                    if os.path.isabs(member_path) or ".." in member_path:
                        logger.warning(f"跳过可疑路径: {member_path}")
                        continue
                    
                    extracted_path = os.path.join(output_dir, member_path)
                    
                    # 确保目录存在
                    if member_path.endswith('/'):
                        os.makedirs(extracted_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                        zip_ref.extract(member_info, output_dir)
                        
                        file_size = os.path.getsize(extracted_path)
                        total_size += file_size
                        file_count += 1
                        extracted_files.append(extracted_path)
                        
                        if total_size > self.max_size_bytes:
                            logger.warning(f"达到最大解压大小限制: {self.max_size_bytes / (1024*1024)}MB")
                            break
                
                return {
                    "success": True,
                    "format": "zip",
                    "extracted_files": extracted_files,
                    "file_count": file_count,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                }
        except zipfile.BadZipFile:
            return {
                "success": False,
                "error": "无效的ZIP文件",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"ZIP解压失败: {str(e)}",
            }

    def _extract_rar(
        self, rar_path: str, output_dir: str
    ) -> Dict[str, Any]:
        """解压RAR文件"""
        if not self.has_rarfile:
            return {
                "success": False,
                "error": "rarfile库未安装，无法解压RAR文件",
            }
        
        extracted_files = []
        total_size = 0
        file_count = 0
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with self.rarfile.RarFile(rar_path) as rar_ref:
                # 解压文件
                for member_info in rar_ref.infolist():
                    if file_count >= self.max_files:
                        logger.warning(f"达到最大文件数量限制: {self.max_files}")
                        break
                    
                    # 安全检查
                    member_path = member_info.filename
                    if os.path.isabs(member_path) or ".." in member_path:
                        logger.warning(f"跳过可疑路径: {member_path}")
                        continue
                    
                    extracted_path = os.path.join(output_dir, member_path)
                    
                    if member_info.isdir():
                        os.makedirs(extracted_path, exist_ok=True)
                    else:
                        os.makedirs(os.path.dirname(extracted_path), exist_ok=True)
                        rar_ref.extract(member_info, output_dir)
                        
                        file_size = os.path.getsize(extracted_path)
                        total_size += file_size
                        file_count += 1
                        extracted_files.append(extracted_path)
                        
                        if total_size > self.max_size_bytes:
                            logger.warning(f"达到最大解压大小限制: {self.max_size_bytes / (1024*1024)}MB")
                            break
                
                return {
                    "success": True,
                    "format": "rar",
                    "extracted_files": extracted_files,
                    "file_count": file_count,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                }
        except self.rarfile.RarCannotExec:
            return {
                "success": False,
                "error": "RAR解压工具未找到（需要安装unrar）",
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"RAR解压失败: {str(e)}",
            }

    def _extract_7z(
        self, sevenz_path: str, output_dir: str
    ) -> Dict[str, Any]:
        """解压7Z文件"""
        if not self.has_py7zr:
            return {
                "success": False,
                "error": "py7zr库未安装，无法解压7Z文件",
            }
        
        extracted_files = []
        total_size = 0
        file_count = 0
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            with self.py7zr.SevenZipFile(sevenz_path, mode='r') as archive:
                archive.extractall(path=output_dir)
                
                # 统计解压的文件
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        total_size += file_size
                        file_count += 1
                        extracted_files.append(file_path)
                        
                        if file_count >= self.max_files or total_size > self.max_size_bytes:
                            break
                    if file_count >= self.max_files or total_size > self.max_size_bytes:
                        break
                
                return {
                    "success": True,
                    "format": "7z",
                    "extracted_files": extracted_files,
                    "file_count": file_count,
                    "total_size": total_size,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"7Z解压失败: {str(e)}",
            }

    def list_archive_contents(self, archive_path: str) -> Dict[str, Any]:
        """
        列出压缩文件内容（不解压）
        
        Args:
            archive_path: 压缩文件路径
            
        Returns:
            文件列表字典
        """
        if not os.path.exists(archive_path):
            return {
                "success": False,
                "error": f"文件不存在: {archive_path}",
            }

        archive_ext = Path(archive_path).suffix.lower()
        
        try:
            if archive_ext == ".zip":
                return self._list_zip_contents(archive_path)
            elif archive_ext == ".rar":
                return self._list_rar_contents(archive_path)
            elif archive_ext in [".7z", ".7zip"]:
                return self._list_7z_contents(archive_path)
            else:
                return {
                    "success": False,
                    "error": f"不支持的压缩格式: {archive_ext}",
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _list_zip_contents(self, zip_path: str) -> Dict[str, Any]:
        """列出ZIP文件内容"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = []
                total_size = 0
                
                for member_info in zip_ref.infolist():
                    file_list.append({
                        "name": member_info.filename,
                        "size": member_info.file_size,
                        "compressed_size": member_info.compress_size,
                        "is_dir": member_info.filename.endswith('/'),
                    })
                    total_size += member_info.file_size
                
                return {
                    "success": True,
                    "format": "zip",
                    "files": file_list,
                    "file_count": len(file_list),
                    "total_size": total_size,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _list_rar_contents(self, rar_path: str) -> Dict[str, Any]:
        """列出RAR文件内容"""
        if not self.has_rarfile:
            return {
                "success": False,
                "error": "rarfile库未安装",
            }
        
        try:
            with self.rarfile.RarFile(rar_path) as rar_ref:
                file_list = []
                total_size = 0
                
                for member_info in rar_ref.infolist():
                    file_list.append({
                        "name": member_info.filename,
                        "size": member_info.file_size,
                        "compressed_size": member_info.compress_size,
                        "is_dir": member_info.isdir(),
                    })
                    total_size += member_info.file_size
                
                return {
                    "success": True,
                    "format": "rar",
                    "files": file_list,
                    "file_count": len(file_list),
                    "total_size": total_size,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    def _list_7z_contents(self, sevenz_path: str) -> Dict[str, Any]:
        """列出7Z文件内容"""
        if not self.has_py7zr:
            return {
                "success": False,
                "error": "py7zr库未安装",
            }
        
        try:
            with self.py7zr.SevenZipFile(sevenz_path, mode='r') as archive:
                file_list = []
                total_size = 0
                
                for member in archive.getnames():
                    file_info = archive.getmember(member)
                    file_list.append({
                        "name": member,
                        "size": file_info.uncompressed if hasattr(file_info, 'uncompressed') else 0,
                        "compressed_size": file_info.compressed if hasattr(file_info, 'compressed') else 0,
                        "is_dir": member.endswith('/'),
                    })
                    if hasattr(file_info, 'uncompressed'):
                        total_size += file_info.uncompressed
                
                return {
                    "success": True,
                    "format": "7z",
                    "files": file_list,
                    "file_count": len(file_list),
                    "total_size": total_size,
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# 全局实例
_archive_extractor: Optional[ArchiveExtractor] = None


def get_archive_extractor(**kwargs) -> ArchiveExtractor:
    """获取压缩文件提取器实例（单例）"""
    global _archive_extractor
    if _archive_extractor is None:
        _archive_extractor = ArchiveExtractor(**kwargs)
    return _archive_extractor

