"""
备忘录系统
自动识别重要信息并存储
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json

class MemoSystem:
    """
    备忘录系统
    
    功能：
    1. 自动识别重要信息（任务、日期、联系人等）
    2. 存储和管理备忘录
    3. 与智能工作计划联动
    """
    
    def __init__(self, storage_path: str = "memos.db"):
        self.storage_path = storage_path
        self.memos = []
        self._load_memos()
        
    async def add_memo(self, memo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        添加备忘录⭐增强版
        
        Args:
            memo_data: 备忘录数据
                - title: 标题（可选）
                - content: 内容
                - type: 类型（task, date, contact, note等）
                - importance: 重要性（1-5）
                - tags: 标签列表
                - dates: 日期列表
                - times: 时间列表
                - contacts: 联系人列表
        """
        memo = {
            "id": len(self.memos) + 1,
            "title": memo_data.get("title", memo_data.get("content", "")[:30]),
            "content": memo_data.get("content", ""),
            "type": memo_data.get("type", "note"),
            "importance": memo_data.get("importance", 3),
            "tags": memo_data.get("tags", []),
            "dates": memo_data.get("dates", []),
            "times": memo_data.get("times", []),
            "contacts": memo_data.get("contacts", []),
            "metadata": memo_data.get("metadata", {}),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.memos.append(memo)
        await self._save_memos()
        
        return memo
    
    async def extract_important_info(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取重要信息
        
        Args:
            text: 输入文本
            
        Returns:
            提取的重要信息列表
        """
        important_info = []
        
        # TODO: 使用NLP模型识别重要信息
        # 1. 识别任务（"需要"、"应该"、"记得"等关键词）
        # 2. 识别日期（"明天"、"下周一"、"2025-11-15"等）
        # 3. 识别联系人（人名、邮箱、电话等）
        # 4. 识别重要事件（会议、截止日期等）
        
        # 简单示例：识别任务
        task_keywords = ["需要", "应该", "记得", "要", "必须", "完成"]
        for keyword in task_keywords:
            if keyword in text:
                important_info.append({
                    "type": "task",
                    "content": text,
                    "importance": 4,
                    "tags": ["任务"]
                })
                break
        
        return important_info
    
    async def get_memos(
        self,
        type: Optional[str] = None,
        importance: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """获取备忘录"""
        filtered = self.memos
        
        if type:
            filtered = [m for m in filtered if m.get("type") == type]
        
        if importance:
            filtered = [m for m in filtered if m.get("importance") >= importance]
        
        if tags:
            filtered = [m for m in filtered if any(tag in m.get("tags", []) for tag in tags)]
        
        return filtered
    
    async def update_memo(self, memo_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新备忘录"""
        for memo in self.memos:
            if memo["id"] == memo_id:
                memo.update(updates)
                memo["updated_at"] = datetime.now().isoformat()
                await self._save_memos()
                return memo
        return None
    
    async def delete_memo(self, memo_id: int) -> bool:
        """删除备忘录"""
        for i, memo in enumerate(self.memos):
            if memo["id"] == memo_id:
                self.memos.pop(i)
                await self._save_memos()
                return True
        return False
    
    async def _save_memos(self):
        """保存备忘录到文件"""
        # TODO: 实现持久化存储
        pass
    
    def _load_memos(self):
        """从文件加载备忘录"""
        # TODO: 实现从文件加载
        pass

