"""
桌面通知系统
支持macOS和Windows的桌面通知
"""

import subprocess
import platform
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationSystem:
    """桌面通知系统"""
    
    def __init__(self):
        self.system = platform.system()
        logger.info(f"通知系统初始化 - 操作系统: {self.system}")
    
    def send_notification(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: bool = True,
        icon: Optional[str] = None
    ) -> bool:
        """
        发送桌面通知
        
        Args:
            title: 通知标题
            message: 通知内容
            subtitle: 副标题（仅macOS）
            sound: 是否播放提示音
            icon: 图标路径
            
        Returns:
            是否成功
        """
        try:
            if self.system == "Darwin":  # macOS
                return self._send_macos_notification(title, message, subtitle, sound)
            elif self.system == "Windows":
                return self._send_windows_notification(title, message)
            elif self.system == "Linux":
                return self._send_linux_notification(title, message)
            else:
                logger.warning(f"不支持的操作系统: {self.system}")
                return False
                
        except Exception as e:
            logger.error(f"发送通知失败: {e}")
            return False
    
    def _send_macos_notification(
        self,
        title: str,
        message: str,
        subtitle: Optional[str] = None,
        sound: bool = True
    ) -> bool:
        """发送macOS通知（使用osascript）"""
        try:
            # 构建AppleScript命令
            script = f'display notification "{message}" with title "{title}"'
            
            if subtitle:
                script += f' subtitle "{subtitle}"'
            
            if sound:
                script += ' sound name "default"'
            
            # 执行AppleScript
            subprocess.run(
                ['osascript', '-e', script],
                check=True,
                capture_output=True
            )
            
            logger.info(f"macOS通知已发送: {title}")
            return True
            
        except Exception as e:
            logger.error(f"macOS通知失败: {e}")
            return False
    
    def _send_windows_notification(
        self,
        title: str,
        message: str
    ) -> bool:
        """发送Windows通知（使用win10toast）"""
        try:
            # 尝试使用win10toast库
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=10,
                    threaded=True
                )
                logger.info(f"Windows通知已发送: {title}")
                return True
            except ImportError:
                # 如果没有安装win10toast，使用PowerShell
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template.GetXml())
                $xml.SelectSingleNode('//text[@id="1"]').InnerText = "{title}"
                $xml.SelectSingleNode('//text[@id="2"]').InnerText = "{message}"
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("AI Stack").Show($toast)
                '''
                
                subprocess.run(
                    ['powershell', '-Command', ps_script],
                    check=True,
                    capture_output=True
                )
                logger.info(f"Windows通知已发送: {title}")
                return True
                
        except Exception as e:
            logger.error(f"Windows通知失败: {e}")
            return False
    
    def _send_linux_notification(
        self,
        title: str,
        message: str
    ) -> bool:
        """发送Linux通知（使用notify-send）"""
        try:
            subprocess.run(
                ['notify-send', title, message],
                check=True,
                capture_output=True
            )
            logger.info(f"Linux通知已发送: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Linux通知失败: {e}")
            return False
    
    # ==================== 预定义通知模板 ====================
    
    def notify_system_started(self, service_name: str):
        """系统启动通知"""
        self.send_notification(
            "✅ 服务启动",
            f"{service_name} 已成功启动",
            "AI Stack"
        )
    
    def notify_system_stopped(self, service_name: str):
        """系统停止通知"""
        self.send_notification(
            "🛑 服务停止",
            f"{service_name} 已停止运行",
            "AI Stack"
        )
    
    def notify_task_completed(self, task_name: str, duration: str):
        """任务完成通知"""
        self.send_notification(
            "✅ 任务完成",
            f"{task_name} 已完成（耗时{duration}）",
            "AI Stack - 任务代理"
        )
    
    def notify_task_failed(self, task_name: str, error: str):
        """任务失败通知"""
        self.send_notification(
            "❌ 任务失败",
            f"{task_name} 执行失败: {error[:50]}",
            "AI Stack - 任务代理"
        )
    
    def notify_resource_conflict(self, conflict_type: str, severity: str):
        """资源冲突通知"""
        self.send_notification(
            "⚠️ 资源冲突",
            f"检测到{conflict_type}冲突，严重程度: {severity}",
            "AI Stack - 资源管理"
        )
    
    def notify_new_data(self, data_type: str, count: int):
        """新数据通知"""
        self.send_notification(
            "📊 新数据",
            f"收到 {count} 条新的{data_type}数据",
            "AI Stack"
        )
    
    def notify_report_ready(self, report_name: str):
        """报告就绪通知"""
        self.send_notification(
            "📄 报告就绪",
            f"{report_name} 已生成完成",
            "AI Stack - 趋势分析"
        )
    
    def notify_error(self, error_title: str, error_message: str):
        """错误通知"""
        self.send_notification(
            f"❌ {error_title}",
            error_message[:100],
            "AI Stack"
        )
    
    def notify_success(self, success_title: str, success_message: str):
        """成功通知"""
        self.send_notification(
            f"✅ {success_title}",
            success_message[:100],
            "AI Stack"
        )


# ==================== 交互式通知（用户选择）====================

class InteractiveNotification:
    """交互式通知（macOS）"""
    
    @staticmethod
    def show_choice_dialog(
        title: str,
        message: str,
        choices: list
    ) -> Optional[str]:
        """
        显示选择对话框
        
        Args:
            title: 标题
            message: 消息
            choices: 选项列表 ["选项1", "选项2", ...]
            
        Returns:
            用户选择的选项（或None）
        """
        try:
            if platform.system() != "Darwin":
                logger.warning("交互式对话框仅支持macOS")
                return None
            
            # 构建按钮字符串
            buttons = '", "'.join(choices)
            
            script = f'''
            set choice to button returned of (display dialog "{message}" ¬
                with title "{title}" ¬
                buttons {{"{buttons}"}} ¬
                default button 1)
            return choice
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            
            selected = result.stdout.strip()
            logger.info(f"用户选择: {selected}")
            return selected
            
        except Exception as e:
            logger.error(f"显示选择对话框失败: {e}")
            return None
    
    @staticmethod
    def show_resource_conflict_dialog(
        conflict_info: dict,
        resolution_options: list
    ) -> Optional[int]:
        """
        显示资源冲突解决选择对话框
        
        Args:
            conflict_info: 冲突信息
            resolution_options: 解决方案列表
            
        Returns:
            选择的方案ID
        """
        conflict_type = ', '.join(conflict_info.get('conflict_type', []))
        severity = conflict_info.get('severity', 'unknown')
        
        message = f"检测到资源冲突\\n类型: {conflict_type}\\n严重程度: {severity}\\n\\n请选择解决方案:"
        
        choices = [
            f"{i+1}. {opt.get('title', '未知')}"
            for i, opt in enumerate(resolution_options[:4])
        ]
        
        selected = InteractiveNotification.show_choice_dialog(
            "⚠️ 资源冲突",
            message,
            choices
        )
        
        if selected:
            # 提取选项编号
            for i, choice in enumerate(choices):
                if choice in selected:
                    return resolution_options[i].get('option_id')
        
        return None


# ==================== 全局通知实例 ====================

notification_system = NotificationSystem()


# ==================== 使用示例 ====================

"""
使用示例:

1. 发送简单通知:

from common.notification_system import notification_system

notification_system.send_notification(
    "任务完成",
    "数据采集任务已成功完成"
)

2. 使用预定义通知:

notification_system.notify_task_completed("每日数据采集", "5分钟")
notification_system.notify_resource_conflict("内存", "high")
notification_system.notify_report_ready("市场趋势分析报告")

3. 交互式选择:

from common.notification_system import InteractiveNotification

choice = InteractiveNotification.show_choice_dialog(
    "资源冲突",
    "系统资源不足，请选择:",
    ["暂停低优先级服务", "降低资源分配", "继续监控"]
)

if choice == "暂停低优先级服务":
    # 执行相应操作
    pass
"""


