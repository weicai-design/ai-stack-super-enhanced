#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习曲线追踪器
P2-303: 实现学习曲线功能
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from collections import defaultdict

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


class LearningCurveTracker:
    """
    学习曲线追踪器
    
    功能：
    1. 追踪学习进度
    2. 记录准确率和损失值
    3. 生成学习曲线数据
    4. 分析学习趋势
    """
    
    def __init__(self):
        self.curves: Dict[str, LearningCurve] = {}
        self.learning_history: List[Dict[str, Any]] = []
        
        logger.info("学习曲线追踪器初始化完成")
    
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


_learning_curve_tracker: Optional[LearningCurveTracker] = None


def get_learning_curve_tracker() -> LearningCurveTracker:
    """获取学习曲线追踪器实例"""
    global _learning_curve_tracker
    if _learning_curve_tracker is None:
        _learning_curve_tracker = LearningCurveTracker()
    return _learning_curve_tracker

