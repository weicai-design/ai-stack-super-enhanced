"""
试算历史记录管理
保存和管理试算历史记录，支持对比分析
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class TrialHistory(Base):
    """试算历史记录表"""
    __tablename__ = "trial_history"
    
    id = Column(Integer, primary_key=True, index=True)
    calculation_type = Column(String, index=True)  # 计算类型
    target_value = Column(Float)  # 目标值
    parameters = Column(JSON)  # 参数
    result = Column(JSON)  # 计算结果
    created_at = Column(DateTime, default=datetime.now)
    created_by = Column(String, nullable=True)  # 创建人
    notes = Column(Text, nullable=True)  # 备注


class TrialHistoryManager:
    """试算历史记录管理器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save_trial(
        self,
        calculation_type: str,
        target_value: float,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        created_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存试算记录
        
        Args:
            calculation_type: 计算类型
            target_value: 目标值
            parameters: 参数
            result: 计算结果
            created_by: 创建人
            notes: 备注
            
        Returns:
            保存结果
        """
        try:
            trial = TrialHistory(
                calculation_type=calculation_type,
                target_value=target_value,
                parameters=parameters,
                result=result,
                created_by=created_by,
                notes=notes
            )
            self.db.add(trial)
            self.db.commit()
            self.db.refresh(trial)
            
            return {
                "success": True,
                "trial_id": trial.id,
                "message": "试算记录已保存"
            }
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_trial_history(
        self,
        calculation_type: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取试算历史记录
        
        Args:
            calculation_type: 计算类型（可选）
            limit: 返回数量限制
            
        Returns:
            历史记录列表
        """
        query = self.db.query(TrialHistory)
        
        if calculation_type:
            query = query.filter(TrialHistory.calculation_type == calculation_type)
        
        trials = query.order_by(TrialHistory.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": trial.id,
                "calculation_type": trial.calculation_type,
                "target_value": trial.target_value,
                "parameters": trial.parameters,
                "result": trial.result,
                "created_at": trial.created_at.isoformat() if trial.created_at else None,
                "created_by": trial.created_by,
                "notes": trial.notes
            }
            for trial in trials
        ]
    
    async def compare_trials(
        self,
        trial_ids: List[int]
    ) -> Dict[str, Any]:
        """
        对比多个试算结果
        
        Args:
            trial_ids: 试算记录ID列表
            
        Returns:
            对比结果
        """
        trials = self.db.query(TrialHistory).filter(
            TrialHistory.id.in_(trial_ids)
        ).all()
        
        if len(trials) < 2:
            return {
                "success": False,
                "error": "至少需要2条记录才能对比"
            }
        
        comparison = {
            "success": True,
            "trials": [
                {
                    "id": trial.id,
                    "calculation_type": trial.calculation_type,
                    "target_value": trial.target_value,
                    "result": trial.result,
                    "created_at": trial.created_at.isoformat() if trial.created_at else None
                }
                for trial in trials
            ],
            "differences": self._calculate_differences(trials)
        }
        
        return comparison
    
    def _calculate_differences(
        self,
        trials: List[TrialHistory]
    ) -> List[Dict[str, Any]]:
        """计算差异"""
        differences = []
        
        if len(trials) >= 2:
            trial1 = trials[0]
            trial2 = trials[1]
            
            result1 = trial1.result or {}
            result2 = trial2.result or {}
            
            # 对比关键指标
            if "total_cost" in result1 and "total_cost" in result2:
                diff = result2["total_cost"] - result1["total_cost"]
                differences.append({
                    "metric": "总成本",
                    "value1": result1["total_cost"],
                    "value2": result2["total_cost"],
                    "difference": diff,
                    "percentage": (diff / result1["total_cost"] * 100) if result1["total_cost"] > 0 else 0
                })
            
            if "total_days" in result1 and "total_days" in result2:
                diff = result2["total_days"] - result1["total_days"]
                differences.append({
                    "metric": "总天数",
                    "value1": result1["total_days"],
                    "value2": result2["total_days"],
                    "difference": diff,
                    "percentage": (diff / result1["total_days"] * 100) if result1["total_days"] > 0 else 0
                })
        
        return differences

