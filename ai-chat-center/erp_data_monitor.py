"""
需求6: ERP数据单向监听和收集系统
无需ERP管理员授权，自动监听和收集数据
"""

import asyncio
import httpx
import json
from datetime import datetime
from typing import Dict, List, Any
import sqlite3
import os


class ERPDataMonitor:
    """ERP数据监听器"""
    
    def __init__(self, db_path: str = "erp_monitor.db"):
        self.db_path = db_path
        self.init_database()
        
        # ERP数据源配置
        self.data_sources = {
            "internal_erp": "http://localhost:8013",  # 内部ERP
            # 可以添加更多外部ERP数据源
        }
        
        self.monitoring = False
    
    def init_database(self):
        """初始化监听数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 财务数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                revenue REAL,
                expenses REAL,
                profit REAL,
                source TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 订单数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                order_id TEXT,
                customer TEXT,
                amount REAL,
                status TEXT,
                source TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 库存数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                product_id TEXT,
                product_name TEXT,
                quantity INTEGER,
                location TEXT,
                source TEXT,
                raw_data TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 监听日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitor_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT,
                source TEXT,
                data_count INTEGER,
                status TEXT,
                message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ ERP监听数据库初始化完成: {self.db_path}")
    
    async def collect_financial_data(self, source_name: str, api_url: str) -> Dict[str, Any]:
        """收集财务数据"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url}/api/finance/summary",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 保存到数据库
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO financial_data (timestamp, revenue, expenses, profit, source, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        datetime.now().isoformat(),
                        data.get('revenue'),
                        data.get('expenses'),
                        data.get('profit'),
                        source_name,
                        json.dumps(data)
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    return {"success": True, "data": data}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def collect_order_data(self, source_name: str, api_url: str) -> Dict[str, Any]:
        """收集订单数据"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url}/api/orders",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    orders = response.json()
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    for order in orders[:10]:  # 限制数量
                        cursor.execute("""
                            INSERT INTO order_data (timestamp, order_id, customer, amount, status, source, raw_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            datetime.now().isoformat(),
                            order.get('id'),
                            order.get('customer'),
                            order.get('amount'),
                            order.get('status'),
                            source_name,
                            json.dumps(order)
                        ))
                    
                    conn.commit()
                    conn.close()
                    
                    return {"success": True, "count": len(orders)}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def monitor_loop(self, interval: int = 300):
        """
        持续监听循环（每5分钟）
        """
        self.monitoring = True
        
        print(f"🔄 ERP数据监听已启动（间隔: {interval}秒）")
        
        while self.monitoring:
            try:
                # 收集所有数据源
                for source_name, api_url in self.data_sources.items():
                    print(f"📊 正在收集 {source_name} 数据...")
                    
                    # 收集财务数据
                    await self.collect_financial_data(source_name, api_url)
                    
                    # 收集订单数据
                    await self.collect_order_data(source_name, api_url)
                    
                    # 记录日志
                    self.log_monitoring_event(source_name, "data_collected", "success")
                
                print(f"✅ 数据收集完成，{interval}秒后下次收集")
                await asyncio.sleep(interval)
            
            except Exception as e:
                print(f"❌ 监听循环错误: {e}")
                await asyncio.sleep(60)
    
    def log_monitoring_event(self, source: str, event_type: str, status: str, message: str = ""):
        """记录监听日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO monitor_logs (timestamp, event_type, source, status, message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                event_type,
                source,
                status,
                message
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ 日志记录失败: {e}")
    
    def query_collected_data(self, data_type: str = "financial", limit: int = 10) -> List[Dict[str, Any]]:
        """查询收集的数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        
        try:
            if data_type == "financial":
                cursor.execute("""
                    SELECT timestamp, revenue, expenses, profit, source
                    FROM financial_data
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "timestamp": row[0],
                        "revenue": row[1],
                        "expenses": row[2],
                        "profit": row[3],
                        "source": row[4]
                    })
            
            elif data_type == "orders":
                cursor.execute("""
                    SELECT timestamp, order_id, customer, amount, status, source
                    FROM order_data
                    ORDER BY created_at DESC
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                for row in rows:
                    results.append({
                        "timestamp": row[0],
                        "order_id": row[1],
                        "customer": row[2],
                        "amount": row[3],
                        "status": row[4],
                        "source": row[5]
                    })
        
        finally:
            conn.close()
        
        return results
    
    def analyze_financial_trends(self) -> Dict[str, Any]:
        """分析财务趋势"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取最近10条财务数据
            cursor.execute("""
                SELECT revenue, expenses, profit, timestamp
                FROM financial_data
                ORDER BY created_at DESC
                LIMIT 10
            """)
            
            rows = cursor.fetchall()
            
            if not rows:
                return {"message": "暂无数据"}
            
            revenues = [r[0] for r in rows if r[0]]
            profits = [r[2] for r in rows if r[2]]
            
            analysis = {
                "total_records": len(rows),
                "avg_revenue": sum(revenues) / len(revenues) if revenues else 0,
                "avg_profit": sum(profits) / len(profits) if profits else 0,
                "trend": "上升" if len(profits) > 1 and profits[0] > profits[-1] else "下降",
                "latest_data": {
                    "revenue": rows[0][0],
                    "expenses": rows[0][1],
                    "profit": rows[0][2],
                    "timestamp": rows[0][3]
                }
            }
            
            return analysis
        
        finally:
            conn.close()
    
    def stop_monitoring(self):
        """停止监听"""
        self.monitoring = False
        print("🛑 ERP数据监听已停止")


