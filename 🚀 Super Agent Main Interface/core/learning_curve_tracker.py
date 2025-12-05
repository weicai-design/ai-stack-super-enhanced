#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习曲线追踪器
P2-303: 实现学习曲线功能
"""

from __future__ import annotations

import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class LearningPoint:
    """学习点"""
    timestamp: str
    accuracy: float  # 准确率 0-100
    loss: Optional[float] = None  # 损失值
    epoch: Optional[int] = None  # 训练轮次
    dataset_size: Optional[int] = None  # 数据集大小
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningCurve:
    """学习曲线"""
    curve_id: str
    model_name: str
    task_type: str
    points: List[LearningPoint] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["points"] = [p.to_dict() for p in self.points]
        return data


@dataclass
class BehaviorLog:
    """行为日志"""
    log_id: str
    user_id: str
    action_type: str  # view/use/modify/query/execute等
    module: str
    function: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    success: bool = True
    duration: Optional[float] = None  # 执行时长（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ModelStrategy:
    """模型策略"""
    strategy_id: str
    model_name: str
    strategy_name: str
    strategy_config: Dict[str, Any]
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    is_active: bool = True
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExpertSuggestion:
    """专家建议"""
    suggestion_id: str
    curve_id: Optional[str] = None
    user_id: Optional[str] = None
    suggestion_type: str = "general"  # learning/optimization/strategy/behavior
    title: str = ""
    content: str = ""
    priority: str = "medium"  # low/medium/high/critical
    status: str = "pending"  # pending/accepted/rejected/implemented
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    feedback: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LearningCurveTracker:
    """
    学习曲线追踪器（生产级实现 - 6.2）
    
    功能：
    1. 追踪学习进度
    2. 记录准确率和损失值
    3. 生成学习曲线数据
    4. 分析学习趋势
    5. 行为日志聚合（6.2新增）
    6. 模型策略更新（6.2新增）
    7. 专家建议表联动（6.2新增）
    """
    
    def __init__(self):
        self.curves: Dict[str, LearningCurve] = {}
        self.learning_history: List[Dict[str, Any]] = []
        
        # 行为日志（6.2新增）
        self.behavior_logs: List[BehaviorLog] = []
        self.max_logs = 100000  # 最大日志数量
        
        # 模型策略（6.2新增）
        self.model_strategies: Dict[str, List[ModelStrategy]] = defaultdict(list)  # model_name -> [strategies]
        self.active_strategies: Dict[str, ModelStrategy] = {}  # model_name -> active_strategy
        
        # 专家建议表（6.2新增）
        self.expert_suggestions: Dict[str, ExpertSuggestion] = {}
        
        logger.info("学习曲线追踪器初始化完成（生产级 - 6.2）")
    
    def create_curve(
        self,
        model_name: str,
        task_type: str,
        curve_id: Optional[str] = None,
    ) -> LearningCurve:
        """
        创建学习曲线
        
        Args:
            model_name: 模型名称
            task_type: 任务类型
            curve_id: 曲线ID（可选）
            
        Returns:
            学习曲线对象
        """
        if not curve_id:
            curve_id = f"curve_{model_name}_{task_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        curve = LearningCurve(
            curve_id=curve_id,
            model_name=model_name,
            task_type=task_type,
        )
        
        self.curves[curve_id] = curve
        
        logger.info(f"创建学习曲线: {curve_id} - {model_name}")
        
        return curve
    
    def add_point(
        self,
        curve_id: str,
        accuracy: float,
        loss: Optional[float] = None,
        epoch: Optional[int] = None,
        dataset_size: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        添加学习点
        
        Args:
            curve_id: 曲线ID
            accuracy: 准确率
            loss: 损失值
            epoch: 训练轮次
            dataset_size: 数据集大小
            metadata: 元数据
            
        Returns:
            是否成功
        """
        if curve_id not in self.curves:
            return False
        
        curve = self.curves[curve_id]
        
        point = LearningPoint(
            timestamp=datetime.utcnow().isoformat() + "Z",
            accuracy=max(0.0, min(100.0, accuracy)),
            loss=loss,
            epoch=epoch,
            dataset_size=dataset_size,
            metadata=metadata or {},
        )
        
        curve.points.append(point)
        curve.updated_at = datetime.utcnow().isoformat() + "Z"
        
        # 记录学习历史
        self.learning_history.append({
            "curve_id": curve_id,
            "model_name": curve.model_name,
            "task_type": curve.task_type,
            "point": point.to_dict(),
        })
        
        logger.debug(f"添加学习点: {curve_id} - 准确率: {accuracy:.2f}%")
        
        return True
    
    def get_curve(self, curve_id: str) -> Optional[LearningCurve]:
        """获取学习曲线"""
        return self.curves.get(curve_id)
    
    def get_curve_data(
        self,
        curve_id: str,
        include_loss: bool = False,
    ) -> Dict[str, Any]:
        """
        获取学习曲线数据（用于图表展示）
        
        Args:
            curve_id: 曲线ID
            include_loss: 是否包含损失值
            
        Returns:
            曲线数据
        """
        curve = self.curves.get(curve_id)
        if not curve:
            return {}
        
        points = curve.points
        
        data = {
            "curve_id": curve_id,
            "model_name": curve.model_name,
            "task_type": curve.task_type,
            "timestamps": [p.timestamp for p in points],
            "accuracy": [p.accuracy for p in points],
            "epochs": [p.epoch for p in points] if any(p.epoch for p in points) else None,
        }
        
        if include_loss and any(p.loss for p in points):
            data["loss"] = [p.loss for p in points]
        
        # 计算趋势
        if len(points) >= 2:
            recent_accuracy = points[-1].accuracy
            previous_accuracy = points[-2].accuracy
            trend = "上升" if recent_accuracy > previous_accuracy else "下降" if recent_accuracy < previous_accuracy else "平稳"
            data["trend"] = trend
            data["improvement"] = recent_accuracy - previous_accuracy
        
        # 统计信息
        if points:
            data["statistics"] = {
                "total_points": len(points),
                "current_accuracy": points[-1].accuracy,
                "max_accuracy": max(p.accuracy for p in points),
                "min_accuracy": min(p.accuracy for p in points),
                "avg_accuracy": sum(p.accuracy for p in points) / len(points),
            }
        
        return data
    
    def list_curves(
        self,
        model_name: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> List[LearningCurve]:
        """列出学习曲线"""
        curves = list(self.curves.values())
        
        if model_name:
            curves = [c for c in curves if c.model_name == model_name]
        if task_type:
            curves = [c for c in curves if c.task_type == task_type]
        
        # 按更新时间倒序
        curves.sort(key=lambda c: c.updated_at, reverse=True)
        
        return curves
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        total_curves = len(self.curves)
        total_points = sum(len(c.points) for c in self.curves.values())
        
        # 按模型统计
        model_stats = defaultdict(lambda: {"curves": 0, "points": 0, "avg_accuracy": 0.0})
        for curve in self.curves.values():
            model_stats[curve.model_name]["curves"] += 1
            model_stats[curve.model_name]["points"] += len(curve.points)
            if curve.points:
                avg_acc = sum(p.accuracy for p in curve.points) / len(curve.points)
                model_stats[curve.model_name]["avg_accuracy"] = avg_acc
        
        # 按任务类型统计
        task_stats = defaultdict(lambda: {"curves": 0, "points": 0})
        for curve in self.curves.values():
            task_stats[curve.task_type]["curves"] += 1
            task_stats[curve.task_type]["points"] += len(curve.points)
        
        return {
            "total_curves": total_curves,
            "total_points": total_points,
            "model_statistics": dict(model_stats),
            "task_statistics": dict(task_stats),
        }
    
    # ============ 行为日志聚合（6.2新增） ============
    
    def record_behavior(
        self,
        user_id: str,
        action_type: str,
        module: str,
        function: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration: Optional[float] = None,
    ) -> BehaviorLog:
        """
        记录行为日志
        
        Args:
            user_id: 用户ID
            action_type: 行为类型
            module: 模块名称
            function: 功能名称
            context: 上下文信息
            success: 是否成功
            duration: 执行时长（秒）
            
        Returns:
            行为日志对象
        """
        log = BehaviorLog(
            log_id=f"log_{uuid4()}",
            user_id=user_id,
            action_type=action_type,
            module=module,
            function=function,
            context=context or {},
            success=success,
            duration=duration,
        )
        
        self.behavior_logs.append(log)
        
        # 限制日志数量
        if len(self.behavior_logs) > self.max_logs:
            self.behavior_logs = self.behavior_logs[-self.max_logs:]
        
        logger.debug(f"记录行为日志: {user_id} - {action_type} - {module}::{function}")
        
        return log
    
    def aggregate_behavior_logs(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        action_type: Optional[str] = None,
        module: Optional[str] = None,
        group_by: str = "hour",  # hour/day/week/month
    ) -> Dict[str, Any]:
        """
        聚合行为日志
        
        Args:
            user_id: 用户ID（可选）
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            action_type: 行为类型（可选）
            module: 模块名称（可选）
            group_by: 分组方式（hour/day/week/month）
            
        Returns:
            聚合结果
        """
        # 过滤日志
        filtered_logs = self.behavior_logs
        
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        if start_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp >= start_time]
        if end_time:
            filtered_logs = [log for log in filtered_logs if log.timestamp <= end_time]
        if action_type:
            filtered_logs = [log for log in filtered_logs if log.action_type == action_type]
        if module:
            filtered_logs = [log for log in filtered_logs if log.module == module]
        
        # 按时间分组
        grouped_data = defaultdict(lambda: {
            "count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_duration": 0.0,
            "actions_by_type": defaultdict(int),
            "modules": defaultdict(int),
        })
        
        for log in filtered_logs:
            # 解析时间并分组
            timestamp = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
            
            if group_by == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                key = timestamp.strftime("%Y-%m-%d")
            elif group_by == "week":
                week_start = timestamp - timedelta(days=timestamp.weekday())
                key = week_start.strftime("%Y-W%W")
            elif group_by == "month":
                key = timestamp.strftime("%Y-%m")
            else:
                key = timestamp.strftime("%Y-%m-%d")
            
            group = grouped_data[key]
            group["count"] += 1
            if log.success:
                group["success_count"] += 1
            else:
                group["failure_count"] += 1
            if log.duration:
                group["total_duration"] += log.duration
            group["actions_by_type"][log.action_type] += 1
            group["modules"][log.module] += 1
        
        # 转换格式
        aggregated = {
            "period": {
                "start_time": start_time,
                "end_time": end_time,
                "group_by": group_by,
            },
            "total_logs": len(filtered_logs),
            "grouped_data": {
                key: {
                    "count": data["count"],
                    "success_count": data["success_count"],
                    "failure_count": data["failure_count"],
                    "success_rate": (data["success_count"] / data["count"] * 100) if data["count"] > 0 else 0,
                    "avg_duration": (data["total_duration"] / data["count"]) if data["count"] > 0 else 0,
                    "actions_by_type": dict(data["actions_by_type"]),
                    "modules": dict(data["modules"]),
                }
                for key, data in grouped_data.items()
            },
        }
        
        logger.info(f"聚合行为日志: {len(filtered_logs)}条日志，{len(grouped_data)}个分组")
        
        return aggregated
    
    def analyze_behavior_patterns(
        self,
        user_id: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        分析行为模式
        
        Args:
            user_id: 用户ID（可选）
            days: 分析天数
            
        Returns:
            行为模式分析结果
        """
        end_time = datetime.utcnow().isoformat() + "Z"
        start_time = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        # 获取日志
        filtered_logs = self.behavior_logs
        if user_id:
            filtered_logs = [log for log in filtered_logs if log.user_id == user_id]
        filtered_logs = [
            log for log in filtered_logs
            if start_time <= log.timestamp <= end_time
        ]
        
        if not filtered_logs:
            return {
                "patterns": {},
                "insights": [],
            }
        
        # 分析模式
        patterns = {
            "most_used_modules": defaultdict(int),
            "most_used_functions": defaultdict(int),
            "action_type_distribution": defaultdict(int),
            "time_distribution": defaultdict(int),  # 按小时
            "day_distribution": defaultdict(int),  # 按星期
            "success_rate_by_module": defaultdict(lambda: {"success": 0, "total": 0}),
        }
        
        for log in filtered_logs:
            patterns["most_used_modules"][log.module] += 1
            if log.function:
                patterns["most_used_functions"][f"{log.module}::{log.function}"] += 1
            patterns["action_type_distribution"][log.action_type] += 1
            
            timestamp = datetime.fromisoformat(log.timestamp.replace("Z", "+00:00"))
            patterns["time_distribution"][timestamp.hour] += 1
            patterns["day_distribution"][timestamp.weekday()] += 1
            
            module_stats = patterns["success_rate_by_module"][log.module]
            module_stats["total"] += 1
            if log.success:
                module_stats["success"] += 1
        
        # 生成洞察
        insights = []
        
        # 最常用模块
        if patterns["most_used_modules"]:
            top_module = max(patterns["most_used_modules"].items(), key=lambda x: x[1])
            insights.append(f"最常用模块: {top_module[0]} (使用{top_module[1]}次)")
        
        # 成功率分析
        for module, stats in patterns["success_rate_by_module"].items():
            if stats["total"] > 0:
                success_rate = stats["success"] / stats["total"] * 100
                if success_rate < 80:
                    insights.append(f"模块 {module} 成功率较低: {success_rate:.1f}%")
        
        # 时间模式
        if patterns["time_distribution"]:
            peak_hour = max(patterns["time_distribution"].items(), key=lambda x: x[1])
            insights.append(f"使用高峰期: {peak_hour[0]}:00 (使用{peak_hour[1]}次)")
        
        return {
            "patterns": {
                "most_used_modules": dict(sorted(patterns["most_used_modules"].items(), key=lambda x: x[1], reverse=True)[:10]),
                "most_used_functions": dict(sorted(patterns["most_used_functions"].items(), key=lambda x: x[1], reverse=True)[:10]),
                "action_type_distribution": dict(patterns["action_type_distribution"]),
                "time_distribution": dict(patterns["time_distribution"]),
                "day_distribution": dict(patterns["day_distribution"]),
                "success_rate_by_module": {
                    module: {
                        "success_rate": (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0,
                        "total": stats["total"],
                    }
                    for module, stats in patterns["success_rate_by_module"].items()
                },
            },
            "insights": insights,
        }
    
    # ============ 模型策略更新接口（6.2新增） ============
    
    def create_strategy(
        self,
        model_name: str,
        strategy_name: str,
        strategy_config: Dict[str, Any],
    ) -> ModelStrategy:
        """
        创建模型策略
        
        Args:
            model_name: 模型名称
            strategy_name: 策略名称
            strategy_config: 策略配置
            
        Returns:
            模型策略对象
        """
        # 检查是否已有同名策略
        existing_strategies = self.model_strategies.get(model_name, [])
        version = 1
        if existing_strategies:
            max_version = max(s.version for s in existing_strategies)
            version = max_version + 1
        
        strategy = ModelStrategy(
            strategy_id=f"strategy_{uuid4()}",
            model_name=model_name,
            strategy_name=strategy_name,
            strategy_config=strategy_config,
            version=version,
        )
        
        self.model_strategies[model_name].append(strategy)
        
        logger.info(f"创建模型策略: {model_name} - {strategy_name} (v{version})")
        
        return strategy
    
    def update_strategy(
        self,
        strategy_id: str,
        strategy_config: Optional[Dict[str, Any]] = None,
        performance_metrics: Optional[Dict[str, Any]] = None,
    ) -> Optional[ModelStrategy]:
        """
        更新模型策略
        
        Args:
            strategy_id: 策略ID
            strategy_config: 策略配置（可选）
            performance_metrics: 性能指标（可选）
            
        Returns:
            更新后的策略对象
        """
        # 查找策略
        strategy = None
        for strategies in self.model_strategies.values():
            for s in strategies:
                if s.strategy_id == strategy_id:
                    strategy = s
                    break
            if strategy:
                break
        
        if not strategy:
            logger.error(f"策略不存在: {strategy_id}")
            return None
        
        # 更新配置
        if strategy_config:
            strategy.strategy_config.update(strategy_config)
        
        # 更新性能指标
        if performance_metrics:
            strategy.performance_metrics.update(performance_metrics)
        
        strategy.updated_at = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"更新模型策略: {strategy_id}")
        
        return strategy
    
    def activate_strategy(
        self,
        strategy_id: str,
    ) -> bool:
        """
        激活模型策略
        
        Args:
            strategy_id: 策略ID
            
        Returns:
            是否成功
        """
        # 查找策略
        strategy = None
        for strategies in self.model_strategies.values():
            for s in strategies:
                if s.strategy_id == strategy_id:
                    strategy = s
                    break
            if strategy:
                break
        
        if not strategy:
            logger.error(f"策略不存在: {strategy_id}")
            return False
        
        # 停用同模型的其他策略
        for s in self.model_strategies.get(strategy.model_name, []):
            s.is_active = False
        
        # 激活当前策略
        strategy.is_active = True
        self.active_strategies[strategy.model_name] = strategy
        
        logger.info(f"激活模型策略: {strategy_id} - {strategy.model_name}")
        
        return True
    
    def get_strategy(
        self,
        model_name: str,
        strategy_id: Optional[str] = None,
    ) -> Optional[ModelStrategy]:
        """
        获取模型策略
        
        Args:
            model_name: 模型名称
            strategy_id: 策略ID（如果为None，返回激活的策略）
            
        Returns:
            模型策略对象
        """
        if strategy_id:
            for strategies in self.model_strategies.values():
                for s in strategies:
                    if s.strategy_id == strategy_id:
                        return s
            return None
        else:
            return self.active_strategies.get(model_name)
    
    def list_strategies(
        self,
        model_name: Optional[str] = None,
        active_only: bool = False,
    ) -> List[ModelStrategy]:
        """
        列出模型策略
        
        Args:
            model_name: 模型名称（可选）
            active_only: 是否只返回激活的策略
            
        Returns:
            策略列表
        """
        all_strategies = []
        
        if model_name:
            strategies = self.model_strategies.get(model_name, [])
            if active_only:
                strategies = [s for s in strategies if s.is_active]
            all_strategies.extend(strategies)
        else:
            for strategies in self.model_strategies.values():
                if active_only:
                    strategies = [s for s in strategies if s.is_active]
                all_strategies.extend(strategies)
        
        # 按更新时间倒序
        all_strategies.sort(key=lambda s: s.updated_at, reverse=True)
        
        return all_strategies
    
    # ============ 专家建议表联动（6.2新增） ============
    
    def generate_expert_suggestion(
        self,
        curve_id: Optional[str] = None,
        user_id: Optional[str] = None,
        suggestion_type: str = "general",
        title: str = "",
        content: str = "",
        priority: str = "medium",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExpertSuggestion:
        """
        生成专家建议
        
        Args:
            curve_id: 学习曲线ID（可选）
            user_id: 用户ID（可选）
            suggestion_type: 建议类型
            title: 建议标题
            content: 建议内容
            priority: 优先级
            metadata: 元数据
            
        Returns:
            专家建议对象
        """
        suggestion = ExpertSuggestion(
            suggestion_id=f"suggestion_{uuid4()}",
            curve_id=curve_id,
            user_id=user_id,
            suggestion_type=suggestion_type,
            title=title,
            content=content,
            priority=priority,
            metadata=metadata or {},
        )
        
        self.expert_suggestions[suggestion.suggestion_id] = suggestion
        
        logger.info(f"生成专家建议: {suggestion.suggestion_id} - {title}")
        
        return suggestion
    
    def generate_suggestions_from_curve(
        self,
        curve_id: str,
    ) -> List[ExpertSuggestion]:
        """
        从学习曲线生成专家建议
        
        Args:
            curve_id: 学习曲线ID
            
        Returns:
            专家建议列表
        """
        curve = self.curves.get(curve_id)
        if not curve:
            return []
        
        suggestions = []
        
        # 分析学习曲线
        if len(curve.points) >= 2:
            recent_points = curve.points[-10:] if len(curve.points) >= 10 else curve.points
            accuracies = [p.accuracy for p in recent_points]
            
            # 准确率下降建议
            if len(accuracies) >= 2 and accuracies[-1] < accuracies[-2]:
                suggestions.append(self.generate_expert_suggestion(
                    curve_id=curve_id,
                    suggestion_type="learning",
                    title="学习准确率下降",
                    content=f"检测到学习准确率从 {accuracies[-2]:.2f}% 下降到 {accuracies[-1]:.2f}%，建议检查训练数据质量或调整学习率。",
                    priority="high",
                    metadata={"accuracy_trend": "decreasing"},
                ))
            
            # 准确率停滞建议
            if len(accuracies) >= 5:
                recent_avg = sum(accuracies[-5:]) / 5
                previous_avg = sum(accuracies[-10:-5]) / 5 if len(accuracies) >= 10 else accuracies[0]
                if abs(recent_avg - previous_avg) < 1.0:
                    suggestions.append(self.generate_expert_suggestion(
                        curve_id=curve_id,
                        suggestion_type="optimization",
                        title="学习准确率停滞",
                        content=f"学习准确率在 {recent_avg:.2f}% 附近停滞，建议尝试调整模型架构或增加训练数据。",
                        priority="medium",
                        metadata={"accuracy_trend": "stagnant"},
                    ))
        
        return suggestions
    
    def generate_suggestions_from_behavior(
        self,
        user_id: str,
    ) -> List[ExpertSuggestion]:
        """
        从行为日志生成专家建议
        
        Args:
            user_id: 用户ID
            
        Returns:
            专家建议列表
        """
        # 分析行为模式
        patterns = self.analyze_behavior_patterns(user_id=user_id, days=30)
        
        suggestions = []
        
        # 基于行为模式生成建议
        if patterns.get("patterns"):
            success_rates = patterns["patterns"].get("success_rate_by_module", {})
            for module, stats in success_rates.items():
                if stats["total"] > 10 and stats.get("success_rate", 100) < 80:
                    suggestions.append(self.generate_expert_suggestion(
                        user_id=user_id,
                        suggestion_type="behavior",
                        title=f"模块 {module} 使用成功率较低",
                        content=f"模块 {module} 的成功率为 {stats.get('success_rate', 0):.1f}%，建议检查使用方式或查看相关文档。",
                        priority="medium",
                        metadata={"module": module, "success_rate": stats.get("success_rate", 0)},
                    ))
        
        return suggestions
    
    def update_suggestion_status(
        self,
        suggestion_id: str,
        status: str,
        feedback: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        更新建议状态
        
        Args:
            suggestion_id: 建议ID
            status: 新状态（pending/accepted/rejected/implemented）
            feedback: 反馈信息（可选）
            
        Returns:
            是否成功
        """
        suggestion = self.expert_suggestions.get(suggestion_id)
        if not suggestion:
            return False
        
        suggestion.status = status
        suggestion.updated_at = datetime.utcnow().isoformat() + "Z"
        
        if feedback:
            suggestion.feedback = feedback
        
        logger.info(f"更新建议状态: {suggestion_id} - {status}")
        
        return True
    
    def get_suggestions(
        self,
        curve_id: Optional[str] = None,
        user_id: Optional[str] = None,
        suggestion_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[ExpertSuggestion]:
        """
        获取专家建议
        
        Args:
            curve_id: 学习曲线ID（可选）
            user_id: 用户ID（可选）
            suggestion_type: 建议类型（可选）
            status: 状态（可选）
            limit: 返回数量限制
            
        Returns:
            专家建议列表
        """
        suggestions = list(self.expert_suggestions.values())
        
        if curve_id:
            suggestions = [s for s in suggestions if s.curve_id == curve_id]
        if user_id:
            suggestions = [s for s in suggestions if s.user_id == user_id]
        if suggestion_type:
            suggestions = [s for s in suggestions if s.suggestion_type == suggestion_type]
        if status:
            suggestions = [s for s in suggestions if s.status == status]
        
        # 按创建时间倒序
        suggestions.sort(key=lambda s: s.created_at, reverse=True)
        
        return suggestions[:limit]
    
    def link_suggestion_to_curve(
        self,
        suggestion_id: str,
        curve_id: str,
    ) -> bool:
        """
        将建议关联到学习曲线
        
        Args:
            suggestion_id: 建议ID
            curve_id: 学习曲线ID
            
        Returns:
            是否成功
        """
        suggestion = self.expert_suggestions.get(suggestion_id)
        if not suggestion:
            return False
        
        suggestion.curve_id = curve_id
        suggestion.updated_at = datetime.utcnow().isoformat() + "Z"
        
        logger.info(f"关联建议到学习曲线: {suggestion_id} -> {curve_id}")
        
        return True


_learning_curve_tracker: Optional[LearningCurveTracker] = None


def get_learning_curve_tracker() -> LearningCurveTracker:
    """获取学习曲线追踪器实例"""
    global _learning_curve_tracker
    if _learning_curve_tracker is None:
        _learning_curve_tracker = LearningCurveTracker()
    return _learning_curve_tracker

