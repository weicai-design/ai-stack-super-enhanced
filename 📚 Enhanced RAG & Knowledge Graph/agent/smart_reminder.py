"""
智能提醒系统
支持自动时间解析、定时提醒、任务提醒等功能
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


class SmartReminder:
    """智能提醒系统"""
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        初始化智能提醒系统
        
        Args:
            storage_path: 提醒数据存储路径
        """
        self.storage_path = storage_path or "data/reminders.json"
        self.reminders = []
        self.load_reminders()
        
    def parse_time_from_text(self, text: str) -> Optional[datetime]:
        """
        从文本中解析时间
        
        支持格式：
        - "明天10点"
        - "下周五下午3点"
        - "3天后"
        - "11月15日"
        - "2025-11-15 14:30"
        
        Args:
            text: 包含时间信息的文本
            
        Returns:
            解析出的时间，如果无法解析则返回None
        """
        now = datetime.now()
        
        # 精确时间格式
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{1,2})', 
             lambda m: datetime(int(m[1]), int(m[2]), int(m[3]), int(m[4]), int(m[5]))),
            (r'(\d{1,2})月(\d{1,2})日\s*(\d{1,2})[点时]',
             lambda m: datetime(now.year, int(m[1]), int(m[2]), int(m[3]))),
        ]
        
        for pattern, handler in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return handler(match.groups())
                except:
                    pass
        
        # 相对时间
        if "明天" in text:
            target = now + timedelta(days=1)
            hour = self._extract_hour(text) or 9  # 默认早上9点
            return target.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if "后天" in text:
            target = now + timedelta(days=2)
            hour = self._extract_hour(text) or 9
            return target.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if match := re.search(r'(\d+)天后', text):
            days = int(match.group(1))
            target = now + timedelta(days=days)
            hour = self._extract_hour(text) or 9
            return target.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        if match := re.search(r'(\d+)小时后', text):
            hours = int(match.group(1))
            return now + timedelta(hours=hours)
        
        if "下周" in text:
            days_ahead = 7 - now.weekday()
            if "一" in text or "周一" in text:
                days_ahead += 0
            elif "二" in text or "周二" in text:
                days_ahead += 1
            elif "三" in text or "周三" in text:
                days_ahead += 2
            elif "四" in text or "周四" in text:
                days_ahead += 3
            elif "五" in text or "周五" in text:
                days_ahead += 4
            
            target = now + timedelta(days=days_ahead)
            hour = self._extract_hour(text) or 9
            return target.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return None
    
    def _extract_hour(self, text: str) -> Optional[int]:
        """从文本中提取小时"""
        if "早上" in text or "上午" in text:
            if match := re.search(r'(\d{1,2})[点时]', text):
                return int(match.group(1))
            return 9
        
        if "中午" in text:
            return 12
        
        if "下午" in text:
            if match := re.search(r'(\d{1,2})[点时]', text):
                hour = int(match.group(1))
                return hour + 12 if hour < 12 else hour
            return 14
        
        if "晚上" in text:
            if match := re.search(r'(\d{1,2})[点时]', text):
                hour = int(match.group(1))
                return hour + 12 if hour < 12 else hour
            return 19
        
        if match := re.search(r'(\d{1,2})[点时]', text):
            return int(match.group(1))
        
        return None
    
    def create_reminder(
        self,
        title: str,
        content: str,
        remind_time: datetime,
        reminder_type: str = "normal",
        repeat: Optional[str] = None,
        priority: int = 1
    ) -> Dict:
        """
        创建提醒
        
        Args:
            title: 提醒标题
            content: 提醒内容
            remind_time: 提醒时间
            reminder_type: 提醒类型（normal, task, event）
            repeat: 重复规则（daily, weekly, monthly）
            priority: 优先级（1-5）
            
        Returns:
            创建的提醒信息
        """
        reminder = {
            "id": f"RMD-{int(datetime.now().timestamp())}",
            "title": title,
            "content": content,
            "remind_time": remind_time.isoformat(),
            "type": reminder_type,
            "repeat": repeat,
            "priority": priority,
            "status": "active",
            "created_at": datetime.now().isoformat(),
            "notified": False
        }
        
        self.reminders.append(reminder)
        self.save_reminders()
        
        return {
            "success": True,
            "reminder": reminder,
            "message": "提醒已创建"
        }
    
    def create_from_conversation(self, conversation_text: str) -> Dict:
        """
        从对话中智能创建提醒
        
        自动识别时间和任务
        
        Args:
            conversation_text: 对话文本
            
        Returns:
            创建结果
        """
        # 解析时间
        remind_time = self.parse_time_from_text(conversation_text)
        
        if not remind_time:
            return {
                "success": False,
                "message": "无法从文本中识别时间"
            }
        
        # 提取关键内容作为标题
        title = self._extract_task_title(conversation_text)
        
        return self.create_reminder(
            title=title,
            content=conversation_text,
            remind_time=remind_time,
            reminder_type="task"
        )
    
    def _extract_task_title(self, text: str) -> str:
        """提取任务标题"""
        # 简单提取：取前20个字符
        title = text.replace('\n', ' ')[:30]
        if len(text) > 30:
            title += "..."
        return title
    
    def get_pending_reminders(self) -> List[Dict]:
        """
        获取待提醒列表
        
        Returns:
            待提醒列表
        """
        now = datetime.now()
        pending = []
        
        for reminder in self.reminders:
            if reminder["status"] != "active" or reminder["notified"]:
                continue
            
            remind_time = datetime.fromisoformat(reminder["remind_time"])
            if remind_time <= now:
                pending.append(reminder)
        
        # 按优先级和时间排序
        pending.sort(key=lambda x: (-x["priority"], x["remind_time"]))
        
        return pending
    
    def mark_notified(self, reminder_id: str) -> Dict:
        """标记提醒已通知"""
        for reminder in self.reminders:
            if reminder["id"] == reminder_id:
                reminder["notified"] = True
                
                # 如果有重复规则，创建下一次提醒
                if reminder.get("repeat"):
                    next_time = self._calculate_next_time(
                        datetime.fromisoformat(reminder["remind_time"]),
                        reminder["repeat"]
                    )
                    
                    self.create_reminder(
                        title=reminder["title"],
                        content=reminder["content"],
                        remind_time=next_time,
                        reminder_type=reminder["type"],
                        repeat=reminder["repeat"],
                        priority=reminder["priority"]
                    )
                
                self.save_reminders()
                return {
                    "success": True,
                    "message": "已标记为已通知"
                }
        
        return {
            "success": False,
            "message": "提醒不存在"
        }
    
    def _calculate_next_time(self, current_time: datetime, repeat: str) -> datetime:
        """计算下一次提醒时间"""
        if repeat == "daily":
            return current_time + timedelta(days=1)
        elif repeat == "weekly":
            return current_time + timedelta(weeks=1)
        elif repeat == "monthly":
            return current_time + timedelta(days=30)
        else:
            return current_time
    
    def delete_reminder(self, reminder_id: str) -> Dict:
        """删除提醒"""
        original_len = len(self.reminders)
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
        
        if len(self.reminders) < original_len:
            self.save_reminders()
            return {
                "success": True,
                "message": "提醒已删除"
            }
        
        return {
            "success": False,
            "message": "提醒不存在"
        }
    
    def get_all_reminders(self, filter_type: Optional[str] = None) -> List[Dict]:
        """获取所有提醒"""
        if filter_type:
            return [r for r in self.reminders if r["type"] == filter_type]
        return self.reminders
    
    def save_reminders(self):
        """保存提醒到文件"""
        try:
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(self.reminders, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存提醒失败: {e}")
    
    def load_reminders(self):
        """从文件加载提醒"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    self.reminders = json.load(f)
        except Exception as e:
            print(f"加载提醒失败: {e}")
            self.reminders = []
    
    def get_statistics(self) -> Dict:
        """获取提醒统计"""
        total = len(self.reminders)
        active = len([r for r in self.reminders if r["status"] == "active"])
        notified = len([r for r in self.reminders if r["notified"]])
        
        by_type = {}
        for r in self.reminders:
            t = r["type"]
            by_type[t] = by_type.get(t, 0) + 1
        
        return {
            "total": total,
            "active": active,
            "notified": notified,
            "pending": active - notified,
            "by_type": by_type
        }


# 使用示例
if __name__ == "__main__":
    reminder = SmartReminder()
    
    # 测试时间解析
    test_texts = [
        "明天上午10点开会",
        "3天后提交报告",
        "下周五下午3点面试",
        "2025-11-15 14:30 项目评审"
    ]
    
    print("✅ 智能提醒系统已加载\n")
    print("📋 时间解析测试：")
    for text in test_texts:
        parsed_time = reminder.parse_time_from_text(text)
        if parsed_time:
            print(f"  '{text}' → {parsed_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            print(f"  '{text}' → 无法解析")
    
    # 创建提醒示例
    result = reminder.create_reminder(
        title="项目会议",
        content="讨论Q4项目进度",
        remind_time=datetime.now() + timedelta(hours=2),
        reminder_type="event",
        priority=4
    )
    
    print(f"\n✅ 创建提醒: {result['reminder']['title']}")
    print(f"📊 统计: {reminder.get_statistics()}")


