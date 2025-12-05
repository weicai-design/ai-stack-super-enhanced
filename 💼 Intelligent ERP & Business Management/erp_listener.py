#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP监听器（生产级实现）
4.3: 支持Webhook/轮询，写入任务队列
"""

from __future__ import annotations

import os
import logging
import asyncio
from typing import Any, Dict, Optional, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import httpx
import hashlib
import hmac
import json
from urllib.parse import urlparse, parse_qs

# 导入ERP核心模块
from core.data_listener import ERPDataListener, EventType, ERPEvent
from core.listener_container import data_listener

logger = logging.getLogger(__name__)

# 导入任务队列（如果存在）
try:
    from core.task_planning import TaskPlanning
    TASK_PLANNING_AVAILABLE = True
except ImportError:
    TASK_PLANNING_AVAILABLE = False
    logger.warning("TaskPlanning模块不可用，将使用内置任务队列")


class ListenerMode(str, Enum):
    """监听模式"""
    WEBHOOK = "webhook"  # Webhook模式
    POLLING = "polling"  # 轮询模式
    HYBRID = "hybrid"  # 混合模式（同时支持Webhook和轮询）


class ERPListener:
    """
    ERP监听器（生产级）
    
    功能：
    1. Webhook接收（接收ERP系统的推送事件）
    2. 轮询查询（主动查询ERP系统数据变化）
    3. 任务队列写入（将事件转换为任务并写入队列）
    """
    
    def __init__(
        self,
        erp_api_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        polling_interval: int = 60,  # 轮询间隔（秒）
        mode: ListenerMode = ListenerMode.HYBRID,
        task_queue: Optional[asyncio.Queue] = None,
    ):
        """
        初始化ERP监听器
        
        Args:
            erp_api_url: ERP系统API地址
            webhook_secret: Webhook签名密钥（用于验证请求）
            polling_interval: 轮询间隔（秒）
            mode: 监听模式
            task_queue: 任务队列（如果为None，则创建新的队列）
        """
        # ERP系统配置
        self.erp_api_url = erp_api_url or os.getenv("ERP_API_URL", "http://localhost:8013")
        self.webhook_secret = webhook_secret or os.getenv("ERP_WEBHOOK_SECRET", "")
        self.polling_interval = polling_interval
        self.mode = mode
        
        # 任务队列
        if task_queue:
            self.task_queue = task_queue
        else:
            self.task_queue = asyncio.Queue(maxsize=1000)
        
        # 集成现有的ERP数据监听器
        self.data_listener = data_listener
        
        # 轮询状态
        self.is_polling = False
        self.polling_task: Optional[asyncio.Task] = None
        self.last_poll_time: Optional[datetime] = None
        self.last_poll_results: Dict[str, Any] = {}
        
        # Webhook状态
        self.webhook_endpoints: Dict[str, Callable] = {}
        self.webhook_stats = {
            "total_received": 0,
            "valid_requests": 0,
            "invalid_requests": 0,
            "errors": 0,
        }
        
        # 任务队列统计
        self.task_queue_stats = {
            "total_enqueued": 0,
            "total_processed": 0,
            "failed_tasks": 0,
            "current_size": 0,
            "max_size": 0,
        }
        
        # HTTP客户端
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "ERP-Listener/1.0",
                "Content-Type": "application/json",
            },
        )
        
        # 任务处理任务
        self.task_processor_task: Optional[asyncio.Task] = None
        self.is_processing = False
        
        logger.info(f"ERP监听器初始化完成，模式: {mode.value}, ERP API: {self.erp_api_url}")
    
    async def start(self):
        """启动监听器"""
        try:
            # 启动任务处理循环
            if not self.is_processing:
                self.is_processing = True
                self.task_processor_task = asyncio.create_task(self._task_processor_loop())
                logger.info("任务处理循环已启动")
            
            # 根据模式启动相应的监听
            if self.mode in [ListenerMode.POLLING, ListenerMode.HYBRID]:
                await self.start_polling()
            
            if self.mode in [ListenerMode.WEBHOOK, ListenerMode.HYBRID]:
                logger.info("Webhook模式已启用，等待接收请求")
            
            logger.info(f"ERP监听器已启动，模式: {self.mode.value}")
            
        except Exception as e:
            logger.error(f"启动监听器失败: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """停止监听器"""
        try:
            # 停止轮询
            if self.is_polling:
                await self.stop_polling()
            
            # 停止任务处理
            if self.is_processing:
                self.is_processing = False
                if self.task_processor_task:
                    self.task_processor_task.cancel()
                    try:
                        await self.task_processor_task
                    except asyncio.CancelledError:
                        pass
            
            # 关闭HTTP客户端
            await self.client.aclose()
            
            logger.info("ERP监听器已停止")
            
        except Exception as e:
            logger.error(f"停止监听器失败: {e}", exc_info=True)
    
    # ============ Webhook 功能 ============
    
    async def handle_webhook(
        self,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        处理Webhook请求
        
        Args:
            payload: Webhook数据
            signature: 请求签名（用于验证）
            headers: HTTP请求头
            
        Returns:
            处理结果
        """
        try:
            self.webhook_stats["total_received"] += 1
            
            # 验证签名（如果提供）
            if signature and self.webhook_secret:
                if not self._verify_webhook_signature(payload, signature, headers):
                    self.webhook_stats["invalid_requests"] += 1
                    logger.warning("Webhook签名验证失败")
                    return {
                        "success": False,
                        "error": "签名验证失败",
                    }
            
            # 提取事件信息
            event_type = payload.get("event_type", "")
            entity_type = payload.get("entity_type", "")
            entity_id = payload.get("entity_id", "")
            data = payload.get("data", {})
            
            if not event_type or not entity_type or not entity_id:
                self.webhook_stats["invalid_requests"] += 1
                return {
                    "success": False,
                    "error": "缺少必要字段: event_type, entity_type, entity_id",
                }
            
            # 创建ERP事件
            erp_event = ERPEvent(
                event_type=EventType.CUSTOM,  # 或根据event_type映射
                entity_type=entity_type,
                entity_id=str(entity_id),
                new_data=data,
                metadata={
                    "source": "webhook",
                    "received_at": datetime.now().isoformat(),
                    "original_payload": payload,
                },
            )
            
            # 将事件写入任务队列
            await self._enqueue_task(erp_event)
            
            self.webhook_stats["valid_requests"] += 1
            
            logger.info(f"Webhook事件已接收: {event_type}, 实体: {entity_type}:{entity_id}")
            
            return {
                "success": True,
                "message": "Webhook已处理",
                "event_id": erp_event.entity_id,
            }
            
        except Exception as e:
            self.webhook_stats["errors"] += 1
            logger.error(f"处理Webhook失败: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
    
    def _verify_webhook_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        验证Webhook签名（生产级实现）
        
        Args:
            payload: Webhook数据
            signature: 请求签名
            headers: HTTP请求头
            
        Returns:
            是否验证通过
        """
        # 参数验证
        if not signature or not isinstance(signature, str):
            logger.error("无效的签名")
            return False
        
        if not self.webhook_secret:
            logger.error("缺少webhook_secret，无法验证签名")
            return False
        
        try:
            # 构建签名字符串（根据ERP系统文档的签名算法）
            timestamp = headers.get("X-Timestamp", "") if headers else ""
            nonce = headers.get("X-Nonce", "") if headers else ""
            
            if not timestamp or not nonce:
                logger.error("回调数据缺少X-Timestamp或X-Nonce字段")
                return False
            
            body_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            sign_str = f"{timestamp}{nonce}{body_str}{self.webhook_secret}"
            
            # 计算签名
            calculated_signature = hashlib.sha256(sign_str.encode()).hexdigest()
            
            # 安全比较（防止时序攻击）
            if len(calculated_signature) != len(signature):
                logger.warning("签名长度不匹配")
                return False
            
            # 使用hmac.compare_digest进行安全比较
            return hmac.compare_digest(calculated_signature, signature)
            
        except Exception as e:
            logger.error(f"签名验证异常: {e}", exc_info=True)
            return False
    
    # ============ 轮询功能 ============
    
    async def start_polling(self):
        """启动轮询"""
        if self.is_polling:
            logger.warning("轮询已在运行")
            return
        
        self.is_polling = True
        self.polling_task = asyncio.create_task(self._polling_loop())
        logger.info(f"轮询已启动，间隔: {self.polling_interval}秒")
    
    async def stop_polling(self):
        """停止轮询"""
        if not self.is_polling:
            return
        
        self.is_polling = False
        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        
        logger.info("轮询已停止")
    
    async def _polling_loop(self):
        """轮询循环（生产级实现）"""
        logger.info("轮询循环已启动")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_polling:
            try:
                # 执行轮询
                await self._poll_erp_data()
                
                # 重置连续错误计数
                consecutive_errors = 0
                
                # 等待下一次轮询
                await asyncio.sleep(self.polling_interval)
                
            except asyncio.CancelledError:
                logger.info("轮询循环已取消")
                break
            except httpx.TimeoutException as e:
                consecutive_errors += 1
                error_msg = f"轮询超时: {str(e)}"
                logger.error(error_msg)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"连续{max_consecutive_errors}次轮询超时，暂停轮询")
                    await asyncio.sleep(self.polling_interval * 2)
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(self.polling_interval)
            except httpx.HTTPStatusError as e:
                consecutive_errors += 1
                error_msg = f"轮询HTTP错误 {e.response.status_code}: {e.response.text}"
                logger.error(error_msg)
                
                # 如果是5xx错误，增加等待时间
                if e.response.status_code >= 500:
                    await asyncio.sleep(self.polling_interval * 2)
                else:
                    await asyncio.sleep(self.polling_interval)
            except Exception as e:
                consecutive_errors += 1
                error_msg = f"轮询错误: {str(e)}"
                logger.error(error_msg, exc_info=True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error(f"连续{max_consecutive_errors}次轮询错误，暂停轮询")
                    await asyncio.sleep(self.polling_interval * 2)
                    consecutive_errors = 0
                else:
                    await asyncio.sleep(self.polling_interval)
    
    async def _poll_erp_data(self):
        """
        轮询ERP数据
        
        查询ERP系统的数据变化，检测新订单、库存变化、生产状态等
        """
        try:
            current_time = datetime.now()
            
            # 查询订单变化
            await self._poll_orders()
            
            # 查询库存变化
            await self._poll_inventory()
            
            # 查询生产状态
            await self._poll_production()
            
            # 查询财务数据
            await self._poll_financial()
            
            self.last_poll_time = current_time
            
        except Exception as e:
            logger.error(f"轮询ERP数据失败: {e}", exc_info=True)
    
    async def _poll_orders(self):
        """轮询订单数据"""
        try:
            # 查询最近的订单
            params = {
                "limit": 50,
                "sort": "updated_at",
                "order": "desc",
            }
            
            # 如果有上次轮询时间，只查询更新的订单
            if self.last_poll_time:
                params["updated_since"] = self.last_poll_time.isoformat()
            
            response = await self.client.get(
                f"{self.erp_api_url}/api/orders",
                params=params,
            )
            
            if response.status_code == 200:
                data = response.json()
                orders = data.get("orders", [])
                
                # 检测新订单或更新的订单
                for order in orders:
                    order_id = order.get("order_id") or order.get("id")
                    if not order_id:
                        continue
                    
                    # 检查是否是新的或更新的订单
                    last_result = self.last_poll_results.get("orders", {})
                    last_order = last_result.get(str(order_id))
                    
                    if not last_order:
                        # 新订单
                        event = ERPEvent(
                            event_type=EventType.ORDER_CREATED,
                            entity_type="order",
                            entity_id=str(order_id),
                            new_data=order,
                            metadata={
                                "source": "polling",
                                "polled_at": datetime.now().isoformat(),
                            },
                        )
                        await self._enqueue_task(event)
                    elif last_order.get("updated_at") != order.get("updated_at"):
                        # 订单已更新
                        event = ERPEvent(
                            event_type=EventType.ORDER_UPDATED,
                            entity_type="order",
                            entity_id=str(order_id),
                            old_data=last_order,
                            new_data=order,
                            metadata={
                                "source": "polling",
                                "polled_at": datetime.now().isoformat(),
                            },
                        )
                        await self._enqueue_task(event)
                
                # 保存本次轮询结果
                self.last_poll_results["orders"] = {
                    str(order.get("order_id") or order.get("id")): order
                    for order in orders
                }
                
        except Exception as e:
            logger.error(f"轮询订单失败: {e}", exc_info=True)
    
    async def _poll_inventory(self):
        """轮询库存数据"""
        try:
            params = {
                "limit": 100,
                "sort": "updated_at",
                "order": "desc",
            }
            
            if self.last_poll_time:
                params["updated_since"] = self.last_poll_time.isoformat()
            
            response = await self.client.get(
                f"{self.erp_api_url}/api/inventory",
                params=params,
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    item_id = item.get("item_id") or item.get("id")
                    if not item_id:
                        continue
                    
                    # 检查库存变化
                    last_result = self.last_poll_results.get("inventory", {})
                    last_item = last_result.get(str(item_id))
                    
                    if last_item:
                        quantity = item.get("quantity", 0)
                        last_quantity = last_item.get("quantity", 0)
                        min_stock = item.get("min_stock", 0)
                        
                        # 库存更新事件
                        if quantity != last_quantity:
                            event = ERPEvent(
                                event_type=EventType.INVENTORY_UPDATED,
                                entity_type="inventory",
                                entity_id=str(item_id),
                                old_data=last_item,
                                new_data=item,
                                metadata={
                                    "source": "polling",
                                    "polled_at": datetime.now().isoformat(),
                                },
                            )
                            await self._enqueue_task(event)
                        
                        # 库存不足告警
                        if quantity < min_stock and last_quantity >= min_stock:
                            event = ERPEvent(
                                event_type=EventType.INVENTORY_LOW,
                                entity_type="inventory",
                                entity_id=str(item_id),
                                new_data=item,
                                metadata={
                                    "source": "polling",
                                    "polled_at": datetime.now().isoformat(),
                                    "alert": "库存不足",
                                },
                            )
                            await self._enqueue_task(event)
                
                self.last_poll_results["inventory"] = {
                    str(item.get("item_id") or item.get("id")): item
                    for item in items
                }
                
        except Exception as e:
            logger.error(f"轮询库存失败: {e}", exc_info=True)
    
    async def _poll_production(self):
        """轮询生产数据"""
        try:
            params = {
                "limit": 50,
                "sort": "updated_at",
                "order": "desc",
            }
            
            if self.last_poll_time:
                params["updated_since"] = self.last_poll_time.isoformat()
            
            response = await self.client.get(
                f"{self.erp_api_url}/api/production/executions",
                params=params,
            )
            
            if response.status_code == 200:
                data = response.json()
                executions = data.get("executions", [])
                
                for execution in executions:
                    exec_id = execution.get("execution_id") or execution.get("id")
                    if not exec_id:
                        continue
                    
                    status = execution.get("status", "")
                    last_result = self.last_poll_results.get("production", {})
                    last_exec = last_result.get(str(exec_id))
                    
                    if last_exec and last_exec.get("status") != status:
                        # 生产状态变化
                        event_type = None
                        if status == "completed":
                            event_type = EventType.PRODUCTION_COMPLETED
                        elif status == "failed":
                            event_type = EventType.PRODUCTION_FAILED
                        elif status == "started":
                            event_type = EventType.PRODUCTION_STARTED
                        
                        if event_type:
                            event = ERPEvent(
                                event_type=event_type,
                                entity_type="production",
                                entity_id=str(exec_id),
                                old_data=last_exec,
                                new_data=execution,
                                metadata={
                                    "source": "polling",
                                    "polled_at": datetime.now().isoformat(),
                                },
                            )
                            await self._enqueue_task(event)
                
                self.last_poll_results["production"] = {
                    str(exec.get("execution_id") or exec.get("id")): exec
                    for exec in executions
                }
                
        except Exception as e:
            logger.error(f"轮询生产数据失败: {e}", exc_info=True)
    
    async def _poll_financial(self):
        """轮询财务数据"""
        try:
            params = {
                "limit": 50,
                "sort": "updated_at",
                "order": "desc",
            }
            
            if self.last_poll_time:
                params["updated_since"] = self.last_poll_time.isoformat()
            
            response = await self.client.get(
                f"{self.erp_api_url}/api/finance/data",
                params=params,
            )
            
            if response.status_code == 200:
                data = response.json()
                financial_data = data.get("data", [])
                
                for fd in financial_data:
                    fd_id = fd.get("id")
                    if not fd_id:
                        continue
                    
                    last_result = self.last_poll_results.get("financial", {})
                    last_fd = last_result.get(str(fd_id))
                    
                    if not last_fd:
                        # 新的财务数据
                        event = ERPEvent(
                            event_type=EventType.FINANCIAL_DATA_UPDATED,
                            entity_type="financial",
                            entity_id=str(fd_id),
                            new_data=fd,
                            metadata={
                                "source": "polling",
                                "polled_at": datetime.now().isoformat(),
                            },
                        )
                        await self._enqueue_task(event)
                
                self.last_poll_results["financial"] = {
                    str(fd.get("id")): fd
                    for fd in financial_data
                }
                
        except Exception as e:
            logger.error(f"轮询财务数据失败: {e}", exc_info=True)
    
    # ============ 任务队列功能 ============
    
    async def _enqueue_task(self, event: ERPEvent):
        """
        将事件转换为任务并写入任务队列（生产级实现）
        
        Args:
            event: ERP事件
        """
        try:
            # 构建任务数据
            task_data = {
                "task_id": f"ERP_{event.entity_type}_{event.entity_id}_{int(datetime.now().timestamp())}",
                "task_type": "erp_event",
                "event_type": event.event_type.value,
                "entity_type": event.entity_type,
                "entity_id": event.entity_id,
                "data": {
                    "old_data": event.old_data,
                    "new_data": event.new_data,
                    "metadata": event.metadata,
                },
                "priority": self._calculate_priority(event),
                "status": "pending",
                "created_at": event.timestamp.isoformat(),
                "retry_count": 0,
                "max_retries": 3,
            }
            
            # 检查队列是否已满
            if self.task_queue.full():
                logger.warning("任务队列已满，等待空间...")
                # 可以选择丢弃低优先级任务或等待
                try:
                    await asyncio.wait_for(
                        self.task_queue.put(task_data),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    logger.error(f"任务入队超时，任务ID: {task_data['task_id']}")
                    return
            else:
                await self.task_queue.put(task_data)
            
            # 更新统计
            self.task_queue_stats["total_enqueued"] += 1
            self.task_queue_stats["current_size"] = self.task_queue.qsize()
            if self.task_queue_stats["current_size"] > self.task_queue_stats["max_size"]:
                self.task_queue_stats["max_size"] = self.task_queue_stats["current_size"]
            
            # 同时发送到ERP数据监听器
            try:
                await self.data_listener.emit_event(event)
            except Exception as e:
                logger.warning(f"发送事件到数据监听器失败: {e}")
            
            logger.debug(f"任务已入队: {task_data['task_id']}, 优先级: {task_data['priority']}")
            
        except Exception as e:
            logger.error(f"入队任务失败: {e}", exc_info=True)
    
    def _calculate_priority(self, event: ERPEvent) -> int:
        """
        计算任务优先级
        
        Args:
            event: ERP事件
            
        Returns:
            优先级（1-10，数字越大优先级越高）
        """
        # 根据事件类型设置优先级
        priority_map = {
            EventType.ORDER_CREATED: 8,
            EventType.ORDER_STATUS_CHANGED: 7,
            EventType.INVENTORY_LOW: 9,  # 库存不足高优先级
            EventType.PRODUCTION_FAILED: 9,
            EventType.QUALITY_CHECK_FAILED: 8,
            EventType.PAYMENT_RECEIVED: 6,
            EventType.FINANCIAL_DATA_UPDATED: 5,
        }
        
        return priority_map.get(event.event_type, 5)
    
    async def _task_processor_loop(self):
        """任务处理循环（生产级实现）"""
        logger.info("任务处理循环已启动")
        
        max_retries = 3
        retry_delay = 1.0
        
        while self.is_processing:
            try:
                # 从队列获取任务（带超时）
                try:
                    task_data = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # 处理任务（带重试）
                retry_count = 0
                task_success = False
                
                while retry_count < max_retries and not task_success:
                    try:
                        await self._process_task(task_data)
                        task_success = True
                        
                        # 更新统计
                        self.task_queue_stats["total_processed"] += 1
                        self.task_queue_stats["current_size"] = self.task_queue.qsize()
                        
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            logger.warning(
                                f"任务处理失败，重试 {retry_count}/{max_retries}: {str(e)}"
                            )
                            await asyncio.sleep(retry_delay * retry_count)
                        else:
                            logger.error(
                                f"任务处理失败，已达最大重试次数: {str(e)}",
                                exc_info=True
                            )
                            # 将失败的任务记录到失败队列（如果实现）
                            self.task_queue_stats["failed_tasks"] = \
                                self.task_queue_stats.get("failed_tasks", 0) + 1
                
            except asyncio.CancelledError:
                logger.info("任务处理循环已取消")
                break
            except Exception as e:
                logger.error(f"任务处理循环错误: {e}", exc_info=True)
                await asyncio.sleep(1)
    
    async def _process_task(self, task_data: Dict[str, Any]):
        """
        处理任务
        
        Args:
            task_data: 任务数据
        """
        try:
            task_id = task_data.get("task_id")
            event_type = task_data.get("event_type")
            entity_type = task_data.get("entity_type")
            entity_id = task_data.get("entity_id")
            data = task_data.get("data", {})
            
            logger.info(f"处理任务: {task_id}, 事件: {event_type}, 实体: {entity_type}:{entity_id}")
            
            # 如果TaskPlanning可用，创建任务
            if TASK_PLANNING_AVAILABLE:
                try:
                    # 这里可以集成TaskPlanning系统
                    # task_planning = TaskPlanning()
                    # await task_planning.create_task_from_event(task_data)
                    pass
                except Exception as e:
                    logger.warning(f"集成TaskPlanning失败: {e}")
            
            # 执行任务处理逻辑
            # 这里可以根据不同的事件类型执行不同的处理逻辑
            await self._execute_task_handler(task_data)
            
        except Exception as e:
            logger.error(f"处理任务失败: {e}", exc_info=True)
    
    async def _execute_task_handler(self, task_data: Dict[str, Any]):
        """
        执行任务处理器
        
        Args:
            task_data: 任务数据
        """
        event_type = task_data.get("event_type")
        entity_type = task_data.get("entity_type")
        
        # 根据事件类型和实体类型执行不同的处理逻辑
        if entity_type == "order":
            await self._handle_order_task(task_data)
        elif entity_type == "inventory":
            await self._handle_inventory_task(task_data)
        elif entity_type == "production":
            await self._handle_production_task(task_data)
        elif entity_type == "financial":
            await self._handle_financial_task(task_data)
        else:
            logger.debug(f"未实现的任务处理器: {entity_type}")
    
    async def _handle_order_task(self, task_data: Dict[str, Any]):
        """处理订单任务"""
        # 实现订单相关的处理逻辑
        pass
    
    async def _handle_inventory_task(self, task_data: Dict[str, Any]):
        """处理库存任务"""
        # 实现库存相关的处理逻辑
        pass
    
    async def _handle_production_task(self, task_data: Dict[str, Any]):
        """处理生产任务"""
        # 实现生产相关的处理逻辑
        pass
    
    async def _handle_financial_task(self, task_data: Dict[str, Any]):
        """处理财务任务"""
        # 实现财务相关的处理逻辑
        pass
    
    # ============ 状态查询 ============
    
    def get_status(self) -> Dict[str, Any]:
        """获取监听器状态"""
        return {
            "mode": self.mode.value,
            "is_polling": self.is_polling,
            "is_processing": self.is_processing,
            "last_poll_time": self.last_poll_time.isoformat() if self.last_poll_time else None,
            "webhook_stats": self.webhook_stats,
            "task_queue_stats": {
                **self.task_queue_stats,
                "current_size": self.task_queue.qsize(),
            },
        }
    
    async def get_task_queue_size(self) -> int:
        """获取任务队列大小"""
        return self.task_queue.qsize()
    
    async def clear_task_queue(self):
        """清空任务队列"""
        while not self.task_queue.empty():
            try:
                self.task_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        
        self.task_queue_stats["current_size"] = 0
        logger.info("任务队列已清空")


# 单例工厂函数
_listener_instance: Optional[ERPListener] = None


def get_erp_listener(
    erp_api_url: Optional[str] = None,
    **kwargs
) -> ERPListener:
    """
    获取ERP监听器实例（单例模式）
    
    Args:
        erp_api_url: ERP系统API地址
        **kwargs: 其他配置参数
        
    Returns:
        ERP监听器实例
    """
    global _listener_instance
    
    if _listener_instance is None:
        _listener_instance = ERPListener(
            erp_api_url=erp_api_url,
            **kwargs
        )
    
    return _listener_instance








