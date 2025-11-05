"""
title: Terminal Command Executor
author: AI Stack Team
version: 1.0.0
description: Execute terminal commands safely from OpenWebUI
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, List
import subprocess
import shlex
import os


class Action:
    class Valves(BaseModel):
        """配置阀门"""
        enable_terminal: bool = Field(
            default=False,
            description="启用终端功能（⚠️ 谨慎开启）"
        )
        allowed_commands: List[str] = Field(
            default=["ls", "cat", "pwd", "echo", "date", "whoami", "python3", "node", "npm"],
            description="允许的命令白名单"
        )
        max_execution_time: int = Field(
            default=30,
            description="命令最大执行时间（秒）"
        )
        working_directory: str = Field(
            default="/Users/ywc/ai-stack-super-enhanced",
            description="工作目录"
        )
    
    def __init__(self):
        self.valves = self.Valves()
        
        # 危险命令黑名单
        self.blacklist_commands = [
            "rm", "rmdir", "del", "format",
            "dd", "mkfs", "fdisk",
            "shutdown", "reboot", "halt",
            "kill", "killall", "pkill",
            "chmod", "chown",
            "sudo", "su",
            ">", ">>", "|", ";", "&&", "||"  # 重定向和管道
        ]
    
    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Any]] = None,
    ) -> Optional[dict]:
        """
        终端执行动作
        
        支持的命令：
        - /terminal <command> - 执行命令
        - /terminal ls - 列出文件
        - /terminal cat <file> - 查看文件
        - /terminal pwd - 当前目录
        """
        
        if not self.valves.enable_terminal:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "⚠️ 终端功能未启用。请在Function设置中启用 `enable_terminal`。"
                    }
                ]
            }
        
        user_message = body["messages"][-1]["content"]
        
        # 解析命令
        if not user_message.startswith("/terminal"):
            return None
        
        command = user_message.replace("/terminal", "").strip()
        
        if not command:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": "💻 **终端执行器**\n\n使用方法: `/terminal <command>`\n\n允许的命令: " + ", ".join(self.valves.allowed_commands)
                    }
                ]
            }
        
        # 安全检查
        safety_check = self.check_command_safety(command)
        if not safety_check["safe"]:
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": f"🛡️ **安全检查失败**\n\n{safety_check['reason']}"
                    }
                ]
            }
        
        # 执行命令
        return await self.execute_command(command, event_emitter)
    
    def check_command_safety(self, command: str) -> dict:
        """检查命令安全性"""
        # 检查黑名单
        for forbidden in self.blacklist_commands:
            if forbidden in command:
                return {
                    "safe": False,
                    "reason": f"禁止使用危险命令: {forbidden}"
                }
        
        # 检查白名单
        cmd_parts = shlex.split(command)
        if not cmd_parts:
            return {"safe": False, "reason": "命令为空"}
        
        base_command = cmd_parts[0]
        
        # 检查是否在白名单中
        allowed = False
        for allowed_cmd in self.valves.allowed_commands:
            if base_command == allowed_cmd or base_command.endswith(f"/{allowed_cmd}"):
                allowed = True
                break
        
        if not allowed:
            return {
                "safe": False,
                "reason": f"命令 '{base_command}' 不在白名单中。允许的命令: {', '.join(self.valves.allowed_commands)}"
            }
        
        return {"safe": True}
    
    async def execute_command(
        self, 
        command: str, 
        event_emitter: Optional[Callable] = None
    ) -> dict:
        """执行终端命令"""
        try:
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": f"执行命令: {command}", "done": False},
                    }
                )
            
            # 执行命令
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.valves.working_directory,
                capture_output=True,
                text=True,
                timeout=self.valves.max_execution_time
            )
            
            # 格式化输出
            formatted = f"💻 **命令执行结果**\n\n"
            formatted += f"**命令**: `{command}`\n"
            formatted += f"**目录**: {self.valves.working_directory}\n"
            formatted += f"**退出码**: {result.returncode}\n\n"
            
            if result.stdout:
                formatted += "**输出**:\n```\n"
                formatted += result.stdout[:1000]  # 限制输出长度
                if len(result.stdout) > 1000:
                    formatted += "\n... (输出已截断)"
                formatted += "\n```\n\n"
            
            if result.stderr:
                formatted += "**错误**:\n```\n"
                formatted += result.stderr[:500]
                formatted += "\n```\n\n"
            
            if event_emitter:
                await event_emitter(
                    {
                        "type": "status",
                        "data": {"description": "命令执行完成", "done": True},
                    }
                )
            
            return {
                "messages": [
                    {
                        "role": "assistant",
                        "content": formatted
                    }
                ]
            }
        
        except subprocess.TimeoutExpired:
            return self.error_response(f"命令执行超时 (>{self.valves.max_execution_time}秒)")
        
        except Exception as e:
            return self.error_response(str(e))
    
    def error_response(self, error: str) -> dict:
        """错误响应"""
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"❌ 终端执行错误: {error}"
                }
            ]
        }



