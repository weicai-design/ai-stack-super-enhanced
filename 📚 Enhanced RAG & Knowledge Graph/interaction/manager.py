"""
交互管理器（增强版）
Interaction Manager

版本: v1.0.0
"""

import logging
from typing import Dict, List
from collections import defaultdict
from .models import Message, Session, Command
from .chat_window import chat_window
from .function_router import function_router

logger = logging.getLogger(__name__)


class InteractionManager:
    """交互管理器（增强版）"""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.commands: Dict[str, List[Command]] = defaultdict(list)
        
        # 核心组件
        self.chat_window = chat_window
        self.router = function_router
        
        logger.info("✅ 交互管理器（增强版）已初始化")
    
    def create_session(self, tenant_id: str, user_id: str) -> Session:
        """创建会话"""
        session = Session(tenant_id=tenant_id, user_id=user_id)
        self.sessions[session.id] = session
        logger.info(f"会话已创建: {session.id}")
        return session
    
    def add_message(self, session_id: str, message: Message) -> Dict:
        """添加消息并处理"""
        if session_id not in self.sessions:
            raise ValueError("会话不存在")
        
        session = self.sessions[session_id]
        return self.chat_window.process_message(session, message)
    
    def execute_command(self, tenant_id: str, command: Command) -> Command:
        """执行命令"""
        command.tenant_id = tenant_id
        command.status = "executed"
        command.result = {"success": True, "message": "命令已执行"}
        self.commands[tenant_id].append(command)
        logger.info(f"命令已执行: {command.command}")
        return command
    
    def get_available_functions(self) -> dict:
        """获取可用功能"""
        return self.router.get_available_functions()
    
    def route_to_function(self, function_name: str, params: dict) -> dict:
        """路由到功能"""
        return self.router.route_request(function_name, params)


interaction_manager = InteractionManager()

