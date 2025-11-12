"""
超级Agent主界面API
提供RESTful API接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio

from ..core.super_agent import SuperAgent
from ..core.memo_system import MemoSystem
from ..core.task_planning import TaskPlanning
from ..core.self_learning import SelfLearningMonitor
from ..core.resource_monitor import ResourceMonitor
from ..core.voice_interaction import VoiceInteraction
from ..core.translation import TranslationService
from ..core.file_generation import FileGenerationService
from ..core.web_search import WebSearchService
from ..core.file_format_handler import FileFormatHandler
from ..core.terminal_executor import TerminalExecutor

router = APIRouter(prefix="/api/super-agent", tags=["Super Agent"])

# 初始化服务
super_agent = SuperAgent()
memo_system = MemoSystem()
task_planning = TaskPlanning(memo_system)
learning_monitor = SelfLearningMonitor()
resource_monitor = ResourceMonitor()
voice_interaction = VoiceInteraction()
translation_service = TranslationService()
file_generation = FileGenerationService()
web_search = WebSearchService()
file_format_handler = FileFormatHandler()  # 文件格式处理器
terminal_executor = TerminalExecutor()  # 终端执行器

# 设置依赖
super_agent.set_memo_system(memo_system)
super_agent.set_learning_monitor(learning_monitor)
super_agent.set_resource_monitor(resource_monitor)
super_agent.set_task_planning(task_planning)

# 启动资源监控（后台任务）
import asyncio
asyncio.create_task(resource_monitor.start_monitoring(interval=5))


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str
    input_type: str = "text"  # text, voice, file, search
    context: Optional[Dict] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    success: bool
    response: str
    response_time: float
    rag_retrievals: Optional[Dict] = None
    timestamp: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口⭐优化版（2秒响应目标）
    
    执行完整的AI工作流9步骤
    """
    try:
        # 如果是文件类型，先处理文件
        if request.input_type == "file" and request.context and request.context.get("file_data"):
            file_data = request.context.get("file_data")
            filename = request.context.get("filename", "unknown")
            mime_type = request.context.get("mime_type")
            
            # 处理文件
            file_result = await file_format_handler.process_file(file_data, filename, mime_type)
            
            # 将文件内容添加到用户输入
            if file_result.get("success") and file_result.get("text"):
                request.message = f"{request.message}\n\n文件内容:\n{file_result['text']}"
        
        result = await super_agent.process_user_input(
            user_input=request.message,
            input_type=request.input_type,
            context=request.context
        )
        
        return ChatResponse(
            success=result["success"],
            response=result.get("response", ""),
            response_time=result.get("response_time", 0),
            rag_retrievals=result.get("rag_retrievals"),
            timestamp=result.get("timestamp", "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memos")
async def get_memos(
    type: Optional[str] = None,
    importance: Optional[int] = None,
    tags: Optional[str] = None
):
    """获取备忘录列表"""
    tag_list = tags.split(",") if tags else None
    memos = await memo_system.get_memos(type=type, importance=importance, tags=tag_list)
    return {"memos": memos, "total": len(memos)}


@router.post("/memos")
async def add_memo(memo_data: Dict):
    """添加备忘录"""
    memo = await memo_system.add_memo(memo_data)
    return {"success": True, "memo": memo}


@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    needs_confirmation: Optional[bool] = None
):
    """获取任务列表"""
    tasks = task_planning.get_tasks(status=status, needs_confirmation=needs_confirmation)
    return {"tasks": tasks, "total": len(tasks)}


@router.post("/tasks/extract")
async def extract_tasks():
    """从备忘录提炼任务⭐增强版（使用模板库）"""
    tasks = await task_planning.extract_tasks_from_memos()
    return {"tasks": tasks, "total": len(tasks)}


@router.get("/tasks/templates")
async def get_task_templates():
    """获取任务模板列表"""
    templates = task_planning.template_library.get_all_templates()
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.get("/file-formats/supported")
async def get_supported_formats():
    """获取支持的文件格式列表"""
    formats = file_format_handler.get_supported_formats()
    return {
        "formats": formats,
        "total": len(formats),
        "categories": list(file_format_handler.supported_formats.keys())
    }


@router.post("/tasks/{task_id}/confirm")
async def confirm_task(
    task_id: int,
    request: Dict[str, Any] = Body(...)
):
    """确认任务"""
    confirmed = request.get("confirmed", False)
    reason = request.get("reason")
    result = await task_planning.confirm_task(task_id, confirmed, reason)
    if result:
        return {"success": True, "task": result}
    else:
        raise HTTPException(status_code=404, detail="任务不存在")


@router.post("/tasks/{task_id}/execute")
async def execute_task(task_id: int):
    """执行任务⭐完善版"""
    result = await task_planning.execute_task(task_id)
    if result.get("success"):
        return result
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "任务执行失败"))


@router.get("/tasks/statistics")
async def get_task_statistics():
    """获取任务统计信息⭐增强版"""
    stats = task_planning.get_statistics()
    return stats


@router.get("/resource/status")
async def get_resource_status():
    """获取资源状态"""
    status = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts()
    return {
        "status": status,
        "alerts": alerts,
        "alerts_count": len(alerts)
    }


@router.get("/resource/trends")
async def get_resource_trends(hours: int = 1):
    """获取资源趋势"""
    trends = resource_monitor.get_resource_trends(hours)
    return trends


@router.get("/learning/statistics")
async def get_learning_statistics():
    """获取学习统计信息"""
    stats = learning_monitor.get_statistics()
    return stats


@router.post("/voice/recognize")
async def recognize_voice(
    audio_data: Optional[UploadFile] = File(None),
    audio_text: Optional[str] = None,
    language: Optional[str] = None
):
    """语音识别"""
    audio_bytes = None
    if audio_data:
        audio_bytes = await audio_data.read()
    
    result = await voice_interaction.recognize_speech(
        audio_data=audio_bytes,
        audio_text=audio_text,
        language=language
    )
    return result


@router.post("/voice/synthesize")
async def synthesize_voice(
    text: str,
    language: Optional[str] = None,
    voice: Optional[str] = None,
    speed: float = 1.0,
    pitch: float = 1.0
):
    """语音合成（TTS）"""
    result = await voice_interaction.synthesize_speech(
        text=text,
        language=language,
        voice=voice,
        speed=speed,
        pitch=pitch
    )
    return result


@router.get("/voice/languages")
async def get_voice_languages():
    """获取支持的语音语言列表"""
    languages = voice_interaction.get_supported_languages()
    return {"languages": languages, "current": voice_interaction.current_language}


@router.post("/translate")
async def translate(
    text: str,
    target_lang: str = "zh",
    source_lang: Optional[str] = None
):
    """翻译文本（支持60种语言）"""
    result = await translation_service.translate(text, target_lang, source_lang)
    return result


@router.post("/translate/batch")
async def batch_translate(
    texts: List[str],
    target_lang: str = "zh",
    source_lang: Optional[str] = None
):
    """批量翻译"""
    results = await translation_service.batch_translate(texts, target_lang, source_lang)
    return {"results": results, "count": len(results)}


@router.post("/translate/detect")
async def detect_language(text: str):
    """检测语言"""
    lang = await translation_service.detect_language(text)
    return {"language": lang, "is_supported": translation_service.is_supported(lang)}


@router.get("/translate/languages")
async def get_translation_languages():
    """获取支持的翻译语言列表（60种）"""
    languages = translation_service.get_supported_languages()
    return {
        "languages": languages,
        "count": len(languages),
        "default_target": translation_service.default_target
    }


@router.post("/search")
async def search(
    query: str,
    engine: Optional[str] = None,
    search_type: str = "web",
    max_results: int = 10
):
    """网络搜索（与聊天框合并）"""
    result = await web_search.search(query, engine, search_type, max_results)
    return result


@router.post("/search/multi")
async def multi_search(
    query: str,
    engines: Optional[List[str]] = None,
    search_type: str = "web",
    max_results_per_engine: int = 5
):
    """多引擎搜索并整合结果"""
    result = await web_search.multi_search(
        query, engines, search_type, max_results_per_engine
    )
    return result


@router.get("/search/engines")
async def get_search_engines():
    """获取可用的搜索引擎列表"""
    engines = {
        name: {
            "enabled": config["enabled"],
            "has_api_key": config.get("api_key") is not None
        }
        for name, config in web_search.search_engines.items()
    }
    return {
        "engines": engines,
        "default": web_search.default_engine
    }


@router.post("/generate/file")
async def generate_file(
    file_type: str,  # word, excel, ppt, pdf, image
    content: str,
    template: Optional[str] = None,
    title: Optional[str] = None,
    output_path: Optional[str] = None
):
    """生成文件（Word/Excel/PPT/PDF）"""
    if file_type == "word":
        result = await file_generation.generate_word(content, template, output_path, title)
    elif file_type == "excel":
        # 解析content为数据格式（JSON格式：{"headers": [...], "data": [[...]]}）
        try:
            import json
            content_data = json.loads(content)
            headers = content_data.get("headers")
            data = content_data.get("data", [])
            result = await file_generation.generate_excel(
                data, headers, output_path, content_data.get("sheet_name", "Sheet1")
            )
        except:
            raise HTTPException(status_code=400, detail="Excel内容格式错误，需要JSON格式：{\"headers\": [...], \"data\": [[...]]}")
    elif file_type == "ppt":
        # 解析content为幻灯片格式
        try:
            import json
            slides_data = json.loads(content)
            slides = slides_data.get("slides", [])
            result = await file_generation.generate_ppt(slides, template, output_path)
        except:
            raise HTTPException(status_code=400, detail="PPT内容格式错误")
    elif file_type == "pdf":
        result = await file_generation.generate_pdf(content, template, output_path, title)
    elif file_type == "image":
        result = await file_generation.generate_image(content)
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")
    
    if result.get("success"):
        # 返回base64编码的文件数据
        file_data = result.get("file_data", b"")
        if isinstance(file_data, bytes):
            import base64
            result["file_data_base64"] = base64.b64encode(file_data).decode('utf-8')
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "文件生成失败"))


@router.post("/terminal/execute")
async def execute_terminal_command(
    command: str = Body(..., embed=True),
    timeout: int = Body(30, embed=True),
    cwd: Optional[str] = Body(None, embed=True)
):
    """执行终端命令"""
    result = await terminal_executor.execute_command(
        command=command,
        timeout=timeout,
        cwd=cwd
    )
    return result


@router.get("/terminal/history")
async def get_terminal_history(limit: int = 20):
    """获取终端命令历史"""
    history = terminal_executor.get_command_history(limit=limit)
    return {"history": history}


@router.get("/terminal/system-info")
async def get_terminal_system_info():
    """获取系统信息"""
    info = terminal_executor.get_system_info()
    return info


@router.post("/terminal/cd")
async def change_terminal_directory(path: str = Body(..., embed=True)):
    """切换终端工作目录"""
    result = terminal_executor.change_directory(path)
    return result


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "super_agent": True,
            "memo_system": True,
            "task_planning": True,
            "learning_monitor": True,
            "resource_monitor": True,
            "voice_interaction": True,
            "translation": True,
            "file_generation": True,
            "web_search": True,
            "file_format_handler": True,
            "terminal_executor": True
        }
    }

