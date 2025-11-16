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
import json
import os

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
from core.task_orchestrator import TaskStatus
from core.learning_events import LearningEventType
from core.data_sources.factory_data_source import FactoryDataSource
from core.integrations.external_status import ExternalIntegrationStatus
from 💼 Intelligent ERP & Business Management.core.trial_data_source import DemoFactoryTrialDataSource
from 💼 Intelligent ERP & Business Management.core.erp_8d_analysis import analyze_8d
from core.strategy_engine import StrategyEngine
from core.content_compliance import ContentComplianceService
from core.stock_gateway import StockGateway
from core.stock_simulator import StockSimulator
from core.stock_backtest import BacktestEngine
from core.integrations.douyin import DouyinIntegration
from 📚 Enhanced RAG & Knowledge Graph.core.rag_tools import (
    clean_text as rag_clean,
    standardize_text as rag_standardize,
    deduplicate as rag_dedup,
    validate as rag_validate,
    authenticity_score as rag_auth_score
)
from 💻 AI Programming Assistant.core.cursor_bridge import CursorBridge

router = APIRouter(prefix="/api/super-agent", tags=["Super Agent"])

# 初始化服务
super_agent = SuperAgent()
memo_system = MemoSystem()
task_planning = TaskPlanning(memo_system)
learning_monitor = SelfLearningMonitor(resource_manager=None, event_bus=super_agent.event_bus)
resource_monitor = ResourceMonitor()
resource_adjuster = ResourceAutoAdjuster(resource_manager=None)  # 资源自动调节器
voice_interaction = VoiceInteraction()
translation_service = TranslationService()
file_generation = FileGenerationService()
web_search = WebSearchService()
file_format_handler = FileFormatHandler()  # 文件格式处理器
terminal_executor = TerminalExecutor(workflow_monitor=super_agent.workflow_monitor)  # 终端执行器
external_status = ExternalIntegrationStatus()
strategy_engine = StrategyEngine()
content_compliance = ContentComplianceService()
stock_gateway = StockGateway()
stock_sim = StockSimulator()
douyin = DouyinIntegration()
cursor_bridge = CursorBridge()
backtest_engine = BacktestEngine()
try:
    factory_data_source = FactoryDataSource()
    factory_data_source_error = None
except FileNotFoundError as exc:
    factory_data_source = None
    factory_data_source_error = str(exc)
try:
    trial_data_source = DemoFactoryTrialDataSource()
    trial_data_source_error = None
except FileNotFoundError as exc:
    trial_data_source = None
    trial_data_source_error = str(exc)

# 设置依赖
super_agent.set_memo_system(memo_system)
super_agent.set_learning_monitor(learning_monitor)
super_agent.set_resource_monitor(resource_monitor)
super_agent.set_task_planning(task_planning)

# 启动资源监控（后台任务）
import asyncio
asyncio.create_task(resource_monitor.start_monitoring(interval=5))

# 启动ERP监听（轻量轮询对比）
_erp_last_order_count = {"count": 0}
async def _erp_listener():
    """每20秒轮询一次订单/工单变化，写入系统事件，供自学习/主界面使用"""
    ds = None
    try:
        ds = _get_factory_data_source()
    except Exception:
        return
    while True:
        try:
            orders = ds.get_orders()
            count = len(orders)
            if count != _erp_last_order_count["count"]:
                _erp_last_order_count["count"] = count
                if super_agent.workflow_monitor:
                    await super_agent.workflow_monitor.record_system_event(
                        event_type="erp_change",
                        source="erp_listener",
                        severity="info",
                        success=True,
                        data={"orders_count": count},
                        error=None
                    )
            await asyncio.sleep(20)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(20)

asyncio.create_task(_erp_listener())

bpmn_dir = Path(project_root) / "data" / "bpmn"
bpmn_dir.mkdir(parents=True, exist_ok=True)
rag_dir = Path(project_root) / "data" / "rag"
rag_dir.mkdir(parents=True, exist_ok=True)
rag_store_path = rag_dir / "documents.jsonl"

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


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "medium"
    metadata: Optional[Dict[str, Any]] = None
    dependencies: Optional[List[str]] = None


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatus
    updates: Optional[Dict[str, Any]] = None


class TaskRetrospectRequest(BaseModel):
    """任务复盘请求"""
    success: bool
    summary: Optional[str] = ""
    lessons: Optional[List[str]] = None
    metrics: Optional[Dict[str, Any]] = None


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
        
        # 策略决策（SLO/降级/预算）
        decision = strategy_engine.decide(request.message, request.input_type)

        # 使用性能优化器执行（带超时和缓存），应用策略时间预算
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
            timeout=decision.timeout_seconds,
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
        # 释放预算占用
        strategy_engine.release()
        
        return ChatResponse(
            success=result.get("success", False) if result else False,
            response=result.get("response", "") if result else "",
            response_time=response_time,
            rag_retrievals=result.get("rag_retrievals") if result else None,
            timestamp=result.get("timestamp", datetime.now().isoformat()) if result else datetime.now().isoformat()
        )
    except Exception as e:
        strategy_engine.release()
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


@router.post("/tasks/{task_id}/retrospect")
async def retrospect_task(task_id: int, request: TaskRetrospectRequest):
    """任务复盘：记录总结/经验/指标并完成生命周期闭环"""
    # 复盘数据结构直接附加到任务（利用已有task_planning存储）
    tasks = task_planning.get_tasks()
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    task.setdefault("retrospect", {})
    task["retrospect"].update({
        "success": request.success,
        "summary": request.summary or "",
        "lessons": request.lessons or [],
        "metrics": request.metrics or {},
        "retrospected_at": datetime.now().isoformat()
    })
    # 可选：将经验写回学习系统/RAG
    if hasattr(super_agent, "learning_monitor") and super_agent.learning_monitor:
        try:
            await super_agent.learning_monitor.record_insight({
                "type": "task_retrospect",
                "task_id": task_id,
                "success": request.success,
                "lessons": request.lessons or [],
                "timestamp": datetime.now().isoformat()
            })
        except Exception:
            pass
    return {"success": True, "task": task}


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
async def execute_plan(plan_id: int, concurrency: int = 2):
    """执行工作计划（并发+依赖处理+简单重试）"""
    plan = next((p for p in task_planning.plans if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    # 若未确认则自动确认并将pending任务置为confirmed
    if plan.get("status") != "confirmed":
        plan["status"] = "confirmed"
        plan["confirmed_at"] = datetime.now().isoformat()
        for t in plan["tasks"]:
            if t.get("status") == "pending":
                t["status"] = "confirmed"
    # 计划内任务ID集合
    plan_task_ids = [t["id"] for t in plan["tasks"]]
    id_to_task = {t["id"]: t for t in task_planning.tasks if t["id"] in plan_task_ids}
    # 并发调度
    import asyncio
    sem = asyncio.Semaphore(max(1, min(10, concurrency)))
    completed = set([tid for tid, t in id_to_task.items() if t.get("status") == "completed"])
    failed: Dict[int, str] = {}
    results: List[Dict[str, Any]] = []
    in_progress: set[int] = set()

    async def can_run(tid: int) -> bool:
        t = id_to_task.get(tid) or {}
        deps = t.get("dependencies") or []
        return all((dep in completed) for dep in deps)

    async def run_one(tid: int):
        async with sem:
            t = id_to_task.get(tid) or {}
            max_retries = int(t.get("retries", 0) or 0)
            backoff = float(t.get("retry_backoff_sec", 0.0) or 0.0)
            attempt = 0
            while True:
                res = await task_planning.execute_task(tid)
                results.append(res)
                if res.get("success"):
                    completed.add(tid)
                    break
                else:
                    if attempt < max_retries:
                        attempt += 1
                        if backoff > 0:
                            await asyncio.sleep(backoff * attempt)
                        continue
                    failed[tid] = res.get("error", "unknown")
                    break

    remaining = set(plan_task_ids) - completed
    while remaining:
        ready = [tid for tid in remaining if tid not in in_progress]
        # 过滤依赖未满足的
        ready = [tid for tid in ready if (await can_run(tid))]
        if not ready and not in_progress:
            break  # 阻塞
        # 启动
        import itertools
        slots = max(0, max(1, min(concurrency, 10)) - len(in_progress))
        for tid in itertools.islice(ready, 0, slots):
            in_progress.add(tid)
            asyncio.create_task(run_one(tid))
        await asyncio.sleep(0.2)
        # 清理已完成/失败
        in_progress = {tid for tid in in_progress if tid not in completed and tid not in failed}
        remaining = remaining - completed - set(failed.keys())

    return {
        "success": True if not failed else False,
        "plan_id": plan_id,
        "completed_count": len(completed),
        "failed": failed,
        "results": results
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


@router.get("/workflow/system-events")
async def get_system_events(limit: int = 20, event_type: Optional[str] = None):
    """获取系统级事件（如终端命令、安全日志）"""
    monitor = super_agent.workflow_monitor
    if not monitor:
        return {"events": [], "count": 0, "summary": {}}
    events = monitor.get_recent_system_events(limit=limit, event_type=event_type)
    summary = monitor.get_system_event_summary(event_type=event_type)
    return {"events": events, "count": len(events), "summary": summary}


@router.get("/learning/events")
async def get_learning_events(limit: int = 50, event_type: Optional[str] = None):
    """获取学习事件总线中的事件"""
    bus = super_agent.event_bus
    try:
        event_type_enum = LearningEventType(event_type) if event_type else None
    except ValueError:
        raise HTTPException(status_code=400, detail=f"未知的事件类型: {event_type}")
    events = [
        event.__dict__
        for event in bus.get_recent_events(limit=limit, event_type=event_type_enum)
    ]
    return {"events": events, "count": len(events), "stats": bus.get_statistics()}


def _get_task_orchestrator():
    orchestrator = super_agent.task_orchestrator
    if not orchestrator:
        raise HTTPException(status_code=503, detail="任务编排器尚未初始化")
    return orchestrator


def _get_factory_data_source():
    if factory_data_source:
        return factory_data_source
    raise HTTPException(
        status_code=503,
        detail=factory_data_source_error or "demo_factory 数据源尚未准备，请先生成数据库",
    )

def _get_trial_data_source():
    if trial_data_source:
        return trial_data_source
    raise HTTPException(
        status_code=503,
        detail=trial_data_source_error or "trial 数据源尚未准备，请先生成 demo_factory 数据库",
    )


@router.get("/tasks")
async def list_tasks():
    orchestrator = _get_task_orchestrator()
    return {"tasks": orchestrator.list_tasks()}

@router.get("/tasks/{task_id}")
async def get_task_detail(task_id: str):
    """获取编排任务详情（Orchestrator管理的任务）"""
    orchestrator = _get_task_orchestrator()
    data = orchestrator.get_task(task_id)
    if not data:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": data}


@router.post("/tasks")
async def create_task(request: TaskCreateRequest):
    orchestrator = _get_task_orchestrator()
    task = await orchestrator.register_task(
        title=request.title,
        description=request.description or "",
        priority=request.priority,
        metadata=request.metadata,
        dependencies=request.dependencies,
        source="api",
    )
    return {"task": task}


@router.post("/tasks/{task_id}/status")
async def update_task_status(task_id: str, request: TaskStatusUpdateRequest):
    orchestrator = _get_task_orchestrator()
    task = await orchestrator.update_task_status(
        task_id=task_id,
        status=request.status,
        updates=request.updates,
    )
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": task}

@router.get("/planning/tasks/{task_id}")
async def get_planning_task_detail(task_id: int):
    """获取规划系统中的任务详情（包含执行日志/复盘等）"""
    task = next((t for t in task_planning.tasks if t.get("id") == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return {"task": task}

@router.get("/erp/demo/dashboard")
async def get_demo_dashboard():
    ds = _get_factory_data_source()
    return ds.get_dashboards()


@router.get("/erp/demo/orders")
async def get_demo_orders(
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    订单列表（支持状态筛选/关键词过滤/分页）
    关键词匹配字段：order_id / customer / product_code / product_name
    """
    ds = _get_factory_data_source()
    items = ds.get_orders(status=status)
    # 关键词过滤（简化）
    if q:
        ql = q.lower()
        def match(o):
            for k in ["order_id", "customer", "product_code", "product_name"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    # 分页
    page = max(1, page)
    page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    # 状态分布（简易图表数据）
    status_dist = {}
    for o in items:
        s = o.get("status", "unknown")
        status_dist[s] = status_dist.get(s, 0) + 1
    return {
        "orders": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "status_distribution": status_dist
    }


@router.get("/erp/demo/production-jobs")
async def get_production_jobs(
    order_id: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_production_jobs(order_id=order_id)
    # 关键词过滤（job_id/order_id/machine/operation等字段）
    if q:
        ql = q.lower()
        def match(o):
            for k in ["job_id", "order_id", "machine", "operation"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布
    state_dist = {}
    for j in items:
        s = j.get("status", "unknown")
        state_dist[s] = state_dist.get(s, 0) + 1
    return {"jobs": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": state_dist}


@router.get("/erp/demo/procurements")
async def get_procurement_alerts(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_procurement_alerts()
    if q:
        ql = q.lower()
        def match(o):
            for k in ["po_id", "supplier", "material_code", "material_name", "alert", "status"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布
    state_dist = {}
    for p in items:
        s = p.get("status", "unknown")
        state_dist[s] = state_dist.get(s, 0) + 1
    return {"procurements": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": state_dist}

@router.get("/erp/demo/inventory")
async def get_inventory(
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    ds = _get_factory_data_source()
    items = ds.get_inventory_status()
    if q:
        ql = q.lower()
        def match(o):
            for k in ["material_code", "material_name", "status_flag"]:
                v = str(o.get(k, "")).lower()
                if ql in v:
                    return True
            return False
        items = [o for o in items if match(o)]
    total = len(items)
    page = max(1, page); page_size = max(1, min(200, page_size))
    start = (page - 1) * page_size; end = start + page_size
    page_items = items[start:end]
    # 状态分布（低于安全/正常）
    flag_dist = {}
    for it in items:
        s = it.get("status_flag", "normal")
        flag_dist[s] = flag_dist.get(s, 0) + 1
    return {"inventory": page_items, "total": total, "page": page, "page_size": page_size, "status_distribution": flag_dist}


@router.get("/erp/demo/cash-flow")
async def get_cash_flow_summary():
    ds = _get_factory_data_source()
    return ds.get_cash_flow_summary()

@router.post("/erp/trial/calc")
async def trial_calculation(
    target_weekly_revenue: Optional[float] = Body(None, embed=True),
    target_daily_units: Optional[int] = Body(None, embed=True),
    product_code: Optional[str] = Body(None, embed=True),
    order_id: Optional[str] = Body(None, embed=True)
):
    """
    运营试算器：为达到目标（周营收或日产量），需要的日均产出/订单配置建议
    - 若提供 target_weekly_revenue：根据产品单价与可用天数，倒推出建议日产量
    - 若提供 target_daily_units：计算预计周营收
    """
    ds = _get_trial_data_source()
    product = await ds.get_product_data(
        order_id=order_id,
        product_code=product_code,
        legacy_identifier=product_code or order_id
    )
    if not product:
        raise HTTPException(status_code=404, detail="未找到可用于试算的订单/产品数据")

    unit_price = float(product.get("unit_price") or 0.0)
    available_days = product.get("available_days") or 7
    available_days = max(1, int(available_days))

    result: Dict[str, Any] = {
        "product": {
            "order_id": product.get("order_id"),
            "product_code": product.get("product_code"),
            "product_name": product.get("product_name"),
            "unit_price": unit_price,
            "available_days": available_days,
            "promise_date": product.get("promise_date"),
            "requested_date": product.get("requested_date"),
            "priority": product.get("priority"),
        },
        "inputs": {
            "target_weekly_revenue": target_weekly_revenue,
            "target_daily_units": target_daily_units
        }
    }

    if target_weekly_revenue and unit_price > 0:
        # 按周营收目标倒推建议日产量
        required_units_week = target_weekly_revenue / unit_price
        required_units_day = required_units_week / 7.0
        result["trial"] = {
            "type": "by_weekly_revenue",
            "required_units_per_day": round(required_units_day, 2),
            "assumptions": {
                "unit_price": unit_price,
                "days_per_week": 7
            }
        }
    elif target_daily_units:
        # 按日产量推算预计周营收
        expected_week_revenue = target_daily_units * unit_price * 7.0
        result["trial"] = {
            "type": "by_daily_units",
            "expected_weekly_revenue": round(expected_week_revenue, 2),
            "assumptions": {
                "unit_price": unit_price,
                "days_per_week": 7
            }
        }
    else:
        # 默认按订单窗口与单价，给出达成订单的建议日产量
        quantity = int(product.get("quantity") or 0)
        if quantity > 0:
            required_units_day = quantity / available_days
            result["trial"] = {
                "type": "by_order_quantity",
                "required_units_per_day": round(required_units_day, 2),
                "assumptions": {
                    "available_days": available_days,
                    "order_quantity": quantity
                }
            }
        else:
            result["trial"] = {
                "type": "insufficient_data",
                "message": "缺少目标或订单数量，无法计算"
            }

    # 附带历史交付作为参考
    history = await ds.get_historical_delivery_data(
        order_id=product.get("order_id"),
        product_code=product.get("product_code"),
        days=30
    )
    result["history"] = history
    result["success"] = True
    result["timestamp"] = datetime.now().isoformat()
    return result

@router.post("/erp/8d/analyze")
async def erp_8d_analyze(payload: Dict[str, Any] = Body(...)):
    """
    ERP八维度分析：质量/成本/交期/安全/利润/效率/管理/技术
    传入各维度必要指标（可缺省，采用保守默认），返回指标与总览评分
    """
    try:
        result = analyze_8d(payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"8D分析失败: {str(e)}")

# ====== ERP BPMN 流程编辑/管理 ======
@router.get("/erp/bpmn/processes")
async def list_bpmn_processes():
    items = []
    for file in bpmn_dir.glob("*.json"):
        try:
            items.append({
                "id": file.stem,
                "filename": file.name,
                "size": file.stat().st_size,
                "updated_at": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
        except Exception:
            continue
    return {"processes": sorted(items, key=lambda x: x["updated_at"], reverse=True)}

@router.get("/erp/bpmn/process/{process_id}")
async def get_bpmn_process(process_id: str):
    path = bpmn_dir / f"{process_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="流程不存在")
    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return {"id": process_id, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SaveBPMNRequest(BaseModel):
    id: Optional[str] = None
    data: Dict[str, Any]

@router.post("/erp/bpmn/process")
async def save_bpmn_process(req: SaveBPMNRequest):
    pid = req.id or f"proc_{int(datetime.now().timestamp())}"
    path = bpmn_dir / f"{pid}.json"
    try:
        path.write_text(json.dumps(req.data, ensure_ascii=False, indent=2), encoding="utf-8")
        return {"success": True, "id": pid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/erp/bpmn/process/{process_id}")
async def delete_bpmn_process(process_id: str):
    path = bpmn_dir / f"{process_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="流程不存在")
    try:
        path.unlink()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ====== BPMN 运行时追踪（最小可用） ======
runtime_path = bpmn_dir / "runtime.jsonl"

class BpmnRuntimeEvent(BaseModel):
    instance_id: str
    process_id: str
    node_id: str
    node_name: Optional[str] = None
    status: str  # started/completed/error
    message: Optional[str] = None

@router.post("/erp/bpmn/runtime/event")
async def bpmn_runtime_event(ev: BpmnRuntimeEvent):
    """记录流程实例节点事件"""
    rec = ev.dict()
    rec["timestamp"] = datetime.now().isoformat()
    try:
        with open(runtime_path, "a", encoding="utf-8") as f:
            import json as _json
            f.write(_json.dumps(rec, ensure_ascii=False) + "\n")
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/erp/bpmn/runtime/instances")
async def bpmn_runtime_instances(limit: int = 50):
    """按实例聚合最近事件（最小可用）"""
    from collections import defaultdict
    agg = defaultdict(list)
    try:
        if runtime_path.exists():
            with open(runtime_path, "r", encoding="utf-8") as f:
                import json as _json
                lines = f.readlines()[-1000:]
                for line in lines:
                    try:
                        e = _json.loads(line)
                        agg[e["instance_id"]].append(e)
                    except Exception:
                        continue
        instances = []
        for iid, events in agg.items():
            events_sorted = sorted(events, key=lambda x: x.get("timestamp", ""))
            last = events_sorted[-1]
            instances.append({
                "instance_id": iid,
                "process_id": last.get("process_id"),
                "last_node": last.get("node_id"),
                "last_status": last.get("status"),
                "events_count": len(events_sorted),
                "updated_at": last.get("timestamp")
            })
        instances = sorted(instances, key=lambda x: x["updated_at"], reverse=True)[:limit]
        return {"instances": instances, "count": len(instances)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/status")
async def get_external_integrations():
    return {"integrations": external_status.get_status()}


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
        **stats,
        "strategy": strategy_engine.get_stats()
    }

@router.get("/dashboard/overview")
async def get_dashboard_overview():
    """统一遥测总览：性能/策略/资源/学习/工作流统计"""
    perf = performance_monitor.get_performance_stats()
    strategy = strategy_engine.get_stats()
    resource = resource_monitor.get_current_status()
    alerts = resource_monitor.get_alerts()
    workflow_stats = super_agent.workflow_monitor.get_statistics() if super_agent.workflow_monitor else {}
    learning_stats = learning_monitor.get_statistics() if learning_monitor else {}
    return {
        "success": True,
        "performance": perf,
        "strategy": strategy,
        "resource": {
            "status": resource,
            "alerts": alerts,
            "alerts_count": len(alerts)
        },
        "workflow": workflow_stats,
        "learning": learning_stats,
        "timestamp": datetime.now().isoformat()
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

@router.get("/security/audit/overview")
async def security_audit_overview(limit: int = 20):
    """统一安全与合规审计总览（终端/系统事件）"""
    monitor = super_agent.workflow_monitor
    if not monitor:
        return {"events": [], "count": 0}
    events = monitor.get_recent_system_events(limit=limit, event_type=None)
    # 仅提取部分字段
    simplified = []
    for e in events:
        simplified.append({
            "event_id": getattr(e, "event_id", None),
            "type": getattr(e, "event_type", ""),
            "source": getattr(e, "source", ""),
            "success": getattr(e, "success", True),
            "severity": getattr(e, "severity", "info"),
            "timestamp": getattr(e, "timestamp", datetime.now()).isoformat(),
            "short": str(getattr(e, "data", {}))[:120]
        })
    return {"events": simplified, "count": len(simplified)}


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

@router.post("/content/compliance/check")
async def check_content_compliance(
    text: str = Body(..., embed=True),
    references: Optional[List[str]] = Body(None, embed=True)
):
    """内容合规检查：原创度/相似度/敏感词（轻量版）"""
    result = await content_compliance.check_text(text, references or [])
    return result

# ====== 股票量化：数据源网关与模拟撮合 ======
@router.get("/stock/sources")
async def list_stock_sources():
    return stock_gateway.list_sources()

@router.post("/stock/switch-source")
async def switch_stock_source(source: str = Body(..., embed=True)):
    ok = stock_gateway.switch(source)
    if not ok:
        raise HTTPException(status_code=400, detail="数据源不存在")
    return {"success": True, "active": source}

@router.get("/stock/quote")
async def get_stock_quote(symbol: str, market: str = "A"):
    data = await stock_gateway.quote(symbol, market)
    # 同步给模拟器撮合（若有挂单）
    fills = stock_sim.mark_to_market_and_fill(symbol, data["price"])
    return {"quote": data, "sim_fills": fills}

@router.post("/stock/sim/place-order")
async def sim_place_order(
    symbol: str = Body(..., embed=True),
    side: str = Body(..., embed=True),  # buy/sell
    qty: int = Body(..., embed=True),
    order_type: str = Body("market", embed=True),  # market/limit
    price: Optional[float] = Body(None, embed=True)
):
    result = stock_sim.place_order(symbol, side, qty, order_type, price)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "下单失败"))
    return result

@router.post("/stock/sim/cancel")
async def sim_cancel(order_id: str = Body(..., embed=True)):
    result = stock_sim.cancel_order(order_id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "撤单失败"))
    return result

@router.get("/stock/sim/state")
async def sim_state():
    return stock_sim.get_state()

@router.get("/stock/backtest")
async def stock_backtest(symbol: str = "000001", days: int = 60, seed: int = 7):
    return backtest_engine.run(symbol, days, seed)
# ====== 抖音集成：授权与草稿发布（合规前置） ======
@router.get("/douyin/status")
async def douyin_status():
    return douyin.get_status()

@router.post("/douyin/begin-auth")
async def douyin_begin_auth():
    return douyin.begin_auth()

@router.post("/douyin/revoke")
async def douyin_revoke():
    return douyin.revoke()

class DouyinDraftRequest(BaseModel):
    title: str
    content: str
    tags: Optional[List[str]] = None
    references: Optional[List[str]] = None
    min_originality: float = 60.0
    block_sensitive: bool = True

@router.post("/douyin/create-draft")
async def douyin_create_draft(req: DouyinDraftRequest):
    # 合规前置检查
    compliance = await content_compliance.check_text(req.content, req.references or [])
    if not compliance.get("success"):
        raise HTTPException(status_code=400, detail=f"合规检测失败：{compliance.get('error','未知错误')}")
    if compliance["originality_percent"] < req.min_originality:
        return {
            "success": False,
            "blocked": True,
            "reason": "原创度不足",
            "compliance": compliance
        }
    if req.block_sensitive and compliance.get("sensitive_hits"):
        return {
            "success": False,
            "blocked": True,
            "reason": "命中敏感词",
            "compliance": compliance
        }
    # 通过则创建抖音草稿
    draft = await douyin.create_draft(req.title, req.content, req.tags or [])
    if not draft.get("success"):
        raise HTTPException(status_code=400, detail=draft.get("error", "草稿创建失败"))
    return {
        "success": True,
        "draft": draft,
        "compliance": compliance
    }

# ====== RAG 预处理与真实性验证 ======
class RagPreprocessRequest(BaseModel):
    text: str

@router.post("/rag/preprocess/clean")
async def rag_preprocess_clean(req: RagPreprocessRequest):
    return {"success": True, "text": rag_clean(req.text)}

@router.post("/rag/preprocess/standardize")
async def rag_preprocess_standardize(req: RagPreprocessRequest):
    return {"success": True, "text": rag_standardize(req.text)}

@router.post("/rag/preprocess/deduplicate")
async def rag_preprocess_deduplicate(req: RagPreprocessRequest):
    res = rag_dedup(req.text)
    return {"success": True, **res}

@router.post("/rag/preprocess/validate")
async def rag_preprocess_validate(req: RagPreprocessRequest):
    res = rag_validate(req.text)
    return {"success": True, **res}

@router.post("/rag/authenticity/check")
async def rag_authenticity_check(req: RagPreprocessRequest):
    res = rag_auth_score(req.text)
    return res

# ====== RAG 流水线化：上传→预处理→真实性→入库（最小可用） ======
class RagIngestRequest(BaseModel):
    text: Optional[str] = None
    title: Optional[str] = None
    run_clean: bool = True
    run_standardize: bool = True
    run_dedup: bool = True
    min_authenticity: float = 55.0

@router.post("/rag/pipeline/ingest")
async def rag_pipeline_ingest(req: RagIngestRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail="缺少文本")
    text = req.text
    steps = {}
    if req.run_clean:
        text = rag_clean(text); steps["clean"] = True
    if req.run_standardize:
        text = rag_standardize(text); steps["standardize"] = True
    if req.run_dedup:
        d = rag_dedup(text); text = d["unique_text"]; steps["deduplicate"] = {"removed": d["removed"], "kept": d["kept"]}
    valid = rag_validate(text)
    auth = rag_auth_score(text)
    accepted = auth.get("score", 0) >= req.min_authenticity and valid.get("valid", True)
    # TODO: 入库到RAG（此处占位，仅返回拟入库的文档数据）
    doc = {
        "id": f"doc_{int(datetime.now().timestamp()*1000)}",
        "title": req.title or (text[:30] if text else "文档"),
        "content": text,
        "ingested_at": datetime.now().isoformat(),
        "authenticity": auth,
        "validation": valid
    }
    # 持久化入库（JSONL占位），并写入简易倒排索引（按关键词拆分写meta）
    try:
        with open(rag_store_path, "a", encoding="utf-8") as f:
            import json as _json
            f.write(_json.dumps(doc, ensure_ascii=False) + "\n")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f\"持久化失败: {str(e)}\")
    return {
        "success": True,
        "accepted": accepted,
        "document": doc,
        "steps": steps
    }

@router.get("/rag/pipeline/documents")
async def rag_pipeline_list_docs(limit: int = 20):
    """列出最近入库的RAG文档（占位存储）"""
    items = []
    try:
        if rag_store_path.exists():
            with open(rag_store_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[-limit:]
                import json as _json
                for line in reversed(lines):
                    try:
                        items.append(_json.loads(line))
                    except Exception:
                        continue
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"documents": items, "count": len(items)}

@router.get("/rag/pipeline/search")
async def rag_pipeline_search(q: str, limit: int = 10):
    """占位检索：基于子串与简单关键词匹配"""
    results = []
    try:
        if not rag_store_path.exists():
            return {"results": [], "count": 0}
        with open(rag_store_path, "r", encoding="utf-8") as f:
            import json as _json, re as _re
            kws = [k for k in _re.split(r\"\\W+\", q) if k]
            for line in reversed(f.readlines()):
                try:
                    doc = _json.loads(line)
                except Exception:
                    continue
                text = (doc.get(\"title\", \"\") + \"\\n\" + doc.get(\"content\", \"\"))
                score = 0
                if q in text:
                    score += 2
                score += sum(1 for k in kws if k and k in text)
                if score > 0:
                    results.append({\"id\": doc.get(\"id\"), \"title\": doc.get(\"title\"), \"score\": score})
                if len(results) >= limit:
                    break
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {\"results\": results, \"count\": len(results)}

# ====== 编程助手：Cursor 桥接 ======
@router.get("/coding/cursor/status")
async def cursor_status():
    return cursor_bridge.get_status()

class CursorOpenRequest(BaseModel):
    file_path: str
    line_number: Optional[int] = None

@router.post("/coding/cursor/open-file")
async def cursor_open_file(req: CursorOpenRequest):
    result = await cursor_bridge.open_in_cursor(req.file_path, req.line_number)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "打开失败"))
    return result

class CursorSyncRequest(BaseModel):
    file_path: str
    code: str

@router.post("/coding/cursor/sync-code")
async def cursor_sync_code(req: CursorSyncRequest):
    return await cursor_bridge.sync_code(req.file_path, req.code)

class CursorEdit(BaseModel):
    type: str
    start_line: int
    end_line: int
    content: Optional[str] = ""

class CursorEditRequest(BaseModel):
    file_path: str
    edits: List[CursorEdit]

@router.post("/coding/cursor/edit-code")
async def cursor_edit_code(req: CursorEditRequest):
    edits = [e.dict() for e in req.edits]
    return await cursor_bridge.edit_code(req.file_path, edits)

class CursorCompletionRequest(BaseModel):
    file_path: str
    line_number: int
    column: int
    context_lines: int = 5

@router.post("/coding/cursor/completion")
async def cursor_completion(req: CursorCompletionRequest):
    return await cursor_bridge.get_code_completion(req.file_path, req.line_number, req.column, req.context_lines)

class CursorDetectRequest(BaseModel):
    file_path: str

@router.post("/coding/cursor/detect-errors")
async def cursor_detect_errors(req: CursorDetectRequest):
    return await cursor_bridge.detect_errors(req.file_path)

class CursorProjectRequest(BaseModel):
    project_path: str
    files: Optional[List[str]] = None

@router.post("/coding/cursor/open-project")
async def cursor_open_project(req: CursorProjectRequest):
    result = await cursor_bridge.sync_project(req.project_path, req.files)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "打开项目失败"))
    return result
