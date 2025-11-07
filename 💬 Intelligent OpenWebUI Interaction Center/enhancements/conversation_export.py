"""
对话历史导出模块
支持多种格式：Markdown, JSON, HTML, TXT
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from context_memory_manager import ContextMemoryManager


class ConversationExporter:
    """对话历史导出器"""
    
    def __init__(self, memory_manager: ContextMemoryManager):
        self.memory_manager = memory_manager
    
    def export_to_markdown(
        self, 
        session_id: str, 
        include_metadata: bool = False
    ) -> str:
        """
        导出为Markdown格式
        
        Args:
            session_id: 会话ID
            include_metadata: 是否包含元数据
        
        Returns:
            Markdown格式的文本
        """
        # 获取会话信息
        summary = self.memory_manager.get_session_summary(session_id)
        history = self.memory_manager.get_conversation_history(session_id, limit=1000)
        
        # 构建Markdown
        lines = []
        
        # 标题
        lines.append(f"# 对话历史记录\n")
        
        # 会话信息
        if summary:
            lines.append(f"## 📊 会话信息\n")
            lines.append(f"- **会话ID**: `{session_id}`")
            lines.append(f"- **标题**: {summary.get('title', '无标题')}")
            lines.append(f"- **开始时间**: {summary.get('start_time', 'N/A')}")
            lines.append(f"- **最后活动**: {summary.get('last_active', 'N/A')}")
            lines.append(f"- **总消息数**: {summary.get('total_messages', 0)}条")
            lines.append(f"- **总字数**: {summary.get('total_words', 0):,}字")
            
            if summary.get('summary'):
                lines.append(f"- **摘要**: {summary['summary']}")
            
            if summary.get('key_topics'):
                topics = ", ".join(summary['key_topics'][:10])
                lines.append(f"- **关键主题**: {topics}")
            
            lines.append("")
        
        # 对话内容
        lines.append(f"## 💬 对话内容\n")
        lines.append(f"---\n")
        
        for msg in history:
            role = msg['role']
            content = msg['content']
            timestamp = msg['timestamp']
            
            # 角色标识
            if role == 'user':
                role_icon = "👤 **用户**"
            elif role == 'assistant':
                role_icon = "🤖 **AI助手**"
            else:
                role_icon = "⚙️ **系统**"
            
            # 时间戳
            time_str = timestamp[:19] if len(timestamp) >= 19 else timestamp
            
            lines.append(f"### {role_icon} · {time_str}\n")
            lines.append(f"{content}\n")
            
            # 元数据（可选）
            if include_metadata and msg.get('metadata'):
                metadata = msg['metadata']
                if metadata:
                    lines.append(f"<details>")
                    lines.append(f"<summary>📋 元数据</summary>\n")
                    lines.append(f"```json")
                    lines.append(json.dumps(metadata, indent=2, ensure_ascii=False))
                    lines.append(f"```")
                    lines.append(f"</details>\n")
            
            lines.append(f"---\n")
        
        # 页脚
        lines.append(f"\n---")
        lines.append(f"\n*导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        lines.append(f"\n*由 AI Stack 智能对话中心生成*")
        
        return "\n".join(lines)
    
    def export_to_json(
        self, 
        session_id: str, 
        pretty: bool = True
    ) -> str:
        """
        导出为JSON格式
        
        Args:
            session_id: 会话ID
            pretty: 是否格式化
        
        Returns:
            JSON格式的文本
        """
        summary = self.memory_manager.get_session_summary(session_id)
        history = self.memory_manager.get_conversation_history(session_id, limit=1000)
        
        export_data = {
            "session_id": session_id,
            "export_time": datetime.now().isoformat(),
            "summary": summary,
            "messages": history,
            "statistics": {
                "total_messages": len(history),
                "total_words": sum(msg.get('word_count', 0) for msg in history),
                "user_messages": sum(1 for msg in history if msg['role'] == 'user'),
                "assistant_messages": sum(1 for msg in history if msg['role'] == 'assistant')
            }
        }
        
        if pretty:
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        else:
            return json.dumps(export_data, ensure_ascii=False)
    
    def export_to_html(self, session_id: str) -> str:
        """
        导出为HTML格式（可打印）
        
        Args:
            session_id: 会话ID
        
        Returns:
            HTML格式的文本
        """
        summary = self.memory_manager.get_session_summary(session_id)
        history = self.memory_manager.get_conversation_history(session_id, limit=1000)
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>对话历史 - {session_id}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #667eea;
            margin-bottom: 30px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .summary {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }}
        .summary-item {{
            margin: 5px 0;
        }}
        .message {{
            margin: 20px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ddd;
        }}
        .message-user {{
            background: #e3f2fd;
            border-left-color: #2196F3;
        }}
        .message-assistant {{
            background: #f3e5f5;
            border-left-color: #9c27b0;
        }}
        .message-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            font-weight: 600;
        }}
        .message-role {{
            font-size: 16px;
        }}
        .message-time {{
            font-size: 12px;
            color: #666;
        }}
        .message-content {{
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 14px;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📝 对话历史记录</h1>
        
        <div class="summary">
            <h2>📊 会话信息</h2>
"""
        
        # 添加会话信息
        if summary:
            html += f"""
            <div class="summary-item"><strong>会话ID:</strong> {session_id}</div>
            <div class="summary-item"><strong>标题:</strong> {summary.get('title', '无标题')}</div>
            <div class="summary-item"><strong>开始时间:</strong> {summary.get('start_time', 'N/A')}</div>
            <div class="summary-item"><strong>最后活动:</strong> {summary.get('last_active', 'N/A')}</div>
            <div class="summary-item"><strong>总消息数:</strong> {summary.get('total_messages', 0)}条</div>
            <div class="summary-item"><strong>总字数:</strong> {summary.get('total_words', 0):,}字</div>
"""
            if summary.get('summary'):
                html += f"""
            <div class="summary-item"><strong>摘要:</strong> {summary['summary']}</div>
"""
        
        html += """
        </div>
        
        <h2>💬 对话内容</h2>
"""
        
        # 添加对话内容
        for msg in history:
            role = msg['role']
            content = msg['content'].replace('<', '&lt;').replace('>', '&gt;')
            timestamp = msg['timestamp'][:19] if len(msg['timestamp']) >= 19 else msg['timestamp']
            
            if role == 'user':
                role_text = "👤 用户"
                css_class = "message-user"
            elif role == 'assistant':
                role_text = "🤖 AI助手"
                css_class = "message-assistant"
            else:
                role_text = "⚙️ 系统"
                css_class = "message"
            
            html += f"""
        <div class="message {css_class}">
            <div class="message-header">
                <span class="message-role">{role_text}</span>
                <span class="message-time">{timestamp}</span>
            </div>
            <div class="message-content">{content}</div>
        </div>
"""
        
        # 页脚
        html += f"""
        <div class="footer">
            <p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>由 AI Stack 智能对话中心生成</p>
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def export_to_txt(self, session_id: str) -> str:
        """
        导出为纯文本格式
        
        Args:
            session_id: 会话ID
        
        Returns:
            纯文本格式
        """
        summary = self.memory_manager.get_session_summary(session_id)
        history = self.memory_manager.get_conversation_history(session_id, limit=1000)
        
        lines = []
        
        # 标题
        lines.append("=" * 60)
        lines.append("对话历史记录".center(56))
        lines.append("=" * 60)
        lines.append("")
        
        # 会话信息
        if summary:
            lines.append("会话信息:")
            lines.append(f"  会话ID: {session_id}")
            lines.append(f"  标题: {summary.get('title', '无标题')}")
            lines.append(f"  开始时间: {summary.get('start_time', 'N/A')}")
            lines.append(f"  最后活动: {summary.get('last_active', 'N/A')}")
            lines.append(f"  总消息数: {summary.get('total_messages', 0)}条")
            lines.append(f"  总字数: {summary.get('total_words', 0):,}字")
            if summary.get('summary'):
                lines.append(f"  摘要: {summary['summary']}")
            lines.append("")
        
        # 对话内容
        lines.append("-" * 60)
        lines.append("对话内容:")
        lines.append("-" * 60)
        lines.append("")
        
        for msg in history:
            role = msg['role']
            content = msg['content']
            timestamp = msg['timestamp'][:19] if len(msg['timestamp']) >= 19 else msg['timestamp']
            
            if role == 'user':
                role_text = "[用户]"
            elif role == 'assistant':
                role_text = "[AI助手]"
            else:
                role_text = "[系统]"
            
            lines.append(f"{role_text} {timestamp}")
            lines.append(content)
            lines.append("")
        
        # 页脚
        lines.append("-" * 60)
        lines.append(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("由 AI Stack 智能对话中心生成")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# 全局实例（在需要时创建）
_exporter_instance = None

def get_exporter(memory_manager: ContextMemoryManager = None) -> ConversationExporter:
    """获取导出器实例"""
    global _exporter_instance
    if _exporter_instance is None and memory_manager:
        _exporter_instance = ConversationExporter(memory_manager)
    return _exporter_instance

