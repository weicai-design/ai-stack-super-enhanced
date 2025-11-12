"""
内容管理器（增强版）
Content Manager

版本: v1.0.0
"""

import logging
from typing import Dict, List
from collections import defaultdict
from .models import Content, Material, PublishPlan
from .collector import material_collector
from .creator import content_creator
from .publisher import content_publisher

logger = logging.getLogger(__name__)


class ContentManager:
    """内容管理器（增强版）"""
    
    def __init__(self):
        self.materials: Dict[str, List[Material]] = defaultdict(list)
        self.contents: Dict[str, List[Content]] = defaultdict(list)
        self.plans: Dict[str, List[PublishPlan]] = defaultdict(list)
        
        # 核心组件
        self.collector = material_collector
        self.creator = content_creator
        self.publisher = content_publisher
        
        logger.info("✅ 内容管理器（增强版）已初始化")
    
    # ==================== 素材管理 ====================
    
    def collect_material(self, tenant_id: str, material: Material) -> Material:
        """收集素材"""
        material.tenant_id = tenant_id
        self.materials[tenant_id].append(material)
        return material
    
    def collect_from_web(self, tenant_id: str, keywords: List[str]) -> List[Material]:
        """从网络收集"""
        materials = self.collector.collect_from_web(keywords)
        for m in materials:
            m.tenant_id = tenant_id
            self.materials[tenant_id].append(m)
        return materials
    
    def get_materials(self, tenant_id: str) -> List[Material]:
        """获取素材列表"""
        return self.materials.get(tenant_id, [])
    
    # ==================== 内容创作 ====================
    
    def create_content(self, tenant_id: str, content: Content) -> Content:
        """创作内容"""
        content.tenant_id = tenant_id
        self.contents[tenant_id].append(content)
        return content
    
    def create_from_material(
        self,
        tenant_id: str,
        material_id: str,
        platform: str
    ) -> Content:
        """基于素材创作"""
        # 找到素材
        material = None
        for m in self.materials.get(tenant_id, []):
            if m.id == material_id:
                material = m
                break
        
        if not material:
            raise ValueError("素材不存在")
        
        content = self.creator.create_from_material(tenant_id, material, platform)
        self.contents[tenant_id].append(content)
        return content
    
    def get_contents(self, tenant_id: str) -> List[Content]:
        """获取内容列表"""
        return self.contents.get(tenant_id, [])
    
    # ==================== 发布管理 ====================
    
    def schedule_publish(self, tenant_id: str, plan: PublishPlan) -> PublishPlan:
        """计划发布"""
        plan.tenant_id = tenant_id
        self.plans[tenant_id].append(plan)
        return self.publisher.schedule_publish(tenant_id, plan)
    
    def publish_now(self, tenant_id: str, content_id: str, platform: str) -> Content:
        """立即发布"""
        # 找到内容
        content = None
        for c in self.contents.get(tenant_id, []):
            if c.id == content_id:
                content = c
                break
        
        if not content:
            raise ValueError("内容不存在")
        
        return self.publisher.publish_content(content, platform)
    
    def get_publish_plans(self, tenant_id: str) -> List[PublishPlan]:
        """获取发布计划"""
        return self.plans.get(tenant_id, [])
    
    # ==================== 效果跟踪 ====================
    
    def track_performance(self, tenant_id: str, content_id: str) -> dict:
        """跟踪效果"""
        for content in self.contents.get(tenant_id, []):
            if content.id == content_id:
                return self.publisher.track_performance(content)
        return {}


content_manager = ContentManager()

