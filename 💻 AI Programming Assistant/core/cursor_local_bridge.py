"""
Cursor本地桥接
P0-016: 集成 Cursor（协议/插件/本地桥，授权与权限隔离）
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import asyncio
import logging
import subprocess
import os
import json

from .cursor_protocol import CursorProtocol, ProtocolCommand, ProtocolMessage, ProtocolMessageType
from .cursor_bridge import CursorBridge
from .cursor_plugin_system import CursorPluginSystem, PermissionManager, PluginPermission

logger = logging.getLogger(__name__)


@dataclass
class BridgeConnection:
    """桥接连接"""
    connection_id: str
    client_type: str  # cursor, ai_stack, plugin
    connected_at: datetime
    last_activity: datetime
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CursorLocalBridge:
    """
    Cursor本地桥接
    
    功能：
    1. 本地进程间通信
    2. 连接管理
    3. 消息路由
    4. 权限验证
    5. 与Cursor编辑器集成
    """
    
    def __init__(
        self,
        protocol: Optional[CursorProtocol] = None,
        plugin_system: Optional[CursorPluginSystem] = None,
        permission_manager: Optional[PermissionManager] = None
    ):
        self.protocol = protocol or CursorProtocol()
        self.plugin_system = plugin_system or CursorPluginSystem()
        self.permission_manager = permission_manager or PermissionManager()
        self.cursor_bridge = CursorBridge()
        
        self.connections: Dict[str, BridgeConnection] = {}
        self.is_running = False
        
        # 注册协议处理器
        self._register_protocol_handlers()
        
        logger.info("Cursor本地桥接初始化完成")
    
    def _register_protocol_handlers(self):
        """注册协议处理器"""
        # 打开文件
        self.protocol.register_handler(
            ProtocolCommand.OPEN_FILE,
            self._handle_open_file
        )
        
        # 编辑代码
        self.protocol.register_handler(
            ProtocolCommand.EDIT_CODE,
            self._handle_edit_code
        )
        
        # 获取补全
        self.protocol.register_handler(
            ProtocolCommand.GET_COMPLETION,
            self._handle_get_completion
        )
        
        # 检测错误
        self.protocol.register_handler(
            ProtocolCommand.DETECT_ERRORS,
            self._handle_detect_errors
        )
        
        # 同步项目
        self.protocol.register_handler(
            ProtocolCommand.SYNC_PROJECT,
            self._handle_sync_project
        )
        
        # 获取文件内容
        self.protocol.register_handler(
            ProtocolCommand.GET_FILE_CONTENT,
            self._handle_get_file_content
        )
        
        # 保存文件
        self.protocol.register_handler(
            ProtocolCommand.SAVE_FILE,
            self._handle_save_file
        )
        
        # 执行命令
        self.protocol.register_handler(
            ProtocolCommand.EXECUTE_COMMAND,
            self._handle_execute_command
        )
    
    async def _handle_open_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理打开文件请求"""
        file_path = params.get("file_path")
        line_number = params.get("line_number")
        
        if not file_path:
            raise ValueError("缺少file_path参数")
        
        # 检查权限
        if not self.permission_manager.check_permissions([PluginPermission.READ_FILE]):
            raise PermissionError("没有读取文件权限")
        
        result = await self.cursor_bridge.open_in_cursor(file_path, line_number)
        return result
    
    async def _handle_edit_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理编辑代码请求"""
        file_path = params.get("file_path")
        edits = params.get("edits", [])
        
        if not file_path:
            raise ValueError("缺少file_path参数")
        
        if not edits:
            raise ValueError("缺少edits参数")
        
        # 检查权限
        if not self.permission_manager.check_permissions([PluginPermission.WRITE_FILE]):
            raise PermissionError("没有写入文件权限")
        
        # 调用插件钩子
        await self.plugin_system.call_hook('code_edit', file_path=file_path, edits=edits)
        
        result = await self.cursor_bridge.edit_code(file_path, edits)
        return result
    
    async def _handle_get_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取补全请求"""
        file_path = params.get("file_path")
        line_number = params.get("line_number")
        column = params.get("column")
        context_lines = params.get("context_lines", 5)
        
        if not all([file_path, line_number is not None, column is not None]):
            raise ValueError("缺少必要参数")
        
        # 调用插件钩子
        hook_results = await self.plugin_system.call_hook(
            'completion_request',
            file_path=file_path,
            line_number=line_number,
            column=column
        )
        
        result = await self.cursor_bridge.get_code_completion(
            file_path, line_number, column, context_lines
        )
        
        # 合并插件建议
        if hook_results:
            plugin_suggestions = []
            for hook_result in hook_results:
                if isinstance(hook_result, dict) and "suggestions" in hook_result:
                    plugin_suggestions.extend(hook_result["suggestions"])
            
            if plugin_suggestions:
                result["suggestions"].extend(plugin_suggestions)
                result["suggestions"] = result["suggestions"][:20]  # 限制数量
        
        return result
    
    async def _handle_detect_errors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理检测错误请求"""
        file_path = params.get("file_path")
        
        if not file_path:
            raise ValueError("缺少file_path参数")
        
        result = await self.cursor_bridge.detect_errors(file_path)
        
        # 调用插件钩子
        if result.get("errors"):
            await self.plugin_system.call_hook(
                'error_detected',
                file_path=file_path,
                errors=result["errors"]
            )
        
        return result
    
    async def _handle_sync_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理同步项目请求"""
        project_path = params.get("project_path")
        files = params.get("files")
        
        if not project_path:
            raise ValueError("缺少project_path参数")
        
        result = await self.cursor_bridge.sync_project(project_path, files)
        return result
    
    async def _handle_get_file_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理获取文件内容请求"""
        file_path = params.get("file_path")
        start_line = params.get("start_line", 1)
        end_line = params.get("end_line")
        
        if not file_path:
            raise ValueError("缺少file_path参数")
        
        # 检查权限
        if not self.permission_manager.check_permissions([PluginPermission.READ_FILE]):
            raise PermissionError("没有读取文件权限")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line) if end_line else len(lines)
            content = ''.join(lines[start_idx:end_idx])
            
            return {
                "success": True,
                "file_path": file_path,
                "content": content,
                "start_line": start_line,
                "end_line": end_idx,
                "total_lines": len(lines)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_save_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理保存文件请求"""
        file_path = params.get("file_path")
        content = params.get("content")
        
        if not file_path or content is None:
            raise ValueError("缺少必要参数")
        
        # 检查权限
        if not self.permission_manager.check_permissions([PluginPermission.WRITE_FILE]):
            raise PermissionError("没有写入文件权限")
        
        # 调用插件钩子
        await self.plugin_system.call_hook('file_save', file_path=file_path, content=content)
        
        result = await self.cursor_bridge.sync_code(file_path, content)
        return result
    
    async def _handle_execute_command(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理执行命令请求"""
        command = params.get("command")
        cwd = params.get("cwd")
        
        if not command:
            raise ValueError("缺少command参数")
        
        # 检查权限
        if not self.permission_manager.check_permissions([PluginPermission.EXECUTE_COMMAND]):
            raise PermissionError("没有执行命令权限")
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "命令执行超时"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def start(self):
        """启动桥接"""
        if self.is_running:
            logger.warning("桥接已在运行")
            return
        
        await self.protocol.start_server()
        self.is_running = True
        logger.info("Cursor本地桥接已启动")
    
    async def stop(self):
        """停止桥接"""
        self.is_running = False
        await self.protocol.stop_server()
        logger.info("Cursor本地桥接已停止")
    
    def register_connection(
        self,
        connection_id: str,
        client_type: str,
        permissions: Optional[List[str]] = None
    ) -> BridgeConnection:
        """注册连接"""
        connection = BridgeConnection(
            connection_id=connection_id,
            client_type=client_type,
            connected_at=datetime.now(),
            last_activity=datetime.now(),
            permissions=permissions or []
        )
        self.connections[connection_id] = connection
        logger.info(f"已注册连接: {connection_id} ({client_type})")
        return connection
    
    def update_connection_activity(self, connection_id: str):
        """更新连接活动时间"""
        if connection_id in self.connections:
            self.connections[connection_id].last_activity = datetime.now()
    
    def get_connection(self, connection_id: str) -> Optional[BridgeConnection]:
        """获取连接"""
        return self.connections.get(connection_id)
    
    def list_connections(self) -> List[Dict[str, Any]]:
        """列出所有连接"""
        return [
            {
                "connection_id": c.connection_id,
                "client_type": c.client_type,
                "connected_at": c.connected_at.isoformat(),
                "last_activity": c.last_activity.isoformat(),
                "permissions": c.permissions
            }
            for c in self.connections.values()
        ]
    
    async def send_to_cursor(
        self,
        command: ProtocolCommand,
        params: Dict[str, Any]
    ) -> ProtocolMessage:
        """发送消息到Cursor"""
        return await self.protocol.send_request(command, params)
    
    def get_status(self) -> Dict[str, Any]:
        """获取桥接状态"""
        return {
            "is_running": self.is_running,
            "protocol_status": "running" if self.protocol.is_running else "stopped",
            "plugin_count": len(self.plugin_system.plugins),
            "connection_count": len(self.connections),
            "cursor_installed": self.cursor_bridge.cursor_installed,
            "permissions": self.permission_manager.get_permission_status()
        }

