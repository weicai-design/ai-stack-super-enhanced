"""
自适应事件总线
Adaptive Event Bus - 智能事件通信系统

功能：
- 跨模块事件发布/订阅
- 自适应路由与负载均衡
- 事件优先级管理
- 故障隔离与重试机制
- 事件审计与监控

版本: 1.0.0
"""

import asyncio
import logging
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventPriority(Enum):
    """事件优先级枚举"""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class DeliveryGuarantee(Enum):
    """投递保证枚举"""

    AT_MOST_ONCE = "at_most_once"  # 至多一次
    AT_LEAST_ONCE = "at_least_once"  # 至少一次
    EXACTLY_ONCE = "exactly_once"  # 精确一次


@dataclass
class Event:
    """事件数据类"""

    id: str
    topic: str
    data: Any
    priority: EventPriority
    timestamp: float
    source: str
    metadata: Dict[str, Any] = None


@dataclass
class Subscription:
    """订阅信息类"""

    id: str
    topic: str
    callback: Callable
    priority: int
    filters: Dict[str, Any] = None
    guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    max_retries: int = 3
    timeout: float = 30.0


class EventMiddleware:
    """事件中间件基类"""

    async def before_publish(self, event: Event) -> Event:
        """发布前处理"""
        return event

    async def after_publish(self, event: Event) -> None:
        """发布后处理"""
        pass

    async def before_deliver(self, event: Event, subscription: Subscription) -> Event:
        """投递前处理"""
        return event

    async def after_deliver(
        self, event: Event, subscription: Subscription, success: bool
    ) -> None:
        """投递后处理"""
        pass


class LoggingMiddleware(EventMiddleware):
    """日志记录中间件"""

    async def before_publish(self, event: Event) -> Event:
        logger.debug(f"发布事件: {event.topic} [{event.id}]")
        return event

    async def after_deliver(
        self, event: Event, subscription: Subscription, success: bool
    ) -> None:
        if success:
            logger.debug(f"事件投递成功: {event.topic} -> {subscription.id}")
        else:
            logger.warning(f"事件投递失败: {event.topic} -> {subscription.id}")


class AdaptiveEventBus:
    """
    自适应事件总线主类
    """

    def __init__(self):
        self.subscriptions: Dict[str, List[Subscription]] = defaultdict(list)
        self.middleware: List[EventMiddleware] = []
        self.event_history: deque = deque(maxlen=1000)  # 事件历史记录
        self.metrics: Dict[str, Any] = {
            "events_published": 0,
            "events_delivered": 0,
            "delivery_errors": 0,
            "topics_active": set(),
        }
        self.is_running: bool = False
        self.retry_queues: Dict[str, asyncio.Queue] = {}
        self.retry_tasks: Dict[str, asyncio.Task] = {}

    async def initialize(self, config: Dict[str, Any] = None) -> None:
        """
        初始化事件总线

        Args:
            config: 事件总线配置
        """
        logger.info("初始化自适应事件总线...")

        # 添加默认中间件
        self.middleware.append(LoggingMiddleware())

        # 初始化重试队列
        self.is_running = True

        logger.info("自适应事件总线初始化完成")

    async def start(self) -> None:
        """启动事件总线"""
        logger.info("启动自适应事件总线")
        self.is_running = True

    async def stop(self) -> None:
        """停止事件总线"""
        logger.info("停止自适应事件总线")
        self.is_running = False

        # 停止所有重试任务
        for task in self.retry_tasks.values():
            task.cancel()

        # 等待任务完成
        for task in self.retry_tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        return {
            "status": "healthy",
            "subscriptions": sum(len(subs) for subs in self.subscriptions.values()),
            "topics": len(self.subscriptions),
            "middleware": len(self.middleware),
            "metrics": self.metrics,
            "retry_queues": len(self.retry_queues),
            "timestamp": time.time(),
        }

    def subscribe(
        self,
        topic: str,
        callback: Callable,
        priority: int = 0,
        filters: Dict[str, Any] = None,
        guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE,
        max_retries: int = 3,
        timeout: float = 30.0,
    ) -> str:
        """
        订阅事件

        Args:
            topic: 事件主题
            callback: 回调函数
            priority: 优先级（数字越大优先级越高）
            filters: 事件过滤器
            guarantee: 投递保证
            max_retries: 最大重试次数
            timeout: 超时时间

        Returns:
            str: 订阅ID
        """
        subscription_id = str(uuid.uuid4())

        subscription = Subscription(
            id=subscription_id,
            topic=topic,
            callback=callback,
            priority=priority,
            filters=filters,
            guarantee=guarantee,
            max_retries=max_retries,
            timeout=timeout,
        )

        # 按优先级插入（保持有序）
        subscriptions = self.subscriptions[topic]
        insert_index = 0
        for i, sub in enumerate(subscriptions):
            if priority > sub.priority:
                insert_index = i + 1
            else:
                break

        subscriptions.insert(insert_index, subscription)
        self.metrics["topics_active"].add(topic)

        logger.info(f"事件订阅创建: {topic} -> {subscription_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """
        取消订阅

        Args:
            subscription_id: 订阅ID

        Returns:
            bool: 取消是否成功
        """
        for topic, subscriptions in self.subscriptions.items():
            for i, subscription in enumerate(subscriptions):
                if subscription.id == subscription_id:
                    subscriptions.pop(i)
                    logger.info(f"事件订阅取消: {topic} -> {subscription_id}")

                    # 清理空主题
                    if not subscriptions:
                        del self.subscriptions[topic]
                        self.metrics["topics_active"].discard(topic)

                    return True

        logger.warning(f"订阅未找到: {subscription_id}")
        return False

    async def publish(
        self,
        topic: str,
        data: Any,
        priority: EventPriority = EventPriority.NORMAL,
        source: str = "unknown",
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        发布事件

        Args:
            topic: 事件主题
            data: 事件数据
            priority: 事件优先级
            source: 事件源
            metadata: 元数据

        Returns:
            str: 事件ID
        """
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            topic=topic,
            data=data,
            priority=priority,
            timestamp=time.time(),
            source=source,
            metadata=metadata or {},
        )

        # 执行中间件前置处理
        for middleware in self.middleware:
            event = await middleware.before_publish(event)

        # 记录事件
        self.event_history.append(event)
        self.metrics["events_published"] += 1

        # 异步投递事件（不阻塞发布者）
        asyncio.create_task(self._deliver_event(event))

        # 执行中间件后置处理
        for middleware in self.middleware:
            await middleware.after_publish(event)

        logger.debug(f"事件发布完成: {topic} [{event_id}]")
        return event_id

    async def _deliver_event(self, event: Event) -> None:
        """
        投递事件给订阅者

        Args:
            event: 事件对象
        """
        if event.topic not in self.subscriptions:
            return

        subscriptions = self.subscriptions[event.topic].copy()

        # 按优先级分组投递
        priority_groups = defaultdict(list)
        for subscription in subscriptions:
            priority_groups[subscription.priority].append(subscription)

        # 从高优先级开始投递
        for priority in sorted(priority_groups.keys(), reverse=True):
            tasks = []
            for subscription in priority_groups[priority]:
                task = asyncio.create_task(
                    self._deliver_to_subscriber(event, subscription)
                )
                tasks.append(task)

            # 等待当前优先级组完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _deliver_to_subscriber(
        self, event: Event, subscription: Subscription
    ) -> None:
        """
        投递事件给单个订阅者

        Args:
            event: 事件对象
            subscription: 订阅信息
        """
        try:
            # 检查事件过滤器
            if not self._matches_filters(event, subscription.filters):
                return

            # 执行中间件前置处理
            delivered_event = event
            for middleware in self.middleware:
                delivered_event = await middleware.before_deliver(
                    delivered_event, subscription
                )

            # 执行回调
            if asyncio.iscoroutinefunction(subscription.callback):
                await asyncio.wait_for(
                    subscription.callback(delivered_event), timeout=subscription.timeout
                )
            else:
                # 同步函数在线程池中执行
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, subscription.callback, delivered_event)

            # 记录成功投递
            self.metrics["events_delivered"] += 1

            # 执行中间件后置处理
            for middleware in self.middleware:
                await middleware.after_deliver(event, subscription, True)

        except asyncio.TimeoutError:
            logger.warning(f"事件投递超时: {event.topic} -> {subscription.id}")
            await self._handle_delivery_error(event, subscription, "timeout")

        except Exception as e:
            logger.error(f"事件投递失败: {event.topic} -> {subscription.id}: {str(e)}")
            await self._handle_delivery_error(event, subscription, str(e))

    async def _handle_delivery_error(
        self, event: Event, subscription: Subscription, error: str
    ) -> None:
        """
        处理投递错误

        Args:
            event: 事件对象
            subscription: 订阅信息
            error: 错误信息
        """
        self.metrics["delivery_errors"] += 1

        # 执行中间件后置处理
        for middleware in self.middleware:
            await middleware.after_deliver(event, subscription, False)

        # 根据投递保证处理重试
        if subscription.guarantee in [
            DeliveryGuarantee.AT_LEAST_ONCE,
            DeliveryGuarantee.EXACTLY_ONCE,
        ]:
            await self._schedule_retry(event, subscription, error)

    async def _schedule_retry(
        self, event: Event, subscription: Subscription, error: str
    ) -> None:
        """
        调度重试

        Args:
            event: 事件对象
            subscription: 订阅信息
            error: 错误信息
        """
        retry_key = f"{subscription.id}_{event.id}"

        if retry_key not in self.retry_queues:
            self.retry_queues[retry_key] = asyncio.Queue()
            self.retry_tasks[retry_key] = asyncio.create_task(
                self._retry_delivery_worker(retry_key, subscription)
            )

        retry_info = {
            "event": event,
            "subscription": subscription,
            "error": error,
            "attempt": 1,
            "max_attempts": subscription.max_retries,
            "next_retry": time.time() + self._calculate_retry_delay(1),
        }

        await self.retry_queues[retry_key].put(retry_info)

    async def _retry_delivery_worker(
        self, retry_key: str, subscription: Subscription
    ) -> None:
        """
        重试投递工作器

        Args:
            retry_key: 重试键
            subscription: 订阅信息
        """
        queue = self.retry_queues[retry_key]

        while self.is_running:
            try:
                retry_info = await asyncio.wait_for(queue.get(), timeout=1.0)

                current_time = time.time()
                if current_time < retry_info["next_retry"]:
                    # 未到重试时间，重新入队
                    await queue.put(retry_info)
                    await asyncio.sleep(0.1)
                    continue

                # 执行重试
                try:
                    await self._deliver_to_subscriber(
                        retry_info["event"], retry_info["subscription"]
                    )
                    # 重试成功，清理
                    queue.task_done()
                    continue

                except Exception as e:
                    retry_info["attempt"] += 1
                    retry_info["error"] = str(e)
                    retry_info["next_retry"] = (
                        time.time() + self._calculate_retry_delay(retry_info["attempt"])
                    )

                    if retry_info["attempt"] <= retry_info["max_attempts"]:
                        # 继续重试
                        await queue.put(retry_info)
                    else:
                        # 重试次数用尽
                        logger.error(
                            f"事件重试失败: {retry_info['event'].topic} -> "
                            f"{subscription.id} (尝试 {retry_info['attempt']-1} 次)"
                        )
                        queue.task_done()

            except asyncio.TimeoutError:
                # 检查队列是否为空且长时间无活动
                if queue.empty():
                    # 清理资源
                    del self.retry_queues[retry_key]
                    self.retry_tasks[retry_key].cancel()
                    del self.retry_tasks[retry_key]
                    break

    def _calculate_retry_delay(self, attempt: int) -> float:
        """
        计算重试延迟（指数退避）

        Args:
            attempt: 重试次数

        Returns:
            float: 延迟时间(秒)
        """
        return min(2**attempt, 60)  # 最大延迟60秒

    def _matches_filters(self, event: Event, filters: Dict[str, Any]) -> bool:
        """
        检查事件是否匹配过滤器

        Args:
            event: 事件对象
            filters: 过滤器字典

        Returns:
            bool: 是否匹配
        """
        if not filters:
            return True

        for key, expected_value in filters.items():
            # 支持嵌套字段访问 (如: metadata.user_id)
            if "." in key:
                parts = key.split(".")
                current_value = event
                for part in parts:
                    if hasattr(current_value, part):
                        current_value = getattr(current_value, part)
                    elif isinstance(current_value, dict) and part in current_value:
                        current_value = current_value[part]
                    else:
                        current_value = None
                        break
            else:
                if hasattr(event, key):
                    current_value = getattr(event, key)
                else:
                    current_value = None

            if current_value != expected_value:
                return False

        return True

    def add_middleware(self, middleware: EventMiddleware) -> None:
        """
        添加中间件

        Args:
            middleware: 事件中间件
        """
        self.middleware.append(middleware)
        logger.info(f"事件中间件添加: {middleware.__class__.__name__}")

    def remove_middleware(self, middleware_class: type) -> bool:
        """
        移除中间件

        Args:
            middleware_class: 中间件类

        Returns:
            bool: 移除是否成功
        """
        for i, middleware in enumerate(self.middleware):
            if isinstance(middleware, middleware_class):
                self.middleware.pop(i)
                logger.info(f"事件中间件移除: {middleware_class.__name__}")
                return True

        return False

    def get_subscription_info(self, topic: str = None) -> Dict[str, Any]:
        """
        获取订阅信息

        Args:
            topic: 主题名称，None表示所有主题

        Returns:
            Dict[str, Any]: 订阅信息
        """
        if topic:
            subscriptions = self.subscriptions.get(topic, [])
            return {
                "topic": topic,
                "subscriptions": [
                    {
                        "id": sub.id,
                        "priority": sub.priority,
                        "guarantee": sub.guarantee.value,
                        "max_retries": sub.max_retries,
                        "timeout": sub.timeout,
                    }
                    for sub in subscriptions
                ],
            }
        else:
            return {
                "topics": {
                    topic: [
                        {
                            "id": sub.id,
                            "priority": sub.priority,
                            "guarantee": sub.guarantee.value,
                            "max_retries": sub.max_retries,
                            "timeout": sub.timeout,
                        }
                        for sub in subscriptions
                    ]
                    for topic, subscriptions in self.subscriptions.items()
                }
            }

    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取事件历史

        Args:
            limit: 返回数量限制

        Returns:
            List[Dict[str, Any]]: 事件历史列表
        """
        history = list(self.event_history)[-limit:]
        return [
            {
                "id": event.id,
                "topic": event.topic,
                "priority": event.priority.value,
                "timestamp": event.timestamp,
                "source": event.source,
            }
            for event in reversed(history)
        ]


# 导出类
__all__ = [
    "AdaptiveEventBus",
    "Event",
    "EventPriority",
    "DeliveryGuarantee",
    "EventMiddleware",
]
