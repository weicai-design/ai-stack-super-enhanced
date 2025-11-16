#!/usr/bin/env python3
"""
初始化演示工厂数据库

该脚本会创建一个覆盖制造型企业订单→生产→采购→库存→交付→回款的示例数据集，
用于ERP/运营/财务模块的端到端联调与演示。
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Iterable, Sequence

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "demo_factory.db"


def execute_batch(cursor: sqlite3.Cursor, sql: str, rows: Iterable[Sequence]):
    if not rows:
        return
    cursor.executemany(sql, rows)


def init_schema(conn: sqlite3.Connection):
    conn.execute("PRAGMA foreign_keys = ON;")
    tables = [
        "orders",
        "projects",
        "production_jobs",
        "procurements",
        "inventory",
        "quality_events",
        "shipments",
        "cash_flows",
    ]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table};")

    conn.executescript(
        """
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            product_code TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            priority INTEGER NOT NULL DEFAULT 2,
            status TEXT NOT NULL,
            requested_date DATE NOT NULL,
            promise_date DATE NOT NULL,
            created_at DATETIME NOT NULL,
            notes TEXT
        );

        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            stage TEXT NOT NULL,
            progress REAL NOT NULL DEFAULT 0,
            owner TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            next_milestone DATE,
            updated_at DATETIME NOT NULL
        );

        CREATE TABLE production_jobs (
            job_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            workstation TEXT NOT NULL,
            plan_start DATETIME NOT NULL,
            plan_end DATETIME NOT NULL,
            actual_start DATETIME,
            actual_end DATETIME,
            status TEXT NOT NULL,
            yield_rate REAL,
            bottleneck_flag INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE procurements (
            procurement_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            supplier TEXT NOT NULL,
            material_code TEXT NOT NULL,
            material_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            eta DATE NOT NULL,
            status TEXT NOT NULL,
            last_checked DATETIME NOT NULL
        );

        CREATE TABLE inventory (
            material_code TEXT PRIMARY KEY,
            material_name TEXT NOT NULL,
            safety_stock INTEGER NOT NULL,
            on_hand INTEGER NOT NULL,
            reserved INTEGER NOT NULL,
            uom TEXT NOT NULL,
            updated_at DATETIME NOT NULL
        );

        CREATE TABLE quality_events (
            event_id TEXT PRIMARY KEY,
            job_id TEXT NOT NULL REFERENCES production_jobs(job_id),
            defect_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            description TEXT,
            detected_at DATETIME NOT NULL,
            corrected_at DATETIME,
            status TEXT NOT NULL
        );

        CREATE TABLE shipments (
            shipment_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            quantity INTEGER NOT NULL,
            carrier TEXT NOT NULL,
            tracking_no TEXT,
            status TEXT NOT NULL,
            departed_at DATETIME,
            delivered_at DATETIME
        );

        CREATE TABLE cash_flows (
            cash_flow_id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL REFERENCES orders(order_id),
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'CNY',
            occurred_at DATETIME NOT NULL,
            status TEXT NOT NULL,
            remarks TEXT
        );
        """
    )

    conn.executescript(
        """
        CREATE VIEW v_order_health AS
        SELECT
            o.order_id,
            o.customer,
            o.product_name,
            o.quantity,
            o.status,
            o.promise_date,
            MAX(p.progress) AS project_progress,
            MAX(j.status) AS latest_job_status,
            MIN(j.plan_end) AS next_station_finish,
            SUM(cf.amount) FILTER (WHERE cf.type='collection') AS collected,
            SUM(cf.amount) FILTER (WHERE cf.type='payment') AS paid
        FROM orders o
        LEFT JOIN projects p ON o.order_id = p.order_id
        LEFT JOIN production_jobs j ON o.order_id = j.order_id
        LEFT JOIN cash_flows cf ON o.order_id = cf.order_id
        GROUP BY o.order_id;
        """
    )


def seed_data(conn: sqlite3.Connection):
    now = datetime.now()
    orders = [
        (
            "ORD-2025-001",
            "星河半导体",
            "CHIP-PWR-12",
            "功率芯片模组",
            1200,
            1280.0,
            1,
            "production",
            (now + timedelta(days=7)).date(),
            (now + timedelta(days=14)).date(),
            now - timedelta(days=5),
            "含紧急交付条款",
        ),
        (
            "ORD-2025-002",
            "天行汽车",
            "BAT-A1-MOD",
            "电池管理子系统",
            600,
            2380.0,
            2,
            "planning",
            (now + timedelta(days=10)).date(),
            (now + timedelta(days=20)).date(),
            now - timedelta(days=2),
            None,
        ),
        (
            "ORD-2025-003",
            "蓝湾能源",
            "INV-48K",
            "工业逆变器",
            80,
            12500.0,
            1,
            "delivery",
            (now - timedelta(days=2)).date(),
            (now - timedelta(days=1)).date(),
            now - timedelta(days=15),
            "等待客户验收报告",
        ),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO orders (
            order_id, customer, product_code, product_name, quantity,
            unit_price, priority, status, requested_date, promise_date,
            created_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        orders,
    )

    projects = [
        ("PRJ-001", "ORD-2025-001", "生产准备", 0.6, "王研", "medium", (now + timedelta(days=3)).date(), now),
        ("PRJ-002", "ORD-2025-001", "质量验证", 0.2, "陆洁", "high", (now + timedelta(days=5)).date(), now),
        ("PRJ-003", "ORD-2025-002", "物料齐套", 0.35, "陈诚", "low", (now + timedelta(days=6)).date(), now),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO projects (
            project_id, order_id, stage, progress, owner,
            risk_level, next_milestone, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        projects,
    )

    production_jobs = [
        (
            "JOB-001",
            "ORD-2025-001",
            "SMT-Line-01",
            now - timedelta(days=1),
            now + timedelta(days=1),
            now - timedelta(days=1, hours=3),
            None,
            "running",
            0.985,
            1,
        ),
        (
            "JOB-002",
            "ORD-2025-001",
            "Assembly-02",
            now + timedelta(days=2),
            now + timedelta(days=4),
            None,
            None,
            "planned",
            None,
            0,
        ),
        (
            "JOB-003",
            "ORD-2025-002",
            "SMT-Line-02",
            now + timedelta(days=1),
            now + timedelta(days=3),
            None,
            None,
            "planned",
            None,
            0,
        ),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO production_jobs (
            job_id, order_id, workstation, plan_start, plan_end,
            actual_start, actual_end, status, yield_rate, bottleneck_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        production_jobs,
    )

    procurements = [
        (
            "PO-001",
            "ORD-2025-001",
            "凌云电子",
            "MCU-XR32",
            "控制MCU",
            1500,
            38.5,
            (now + timedelta(days=2)).date(),
            "in_transit",
            now,
        ),
        (
            "PO-002",
            "ORD-2025-002",
            "华光材料",
            "AL-HEATSINK",
            "散热模组",
            800,
            82.3,
            (now + timedelta(days=5)).date(),
            "confirmed",
            now,
        ),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO procurements (
            procurement_id, order_id, supplier, material_code, material_name,
            quantity, unit_cost, eta, status, last_checked
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        procurements,
    )

    inventory = [
        ("MCU-XR32", "控制MCU", 800, 620, 150, "pcs", now),
        ("AL-HEATSINK", "散热模组", 400, 420, 200, "pcs", now),
        ("BAT-CELL-A1", "电芯-A1", 3000, 2400, 1500, "pcs", now),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO inventory (
            material_code, material_name, safety_stock, on_hand,
            reserved, uom, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        inventory,
    )

    quality_events = [
        (
            "QE-001",
            "JOB-001",
            "焊点虚焊",
            "medium",
            "AOI检测到批次偏差",
            now - timedelta(hours=6),
            None,
            "investigating",
        ),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO quality_events (
            event_id, job_id, defect_type, severity, description,
            detected_at, corrected_at, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        quality_events,
    )

    shipments = [
        (
            "SHP-001",
            "ORD-2025-003",
            60,
            "顺丰冷链",
            "SF123456789",
            "delivered",
            now - timedelta(days=3),
            now - timedelta(days=1),
        )
    ]

    execute_batch(
        conn,
        """
        INSERT INTO shipments (
            shipment_id, order_id, quantity, carrier, tracking_no,
            status, departed_at, delivered_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        shipments,
    )

    cash_flows = [
        ("CF-001", "ORD-2025-001", "collection", 300000.0, "CNY", now - timedelta(days=1), "received", "首付款"),
        ("CF-002", "ORD-2025-001", "payment", 48000.0, "CNY", now - timedelta(days=2), "paid", "物料采购"),
        ("CF-003", "ORD-2025-003", "collection", 850000.0, "CNY", now - timedelta(days=5), "received", "验收尾款"),
    ]

    execute_batch(
        conn,
        """
        INSERT INTO cash_flows (
            cash_flow_id, order_id, type, amount, currency,
            occurred_at, status, remarks
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        cash_flows,
    )


def main():
    with sqlite3.connect(DB_PATH) as conn:
        init_schema(conn)
        seed_data(conn)
        conn.commit()

    print(f"[setup_demo_factory_db] 已在 {DB_PATH} 生成示例数据库")


if __name__ == "__main__":
    main()




