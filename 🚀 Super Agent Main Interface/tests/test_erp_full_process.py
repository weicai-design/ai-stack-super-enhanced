#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP 11环节全流程实现测试（T012-T022）

覆盖内容：
- 蓝图能力数量符合目标
- 11环节矩阵及虚拟环节（售后/财务）
- 八维度分析（整体 + 单环节）
- 数据源覆盖（订单/采购/库存/生产）
- 流程拓扑结构可用
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, Any, List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.erp_process_service import ERPProcessService, DIMENSIONS  # noqa: E402


class DummyDataSource:
    """提供可控的ERP数据源，用于验证数据融合能力"""

    def get_orders(self, status: str | None = None) -> List[Dict[str, Any]]:
        return [
            {
                "order_id": "SO-DS-1",
                "customer": "测试客户",
                "industry": "半导体",
                "quantity": 120,
                "unit_price": 15000,
                "status": "executing",
                "promise_date": "2025-12-30",
                "priority": "high",
            }
        ]

    def get_procurement_alerts(self) -> List[Dict[str, Any]]:
        return [
            {
                "po_id": "PO-DS-1",
                "supplier": "测试供应商",
                "material_code": "MAT-DS-1",
                "material_name": "测试物料",
                "amount": 100000,
                "status": "confirmed",
                "eta": "2025-11-20",
            }
        ]

    def get_inventory_status(self) -> List[Dict[str, Any]]:
        return [
            {
                "material_code": "MAT-DS-1",
                "material_name": "测试物料",
                "on_hand": 500,
                "reserved": 200,
                "safety_stock": 150,
                "reorder_point": 220,
            }
        ]

    def get_production_jobs(self, order_id: str | None = None) -> List[Dict[str, Any]]:
        return [
            {
                "job_id": "MO-DS-1",
                "order_id": "SO-DS-1",
                "line": "L-DS",
                "quantity": 500,
                "completed": 120,
                "plan_start": "2025-11-01",
                "plan_end": "2025-11-15",
                "status": "executing",
            }
        ]

    def get_cash_flow_summary(self) -> Dict[str, Any]:
        return {"total_collections": 500000, "total_payments": 120000, "balance": 380000}


def test_stage_blueprint_capability_targets():
    service = ERPProcessService()
    blueprint = service.get_stage_blueprint("order_management")
    assert blueprint is not None, "应返回订单管理蓝图"
    data = blueprint["blueprint"]
    assert data["capability_count"] >= data["capability_target"], "能力数量应达到目标"
    assert len(data["capabilities"]) == data["capability_count"]
    assert data["name"] == "订单管理"


def test_stage_matrix_contains_virtual_rows():
    service = ERPProcessService()
    matrix = service.get_stage_matrix()
    stage_ids = {row["stage_id"] for row in matrix["matrix"]}
    assert "after_sales" in stage_ids, "矩阵中应包含售后环节"
    assert "finance_settlement" in stage_ids, "矩阵中应包含财务结算环节"
    assert matrix["dimension_analysis"]["scope"] == "overall"


def test_dimension_analysis_scope():
    service = ERPProcessService()
    overall = service.get_dimension_analysis()
    assert overall["scope"] == "overall"
    assert len(overall["dimensions"]) == len(DIMENSIONS)

    stage_result = service.get_dimension_analysis("order_management")
    assert stage_result["scope"] == "order_management"
    assert stage_result["success"] is True


def test_datasource_override_injects_records():
    service = ERPProcessService(stage_manager=None, data_source=DummyDataSource())
    orders_view = service.get_orders_view()
    assert any(order["order_id"] == "SO-DS-1" for order in orders_view["orders"])

    inventory_view = service.get_inventory_view()
    assert inventory_view["inventory"][0]["material_id"] == "MAT-DS-1"

    production_view = service.get_production_view()
    assert production_view["jobs"][0]["job_id"] == "MO-DS-1"


def test_flow_map_structure():
    service = ERPProcessService()
    flow_map = service.get_flow_map()
    assert flow_map["success"] is True
    nodes = flow_map["nodes"]
    edges = flow_map["edges"]
    assert len(nodes) >= len(service.stage_state) + 2  # 包含售后+财务
    assert len(edges) == len(nodes) - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


