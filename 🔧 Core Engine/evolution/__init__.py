# ai-stack-super-enhanced/🔧 Core Engine/evolution/__init__.py
"""
进化引擎模块初始化文件
负责进化引擎模块的包初始化和公共接口导出
对应开发计划：阶段1 - Core Engine (26个文件) 中的 evolution/进化引擎基础
对应开发规则：9.1/9.2 自我学习和自我进化功能需求
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

from .feedback_processor import FeedbackProcessor

# 导出核心进化引擎类
from .meta_evolution_engine import MetaEvolutionEngine
from .performance_analyzer import PerformanceAnalyzer
from .strategy_evolver import StrategyEvolver

# 模块版本信息
__version__ = "1.0.0"
__author__ = "AI-STACK Evolution Team"
__description__ = "AI-STACK 自我学习和进化引擎核心模块"

# 全局进化配置
EVOLUTION_CONFIG = {
    "learning_rate": 0.01,
    "mutation_rate": 0.05,
    "crossover_rate": 0.8,
    "population_size": 50,
    "max_generations": 1000,
    "fitness_threshold": 0.95,
    "adaptation_speed": "adaptive",
}


class EvolutionModule:
    """进化模块管理器"""

    def __init__(self):
        self.meta_engine = None
        self.performance_analyzer = None
        self.feedback_processor = None
        self.strategy_evolver = None
        self.is_initialized = False

    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化进化引擎模块

        Args:
            config: 进化配置参数

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始初始化进化引擎模块")

            # 合并配置
            evolution_config = EVOLUTION_CONFIG.copy()
            if config:
                evolution_config.update(config)

            # 初始化各组件
            self.performance_analyzer = PerformanceAnalyzer()
            await self.performance_analyzer.initialize(evolution_config)

            self.feedback_processor = FeedbackProcessor()
            await self.feedback_processor.initialize(evolution_config)

            self.strategy_evolver = StrategyEvolver()
            await self.strategy_evolver.initialize(evolution_config)

            self.meta_engine = MetaEvolutionEngine(
                performance_analyzer=self.performance_analyzer,
                feedback_processor=self.feedback_processor,
                strategy_evolver=self.strategy_evolver,
            )
            await self.meta_engine.initialize(evolution_config)

            self.is_initialized = True
            logger.info("进化引擎模块初始化完成")
            return True

        except Exception as e:
            logger.error(f"进化引擎模块初始化失败: {str(e)}", exc_info=True)
            self.is_initialized = False
            return False

    async def get_health_status(self) -> Dict[str, Any]:
        """获取模块健康状态"""
        if not self.is_initialized:
            return {
                "status": "unhealthy",
                "message": "进化引擎模块未初始化",
                "components": {},
            }

        components_status = {}

        # 检查各组件状态
        for name, component in [
            ("meta_evolution_engine", self.meta_engine),
            ("performance_analyzer", self.performance_analyzer),
            ("feedback_processor", self.feedback_processor),
            ("strategy_evolver", self.strategy_evolver),
        ]:
            if component and hasattr(component, "get_health_status"):
                try:
                    components_status[name] = await component.get_health_status()
                except Exception as e:
                    components_status[name] = {
                        "status": "error",
                        "message": f"健康检查失败: {str(e)}",
                    }
            else:
                components_status[name] = {
                    "status": "unknown",
                    "message": "组件未初始化或不可用",
                }

        # 计算整体状态
        all_healthy = all(
            status.get("status") == "healthy" for status in components_status.values()
        )

        return {
            "status": "healthy" if all_healthy else "degraded",
            "message": "所有组件运行正常" if all_healthy else "部分组件运行异常",
            "components": components_status,
            "version": __version__,
            "initialized": self.is_initialized,
        }


# 创建全局模块实例
evolution_module = EvolutionModule()

# 导出公共接口
__all__ = [
    "MetaEvolutionEngine",
    "PerformanceAnalyzer",
    "FeedbackProcessor",
    "StrategyEvolver",
    "evolution_module",
    "EVOLUTION_CONFIG",
]

logger.info(f"进化引擎模块初始化文件加载完成 - 版本 {__version__}")
