"""
任务执行器
负责任务的实际执行、状态跟踪、错误处理
"""

import asyncio
import uuid
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, db_session=None, monitor=None):
        self.db_session = db_session
        self.monitor = monitor
        self.running_tasks = {}
        self.task_handlers = {}
        
        # 注册默认任务处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认任务处理器"""
        self.register_handler("data_collection", self._handle_data_collection)
        self.register_handler("data_analysis", self._handle_data_analysis)
        self.register_handler("content_generation", self._handle_content_generation)
        self.register_handler("monitoring", self._handle_monitoring)
        self.register_handler("trading", self._handle_trading)
        self.register_handler("general", self._handle_general_task)
    
    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self.task_handlers[task_type] = handler
        logger.info(f"注册任务处理器: {task_type}")
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务配置
            
        Returns:
            执行结果
        """
        execution_id = str(uuid.uuid4())
        task_id = task.get("id", "unknown")
        task_type = task.get("type", "general")
        
        logger.info(f"开始执行任务 {task_id}, 执行ID: {execution_id}")
        
        # 记录开始时间
        start_time = datetime.now()
        
        # 初始化执行记录
        execution_record = {
            "execution_id": execution_id,
            "task_id": task_id,
            "task_name": task.get("name", "未命名任务"),
            "status": "running",
            "progress": 0.0,
            "started_at": start_time.isoformat(),
            "steps_completed": 0,
            "total_steps": len(task.get("steps", [])),
            "current_step": None,
            "errors": []
        }
        
        self.running_tasks[execution_id] = execution_record
        
        try:
            # 通知监控系统
            if self.monitor:
                await self.monitor.on_task_started(execution_record)
            
            # 执行任务步骤
            steps = task.get("steps", [])
            step_results = []
            
            for i, step in enumerate(steps):
                logger.info(f"执行步骤 {step['order']}: {step['name']}")
                
                # 更新当前步骤
                execution_record["current_step"] = step["name"]
                execution_record["progress"] = (i / len(steps)) * 100
                
                # 检查依赖
                if not self._check_dependencies(step, step_results):
                    raise Exception(f"步骤 {step['name']} 的依赖未满足")
                
                # 执行步骤
                step_result = await self._execute_step(step, task_type, task)
                step_results.append(step_result)
                
                execution_record["steps_completed"] = i + 1
                
                # 通知监控系统
                if self.monitor:
                    await self.monitor.on_step_completed(execution_id, step, step_result)
                
                # 如果步骤失败且需要中止
                if not step_result.get("success", False) and not step.get("continue_on_failure", False):
                    raise Exception(f"步骤 {step['name']} 执行失败: {step_result.get('error')}")
            
            # 计算执行时长
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 构建最终结果
            result = {
                "success": True,
                "execution_id": execution_id,
                "task_id": task_id,
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration": duration,
                "steps_completed": len(steps),
                "step_results": step_results,
                "final_output": self._aggregate_outputs(step_results)
            }
            
            execution_record["status"] = "completed"
            execution_record["progress"] = 100.0
            execution_record["result"] = result
            
            # 通知监控系统
            if self.monitor:
                await self.monitor.on_task_completed(execution_id, result)
            
            logger.info(f"任务 {task_id} 执行完成，耗时 {duration:.2f} 秒")
            
            return result
            
        except Exception as e:
            error_message = str(e)
            error_trace = traceback.format_exc()
            
            logger.error(f"任务 {task_id} 执行失败: {error_message}")
            logger.error(error_trace)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = {
                "success": False,
                "execution_id": execution_id,
                "task_id": task_id,
                "started_at": start_time.isoformat(),
                "failed_at": end_time.isoformat(),
                "duration": duration,
                "error": error_message,
                "error_trace": error_trace,
                "steps_completed": execution_record.get("steps_completed", 0)
            }
            
            execution_record["status"] = "failed"
            execution_record["error"] = error_message
            execution_record["result"] = result
            
            # 通知监控系统
            if self.monitor:
                await self.monitor.on_task_failed(execution_id, result)
            
            return result
            
        finally:
            # 清理运行记录
            if execution_id in self.running_tasks:
                del self.running_tasks[execution_id]
    
    def _check_dependencies(self, step: Dict[str, Any], completed_steps: list) -> bool:
        """检查步骤依赖是否满足"""
        dependencies = step.get("dependencies", [])
        
        if not dependencies:
            return True
        
        # 检查所有依赖的步骤是否已完成且成功
        for dep_order in dependencies:
            # 查找依赖步骤的结果
            dep_result = next(
                (r for r in completed_steps if r.get("step_order") == dep_order),
                None
            )
            
            if not dep_result or not dep_result.get("success", False):
                return False
        
        return True
    
    async def _execute_step(
        self,
        step: Dict[str, Any],
        task_type: str,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行单个步骤"""
        step_start = datetime.now()
        
        try:
            # 获取步骤处理器
            handler = self.task_handlers.get(task_type, self._handle_general_step)
            
            # 执行步骤（带超时）
            timeout = step.get("timeout", 600)  # 默认10分钟超时
            
            result = await asyncio.wait_for(
                handler(step, task),
                timeout=timeout
            )
            
            step_end = datetime.now()
            duration = (step_end - step_start).total_seconds()
            
            return {
                "step_order": step["order"],
                "step_name": step["name"],
                "success": True,
                "duration": duration,
                "output": result
            }
            
        except asyncio.TimeoutError:
            logger.error(f"步骤 {step['name']} 执行超时")
            return {
                "step_order": step["order"],
                "step_name": step["name"],
                "success": False,
                "error": "执行超时"
            }
            
        except Exception as e:
            logger.error(f"步骤 {step['name']} 执行失败: {e}")
            return {
                "step_order": step["order"],
                "step_name": step["name"],
                "success": False,
                "error": str(e)
            }
    
    async def _handle_data_collection(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理数据采集任务"""
        step_type = step.get("type")
        
        if step_type == "preparation":
            logger.info("准备采集环境...")
            await asyncio.sleep(1)  # 模拟准备过程
            return {"status": "环境准备完成"}
            
        elif step_type == "execution":
            logger.info("执行数据采集...")
            await asyncio.sleep(2)  # 模拟采集过程
            return {
                "status": "采集完成",
                "items_collected": 100,
                "data_size_mb": 5.2
            }
            
        elif step_type == "processing":
            logger.info("数据清洗与验证...")
            await asyncio.sleep(1)
            return {
                "status": "处理完成",
                "items_processed": 100,
                "items_valid": 95
            }
            
        elif step_type == "storage":
            logger.info("存储数据...")
            await asyncio.sleep(0.5)
            return {"status": "存储完成", "records_saved": 95}
            
        else:
            return {"status": "步骤完成"}
    
    async def _handle_data_analysis(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理数据分析任务"""
        step_type = step.get("type")
        
        if step_type == "data_loading":
            logger.info("加载数据...")
            await asyncio.sleep(1)
            return {"status": "数据加载完成", "records": 1000}
            
        elif step_type == "preprocessing":
            logger.info("数据预处理...")
            await asyncio.sleep(1.5)
            return {"status": "预处理完成", "features_created": 15}
            
        elif step_type == "analysis":
            logger.info("执行分析...")
            await asyncio.sleep(2)
            return {
                "status": "分析完成",
                "insights": ["洞察1", "洞察2", "洞察3"]
            }
            
        elif step_type == "reporting":
            logger.info("生成报告...")
            await asyncio.sleep(1)
            return {"status": "报告生成完成", "report_path": "/reports/analysis_report.pdf"}
            
        else:
            return {"status": "步骤完成"}
    
    async def _handle_content_generation(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理内容生成任务"""
        step_type = step.get("type")
        
        if step_type == "material_collection":
            logger.info("收集素材...")
            await asyncio.sleep(1.5)
            return {"status": "素材收集完成", "materials": 10}
            
        elif step_type == "generation":
            logger.info("生成内容...")
            await asyncio.sleep(2)
            return {"status": "内容生成完成", "content_length": 1500}
            
        elif step_type == "post_processing":
            logger.info("去AI化处理...")
            await asyncio.sleep(1)
            return {"status": "处理完成", "uniqueness_score": 0.85}
            
        elif step_type == "quality_check":
            logger.info("质量检查...")
            await asyncio.sleep(0.5)
            return {"status": "检查完成", "quality_score": 0.92}
            
        elif step_type == "publication":
            logger.info("发布内容...")
            await asyncio.sleep(1)
            return {"status": "发布完成", "post_id": "12345"}
            
        else:
            return {"status": "步骤完成"}
    
    async def _handle_monitoring(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理监控任务"""
        logger.info(f"执行监控步骤: {step['name']}")
        await asyncio.sleep(0.5)
        return {"status": "监控运行中"}
    
    async def _handle_trading(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理交易任务"""
        step_type = step.get("type")
        
        if step_type == "data_fetch":
            logger.info("获取市场数据...")
            await asyncio.sleep(1)
            return {"status": "数据获取完成", "quotes": 50}
            
        elif step_type == "strategy_analysis":
            logger.info("策略分析...")
            await asyncio.sleep(1.5)
            return {"status": "分析完成", "signal": "buy", "confidence": 0.75}
            
        elif step_type == "risk_assessment":
            logger.info("风险评估...")
            await asyncio.sleep(0.5)
            return {"status": "评估完成", "risk_level": "medium"}
            
        elif step_type == "trade_execution":
            logger.info("执行交易...")
            await asyncio.sleep(0.3)
            return {"status": "交易完成", "order_id": "ORD-12345"}
            
        else:
            return {"status": "步骤完成"}
    
    async def _handle_general_task(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理通用任务"""
        return await self._handle_general_step(step, task)
    
    async def _handle_general_step(self, step: Dict[str, Any], task: Dict[str, Any]) -> Any:
        """处理通用步骤"""
        logger.info(f"执行通用步骤: {step['name']}")
        
        # 模拟执行时间
        estimated_duration = step.get("estimated_duration", 10)
        await asyncio.sleep(min(estimated_duration / 10, 2))  # 最多等待2秒
        
        return {
            "status": "completed",
            "message": f"步骤 {step['name']} 执行完成"
        }
    
    def _aggregate_outputs(self, step_results: list) -> Dict[str, Any]:
        """聚合步骤输出"""
        aggregated = {
            "total_steps": len(step_results),
            "successful_steps": sum(1 for r in step_results if r.get("success", False)),
            "total_duration": sum(r.get("duration", 0) for r in step_results),
            "outputs": {}
        }
        
        # 收集每个步骤的输出
        for result in step_results:
            step_name = result.get("step_name", "unknown")
            aggregated["outputs"][step_name] = result.get("output", {})
        
        return aggregated
    
    def get_running_tasks(self) -> Dict[str, Dict[str, Any]]:
        """获取正在运行的任务"""
        return self.running_tasks.copy()
    
    def get_task_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        return self.running_tasks.get(execution_id)
    
    async def cancel_task(self, execution_id: str) -> bool:
        """取消任务"""
        if execution_id in self.running_tasks:
            self.running_tasks[execution_id]["status"] = "cancelled"
            logger.info(f"任务 {execution_id} 已取消")
            return True
        return False

