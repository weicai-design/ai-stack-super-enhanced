"""统一聊天窗口"""
import logging
from typing import List, Dict, Any
from .models import Message, Session

logger = logging.getLogger(__name__)

class ChatWindow:
    def __init__(self):
        logger.info("✅ 聊天窗口已初始化")
    
    def process_message(self, session: Session, message: Message) -> Dict[str, Any]:
        """处理消息"""
        session.messages.append(message)
        
        # 简单回复（实际应调用AI）
        response_msg = Message(
            session_id=session.id,
            role="assistant",
            content=f"收到您的消息：{message.content}"
        )
        session.messages.append(response_msg)
        
        return {
            "message": response_msg.model_dump(),
            "session_context": session.context
        }
    
    def route_to_function(self, message: str) -> str:
        """路由到功能模块"""
        keywords = {
            "财务": "/finance",
            "订单": "/erp/orders",
            "股票": "/stock",
            "内容": "/content",
            "趋势": "/trend"
        }
        
        for keyword, route in keywords.items():
            if keyword in message:
                return route
        
        return "/default"

chat_window = ChatWindow()

















