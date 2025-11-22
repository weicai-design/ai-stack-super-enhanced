#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
租户配额管理器
P3-402: 实现租户配额管理
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class QuotaType(str, Enum):
    """配额类型"""
    STORAGE = "storage"  # 存储配额（字节）
    FILE_COUNT = "file_count"  # 文件数量配额
    USER_COUNT = "user_count"  # 用户数量配额
    API_CALLS = "api_calls"  # API调用配额（每日）
    AI_TOKENS = "ai_tokens"  # AI Token配额（每月）
    DATABASE_SIZE = "database_size"  # 数据库大小配额（字节）


@dataclass
class TenantQuota:
    """租户配额"""
    tenant_id: str
    quota_type: QuotaType
    limit: int  # 配额限制
    used: int = 0  # 已使用量
    reset_period: str = "monthly"  # 重置周期 (daily/weekly/monthly/yearly)
    last_reset: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["quota_type"] = self.quota_type.value
        data["usage_percent"] = (self.used / self.limit * 100) if self.limit > 0 else 0
        data["remaining"] = max(0, self.limit - self.used)
        return data


class TenantQuotaManager:
    """
    租户配额管理器
    
    功能：
    1. 配额设置和管理
    2. 使用量统计
    3. 配额检查
    4. 配额告警
    5. 自动重置
    """
    
    def __init__(self):
        self.quotas: Dict[str, Dict[str, TenantQuota]] = {}  # {tenant_id: {quota_type: quota}}
        self.usage_history: Dict[str, List[Dict[str, Any]]] = {}  # 使用历史
        
        logger.info("租户配额管理器初始化完成")
    
    def set_quota(
        self,
        tenant_id: str,
        quota_type: QuotaType,
        limit: int,
        reset_period: str = "monthly",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TenantQuota:
        """
        设置租户配额
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型
            limit: 配额限制
            reset_period: 重置周期
            metadata: 元数据
            
        Returns:
            配额对象
        """
        if tenant_id not in self.quotas:
            self.quotas[tenant_id] = {}
        
        quota = TenantQuota(
            tenant_id=tenant_id,
            quota_type=quota_type,
            limit=limit,
            reset_period=reset_period,
            last_reset=datetime.utcnow().isoformat(),
            metadata=metadata or {},
        )
        
        self.quotas[tenant_id][quota_type.value] = quota
        
        logger.info(f"设置租户配额: {tenant_id} - {quota_type.value} = {limit}")
        
        return quota
    
    def get_quota(
        self,
        tenant_id: str,
        quota_type: str,
    ) -> Optional[int]:
        """
        获取租户配额限制
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型
            
        Returns:
            配额限制（如果不存在返回None）
        """
        if tenant_id not in self.quotas:
            return None
        
        quota = self.quotas[tenant_id].get(quota_type)
        if not quota:
            return None
        
        # 检查是否需要重置
        self._check_and_reset(quota)
        
        return quota.limit
    
    def get_quota_object(
        self,
        tenant_id: str,
        quota_type: str,
    ) -> Optional[TenantQuota]:
        """获取配额对象"""
        if tenant_id not in self.quotas:
            return None
        
        quota = self.quotas[tenant_id].get(quota_type)
        if quota:
            self._check_and_reset(quota)
        
        return quota
    
    def check_quota(
        self,
        tenant_id: str,
        quota_type: str,
        required: int,
    ) -> tuple[bool, Optional[str], Optional[TenantQuota]]:
        """
        检查配额是否足够
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型
            required: 所需数量
            
        Returns:
            (是否足够, 错误信息, 配额对象)
        """
        quota = self.get_quota_object(tenant_id, quota_type)
        
        if not quota:
            # 无配额限制
            return True, None, None
        
        if quota.used + required > quota.limit:
            return False, f"配额不足: 已使用{quota.used} + 需要{required} > 限制{quota.limit}", quota
        
        return True, None, quota
    
    def use_quota(
        self,
        tenant_id: str,
        quota_type: str,
        amount: int,
    ) -> tuple[bool, Optional[str]]:
        """
        使用配额
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型
            amount: 使用量
            
        Returns:
            (是否成功, 错误信息)
        """
        allowed, error, quota = self.check_quota(tenant_id, quota_type, amount)
        
        if not allowed:
            return False, error
        
        if quota:
            quota.used += amount
            
            # 记录使用历史
            self._record_usage(tenant_id, quota_type, amount)
        
        return True, None
    
    def release_quota(
        self,
        tenant_id: str,
        quota_type: str,
        amount: int,
    ) -> bool:
        """
        释放配额
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型
            amount: 释放量
            
        Returns:
            是否成功
        """
        quota = self.get_quota_object(tenant_id, quota_type)
        
        if quota:
            quota.used = max(0, quota.used - amount)
            return True
        
        return False
    
    def get_usage(
        self,
        tenant_id: str,
        quota_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取使用量
        
        Args:
            tenant_id: 租户ID
            quota_type: 配额类型（可选）
            
        Returns:
            使用量信息
        """
        if tenant_id not in self.quotas:
            return {}
        
        if quota_type:
            quota = self.get_quota_object(tenant_id, quota_type)
            if quota:
                return quota.to_dict()
            return {}
        
        # 返回所有配额的使用量
        usage = {}
        for qtype, quota in self.quotas[tenant_id].items():
            self._check_and_reset(quota)
            usage[qtype] = quota.to_dict()
        
        return usage
    
    def get_all_quotas(self, tenant_id: str) -> Dict[str, TenantQuota]:
        """获取租户所有配额"""
        if tenant_id not in self.quotas:
            return {}
        
        # 检查并重置所有配额
        for quota in self.quotas[tenant_id].values():
            self._check_and_reset(quota)
        
        return self.quotas[tenant_id].copy()
    
    def _check_and_reset(self, quota: TenantQuota):
        """检查并重置配额"""
        if not quota.last_reset:
            return
        
        last_reset = datetime.fromisoformat(quota.last_reset.replace("Z", "+00:00"))
        now = datetime.utcnow()
        
        should_reset = False
        
        if quota.reset_period == "daily":
            should_reset = (now - last_reset).days >= 1
        elif quota.reset_period == "weekly":
            should_reset = (now - last_reset).days >= 7
        elif quota.reset_period == "monthly":
            should_reset = (now - last_reset).days >= 30
        elif quota.reset_period == "yearly":
            should_reset = (now - last_reset).days >= 365
        
        if should_reset:
            quota.used = 0
            quota.last_reset = now.isoformat()
            logger.info(f"配额已重置: {quota.tenant_id} - {quota.quota_type.value}")
    
    def _record_usage(
        self,
        tenant_id: str,
        quota_type: str,
        amount: int,
    ):
        """记录使用历史"""
        if tenant_id not in self.usage_history:
            self.usage_history[tenant_id] = []
        
        self.usage_history[tenant_id].append({
            "quota_type": quota_type,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # 只保留最近1000条记录
        if len(self.usage_history[tenant_id]) > 1000:
            self.usage_history[tenant_id] = self.usage_history[tenant_id][-1000:]
    
    def get_usage_history(
        self,
        tenant_id: str,
        quota_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取使用历史"""
        if tenant_id not in self.usage_history:
            return []
        
        history = self.usage_history[tenant_id]
        
        if quota_type:
            history = [h for h in history if h["quota_type"] == quota_type]
        
        return history[-limit:]


_quota_manager: Optional[TenantQuotaManager] = None


def get_quota_manager() -> TenantQuotaManager:
    """获取配额管理器实例"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = TenantQuotaManager()
    return _quota_manager

