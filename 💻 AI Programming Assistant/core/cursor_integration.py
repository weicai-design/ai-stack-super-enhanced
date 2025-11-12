"""
Cursor集成（完善版）
完整的Cursor IDE集成功能
"""

from typing import Dict, List, Optional, Any
import asyncio
from .cursor_bridge import CursorBridge

class CursorIntegration:
    """
    Cursor集成（完善版）
    
    功能：
    1. Cursor API调用
    2. 项目同步机制
    3. 代码编辑桥接（插入、删除、替换）
    4. 实时预览
    5. 代码补全建议
    6. 错误检测
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.enabled = api_key is not None
        self.cursor_bridge = CursorBridge()
        self.edit_history = []  # 编辑历史
    
    async def edit_code(
        self,
        file_path: str,
        edits: List[Dict[str, Any]],
        project_path: Optional[str] = None,
        open_in_cursor: bool = True
    ) -> Dict[str, Any]:
        """
        编辑代码（完善版）
        
        Args:
            file_path: 文件路径
            edits: 编辑操作列表 [{"type": "replace/insert/delete", "start_line": 1, "end_line": 2, "content": "..."}]
            project_path: 项目路径
            open_in_cursor: 是否在Cursor中打开文件
            
        Returns:
            编辑结果
        """
        if not self.cursor_bridge.cursor_installed:
            return {
                "success": False,
                "error": "Cursor未安装",
                "suggestion": "请先安装Cursor编辑器"
            }
        
        # 应用编辑
        edit_result = await self.cursor_bridge.edit_code(file_path, edits)
        
        if not edit_result["success"]:
            return edit_result
        
        # 记录编辑历史
        self.edit_history.append({
            "file_path": file_path,
            "edits": edits,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 限制历史记录数量
        if len(self.edit_history) > 100:
            self.edit_history = self.edit_history[-100:]
        
        # 在Cursor中打开文件（如果需要）
        if open_in_cursor:
            open_result = await self.cursor_bridge.open_in_cursor(file_path)
            edit_result["cursor_opened"] = open_result.get("success", False)
        
        return edit_result
    
    async def get_completions(
        self,
        file_path: str,
        line_number: int,
        column: int,
        context_lines: int = 5
    ) -> Dict[str, Any]:
        """
        获取代码补全建议
        
        Args:
            file_path: 文件路径
            line_number: 行号
            column: 列号
            context_lines: 上下文行数
            
        Returns:
            补全建议
        """
        return await self.cursor_bridge.get_code_completion(
            file_path, line_number, column, context_lines
        )
    
    async def check_errors(
        self,
        file_path: str
    ) -> Dict[str, Any]:
        """
        检测代码错误
        
        Args:
            file_path: 文件路径
            
        Returns:
            错误列表
        """
        return await self.cursor_bridge.detect_errors(file_path)
    
    async def sync_project(
        self,
        project_path: str,
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        同步项目到Cursor
        
        Args:
            project_path: 项目路径
            files: 要同步的文件列表
            
        Returns:
            同步结果
        """
        return await self.cursor_bridge.sync_project(project_path, files)
    
    async def preview_code(
        self,
        file_path: str,
        start_line: int = 1,
        end_line: Optional[int] = None,
        highlight_line: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        预览代码（实时预览）
        
        Args:
            file_path: 文件路径
            start_line: 起始行号
            end_line: 结束行号
            highlight_line: 高亮行号
            
        Returns:
            预览结果
        """
        try:
            import os
            
            if not os.path.exists(file_path):
                return {
                    "success": False,
                    "error": "文件不存在"
                }
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 提取指定范围
            start_idx = max(0, start_line - 1)
            end_idx = min(len(lines), end_line) if end_line else len(lines)
            preview_lines = lines[start_idx:end_idx]
            
            return {
                "success": True,
                "file_path": file_path,
                "preview": ''.join(preview_lines),
                "start_line": start_line,
                "end_line": end_idx,
                "highlight_line": highlight_line,
                "total_lines": len(lines)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_edit_history(self, file_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取编辑历史
        
        Args:
            file_path: 文件路径（可选，None表示所有文件）
            
        Returns:
            编辑历史列表
        """
        if file_path:
            return [h for h in self.edit_history if h["file_path"] == file_path]
        return self.edit_history
    
    def get_status(self) -> Dict[str, Any]:
        """获取Cursor集成状态"""
        bridge_status = self.cursor_bridge.get_status()
        return {
            **bridge_status,
            "integration_enabled": self.enabled,
            "edit_history_count": len(self.edit_history)
        }

