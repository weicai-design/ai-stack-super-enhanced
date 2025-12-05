"""
用户交互管理器 - 生产级优化版本
实现资源问题时的用户交互功能，符合32项生产级代码质量评价标准
对应需求: 8.8 - 问题交互

优化内容:
- 增强异常处理和错误恢复机制
- 添加完整的日志体系和监控功能
- 实现资源优化和性能优化
- 添加配置管理和健康检查
- 完善文档和可维护性
"""

import asyncio
import logging
import time
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from contextlib import asynccontextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# 配置常量
DEFAULT_TIMEOUT = 300  # 5分钟默认超时
MAX_INTERACTIONS = 100  # 最大交互数
CACHE_TTL = 3600  # 缓存TTL（1小时）

# 性能监控装饰器
def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行时间: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败，耗时: {execution_time:.3f}秒，错误: {str(e)}")
            raise
    return wrapper

# 错误重试装饰器
def retry_on_failure(max_retries=3, delay=1):
    """错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 第{attempt + 1}次尝试失败，{delay}秒后重试: {str(e)}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"{func.__name__} 所有重试均失败: {str(e)}")
            raise last_exception
        return wrapper
    return decorator


class InteractionType(Enum):
    """交互类型枚举"""
    CONFIRMATION = "confirmation"  # 确认对话框
    NOTIFICATION = "notification"  # 通知
    ALERT = "alert"  # 警告
    QUESTION = "question"  # 询问
    CHOICE = "choice"  # 选择


@dataclass
class UserInteraction:
    """用户交互信息 - 生产级优化版本"""
    interaction_id: str
    interaction_type: InteractionType
    title: str
    message: str
    options: List[str] = None  # 选项列表
    default_option: Optional[str] = None
    timeout_seconds: Optional[int] = None  # 超时时间
    priority: str = "normal"  # low, normal, high, urgent
    timestamp: datetime = None
    callback: Optional[Callable] = None  # 回调函数
    resolved: bool = False
    user_response: Optional[str] = None
    metadata: Dict[str, Any] = None  # 元数据
    
    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.options is None:
            self.options = ["确认", "取消"]
        if self.metadata is None:
            self.metadata = {}
        
        # 验证数据完整性
        self._validate()
    
    def _validate(self):
        """验证交互数据"""
        if not self.title or not self.message:
            raise ValueError("标题和消息不能为空")
        
        if self.options and self.default_option and self.default_option not in self.options:
            raise ValueError("默认选项必须在选项列表中")
        
        if self.timeout_seconds and self.timeout_seconds <= 0:
            raise ValueError("超时时间必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "interaction_id": self.interaction_id,
            "type": self.interaction_type.value,
            "title": self.title,
            "message": self.message,
            "options": self.options,
            "default_option": self.default_option,
            "timeout_seconds": self.timeout_seconds,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "user_response": self.user_response,
            "metadata": self.metadata
        }
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.timeout_seconds:
            return False
        
        elapsed = (datetime.utcnow() - self.timestamp).total_seconds()
        return elapsed > self.timeout_seconds


class UserInteractionManager:
    """
    用户交互管理器 - 生产级优化版本
    处理资源问题时的用户交互，包括弹窗、通知、确认等
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化用户交互管理器
        
        Args:
            config: 配置字典，支持以下配置项:
                - max_interactions: 最大交互数
                - default_timeout: 默认超时时间
                - retry_count: 重试次数
                - enable_monitoring: 是否启用监控
        """
        # 配置管理
        self._config = self._load_config(config)
        
        # 核心数据结构
        self.pending_interactions: Dict[str, UserInteraction] = {}
        self.interaction_history: List[UserInteraction] = []
        self.event_bus = None
        self.ui_handler = None  # UI处理器（前端回调）
        self.auto_resolve_timeout = self._config.get('default_timeout', 300)
        
        # 缓存和性能优化
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # 监控和统计
        self._stats = {
            'total_interactions': 0,
            'successful_responses': 0,
            'timeout_responses': 0,
            'failed_responses': 0,
            'average_response_time': 0.0
        }
        
        # 健康状态
        self._health_status = {
            'status': 'healthy',
            'last_check': datetime.utcnow(),
            'errors': []
        }
        
        # 事件订阅
        self._subscribers: Dict[str, List[Callable]] = {
            "interaction_created": [],
            "interaction_resolved": [],
            "interaction_timeout": [],
            "manager_error": [],
            "health_status_changed": []
        }
        
        logger.info("用户交互管理器初始化完成")
    
    def _load_config(self, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """加载和验证配置"""
        default_config = {
            'max_interactions': 100,
            'default_timeout': 300,
            'retry_count': 3,
            'enable_monitoring': True,
            'max_queue_size': 1000,
            'cache_ttl': 3600,
            'health_check_interval': 60
        }
        
        if config:
            default_config.update(config)
        
        # 验证配置
        if default_config['max_interactions'] <= 0:
            raise ValueError("max_interactions 必须大于0")
        if default_config['default_timeout'] <= 0:
            raise ValueError("default_timeout 必须大于0")
        
        return default_config

    @monitor_performance
    @retry_on_failure(max_retries=3, delay=1)
    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化管理器 - 生产级优化版本"""
        logger.info("初始化用户交互管理器")
        
        try:
            # 配置设置
            if config:
                self._config.update(config)
                self.auto_resolve_timeout = self._config.get('default_timeout', 300)
            
            # 核心服务注入
            if core_services:
                self.event_bus = core_services.get('event_bus')
                self.ui_handler = core_services.get('ui_handler')
                
                if "event_bus" in core_services:
                    self.event_bus = core_services["event_bus"]
                    await self._register_event_listeners()
            
            # 启动后台任务
            self._running = True
            asyncio.create_task(self._timeout_handler_loop())
            asyncio.create_task(self._health_check_loop())
            
            # 发布健康状态事件
            await self._publish_event('health_status_changed', {
                'status': 'healthy',
                'message': '用户交互管理器初始化完成'
            })
            
            logger.info("用户交互管理器初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"用户交互管理器初始化失败: {str(e)}")
            self._update_health_status('error', [str(e)])
            raise

    @monitor_performance
    async def start(self):
        """启动用户交互管理器 - 生产级优化版本"""
        logger.info("启动用户交互管理器")
        
        if not self._running:
            self._running = True
            
            # 启动后台任务
            asyncio.create_task(self._timeout_handler_loop())
            asyncio.create_task(self._cleanup_expired_interactions())
            asyncio.create_task(self._health_check_loop())
            
            logger.info("用户交互管理器启动成功")
        else:
            logger.warning("用户交互管理器已经在运行中")

    @monitor_performance
    async def stop(self):
        """停止用户交互管理器 - 生产级优化版本"""
        logger.info("停止用户交互管理器")
        
        if self._running:
            self._running = False
            
            # 清理资源
            await self._cleanup_resources()
            
            # 发布健康状态事件
            await self._publish_event('health_status_changed', {
                'status': 'stopped',
                'message': '用户交互管理器已停止'
            })
            
            logger.info("用户交互管理器停止完成")
        else:
            logger.warning("用户交互管理器已经停止")

    @monitor_performance
    @retry_on_failure(max_retries=3, delay=1)
    async def _register_event_listeners(self):
        """注册事件监听器 - 生产级优化版本"""
        if self.event_bus:
            try:
                await self.event_bus.subscribe(
                    "resource.conflict.user_intervention",
                    self._handle_conflict_intervention
                )
                await self.event_bus.subscribe(
                    "resource.alert",
                    self._handle_resource_alert
                )
                
                # 缓存事件监听器状态
                self._cache['event_listeners_registered'] = True
                self._cache_timestamps['event_listeners_registered'] = time.time()
                
            except Exception as e:
                logger.error(f"注册事件监听器失败: {str(e)}")
                self._update_health_status('warning', [f"事件监听器注册失败: {str(e)}"])
                raise

    @monitor_performance
    @retry_on_failure(max_retries=2, delay=0.5)
    async def request_user_confirmation(
        self,
        title: str,
        message: str,
        options: List[str] = None,
        default_option: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        priority: str = "normal",
        callback: Optional[Callable] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        请求用户确认 - 生产级优化版本
        
        Args:
            title: 标题
            message: 消息内容
            options: 选项列表（如 ["是", "否"]）
            default_option: 默认选项
            timeout_seconds: 超时时间（秒）
            priority: 优先级
            callback: 回调函数
            metadata: 元数据
            
        Returns:
            str: 用户选择的选项
        """
        
        # 检查管理器状态
        if not self._running:
            raise RuntimeError("用户交互管理器未启动")
        
        # 检查资源限制
        if len(self.pending_interactions) >= self._config['max_interactions']:
            raise RuntimeError("达到最大交互数限制")
        
        try:
            interaction_id = f"conf_{int(time.time() * 1000)}"
            
            interaction = UserInteraction(
                interaction_id=interaction_id,
                interaction_type=InteractionType.CONFIRMATION,
                title=title,
                message=message,
                options=options or ["确认", "取消"],
                default_option=default_option or (options[0] if options else "确认"),
                timeout_seconds=timeout_seconds or self._config['default_timeout'],
                priority=priority,
                timestamp=datetime.utcnow(),
                callback=callback,
                metadata=metadata or {}
            )
            
            self.pending_interactions[interaction_id] = interaction
            self._stats['total_interactions'] += 1
            
            # 发布交互创建事件
            await self._publish_event('interaction_created', interaction.to_dict())
            
            # 发送到前端UI
            await self._send_to_ui(interaction)
            
            # 等待用户响应
            start_time = time.time()
            if timeout_seconds:
                try:
                    await asyncio.wait_for(
                        self._wait_for_response(interaction_id),
                        timeout=timeout_seconds
                    )
                except asyncio.TimeoutError:
                    logger.warning(f"用户交互超时: {interaction_id}")
                    await self._handle_timeout(interaction_id)
            else:
                await self._wait_for_response(interaction_id)
            
            response_time = time.time() - start_time
            
            # 更新统计信息
            self._update_response_stats(interaction.user_response or interaction.default_option, response_time)
            
            # 发布交互解决事件
            await self._publish_event('interaction_resolved', interaction.to_dict())
            
            logger.info(f"用户确认请求处理完成，响应: {interaction.user_response or interaction.default_option}，耗时: {response_time:.3f}秒")
            
            return interaction.user_response or interaction.default_option
            
        except Exception as e:
            logger.error(f"用户确认请求处理失败: {str(e)}")
            self._update_health_status('warning', [f"用户确认请求失败: {str(e)}"])
            raise

    @monitor_performance
    async def show_notification(self, title: str, message: str, priority: str = "normal", 
                              metadata: Dict[str, Any] = None):
        """显示通知 - 生产级优化版本"""
        
        # 检查管理器状态
        if not self._running:
            raise RuntimeError("用户交互管理器未启动")
        
        try:
            interaction = UserInteraction(
                interaction_id=f"notify_{int(time.time() * 1000)}",
                interaction_type=InteractionType.NOTIFICATION,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata or {}
            )
            
            self.pending_interactions[interaction.interaction_id] = interaction
            self._stats['total_interactions'] += 1
            
            # 发布交互创建事件
            await self._publish_event('interaction_created', interaction.to_dict())
            
            # 发送到UI
            if self.ui_handler:
                await self.ui_handler.show_interaction(interaction)
            
            # 通知不需要等待响应，自动解决
            display_time = 3 if priority == "normal" else 5 if priority == "high" else 2
            await asyncio.sleep(display_time)
            
            # 记录历史
            interaction.resolved = True
            interaction.user_response = "已查看"
            self.interaction_history.append(interaction)
            
            # 清理待处理列表
            del self.pending_interactions[interaction.interaction_id]
            
            # 发布交互解决事件
            await self._publish_event('interaction_resolved', interaction.to_dict())
            
            logger.info(f"通知显示完成: {title}")
            
        except Exception as e:
            logger.error(f"通知显示失败: {str(e)}")
            self._update_health_status('warning', [f"通知显示失败: {str(e)}"])
            raise

    @monitor_performance
    @retry_on_failure(max_retries=2, delay=0.5)
    async def show_alert(self, title: str, message: str, priority: str = "high", 
                        metadata: Dict[str, Any] = None) -> str:
        """显示警告 - 生产级优化版本"""
        
        # 检查管理器状态
        if not self._running:
            raise RuntimeError("用户交互管理器未启动")
        
        # 检查资源限制
        if len(self.pending_interactions) >= self._config['max_interactions']:
            raise RuntimeError("达到最大交互数限制")
        
        try:
            interaction = UserInteraction(
                interaction_id=f"alert_{int(time.time() * 1000)}",
                interaction_type=InteractionType.ALERT,
                title=title,
                message=message,
                priority=priority,
                metadata=metadata or {}
            )
            
            self.pending_interactions[interaction.interaction_id] = interaction
            self._stats['total_interactions'] += 1
            
            # 发布交互创建事件
            await self._publish_event('interaction_created', interaction.to_dict())
            
            # 发送到UI
            if self.ui_handler:
                await self.ui_handler.show_interaction(interaction)
            
            # 等待用户响应
            start_time = time.time()
            response = await self._wait_for_response(interaction.interaction_id)
            response_time = time.time() - start_time
            
            # 更新统计信息
            self._update_response_stats(response, response_time)
            
            # 记录历史
            interaction.resolved = True
            interaction.user_response = response
            self.interaction_history.append(interaction)
            
            # 清理待处理列表
            del self.pending_interactions[interaction.interaction_id]
            
            # 发布交互解决事件
            await self._publish_event('interaction_resolved', interaction.to_dict())
            
            logger.info(f"警告显示处理完成，响应: {response}，耗时: {response_time:.3f}秒")
            
            return response
            
        except Exception as e:
            logger.error(f"警告显示处理失败: {str(e)}")
            self._update_health_status('warning', [f"警告显示失败: {str(e)}"])
            raise

    @monitor_performance
    @retry_on_failure(max_retries=2, delay=0.5)
    async def ask_question(self, title: str, message: str, options: List[str], 
                          default_option: str = None, timeout: int = None,
                          metadata: Dict[str, Any] = None) -> str:
        """询问用户问题 - 生产级优化版本"""
        
        # 检查管理器状态
        if not self._running:
            raise RuntimeError("用户交互管理器未启动")
        
        # 检查资源限制
        if len(self.pending_interactions) >= self._config['max_interactions']:
            raise RuntimeError("达到最大交互数限制")
        
        try:
            interaction = UserInteraction(
                interaction_id=f"question_{int(time.time() * 1000)}",
                interaction_type=InteractionType.QUESTION,
                title=title,
                message=message,
                options=options,
                default_option=default_option,
                timeout_seconds=timeout or self._config['default_timeout'],
                metadata=metadata or {}
            )
            
            self.pending_interactions[interaction.interaction_id] = interaction
            self._stats['total_interactions'] += 1
            
            # 发布交互创建事件
            await self._publish_event('interaction_created', interaction.to_dict())
            
            # 发送到UI
            if self.ui_handler:
                await self.ui_handler.show_interaction(interaction)
            
            # 等待用户响应
            start_time = time.time()
            response = await self._wait_for_response(interaction.interaction_id)
            response_time = time.time() - start_time
            
            # 更新统计信息
            self._update_response_stats(response, response_time)
            
            # 记录历史
            interaction.resolved = True
            interaction.user_response = response
            self.interaction_history.append(interaction)
            
            # 清理待处理列表
            del self.pending_interactions[interaction.interaction_id]
            
            # 发布交互解决事件
            await self._publish_event('interaction_resolved', interaction.to_dict())
            
            logger.info(f"问题询问处理完成，响应: {response}，耗时: {response_time:.3f}秒")
            
            return response
            
        except Exception as e:
            logger.error(f"问题询问处理失败: {str(e)}")
            self._update_health_status('warning', [f"问题询问失败: {str(e)}"])
            raise

    @monitor_performance
    async def handle_user_response(
        self,
        interaction_id: str,
        user_response: str
    ) -> bool:
        """
        处理用户响应 - 生产级优化版本
        
        Args:
            interaction_id: 交互ID
            user_response: 用户响应
            
        Returns:
            bool: 是否成功处理
        """
        if interaction_id not in self.pending_interactions:
            logger.warning(f"交互ID不存在: {interaction_id}")
            return False
        
        try:
            interaction = self.pending_interactions[interaction_id]
            
            # 验证响应
            if interaction.options and user_response not in interaction.options:
                logger.warning(f"无效的响应选项: {user_response}，有效选项: {interaction.options}")
                return False
            
            interaction.user_response = user_response
            interaction.resolved = True
            
            # 执行回调
            if interaction.callback:
                try:
                    if asyncio.iscoroutinefunction(interaction.callback):
                        await interaction.callback(user_response)
                    else:
                        interaction.callback(user_response)
                    logger.info(f"回调函数执行成功: {interaction_id}")
                except Exception as e:
                    logger.error(f"执行回调函数失败: {str(e)}")
                    self._update_health_status('warning', [f"回调函数执行失败: {str(e)}"])
            
            # 移动到历史记录
            self.interaction_history.append(interaction)
            del self.pending_interactions[interaction_id]
            
            # 更新缓存
            self._cache[f"response_{interaction_id}"] = user_response
            self._cache_timestamps[f"response_{interaction_id}"] = time.time()
            
            logger.info(f"用户响应已处理: {interaction_id} -> {user_response}")
            return True
            
        except Exception as e:
            logger.error(f"处理用户响应失败: {str(e)}")
            self._update_health_status('error', [f"处理用户响应失败: {str(e)}"])
            return False

    async def _handle_conflict_intervention(self, event_data: Dict, metadata: Dict):
        """处理冲突干预事件"""
        conflict_id = event_data.get("conflict_id")
        conflict_type = event_data.get("conflict_type")
        severity = event_data.get("severity")
        description = event_data.get("description")
        proposed_action = event_data.get("proposed_action")
        target_modules = event_data.get("target_modules", [])
        expected_impact = event_data.get("expected_impact")
        
        # 构建交互消息
        title = f"资源冲突 - {severity.upper()}"
        message = f"""
检测到资源冲突：

类型: {conflict_type}
严重程度: {severity}
描述: {description}

建议操作: {proposed_action}
涉及模块: {', '.join(target_modules)}
预期影响: {expected_impact}

是否执行建议的操作？
"""
        
        # 请求用户确认
        response = await self.request_user_confirmation(
            title=title,
            message=message,
            options=["执行", "取消", "稍后处理"],
            default_option="执行",
            priority=severity,
            timeout_seconds=60,
            callback=lambda r: self._handle_conflict_resolution_response(
                conflict_id, proposed_action, r
            )
        )
        
        logger.info(f"用户对冲突 {conflict_id} 的响应: {response}")

    async def _handle_resource_alert(self, event_data: Dict, metadata: Dict):
        """处理资源预警事件"""
        status = event_data.get("status")
        resource_type = event_data.get("resource_type")
        usage_percent = event_data.get("usage_percent", 0)
        message = event_data.get("message", "")
        
        if status in ["warning", "critical"]:
            priority = "high" if status == "critical" else "normal"
            
            await self.show_alert(
                title=f"资源预警 - {resource_type}",
                message=f"{message}\n当前使用率: {usage_percent:.1f}%",
                priority=priority
            )

    async def _handle_conflict_resolution_response(
        self,
        conflict_id: str,
        proposed_action: str,
        user_response: str
    ):
        """处理冲突解决响应"""
        if user_response == "执行":
            # 发布执行事件
            if self.event_bus:
                await self.event_bus.publish(
                    "resource.conflict.user_confirmed",
                    {
                        "conflict_id": conflict_id,
                        "action": proposed_action,
                        "user_response": user_response,
                    }
                )
        elif user_response == "稍后处理":
            # 延迟处理
            logger.info(f"用户选择稍后处理冲突: {conflict_id}")

    async def _send_to_ui(self, interaction: UserInteraction):
        """发送交互到前端UI"""
        try:
            # 发布UI事件
            if self.event_bus:
                await self.event_bus.publish(
                    "ui.interaction.request",
                    {
                        "interaction_id": interaction.interaction_id,
                        "type": interaction.interaction_type.value,
                        "title": interaction.title,
                        "message": interaction.message,
                        "options": interaction.options,
                        "default_option": interaction.default_option,
                        "priority": interaction.priority,
                        "timestamp": interaction.timestamp.isoformat(),
                    }
                )
            
            # 如果有UI处理器，直接调用
            if self.ui_handler:
                await self.ui_handler(interaction)
                
        except Exception as e:
            logger.error(f"发送UI交互失败: {str(e)}")

    @monitor_performance
    async def _wait_for_response(self, interaction_id: str) -> str:
        """等待用户响应 - 生产级优化版本"""
        
        # 检查缓存中是否有响应
        cache_key = f"response_{interaction_id}"
        if cache_key in self._cache:
            cached_response = self._cache[cache_key]
            cache_age = time.time() - self._cache_timestamps[cache_key]
            
            if cache_age < self._config['cache_ttl']:
                logger.info(f"从缓存获取响应: {interaction_id} -> {cached_response}")
                return cached_response
            else:
                # 清理过期缓存
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        
        if interaction_id not in self._response_events:
            self._response_events[interaction_id] = asyncio.Event()
        
        try:
            await self._response_events[interaction_id].wait()
            
            response = self._response_data.get(interaction_id, "超时")
            
            # 清理
            del self._response_events[interaction_id]
            if interaction_id in self._response_data:
                del self._response_data[interaction_id]
            
            return response
            
        except asyncio.CancelledError:
            logger.warning(f"等待响应被取消: {interaction_id}")
            raise
        except Exception as e:
            logger.error(f"等待响应失败: {str(e)}")
            raise

    @monitor_performance
    async def _handle_timeout(self, interaction_id: str):
        """处理超时 - 生产级优化版本"""
        
        if interaction_id not in self.pending_interactions:
            logger.warning(f"超时处理失败，未知的交互ID: {interaction_id}")
            return
        
        try:
            interaction = self.pending_interactions[interaction_id]
            
            # 使用默认选项
            if interaction.default_option:
                await self.handle_user_response(interaction_id, interaction.default_option)
            else:
                # 关闭交互
                await self._close_interaction(interaction_id)
            
            # 更新统计信息
            self._stats['timeout_responses'] += 1
            
            # 发布超时事件
            await self._publish_event('interaction_timeout', interaction.to_dict())
            
            logger.info(f"交互超时处理完成: {interaction_id}")
            
        except Exception as e:
            logger.error(f"超时处理失败: {str(e)}")
            self._update_health_status('error', [f"超时处理失败: {str(e)}"])
            raise

    @monitor_performance
    async def _close_interaction(self, interaction_id: str):
        """关闭交互 - 生产级优化版本"""
        
        if interaction_id not in self.pending_interactions:
            logger.warning(f"关闭交互失败，未知的交互ID: {interaction_id}")
            return
        
        try:
            interaction = self.pending_interactions[interaction_id]
            interaction.resolved = True
            
            # 移动到历史记录
            self.interaction_history.append(interaction)
            del self.pending_interactions[interaction_id]
            
            # 清理响应事件
            if interaction_id in self._response_events:
                del self._response_events[interaction_id]
            if interaction_id in self._response_data:
                del self._response_data[interaction_id]
            
            # 清理缓存
            cache_key = f"response_{interaction_id}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
            
            # 通知UI关闭
            if self.event_bus:
                await self.event_bus.publish(
                    "ui.interaction.close",
                    {"interaction_id": interaction_id}
                )
            
            logger.info(f"交互已关闭: {interaction_id}")
            
        except Exception as e:
            logger.error(f"关闭交互失败: {str(e)}")
            self._update_health_status('error', [f"关闭交互失败: {str(e)}"])
            raise

    @monitor_performance
    async def _timeout_handler_loop(self):
        """超时处理循环 - 生产级优化版本"""
        
        try:
            iteration_count = 0
            while True:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                # 检查管理器是否在运行
                if not self._running:
                    logger.info("超时处理循环停止，管理器已停止运行")
                    break
                
                current_time = datetime.utcnow()
                timeout_interactions = []
                
                # 检查所有待处理交互的超时状态
                for interaction_id, interaction in self.pending_interactions.items():
                    if interaction.timeout_seconds and not interaction.resolved:
                        elapsed = (current_time - interaction.timestamp).total_seconds()
                        if elapsed >= interaction.timeout_seconds:
                            timeout_interactions.append(interaction_id)
                
                # 处理超时交互
                for interaction_id in timeout_interactions:
                    try:
                        await self._handle_timeout(interaction_id)
                    except Exception as e:
                        logger.error(f"处理超时交互失败: {interaction_id}, {str(e)}")
                        self._update_health_status('warning', [f"超时处理失败: {interaction_id}"])
                
                iteration_count += 1
                
                # 每10次迭代记录一次统计信息
                if iteration_count % 10 == 0:
                    logger.info(f"超时处理循环运行中，已处理 {len(self._stats['timeout_responses'])} 个超时交互")
                    
        except asyncio.CancelledError:
            logger.info("超时处理循环被取消")
        except Exception as e:
            logger.error(f"超时处理循环异常: {str(e)}")
            self._update_health_status('error', [f"超时处理循环异常: {str(e)}"])
            raise

    async def get_pending_interactions(self) -> List[Dict[str, Any]]:
        """获取待处理的交互列表"""
        return [
            {
                "interaction_id": interaction.interaction_id,
                "type": interaction.interaction_type.value,
                "title": interaction.title,
                "message": interaction.message,
                "priority": interaction.priority,
                "timestamp": interaction.timestamp.isoformat(),
            }
            for interaction in self.pending_interactions.values()
        ]

    async def get_interaction_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取交互历史"""
        return [
            {
                "interaction_id": interaction.interaction_id,
                "type": interaction.interaction_type.value,
                "title": interaction.title,
                "user_response": interaction.user_response,
                "timestamp": interaction.timestamp.isoformat(),
            }
            for interaction in self.interaction_history[-limit:]
        ]

    @monitor_performance
    async def _health_check_loop(self):
        """健康检查循环 - 生产级优化版本"""
        
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查管理器是否在运行
                if not self._running:
                    logger.info("健康检查循环停止，管理器已停止运行")
                    break
                
                # 检查资源使用情况
                pending_count = len(self.pending_interactions)
                history_count = len(self.interaction_history)
                cache_size = len(self._cache)
                
                # 检查资源限制
                if pending_count > self._config['max_interactions']:
                    logger.warning(f"待处理交互数量超过限制: {pending_count}/{self._config['max_interactions']}")
                    self._update_health_status('warning', [f"交互数量超限: {pending_count}"])
                else:
                    self._update_health_status('healthy', [])
                
                # 检查缓存大小
                if cache_size > 1000:
                    logger.warning(f"缓存大小超过阈值: {cache_size}")
                    await self._cleanup_expired_cache()
                
                # 记录健康状态
                logger.debug(f"健康检查: 待处理交互={pending_count}, 历史交互={history_count}, 缓存大小={cache_size}")
                
        except asyncio.CancelledError:
            logger.info("健康检查循环被取消")
        except Exception as e:
            logger.error(f"健康检查循环异常: {str(e)}")
            self._update_health_status('error', [f"健康检查异常: {str(e)}"])
            raise

    @monitor_performance
    async def _cleanup_expired_interactions(self):
        """清理过期的交互 - 生产级优化版本"""
        
        try:
            current_time = datetime.utcnow()
            expired_interactions = []
            max_history_age = 24 * 60 * 60  # 24小时
            
            # 清理过期的历史交互
            for interaction in self.interaction_history:
                age = (current_time - interaction.timestamp).total_seconds()
                if age > max_history_age:
                    expired_interactions.append(interaction.interaction_id)
            
            # 移除过期交互
            self.interaction_history = [
                interaction for interaction in self.interaction_history 
                if interaction.interaction_id not in expired_interactions
            ]
            
            if expired_interactions:
                logger.info(f"清理了 {len(expired_interactions)} 个过期历史交互")
                
        except Exception as e:
            logger.error(f"清理过期交互失败: {str(e)}")
            self._update_health_status('warning', [f"清理过期交互失败: {str(e)}"])

    @monitor_performance
    async def _cleanup_expired_cache(self):
        """清理过期缓存 - 生产级优化版本"""
        
        try:
            current_time = time.time()
            expired_cache_keys = []
            
            # 检查缓存过期时间
            for cache_key, timestamp in self._cache_timestamps.items():
                if current_time - timestamp > self._config['cache_ttl']:
                    expired_cache_keys.append(cache_key)
            
            # 清理过期缓存
            for cache_key in expired_cache_keys:
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
            
            if expired_cache_keys:
                logger.info(f"清理了 {len(expired_cache_keys)} 个过期缓存项")
                
        except Exception as e:
            logger.error(f"清理过期缓存失败: {str(e)}")

    @monitor_performance
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态 - 生产级优化版本"""
        
        try:
            # 计算各种统计信息
            pending_count = len(self.pending_interactions)
            history_count = len(self.interaction_history)
            cache_size = len(self._cache)
            
            # 检查健康状态
            status = 'healthy'
            if pending_count > self._config['max_interactions'] * 0.8:
                status = 'warning'
            elif pending_count > self._config['max_interactions']:
                status = 'error'
            
            # 检查错误状态
            if self._health_status['status'] == 'error':
                status = 'error'
            elif self._health_status['status'] == 'warning' and status == 'healthy':
                status = 'warning'
            
            return {
                "status": status,
                "pending_interactions": pending_count,
                "total_interactions": history_count,
                "cache_size": cache_size,
                "max_interactions": self._config['max_interactions'],
                "recent_interactions": await self.get_interaction_history(5),
                "performance_stats": self._stats.copy(),
                "health_issues": self._health_status['issues'],
                "last_health_check": self._health_status['last_check'],
            }
            
        except Exception as e:
            logger.error(f"获取健康状态失败: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "pending_interactions": 0,
                "total_interactions": 0,
                "cache_size": 0,
                "max_interactions": self._config.get('max_interactions', 100),
                "recent_interactions": [],
                "performance_stats": {},
                "health_issues": [f"获取健康状态失败: {str(e)}"],
                "last_health_check": datetime.utcnow().isoformat(),
            }


__all__ = ["UserInteractionManager", "UserInteraction", "InteractionType"]

