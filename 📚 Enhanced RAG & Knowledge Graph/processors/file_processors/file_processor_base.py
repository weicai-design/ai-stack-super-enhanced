"""
File Processor Base Class
文件处理器基类 - 所有文件处理器的基类
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class FileProcessorBase(ABC):
    """文件处理器基类"""
    
    def __init__(self):
        self._processing_stats = {
            "success_count": 0,
            "error_count": 0,
            "total_files_processed": 0
        }
    
    async def initialize(self, config: Dict[str, Any], core_services: Dict[str, Any]):
        """初始化处理器"""
        self.config = config
        self.core_services = core_services
        logger.info(f"{self.__class__.__name__} 初始化完成")
    
    @abstractmethod
    async def process_file(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """处理文件的主要方法"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """返回支持的格式列表"""
        pass
    
    def get_processing_stats(self) -> Dict[str, int]:
        """获取处理统计信息"""
        return self._processing_stats.copy()
    
    def _update_stats(self, success: bool = True):
        """更新统计信息"""
        if success:
            self._processing_stats["success_count"] += 1
        else:
            self._processing_stats["error_count"] += 1
        self._processing_stats["total_files_processed"] += 1
    
    async def get_health_status(self) -> Dict[str, Any]:
        """返回健康状态"""
        return {
            "status": "healthy",
            "processing_stats": self.get_processing_stats()
        }
    
    async def stop(self):
        """停止处理器"""
        logger.info(f"{self.__class__.__name__} 停止完成")
    
    async def reload_config(self, new_config: Dict[str, Any]):
        """重新加载配置"""
        self.config = new_config
        logger.info(f"{self.__class__.__name__} 配置已更新")
