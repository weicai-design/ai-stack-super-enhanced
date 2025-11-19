"""
终端命令执行器（增强版）
支持在聊天框中执行终端命令，包含：
1. 本地沙箱机制（工作目录隔离、资源限制）
2. 白名单管理系统（可配置、可扩展）
3. 审计日志系统（独立存储、查询、导出）
4. 安全策略配置
"""

import asyncio
import os
import platform
import shutil

# resource模块仅在Unix系统上可用
try:
    import resource
except ImportError:
    resource = None
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import uuid4
import logging
import json
from pathlib import Path

from core.security.command_policy import CommandSecurityPolicy, CommandPolicyResult

if TYPE_CHECKING:
    from .workflow_monitor import WorkflowMonitor
    from .terminal_audit import TerminalAuditLogger

# 延迟导入以避免循环依赖
try:
    from .terminal_audit import AuditEventType, AuditSeverity
    # 使用枚举值
    _COMMAND_START = AuditEventType.COMMAND_START.value
    _COMMAND_BLOCKED = AuditEventType.COMMAND_BLOCKED.value
    _COMMAND_COMPLETED = AuditEventType.COMMAND_COMPLETED.value
    _COMMAND_FAILED = AuditEventType.COMMAND_FAILED.value
    _WHITELIST_UPDATE = AuditEventType.WHITELIST_UPDATE.value
    _SEVERITY_INFO = AuditSeverity.INFO.value
    _SEVERITY_MEDIUM = AuditSeverity.MEDIUM.value
    _SEVERITY_HIGH = AuditSeverity.HIGH.value
except ImportError:
    # 如果导入失败，使用字符串常量
    _COMMAND_START = "command_start"
    _COMMAND_BLOCKED = "command_blocked"
    _COMMAND_COMPLETED = "command_completed"
    _COMMAND_FAILED = "command_failed"
    _WHITELIST_UPDATE = "whitelist_update"
    _SEVERITY_INFO = "info"
    _SEVERITY_MEDIUM = "medium"
    _SEVERITY_HIGH = "high"

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
    
    def __init__(
        self,
        workflow_monitor: Optional["WorkflowMonitor"] = None,
        audit_logger: Optional["TerminalAuditLogger"] = None,
        sandbox_enabled: bool = True
    ):
        """
        初始化终端执行器（增强版）
        
        Args:
            workflow_monitor: 工作流监控器
            audit_logger: 审计日志系统
            sandbox_enabled: 是否启用沙箱模式
        """
        self.command_history: List[CommandRecord] = []
        self.max_history = 200
        
        # 白名单配置（可配置）
        self.whitelist_config_file = Path(__file__).parent.parent / "data" / "terminal_whitelist.json"
        self.whitelist_config_file.parent.mkdir(parents=True, exist_ok=True)
        self.security_policy: Optional[CommandSecurityPolicy] = None
        self._load_whitelist_config()
        self._refresh_security_policy()
        
        # 危险命令列表
        self.dangerous_commands = [
            'rm -rf', 'format', 'del /f', 'shutdown', 'reboot',
            'mkfs', 'dd if=', 'sudo rm', 'chmod 777', ':(){', 'kill -9 1',
            'sudo', 'su', 'passwd', 'useradd', 'userdel', 'groupadd'
        ]
        
        # 禁止的token
        self.forbidden_tokens = [
            '&&', '||', ';', '|', '>', '<', '$(', '`', '\\', '../', '~', '%', '&'
        ]
        
        # 敏感环境变量模式
        self.sensitive_env_patterns = [
            "API_KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AWS_", "AZURE_"
        ]
        
        # 沙箱配置
        self.sandbox_enabled = sandbox_enabled
        self.current_directory = os.getcwd()
        self.workspace_root = os.environ.get("TERMINAL_WORKSPACE_ROOT", self.current_directory)
        
        # 创建沙箱工作目录
        if self.sandbox_enabled:
            self.sandbox_dir = Path(self.workspace_root) / ".terminal_sandbox"
            self.sandbox_dir.mkdir(parents=True, exist_ok=True)
            self.current_directory = str(self.sandbox_dir)
        else:
            self.sandbox_dir = None
        
        # 资源限制
        self.max_output_chars = 10_000
        self.max_output_lines = 400
        self.max_runtime = 30
        self.max_concurrent_commands = 2
        self.max_memory_mb = 512  # 最大内存512MB
        self.max_cpu_time = 30  # 最大CPU时间30秒
        
        self._semaphore = asyncio.Semaphore(self.max_concurrent_commands)
        self.workflow_monitor: Optional["WorkflowMonitor"] = workflow_monitor
        self.audit_logger: Optional["TerminalAuditLogger"] = audit_logger
        
        logger.info(f"终端执行器已初始化（沙箱模式: {self.sandbox_enabled}）")
    
    def _load_whitelist_config(self):
        """加载白名单配置"""
        try:
            if self.whitelist_config_file.exists():
                with open(self.whitelist_config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self.allowed_commands = set(config.get("allowed_commands", []))
                    self.dangerous_commands = config.get("dangerous_commands", self.dangerous_commands)
                    self.forbidden_tokens = config.get("forbidden_tokens", self.forbidden_tokens)
            else:
                # 默认白名单
                self.allowed_commands = {
                    'ls', 'pwd', 'cd', 'cat', 'grep', 'find', 'ps', 'top',
                    'df', 'du', 'free', 'uptime', 'whoami', 'date', 'echo',
                    'git', 'python', 'python3', 'pip', 'pip3', 'node', 'npm',
                    'docker', 'docker-compose', 'kubectl', 'curl', 'wget',
                    'head', 'tail', 'wc', 'env', 'which', 'mkdir', 'touch',
                    'cp', 'mv', 'rm', 'chmod', 'chown', 'tar', 'zip', 'unzip'
                }
                self._save_whitelist_config()
        except Exception as e:
            logger.warning(f"加载白名单配置失败，使用默认配置: {e}")
            self.allowed_commands = {
                'ls', 'pwd', 'cd', 'cat', 'grep', 'find', 'ps', 'top',
                'df', 'du', 'free', 'uptime', 'whoami', 'date', 'echo'
            }
    
    def _save_whitelist_config(self):
        """保存白名单配置"""
        try:
            config = {
                "allowed_commands": sorted(list(self.allowed_commands)),
                "dangerous_commands": self.dangerous_commands,
                "forbidden_tokens": self.forbidden_tokens,
                "updated_at": datetime.now().isoformat()
            }
            with open(self.whitelist_config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存白名单配置失败: {e}")
        finally:
            self._refresh_security_policy()
    
    def update_whitelist(
        self,
        add_commands: Optional[List[str]] = None,
        remove_commands: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        更新白名单
        
        Args:
            add_commands: 要添加的命令列表
            remove_commands: 要移除的命令列表
            
        Returns:
            更新结果
        """
        try:
            if add_commands:
                for cmd in add_commands:
                    self.allowed_commands.add(cmd)
            
            if remove_commands:
                for cmd in remove_commands:
                    self.allowed_commands.discard(cmd)
            
            self._save_whitelist_config()
            
            # 记录审计日志
            if self.audit_logger:
                asyncio.create_task(self.audit_logger.log_event(
                    event_type=_WHITELIST_UPDATE,
                    severity=_SEVERITY_INFO,
                    metadata={
                        "added": add_commands or [],
                        "removed": remove_commands or [],
                        "total_count": len(self.allowed_commands)
                    }
                ))
            
            return {
                "success": True,
                "message": "白名单已更新",
                "allowed_commands": sorted(list(self.allowed_commands)),
                "count": len(self.allowed_commands)
            }
        except Exception as e:
            logger.error(f"更新白名单失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _refresh_security_policy(self) -> None:
        """同步安全策略实例"""
        try:
            self.security_policy = CommandSecurityPolicy(
                allowed_commands=self.allowed_commands,
                dangerous_commands=self.dangerous_commands,
                forbidden_tokens=self.forbidden_tokens,
                config_path=self.whitelist_config_file
            )
        except Exception as exc:
            logger.warning(f"初始化安全策略失败，将使用内建校验: {exc}")
            self.security_policy = None
    
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
            # 记录审计日志
            if self.audit_logger:
                await self.audit_logger.log_event(
                    event_type=_COMMAND_BLOCKED,
                    severity=_SEVERITY_HIGH,
                    command_id=command_id,
                    command=command,
                    cwd=cwd or self.current_directory,
                    error=safety_check.reason,
                    metadata={"blocked_token": safety_check.blocked_token}
                )
            
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
        
        # 记录审计日志（命令开始）
        if self.audit_logger:
            await self.audit_logger.log_event(
                event_type=_COMMAND_START,
                severity=_SEVERITY_INFO,
                command_id=command_id,
                command=command,
                cwd=work_dir,
                metadata={"timeout": timeout, "sandbox": self.sandbox_enabled}
            )
        
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
                # 执行命令（在沙箱中）
                # Windows不支持preexec_fn，需要平台检查
                preexec_fn = None
                if self.sandbox_enabled and platform.system() in ['Linux', 'Darwin']:
                    preexec_fn = self._set_resource_limits
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir,
                    env=exec_env,
                    preexec_fn=preexec_fn
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
                    "duration": record.duration,
                    "sandbox": self.sandbox_enabled
                }
                
                # 记录审计日志（命令完成/失败）
                if self.audit_logger:
                    event_type = _COMMAND_COMPLETED if record.success else _COMMAND_FAILED
                    severity = _SEVERITY_INFO if record.success else _SEVERITY_MEDIUM
                    await self.audit_logger.log_event(
                        event_type=event_type,
                        severity=severity,
                        command_id=command_id,
                        command=command,
                        cwd=work_dir,
                        return_code=process.returncode,
                        duration=record.duration,
                        success=record.success,
                        error=None if record.success else record.error,
                        metadata={
                            "stdout_truncated": stdout_truncated,
                            "stderr_truncated": stderr_truncated
                        }
                    )
                
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
        if self.security_policy:
            policy_result: CommandPolicyResult = self.security_policy.inspect(command)
            if not policy_result.safe:
                return CommandSafetyResult(
                    safe=False,
                    reason=policy_result.reason,
                    blocked_token=policy_result.blocked_token,
                    command=policy_result.command or command
                )
            return CommandSafetyResult(
                safe=True,
                reason=policy_result.reason or "命令安全",
                command=command
            )
        
        # 回退逻辑：沿用旧有检查
        command_lower = command.lower().strip()
        for token in self.forbidden_tokens:
            if token in command_lower:
                return CommandSafetyResult(
                    safe=False,
                    reason=f"命令中包含受限制的符号: {token}",
                    blocked_token=token,
                    command=command
                )
        for dangerous in self.dangerous_commands:
            if dangerous.lower() in command_lower:
                return CommandSafetyResult(
                    safe=False,
                    reason=f"包含危险命令: {dangerous}",
                    blocked_token=dangerous,
                    command=command
                )
        base_command = command.split()[0]
        if base_command not in self.allowed_commands:
            return CommandSafetyResult(
                safe=False,
                reason=f"命令 {base_command} 未在允许列表中",
                blocked_token=base_command,
                command=command
            )
        return CommandSafetyResult(safe=True, reason="命令安全", command=command)
    
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
    
    def set_audit_logger(self, audit_logger: Optional["TerminalAuditLogger"]):
        """设置审计日志系统"""
        self.audit_logger = audit_logger
    
    def _set_resource_limits(self):
        """设置资源限制（仅Linux/macOS）"""
        if resource is None:
            return
        
        if platform.system() in ['Linux', 'Darwin']:
            try:
                # 限制内存使用（MB转字节）
                max_memory_bytes = self.max_memory_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
                
                # 限制CPU时间（秒）
                resource.setrlimit(resource.RLIMIT_CPU, (self.max_cpu_time, self.max_cpu_time))
                
                # 限制文件大小
                resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))  # 100MB
            except Exception as e:
                logger.warning(f"设置资源限制失败: {e}")
    
    def get_whitelist(self) -> Dict[str, Any]:
        """获取当前白名单配置"""
        return {
            "allowed_commands": sorted(list(self.allowed_commands)),
            "dangerous_commands": self.dangerous_commands,
            "forbidden_tokens": self.forbidden_tokens,
            "count": len(self.allowed_commands)
        }
    
    def clear_sandbox(self) -> Dict[str, Any]:
        """
        清理沙箱目录
        
        Returns:
            清理结果
        """
        if not self.sandbox_enabled or not self.sandbox_dir:
            return {"success": False, "error": "沙箱未启用"}
        
        try:
            # 删除沙箱目录中的所有内容（保留目录本身）
            for item in self.sandbox_dir.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            
            return {
                "success": True,
                "message": "沙箱已清理",
                "sandbox_dir": str(self.sandbox_dir)
            }
        except Exception as e:
            logger.error(f"清理沙箱失败: {e}")
            return {"success": False, "error": str(e)}


