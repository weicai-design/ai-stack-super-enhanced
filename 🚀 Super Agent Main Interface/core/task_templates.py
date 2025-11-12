"""
任务模板库
提供世界级的任务模板和最佳实践
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class TaskTemplateLibrary:
    """
    任务模板库
    
    功能：
    1. 提供预定义任务模板
    2. 任务最佳实践
    3. 任务依赖关系模板
    4. 任务执行步骤模板
    """
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[str, Dict[str, Any]]:
        """初始化任务模板"""
        return {
            # 数据采集任务模板
            "data_collection": {
                "name": "数据采集任务",
                "description": "从多个来源采集数据",
                "steps": [
                    {"name": "准备数据源", "duration": 15, "order": 1},
                    {"name": "配置采集工具", "duration": 30, "order": 2},
                    {"name": "执行数据采集", "duration": 60, "order": 3},
                    {"name": "数据清洗和验证", "duration": 30, "order": 4},
                    {"name": "存储数据", "duration": 15, "order": 5},
                    {"name": "生成采集报告", "duration": 15, "order": 6}
                ],
                "dependencies": [],
                "estimated_duration": 165,  # 分钟
                "priority": "medium",
                "best_practices": [
                    "确保数据源可用性",
                    "设置数据验证规则",
                    "记录采集日志",
                    "处理异常情况"
                ]
            },
            
            # 数据分析任务模板
            "data_analysis": {
                "name": "数据分析任务",
                "description": "分析数据并生成洞察",
                "steps": [
                    {"name": "加载数据", "duration": 10, "order": 1},
                    {"name": "数据预处理", "duration": 30, "order": 2},
                    {"name": "执行分析", "duration": 60, "order": 3},
                    {"name": "生成可视化", "duration": 30, "order": 4},
                    {"name": "编写分析报告", "duration": 45, "order": 5},
                    {"name": "发布结果", "duration": 15, "order": 6}
                ],
                "dependencies": [],
                "estimated_duration": 190,
                "priority": "medium",
                "best_practices": [
                    "验证数据质量",
                    "使用统计方法验证结果",
                    "创建清晰的可视化",
                    "记录分析假设"
                ]
            },
            
            # 内容生成任务模板
            "content_generation": {
                "name": "内容生成任务",
                "description": "生成高质量内容",
                "steps": [
                    {"name": "收集素材", "duration": 30, "order": 1},
                    {"name": "制定大纲", "duration": 20, "order": 2},
                    {"name": "生成初稿", "duration": 60, "order": 3},
                    {"name": "内容优化", "duration": 30, "order": 4},
                    {"name": "去AI化处理", "duration": 20, "order": 5},
                    {"name": "质量检查", "duration": 15, "order": 6},
                    {"name": "发布内容", "duration": 10, "order": 7}
                ],
                "dependencies": [],
                "estimated_duration": 185,
                "priority": "medium",
                "best_practices": [
                    "确保内容原创性",
                    "检查语法和拼写",
                    "优化SEO",
                    "添加相关图片"
                ]
            },
            
            # 监控任务模板
            "monitoring": {
                "name": "监控任务",
                "description": "持续监控系统状态",
                "steps": [
                    {"name": "初始化监控", "duration": 15, "order": 1},
                    {"name": "配置告警规则", "duration": 20, "order": 2},
                    {"name": "启动监控", "duration": 10, "order": 3},
                    {"name": "持续监控", "duration": 0, "order": 4, "continuous": True},
                    {"name": "异常检测", "duration": 0, "order": 5, "trigger": "on_alert"},
                    {"name": "生成监控报告", "duration": 15, "order": 6, "schedule": "daily"}
                ],
                "dependencies": [],
                "estimated_duration": 60,  # 初始设置时间
                "priority": "high",
                "best_practices": [
                    "设置合理的告警阈值",
                    "定期检查监控状态",
                    "记录监控历史",
                    "及时响应告警"
                ]
            },
            
            # 交易任务模板
            "trading": {
                "name": "交易任务",
                "description": "执行交易操作",
                "steps": [
                    {"name": "获取市场数据", "duration": 10, "order": 1},
                    {"name": "策略分析", "duration": 30, "order": 2},
                    {"name": "风险评估", "duration": 20, "order": 3},
                    {"name": "执行交易", "duration": 5, "order": 4},
                    {"name": "记录交易", "duration": 10, "order": 5},
                    {"name": "监控持仓", "duration": 0, "order": 6, "continuous": True}
                ],
                "dependencies": [],
                "estimated_duration": 75,
                "priority": "high",
                "best_practices": [
                    "严格执行止损规则",
                    "记录所有交易决策",
                    "定期回顾交易策略",
                    "控制风险敞口"
                ]
            },
            
            # 通用任务模板
            "general": {
                "name": "通用任务",
                "description": "通用任务模板",
                "steps": [
                    {"name": "任务初始化", "duration": 10, "order": 1},
                    {"name": "执行任务", "duration": 60, "order": 2},
                    {"name": "后处理", "duration": 15, "order": 3},
                    {"name": "清理资源", "duration": 5, "order": 4}
                ],
                "dependencies": [],
                "estimated_duration": 90,
                "priority": "medium",
                "best_practices": [
                    "明确任务目标",
                    "记录执行过程",
                    "处理异常情况",
                    "验证任务结果"
                ]
            }
        }
    
    def get_template(self, template_type: str) -> Optional[Dict[str, Any]]:
        """获取任务模板"""
        return self.templates.get(template_type)
    
    def get_all_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取所有模板"""
        return self.templates
    
    def create_task_from_template(
        self,
        template_type: str,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        从模板创建任务
        
        Args:
            template_type: 模板类型
            custom_config: 自定义配置
            
        Returns:
            任务配置
        """
        template = self.get_template(template_type)
        if not template:
            return {}
        
        task_config = {
            "name": template["name"],
            "description": template["description"],
            "steps": template["steps"].copy(),
            "dependencies": template["dependencies"].copy(),
            "estimated_duration": template["estimated_duration"],
            "priority": template["priority"],
            "best_practices": template["best_practices"].copy(),
            "template_type": template_type
        }
        
        # 应用自定义配置
        if custom_config:
            task_config.update(custom_config)
        
        return task_config
    
    def suggest_template(self, task_description: str) -> Optional[str]:
        """
        根据任务描述推荐模板
        
        Args:
            task_description: 任务描述
            
        Returns:
            推荐的模板类型
        """
        description_lower = task_description.lower()
        
        # 关键词匹配
        keywords = {
            "data_collection": ["采集", "收集", "爬取", "抓取", "获取数据"],
            "data_analysis": ["分析", "统计", "报告", "洞察", "可视化"],
            "content_generation": ["生成", "创作", "内容", "文章", "文案"],
            "monitoring": ["监控", "检测", "告警", "观察", "追踪"],
            "trading": ["交易", "买卖", "投资", "下单", "持仓"]
        }
        
        for template_type, template_keywords in keywords.items():
            if any(keyword in description_lower for keyword in template_keywords):
                return template_type
        
        return "general"


