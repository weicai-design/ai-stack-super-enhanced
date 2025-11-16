"""
demo_factory 数据访问层
负责从 data/demo_factory.db 中拉取订单/生产/财务等信息
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class FactoryDataSource:
    """面向ERP/财务/运营模块的轻量级数据仓库"""

    def __init__(self, db_path: Optional[str] = None):
        default_path = (
            Path(__file__).resolve().parents[2] / "data" / "demo_factory.db"
        )
        self.db_path = db_path or os.environ.get("FACTORY_DB_PATH", str(default_path))
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"demo_factory.db 未找到，请先运行 scripts/setup_demo_factory_db.py，路径: {self.db_path}"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_order_health(self, limit: int = 20) -> List[Dict[str, Any]]:
        query = """
        SELECT * FROM v_order_health
        ORDER BY promise_date ASC
        LIMIT ?
        """
        with self._connect() as conn:
            rows = conn.execute(query, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_orders(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM orders"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY requested_date ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_production_jobs(self, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM production_jobs"
        params: List[Any] = []
        if order_id:
            query += " WHERE order_id = ?"
            params.append(order_id)
        query += " ORDER BY plan_start ASC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_procurement_alerts(self) -> List[Dict[str, Any]]:
        query = """
        SELECT *,
               CASE
                   WHEN status = 'in_transit' AND date(eta) < date('now','+1 day') THEN '风险：即将延迟'
                   WHEN status = 'confirmed' AND date(eta) < date('now','+3 day') THEN '关注：提前跟进供应商'
                   ELSE '正常'
               END AS alert
        FROM procurements
        ORDER BY eta ASC
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    def get_inventory_status(self) -> List[Dict[str, Any]]:
        query = """
        SELECT *,
               CASE
                   WHEN on_hand - reserved < safety_stock THEN '低于安全库存'
                   ELSE '正常'
               END AS status_flag
        FROM inventory
        ORDER BY updated_at DESC
        """
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            return [dict(row) for row in rows]

    def get_cash_flow_summary(self) -> Dict[str, Any]:
        query = """
        SELECT
            SUM(CASE WHEN type='collection' THEN amount ELSE 0 END) AS total_collections,
            SUM(CASE WHEN type='payment' THEN amount ELSE 0 END) AS total_payments,
            SUM(CASE WHEN type='collection' THEN amount ELSE 0 END) -
            SUM(CASE WHEN type='payment' THEN amount ELSE 0 END) AS balance
        FROM cash_flows
        """
        with self._connect() as conn:
            row = conn.execute(query).fetchone()
            return dict(row) if row else {}

    def get_dashboards(self) -> Dict[str, Any]:
        """统一返回看板数据"""
        return {
            "order_health": self.get_order_health(),
            "inventory": self.get_inventory_status(),
            "procurements": self.get_procurement_alerts(),
            "cash_flow": self.get_cash_flow_summary(),
        }





