"""
用户交互管理器
实现资源问题时的用户交互功能
对应需求: 8.8 - 问题交互
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    """交互类型枚举"""
    CONFIRMATION = "confirmation"  # 确认对话框
    NOTIFICATION = "notification"  # 通知
    ALERT = "alert"  # 警告
    QUESTION = "question"  # 询问
    CHOICE = "choice"  # 选择


@dataclass
class UserInteraction:
    """用户交互信息"""
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


class UserInteractionManager:
    """
    用户交互管理器
    处理资源问题时的用户交互，包括弹窗、通知、确认等
    """

    def __init__(self):
        self.pending_interactions: Dict[str, UserInteraction] = {}
        self.interaction_history: List[UserInteraction] = []
        self.event_bus = None
        self.ui_handler = None  # UI处理器（前端回调）
        self.auto_resolve_timeout = 300  # 5分钟自动解决

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化用户交互管理器"""
        self.config = config or {}
        self.core_services = core_services or {}
        
        if "event_bus" in self.core_services:
            self.event_bus = self.core_services["event_bus"]
            await self._register_event_listeners()
        
        if "auto_resolve_timeout" in self.config:
            self.auto_resolve_timeout = self.config["auto_resolve_timeout"]
        
        logger.info("用户交互管理器初始化完成")

    async def start(self):
        """启动用户交互管理器"""
        # 启动超时处理任务
        asyncio.create_task(self._timeout_handler_loop())
        logger.info("用户交互管理器已启动")

    async def stop(self):
        """停止用户交互管理器"""
        logger.info("用户交互管理器已停止")

    async def _register_event_listeners(self):
        """注册事件监听器"""
        if self.event_bus:
            await self.event_bus.subscribe(
                "resource.conflict.user_intervention",
                self._handle_conflict_intervention
            )
            await self.event_bus.subscribe(
                "resource.alert",
                self._handle_resource_alert
            )

    async def request_user_confirmation(
        self,
        title: str,
        message: str,
        options: List[str] = None,
        default_option: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        priority: str = "normal",
        callback: Optional[Callable] = None
    ) -> str:
        """
        请求用户确认
        
        Args:
            title: 标题
            message: 消息内容
            options: 选项列表（如 ["是", "否"]）
            default_option: 默认选项
            timeout_seconds: 超时时间（秒）
            priority: 优先级
            callback: 回调函数
            
        Returns:
            str: 用户选择的选项
        """
        interaction_id = f"interaction_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            interaction_type=InteractionType.CONFIRMATION,
            title=title,
            message=message,
            options=options or ["确认", "取消"],
            default_option=default_option or (options[0] if options else "确认"),
            timeout_seconds=timeout_seconds,
            priority=priority,
            timestamp=datetime.utcnow(),
            callback=callback,
        )
        
        self.pending_interactions[interaction_id] = interaction
        
        # 发送到前端UI
        await self._send_to_ui(interaction)
        
        # 等待用户响应
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
        
        return interaction.user_response or interaction.default_option

    async def show_notification(
        self,
        title: str,
        message: str,
        priority: str = "normal",
        duration_seconds: int = 5
    ):
        """显示通知"""
        interaction_id = f"notification_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            interaction_type=InteractionType.NOTIFICATION,
            title=title,
            message=message,
            priority=priority,
            timestamp=datetime.utcnow(),
        )
        
        # 发送到前端UI
        await self._send_to_ui(interaction)
        
        # 自动关闭
        if duration_seconds > 0:
            await asyncio.sleep(duration_seconds)
            await self._close_interaction(interaction_id)

    async def show_alert(
        self,
        title: str,
        message: str,
        priority: str = "high",
        callback: Optional[Callable] = None
    ):
        """显示警告"""
        interaction_id = f"alert_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            interaction_type=InteractionType.ALERT,
            title=title,
            message=message,
            priority=priority,
            timestamp=datetime.utcnow(),
            callback=callback,
        )
        
        self.pending_interactions[interaction_id] = interaction
        
        # 发送到前端UI
        await self._send_to_ui(interaction)

    async def ask_question(
        self,
        title: str,
        question: str,
        options: List[str],
        default_option: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """询问用户问题"""
        interaction_id = f"question_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
        
        interaction = UserInteraction(
            interaction_id=interaction_id,
            interaction_type=InteractionType.QUESTION,
            title=title,
            message=question,
            options=options,
            default_option=default_option or (options[0] if options else None),
            timeout_seconds=timeout_seconds,
            timestamp=datetime.utcnow(),
            callback=callback,
        )
        
        self.pending_interactions[interaction_id] = interaction
        
        # 发送到前端UI
        await self._send_to_ui(interaction)
        
        # 等待用户响应
        if timeout_seconds:
            try:
                await asyncio.wait_for(
                    self._wait_for_response(interaction_id),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                await self._handle_timeout(interaction_id)
        else:
            await self._wait_for_response(interaction_id)
        
        return interaction.user_response or interaction.default_option

    async def handle_user_response(
        self,
        interaction_id: str,
        user_response: str
    ) -> bool:
        """
        处理用户响应
        
        Args:
            interaction_id: 交互ID
            user_response: 用户响应
            
        Returns:
            bool: 是否成功处理
        """
        if interaction_id not in self.pending_interactions:
            logger.warning(f"交互ID不存在: {interaction_id}")
            return False
        
        interaction = self.pending_interactions[interaction_id]
        interaction.user_response = user_response
        interaction.resolved = True
        
        # 执行回调
        if interaction.callback:
            try:
                if asyncio.iscoroutinefunction(interaction.callback):
                    await interaction.callback(user_response)
                else:
                    interaction.callback(user_response)
            except Exception as e:
                logger.error(f"执行回调函数失败: {str(e)}")
        
        # 移动到历史记录
        self.interaction_history.append(interaction)
        del self.pending_interactions[interaction_id]
        
        logger.info(f"用户响应已处理: {interaction_id} -> {user_response}")
        return True

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

    async def _wait_for_response(self, interaction_id: str):
        """等待用户响应"""
        while interaction_id in self.pending_interactions:
            interaction = self.pending_interactions[interaction_id]
            if interaction.resolved:
                break
            await asyncio.sleep(0.5)

    async def _handle_timeout(self, interaction_id: str):
        """处理超时"""
        if interaction_id not in self.pending_interactions:
            return
        
        interaction = self.pending_interactions[interaction_id]
        
        # 使用默认选项
        if interaction.default_option:
            await self.handle_user_response(interaction_id, interaction.default_option)
        else:
            # 关闭交互
            await self._close_interaction(interaction_id)
        
        logger.info(f"交互超时处理完成: {interaction_id}")

    async def _close_interaction(self, interaction_id: str):
        """关闭交互"""
        if interaction_id in self.pending_interactions:
            interaction = self.pending_interactions[interaction_id]
            interaction.resolved = True
            self.interaction_history.append(interaction)
            del self.pending_interactions[interaction_id]
            
            # 通知UI关闭
            if self.event_bus:
                await self.event_bus.publish(
                    "ui.interaction.close",
                    {"interaction_id": interaction_id}
                )

    async def _timeout_handler_loop(self):
        """超时处理循环"""
        try:
            while True:
                await asyncio.sleep(10)  # 每10秒检查一次
                
                current_time = datetime.utcnow()
                timeout_interactions = []
                
                for interaction_id, interaction in self.pending_interactions.items():
                    if interaction.timeout_seconds and not interaction.resolved:
                        elapsed = (current_time - interaction.timestamp).total_seconds()
                        if elapsed >= interaction.timeout_seconds:
                            timeout_interactions.append(interaction_id)
                
                for interaction_id in timeout_interactions:
                    await self._handle_timeout(interaction_id)
                    
        except asyncio.CancelledError:
            logger.info("超时处理循环被取消")
        except Exception as e:
            logger.error(f"超时处理循环异常: {str(e)}")

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

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return {
            "status": "healthy",
            "pending_interactions": len(self.pending_interactions),
            "total_interactions": len(self.interaction_history),
            "recent_interactions": await self.get_interaction_history(5),
        }


__all__ = ["UserInteractionManager", "UserInteraction", "InteractionType"]

