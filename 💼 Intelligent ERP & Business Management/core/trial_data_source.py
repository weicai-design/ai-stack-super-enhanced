"""
试算模块专用的数据访问层

从 demo_factory.db 中拉取订单、交付和库存数据，为试算计算提供真实业务参数。
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class DemoFactoryTrialDataSource:
    """基于 demo_factory.db 的轻量级ERP数据源"""

    def __init__(self, db_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parents[2]
        default_db = base_dir / "data" / "demo_factory.db"
        self.db_path = os.environ.get("FACTORY_DB_PATH", db_path or str(default_db))
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"未找到 demo_factory.db，请先运行 scripts/setup_demo_factory_db.py，当前路径: {self.db_path}"
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    async def get_product_data(
        self,
        *,
        order_id: Optional[str] = None,
        product_code: Optional[str] = None,
        legacy_identifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取订单/产品的核心信息"""
        return await asyncio.to_thread(
            self._get_product_data_sync,
            order_id,
            product_code,
            legacy_identifier,
        )

    def _get_product_data_sync(
        self,
        order_id: Optional[str],
        product_code: Optional[str],
        legacy_identifier: Optional[str],
    ) -> Dict[str, Any]:
        with self._connect() as conn:
            resolved_order_id = self._resolve_order_id(
                conn, order_id=order_id, product_code=product_code, legacy_identifier=legacy_identifier
            )

            if resolved_order_id:
                row = conn.execute(
                    """
                    SELECT order_id, customer, product_code, product_name, quantity,
                           unit_price, priority, status, requested_date, promise_date, created_at
                    FROM orders
                    WHERE order_id = ?
                    """,
                    (resolved_order_id,),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT order_id, customer, product_code, product_name, quantity,
                           unit_price, priority, status, requested_date, promise_date, created_at
                    FROM orders
                    ORDER BY priority ASC, created_at DESC
                    LIMIT 1
                    """
                ).fetchone()

            if not row:
                return {}

            product = dict(row)
            product["available_days"] = self._calculate_available_days(product)
            product["order_window_days"] = self._calculate_order_window(product)
            product["resolved_order_id"] = product["order_id"]

            return product

    async def get_historical_delivery_data(
        self,
        *,
        order_id: Optional[str] = None,
        product_code: Optional[str] = None,
        legacy_identifier: Optional[str] = None,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """获取指定订单的历史交付记录"""
        return await asyncio.to_thread(
            self._get_historical_delivery_data_sync,
            order_id,
            product_code,
            legacy_identifier,
            days,
        )

    def _get_historical_delivery_data_sync(
        self,
        order_id: Optional[str],
        product_code: Optional[str],
        legacy_identifier: Optional[str],
        days: int,
    ) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            resolved_order_id = self._resolve_order_id(
                conn, order_id=order_id, product_code=product_code, legacy_identifier=legacy_identifier
            )

            if not resolved_order_id:
                return []

            since = datetime.now() - timedelta(days=days)
            rows = conn.execute(
                """
                SELECT date(COALESCE(delivered_at, departed_at)) AS day,
                       SUM(quantity) AS qty
                FROM shipments
                WHERE order_id = ?
                  AND COALESCE(delivered_at, departed_at) >= ?
                GROUP BY date(COALESCE(delivered_at, departed_at))
                ORDER BY day ASC
                """,
                (resolved_order_id, since),
            ).fetchall()

            if rows:
                return [
                    {
                        "date": row["day"],
                        "quantity": row["qty"] or 0,
                    }
                    for row in rows
                    if row["day"]
                ]

            # 若没有交付记录，依据订单数量构造一个简化的参考序列
            order_row = conn.execute(
                "SELECT quantity FROM orders WHERE order_id = ?",
                (resolved_order_id,),
            ).fetchone()

            if not order_row:
                return []

            total_quantity = order_row["quantity"]
            reference_days = min(5, max(1, days))
            per_day = total_quantity / reference_days
            today = datetime.now().date()

            return [
                {
                    "date": (today - timedelta(days=reference_days - idx)).isoformat(),
                    "quantity": round(per_day * (0.9 + idx * 0.02), 2),
                }
                for idx in range(reference_days)
            ]

    def _resolve_order_id(
        self,
        conn: sqlite3.Connection,
        *,
        order_id: Optional[str],
        product_code: Optional[str],
        legacy_identifier: Optional[str],
    ) -> Optional[str]:
        if order_id:
            return order_id

        if product_code:
            row = conn.execute(
                """
                SELECT order_id
                FROM orders
                WHERE product_code = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (product_code,),
            ).fetchone()
            if row:
                return row["order_id"]

        if legacy_identifier:
            row = conn.execute(
                """
                SELECT order_id
                FROM orders
                WHERE order_id = :identifier OR product_code = :identifier
                ORDER BY created_at DESC
                LIMIT 1
                """,
                {"identifier": legacy_identifier},
            ).fetchone()
            if row:
                return row["order_id"]

        return None

    def _calculate_available_days(self, product: Dict[str, Any]) -> Optional[int]:
        promise_date = product.get("promise_date")
        if not promise_date:
            return None

        try:
            promise = datetime.fromisoformat(str(promise_date)).date()
        except ValueError:
            return None

        today = datetime.now().date()
        delta = (promise - today).days
        return max(delta, 1) if delta > 0 else 1

    def _calculate_order_window(self, product: Dict[str, Any]) -> Optional[int]:
        requested = product.get("requested_date")
        promise = product.get("promise_date")
        if not requested or not promise:
            return None

        try:
            start = datetime.fromisoformat(str(requested)).date()
            end = datetime.fromisoformat(str(promise)).date()
        except ValueError:
            return None

        return max((end - start).days, 1)














