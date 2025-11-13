"""
超级Agent主界面API
提供RESTful API接口
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import asyncio
import time
from datetime import datetime

import sys
from pathlib import Path

# 添加项目根目录到路径（如果还没有）
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.super_agent import SuperAgent
from core.memo_system import MemoSystem
from core.task_planning import TaskPlanning
from core.self_learning import SelfLearningMonitor
from core.resource_monitor import ResourceMonitor
from core.resource_auto_adjuster import ResourceAutoAdjuster
from core.voice_interaction import VoiceInteraction
from core.translation import TranslationService
from core.file_generation import FileGenerationService
from core.web_search import WebSearchService
from core.file_format_handler import FileFormatHandler
from core.terminal_executor import TerminalExecutor
from core.performance_monitor import performance_monitor, response_time_optimizer
from core.llm_service import get_llm_service, LLMProvider

router = APIRouter(prefix="/api/super-agent", tags=["Super Agent"])

# 初始化服务
super_agent = SuperAgent()
memo_system = MemoSystem()
task_planning = TaskPlanning(memo_system)
learning_monitor = SelfLearningMonitor(resource_manager=None)
resource_monitor = ResourceMonitor()
resource_adjuster = ResourceAutoAdjuster(resource_manager=None)  # 资源自动调节器
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
        
        # 使用性能优化器执行（带超时和缓存）
        start_time = time.time()
        
        # 创建异步函数
        async def process_input():
            return await super_agent.process_user_input(
                user_input=request.message,
                input_type=request.input_type,
                context=request.context
            )
        
        result = await response_time_optimizer.optimize_with_timeout(
            process_input,
            timeout=8.0,  # 优化：减少超时到8秒（优化后应该更快）
            cache_key=f"chat:{request.message}:{request.input_type}" if len(request.message) < 200 else None
        )
        
        # 确保result不为None
        if result is None:
            result = {
                "success": False,
                "response": "处理超时，请稍后重试",
                "response_time": 2.0,
                "rag_retrievals": None,
                "timestamp": datetime.now().isoformat()
            }
        
        # 记录响应时间
        response_time = time.time() - start_time
        performance_monitor.record_response_time(response_time, from_cache=result.get("from_cache", False) if result else False)
        
        return ChatResponse(
            success=result.get("success", False) if result else False,
            response=result.get("response", "") if result else "",
            response_time=response_time,
            rag_retrievals=result.get("rag_retrievals") if result else None,
            timestamp=result.get("timestamp", datetime.now().isoformat()) if result else datetime.now().isoformat()
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


@router.get("/plans")
async def get_plans():
    """获取工作计划列表"""
    plans = task_planning.plans
    return {"plans": plans, "total": len(plans)}


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: int):
    """获取工作计划详情"""
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if plan:
        return {"success": True, "plan": plan}
    else:
        raise HTTPException(status_code=404, detail="计划不存在")


@router.post("/plans/{plan_id}/confirm")
async def confirm_plan(
    plan_id: int,
    request: Dict[str, Any] = Body(...)
):
    """确认工作计划⭐增强版"""
    confirmed = request.get("confirmed", False)
    adjustments = request.get("adjustments", {})  # 用户调整
    
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    
    if confirmed:
        plan["status"] = "confirmed"
        plan["confirmed_at"] = datetime.now().isoformat()
        plan["needs_confirmation"] = False
        
        # 应用用户调整
        if adjustments:
            # 调整任务顺序
            if "task_order" in adjustments:
                task_order = adjustments["task_order"]
                plan["tasks"] = [t for _, t in sorted(zip(task_order, plan["tasks"]), key=lambda x: x[0])]
            
            # 调整任务优先级
            if "task_priorities" in adjustments:
                for task_id, priority in adjustments["task_priorities"].items():
                    task = next((t for t in plan["tasks"] if t["id"] == task_id), None)
                    if task:
                        task["priority"] = priority
            
            # 重新计算计划
            plan["total_duration_minutes"] = sum(t.get("estimated_duration", 0) for t in plan["tasks"])
            plan["estimated_completion_time"] = task_planning._estimate_completion_time(plan["tasks"])
    else:
        plan["status"] = "rejected"
        plan["rejected_at"] = datetime.now().isoformat()
        plan["rejection_reason"] = request.get("reason", "用户拒绝")
    
    return {"success": True, "plan": plan}


@router.post("/plans/{plan_id}/execute")
async def execute_plan(plan_id: int):
    """执行工作计划"""
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    
    if plan["status"] != "confirmed":
        raise HTTPException(status_code=400, detail="计划未确认")
    
    # 按顺序执行任务
    execution_results = []
    for task in plan["tasks"]:
        if task.get("status") == "pending":
            result = await task_planning.execute_task(task["id"])
            execution_results.append(result)
            
            if not result.get("success"):
                # 任务失败，停止执行
                break
    
    return {
        "success": True,
        "plan_id": plan_id,
        "execution_results": execution_results,
        "completed_tasks": len([r for r in execution_results if r.get("success")])
    }


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


@router.get("/workflow/statistics")
async def get_workflow_statistics():
    """获取工作流统计信息"""
    stats = super_agent.workflow_monitor.get_statistics() if super_agent.workflow_monitor else {}
    return stats


@router.get("/workflow/recent")
async def get_recent_workflows(limit: int = 10):
    """获取最近的工作流记录"""
    workflows = super_agent.workflow_monitor.get_recent_workflows(limit) if super_agent.workflow_monitor else []
    return {"workflows": workflows, "count": len(workflows)}


@router.get("/resource/adjuster/statistics")
async def get_resource_adjuster_statistics():
    """获取资源自动调节统计信息"""
    stats = resource_adjuster.get_statistics()
    return stats


@router.post("/resource/adjuster/monitor")
async def monitor_resources():
    """监控资源并检测问题"""
    issues = await resource_adjuster.monitor_resources()
    return {"issues": [{
        "type": issue.issue_type.value,
        "severity": issue.severity,
        "description": issue.description,
        "current_value": issue.current_value,
        "threshold": issue.threshold,
        "affected_modules": issue.affected_modules,
        "detected_at": issue.detected_at.isoformat()
    } for issue in issues], "count": len(issues)}


@router.post("/resource/adjuster/analyze")
async def analyze_resource_issue(issue_type: str, severity: str):
    """分析资源问题并生成调节建议"""
    # 查找匹配的问题
    matching_issues = [
        issue for issue in resource_adjuster.issues[-100:]
        if issue.issue_type.value == issue_type and issue.severity == severity
    ]
    
    if not matching_issues:
        return {"suggestions": [], "message": "未找到匹配的问题"}
    
    issue = matching_issues[-1]  # 使用最新的问题
    suggestions = await resource_adjuster.analyze_issue(issue)
    
    return {
        "suggestions": [{
            "action": suggestion.action.value,
            "description": suggestion.description,
            "expected_impact": suggestion.expected_impact,
            "risk_level": suggestion.risk_level,
            "requires_approval": suggestion.requires_approval,
            "estimated_improvement": suggestion.estimated_improvement
        } for suggestion in suggestions],
        "count": len(suggestions)
    }


@router.post("/resource/adjuster/execute")
async def execute_adjustment(
    action: str,
    description: str,
    approved: bool = False
):
    """执行资源调节动作"""
    # 查找匹配的建议
    matching_suggestions = [
        s for s in resource_adjuster.suggestions[-100:]
        if s.action.value == action and s.description == description
    ]
    
    if not matching_suggestions:
        return {"success": False, "message": "未找到匹配的建议"}
    
    suggestion = matching_suggestions[-1]
    result = await resource_adjuster.execute_adjustment(suggestion, approved=approved)
    
    return result


@router.post("/resource/adjuster/enable")
async def enable_auto_adjust(threshold: str = "medium"):
    """启用资源自动调节"""
    resource_adjuster.enable_auto_adjust(threshold)
    return {"success": True, "message": f"已启用自动调节，阈值：{threshold}"}


@router.post("/resource/adjuster/disable")
async def disable_auto_adjust():
    """禁用资源自动调节"""
    resource_adjuster.disable_auto_adjust()
    return {"success": True, "message": "已禁用自动调节"}


@router.get("/learning/workflow-statistics")
async def get_learning_workflow_statistics():
    """获取学习系统工作流统计"""
    stats = learning_monitor.get_workflow_statistics() if hasattr(learning_monitor, 'get_workflow_statistics') else {}
    return stats


@router.get("/learning/resource-statistics")
async def get_learning_resource_statistics():
    """获取学习系统资源统计"""
    stats = learning_monitor.get_resource_statistics() if hasattr(learning_monitor, 'get_resource_statistics') else {}
    return stats


@router.get("/performance/stats")
async def get_performance_stats():
    """获取性能统计信息（2秒响应监控）"""
    stats = performance_monitor.get_performance_stats()
    return {
        "success": True,
        **stats
    }


@router.get("/performance/slow-queries")
async def get_slow_queries(limit: int = 10):
    """获取慢查询列表"""
    slow_queries = performance_monitor.get_slow_queries(limit)
    return {
        "success": True,
        "slow_queries": slow_queries,
        "count": len(slow_queries)
    }


@router.get("/performance/bottlenecks")
async def get_bottlenecks():
    """识别性能瓶颈"""
    bottlenecks = performance_monitor.get_bottlenecks()
    return {
        "success": True,
        "bottlenecks": bottlenecks,
        "count": len(bottlenecks)
    }


@router.get("/performance/cache-stats")
async def get_cache_stats():
    """获取缓存统计"""
    cache_stats = response_time_optimizer.get_cache_stats()
    return {
        "success": True,
        **cache_stats
    }


@router.post("/performance/clear-cache")
async def clear_cache():
    """清空缓存"""
    response_time_optimizer.clear_cache()
    return {
        "success": True,
        "message": "缓存已清空"
    }


@router.get("/resource/system")
async def get_system_resources():
    """获取系统资源占用情况（CPU/内存/磁盘/外接硬盘）⭐P0功能"""
    status = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts(severity="high")
    
    # 格式化资源信息
    cpu_info = status.get("cpu", {})
    memory_info = status.get("memory", {})
    disk_info = status.get("disk", {})
    external_drives = status.get("external_drives", [])
    
    return {
        "success": True,
        "resources": {
            "cpu": {
                "percent": cpu_info.get("percent", 0),
                "count": cpu_info.get("count", 0),
                "freq": cpu_info.get("freq"),
                "status": "normal" if cpu_info.get("percent", 0) < 80 else "high"
            },
            "memory": {
                "total_gb": round(memory_info.get("total", 0) / (1024**3), 2),
                "used_gb": round(memory_info.get("used", 0) / (1024**3), 2),
                "available_gb": round(memory_info.get("available", 0) / (1024**3), 2),
                "percent": memory_info.get("percent", 0),
                "status": "normal" if memory_info.get("percent", 0) < 85 else "high"
            },
            "disk": {
                "total_gb": round(disk_info.get("total", 0) / (1024**3), 2),
                "used_gb": round(disk_info.get("used", 0) / (1024**3), 2),
                "free_gb": round(disk_info.get("free", 0) / (1024**3), 2),
                "percent": disk_info.get("percent", 0),
                "status": "normal" if disk_info.get("percent", 0) < 90 else "high"
            },
            "external_drives": [
                {
                    "device": drive.get("device"),
                    "mountpoint": drive.get("mountpoint"),
                    "total_gb": round(drive.get("total", 0) / (1024**3), 2),
                    "used_gb": round(drive.get("used", 0) / (1024**3), 2),
                    "free_gb": round(drive.get("free", 0) / (1024**3), 2),
                    "percent": drive.get("percent", 0),
                    "connected": drive.get("connected", False),
                    "status": "normal" if drive.get("percent", 0) < 90 else "high"
                }
                for drive in external_drives
            ]
        },
        "alerts": alerts,
        "alerts_count": len(alerts),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/resource/external-drives")
async def get_external_drives():
    """获取外接硬盘连接情况⭐P0功能"""
    status = resource_monitor.get_current_status()
    external_drives = status.get("external_drives", [])
    
    return {
        "success": True,
        "external_drives": [
            {
                "device": drive.get("device"),
                "mountpoint": drive.get("mountpoint"),
                "fstype": drive.get("fstype"),
                "total_gb": round(drive.get("total", 0) / (1024**3), 2),
                "used_gb": round(drive.get("used", 0) / (1024**3), 2),
                "free_gb": round(drive.get("free", 0) / (1024**3), 2),
                "percent": drive.get("percent", 0),
                "connected": drive.get("connected", False)
            }
            for drive in external_drives
        ],
        "count": len(external_drives),
        "timestamp": datetime.now().isoformat()
    }


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
            "resource_adjuster": True,
            "workflow_monitor": super_agent.workflow_monitor is not None,
            "voice_interaction": True,
            "translation": True,
            "file_generation": True,
            "web_search": True,
            "file_format_handler": True,
            "terminal_executor": True,
            "performance_monitor": True
        }
    }


class LLMConfigRequest(BaseModel):
    """LLM配置请求"""
    provider: str  # ollama/openai/anthropic/azure_openai
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None


class LLMConfigResponse(BaseModel):
    """LLM配置响应"""
    success: bool
    provider: str
    model: str
    base_url: str
    message: str


@router.post("/llm/config", response_model=LLMConfigResponse)
async def configure_llm(request: LLMConfigRequest):
    """
    配置LLM服务⭐新增
    
    支持：
    - ollama: 本地Ollama
    - openai: OpenAI API
    - anthropic: Anthropic Claude API
    - azure_openai: Azure OpenAI
    """
    try:
        # 验证提供商
        try:
            provider = LLMProvider(request.provider.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的LLM提供商: {request.provider}。支持: ollama, openai, anthropic, azure_openai"
            )
        
        # 更新LLM服务配置
        llm_service = get_llm_service(
            provider=request.provider.lower(),
            api_key=request.api_key,
            base_url=request.base_url,
            model=request.model
        )
        
        # 测试连接（可选）
        try:
            test_response = await llm_service.generate("测试", max_tokens=10)
            test_status = "连接成功"
        except Exception as e:
            test_status = f"配置成功，但连接测试失败: {str(e)}"
        
        return LLMConfigResponse(
            success=True,
            provider=llm_service.provider.value,
            model=llm_service.model,
            base_url=llm_service.base_url,
            message=f"LLM配置成功 ({llm_service.provider.value})。{test_status}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM配置失败: {str(e)}")


@router.get("/llm/config")
async def get_llm_config():
    """获取当前LLM配置"""
    try:
        llm_service = get_llm_service()
        return {
            "provider": llm_service.provider.value,
            "model": llm_service.model,
            "base_url": llm_service.base_url,
            "has_api_key": llm_service.api_key is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/providers")
async def get_llm_providers():
    """获取支持的LLM提供商列表"""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama (本地)",
                "description": "本地运行的Ollama服务",
                "default_url": "http://localhost:11434",
                "requires_api_key": False
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "description": "OpenAI GPT-4/GPT-3.5",
                "default_url": "https://api.openai.com/v1",
                "requires_api_key": True
            },
            {
                "id": "anthropic",
                "name": "Anthropic Claude",
                "description": "Anthropic Claude API",
                "default_url": "https://api.anthropic.com/v1",
                "requires_api_key": True
            },
            {
                "id": "azure_openai",
                "name": "Azure OpenAI",
                "description": "Azure OpenAI服务",
                "default_url": "",
                "requires_api_key": True
            }
        ]
    }

