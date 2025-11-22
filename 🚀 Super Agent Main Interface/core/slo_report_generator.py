#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SLO报告生成器
P3-403: 实现SLO报告生成
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class SLOStatus(str, Enum):
    """SLO状态"""
    MET = "met"  # 达标
    AT_RISK = "at_risk"  # 有风险
    BREACHED = "breached"  # 违反


@dataclass
class SLOTarget:
    """SLO目标"""
    name: str
    target_value: float  # 目标值
    measurement_window: str = "30d"  # 测量窗口 (1d/7d/30d)
    error_budget: float = 0.01  # 错误预算 (1%)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLOMetric:
    """SLO指标"""
    name: str
    current_value: float
    target: SLOTarget
    status: SLOStatus
    error_budget_remaining: float
    error_budget_consumed: float
    measurement_period: str
    data_points: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["target"] = asdict(self.target)
        return data


class SLOReportGenerator:
    """
    SLO报告生成器
    
    功能：
    1. 定义SLO目标
    2. 收集性能数据
    3. 计算SLO状态
    4. 生成SLO报告
    """
    
    def __init__(self):
        self.slo_targets: Dict[str, SLOTarget] = {}
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # 默认SLO目标
        self._initialize_default_slos()
        
        logger.info("SLO报告生成器初始化完成")
    
    def _initialize_default_slos(self):
        """初始化默认SLO目标"""
        # 2秒SLO（响应时间）
        self.slo_targets["response_time_2s"] = SLOTarget(
            name="2秒响应时间SLO",
            target_value=2000.0,  # 2秒 = 2000毫秒
            measurement_window="30d",
            error_budget=0.01,  # 1%错误预算
            metadata={"description": "95%的请求在2秒内完成"},
        )
        
        # 可用性SLO
        self.slo_targets["availability_99_9"] = SLOTarget(
            name="99.9%可用性SLO",
            target_value=99.9,
            measurement_window="30d",
            error_budget=0.001,  # 0.1%错误预算
            metadata={"description": "系统可用性达到99.9%"},
        )
        
        # 错误率SLO
        self.slo_targets["error_rate"] = SLOTarget(
            name="错误率SLO",
            target_value=0.1,  # 0.1%
            measurement_window="30d",
            error_budget=0.01,
            metadata={"description": "错误率低于0.1%"},
        )
    
    def set_slo_target(
        self,
        name: str,
        target_value: float,
        measurement_window: str = "30d",
        error_budget: float = 0.01,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SLOTarget:
        """
        设置SLO目标
        
        Args:
            name: SLO名称
            target_value: 目标值
            measurement_window: 测量窗口
            error_budget: 错误预算
            metadata: 元数据
            
        Returns:
            SLO目标对象
        """
        target = SLOTarget(
            name=name,
            target_value=target_value,
            measurement_window=measurement_window,
            error_budget=error_budget,
            metadata=metadata or {},
        )
        
        self.slo_targets[name] = target
        
        logger.info(f"设置SLO目标: {name} = {target_value}")
        
        return target
    
    def record_metric(
        self,
        slo_name: str,
        value: float,
        timestamp: Optional[str] = None,
    ):
        """
        记录指标数据
        
        Args:
            slo_name: SLO名称
            value: 指标值
            timestamp: 时间戳
        """
        if slo_name not in self.metrics_history:
            self.metrics_history[slo_name] = []
        
        self.metrics_history[slo_name].append({
            "value": value,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
        })
        
        # 只保留最近10000条记录
        if len(self.metrics_history[slo_name]) > 10000:
            self.metrics_history[slo_name] = self.metrics_history[slo_name][-10000:]
    
    def calculate_slo_status(
        self,
        slo_name: str,
        measurement_period: Optional[str] = None,
    ) -> SLOMetric:
        """
        计算SLO状态
        
        Args:
            slo_name: SLO名称
            measurement_period: 测量周期（可选，默认使用SLO目标的窗口）
            
        Returns:
            SLO指标
        """
        target = self.slo_targets.get(slo_name)
        if not target:
            raise ValueError(f"SLO目标不存在: {slo_name}")
        
        # 确定测量周期
        if not measurement_period:
            measurement_period = target.measurement_window
        
        # 获取测量周期内的数据
        data_points = self._get_data_points(slo_name, measurement_period)
        
        if not data_points:
            # 无数据，返回默认状态
            return SLOMetric(
                name=slo_name,
                current_value=0.0,
                target=target,
                status=SLOStatus.AT_RISK,
                error_budget_remaining=target.error_budget,
                error_budget_consumed=0.0,
                measurement_period=measurement_period,
                data_points=[],
            )
        
        # 计算当前值
        current_value = self._calculate_current_value(slo_name, data_points, target)
        
        # 计算SLO状态
        status, error_budget_consumed = self._evaluate_slo(
            current_value=current_value,
            target=target,
            data_points=data_points,
        )
        
        error_budget_remaining = target.error_budget - error_budget_consumed
        
        return SLOMetric(
            name=slo_name,
            current_value=current_value,
            target=target,
            status=status,
            error_budget_remaining=error_budget_remaining,
            error_budget_consumed=error_budget_consumed,
            measurement_period=measurement_period,
            data_points=data_points[-100:],  # 只保留最近100个数据点
        )
    
    def _get_data_points(
        self,
        slo_name: str,
        measurement_period: str,
    ) -> List[Dict[str, Any]]:
        """获取测量周期内的数据点"""
        if slo_name not in self.metrics_history:
            return []
        
        # 解析测量周期
        days = self._parse_period(measurement_period)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 过滤数据点
        data_points = [
            dp for dp in self.metrics_history[slo_name]
            if datetime.fromisoformat(dp["timestamp"].replace("Z", "+00:00")) >= cutoff_date
        ]
        
        return data_points
    
    def _parse_period(self, period: str) -> int:
        """解析时间周期"""
        if period.endswith("d"):
            return int(period[:-1])
        elif period.endswith("h"):
            return int(period[:-1]) / 24
        elif period.endswith("m"):
            return int(period[:-1]) / 24 / 60
        else:
            return 30  # 默认30天
    
    def _calculate_current_value(
        self,
        slo_name: str,
        data_points: List[Dict[str, Any]],
        target: SLOTarget,
    ) -> float:
        """计算当前指标值"""
        if not data_points:
            return 0.0
        
        values = [dp["value"] for dp in data_points]
        
        # 根据SLO类型计算
        if "response_time" in slo_name:
            # 响应时间：使用P95
            sorted_values = sorted(values)
            p95_index = int(len(sorted_values) * 0.95)
            return sorted_values[p95_index] if sorted_values else 0.0
        
        elif "availability" in slo_name:
            # 可用性：成功率百分比
            success_count = sum(1 for v in values if v >= target.target_value)
            return (success_count / len(values) * 100) if values else 0.0
        
        elif "error_rate" in slo_name:
            # 错误率：平均值
            return sum(values) / len(values) if values else 0.0
        
        else:
            # 默认：平均值
            return sum(values) / len(values) if values else 0.0
    
    def _evaluate_slo(
        self,
        current_value: float,
        target: SLOTarget,
        data_points: List[Dict[str, Any]],
    ) -> tuple[SLOStatus, float]:
        """
        评估SLO状态
        
        Returns:
            (状态, 错误预算消耗)
        """
        # 计算错误预算消耗
        if "response_time" in target.name.lower():
            # 响应时间：超过目标值的请求比例
            exceeded_count = sum(1 for dp in data_points if dp["value"] > target.target_value)
            error_budget_consumed = exceeded_count / len(data_points) if data_points else 0.0
        
        elif "availability" in target.name.lower():
            # 可用性：低于目标值的比例
            below_count = sum(1 for dp in data_points if dp["value"] < target.target_value)
            error_budget_consumed = below_count / len(data_points) if data_points else 0.0
        
        elif "error_rate" in target.name.lower():
            # 错误率：超过目标值的比例
            exceeded_count = sum(1 for dp in data_points if dp["value"] > target.target_value)
            error_budget_consumed = exceeded_count / len(data_points) if data_points else 0.0
        
        else:
            error_budget_consumed = 0.0
        
        # 判断状态
        if error_budget_consumed >= target.error_budget:
            status = SLOStatus.BREACHED
        elif error_budget_consumed >= target.error_budget * 0.8:
            status = SLOStatus.AT_RISK
        else:
            status = SLOStatus.MET
        
        return status, error_budget_consumed
    
    def generate_slo_report(
        self,
        measurement_period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        生成SLO报告
        
        Args:
            measurement_period: 测量周期（可选）
            
        Returns:
            SLO报告
        """
        logger.info("生成SLO报告")
        
        metrics = []
        for slo_name in self.slo_targets.keys():
            try:
                metric = self.calculate_slo_status(slo_name, measurement_period)
                metrics.append(metric)
            except Exception as e:
                logger.error(f"计算SLO状态失败: {slo_name} - {e}")
        
        # 计算总体状态
        met_count = sum(1 for m in metrics if m.status == SLOStatus.MET)
        at_risk_count = sum(1 for m in metrics if m.status == SLOStatus.AT_RISK)
        breached_count = sum(1 for m in metrics if m.status == SLOStatus.BREACHED)
        
        report = {
            "report_id": f"slo_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "measurement_period": measurement_period or "30d",
            "summary": {
                "total_slos": len(metrics),
                "met": met_count,
                "at_risk": at_risk_count,
                "breached": breached_count,
                "overall_status": (
                    "breached" if breached_count > 0
                    else "at_risk" if at_risk_count > 0
                    else "met"
                ),
            },
            "metrics": [m.to_dict() for m in metrics],
        }
        
        logger.info(f"SLO报告生成完成: {met_count}达标, {at_risk_count}有风险, {breached_count}违反")
        
        return report


_slo_report_generator: Optional[SLOReportGenerator] = None


def get_slo_report_generator() -> SLOReportGenerator:
    """获取SLO报告生成器实例"""
    global _slo_report_generator
    if _slo_report_generator is None:
        _slo_report_generator = SLOReportGenerator()
    return _slo_report_generator

