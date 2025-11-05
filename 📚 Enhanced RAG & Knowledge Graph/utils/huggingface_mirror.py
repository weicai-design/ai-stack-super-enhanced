"""
HuggingFace Mirror Configuration
HuggingFace镜像配置工具

无VPN环境下的镜像配置和模型下载优化
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# 国内镜像列表（按优先级）
HF_MIRRORS = [
    "https://hf-mirror.com",  # HuggingFace镜像（推荐）
    "https://huggingface.co",  # 官方（备用）
]

# 默认镜像
DEFAULT_MIRROR = HF_MIRRORS[0]


def setup_huggingface_mirror(
    mirror: Optional[str] = None,
    auto_detect: bool = True,
) -> str:
    """
    设置HuggingFace镜像
    
    Args:
        mirror: 镜像URL（如果为None，自动检测）
        auto_detect: 是否自动检测可用的镜像
        
    Returns:
        使用的镜像URL
    """
    # 如果已设置，直接返回
    if "HF_ENDPOINT" in os.environ:
        current_mirror = os.environ["HF_ENDPOINT"]
        logger.debug(f"使用已设置的HuggingFace镜像: {current_mirror}")
        return current_mirror
    
    # 如果指定了镜像，直接使用
    if mirror:
        os.environ["HF_ENDPOINT"] = mirror
        logger.info(f"设置HuggingFace镜像: {mirror}")
        return mirror
    
    # 尝试从配置文件加载
    config_file = Path(__file__).parent.parent.parent / ".config" / "china_mirrors.env"
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                for line in f:
                    if line.startswith("export HF_ENDPOINT="):
                        mirror = line.split("=", 1)[1].strip().strip('"')
                        os.environ["HF_ENDPOINT"] = mirror
                        logger.info(f"从配置文件加载HuggingFace镜像: {mirror}")
                        return mirror
        except Exception as e:
            logger.debug(f"读取配置文件失败: {e}")
    
    # 自动检测可用镜像
    if auto_detect:
        for test_mirror in HF_MIRRORS:
            if _test_mirror_accessible(test_mirror):
                os.environ["HF_ENDPOINT"] = test_mirror
                logger.info(f"自动检测到可用的HuggingFace镜像: {test_mirror}")
                return test_mirror
    
    # 使用默认镜像
    os.environ["HF_ENDPOINT"] = DEFAULT_MIRROR
    logger.info(f"使用默认HuggingFace镜像: {DEFAULT_MIRROR}")
    return DEFAULT_MIRROR


def _test_mirror_accessible(mirror: str, timeout: int = 3) -> bool:
    """
    测试镜像是否可访问
    
    Args:
        mirror: 镜像URL
        timeout: 超时时间（秒）
        
    Returns:
        是否可访问
    """
    try:
        import urllib.request
        import socket
        
        socket.setdefaulttimeout(timeout)
        host = mirror.replace("https://", "").replace("http://", "").split("/")[0]
        socket.create_connection((host, 443), timeout=timeout)
        return True
    except Exception:
        return False


def ensure_mirror_configured() -> str:
    """
    确保HuggingFace镜像已配置
    
    在导入模型前调用此函数，确保使用正确的镜像
    
    Returns:
        使用的镜像URL
    """
    return setup_huggingface_mirror()


# 自动配置（模块导入时）
if "HF_ENDPOINT" not in os.environ:
    ensure_mirror_configured()

