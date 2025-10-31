# ai-stack-super-enhanced/🔧 Core Engine/evolution/feedback_processor.py
"""
反馈处理器 - 负责处理各种反馈信号并转化为进化指导
对应开发计划：阶段1 - Core Engine 中的进化引擎基础
对应开发规则：9.1/9.2 自我学习和自我进化功能需求
"""

import asyncio
import logging
import re
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FeedbackSource(Enum):
    """反馈来源枚举"""

    SYSTEM_MONITORING = "system_monitoring"
    USER_INTERACTION = "user_interaction"
    PERFORMANCE_METRICS = "performance_metrics"
    ERROR_REPORTS = "error_reports"
    SECURITY_EVENTS = "security_events"
    EXTERNAL_SOURCES = "external_sources"
    SELF_EVALUATION = "self_evaluation"


class FeedbackType(Enum):
    """反馈类型枚举"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTIVE = "corrective"
    SUGGESTIVE = "suggestive"
    CRITICAL = "critical"


class FeedbackPriority(Enum):
    """反馈优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class FeedbackProcessor:
    """
    反馈处理器 - 系统反馈信号处理和分析核心组件

    核心功能：
    1. 多源反馈数据收集和标准化
    2. 反馈信号分类和优先级评估
    3. 情感分析和意图识别
    4. 反馈聚合和模式发现
    5. 进化指导生成和传递
    """

    def __init__(self):
        # 反馈数据存储
        self.feedback_queue = asyncio.Queue()
        self.processed_feedback = []
        self.feedback_patterns = {}

        # 处理配置
        self.processing_config = {}
        self.source_weights = {}

        # 分析组件
        self.sentiment_analyzer = None
        self.pattern_miner = None
        self.correlation_engine = None

        # 状态信息
        self.is_initialized = False
        self.processing_task = None
        self.running = False
        self.feedback_count = 0

        # 缓存和优化
        self.feedback_cache = {}
        self.learning_model = {}

        logger.info("反馈处理器实例创建")

    async def initialize(self, config: Dict[str, Any] = None) -> bool:
        """
        初始化反馈处理器

        Args:
            config: 处理配置参数

        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("开始初始化反馈处理器")

            # 设置配置
            self.processing_config = config or {}
            await self._setup_default_config()

            # 初始化分析组件
            await self._initialize_analyzers()

            # 设置源权重
            await self._setup_source_weights()

            # 启动处理任务
            self.running = True
            self.processing_task = asyncio.create_task(self._processing_loop())

            self.is_initialized = True
            logger.info("反馈处理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"反馈处理器初始化失败: {str(e)}", exc_info=True)
            self.is_initialized = False
            return False

    async def _setup_default_config(self):
        """设置默认配置"""
        default_config = {
            "processing_batch_size": 10,
            "max_queue_size": 1000,
            "retention_days": 90,
            "real_time_processing": True,
            "sentiment_analysis_enabled": True,
            "pattern_detection_enabled": True,
            "correlation_analysis_enabled": True,
            "auto_learning_enabled": True,
            "emergency_threshold": 0.9,
            "feedback_aggregation_window": 300,  # 5分钟
        }

        # 合并配置
        for key, value in default_config.items():
            if key not in self.processing_config:
                self.processing_config[key] = value

    async def _initialize_analyzers(self):
        """初始化分析组件"""
        try:
            # 初始化情感分析器
            self.sentiment_analyzer = SentimentAnalyzer()

            # 初始化模式挖掘器
            self.pattern_miner = PatternMiner()

            # 初始化关联引擎
            self.correlation_engine = CorrelationEngine()

            logger.debug("反馈分析组件初始化完成")

        except Exception as e:
            logger.error(f"分析组件初始化失败: {str(e)}")

    async def _setup_source_weights(self):
        """设置源权重"""
        # 默认源权重配置
        self.source_weights = {
            FeedbackSource.SYSTEM_MONITORING: 0.9,
            FeedbackSource.PERFORMANCE_METRICS: 0.8,
            FeedbackSource.ERROR_REPORTS: 0.7,
            FeedbackSource.SECURITY_EVENTS: 0.95,
            FeedbackSource.USER_INTERACTION: 0.6,
            FeedbackSource.EXTERNAL_SOURCES: 0.5,
            FeedbackSource.SELF_EVALUATION: 0.85,
        }

        # 从配置中更新权重
        if "source_weights" in self.processing_config:
            for source, weight in self.processing_config["source_weights"].items():
                try:
                    source_enum = FeedbackSource(source)
                    self.source_weights[source_enum] = weight
                except ValueError:
                    logger.warning(f"未知反馈来源: {source}")

    async def _processing_loop(self):
        """反馈处理循环"""
        logger.info("启动反馈处理循环")

        batch_size = self.processing_config.get("processing_batch_size", 10)

        while self.running:
            try:
                # 批量处理反馈
                batch = await self._collect_feedback_batch(batch_size)

                if batch:
                    # 处理批量反馈
                    processed_batch = await self._process_feedback_batch(batch)

                    # 学习处理结果
                    if self.processing_config.get("auto_learning_enabled", True):
                        await self._learn_from_processed_feedback(processed_batch)

                    # 更新反馈模式
                    if self.processing_config.get("pattern_detection_enabled", True):
                        await self._update_feedback_patterns(processed_batch)

                # 短暂等待以避免过度消耗CPU
                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.info("反馈处理循环被取消")
                break
            except Exception as e:
                logger.error(f"反馈处理循环异常: {str(e)}", exc_info=True)
                await asyncio.sleep(1)  # 异常后等待1秒

    async def _collect_feedback_batch(self, batch_size: int) -> List[Dict[str, Any]]:
        """收集反馈批次"""
        batch = []

        try:
            # 从队列中获取反馈
            while len(batch) < batch_size and not self.feedback_queue.empty():
                try:
                    feedback = await asyncio.wait_for(
                        self.feedback_queue.get(), timeout=0.1
                    )
                    batch.append(feedback)
                    self.feedback_queue.task_done()
                except asyncio.TimeoutError:
                    break

            return batch

        except Exception as e:
            logger.error(f"反馈批次收集失败: {str(e)}")
            return []

    async def submit_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """
        提交反馈数据

        Args:
            feedback_data: 反馈数据

        Returns:
            str: 反馈ID
        """
        try:
            # 生成反馈ID
            feedback_id = str(uuid.uuid4())

            # 标准化反馈数据
            standardized_feedback = await self._standardize_feedback(
                feedback_data, feedback_id
            )

            # 检查队列大小
            max_queue_size = self.processing_config.get("max_queue_size", 1000)
            if self.feedback_queue.qsize() >= max_queue_size:
                logger.warning("反馈队列已满，丢弃最旧的反馈")
                try:
                    self.feedback_queue.get_nowait()
                    self.feedback_queue.task_done()
                except asyncio.QueueEmpty:
                    pass

            # 添加到处理队列
            await self.feedback_queue.put(standardized_feedback)

            logger.debug(f"反馈提交成功: {feedback_id}")
            return feedback_id

        except Exception as e:
            logger.error(f"反馈提交失败: {str(e)}")
            return f"error_{int(datetime.utcnow().timestamp())}"

    async def _standardize_feedback(
        self, raw_feedback: Dict[str, Any], feedback_id: str
    ) -> Dict[str, Any]:
        """标准化反馈数据"""
        try:
            standardized = {
                "feedback_id": feedback_id,
                "timestamp": datetime.utcnow().isoformat(),
                "received_at": datetime.utcnow().isoformat(),
                "raw_data": raw_feedback,
            }

            # 提取来源
            source = await self._extract_feedback_source(raw_feedback)
            standardized["source"] = source.value

            # 提取类型
            feedback_type = await self._classify_feedback_type(raw_feedback, source)
            standardized["type"] = feedback_type.value

            # 评估优先级
            priority = await self._assess_feedback_priority(
                raw_feedback, source, feedback_type
            )
            standardized["priority"] = priority.value

            # 提取内容
            content = await self._extract_feedback_content(raw_feedback)
            standardized["content"] = content

            # 添加元数据
            standardized["metadata"] = {
                "source_confidence": await self._calculate_source_confidence(source),
                "processing_stage": "standardized",
                "standardization_version": "1.0",
            }

            return standardized

        except Exception as e:
            logger.error(f"反馈标准化失败: {str(e)}")
            # 返回最小标准化数据
            return {
                "feedback_id": feedback_id,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "unknown",
                "type": "neutral",
                "priority": "medium",
                "content": {"raw": raw_feedback},
                "metadata": {"error": str(e)},
            }

    async def _extract_feedback_source(
        self, raw_feedback: Dict[str, Any]
    ) -> FeedbackSource:
        """提取反馈来源"""
        try:
            # 根据数据特征判断来源
            if "system_metrics" in raw_feedback or "performance_data" in raw_feedback:
                return FeedbackSource.SYSTEM_MONITORING

            elif "user_id" in raw_feedback or "user_action" in raw_feedback:
                return FeedbackSource.USER_INTERACTION

            elif "error_code" in raw_feedback or "exception" in raw_feedback:
                return FeedbackSource.ERROR_REPORTS

            elif "security_level" in raw_feedback or "threat_indicator" in raw_feedback:
                return FeedbackSource.SECURITY_EVENTS

            elif "external_api" in raw_feedback or "third_party" in raw_feedback:
                return FeedbackSource.EXTERNAL_SOURCES

            elif "self_assessment" in raw_feedback or "introspection" in raw_feedback:
                return FeedbackSource.SELF_EVALUATION

            else:
                # 默认为性能指标
                return FeedbackSource.PERFORMANCE_METRICS

        except Exception as e:
            logger.error(f"反馈来源提取失败: {str(e)}")
            return FeedbackSource.PERFORMANCE_METRICS

    async def _classify_feedback_type(
        self, raw_feedback: Dict[str, Any], source: FeedbackSource
    ) -> FeedbackType:
        """分类反馈类型"""
        try:
            # 基于来源和内容的类型分类
            content_str = str(raw_feedback).lower()

            # 关键事件检测
            critical_indicators = [
                "error",
                "failure",
                "crash",
                "panic",
                "emergency",
                "critical",
            ]
            if any(indicator in content_str for indicator in critical_indicators):
                return FeedbackType.CRITICAL

            # 纠正性反馈检测
            corrective_indicators = [
                "fix",
                "correct",
                "repair",
                "resolve",
                "should",
                "must",
            ]
            if any(indicator in content_str for indicator in corrective_indicators):
                return FeedbackType.CORRECTIVE

            # 建议性反馈检测
            suggestive_indicators = [
                "suggest",
                "recommend",
                "improve",
                "enhance",
                "better",
            ]
            if any(indicator in content_str for indicator in suggestive_indicators):
                return FeedbackType.SUGGESTIVE

            # 情感分析
            if self.processing_config.get("sentiment_analysis_enabled", True):
                sentiment = await self.sentiment_analyzer.analyze(raw_feedback)
                if sentiment > 0.1:
                    return FeedbackType.POSITIVE
                elif sentiment < -0.1:
                    return FeedbackType.NEGATIVE
                else:
                    return FeedbackType.NEUTRAL
            else:
                return FeedbackType.NEUTRAL

        except Exception as e:
            logger.error(f"反馈类型分类失败: {str(e)}")
            return FeedbackType.NEUTRAL

    async def _assess_feedback_priority(
        self,
        raw_feedback: Dict[str, Any],
        source: FeedbackSource,
        feedback_type: FeedbackType,
    ) -> FeedbackPriority:
        """评估反馈优先级"""
        try:
            base_priority_scores = {
                FeedbackPriority.LOW: 1,
                FeedbackPriority.MEDIUM: 2,
                FeedbackPriority.HIGH: 3,
                FeedbackPriority.CRITICAL: 4,
                FeedbackPriority.EMERGENCY: 5,
            }

            # 基础分数基于来源和类型
            source_weight = self.source_weights.get(source, 0.5)
            type_multiplier = self._get_type_multiplier(feedback_type)

            base_score = source_weight * type_multiplier

            # 内容紧急度分析
            urgency_indicators = {
                "immediately": 2.0,
                "urgent": 1.8,
                "asap": 1.7,
                "critical": 1.9,
                "emergency": 2.0,
                "now": 1.6,
            }

            content_str = str(raw_feedback).lower()
            urgency_boost = 1.0
            for indicator, boost in urgency_indicators.items():
                if indicator in content_str:
                    urgency_boost = max(urgency_boost, boost)

            final_score = base_score * urgency_boost

            # 映射到优先级
            if final_score >= 1.8:
                return FeedbackPriority.EMERGENCY
            elif final_score >= 1.5:
                return FeedbackPriority.CRITICAL
            elif final_score >= 1.2:
                return FeedbackPriority.HIGH
            elif final_score >= 0.8:
                return FeedbackPriority.MEDIUM
            else:
                return FeedbackPriority.LOW

        except Exception as e:
            logger.error(f"反馈优先级评估失败: {str(e)}")
            return FeedbackPriority.MEDIUM

    def _get_type_multiplier(self, feedback_type: FeedbackType) -> float:
        """获取类型乘数"""
        multipliers = {
            FeedbackType.CRITICAL: 2.0,
            FeedbackType.NEGATIVE: 1.5,
            FeedbackType.CORRECTIVE: 1.3,
            FeedbackType.SUGGESTIVE: 1.1,
            FeedbackType.POSITIVE: 0.8,
            FeedbackType.NEUTRAL: 0.7,
        }
        return multipliers.get(feedback_type, 1.0)

    async def _extract_feedback_content(
        self, raw_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取反馈内容"""
        try:
            content = {
                "raw": raw_feedback,
                "structured": {},
                "keywords": [],
                "sentiment": 0.0,
            }

            # 提取结构化信息
            if isinstance(raw_feedback, dict):
                for key, value in raw_feedback.items():
                    if isinstance(value, (str, int, float, bool)):
                        content["structured"][key] = value

            # 提取关键词
            content["keywords"] = await self._extract_keywords(raw_feedback)

            # 情感分析
            if self.processing_config.get("sentiment_analysis_enabled", True):
                content["sentiment"] = await self.sentiment_analyzer.analyze(
                    raw_feedback
                )

            return content

        except Exception as e:
            logger.error(f"反馈内容提取失败: {str(e)}")
            return {"raw": raw_feedback, "error": str(e)}

    async def _extract_keywords(self, raw_feedback: Dict[str, Any]) -> List[str]:
        """提取关键词"""
        try:
            text_content = str(raw_feedback)

            # 简单的关键词提取
            words = re.findall(r"\b[a-zA-Z]{3,}\b", text_content.lower())

            # 过滤常见词
            stop_words = {
                "the",
                "and",
                "for",
                "are",
                "but",
                "not",
                "you",
                "all",
                "can",
                "your",
                "has",
                "had",
                "was",
                "were",
                "will",
                "with",
                "have",
                "this",
                "that",
                "from",
            }
            filtered_words = [word for word in words if word not in stop_words]

            # 统计词频
            word_freq = Counter(filtered_words)

            # 返回高频词
            return [word for word, count in word_freq.most_common(10)]

        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            return []

    async def _calculate_source_confidence(self, source: FeedbackSource) -> float:
        """计算来源置信度"""
        # 基于来源可靠性的置信度计算
        confidence_scores = {
            FeedbackSource.SYSTEM_MONITORING: 0.95,
            FeedbackSource.PERFORMANCE_METRICS: 0.9,
            FeedbackSource.SELF_EVALUATION: 0.85,
            FeedbackSource.SECURITY_EVENTS: 0.8,
            FeedbackSource.ERROR_REPORTS: 0.75,
            FeedbackSource.USER_INTERACTION: 0.7,
            FeedbackSource.EXTERNAL_SOURCES: 0.6,
        }

        return confidence_scores.get(source, 0.5)

    async def _process_feedback_batch(
        self, batch: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """处理反馈批次"""
        processed_batch = []

        try:
            for feedback in batch:
                processed_feedback = await self._process_single_feedback(feedback)
                processed_batch.append(processed_feedback)

                # 存储处理结果
                self.processed_feedback.append(processed_feedback)
                self.feedback_count += 1

            # 限制存储大小
            max_storage = self.processing_config.get("max_storage_size", 10000)
            if len(self.processed_feedback) > max_storage:
                self.processed_feedback = self.processed_feedback[-max_storage:]

            logger.debug(f"反馈批次处理完成: {len(processed_batch)}条反馈")
            return processed_batch

        except Exception as e:
            logger.error(f"反馈批次处理失败: {str(e)}")
            return []

    async def _process_single_feedback(
        self, feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理单个反馈"""
        try:
            processed = feedback.copy()

            # 情感分析
            if self.processing_config.get("sentiment_analysis_enabled", True):
                sentiment_result = await self.sentiment_analyzer.analyze_detailed(
                    feedback
                )
                processed["sentiment_analysis"] = sentiment_result

            # 模式匹配
            if self.processing_config.get("pattern_detection_enabled", True):
                pattern_match = await self.pattern_miner.match_patterns(feedback)
                processed["pattern_matches"] = pattern_match

            # 关联分析
            if self.processing_config.get("correlation_analysis_enabled", True):
                correlations = await self.correlation_engine.find_correlations(
                    feedback, self.processed_feedback
                )
                processed["correlations"] = correlations

            # 生成进化指导
            evolution_guidance = await self._generate_evolution_guidance(processed)
            processed["evolution_guidance"] = evolution_guidance

            # 更新处理状态
            processed["metadata"]["processed_at"] = datetime.utcnow().isoformat()
            processed["metadata"]["processing_version"] = "1.0"

            return processed

        except Exception as e:
            logger.error(
                f"单个反馈处理失败: {feedback.get('feedback_id', 'unknown')} - {str(e)}"
            )
            feedback["metadata"]["processing_error"] = str(e)
            return feedback

    async def _generate_evolution_guidance(
        self, processed_feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成进化指导"""
        try:
            guidance = {
                "guidance_id": str(uuid.uuid4()),
                "generated_at": datetime.utcnow().isoformat(),
                "confidence": 0.0,
                "recommendations": [],
                "warnings": [],
                "opportunities": [],
            }

            # 基于反馈类型生成指导
            feedback_type = processed_feedback.get("type", "")
            feedback_priority = processed_feedback.get("priority", "")
            feedback_content = processed_feedback.get("content", {})

            # 负面反馈 -> 纠正性指导
            if feedback_type in ["negative", "critical", "corrective"]:
                corrective_actions = await self._generate_corrective_guidance(
                    processed_feedback
                )
                guidance["recommendations"].extend(corrective_actions)
                guidance["confidence"] += 0.3

            # 建议性反馈 -> 改进指导
            if feedback_type == "suggestive":
                improvement_actions = await self._generate_improvement_guidance(
                    processed_feedback
                )
                guidance["recommendations"].extend(improvement_actions)
                guidance["confidence"] += 0.2

            # 正面反馈 -> 强化指导
            if feedback_type == "positive":
                reinforcement_actions = await self._generate_reinforcement_guidance(
                    processed_feedback
                )
                guidance["recommendations"].extend(reinforcement_actions)
                guidance["confidence"] += 0.1

            # 基于优先级调整置信度
            priority_boost = {
                "emergency": 0.4,
                "critical": 0.3,
                "high": 0.2,
                "medium": 0.1,
                "low": 0.0,
            }
            guidance["confidence"] += priority_boost.get(feedback_priority, 0.0)

            # 限制置信度范围
            guidance["confidence"] = max(0.0, min(1.0, guidance["confidence"]))

            # 生成警告和机会
            if feedback_priority in ["critical", "emergency"]:
                guidance["warnings"].append(
                    {
                        "level": "high",
                        "message": "检测到高优先级反馈，建议立即处理",
                        "related_feedback": processed_feedback["feedback_id"],
                    }
                )

            if feedback_type == "positive" and guidance["confidence"] > 0.7:
                guidance["opportunities"].append(
                    {
                        "type": "optimization",
                        "message": "正面反馈指示当前策略有效，可考虑扩大应用",
                        "confidence": guidance["confidence"],
                    }
                )

            return guidance

        except Exception as e:
            logger.error(f"进化指导生成失败: {str(e)}")
            return {
                "guidance_id": str(uuid.uuid4()),
                "error": str(e),
                "confidence": 0.0,
                "recommendations": [],
            }

    async def _generate_corrective_guidance(
        self, feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成纠正性指导"""
        recommendations = []

        try:
            content = feedback.get("content", {})
            keywords = content.get("keywords", [])
            structured_data = content.get("structured", {})

            # 基于关键词的模式匹配
            issue_patterns = {
                "slow": ["性能优化", "缓存策略", "查询优化"],
                "error": ["错误处理", "输入验证", "异常捕获"],
                "memory": ["内存管理", "资源清理", "泄漏检测"],
                "crash": ["稳定性改进", "容错机制", "状态恢复"],
                "security": ["安全检查", "权限验证", "数据加密"],
            }

            for keyword in keywords:
                for pattern, actions in issue_patterns.items():
                    if pattern in keyword:
                        for action in actions:
                            recommendations.append(
                                {
                                    "type": "corrective",
                                    "action": action,
                                    "reason": f"检测到'{keyword}'相关问题",
                                    "priority": feedback.get("priority", "medium"),
                                    "source_feedback": feedback["feedback_id"],
                                }
                            )

            # 基于结构化数据的建议
            if "error_code" in structured_data:
                recommendations.append(
                    {
                        "type": "corrective",
                        "action": "分析错误代码根本原因",
                        "reason": f"检测到错误代码: {structured_data['error_code']}",
                        "priority": "high",
                        "source_feedback": feedback["feedback_id"],
                    }
                )

            return recommendations[:5]  # 返回前5个建议

        except Exception as e:
            logger.error(f"纠正性指导生成失败: {str(e)}")
            return [
                {
                    "type": "corrective",
                    "action": "调查反馈根本原因",
                    "reason": "反馈处理过程中发生错误",
                    "priority": "medium",
                    "source_feedback": feedback["feedback_id"],
                }
            ]

    async def _generate_improvement_guidance(
        self, feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成改进指导"""
        recommendations = []

        try:
            content = feedback.get("content", {})
            keywords = content.get("keywords", [])

            improvement_patterns = {
                "better": ["性能调优", "用户体验改进"],
                "faster": ["算法优化", "并发处理"],
                "easier": ["界面简化", "流程优化"],
                "more": ["功能扩展", "容量增加"],
                "improve": ["质量提升", "流程改进"],
            }

            for keyword in keywords:
                for pattern, actions in improvement_patterns.items():
                    if pattern in keyword:
                        for action in actions:
                            recommendations.append(
                                {
                                    "type": "improvement",
                                    "action": action,
                                    "reason": f"用户建议'{keyword}'相关改进",
                                    "priority": "medium",
                                    "source_feedback": feedback["feedback_id"],
                                }
                            )

            return recommendations[:3]  # 返回前3个建议

        except Exception as e:
            logger.error(f"改进指导生成失败: {str(e)}")
            return []

    async def _generate_reinforcement_guidance(
        self, feedback: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成强化指导"""
        recommendations = []

        try:
            content = feedback.get("content", {})
            sentiment = content.get("sentiment", 0)

            # 高正面情感 -> 强化当前策略
            if sentiment > 0.5:
                recommendations.append(
                    {
                        "type": "reinforcement",
                        "action": "维持当前优化策略",
                        "reason": "收到强烈正面反馈，当前策略效果良好",
                        "priority": "low",
                        "source_feedback": feedback["feedback_id"],
                    }
                )

            return recommendations

        except Exception as e:
            logger.error(f"强化指导生成失败: {str(e)}")
            return []

    async def _learn_from_processed_feedback(
        self, processed_batch: List[Dict[str, Any]]
    ):
        """从处理过的反馈中学习"""
        try:
            for feedback in processed_batch:
                # 学习反馈模式
                await self._update_learning_model(feedback)

                # 调整处理策略
                await self._adapt_processing_strategy(feedback)

            logger.debug(f"从{len(processed_batch)}条反馈中学习完成")

        except Exception as e:
            logger.error(f"反馈学习失败: {str(e)}")

    async def _update_learning_model(self, feedback: Dict[str, Any]):
        """更新学习模型"""
        try:
            feedback_type = feedback.get("type")
            source = feedback.get("source")
            priority = feedback.get("priority")

            # 更新类型分布
            if "type_distribution" not in self.learning_model:
                self.learning_model["type_distribution"] = defaultdict(int)
            self.learning_model["type_distribution"][feedback_type] += 1

            # 更新源分布
            if "source_distribution" not in self.learning_model:
                self.learning_model["source_distribution"] = defaultdict(int)
            self.learning_model["source_distribution"][source] += 1

            # 更新优先级分布
            if "priority_distribution" not in self.learning_model:
                self.learning_model["priority_distribution"] = defaultdict(int)
            self.learning_model["priority_distribution"][priority] += 1

            # 限制学习模型大小
            for distribution in [
                "type_distribution",
                "source_distribution",
                "priority_distribution",
            ]:
                if distribution in self.learning_model:
                    # 保持最近1000条记录的分布
                    total = sum(self.learning_model[distribution].values())
                    if total > 1000:
                        scale_factor = 1000 / total
                        for key in list(self.learning_model[distribution].keys()):
                            self.learning_model[distribution][key] = int(
                                self.learning_model[distribution][key] * scale_factor
                            )
                            if self.learning_model[distribution][key] == 0:
                                del self.learning_model[distribution][key]

        except Exception as e:
            logger.error(f"学习模型更新失败: {str(e)}")

    async def _adapt_processing_strategy(self, feedback: Dict[str, Any]):
        """调整处理策略"""
        try:
            # 基于反馈特征调整源权重
            source = feedback.get("source")
            guidance_confidence = feedback.get("evolution_guidance", {}).get(
                "confidence", 0
            )

            if guidance_confidence > 0.7:
                # 高置信度指导 -> 提高该源权重
                current_weight = self.source_weights.get(FeedbackSource(source), 0.5)
                new_weight = min(1.0, current_weight + 0.05)
                self.source_weights[FeedbackSource(source)] = new_weight
                logger.debug(f"提高源权重: {source} -> {new_weight}")

            elif guidance_confidence < 0.3:
                # 低置信度指导 -> 降低该源权重
                current_weight = self.source_weights.get(FeedbackSource(source), 0.5)
                new_weight = max(0.1, current_weight - 0.03)
                self.source_weights[FeedbackSource(source)] = new_weight
                logger.debug(f"降低源权重: {source} -> {new_weight}")

        except Exception as e:
            logger.error(f"处理策略调整失败: {str(e)}")

    async def _update_feedback_patterns(self, processed_batch: List[Dict[str, Any]]):
        """更新反馈模式"""
        try:
            for feedback in processed_batch:
                pattern_key = await self._generate_pattern_key(feedback)

                if pattern_key not in self.feedback_patterns:
                    self.feedback_patterns[pattern_key] = {
                        "pattern": pattern_key,
                        "first_seen": datetime.utcnow(),
                        "last_seen": datetime.utcnow(),
                        "occurrence_count": 1,
                        "sources": set([feedback.get("source")]),
                        "types": set([feedback.get("type")]),
                        "priorities": set([feedback.get("priority")]),
                    }
                else:
                    pattern = self.feedback_patterns[pattern_key]
                    pattern["last_seen"] = datetime.utcnow()
                    pattern["occurrence_count"] += 1
                    pattern["sources"].add(feedback.get("source"))
                    pattern["types"].add(feedback.get("type"))
                    pattern["priorities"].add(feedback.get("priority"))

            # 清理旧模式
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            expired_patterns = [
                key
                for key, pattern in self.feedback_patterns.items()
                if pattern["last_seen"] < cutoff_time
                and pattern["occurrence_count"] < 3
            ]

            for key in expired_patterns:
                del self.feedback_patterns[key]

        except Exception as e:
            logger.error(f"反馈模式更新失败: {str(e)}")

    async def _generate_pattern_key(self, feedback: Dict[str, Any]) -> str:
        """生成模式键"""
        try:
            content = feedback.get("content", {})
            keywords = content.get("keywords", [])
            structured = content.get("structured", {})

            # 基于关键词和关键字段生成模式键
            key_parts = []

            # 添加前3个关键词
            key_parts.extend(keywords[:3])

            # 添加关键字段
            key_fields = ["error_code", "module", "component", "operation"]
            for field in key_fields:
                if field in structured:
                    key_parts.append(f"{field}:{structured[field]}")

            return "_".join(sorted(key_parts)) if key_parts else "default_pattern"

        except Exception as e:
            logger.error(f"模式键生成失败: {str(e)}")
            return "error_pattern"

    async def process_feedback(
        self, performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理性能数据并生成反馈

        Args:
            performance_data: 性能数据

        Returns:
            Dict: 处理后的反馈结果
        """
        try:
            logger.info("开始处理性能反馈")

            # 创建反馈数据
            feedback_data = {
                "performance_data": performance_data,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "feedback_type": "performance_analysis",
            }

            # 提交反馈
            feedback_id = await self.submit_feedback(feedback_data)

            # 等待处理完成（简化实现）
            await asyncio.sleep(0.1)

            # 查找处理结果
            processed_feedback = await self._find_processed_feedback(feedback_id)

            if processed_feedback:
                evolution_guidance = processed_feedback.get("evolution_guidance", {})
                logger.info(
                    f"性能反馈处理完成，生成{len(evolution_guidance.get('recommendations', []))}条指导"
                )
                return evolution_guidance
            else:
                logger.warning("未找到处理后的反馈")
                return {
                    "guidance_id": str(uuid.uuid4()),
                    "confidence": 0.0,
                    "recommendations": [],
                    "warnings": ["反馈处理结果未找到"],
                }

        except Exception as e:
            logger.error(f"性能反馈处理失败: {str(e)}", exc_info=True)
            return {
                "guidance_id": str(uuid.uuid4()),
                "error": str(e),
                "confidence": 0.0,
                "recommendations": [],
            }

    async def _find_processed_feedback(
        self, feedback_id: str
    ) -> Optional[Dict[str, Any]]:
        """查找处理后的反馈"""
        for feedback in reversed(self.processed_feedback):
            if feedback.get("feedback_id") == feedback_id:
                return feedback
        return None

    async def get_feedback_insights(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """
        获取反馈洞察

        Args:
            time_range_hours: 时间范围(小时)

        Returns:
            Dict: 反馈洞察
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=time_range_hours)

            recent_feedback = [
                fb
                for fb in self.processed_feedback
                if datetime.fromisoformat(fb["timestamp"].replace("Z", "+00:00"))
                >= cutoff_time
            ]

            insights = {
                "time_range": f"last_{time_range_hours}_hours",
                "total_feedback": len(recent_feedback),
                "summary": await self._generate_insights_summary(recent_feedback),
                "patterns": await self._analyze_feedback_patterns(recent_feedback),
                "trends": await self._analyze_feedback_trends(recent_feedback),
                "recommendations": await self._generate_insights_recommendations(
                    recent_feedback
                ),
            }

            return insights

        except Exception as e:
            logger.error(f"反馈洞察生成失败: {str(e)}")
            return {
                "error": str(e),
                "time_range": f"last_{time_range_hours}_hours",
                "total_feedback": 0,
            }

    async def _generate_insights_summary(
        self, feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成洞察摘要"""
        try:
            if not feedback_list:
                return {"message": "无近期反馈数据"}

            # 统计基本信息
            type_distribution = Counter(
                fb.get("type", "unknown") for fb in feedback_list
            )
            source_distribution = Counter(
                fb.get("source", "unknown") for fb in feedback_list
            )
            priority_distribution = Counter(
                fb.get("priority", "medium") for fb in feedback_list
            )

            # 计算平均情感
            sentiments = [
                fb.get("content", {}).get("sentiment", 0) for fb in feedback_list
            ]
            avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

            # 计算指导置信度
            confidences = [
                fb.get("evolution_guidance", {}).get("confidence", 0)
                for fb in feedback_list
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            return {
                "feedback_count": len(feedback_list),
                "type_distribution": dict(type_distribution),
                "source_distribution": dict(source_distribution),
                "priority_distribution": dict(priority_distribution),
                "average_sentiment": avg_sentiment,
                "average_confidence": avg_confidence,
                "time_period": f"{len(feedback_list)}条反馈",
            }

        except Exception as e:
            logger.error(f"洞察摘要生成失败: {str(e)}")
            return {"error": str(e)}

    async def _analyze_feedback_patterns(
        self, feedback_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """分析反馈模式"""
        try:
            patterns = []

            # 分析高频关键词
            all_keywords = []
            for fb in feedback_list:
                keywords = fb.get("content", {}).get("keywords", [])
                all_keywords.extend(keywords)

            keyword_freq = Counter(all_keywords)
            top_keywords = keyword_freq.most_common(5)

            for keyword, count in top_keywords:
                patterns.append(
                    {
                        "type": "keyword_pattern",
                        "pattern": keyword,
                        "frequency": count,
                        "description": f"高频关键词: {keyword}",
                        "confidence": min(1.0, count / len(feedback_list)),
                    }
                )

            # 分析类型-来源关联
            type_source_pairs = [
                (fb.get("type"), fb.get("source")) for fb in feedback_list
            ]
            pair_freq = Counter(type_source_pairs)

            for (fb_type, source), count in pair_freq.most_common(3):
                patterns.append(
                    {
                        "type": "type_source_correlation",
                        "pattern": f"{fb_type}_{source}",
                        "frequency": count,
                        "description": f"{source}来源的{fb_type}反馈频繁",
                        "confidence": min(1.0, count / len(feedback_list)),
                    }
                )

            return patterns

        except Exception as e:
            logger.error(f"反馈模式分析失败: {str(e)}")
            return [{"type": "analysis_error", "error": str(e)}]

    async def _analyze_feedback_trends(
        self, feedback_list: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """分析反馈趋势"""
        try:
            if len(feedback_list) < 10:
                return {"message": "数据不足进行趋势分析"}

            # 按时间窗口分析
            hourly_feedback = defaultdict(list)
            for fb in feedback_list:
                timestamp = datetime.fromisoformat(
                    fb["timestamp"].replace("Z", "+00:00")
                )
                hour_key = timestamp.replace(minute=0, second=0, microsecond=0)
                hourly_feedback[hour_key].append(fb)

            # 计算每小时指标
            hours = sorted(hourly_feedback.keys())
            sentiment_trend = []
            volume_trend = []

            for hour in hours[-24:]:  # 最近24小时
                hour_feedback = hourly_feedback[hour]
                sentiments = [
                    fb.get("content", {}).get("sentiment", 0) for fb in hour_feedback
                ]
                avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

                sentiment_trend.append(avg_sentiment)
                volume_trend.append(len(hour_feedback))

            # 分析趋势
            sentiment_slope = await self._calculate_trend_slope(sentiment_trend)
            volume_slope = await self._calculate_trend_slope(volume_trend)

            return {
                "sentiment_trend": (
                    "improving"
                    if sentiment_slope > 0.01
                    else "declining" if sentiment_slope < -0.01 else "stable"
                ),
                "volume_trend": (
                    "increasing"
                    if volume_slope > 0.1
                    else "decreasing" if volume_slope < -0.1 else "stable"
                ),
                "sentiment_slope": sentiment_slope,
                "volume_slope": volume_slope,
                "analysis_period": f"{len(hours)}小时",
            }

        except Exception as e:
            logger.error(f"反馈趋势分析失败: {str(e)}")
            return {"error": str(e)}

    async def _calculate_trend_slope(self, values: List[float]) -> float:
        """计算趋势斜率"""
        if len(values) < 2:
            return 0.0

        x = list(range(len(values)))
        y = values

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x_i * x_i for x_i in x)

        numerator = n * sum_xy - sum_x * sum_y
        denominator = n * sum_x2 - sum_x * sum_x

        return numerator / denominator if denominator != 0 else 0.0

    async def _generate_insights_recommendations(
        self, feedback_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """生成洞察建议"""
        recommendations = []

        try:
            insights = await self._generate_insights_summary(feedback_list)
            trends = await self._analyze_feedback_trends(feedback_list)

            # 基于负面反馈比例的建议
            type_dist = insights.get("type_distribution", {})
            negative_count = type_dist.get("negative", 0) + type_dist.get("critical", 0)
            total_count = insights.get("feedback_count", 1)
            negative_ratio = negative_count / total_count

            if negative_ratio > 0.3:
                recommendations.append(
                    {
                        "type": "process_improvement",
                        "priority": "high",
                        "description": f"负面反馈比例较高({negative_ratio:.1%})，建议重点改进",
                        "action": "分析负面反馈根本原因并实施纠正措施",
                    }
                )

            # 基于情感趋势的建议
            sentiment_trend = trends.get("sentiment_trend", "stable")
            if sentiment_trend == "declining":
                recommendations.append(
                    {
                        "type": "proactive_measure",
                        "priority": "medium",
                        "description": "检测到用户情感下降趋势",
                        "action": "实施预防性改进措施阻止趋势恶化",
                    }
                )

            # 基于反馈来源的建议
            source_dist = insights.get("source_distribution", {})
            if source_dist.get("error_reports", 0) > total_count * 0.2:
                recommendations.append(
                    {
                        "type": "quality_assurance",
                        "priority": "high",
                        "description": "错误报告比例较高，表明系统稳定性问题",
                        "action": "加强错误处理和系统稳定性测试",
                    }
                )

            return recommendations[:5]  # 返回前5个建议

        except Exception as e:
            logger.error(f"洞察建议生成失败: {str(e)}")
            return [
                {
                    "type": "analysis_error",
                    "priority": "medium",
                    "description": f"洞察分析过程中发生错误: {str(e)}",
                }
            ]

    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            # 检查处理状态
            queue_size = self.feedback_queue.qsize()
            processed_count = len(self.processed_feedback)

            # 评估处理效率
            processing_efficiency = min(
                1.0, processed_count / (processed_count + queue_size + 1)
            )

            # 检查组件状态
            components_healthy = all(
                [
                    self.sentiment_analyzer is not None,
                    self.pattern_miner is not None,
                    self.correlation_engine is not None,
                ]
            )

            # 评估整体健康状态
            if components_healthy and processing_efficiency > 0.7:
                status = "healthy"
            elif components_healthy and processing_efficiency > 0.3:
                status = "degraded"
            else:
                status = "unhealthy"

            return {
                "status": status,
                "initialized": self.is_initialized,
                "running": self.running,
                "queue_size": queue_size,
                "processed_count": processed_count,
                "processing_efficiency": processing_efficiency,
                "components_healthy": components_healthy,
                "learning_model_size": len(self.learning_model),
                "pattern_count": len(self.feedback_patterns),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self.is_initialized,
                "running": self.running,
            }

    async def stop(self):
        """停止反馈处理器"""
        logger.info("正在停止反馈处理器...")

        self.running = False

        if self.processing_task:
            self.processing_task.cancel()

        # 等待处理完成
        await asyncio.sleep(1)

        logger.info("反馈处理器已停止")


# 辅助分析组件类
class SentimentAnalyzer:
    """情感分析器"""

    async def analyze(self, data: Any) -> float:
        """分析情感"""
        try:
            text = str(data)

            # 简单的情感词分析
            positive_words = {
                "good",
                "great",
                "excellent",
                "fast",
                "smooth",
                "reliable",
                "stable",
                "efficient",
            }
            negative_words = {
                "bad",
                "poor",
                "slow",
                "error",
                "crash",
                "fail",
                "broken",
                "unstable",
            }

            words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))

            positive_count = len(words & positive_words)
            negative_count = len(words & negative_words)

            total = positive_count + negative_count
            if total == 0:
                return 0.0

            sentiment = (positive_count - negative_count) / total
            return max(-1.0, min(1.0, sentiment))

        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return 0.0

    async def analyze_detailed(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """详细情感分析"""
        base_sentiment = await self.analyze(feedback)

        return {
            "score": base_sentiment,
            "magnitude": abs(base_sentiment),
            "category": (
                "positive"
                if base_sentiment > 0.1
                else "negative" if base_sentiment < -0.1 else "neutral"
            ),
            "confidence": min(1.0, abs(base_sentiment) * 2),  # 基于强度的置信度
        }


class PatternMiner:
    """模式挖掘器"""

    async def match_patterns(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """匹配模式"""
        # 简化实现 - 实际中会使用更复杂的模式匹配算法
        return [
            {"pattern_type": "basic", "confidence": 0.5, "description": "基础模式匹配"}
        ]


class CorrelationEngine:
    """关联引擎"""

    async def find_correlations(
        self,
        current_feedback: Dict[str, Any],
        historical_feedback: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """查找关联"""
        # 简化实现 - 实际中会使用关联分析算法
        if len(historical_feedback) < 5:
            return []

        return [
            {
                "type": "temporal",
                "confidence": 0.3,
                "description": "时间关联模式",
                "related_count": min(5, len(historical_feedback)),
            }
        ]
