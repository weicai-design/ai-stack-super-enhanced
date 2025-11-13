"""素材收集器"""
import logging
from typing import List
from .models import Material

logger = logging.getLogger(__name__)

class MaterialCollector:
    def __init__(self):
        logger.info("✅ 素材收集器已初始化")
    
    def collect_from_web(self, keywords: List[str], platform: str = "all") -> List[Material]:
        """从网络收集素材"""
        materials = []
        for keyword in keywords:
            material = Material(
                tenant_id="default",
                title=f"热点素材: {keyword}",
                content=f"关于{keyword}的内容...",
                source=platform,
                tags=[keyword]
            )
            materials.append(material)
        logger.info(f"收集素材: {len(materials)}个")
        return materials

material_collector = MaterialCollector()

















