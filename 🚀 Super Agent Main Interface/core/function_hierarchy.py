#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FOUR_LEVEL_FUNCTIONS

用于 P2-001：在三级模块基础上补充第四级“能力单元”描述。
"""

from __future__ import annotations

FOUR_LEVEL_FUNCTIONS = {
    "rag": {
        "preprocess": {
            "ingest_status": [
                {"id": "rag_ingest_queue", "name": "文档排队监控", "owner": "RAG Bot", "result": "入库 SLA < 3min"},
                {"id": "rag_cache_refresh", "name": "向量缓存刷新", "owner": "Vector Service", "result": "冷热分层"},
            ],
            "clean_quality": [
                {"id": "rag_clean_rules", "name": "规则清洗", "owner": "Data Steward", "result": "脱敏+去噪"},
            ],
        },
        "knowledge": {
            "kg_connections": [
                {"id": "rag_kg_entities", "name": "实体抽取", "owner": "LLM Worker", "result": "实体图谱"},
                {"id": "rag_relevancy_feedback", "name": "相关性反馈", "owner": "Analyst", "result": "调权"},
            ],
        },
    },
    "content": {
        "analytics": {
            "content_analytics": [
                {"id": "post_effect_tracker", "name": "发布效果追踪", "owner": "Content Ops", "result": "多平台数据"},
                {"id": "optimization_loop", "name": "优化建议生成", "owner": "Content AI", "result": "A/B 指南"},
            ]
        }
    },
    "trend": {
        "analysis": {
            "trend_insights": [
                {"id": "insight_generation", "name": "洞察生成链路", "owner": "Trend Engine", "result": "行业/区域/政策解读"},
            ]
        },
        "forecast": {
            "trend_forecast": [
                {"id": "rag_output_link", "name": "RAG 回写联动", "owner": "Trend RAG", "result": "文档+KG"},
            ]
        },
    },
    "operations": {
        "strategy": {
            "strategy_links": [
                {"id": "budget_erp_flow", "name": "预算-ERP 审批同步", "owner": "Finance Ops", "result": "跨系统自动审批"},
                {"id": "cost_capacity_watch", "name": "成本-产能联动", "owner": "Supply Chain", "result": "动态排产"},
            ]
        }
    },
    "coding": {
        "optimization": {
            "coding_optimization": [
                {"id": "closed_loop_tasks", "name": "闭环任务回放", "owner": "Coding Agent", "result": "执行轨迹"},
            ]
        }
    },
    "erp": {
        "stages": {
            "erp_11_stages": [
                {"id": "stage_instance_management", "name": "环节实例管理", "owner": "ERP Manager", "result": "实例创建/更新/完成"},
                {"id": "stage_kpi_calculation", "name": "环节KPI计算", "owner": "ERP Calculator", "result": "KPI得分与分解"},
            ],
            "erp_stage_detail": [
                {"id": "stage_metrics_tracking", "name": "环节指标追踪", "owner": "ERP Monitor", "result": "实时指标更新"},
            ],
        },
        "inventory": {
            "inventory_trial": [
                {"id": "inventory_abc_analysis", "name": "ABC分类分析", "owner": "Inventory Analyst", "result": "ABC分类结果"},
                {"id": "inventory_optimization", "name": "库存优化试算", "owner": "Inventory Optimizer", "result": "优化建议"},
            ],
            "inventory_status": [
                {"id": "inventory_query", "name": "库存查询", "owner": "Inventory Service", "result": "实时库存数据"},
                {"id": "inventory_reservation", "name": "库存预留", "owner": "Inventory Service", "result": "预留记录"},
            ],
        },
        "trial": {
            "erp_trial_calc": [
                {"id": "revenue_trial", "name": "目标营收试算", "owner": "Finance Expert", "result": "营收预测"},
                {"id": "production_trial", "name": "产量试算", "owner": "Production Expert", "result": "产量预测"},
            ],
        },
    },
    "expert": {
        "routing": {
            "expert_routing": [
                {"id": "intelligent_routing", "name": "智能路由", "owner": "Expert Router", "result": "专家选择"},
                {"id": "capability_mapping", "name": "能力映射", "owner": "Expert Router", "result": "能力匹配"},
            ],
        },
        "collaboration": {
            "expert_collaboration": [
                {"id": "multi_expert_session", "name": "多专家会话", "owner": "Collaboration Hub", "result": "协同会话"},
                {"id": "contribution_tracking", "name": "贡献追踪", "owner": "Collaboration Hub", "result": "贡献记录"},
            ],
        },
        "dashboard": {
            "expert_board": [
                {"id": "expert_performance", "name": "专家表现", "owner": "Expert Monitor", "result": "表现指标"},
                {"id": "collaboration_stats", "name": "协同统计", "owner": "Collaboration Monitor", "result": "统计报告"},
            ],
            "expert_metrics": [
                {"id": "collaboration_index", "name": "协作指数", "owner": "Metrics Calculator", "result": "指数得分"},
                {"id": "response_speed", "name": "响应速度", "owner": "Metrics Calculator", "result": "速度指标"},
            ],
        },
    },
}

__all__ = ["FOUR_LEVEL_FUNCTIONS"]


