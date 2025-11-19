#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专家体系标准化
功能：能力地图、路由策略、验收矩阵、模拟演练
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExpertLevel(Enum):
    """专家级别"""
    L1 = "L1"  # 初级
    L2 = "L2"  # 中级
    L3 = "L3"  # 高级
    L4 = "L4"  # 专家级


class CapabilityStatus(Enum):
    """能力状态"""
    READY = "ready"  # 就绪
    BETA = "beta"  # 测试中
    PILOT = "pilot"  # 试点
    PLANNED = "planned"  # 计划中


class TestStatus(Enum):
    """测试状态"""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    RUNNING = "running"


class ExpertStandardization:
    """
    专家体系标准化管理器
    管理能力地图、路由策略、验收矩阵、模拟演练
    """
    
    def __init__(self):
        """初始化标准化管理器"""
        self.ability_map: List[Dict[str, Any]] = []
        self.routing_strategy: Dict[str, Any] = {}
        self.acceptance_matrix: List[Dict[str, Any]] = []
        self.simulation_history: List[Dict[str, Any]] = []
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """初始化默认数据"""
        # 能力地图将在API中从EXPERT_ABILITY_MAP加载
        # 路由策略将在API中从EXPERT_ROUTING_STRATEGY加载
        # 验收矩阵将在API中从EXPERT_ACCEPTANCE_MATRIX加载
        pass
    
    def update_ability_map(self, abilities: List[Dict[str, Any]]):
        """更新能力地图"""
        self.ability_map = abilities
    
    def update_routing_strategy(self, strategy: Dict[str, Any]):
        """更新路由策略"""
        self.routing_strategy = strategy
    
    def update_acceptance_matrix(self, matrix: List[Dict[str, Any]]):
        """更新验收矩阵"""
        self.acceptance_matrix = matrix
    
    def get_ability_summary(self) -> Dict[str, Any]:
        """获取能力地图摘要"""
        if not self.ability_map:
            return {
                "total_experts": 0,
                "avg_confidence": 0.0,
                "modules": [],
                "ready_capabilities": 0
            }
        
        total = len(self.ability_map)
        avg_confidence = sum(item.get("confidence", 0.0) for item in self.ability_map) / total if total else 0.0
        modules = sorted(set(
            m for item in self.ability_map 
            for m in item.get("modules", [])
        ))
        ready_capabilities = sum(
            1
            for item in self.ability_map
            for cap in item.get("capabilities", [])
            if cap.get("status") == CapabilityStatus.READY.value
        )
        
        return {
            "total_experts": total,
            "avg_confidence": round(avg_confidence, 2),
            "modules": modules,
            "ready_capabilities": ready_capabilities
        }
    
    def get_routing_summary(self) -> Dict[str, Any]:
        """获取路由策略摘要"""
        if not self.routing_strategy:
            return {
                "version": "unknown",
                "confidence_thresholds": {},
                "heuristics_count": 0,
                "fallback_chain_count": 0
            }
        
        return {
            "version": self.routing_strategy.get("version", "unknown"),
            "confidence_thresholds": self.routing_strategy.get("confidence_thresholds", {}),
            "heuristics_count": len(self.routing_strategy.get("heuristics", [])),
            "fallback_chain_count": len(self.routing_strategy.get("fallback_chain", [])),
            "module_load": self.routing_strategy.get("module_load", {})
        }
    
    def get_acceptance_summary(self) -> Dict[str, Any]:
        """获取验收矩阵摘要"""
        if not self.acceptance_matrix:
            return {
                "total_capabilities": 0,
                "total_tests": 0,
                "pass_rate": 0.0,
                "last_run": None
            }
        
        total_capabilities = len(self.acceptance_matrix)
        total_tests = sum(
            len(item.get("tests", []))
            for item in self.acceptance_matrix
        )
        pass_count = sum(
            sum(1 for test in item.get("tests", []) if test.get("status") == TestStatus.PASS.value)
            for item in self.acceptance_matrix
        )
        pass_rate = (pass_count / total_tests * 100) if total_tests > 0 else 0.0
        
        # 获取最近的运行时间
        last_runs = [
            item.get("last_run")
            for item in self.acceptance_matrix
            if item.get("last_run")
        ]
        last_run = max(last_runs) if last_runs else None
        
        return {
            "total_capabilities": total_capabilities,
            "total_tests": total_tests,
            "pass_count": pass_count,
            "pass_rate": round(pass_rate, 2),
            "last_run": last_run
        }
    
    def simulate_routing(
        self,
        query: str,
        knowledge_hints: Optional[List[str]] = None,
        expected_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        模拟路由
        
        Args:
            query: 用户查询
            knowledge_hints: 知识提示
            expected_domain: 期望领域
            
        Returns:
            路由结果
        """
        # 分析查询
        domain_scores = {}
        for item in self.ability_map:
            expert_id = item.get("id", "")
            modules = item.get("modules", [])
            signals = item.get("signals", [])
            
            score = 0.0
            # 关键词匹配
            for signal in signals:
                if signal in query:
                    score += 0.3
            
            # 模块匹配
            if expected_domain and expected_domain in modules:
                score += 0.5
            
            # 知识提示匹配
            if knowledge_hints:
                for hint in knowledge_hints:
                    for signal in signals:
                        if signal in hint:
                            score += 0.2
            
            if score > 0:
                domain_scores[expert_id] = {
                    "expert": expert_id,
                    "name": item.get("name", ""),
                    "score": score,
                    "confidence": item.get("confidence", 0.0),
                    "modules": modules
                }
        
        # 选择最佳专家
        if domain_scores:
            best_expert = max(domain_scores.items(), key=lambda x: x[1]["score"])
            expert_info = best_expert[1]
            
            # 计算最终置信度
            final_confidence = min(1.0, expert_info["confidence"] * expert_info["score"])
            
            result = {
                "expert": expert_info["expert"],
                "name": expert_info["name"],
                "domain": expert_info["modules"][0] if expert_info["modules"] else "general",
                "confidence": round(final_confidence, 2),
                "score": round(expert_info["score"], 2),
                "alternatives": sorted(
                    [
                        {
                            "expert": info["expert"],
                            "name": info["name"],
                            "score": round(info["score"], 2)
                        }
                        for expert_id, info in domain_scores.items()
                        if expert_id != best_expert[0]
                    ],
                    key=lambda x: x["score"],
                    reverse=True
                )[:3],
                "simulated_at": datetime.now().isoformat()
            }
        else:
            # 默认路由到RAG专家
            result = {
                "expert": "rag_expert",
                "name": "知识架构专家",
                "domain": "rag",
                "confidence": 0.5,
                "score": 0.0,
                "alternatives": [],
                "simulated_at": datetime.now().isoformat()
            }
        
        # 记录模拟历史
        self.simulation_history.append({
            "query": query,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.simulation_history = self.simulation_history[-100:]  # 保留最近100条
        
        return result
    
    def get_simulation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取模拟历史"""
        return self.simulation_history[-limit:]
    
    def validate_acceptance(
        self,
        capability: str,
        test_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        验证验收标准
        
        Args:
            capability: 能力名称
            test_results: 测试结果
            
        Returns:
            验证结果
        """
        # 查找对应的验收矩阵项
        matrix_item = next(
            (item for item in self.acceptance_matrix if item.get("capability") == capability),
            None
        )
        
        if not matrix_item:
            return {
                "valid": False,
                "message": f"未找到能力 '{capability}' 的验收标准"
            }
        
        acceptance_criteria = matrix_item.get("acceptance", "")
        tests = matrix_item.get("tests", [])
        
        # 检查测试结果
        all_passed = all(
            test.get("status") == TestStatus.PASS.value
            for test in test_results
        )
        
        # 解析验收标准（简化实现）
        # 真实实现应该解析标准字符串并验证指标
        
        return {
            "valid": all_passed,
            "capability": capability,
            "acceptance_criteria": acceptance_criteria,
            "test_count": len(test_results),
            "passed_count": sum(1 for t in test_results if t.get("status") == TestStatus.PASS.value),
            "validated_at": datetime.now().isoformat()
        }


# 全局实例
expert_standardization = ExpertStandardization()

