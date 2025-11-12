"""
AI编程助手API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from ..core.code_generator import CodeGenerator
from ..core.code_reviewer import CodeReviewer
from ..core.code_optimizer import CodeOptimizer
from ..core.bug_fixer import BugFixer
from ..core.cursor_integration import CursorIntegration

router = APIRouter(prefix="/api/coding-assistant", tags=["Coding Assistant"])

# 初始化服务
code_generator = CodeGenerator(model="gpt-4")  # 使用GPT-4生成代码
code_reviewer = CodeReviewer()
code_optimizer = CodeOptimizer()
bug_fixer = BugFixer()
cursor_integration = CursorIntegration()


class GenerateCodeRequest(BaseModel):
    """生成代码请求"""
    description: str
    language: str = "python"
    code_type: str = "function"


@router.post("/generate")
async def generate_code(request: GenerateCodeRequest):
    """生成代码"""
    result = await code_generator.generate_code(
        description=request.description,
        language=request.language,
        code_type=request.code_type
    )
    return result


@router.post("/review")
async def review_code(code: str, language: str = "python"):
    """审查代码"""
    result = await code_reviewer.review_code(code, language)
    return result


@router.post("/optimize")
async def optimize_code(problem_description: str, context: Optional[Dict] = None):
    """
    优化代码（被超级Agent调用）
    
    这是超级Agent自动调用编程助手优化代码的核心接口
    """
    result = await code_optimizer.optimize_performance(problem_description, context)
    return result


@router.get("/cursor/status")
async def get_cursor_status():
    """获取Cursor状态"""
    status = cursor_integration.get_status()
    return status


@router.post("/cursor/open")
async def open_in_cursor(file_path: str, line_number: Optional[int] = None):
    """在Cursor中打开文件"""
    result = await cursor_integration.cursor_bridge.open_in_cursor(file_path, line_number)
    return result


@router.post("/cursor/edit")
async def edit_code_in_cursor(
    file_path: str,
    edits: List[Dict[str, Any]],
    open_in_cursor: bool = True
):
    """
    在Cursor中编辑代码
    
    Args:
        file_path: 文件路径
        edits: 编辑操作列表 [{"type": "replace/insert/delete", "start_line": 1, "end_line": 2, "content": "..."}]
        open_in_cursor: 是否在Cursor中打开文件
    """
    result = await cursor_integration.edit_code(file_path, edits, open_in_cursor=open_in_cursor)
    return result


@router.get("/cursor/completions")
async def get_code_completions(
    file_path: str,
    line_number: int,
    column: int,
    context_lines: int = 5
):
    """获取代码补全建议"""
    result = await cursor_integration.get_completions(file_path, line_number, column, context_lines)
    return result


@router.get("/cursor/errors")
async def check_code_errors(file_path: str):
    """检测代码错误"""
    result = await cursor_integration.check_errors(file_path)
    return result


@router.post("/cursor/sync-project")
async def sync_project_to_cursor(
    project_path: str,
    files: Optional[List[str]] = None
):
    """同步项目到Cursor"""
    result = await cursor_integration.sync_project(project_path, files)
    return result


@router.get("/cursor/preview")
async def preview_code(
    file_path: str,
    start_line: int = 1,
    end_line: Optional[int] = None,
    highlight_line: Optional[int] = None
):
    """预览代码"""
    result = await cursor_integration.preview_code(file_path, start_line, end_line, highlight_line)
    return result


@router.get("/cursor/history")
async def get_edit_history(file_path: Optional[str] = None):
    """获取编辑历史"""
    history = cursor_integration.get_edit_history(file_path)
    return {"history": history, "count": len(history)}


@router.post("/fix-bug")
async def fix_bug(code: str, bug_description: str, language: str = "python"):
    """修复Bug"""
    result = await bug_fixer.fix_bug(code, bug_description, language)
    return result

