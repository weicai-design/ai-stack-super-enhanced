"""
Cursor协议通信
P0-016: 集成 Cursor（协议/插件/本地桥，授权与权限隔离）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
import logging
import socket
import struct
import os
import importlib.util

logger = logging.getLogger(__name__)


class ProtocolMessageType(Enum):
    """协议消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class ProtocolCommand(Enum):
    """协议命令"""
    OPEN_FILE = "open_file"
    EDIT_CODE = "edit_code"
    GET_COMPLETION = "get_completion"
    DETECT_ERRORS = "detect_errors"
    SYNC_PROJECT = "sync_project"
    GET_FILE_CONTENT = "get_file_content"
    SAVE_FILE = "save_file"
    EXECUTE_COMMAND = "execute_command"


@dataclass
class ProtocolMessage:
    """协议消息"""
    message_id: str
    message_type: ProtocolMessageType
    command: Optional[ProtocolCommand] = None
    params: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


class CursorProtocol:
    """
    Cursor协议通信
    
    功能：
    1. 实现Cursor协议消息格式
    2. 支持请求/响应/通知模式
    3. 本地Socket通信
    4. 消息序列化/反序列化
    """
    
    def __init__(self, socket_path: Optional[str] = None):
        self.socket_path = socket_path or "/tmp/cursor_bridge.sock"
        self.server_socket: Optional[socket.socket] = None
        self.client_connections: List[socket.socket] = []
        self.message_handlers: Dict[ProtocolCommand, callable] = {}
        self.is_running = False
        
    async def start_server(self):
        """启动协议服务器"""
        if self.is_running:
            logger.warning("协议服务器已在运行")
            return
        
        try:
            # 创建Unix域套接字
            if os.path.exists(self.socket_path):
                os.unlink(self.socket_path)
            
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.server_socket.bind(self.socket_path)
            self.server_socket.listen(5)
            self.server_socket.setblocking(False)
            
            self.is_running = True
            logger.info(f"Cursor协议服务器已启动: {self.socket_path}")
            
            # 启动接收循环
            asyncio.create_task(self._accept_connections())
            
        except Exception as e:
            logger.error(f"启动协议服务器失败: {e}")
            self.is_running = False
    
    async def _accept_connections(self):
        """接受连接"""
        loop = asyncio.get_event_loop()
        
        while self.is_running:
            try:
                client_socket, _ = await loop.sock_accept(self.server_socket)
                self.client_connections.append(client_socket)
                asyncio.create_task(self._handle_client(client_socket))
            except Exception as e:
                if self.is_running:
                    logger.error(f"接受连接失败: {e}")
                break
    
    async def _handle_client(self, client_socket: socket.socket):
        """处理客户端连接"""
        loop = asyncio.get_event_loop()
        
        try:
            while True:
                # 接收消息长度
                length_data = await loop.sock_recv(client_socket, 4)
                if not length_data:
                    break
                
                message_length = struct.unpack('>I', length_data)[0]
                
                # 接收消息内容
                message_data = b''
                while len(message_data) < message_length:
                    chunk = await loop.sock_recv(client_socket, message_length - len(message_data))
                    if not chunk:
                        break
                    message_data += chunk
                
                # 解析消息
                message = self._deserialize_message(message_data)
                
                # 处理消息
                response = await self._process_message(message)
                
                # 发送响应
                await self._send_message(client_socket, response)
                
        except Exception as e:
            logger.error(f"处理客户端消息失败: {e}")
        finally:
            if client_socket in self.client_connections:
                self.client_connections.remove(client_socket)
            client_socket.close()
    
    async def _process_message(self, message: ProtocolMessage) -> ProtocolMessage:
        """处理消息"""
        if message.message_type != ProtocolMessageType.REQUEST:
            return ProtocolMessage(
                message_id=message.message_id,
                message_type=ProtocolMessageType.ERROR,
                error="无效的消息类型"
            )
        
        if not message.command:
            return ProtocolMessage(
                message_id=message.message_id,
                message_type=ProtocolMessageType.ERROR,
                error="缺少命令"
            )
        
        # 查找处理器
        handler = self.message_handlers.get(message.command)
        if not handler:
            return ProtocolMessage(
                message_id=message.message_id,
                message_type=ProtocolMessageType.ERROR,
                error=f"未找到命令处理器: {message.command.value}"
            )
        
        try:
            # 执行处理器
            result = await handler(message.params)
            
            return ProtocolMessage(
                message_id=message.message_id,
                message_type=ProtocolMessageType.RESPONSE,
                command=message.command,
                result=result
            )
        except Exception as e:
            logger.error(f"处理消息失败: {e}", exc_info=True)
            return ProtocolMessage(
                message_id=message.message_id,
                message_type=ProtocolMessageType.ERROR,
                error=str(e)
            )
    
    def register_handler(self, command: ProtocolCommand, handler: callable):
        """注册消息处理器"""
        self.message_handlers[command] = handler
        logger.info(f"已注册命令处理器: {command.value}")
    
    async def send_request(
        self,
        command: ProtocolCommand,
        params: Dict[str, Any],
        timeout: float = 5.0
    ) -> ProtocolMessage:
        """
        发送请求
        
        Args:
            command: 命令
            params: 参数
            timeout: 超时时间
            
        Returns:
            响应消息
        """
        if not os.path.exists(self.socket_path):
            raise ConnectionError(f"协议服务器未运行: {self.socket_path}")
        
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        
        try:
            client_socket.connect(self.socket_path)
            client_socket.setblocking(False)
            
            # 创建请求消息
            message = ProtocolMessage(
                message_id=f"req_{int(datetime.now().timestamp() * 1000)}",
                message_type=ProtocolMessageType.REQUEST,
                command=command,
                params=params
            )
            
            # 发送消息
            await self._send_message(client_socket, message)
            
            # 接收响应
            loop = asyncio.get_event_loop()
            
            # 接收消息长度
            length_data = await asyncio.wait_for(
                loop.sock_recv(client_socket, 4),
                timeout=timeout
            )
            message_length = struct.unpack('>I', length_data)[0]
            
            # 接收消息内容
            message_data = b''
            while len(message_data) < message_length:
                chunk = await asyncio.wait_for(
                    loop.sock_recv(client_socket, message_length - len(message_data)),
                    timeout=timeout
                )
                message_data += chunk
            
            # 解析响应
            response = self._deserialize_message(message_data)
            return response
            
        finally:
            client_socket.close()
    
    async def _send_message(self, socket: socket.socket, message: ProtocolMessage):
        """发送消息"""
        message_data = self._serialize_message(message)
        message_length = len(message_data)
        
        # 发送长度
        length_data = struct.pack('>I', message_length)
        loop = asyncio.get_event_loop()
        await loop.sock_sendall(socket, length_data)
        
        # 发送内容
        await loop.sock_sendall(socket, message_data)
    
    def _serialize_message(self, message: ProtocolMessage) -> bytes:
        """序列化消息"""
        data = {
            "message_id": message.message_id,
            "message_type": message.message_type.value,
            "command": message.command.value if message.command else None,
            "params": message.params,
            "result": message.result,
            "error": message.error,
            "timestamp": message.timestamp.isoformat()
        }
        return json.dumps(data).encode('utf-8')
    
    def _deserialize_message(self, data: bytes) -> ProtocolMessage:
        """反序列化消息"""
        obj = json.loads(data.decode('utf-8'))
        return ProtocolMessage(
            message_id=obj["message_id"],
            message_type=ProtocolMessageType(obj["message_type"]),
            command=ProtocolCommand(obj["command"]) if obj.get("command") else None,
            params=obj.get("params", {}),
            result=obj.get("result"),
            error=obj.get("error"),
            timestamp=datetime.fromisoformat(obj["timestamp"])
        )
    
    async def stop_server(self):
        """停止协议服务器"""
        self.is_running = False
        
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
        
        for client in self.client_connections:
            client.close()
        self.client_connections.clear()
        
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        logger.info("Cursor协议服务器已停止")

