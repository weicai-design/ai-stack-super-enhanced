"""内容创作器"""
import logging
from .models import Content, Material

logger = logging.getLogger(__name__)

class ContentCreator:
    def __init__(self):
        logger.info("✅ 内容创作器已初始化")
    
    def create_from_material(self, tenant_id: str, material: Material, platform: str) -> Content:
        """基于素材创作内容"""
        content = Content(
            tenant_id=tenant_id,
            title=material.title,
            body=f"根据素材创作的内容：\n\n{material.content}\n\n去AI化处理，形成差异化内容。",
            platform=platform,
            status="draft"
        )
        logger.info(f"内容已创作: {content.title}")
        return content
    
    def generate_unique_content(self, tenant_id: str, topic: str, platform: str) -> Content:
        """生成独特内容"""
        content = Content(
            tenant_id=tenant_id,
            title=f"{topic} - 原创内容",
            body=f"关于{topic}的独特见解...",
            platform=platform
        )
        return content

content_creator = ContentCreator()






































