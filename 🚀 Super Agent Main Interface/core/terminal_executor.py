"""
终端命令执行器
支持在聊天框中执行终端命令
"""

import subprocess
import asyncio
import os
import platform
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TerminalExecutor:
    """
    终端命令执行器
    
    功能：
    1. 执行终端命令
    2. 安全命令验证
    3. 命令历史记录
    4. 输出流式返回
    """
    
    def __init__(self):
        self.command_history = []
        self.max_history = 100
        self.allowed_commands = [
            'ls', 'pwd', 'cd', 'cat', 'grep', 'find', 'ps', 'top',
            'df', 'du', 'free', 'uptime', 'whoami', 'date', 'echo',
            'git', 'python', 'python3', 'pip', 'pip3', 'node', 'npm',
            'docker', 'docker-compose', 'kubectl', 'curl', 'wget'
        ]
        self.dangerous_commands = [
            'rm -rf', 'format', 'del /f', 'shutdown', 'reboot',
            'mkfs', 'dd if=', 'sudo rm', 'chmod 777'
        ]
        self.current_directory = os.getcwd()
    
    async def execute_command(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        执行终端命令
        
        Args:
            command: 要执行的命令
            timeout: 超时时间（秒）
            cwd: 工作目录
            env: 环境变量
            
        Returns:
            执行结果
        """
        # 安全检查
        safety_check = self._check_command_safety(command)
        if not safety_check['safe']:
            return {
                "success": False,
                "error": f"命令不安全: {safety_check['reason']}",
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
        
        # 记录命令历史
        self._add_to_history(command)
        
        # 设置工作目录
        work_dir = cwd or self.current_directory
        
        # 设置环境变量
        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)
        
        try:
            # 执行命令
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir,
                env=exec_env
            )
            
            # 等待执行完成（带超时）
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return {
                    "success": False,
                    "error": f"命令执行超时（{timeout}秒）",
                    "command": command,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 解码输出
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return {
                "success": process.returncode == 0,
                "command": command,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode,
                "timestamp": datetime.now().isoformat(),
                "work_directory": work_dir
            }
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": datetime.now().isoformat()
            }
    
    async def execute_command_stream(
        self,
        command: str,
        timeout: int = 30,
        cwd: Optional[str] = None
    ):
        """
        流式执行命令（实时输出）
        
        Args:
            command: 要执行的命令
            timeout: 超时时间
            cwd: 工作目录
            
        Yields:
            输出行
        """
        # 安全检查
        safety_check = self._check_command_safety(command)
        if not safety_check['safe']:
            yield {
                "type": "error",
                "data": f"命令不安全: {safety_check['reason']}"
            }
            return
        
        # 记录命令历史
        self._add_to_history(command)
        
        work_dir = cwd or self.current_directory
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=work_dir
            )
            
            # 流式读取输出
            while True:
                line = await asyncio.wait_for(
                    process.stdout.readline(),
                    timeout=timeout
                )
                
                if not line:
                    break
                
                yield {
                    "type": "stdout",
                    "data": line.decode('utf-8', errors='replace')
                }
            
            # 等待进程结束
            await process.wait()
            
            yield {
                "type": "done",
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            process.kill()
            yield {
                "type": "error",
                "data": f"命令执行超时（{timeout}秒）"
            }
        except Exception as e:
            yield {
                "type": "error",
                "data": str(e)
            }
    
    def _check_command_safety(self, command: str) -> Dict[str, Any]:
        """
        检查命令安全性
        
        Args:
            command: 命令字符串
            
        Returns:
            安全检查结果
        """
        command_lower = command.lower().strip()
        
        # 检查危险命令
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in command_lower:
                return {
                    "safe": False,
                    "reason": f"包含危险命令: {dangerous}"
                }
        
        # 检查是否允许的命令（可选，如果启用白名单）
        # 这里我们只检查危险命令，允许其他命令
        
        return {
            "safe": True,
            "reason": "命令安全"
        }
    
    def _add_to_history(self, command: str):
        """添加命令到历史记录"""
        self.command_history.append({
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录数量
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
    
    def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取命令历史"""
        return self.command_history[-limit:]
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "current_directory": self.current_directory,
            "home_directory": os.path.expanduser("~")
        }
    
    def change_directory(self, path: str) -> Dict[str, Any]:
        """
        切换工作目录
        
        Args:
            path: 目标路径
            
        Returns:
            切换结果
        """
        try:
            if os.path.isdir(path):
                self.current_directory = os.path.abspath(path)
                return {
                    "success": True,
                    "new_directory": self.current_directory
                }
            else:
                return {
                    "success": False,
                    "error": f"目录不存在: {path}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


