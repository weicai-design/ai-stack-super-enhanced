"""
终端命令执行器
支持在聊天框中执行终端命令
"""

import asyncio
import os
import platform
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4
import logging

if TYPE_CHECKING:
    from .workflow_monitor import WorkflowMonitor

logger = logging.getLogger(__name__)


@dataclass
class CommandSafetyResult:
    """命令安全检查结果"""
    safe: bool
    reason: Optional[str] = None
    blocked_token: Optional[str] = None
    command: Optional[str] = None


@dataclass
class CommandRecord:
    """命令执行记录"""
    command_id: str
    command: str
    timestamp: str
    cwd: str
    duration: Optional[float] = None
    success: bool = True
    return_code: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TerminalExecutor:
    """
    终端命令执行器
    
    功能：
    1. 执行终端命令
    2. 安全命令验证
    3. 命令历史记录
    4. 输出流式返回
    """
    
    def __init__(self, workflow_monitor: Optional["WorkflowMonitor"] = None):
        self.command_history: List[CommandRecord] = []
        self.max_history = 200
        self.allowed_commands = {
            'ls', 'pwd', 'cd', 'cat', 'grep', 'find', 'ps', 'top',
            'df', 'du', 'free', 'uptime', 'whoami', 'date', 'echo',
            'git', 'python', 'python3', 'pip', 'pip3', 'node', 'npm',
            'docker', 'docker-compose', 'kubectl', 'curl', 'wget',
            'head', 'tail', 'wc', 'env', 'which'
        }
        self.dangerous_commands = [
            'rm -rf', 'format', 'del /f', 'shutdown', 'reboot',
            'mkfs', 'dd if=', 'sudo rm', 'chmod 777', ':(){', 'kill -9 1'
        ]
        self.forbidden_tokens = [
            '&&', '||', ';', '|', '>', '<', '$(', '`', '\\', '../', '~', '%', '&'
        ]
        self.sensitive_env_patterns = [
            "API_KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AWS_", "AZURE_"
        ]
        self.current_directory = os.getcwd()
        self.workspace_root = os.environ.get("TERMINAL_WORKSPACE_ROOT", self.current_directory)
        self.max_output_chars = 10_000
        self.max_output_lines = 400
        self.max_runtime = 30
        self.max_concurrent_commands = 2
        self._semaphore = asyncio.Semaphore(self.max_concurrent_commands)
        self.workflow_monitor: Optional["WorkflowMonitor"] = workflow_monitor
    
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
        # 记录命令
        command_id = str(uuid4())
        
        # 安全检查
        safety_check = self._check_command_safety(command)
        if not safety_check.safe:
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="blocked",
                success=False,
                severity="high",
                error=safety_check.reason
            )
            return {
                "success": False,
                "error": f"命令不安全: {safety_check.reason}",
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "command_id": command_id
            }
        
        record = self._add_to_history(command_id, command)
        
        # 设置工作目录
        try:
            work_dir = self._resolve_work_directory(cwd)
        except ValueError as exc:
            record.success = False
            record.error = str(exc)
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="denied",
                success=False,
                severity="high",
                cwd=cwd,
                error=str(exc)
            )
            return {
                "success": False,
                "error": str(exc),
                "command": command,
                "timestamp": record.timestamp,
                "command_id": command_id
            }
        
        # 设置环境变量
        exec_env = self._sanitize_environment(env)
        
        await self._record_terminal_event(
            command_id=command_id,
            command=command,
            phase="start",
            success=True,
            severity="info",
            cwd=work_dir,
            metadata={"timeout": timeout}
        )
        
        try:
            async with self._semaphore:
                # 执行命令
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir,
                    env=exec_env
                )
                
                # 等待执行完成（带超时）
                exec_timeout = min(timeout, self.max_runtime)
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=exec_timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    record.success = False
                    record.error = f"命令执行超时（{exec_timeout}秒）"
                    record.duration = (datetime.now() - datetime.fromisoformat(record.timestamp)).total_seconds()
                    await self._record_terminal_event(
                        command_id=command_id,
                        command=command,
                        phase="timeout",
                        success=False,
                        severity="medium",
                        cwd=work_dir,
                        metadata={"timeout": exec_timeout},
                        error=record.error
                    )
                    return {
                        "success": False,
                        "error": record.error,
                        "command": command,
                        "timestamp": record.timestamp,
                        "command_id": command_id
                    }
                
                # 解码输出
                stdout_text = self._safe_decode(stdout)
                stderr_text = self._safe_decode(stderr)
                
                # 截断输出
                stdout_text, stdout_truncated = self._truncate_output(stdout_text)
                stderr_text, stderr_truncated = self._truncate_output(stderr_text)
                
                record.duration = (datetime.now() - datetime.fromisoformat(record.timestamp)).total_seconds()
                record.return_code = process.returncode
                record.success = process.returncode == 0
                if not record.success:
                    record.error = stderr_text or "命令执行失败"
                
                result = {
                    "success": process.returncode == 0,
                    "command": command,
                    "command_id": command_id,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "stdout_truncated": stdout_truncated,
                    "stderr_truncated": stderr_truncated,
                    "return_code": process.returncode,
                    "timestamp": datetime.now().isoformat(),
                    "work_directory": work_dir,
                    "duration": record.duration
                }
                
                await self._record_terminal_event(
                    command_id=command_id,
                    command=command,
                    phase="completed" if record.success else "failed",
                    success=record.success,
                    severity="info" if record.success else "medium",
                    cwd=work_dir,
                    metadata={
                        "return_code": process.returncode,
                        "duration": record.duration,
                        "stdout_truncated": stdout_truncated,
                        "stderr_truncated": stderr_truncated
                    },
                    error=None if record.success else record.error
                )
                return result
            
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            record.success = False
            record.error = str(e)
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="error",
                success=False,
                severity="high",
                cwd=cwd or self.current_directory,
                error=str(e)
            )
            return {
                "success": False,
                "error": str(e),
                "command": command,
                "timestamp": datetime.now().isoformat(),
                "command_id": command_id
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
        command_id = str(uuid4())
        # 安全检查
        safety_check = self._check_command_safety(command)
        if not safety_check.safe:
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="blocked",
                success=False,
                severity="high",
                error=safety_check.reason
            )
            yield {
                "type": "error",
                "data": f"命令不安全: {safety_check.reason}"
            }
            return
        
        record = self._add_to_history(command_id, command)
        try:
            work_dir = self._resolve_work_directory(cwd)
        except ValueError as exc:
            record.success = False
            record.error = str(exc)
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="denied",
                success=False,
                severity="high",
                cwd=cwd,
                error=str(exc)
            )
            yield {
                "type": "error",
                "data": str(exc)
            }
            return
        
        await self._record_terminal_event(
            command_id=command_id,
            command=command,
            phase="start",
            success=True,
            severity="info",
            cwd=work_dir,
            metadata={"timeout": timeout, "mode": "stream"}
        )
        
        try:
            async with self._semaphore:
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir
                )
                
                exec_timeout = min(timeout, self.max_runtime)
                # 流式读取输出
                lines_read = 0
                start_time = datetime.now()
                while True:
                    try:
                        line = await asyncio.wait_for(
                            process.stdout.readline(),
                            timeout=exec_timeout
                        )
                    except asyncio.TimeoutError:
                        process.kill()
                        record.success = False
                        record.error = f"命令执行超时（{exec_timeout}秒）"
                        yield {
                            "type": "error",
                            "data": record.error
                        }
                        await self._record_terminal_event(
                            command_id=command_id,
                            command=command,
                            phase="timeout",
                            success=False,
                            severity="medium",
                            cwd=work_dir,
                            metadata={"timeout": exec_timeout, "mode": "stream"},
                            error=record.error
                        )
                        return
                    
                    if not line:
                        break
                    
                    decoded_line = self._safe_decode(line)
                    lines_read += 1
                    truncated_line, truncated = self._truncate_output(decoded_line, single_line=True)
                    yield {
                        "type": "stdout",
                        "data": truncated_line,
                        "truncated": truncated
                    }
                    
                    if lines_read >= self.max_output_lines:
                        yield {
                            "type": "warning",
                            "data": f"输出超过{self.max_output_lines}行，剩余内容已截断"
                        }
                        process.kill()
                        break
                
                # 等待进程结束
                await process.wait()
                record.duration = (datetime.now() - start_time).total_seconds()
                record.return_code = process.returncode
                record.success = process.returncode == 0
                
                yield {
                    "type": "done",
                    "return_code": process.returncode,
                    "command_id": command_id,
                    "duration": record.duration
                }
                await self._record_terminal_event(
                    command_id=command_id,
                    command=command,
                    phase="completed" if record.success else "failed",
                    success=record.success,
                    severity="info" if record.success else "medium",
                    cwd=work_dir,
                    metadata={
                        "return_code": process.returncode,
                        "duration": record.duration,
                        "lines_read": lines_read,
                        "mode": "stream"
                    },
                    error=None if record.success else record.error
                )
            
        except Exception as e:
            record.success = False
            record.error = str(e)
            yield {
                "type": "error",
                "data": str(e)
            }
            await self._record_terminal_event(
                command_id=command_id,
                command=command,
                phase="error",
                success=False,
                severity="high",
                cwd=cwd or self.current_directory,
                error=str(e)
            )
    
    def _check_command_safety(self, command: str) -> CommandSafetyResult:
        """
        检查命令安全性
        
        Args:
            command: 命令字符串
            
        Returns:
            安全检查结果
        """
        command_lower = command.lower().strip()
        
        # 禁止多命令连接符及危险token
        for token in self.forbidden_tokens:
            if token in command_lower:
                return CommandSafetyResult(
                    safe=False,
                    reason=f"命令中包含受限制的符号: {token}",
                    blocked_token=token,
                    command=command
                )
        
        # 检查危险命令
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in command_lower:
                return CommandSafetyResult(
                    safe=False,
                    reason=f"包含危险命令: {dangerous}",
                    blocked_token=dangerous,
                    command=command
                )
        
        # 白名单验证（仅允许列表中命令作为入口）
        base_command = command.split()[0]
        if base_command not in self.allowed_commands:
            return CommandSafetyResult(
                safe=False,
                reason=f"命令 {base_command} 未在允许列表中",
                blocked_token=base_command,
                command=command
            )
        
        return CommandSafetyResult(
            safe=True,
            reason="命令安全",
            command=command
        )
    
    def _add_to_history(self, command_id: str, command: str) -> CommandRecord:
        """添加命令到历史记录"""
        record = CommandRecord(
            command_id=command_id,
            command=command,
            timestamp=datetime.now().isoformat(),
            cwd=self.current_directory
        )
        self.command_history.append(record)
        
        if len(self.command_history) > self.max_history:
            self.command_history = self.command_history[-self.max_history:]
        
        return record
    
    def get_command_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取命令历史"""
        return [
            {
                "command_id": record.command_id,
                "command": record.command,
                "timestamp": record.timestamp,
                "cwd": record.cwd,
                "duration": record.duration,
                "success": record.success,
                "return_code": record.return_code,
                "error": record.error
            }
            for record in self.command_history[-limit:]
        ]
    
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
                new_dir = os.path.abspath(path)
                if not new_dir.startswith(self.workspace_root):
                    return {
                        "success": False,
                        "error": "不允许访问工作区外的目录"
                    }
                self.current_directory = new_dir
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

    def _resolve_work_directory(self, cwd: Optional[str]) -> str:
        """解析安全的工作目录"""
        target = cwd or self.current_directory
        abs_path = os.path.abspath(target)
        if not abs_path.startswith(self.workspace_root):
            raise ValueError("工作目录必须在工作区内")
        return abs_path

    def _sanitize_environment(self, extra_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """清理环境变量，避免泄露敏感信息"""
        exec_env = {}
        for key, value in os.environ.items():
            if any(pattern in key for pattern in self.sensitive_env_patterns):
                continue
            exec_env[key] = value
        
        if extra_env:
            for key, value in extra_env.items():
                if any(pattern in key for pattern in self.sensitive_env_patterns):
                    continue
                exec_env[key] = value
        
        return exec_env

    def _safe_decode(self, data: bytes) -> str:
        """安全解码输出"""
        if not data:
            return ""
        return data.decode('utf-8', errors='replace')

    def _truncate_output(self, text: str, single_line: bool = False):
        """截断超长输出"""
        if not text:
            return text, False
        
        if single_line:
            if len(text) > 1000:
                return text[:1000] + "... [行已截断]", True
            return text, False
        
        truncated = False
        lines = text.splitlines()
        if len(lines) > self.max_output_lines:
            lines = lines[:self.max_output_lines]
            truncated = True
        
        trimmed_text = "\n".join(lines)
        if len(trimmed_text) > self.max_output_chars:
            trimmed_text = trimmed_text[:self.max_output_chars] + "\n...[输出已截断]"
            truncated = True
        
        return trimmed_text, truncated

    async def _record_terminal_event(
        self,
        command_id: str,
        command: str,
        phase: str,
        success: bool,
        severity: str,
        cwd: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """记录终端事件到工作流监控器"""
        if not self.workflow_monitor:
            return
        await self.workflow_monitor.record_system_event(
            event_type="terminal_command",
            source="terminal_executor",
            severity=severity,
            success=success,
            data={
                "command_id": command_id,
                "command": command,
                "phase": phase,
                "cwd": cwd or self.current_directory,
                "metadata": metadata or {}
            },
            error=error
        )

    def set_workflow_monitor(self, workflow_monitor: Optional["WorkflowMonitor"]):
        """设置工作流监控器"""
        self.workflow_monitor = workflow_monitor


