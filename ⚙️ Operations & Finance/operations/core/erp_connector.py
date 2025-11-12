"""
ERP连接器
API接口 + 单向监听ERP（事件驱动架构）⭐增强版
"""

from typing import Dict, List, Optional, Any, Callable
import asyncio
import httpx
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ERPConnector:
    """
    ERP连接器⭐增强版
    
    功能：
    1. API接口获取数据
    2. 单向监听ERP数据变化（事件驱动）
    3. 数据同步
    4. 与ERP数据监听系统集成
    """
    
    def __init__(
        self,
        connection_type: str = "both",  # api, listener, both
        erp_api_url: str = "http://localhost:8013",
        listener_api_url: Optional[str] = None
    ):
        self.connection_type = connection_type
        self.erp_api_url = erp_api_url
        self.listener_api_url = listener_api_url or f"{erp_api_url}/api/erp/listener"
        self.listening = False
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.synced_data_cache: Dict[str, Any] = {}
        
    async def get_manufacturing_data(self) -> Dict[str, Any]:
        """通过API获取制造数据"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 获取订单数据
                orders_response = await client.get(f"{self.erp_api_url}/api/customer/orders")
                orders = orders_response.json().get("orders", []) if orders_response.status_code == 200 else []
                
                # 获取项目数据
                projects_response = await client.get(f"{self.erp_api_url}/api/customer/projects")
                projects = projects_response.json().get("projects", []) if projects_response.status_code == 200 else []
                
                # 获取生产数据
                production_response = await client.get(f"{self.erp_api_url}/api/production/plans")
                production = production_response.json().get("plans", []) if production_response.status_code == 200 else []
                
                # 获取交付数据
                delivery_response = await client.get(f"{self.erp_api_url}/api/warehouse/deliveries")
                delivery = delivery_response.json().get("deliveries", []) if delivery_response.status_code == 200 else []
                
                # 获取回款数据
                payment_response = await client.get(f"{self.erp_api_url}/api/finance/payments")
                payment = payment_response.json().get("payments", []) if payment_response.status_code == 200 else []
                
                data = {
                    "orders": orders,
                    "projects": projects,
                    "production": production,
                    "delivery": delivery,
                    "payment": payment,
                    "timestamp": datetime.now().isoformat()
                }
                
                # 更新缓存
                self.synced_data_cache = data
                
                return data
        except Exception as e:
            logger.error(f"获取ERP数据失败: {e}")
            return self.synced_data_cache or {
                "orders": [],
                "projects": [],
                "production": [],
                "delivery": [],
                "payment": [],
                "error": str(e)
            }
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.info(f"注册事件处理器: {event_type}")
    
    async def _handle_erp_event(self, event: Dict[str, Any]):
        """处理ERP事件"""
        event_type = event.get("event_type", "")
        entity_type = event.get("entity_type", "")
        
        # 调用注册的处理器
        handlers = list(self.event_handlers.get(event_type, []))
        handlers.extend(self.event_handlers.get("*", []))  # 全局处理器
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {e}", exc_info=True)
        
        # 更新缓存数据
        await self._update_cache_from_event(event)
    
    async def _update_cache_from_event(self, event: Dict[str, Any]):
        """根据事件更新缓存"""
        event_type = event.get("event_type", "")
        entity_type = event.get("entity_type", "")
        new_data = event.get("new_data", {})
        
        # 根据事件类型更新相应缓存
        if entity_type == "order":
            if "order_created" in event_type or "order_updated" in event_type:
                # 更新订单缓存
                if "orders" not in self.synced_data_cache:
                    self.synced_data_cache["orders"] = []
                # 查找并更新或添加订单
                order_id = event.get("entity_id")
                orders = self.synced_data_cache["orders"]
                existing = next((o for o in orders if str(o.get("id")) == order_id), None)
                if existing:
                    existing.update(new_data)
                else:
                    orders.append(new_data)
        
        elif entity_type == "financial":
            if "financial_data_updated" in event_type:
                # 更新财务数据缓存
                if "financial" not in self.synced_data_cache:
                    self.synced_data_cache["financial"] = []
                # 更新财务数据
                financial_id = event.get("entity_id")
                financial = self.synced_data_cache.get("financial", [])
                existing = next((f for f in financial if str(f.get("id")) == financial_id), None)
                if existing:
                    existing.update(new_data)
                else:
                    financial.append(new_data)
    
    async def start_listening(self, callback: Optional[Callable] = None):
        """开始监听ERP数据变化（事件驱动）⭐"""
        if "listener" not in self.connection_type:
            logger.warning("连接类型不包含listener，跳过监听启动")
            return
        
        self.listening = True
        
        # 注册到ERP数据监听系统
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 注册事件处理器（通过webhook）
                webhook_url = f"{self.erp_api_url.replace(':8013', ':8014')}/api/operations/erp-events"
                
                handler_request = {
                    "event_type": "*",  # 监听所有事件
                    "handler_name": "operations_finance_handler",
                    "handler_url": webhook_url,
                    "priority": 10
                }
                
                response = await client.post(
                    f"{self.listener_api_url}/register-handler",
                    json=handler_request
                )
                
                if response.status_code == 200:
                    logger.info("已注册到ERP数据监听系统")
                else:
                    logger.warning(f"注册监听系统失败: {response.status_code}")
        except Exception as e:
            logger.error(f"注册监听系统失败: {e}")
        
        # 启动事件处理循环
        asyncio.create_task(self._event_processing_loop(callback))
        logger.info("ERP数据监听已启动（事件驱动架构）")
    
    async def _event_processing_loop(self, callback: Optional[Callable] = None):
        """事件处理循环⭐修复版"""
        processed_event_ids = set()  # 跟踪已处理的事件ID
        
        while self.listening:
            try:
                # 从ERP监听系统获取事件
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(
                        f"{self.listener_api_url}/events/history",
                        params={"limit": 10}
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        events = result.get("events", [])
                        
                        # 处理新事件（避免重复处理）
                        for event in events:
                            # 生成事件唯一ID
                            event_id = f"{event.get('event_type')}:{event.get('entity_type')}:{event.get('entity_id')}:{event.get('timestamp')}"
                            
                            if event_id not in processed_event_ids:
                                processed_event_ids.add(event_id)
                                
                                # 只保留最近100个事件ID，避免内存泄漏
                                if len(processed_event_ids) > 100:
                                    # 移除最旧的事件ID（简化实现）
                                    processed_event_ids = set(list(processed_event_ids)[-100:])
                                
                                await self._handle_erp_event(event)
                                if callback:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(event)
                                    else:
                                        callback(event)
                
                await asyncio.sleep(5)  # 每5秒检查一次
            except httpx.TimeoutException:
                logger.warning("获取事件超时，继续重试")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"事件处理循环错误: {e}", exc_info=True)
                await asyncio.sleep(5)
    
    def stop_listening(self):
        """停止监听"""
        self.listening = False
        logger.info("ERP数据监听已停止")
    
    async def sync_data(self):
        """同步数据（主动拉取）"""
        data = await self.get_manufacturing_data()
        return data
    
    def get_cached_data(self) -> Dict[str, Any]:
        """获取缓存数据"""
        return self.synced_data_cache.copy()

