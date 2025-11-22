"""学习管理器"""
import logging
from typing import Dict, List
from collections import defaultdict
from .models import LearningRecord, UserPreference, Optimization

logger = logging.getLogger(__name__)

class LearningManager:
    def __init__(self):
        self.records: Dict[str, List[LearningRecord]] = defaultdict(list)
        self.preferences: Dict[str, UserPreference] = {}
        self.optimizations: Dict[str, List[Optimization]] = defaultdict(list)
        logger.info("✅ 学习管理器已初始化")
    
    def record_learning(self, tenant_id: str, record: LearningRecord) -> LearningRecord:
        record.tenant_id = tenant_id
        self.records[tenant_id].append(record)
        return record
    
    def update_preference(self, tenant_id: str, user_id: str, pref: UserPreference) -> UserPreference:
        key = f"{tenant_id}_{user_id}"
        pref.tenant_id = tenant_id
        pref.user_id = user_id
        self.preferences[key] = pref
        return pref
    
    def suggest_optimization(self, tenant_id: str, opt: Optimization) -> Optimization:
        opt.tenant_id = tenant_id
        self.optimizations[tenant_id].append(opt)
        return opt

learning_manager = LearningManager()


































