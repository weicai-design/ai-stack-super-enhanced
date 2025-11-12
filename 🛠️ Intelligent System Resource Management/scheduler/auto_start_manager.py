"""
自动启动管理器
实现系统开机自启动功能
对应需求: 8.6 - 系统自动启动
"""

import asyncio
import json
import logging
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AutoStartConfig:
    """自动启动配置"""
    enabled: bool = True
    delay_seconds: int = 5  # 开机后延迟启动时间
    services_to_start: List[str] = None  # 要启动的服务列表
    startup_script_path: Optional[str] = None  # 启动脚本路径
    check_interval: int = 60  # 检查间隔（秒）


class AutoStartManager:
    """
    自动启动管理器
    负责系统开机自启动配置和管理
    """

    def __init__(self):
        self.config: Optional[AutoStartConfig] = None
        self.config_file_path = self._get_config_file_path()
        self.is_enabled = False
        self.startup_script_path = None
        self.monitoring_task = None

    def _get_config_file_path(self) -> Path:
        """获取配置文件路径"""
        if platform.system() == "Windows":
            config_dir = Path(os.environ.get("APPDATA", "")) / "AI-STACK"
        else:
            config_dir = Path.home() / ".config" / "ai-stack"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "auto_start.json"

    async def initialize(self, config: Dict = None, core_services: Dict = None):
        """初始化自动启动管理器"""
        try:
            # 加载配置
            await self._load_config()
            
            # 如果提供了新配置，更新
            if config:
                if isinstance(config, dict):
                    self.config = AutoStartConfig(**config)
                else:
                    self.config = config
                await self._save_config()
            
            # 如果没有配置，创建默认配置
            if not self.config:
                self.config = AutoStartConfig()
                await self._save_config()
            
            self.is_enabled = self.config.enabled
            
            logger.info(f"自动启动管理器初始化完成，启用状态: {self.is_enabled}")
            
        except Exception as e:
            logger.error(f"自动启动管理器初始化失败: {str(e)}")
            self.config = AutoStartConfig(enabled=False)

    async def enable_auto_start(self, services: List[str] = None) -> bool:
        """
        启用自动启动
        
        Args:
            services: 要自动启动的服务列表，None表示启动所有服务
            
        Returns:
            bool: 是否成功启用
        """
        try:
            self.config.enabled = True
            if services:
                self.config.services_to_start = services
            
            # 保存配置
            await self._save_config()
            
            # 配置系统级自动启动
            success = await self._configure_system_autostart()
            
            if success:
                self.is_enabled = True
                logger.info("自动启动已启用")
            else:
                logger.warning("自动启动配置失败，但配置已保存")
            
            return success
            
        except Exception as e:
            logger.error(f"启用自动启动失败: {str(e)}")
            return False

    async def disable_auto_start(self) -> bool:
        """禁用自动启动"""
        try:
            self.config.enabled = False
            await self._save_config()
            
            # 移除系统级自动启动配置
            await self._remove_system_autostart()
            
            self.is_enabled = False
            logger.info("自动启动已禁用")
            return True
            
        except Exception as e:
            logger.error(f"禁用自动启动失败: {str(e)}")
            return False

    async def start_monitoring(self):
        """启动监控任务（检查系统是否启动）"""
        if self.monitoring_task:
            return
        
        self.monitoring_task = asyncio.create_task(self._monitor_system_startup())
        logger.info("自动启动监控任务已启动")

    async def stop_monitoring(self):
        """停止监控任务"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
            self.monitoring_task = None
            logger.info("自动启动监控任务已停止")

    async def _monitor_system_startup(self):
        """监控系统启动"""
        try:
            while True:
                await asyncio.sleep(self.config.check_interval)
                
                # 检查是否需要自动启动
                if self.is_enabled and await self._should_auto_start():
                    logger.info("检测到系统启动，准备自动启动服务")
                    await self._execute_auto_start()
                    
        except asyncio.CancelledError:
            logger.info("自动启动监控任务被取消")
        except Exception as e:
            logger.error(f"自动启动监控异常: {str(e)}")

    async def _should_auto_start(self) -> bool:
        """判断是否应该自动启动"""
        # 检查系统启动时间（简化版，实际应该检查系统启动时间戳）
        # 这里可以检查进程启动时间或系统运行时间
        try:
            import psutil
            boot_time = psutil.boot_time()
            process_time = psutil.Process().create_time()
            
            # 如果进程启动时间接近系统启动时间，说明是开机启动
            time_diff = process_time - boot_time
            return time_diff < 300  # 5分钟内
            
        except Exception as e:
            logger.warning(f"检查系统启动时间失败: {str(e)}")
            return False

    async def _execute_auto_start(self):
        """执行自动启动"""
        try:
            # 延迟启动
            if self.config.delay_seconds > 0:
                await asyncio.sleep(self.config.delay_seconds)
            
            # 获取启动脚本路径
            script_path = self.config.startup_script_path or self._get_default_startup_script()
            
            if script_path and os.path.exists(script_path):
                logger.info(f"执行启动脚本: {script_path}")
                # 这里可以调用启动脚本
                # 实际实现应该调用BootManager或StartupController
            else:
                logger.warning("启动脚本不存在，跳过自动启动")
                
        except Exception as e:
            logger.error(f"执行自动启动失败: {str(e)}")

    async def _configure_system_autostart(self) -> bool:
        """配置系统级自动启动"""
        try:
            system = platform.system()
            
            if system == "Windows":
                return await self._configure_windows_autostart()
            elif system == "Darwin":  # macOS
                return await self._configure_macos_autostart()
            elif system == "Linux":
                return await self._configure_linux_autostart()
            else:
                logger.warning(f"不支持的操作系统: {system}")
                return False
                
        except Exception as e:
            logger.error(f"配置系统自动启动失败: {str(e)}")
            return False

    async def _configure_windows_autostart(self) -> bool:
        """配置Windows自动启动"""
        try:
            import winreg
            
            # 创建启动脚本
            script_path = self._create_startup_script()
            if not script_path:
                return False
            
            # 添加到注册表启动项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(key, "AI-STACK", 0, winreg.REG_SZ, script_path)
            winreg.CloseKey(key)
            
            logger.info("Windows自动启动配置成功")
            return True
            
        except Exception as e:
            logger.error(f"配置Windows自动启动失败: {str(e)}")
            return False

    async def _configure_macos_autostart(self) -> bool:
        """配置macOS自动启动"""
        try:
            # 创建LaunchAgent plist文件
            plist_content = self._generate_launchd_plist()
            plist_path = Path.home() / "Library" / "LaunchAgents" / "com.ai-stack.plist"
            
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(plist_content)
            
            # 加载LaunchAgent
            import subprocess
            subprocess.run(["launchctl", "load", str(plist_path)], check=True)
            
            logger.info("macOS自动启动配置成功")
            return True
            
        except Exception as e:
            logger.error(f"配置macOS自动启动失败: {str(e)}")
            return False

    async def _configure_linux_autostart(self) -> bool:
        """配置Linux自动启动"""
        try:
            # 创建systemd服务文件或.desktop文件
            desktop_content = self._generate_desktop_file()
            desktop_path = Path.home() / ".config" / "autostart" / "ai-stack.desktop"
            
            desktop_path.parent.mkdir(parents=True, exist_ok=True)
            desktop_path.write_text(desktop_content)
            desktop_path.chmod(0o755)
            
            logger.info("Linux自动启动配置成功")
            return True
            
        except Exception as e:
            logger.error(f"配置Linux自动启动失败: {str(e)}")
            return False

    async def _remove_system_autostart(self):
        """移除系统级自动启动配置"""
        try:
            system = platform.system()
            
            if system == "Windows":
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE
                )
                try:
                    winreg.DeleteValue(key, "AI-STACK")
                except FileNotFoundError:
                    pass
                winreg.CloseKey(key)
                
            elif system == "Darwin":
                plist_path = Path.home() / "Library" / "LaunchAgents" / "com.ai-stack.plist"
                if plist_path.exists():
                    import subprocess
                    subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
                    plist_path.unlink()
                    
            elif system == "Linux":
                desktop_path = Path.home() / ".config" / "autostart" / "ai-stack.desktop"
                if desktop_path.exists():
                    desktop_path.unlink()
                    
        except Exception as e:
            logger.error(f"移除系统自动启动配置失败: {str(e)}")

    def _create_startup_script(self) -> Optional[str]:
        """创建启动脚本"""
        try:
            script_dir = self.config_file_path.parent
            script_path = script_dir / "start_ai_stack.py"
            
            script_content = f"""#!/usr/bin/env python3
\"\"\"
AI-STACK自动启动脚本
\"\"\"
import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

async def main():
    # 导入启动管理器
    from boot_manager import BootManager
    
    boot_manager = BootManager()
    await boot_manager.initialize()
    
    # 启动系统
    result = await boot_manager.start_system()
    print(f"系统启动结果: {{result}}")

if __name__ == "__main__":
    asyncio.run(main())
"""
            script_path.write_text(script_content)
            script_path.chmod(0o755)
            
            return str(script_path)
            
        except Exception as e:
            logger.error(f"创建启动脚本失败: {str(e)}")
            return None

    def _get_default_startup_script(self) -> Optional[str]:
        """获取默认启动脚本路径"""
        script_path = self.config_file_path.parent / "start_ai_stack.py"
        return str(script_path) if script_path.exists() else None

    def _generate_launchd_plist(self) -> str:
        """生成macOS LaunchAgent plist内容"""
        script_path = self._get_default_startup_script() or "/usr/local/bin/ai-stack-start"
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-stack</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StartInterval</key>
    <integer>{self.config.check_interval}</integer>
</dict>
</plist>
"""

    def _generate_desktop_file(self) -> str:
        """生成Linux .desktop文件内容"""
        script_path = self._get_default_startup_script() or "/usr/local/bin/ai-stack-start"
        
        return f"""[Desktop Entry]
Type=Application
Name=AI-STACK
Exec=/usr/bin/python3 {script_path}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
"""

    async def _load_config(self):
        """加载配置"""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.config = AutoStartConfig(**config_data)
            else:
                self.config = None
                
        except Exception as e:
            logger.error(f"加载自动启动配置失败: {str(e)}")
            self.config = None

    async def _save_config(self):
        """保存配置"""
        try:
            config_data = {
                "enabled": self.config.enabled,
                "delay_seconds": self.config.delay_seconds,
                "services_to_start": self.config.services_to_start or [],
                "startup_script_path": self.config.startup_script_path,
                "check_interval": self.config.check_interval,
            }
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存自动启动配置失败: {str(e)}")

    async def get_status(self) -> Dict[str, Any]:
        """获取自动启动状态"""
        return {
            "enabled": self.is_enabled,
            "config": {
                "delay_seconds": self.config.delay_seconds if self.config else 0,
                "services_to_start": self.config.services_to_start if self.config else [],
                "check_interval": self.config.check_interval if self.config else 60,
            },
            "config_file": str(self.config_file_path),
            "startup_script": self._get_default_startup_script(),
        }

    async def stop(self):
        """停止自动启动管理器"""
        await self.stop_monitoring()
        logger.info("自动启动管理器已停止")

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return await self.get_status()


__all__ = ["AutoStartManager", "AutoStartConfig"]

