#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP专家系统桥接模块
复用《🚀 Super Agent Main Interface》中的企业级专家实现，确保独立ERP工程可直接引用。
"""

from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SUPER_AGENT_ROOT = WORKSPACE_ROOT / "🚀 Super Agent Main Interface"

if SUPER_AGENT_ROOT.exists():
    sys.path.insert(0, str(SUPER_AGENT_ROOT))

from core.experts.erp_experts import (  # type: ignore
    ERPDimension,
    ERPAnalysis,
    QualityExpert,
    QualityImprovementExpert,
    CostExpert,
    CostOptimizationExpert,
    DeliveryExpert,
    DeliveryResilienceExpert,
    SafetyExpert,
    SafetyComplianceExpert,
    ProfitExpert,
    ProfitGrowthExpert,
    EfficiencyExpert,
    EfficiencyAutomationExpert,
    ManagementExpert,
    ERPProcessExpert,
    TechnologyExpert,
    TechnologyInnovationExpert,
    get_erp_experts,
)

__all__ = [
    "ERPDimension",
    "ERPAnalysis",
    "QualityExpert",
    "QualityImprovementExpert",
    "CostExpert",
    "CostOptimizationExpert",
    "DeliveryExpert",
    "DeliveryResilienceExpert",
    "SafetyExpert",
    "SafetyComplianceExpert",
    "ProfitExpert",
    "ProfitGrowthExpert",
    "EfficiencyExpert",
    "EfficiencyAutomationExpert",
    "ManagementExpert",
    "ERPProcessExpert",
    "TechnologyExpert",
    "TechnologyInnovationExpert",
    "get_erp_experts",
]

