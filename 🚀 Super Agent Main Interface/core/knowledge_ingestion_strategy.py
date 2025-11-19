"""
知识自动入库策略
定义何时、如何将知识沉淀到RAG
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
from .knowledge_template import KnowledgePriority

logger = logging.getLogger(__name__)


class IngestionTrigger(Enum):
    """入库触发条件"""
    IMMEDIATE = "immediate"  # 立即入库
    BATCH = "batch"  # 批量入库
    SCHEDULED = "scheduled"  # 定时入库
    THRESHOLD = "threshold"  # 达到阈值时入库
    QUALITY_BASED = "quality_based"  # 基于质量分数


class IngestionPriority(Enum):
    """入库优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class IngestionRule:
    """入库规则"""
    rule_id: str
    name: str
    description: str
    trigger: IngestionTrigger
    conditions: Dict[str, Any]  # 触发条件
    priority: IngestionPriority = IngestionPriority.NORMAL
    enabled: bool = True
    template_id: Optional[str] = None  # 使用的模板ID
    filters: Dict[str, Any] = field(default_factory=dict)  # 过滤条件
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class IngestionQueueItem:
    """入库队列项"""
    item_id: str
    knowledge_entry: Any  # KnowledgeEntry
    rule_id: Optional[str] = None
    priority: IngestionPriority = IngestionPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None


class KnowledgeIngestionStrategy:
    """知识自动入库策略"""
    
    def __init__(self, template_manager, rag_service=None):
        """
        初始化入库策略
        
        Args:
            template_manager: 知识模板管理器
            rag_service: RAG服务（可选，用于直接入库）
        """
        self.template_manager = template_manager
        self.rag_service = rag_service
        
        # 入库规则
        self.rules: Dict[str, IngestionRule] = {}
        
        # 入库队列
        self.queue: List[IngestionQueueItem] = []
        self.processed_items: List[IngestionQueueItem] = []
        
        # 统计信息
        self.stats = {
            "total_ingested": 0,
            "total_failed": 0,
            "total_skipped": 0,
            "by_type": {},
            "by_priority": {}
        }
        
        # 初始化默认规则
        self._init_default_rules()
        
        logger.info("知识自动入库策略系统初始化完成")
    
    def _init_default_rules(self):
        """初始化默认入库规则"""
        # 立即入库规则：高优先级知识
        self.add_rule(IngestionRule(
            rule_id="immediate_high_priority",
            name="高优先级立即入库",
            description="高优先级或关键知识立即入库",
            trigger=IngestionTrigger.IMMEDIATE,
            conditions={
                "priority": ["high", "critical"],
                "quality_score": 70.0  # 质量分数>=70
            },
            priority=IngestionPriority.URGENT,
            enabled=True
        ))
        
        # 批量入库规则：普通知识
        self.add_rule(IngestionRule(
            rule_id="batch_normal",
            name="普通知识批量入库",
            description="普通知识批量入库（每10条或每5分钟）",
            trigger=IngestionTrigger.BATCH,
            conditions={
                "batch_size": 10,
                "batch_interval": 300  # 5分钟
            },
            priority=IngestionPriority.NORMAL,
            enabled=True
        ))
        
        # 质量入库规则：高质量知识
        self.add_rule(IngestionRule(
            rule_id="quality_based",
            name="基于质量分数入库",
            description="质量分数>=80的知识立即入库",
            trigger=IngestionTrigger.QUALITY_BASED,
            conditions={
                "quality_score": 80.0
            },
            priority=IngestionPriority.HIGH,
            enabled=True
        ))
        
        # 定时入库规则：每日入库
        self.add_rule(IngestionRule(
            rule_id="scheduled_daily",
            name="每日定时入库",
            description="每日凌晨2点入库队列中的知识",
            trigger=IngestionTrigger.SCHEDULED,
            conditions={
                "schedule": "0 2 * * *"  # Cron格式
            },
            priority=IngestionPriority.LOW,
            enabled=True
        ))
    
    def add_rule(self, rule: IngestionRule):
        """添加入库规则"""
        self.rules[rule.rule_id] = rule
        logger.info(f"入库规则已添加: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """移除入库规则"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"入库规则已移除: {rule_id}")
    
    def should_ingest(
        self,
        knowledge_entry: Any,
        rule: Optional[IngestionRule] = None
    ) -> tuple[bool, Optional[str]]:
        """
        判断是否应该入库
        
        Args:
            knowledge_entry: 知识条目
            rule: 入库规则（可选，如果不提供则检查所有规则）
            
        Returns:
            (是否应该入库, 匹配的规则ID)
        """
        rules_to_check = [rule] if rule else self.rules.values()
        
        for r in rules_to_check:
            if not r.enabled:
                continue
            
            # 检查触发条件
            if r.trigger == IngestionTrigger.IMMEDIATE:
                # 检查优先级
                if "priority" in r.conditions:
                    required_priorities = r.conditions["priority"]
                    if isinstance(required_priorities, str):
                        required_priorities = [required_priorities]
                    if knowledge_entry.priority.value not in required_priorities:
                        continue
                
                # 检查质量分数
                if "quality_score" in r.conditions:
                    min_score = r.conditions["quality_score"]
                    if knowledge_entry.quality_score < min_score:
                        continue
                
                return True, r.rule_id
            
            elif r.trigger == IngestionTrigger.QUALITY_BASED:
                min_score = r.conditions.get("quality_score", 80.0)
                if knowledge_entry.quality_score >= min_score:
                    return True, r.rule_id
            
            elif r.trigger == IngestionTrigger.BATCH:
                # 批量入库：总是加入队列
                return True, r.rule_id
        
        return False, None
    
    def queue_for_ingestion(
        self,
        knowledge_entry: Any,
        rule_id: Optional[str] = None,
        priority: Optional[IngestionPriority] = None
    ) -> str:
        """
        将知识条目加入入库队列
        
        Args:
            knowledge_entry: 知识条目
            rule_id: 规则ID（可选）
            priority: 优先级（可选）
            
        Returns:
            队列项ID
        """
        import uuid
        
        # 确定优先级
        if not priority:
            if knowledge_entry.priority == KnowledgePriority.CRITICAL:
                priority = IngestionPriority.URGENT
            elif knowledge_entry.priority == KnowledgePriority.HIGH:
                priority = IngestionPriority.HIGH
            else:
                priority = IngestionPriority.NORMAL
        
        item_id = f"queue_{int(datetime.now().timestamp() * 1000)}_{uuid.uuid4().hex[:8]}"
        
        item = IngestionQueueItem(
            item_id=item_id,
            knowledge_entry=knowledge_entry,
            rule_id=rule_id,
            priority=priority
        )
        
        # 根据优先级插入队列
        if priority == IngestionPriority.URGENT:
            self.queue.insert(0, item)
        elif priority == IngestionPriority.HIGH:
            # 插入到第一个普通优先级之前
            insert_pos = 0
            for i, q_item in enumerate(self.queue):
                if q_item.priority == IngestionPriority.NORMAL:
                    insert_pos = i
                    break
            self.queue.insert(insert_pos, item)
        else:
            self.queue.append(item)
        
        logger.debug(f"知识条目已加入入库队列: {item_id}")
        
        return item_id
    
    async def ingest_immediate(
        self,
        knowledge_entry: Any,
        rag_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        立即入库
        
        Args:
            knowledge_entry: 知识条目
            rag_service: RAG服务（可选）
            
        Returns:
            入库结果
        """
        service = rag_service or self.rag_service
        if not service:
            return {
                "success": False,
                "error": "RAG服务未配置"
            }
        
        try:
            # 转换为RAG格式
            rag_data = knowledge_entry.to_rag_format()
            
            # 调用RAG入库接口
            # 这里假设RAG服务有ingest_text方法
            if hasattr(service, 'ingest_text'):
                result = service.ingest_text(
                    text=rag_data["text"],
                    doc_id=rag_data["doc_id"],
                    metadata=rag_data["metadata"],
                    save_index=True
                )
            else:
                # 如果没有ingest_text方法，尝试HTTP调用
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8011/api/rag/ingest/text",
                        json={
                            "text": rag_data["text"],
                            "metadata": rag_data["metadata"],
                            "save_index": True
                        },
                        timeout=30
                    )
                    result = response.json()
            
            if result.get("success", False):
                self.stats["total_ingested"] += 1
                entry_type = knowledge_entry.knowledge_type.value
                self.stats["by_type"][entry_type] = self.stats["by_type"].get(entry_type, 0) + 1
                
                logger.info(f"知识条目已入库: {knowledge_entry.entry_id}")
                
                return {
                    "success": True,
                    "entry_id": knowledge_entry.entry_id,
                    "doc_id": rag_data["doc_id"],
                    "message": "知识已成功入库到RAG"
                }
            else:
                self.stats["total_failed"] += 1
                error_msg = result.get("error", "未知错误")
                logger.error(f"知识入库失败: {error_msg}")
                
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except Exception as e:
            self.stats["total_failed"] += 1
            logger.error(f"知识入库异常: {e}", exc_info=True)
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def process_queue(
        self,
        batch_size: int = 10,
        rag_service: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        处理入库队列
        
        Args:
            batch_size: 批量处理大小
            rag_service: RAG服务（可选）
            
        Returns:
            处理结果
        """
        if not self.queue:
            return {
                "success": True,
                "processed": 0,
                "message": "队列为空"
            }
        
        processed = 0
        failed = 0
        skipped = 0
        
        # 取出要处理的项
        items_to_process = self.queue[:batch_size]
        self.queue = self.queue[batch_size:]
        
        for item in items_to_process:
            try:
                # 检查重试次数
                if item.retry_count >= item.max_retries:
                    skipped += 1
                    self.stats["total_skipped"] += 1
                    logger.warning(f"队列项已达到最大重试次数，跳过: {item.item_id}")
                    continue
                
                # 入库
                result = await self.ingest_immediate(item.knowledge_entry, rag_service)
                
                if result.get("success", False):
                    processed += 1
                    item.error = None
                else:
                    failed += 1
                    item.retry_count += 1
                    item.error = result.get("error")
                    
                    # 如果未达到最大重试次数，重新加入队列
                    if item.retry_count < item.max_retries:
                        self.queue.append(item)
                
                # 记录到已处理列表
                self.processed_items.append(item)
                
                # 限制已处理列表大小
                if len(self.processed_items) > 1000:
                    self.processed_items = self.processed_items[-1000:]
            
            except Exception as e:
                failed += 1
                item.retry_count += 1
                item.error = str(e)
                logger.error(f"处理队列项失败: {e}", exc_info=True)
                
                if item.retry_count < item.max_retries:
                    self.queue.append(item)
        
        return {
            "success": True,
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "remaining": len(self.queue)
        }
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            "queue_size": len(self.queue),
            "processed_count": len(self.processed_items),
            "by_priority": {
                priority.value: sum(1 for item in self.queue if item.priority == priority)
                for priority in IngestionPriority
            },
            "stats": self.stats
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """获取所有规则"""
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "trigger": r.trigger.value,
                "conditions": r.conditions,
                "priority": r.priority.value,
                "enabled": r.enabled,
                "template_id": r.template_id,
                "created_at": r.created_at.isoformat()
            }
            for r in self.rules.values()
        ]

