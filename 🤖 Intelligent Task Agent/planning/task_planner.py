"""
任务规划引擎
负责任务的规划、分解、优化
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class TaskPlanner:
    """任务规划引擎"""
    
    def __init__(self, rag_client=None):
        self.rag_client = rag_client
        
    def create_task_plan(self, task_description: str, task_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建任务计划
        
        Args:
            task_description: 任务描述
            task_config: 任务配置
            
        Returns:
            任务计划
        """
        logger.info(f"开始规划任务: {task_description}")
        
        # 1. 分析任务需求
        task_analysis = self._analyze_task_requirements(task_description, task_config)
        
        # 2. 分解任务步骤
        task_steps = self._decompose_task(task_analysis)
        
        # 3. 优化任务流程
        optimized_steps = self._optimize_task_flow(task_steps)
        
        # 4. 估算资源需求
        resource_estimation = self._estimate_resources(optimized_steps)
        
        # 5. 生成执行计划
        execution_plan = {
            "task_name": task_analysis["name"],
            "description": task_description,
            "priority": task_config.get("priority", 5),
            "estimated_duration": resource_estimation["estimated_duration"],
            "steps": optimized_steps,
            "resource_requirements": resource_estimation,
            "dependencies": task_analysis.get("dependencies", []),
            "created_at": datetime.now().isoformat()
        }
        
        logger.info(f"任务规划完成，共 {len(optimized_steps)} 个步骤")
        return execution_plan
    
    def _analyze_task_requirements(self, description: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """分析任务需求"""
        
        # 从RAG检索相关知识
        rag_insights = []
        if self.rag_client:
            try:
                rag_results = self.rag_client.search(f"任务执行经验: {description}", top_k=3)
                rag_insights = [r.get("content", "") for r in rag_results]
            except Exception as e:
                logger.warning(f"RAG检索失败: {e}")
        
        analysis = {
            "name": config.get("name", "未命名任务"),
            "type": self._identify_task_type(description),
            "complexity": self._estimate_complexity(description),
            "required_capabilities": self._identify_required_capabilities(description),
            "constraints": config.get("constraints", {}),
            "dependencies": config.get("dependencies", []),
            "rag_insights": rag_insights
        }
        
        return analysis
    
    def _identify_task_type(self, description: str) -> str:
        """识别任务类型"""
        description_lower = description.lower()
        
        if any(word in description_lower for word in ["数据", "采集", "爬取", "收集"]):
            return "data_collection"
        elif any(word in description_lower for word in ["分析", "统计", "报告"]):
            return "data_analysis"
        elif any(word in description_lower for word in ["生成", "创作", "内容"]):
            return "content_generation"
        elif any(word in description_lower for word in ["监控", "检测", "告警"]):
            return "monitoring"
        elif any(word in description_lower for word in ["交易", "买卖", "投资"]):
            return "trading"
        else:
            return "general"
    
    def _estimate_complexity(self, description: str) -> str:
        """估算任务复杂度"""
        # 简单启发式规则
        word_count = len(description)
        
        if word_count < 50:
            return "simple"
        elif word_count < 150:
            return "medium"
        else:
            return "complex"
    
    def _identify_required_capabilities(self, description: str) -> List[str]:
        """识别所需能力"""
        capabilities = []
        description_lower = description.lower()
        
        capability_keywords = {
            "web_scraping": ["爬虫", "爬取", "抓取", "网页"],
            "data_processing": ["数据", "处理", "清洗", "转换"],
            "ai_analysis": ["分析", "ai", "智能", "预测"],
            "file_handling": ["文件", "上传", "下载", "存储"],
            "api_integration": ["api", "接口", "调用", "集成"],
            "notification": ["通知", "提醒", "告警", "推送"],
            "scheduling": ["定时", "周期", "调度", "计划"]
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                capabilities.append(capability)
        
        return capabilities or ["general_execution"]
    
    def _decompose_task(self, task_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分解任务为步骤"""
        task_type = task_analysis["type"]
        complexity = task_analysis["complexity"]
        
        # 根据任务类型生成标准步骤
        if task_type == "data_collection":
            steps = self._create_data_collection_steps(task_analysis)
        elif task_type == "data_analysis":
            steps = self._create_data_analysis_steps(task_analysis)
        elif task_type == "content_generation":
            steps = self._create_content_generation_steps(task_analysis)
        elif task_type == "monitoring":
            steps = self._create_monitoring_steps(task_analysis)
        elif task_type == "trading":
            steps = self._create_trading_steps(task_analysis)
        else:
            steps = self._create_general_steps(task_analysis)
        
        return steps
    
    def _create_data_collection_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建数据采集任务步骤"""
        return [
            {
                "order": 1,
                "name": "准备采集环境",
                "type": "preparation",
                "description": "初始化爬虫、检查代理、准备存储",
                "estimated_duration": 30
            },
            {
                "order": 2,
                "name": "执行数据采集",
                "type": "execution",
                "description": "根据配置爬取目标数据",
                "estimated_duration": 300,
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "数据清洗与验证",
                "type": "processing",
                "description": "清洗、去重、验证数据质量",
                "estimated_duration": 120,
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "存储与索引",
                "type": "storage",
                "description": "将数据存储到数据库或文件系统",
                "estimated_duration": 60,
                "dependencies": [3]
            },
            {
                "order": 5,
                "name": "发送完成通知",
                "type": "notification",
                "description": "通知用户任务完成情况",
                "estimated_duration": 5,
                "dependencies": [4]
            }
        ]
    
    def _create_data_analysis_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建数据分析任务步骤"""
        return [
            {
                "order": 1,
                "name": "加载数据",
                "type": "data_loading",
                "description": "从数据源加载待分析数据",
                "estimated_duration": 60
            },
            {
                "order": 2,
                "name": "数据预处理",
                "type": "preprocessing",
                "description": "数据清洗、格式化、特征工程",
                "estimated_duration": 120,
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "执行分析",
                "type": "analysis",
                "description": "运行分析算法、生成洞察",
                "estimated_duration": 180,
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "生成报告",
                "type": "reporting",
                "description": "创建可视化图表和分析报告",
                "estimated_duration": 90,
                "dependencies": [3]
            },
            {
                "order": 5,
                "name": "发布结果",
                "type": "publication",
                "description": "保存报告并通知相关人员",
                "estimated_duration": 30,
                "dependencies": [4]
            }
        ]
    
    def _create_content_generation_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建内容生成任务步骤"""
        return [
            {
                "order": 1,
                "name": "收集素材",
                "type": "material_collection",
                "description": "收集创作所需的素材和参考",
                "estimated_duration": 120
            },
            {
                "order": 2,
                "name": "生成内容",
                "type": "generation",
                "description": "使用AI生成内容初稿",
                "estimated_duration": 180,
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "去AI化处理",
                "type": "post_processing",
                "description": "优化内容，使其更自然和独特",
                "estimated_duration": 120,
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "质量检查",
                "type": "quality_check",
                "description": "检查内容质量、原创性、合规性",
                "estimated_duration": 60,
                "dependencies": [3]
            },
            {
                "order": 5,
                "name": "发布内容",
                "type": "publication",
                "description": "将内容发布到目标平台",
                "estimated_duration": 30,
                "dependencies": [4]
            }
        ]
    
    def _create_monitoring_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建监控任务步骤"""
        return [
            {
                "order": 1,
                "name": "初始化监控",
                "type": "initialization",
                "description": "设置监控指标和阈值",
                "estimated_duration": 30
            },
            {
                "order": 2,
                "name": "数据采集",
                "type": "data_collection",
                "description": "持续采集监控数据",
                "estimated_duration": 0,  # 持续任务
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "异常检测",
                "type": "anomaly_detection",
                "description": "分析数据，检测异常情况",
                "estimated_duration": 0,  # 持续任务
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "告警处理",
                "type": "alerting",
                "description": "发送告警通知",
                "estimated_duration": 0,  # 持续任务
                "dependencies": [3]
            }
        ]
    
    def _create_trading_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建交易任务步骤"""
        return [
            {
                "order": 1,
                "name": "市场数据获取",
                "type": "data_fetch",
                "description": "获取最新市场数据和行情",
                "estimated_duration": 30
            },
            {
                "order": 2,
                "name": "策略分析",
                "type": "strategy_analysis",
                "description": "运行交易策略，生成信号",
                "estimated_duration": 60,
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "风险评估",
                "type": "risk_assessment",
                "description": "评估交易风险和仓位",
                "estimated_duration": 30,
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "执行交易",
                "type": "trade_execution",
                "description": "提交交易订单",
                "estimated_duration": 10,
                "dependencies": [3]
            },
            {
                "order": 5,
                "name": "记录与通知",
                "type": "logging",
                "description": "记录交易结果并通知",
                "estimated_duration": 5,
                "dependencies": [4]
            }
        ]
    
    def _create_general_steps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """创建通用任务步骤"""
        return [
            {
                "order": 1,
                "name": "任务初始化",
                "type": "initialization",
                "description": "准备执行环境和资源",
                "estimated_duration": 30
            },
            {
                "order": 2,
                "name": "执行主任务",
                "type": "execution",
                "description": "执行任务主要逻辑",
                "estimated_duration": 180,
                "dependencies": [1]
            },
            {
                "order": 3,
                "name": "结果处理",
                "type": "post_processing",
                "description": "处理执行结果",
                "estimated_duration": 60,
                "dependencies": [2]
            },
            {
                "order": 4,
                "name": "清理与通知",
                "type": "cleanup",
                "description": "清理资源并发送通知",
                "estimated_duration": 15,
                "dependencies": [3]
            }
        ]
    
    def _optimize_task_flow(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """优化任务流程"""
        # 识别可以并行执行的步骤
        optimized_steps = steps.copy()
        
        for step in optimized_steps:
            # 添加重试配置
            if step["type"] in ["execution", "api_call", "data_fetch"]:
                step["retry_config"] = {
                    "max_retries": 3,
                    "retry_interval": 60,
                    "exponential_backoff": True
                }
            
            # 添加超时配置
            if "estimated_duration" in step and step["estimated_duration"] > 0:
                step["timeout"] = step["estimated_duration"] * 2
        
        return optimized_steps
    
    def _estimate_resources(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """估算资源需求"""
        total_duration = sum(step.get("estimated_duration", 0) for step in steps)
        
        # 简单的资源估算
        resource_estimation = {
            "estimated_duration": total_duration,
            "cpu_cores": 2,
            "memory_mb": 1024,
            "disk_space_mb": 500,
            "network_required": any(
                step["type"] in ["api_call", "data_fetch", "web_scraping"]
                for step in steps
            )
        }
        
        return resource_estimation
    
    def adjust_plan_based_on_feedback(
        self,
        plan: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """根据执行反馈调整计划"""
        
        # 分析执行结果
        actual_duration = execution_result.get("duration", 0)
        estimated_duration = plan.get("estimated_duration", 0)
        
        # 如果实际执行时间显著不同，调整估算
        if actual_duration > estimated_duration * 1.5:
            logger.info("任务执行时间超出预期，调整估算")
            adjustment_factor = actual_duration / estimated_duration
            
            for step in plan["steps"]:
                step["estimated_duration"] = int(
                    step.get("estimated_duration", 0) * adjustment_factor
                )
        
        # 如果有失败的步骤，添加更多重试机制
        if not execution_result.get("success", False):
            failed_steps = execution_result.get("failed_steps", [])
            for step in plan["steps"]:
                if step["order"] in failed_steps:
                    if "retry_config" not in step:
                        step["retry_config"] = {}
                    step["retry_config"]["max_retries"] = step["retry_config"].get("max_retries", 3) + 2
        
        return plan

