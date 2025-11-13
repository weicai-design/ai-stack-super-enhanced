"""内容发布器"""
import logging
from datetime import datetime
from .models import Content, PublishPlan

logger = logging.getLogger(__name__)

class ContentPublisher:
    def __init__(self):
        logger.info("✅ 内容发布器已初始化")
    
    def publish_content(self, content: Content, platform: str) -> Content:
        """发布内容到平台"""
        content.platform = platform
        content.status = "published"
        content.published_at = datetime.now()
        logger.info(f"内容已发布: {content.title} -> {platform}")
        return content
    
    def schedule_publish(self, tenant_id: str, plan: PublishPlan) -> PublishPlan:
        """计划发布"""
        plan.tenant_id = tenant_id
        logger.info(f"发布已计划: {plan.content_id} -> {plan.platform}")
        return plan
    
    def track_performance(self, content: Content) -> dict:
        """跟踪效果"""
        return {
            "content_id": content.id,
            "platform": content.platform,
            "views": content.views,
            "likes": content.likes,
            "engagement_rate": content.likes / content.views if content.views > 0 else 0
        }

content_publisher = ContentPublisher()

















