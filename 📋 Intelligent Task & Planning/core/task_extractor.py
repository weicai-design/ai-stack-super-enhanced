"""
任务提炼引擎
从备忘录和聊天内容中提取任务
"""

from typing import Dict, List, Optional, Any
import re

class TaskExtractor:
    """
    任务提炼引擎
    
    功能：
    1. 从备忘录提取任务
    2. 从聊天内容识别任务
    3. 从自我学习系统获取任务建议
    """
    
    def __init__(self, super_agent_integration=None):
        # 任务关键词模式
        self.task_patterns = [
            r"需要(.+?)(?:。|$)",
            r"应该(.+?)(?:。|$)",
            r"记得(.+?)(?:。|$)",
            r"要(.+?)(?:。|$)",
            r"必须(.+?)(?:。|$)",
            r"完成(.+?)(?:。|$)",
            r"处理(.+?)(?:。|$)",
            r"执行(.+?)(?:。|$)",
            r"帮我(.+?)(?:。|$)",
            r"请(.+?)(?:。|$)",
        ]
        
        # 日期模式
        self.date_patterns = [
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",
            r"(\d{1,2}月\d{1,2}日)",
            r"(明天|后天|下周|下周一|下周二|下周三|下周四|下周五|下周六|下周日)",
        ]
        
        self.super_agent_integration = super_agent_integration
    
    def extract_from_text(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取任务
        
        Args:
            text: 输入文本
            
        Returns:
            提取的任务列表
        """
        tasks = []
        
        # 匹配任务模式
        for pattern in self.task_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                task_content = match.group(1).strip()
                if task_content:
                    # 提取日期
                    due_date = self._extract_date(text)
                    
                    tasks.append({
                        "content": task_content,
                        "due_date": due_date,
                        "confidence": 0.7,
                        "source": "text_extraction"
                    })
        
        return tasks
    
    async def extract_from_memos(self, memos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        从备忘录中提取任务
        
        Args:
            memos: 备忘录列表
            
        Returns:
            提取的任务列表
        """
        tasks = []
        
        # 如果提供了超级Agent集成，先同步
        if self.super_agent_integration:
            sync_result = await self.super_agent_integration.sync_with_super_agent(memos)
            if sync_result.get("success"):
                tasks.extend(sync_result.get("tasks", []))
        
        # 从本地备忘录提取
        for memo in memos:
            if memo.get("type") == "task":
                tasks.append({
                    "content": memo.get("content", ""),
                    "importance": memo.get("importance", 3),
                    "tags": memo.get("tags", []),
                    "source": "memo",
                    "source_id": memo.get("id"),
                    "confidence": 0.9
                })
        
        return tasks
    
    def _extract_date(self, text: str) -> Optional[str]:
        """提取日期"""
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return None
    
    def classify_task(self, task_content: str) -> Dict[str, Any]:
        """
        分类任务
        
        Args:
            task_content: 任务内容
            
        Returns:
            分类结果（类型、优先级、标签等）
        """
        # TODO: 使用NLP模型分类任务
        # 简单示例：基于关键词分类
        
        task_type = "general"
        priority = 2
        
        if any(keyword in task_content for keyword in ["紧急", "重要", "立即"]):
            priority = 4
        elif any(keyword in task_content for keyword in ["尽快", "优先"]):
            priority = 3
        
        if any(keyword in task_content for keyword in ["会议", "讨论"]):
            task_type = "meeting"
        elif any(keyword in task_content for keyword in ["报告", "文档"]):
            task_type = "document"
        elif any(keyword in task_content for keyword in ["开发", "编程", "代码"]):
            task_type = "development"
        
        return {
            "type": task_type,
            "priority": priority,
            "tags": self._extract_tags(task_content)
        }
    
    def _extract_tags(self, text: str) -> List[str]:
        """提取标签"""
        tags = []
        
        # 基于关键词提取标签
        tag_keywords = {
            "开发": ["开发", "编程", "代码", "实现"],
            "会议": ["会议", "讨论", "沟通"],
            "文档": ["文档", "报告", "记录"],
            "测试": ["测试", "验证", "检查"],
            "部署": ["部署", "发布", "上线"],
            "紧急": ["紧急", "立即", "马上"],
            "重要": ["重要", "关键", "必须"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags

