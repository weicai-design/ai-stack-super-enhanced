"""
ERP数据监听系统
实现事件驱动架构，监听ERP数据变化并触发相应操作
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型枚举"""
    ORDER_CREATED = "order_created"
    ORDER_UPDATED = "order_updated"
    ORDER_DELETED = "order_deleted"
    ORDER_STATUS_CHANGED = "order_status_changed"
    
    INVENTORY_LOW = "inventory_low"
    INVENTORY_UPDATED = "inventory_updated"
    
    PRODUCTION_STARTED = "production_started"
    PRODUCTION_COMPLETED = "production_completed"
    PRODUCTION_FAILED = "production_failed"
    
    QUALITY_CHECK_PASSED = "quality_check_passed"
    QUALITY_CHECK_FAILED = "quality_check_failed"
    
    FINANCIAL_DATA_UPDATED = "financial_data_updated"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_SENT = "payment_sent"
    
    CUSTOMER_CREATED = "customer_created"
    CUSTOMER_UPDATED = "customer_updated"
    
    SUPPLIER_CREATED = "supplier_created"
    SUPPLIER_UPDATED = "supplier_updated"
    
    # 项目事件
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_STATUS_CHANGED = "project_status_changed"
    
    # 质量事件
    QUALITY_INSPECTION_CREATED = "quality_inspection_created"
    QUALITY_INSPECTION_COMPLETED = "quality_inspection_completed"
    
    # 交付事件
    DELIVERY_PLAN_CREATED = "delivery_plan_created"
    DELIVERY_STATUS_CHANGED = "delivery_status_changed"
    
    # 售后事件
    AFTER_SALES_TICKET_CREATED = "after_sales_ticket_created"
    AFTER_SALES_TICKET_UPDATED = "after_sales_ticket_updated"
    
    # 仓储事件
    WAREHOUSE_CREATED = "warehouse_created"
    STORAGE_LOCATION_CREATED = "storage_location_created"
    
    # 发运事件
    SHIPMENT_PLAN_CREATED = "shipment_plan_created"
    SHIPMENT_STATUS_CHANGED = "shipment_status_changed"
    
    # 到料事件
    RECEIVING_NOTICE_CREATED = "receiving_notice_created"
    RECEIVING_STATUS_CHANGED = "receiving_status_changed"
    
    # 设备事件
    EQUIPMENT_REGISTERED = "equipment_registered"
    EQUIPMENT_MAINTENANCE_CREATED = "equipment_maintenance_created"
    
    # 自定义事件
    CUSTOM = "custom"


@dataclass
class ERPEvent:
    """ERP事件数据类"""
    event_type: EventType
    entity_type: str  # order, inventory, production, etc.
    entity_id: str
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ERPDataListener:
    """
    ERP数据监听系统
    
    功能：
    1. 监听ERP数据变化（订单、库存、生产、财务等）
    2. 触发事件驱动的操作
    3. 与运营财务模块集成
    4. 支持自定义事件处理器
    """
    
    def __init__(self):
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.is_listening = False
        self.event_queue = asyncio.Queue()
        self.event_history: List[ERPEvent] = []
        self.max_history = 1000
        
        # 监听配置
        self.listen_config = {
            "orders": True,
            "inventory": True,
            "production": True,
            "quality": True,
            "financial": True,
            "customers": True,
            "suppliers": True
        }
        
        # 统计信息
        self.stats = {
            "total_events": 0,
            "events_by_type": {},
            "handlers_executed": 0,
            "errors": 0
        }
    
    def register_handler(
        self,
        event_type: EventType,
        handler: Callable[[ERPEvent], Any],
        priority: int = 0
    ):
        """
        注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理函数（异步或同步）
            priority: 优先级（数字越大优先级越高）
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append({
            "handler": handler,
            "priority": priority
        })
        
        # 按优先级排序
        self.event_handlers[event_type].sort(key=lambda x: x["priority"], reverse=True)
        
        logger.info(f"注册事件处理器: {event_type.value}, 优先级: {priority}")
    
    async def emit_event(self, event: ERPEvent):
        """
        发出事件
        
        Args:
            event: ERP事件
        """
        # 记录事件历史
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
        
        # 更新统计
        self.stats["total_events"] += 1
        event_type_str = event.event_type.value
        self.stats["events_by_type"][event_type_str] = \
            self.stats["events_by_type"].get(event_type_str, 0) + 1
        
        # 将事件加入队列
        await self.event_queue.put(event)
        
        logger.debug(f"发出事件: {event.event_type.value}, 实体: {event.entity_type}:{event.entity_id}")
    
    async def _process_event(self, event: ERPEvent):
        """处理单个事件"""
        event_type = event.event_type
        
        # 获取该类型的所有处理器
        handlers = self.event_handlers.get(event_type, [])
        
        if not handlers:
            logger.debug(f"事件 {event_type.value} 没有注册的处理器")
            return
        
        # 按优先级执行处理器
        for handler_info in handlers:
            handler = handler_info["handler"]
            try:
                # 检查是否是异步函数
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
                
                self.stats["handlers_executed"] += 1
            except Exception as e:
                self.stats["errors"] += 1
                logger.error(f"事件处理器执行失败: {event_type.value}, 错误: {e}", exc_info=True)
    
    async def _event_loop(self):
        """事件处理循环"""
        logger.info("ERP数据监听系统启动")
        
        while self.is_listening:
            try:
                # 从队列获取事件（带超时）
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # 处理事件
                await self._process_event(event)
                
            except asyncio.TimeoutError:
                # 超时是正常的，继续循环
                continue
            except Exception as e:
                logger.error(f"事件处理循环错误: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def start_listening(self):
        """开始监听"""
        if self.is_listening:
            logger.warning("监听系统已经在运行")
            return
        
        self.is_listening = True
        asyncio.create_task(self._event_loop())
        logger.info("ERP数据监听系统已启动")
    
    async def stop_listening(self):
        """停止监听"""
        self.is_listening = False
        logger.info("ERP数据监听系统已停止")
    
    # ========== 数据变化监听方法 ==========
    
    async def on_order_created(self, order_data: Dict[str, Any]):
        """订单创建事件"""
        event = ERPEvent(
            event_type=EventType.ORDER_CREATED,
            entity_type="order",
            entity_id=str(order_data.get("id", "")),
            new_data=order_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_order_updated(
        self,
        order_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ):
        """订单更新事件"""
        # 检查状态是否变化
        old_status = old_data.get("status")
        new_status = new_data.get("status")
        
        if old_status != new_status:
            # 发出状态变化事件
            status_event = ERPEvent(
                event_type=EventType.ORDER_STATUS_CHANGED,
                entity_type="order",
                entity_id=order_id,
                old_data={"status": old_status},
                new_data={"status": new_status},
                metadata={"action": "status_change"}
            )
            await self.emit_event(status_event)
        
        # 发出更新事件
        update_event = ERPEvent(
            event_type=EventType.ORDER_UPDATED,
            entity_type="order",
            entity_id=order_id,
            old_data=old_data,
            new_data=new_data,
            metadata={"action": "update"}
        )
        await self.emit_event(update_event)
    
    async def on_order_deleted(self, order_id: str, order_data: Dict[str, Any]):
        """订单删除事件"""
        event = ERPEvent(
            event_type=EventType.ORDER_DELETED,
            entity_type="order",
            entity_id=order_id,
            old_data=order_data,
            metadata={"action": "delete"}
        )
        await self.emit_event(event)
    
    async def on_inventory_updated(
        self,
        inventory_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ):
        """库存更新事件"""
        old_quantity = old_data.get("quantity", 0)
        new_quantity = new_data.get("quantity", 0)
        min_quantity = new_data.get("min_quantity", 0)
        
        # 检查是否低于最低库存
        if new_quantity <= min_quantity and old_quantity > min_quantity:
            low_event = ERPEvent(
                event_type=EventType.INVENTORY_LOW,
                entity_type="inventory",
                entity_id=inventory_id,
                old_data={"quantity": old_quantity},
                new_data={"quantity": new_quantity, "min_quantity": min_quantity},
                metadata={"action": "low_stock_alert"}
            )
            await self.emit_event(low_event)
        
        # 发出更新事件
        update_event = ERPEvent(
            event_type=EventType.INVENTORY_UPDATED,
            entity_type="inventory",
            entity_id=inventory_id,
            old_data=old_data,
            new_data=new_data,
            metadata={"action": "update"}
        )
        await self.emit_event(update_event)
    
    async def on_production_status_changed(
        self,
        production_id: str,
        old_status: str,
        new_status: str,
        production_data: Dict[str, Any]
    ):
        """生产状态变化事件"""
        event_type_map = {
            "started": EventType.PRODUCTION_STARTED,
            "completed": EventType.PRODUCTION_COMPLETED,
            "failed": EventType.PRODUCTION_FAILED
        }
        
        event_type = event_type_map.get(new_status)
        if event_type:
            event = ERPEvent(
                event_type=event_type,
                entity_type="production",
                entity_id=production_id,
                old_data={"status": old_status},
                new_data={"status": new_status, **production_data},
                metadata={"action": "status_change"}
            )
            await self.emit_event(event)
    
    async def on_quality_check(
        self,
        quality_id: str,
        passed: bool,
        quality_data: Dict[str, Any]
    ):
        """质量检查事件"""
        event_type = EventType.QUALITY_CHECK_PASSED if passed else EventType.QUALITY_CHECK_FAILED
        
        event = ERPEvent(
            event_type=event_type,
            entity_type="quality",
            entity_id=quality_id,
            new_data={**quality_data, "passed": passed},
            metadata={"action": "quality_check"}
        )
        await self.emit_event(event)
    
    async def on_financial_data_created(
        self,
        financial_id: str,
        financial_data: Dict[str, Any]
    ):
        """财务数据创建事件"""
        event = ERPEvent(
            event_type=EventType.FINANCIAL_DATA_UPDATED,  # 使用现有事件类型
            entity_type="financial",
            entity_id=financial_id,
            old_data={},
            new_data=financial_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_financial_data_updated(
        self,
        financial_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any]
    ):
        """财务数据更新事件"""
        event = ERPEvent(
            event_type=EventType.FINANCIAL_DATA_UPDATED,
            entity_type="financial",
            entity_id=financial_id,
            old_data=old_data,
            new_data=new_data,
            metadata={"action": "update"}
        )
        await self.emit_event(event)
    
    async def on_financial_data_deleted(
        self,
        financial_id: str,
        financial_data: Dict[str, Any]
    ):
        """财务数据删除事件"""
        event = ERPEvent(
            event_type=EventType.CUSTOM,
            entity_type="financial",
            entity_id=financial_id,
            old_data=financial_data,
            metadata={"action": "delete", "custom_type": "financial_data_deleted"}
        )
        await self.emit_event(event)
    
    async def on_payment(
        self,
        payment_id: str,
        payment_type: str,  # "received" or "sent"
        payment_data: Dict[str, Any]
    ):
        """支付事件"""
        event_type = EventType.PAYMENT_RECEIVED if payment_type == "received" else EventType.PAYMENT_SENT
        
        event = ERPEvent(
            event_type=event_type,
            entity_type="payment",
            entity_id=payment_id,
            new_data=payment_data,
            metadata={"action": payment_type}
        )
        await self.emit_event(event)
    
    async def on_procurement_order_created(
        self,
        order_id: str,
        order_data: Dict[str, Any]
    ):
        """采购订单创建事件"""
        event = ERPEvent(
            event_type=EventType.CUSTOM,
            entity_type="procurement_order",
            entity_id=order_id,
            new_data=order_data,
            metadata={"action": "create", "custom_type": "procurement_order_created"}
        )
        await self.emit_event(event)
    
    async def on_material_created(
        self,
        material_id: str,
        material_data: Dict[str, Any]
    ):
        """物料创建事件"""
        event = ERPEvent(
            event_type=EventType.CUSTOM,
            entity_type="material",
            entity_id=material_id,
            new_data=material_data,
            metadata={"action": "create", "custom_type": "material_created"}
        )
        await self.emit_event(event)
    
    async def on_project_created(
        self,
        project_id: str,
        project_data: Dict[str, Any]
    ):
        """项目创建事件"""
        event = ERPEvent(
            event_type=EventType.PROJECT_CREATED,
            entity_type="project",
            entity_id=project_id,
            new_data=project_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_project_status_changed(
        self,
        project_id: str,
        old_status: str,
        new_status: str,
        project_data: Dict[str, Any]
    ):
        """项目状态变更事件"""
        event = ERPEvent(
            event_type=EventType.PROJECT_STATUS_CHANGED,
            entity_type="project",
            entity_id=project_id,
            old_data={"status": old_status},
            new_data={"status": new_status, **project_data},
            metadata={"action": "status_change", "old_status": old_status, "new_status": new_status}
        )
        await self.emit_event(event)
    
    async def on_quality_inspection_created(
        self,
        inspection_id: str,
        inspection_data: Dict[str, Any]
    ):
        """质量检验创建事件"""
        event = ERPEvent(
            event_type=EventType.QUALITY_INSPECTION_CREATED,
            entity_type="quality_inspection",
            entity_id=inspection_id,
            new_data=inspection_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_delivery_plan_created(
        self,
        plan_id: str,
        plan_data: Dict[str, Any]
    ):
        """交付计划创建事件"""
        event = ERPEvent(
            event_type=EventType.DELIVERY_PLAN_CREATED,
            entity_type="delivery_plan",
            entity_id=plan_id,
            new_data=plan_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_after_sales_ticket_created(
        self,
        ticket_id: str,
        ticket_data: Dict[str, Any]
    ):
        """售后工单创建事件"""
        event = ERPEvent(
            event_type=EventType.AFTER_SALES_TICKET_CREATED,
            entity_type="after_sales_ticket",
            entity_id=ticket_id,
            new_data=ticket_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_warehouse_created(
        self,
        warehouse_id: str,
        warehouse_data: Dict[str, Any]
    ):
        """仓库创建事件"""
        event = ERPEvent(
            event_type=EventType.WAREHOUSE_CREATED,
            entity_type="warehouse",
            entity_id=warehouse_id,
            new_data=warehouse_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_shipment_plan_created(
        self,
        shipment_id: str,
        shipment_data: Dict[str, Any]
    ):
        """发运计划创建事件"""
        event = ERPEvent(
            event_type=EventType.SHIPMENT_PLAN_CREATED,
            entity_type="shipment",
            entity_id=shipment_id,
            new_data=shipment_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_receiving_notice_created(
        self,
        notice_id: str,
        notice_data: Dict[str, Any]
    ):
        """到料通知创建事件"""
        event = ERPEvent(
            event_type=EventType.RECEIVING_NOTICE_CREATED,
            entity_type="receiving_notice",
            entity_id=notice_id,
            new_data=notice_data,
            metadata={"action": "create"}
        )
        await self.emit_event(event)
    
    async def on_equipment_registered(
        self,
        equipment_id: str,
        equipment_data: Dict[str, Any]
    ):
        """设备注册事件"""
        event = ERPEvent(
            event_type=EventType.EQUIPMENT_REGISTERED,
            entity_type="equipment",
            entity_id=equipment_id,
            new_data=equipment_data,
            metadata={"action": "register"}
        )
        await self.emit_event(event)
    
    # ========== 工具方法 ==========
    
    def get_event_history(
        self,
        event_type: Optional[EventType] = None,
        entity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[ERPEvent]:
        """获取事件历史"""
        events = self.event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        if entity_type:
            events = [e for e in events if e.entity_type == entity_type]
        
        return events[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            queue_size = self.event_queue.qsize()
        except Exception:
            queue_size = 0
        
        return {
            **self.stats,
            "is_listening": self.is_listening,
            "queue_size": queue_size,
            "handlers_count": sum(len(handlers) for handlers in self.event_handlers.values()),
            "history_size": len(self.event_history)
        }
    
    def clear_history(self):
        """清空事件历史"""
        self.event_history.clear()
        logger.info("事件历史已清空")

