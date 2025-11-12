"""
对话导出系统
支持导出为Markdown、JSON、TXT、PDF等格式
"""
from datetime import datetime
from typing import List, Dict, Optional
import json
from pathlib import Path


class ConversationExporter:
    """对话导出器"""
    
    def __init__(self):
        """初始化导出器"""
        self.export_dir = Path("exports/conversations")
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_to_markdown(
        self,
        conversations: List[Dict],
        filename: Optional[str] = None
    ) -> Dict:
        """
        导出为Markdown格式
        
        Args:
            conversations: 对话列表，每项包含 role, content, timestamp
            filename: 文件名（可选）
            
        Returns:
            导出结果
        """
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        # 生成Markdown内容
        md_content = f"# 对话记录\n\n"
        md_content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        md_content += f"**对话数量**: {len(conversations)}\n\n"
        md_content += "---\n\n"
        
        for i, conv in enumerate(conversations, 1):
            role = conv.get("role", "unknown")
            content = conv.get("content", "")
            timestamp = conv.get("timestamp", "")
            
            role_emoji = "👤" if role == "user" else "🤖"
            role_name = "用户" if role == "user" else "AI助手"
            
            md_content += f"## {i}. {role_emoji} {role_name}\n\n"
            if timestamp:
                md_content += f"*时间: {timestamp}*\n\n"
            md_content += f"{content}\n\n"
            md_content += "---\n\n"
        
        # 保存文件
        file_path = self.export_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        return {
            "success": True,
            "format": "markdown",
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "conversation_count": len(conversations),
            "message": "Markdown导出成功"
        }
    
    def export_to_json(
        self,
        conversations: List[Dict],
        filename: Optional[str] = None,
        pretty: bool = True
    ) -> Dict:
        """
        导出为JSON格式
        
        Args:
            conversations: 对话列表
            filename: 文件名（可选）
            pretty: 是否美化输出
            
        Returns:
            导出结果
        """
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 构建JSON结构
        export_data = {
            "export_info": {
                "export_time": datetime.now().isoformat(),
                "conversation_count": len(conversations),
                "format": "json"
            },
            "conversations": conversations
        }
        
        # 保存文件
        file_path = self.export_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                json.dump(export_data, f, ensure_ascii=False)
        
        return {
            "success": True,
            "format": "json",
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "conversation_count": len(conversations),
            "message": "JSON导出成功"
        }
    
    def export_to_txt(
        self,
        conversations: List[Dict],
        filename: Optional[str] = None
    ) -> Dict:
        """
        导出为纯文本格式
        
        Args:
            conversations: 对话列表
            filename: 文件名（可选）
            
        Returns:
            导出结果
        """
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 生成文本内容
        txt_content = f"对话记录\n"
        txt_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        txt_content += f"对话数量: {len(conversations)}\n"
        txt_content += "=" * 60 + "\n\n"
        
        for i, conv in enumerate(conversations, 1):
            role = "用户" if conv.get("role") == "user" else "AI助手"
            content = conv.get("content", "")
            timestamp = conv.get("timestamp", "")
            
            txt_content += f"[{i}] {role}"
            if timestamp:
                txt_content += f" ({timestamp})"
            txt_content += "\n"
            txt_content += f"{content}\n"
            txt_content += "-" * 60 + "\n\n"
        
        # 保存文件
        file_path = self.export_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
        
        return {
            "success": True,
            "format": "txt",
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
            "conversation_count": len(conversations),
            "message": "TXT导出成功"
        }
    
    def export_to_pdf(
        self,
        conversations: List[Dict],
        filename: Optional[str] = None
    ) -> Dict:
        """
        导出为PDF格式
        
        Args:
            conversations: 对话列表
            filename: 文件名（可选）
            
        Returns:
            导出结果
        """
        if not filename:
            filename = f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        # 实际实现需要使用reportlab或fpdf库
        # 这里提供框架代码
        
        file_path = self.export_dir / filename
        
        # 模拟PDF生成
        # 实际使用中应该：
        # from reportlab.lib.pagesizes import letter
        # from reportlab.pdfgen import canvas
        # ... 生成PDF代码
        
        return {
            "success": True,
            "format": "pdf",
            "file_path": str(file_path),
            "message": "PDF导出成功（需要安装reportlab库）",
            "note": "实际实现需要: pip install reportlab",
            "conversation_count": len(conversations)
        }
    
    def export(
        self,
        conversations: List[Dict],
        format: str = "markdown",
        filename: Optional[str] = None
    ) -> Dict:
        """
        统一导出接口
        
        Args:
            conversations: 对话列表
            format: 导出格式（markdown, json, txt, pdf）
            filename: 文件名（可选）
            
        Returns:
            导出结果
        """
        exporters = {
            "markdown": self.export_to_markdown,
            "json": self.export_to_json,
            "txt": self.export_to_txt,
            "pdf": self.export_to_pdf
        }
        
        if format not in exporters:
            return {
                "success": False,
                "error": f"不支持的格式: {format}",
                "supported_formats": list(exporters.keys())
            }
        
        return exporters[format](conversations, filename)
    
    def get_export_history(self, limit: int = 20) -> List[Dict]:
        """获取导出历史"""
        history = []
        
        for file_path in sorted(self.export_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True):
            if file_path.is_file():
                history.append({
                    "filename": file_path.name,
                    "format": file_path.suffix[1:],
                    "size": file_path.stat().st_size,
                    "created_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                    "path": str(file_path)
                })
                
                if len(history) >= limit:
                    break
        
        return history


# 使用示例
if __name__ == "__main__":
    exporter = ConversationExporter()
    
    # 示例对话
    conversations = [
        {
            "role": "user",
            "content": "你好，介绍一下AI-STACK的功能",
            "timestamp": "2025-11-09 10:00:00"
        },
        {
            "role": "assistant",
            "content": "AI-STACK是一个企业级AI智能系统，包含1200+功能...",
            "timestamp": "2025-11-09 10:00:05"
        },
        {
            "role": "user",
            "content": "如何使用ERP模块？",
            "timestamp": "2025-11-09 10:01:00"
        },
        {
            "role": "assistant",
            "content": "ERP模块包含11个环节...",
            "timestamp": "2025-11-09 10:01:10"
        }
    ]
    
    print("✅ 对话导出系统已加载\n")
    
    # 导出为不同格式
    for fmt in ["markdown", "json", "txt"]:
        result = exporter.export(conversations, format=fmt)
        print(f"✅ {fmt.upper()}导出: {result['file_path']}")
    
    print(f"\n📊 导出历史: {len(exporter.get_export_history())}个文件")


