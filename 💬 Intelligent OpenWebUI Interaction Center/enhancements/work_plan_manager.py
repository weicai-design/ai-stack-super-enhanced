"""
工作计划管理模块
基于用户行为学习自动生成和编排工作计划
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class WorkPlanManager:
    """工作计划管理器"""
    
    def __init__(self, db_path: str = "work_plans.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化工作计划数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 工作计划表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                plan_date TEXT NOT NULL,
                plan_title TEXT NOT NULL,
                plan_description TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'pending',
                start_time TEXT,
                end_time TEXT,
                duration_minutes INTEGER,
                auto_generated BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 计划项任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plan_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                task_title TEXT NOT NULL,
                task_description TEXT,
                task_order INTEGER DEFAULT 0,
                estimated_minutes INTEGER,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (plan_id) REFERENCES work_plans(id)
            )
        """)
        
        # 计划关联备忘录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS plan_memo_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plan_id INTEGER NOT NULL,
                memo_id INTEGER NOT NULL,
                link_type TEXT DEFAULT 'related',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (plan_id) REFERENCES work_plans(id)
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ 工作计划数据库初始化完成: {self.db_path}")
    
    def generate_plan_from_learning(self, user_id: str, user_profile: Dict[str, Any], date: str = None) -> List[Dict[str, Any]]:
        """
        基于用户行为学习生成工作计划（初排）
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        plans = []
        
        # 根据用户使用模式生成计划
        if "frequently_used_system" in user_profile.get("patterns", {}):
            system = user_profile["patterns"]["frequently_used_system"]["data"]
            
            if system == "erp":
                plans.append({
                    "title": "检查财务数据",
                    "description": "查看今日财务报表和资金流动",
                    "priority": 3,
                    "start_time": "09:00",
                    "duration_minutes": 30
                })
            
            elif system == "stock":
                plans.append({
                    "title": "股票市场分析",
                    "description": "分析重点股票走势",
                    "priority": 3,
                    "start_time": "09:30",
                    "duration_minutes": 45
                })
        
        # 根据工作习惯添加计划
        if "active_hours" in user_profile.get("habits", {}):
            active_time = user_profile["habits"]["active_hours"].get("time_pattern", "09:00")
            plans.append({
                "title": "重要工作时段",
                "description": "处理重要和紧急任务",
                "priority": 5,
                "start_time": active_time.split("-")[0],
                "duration_minutes": 90
            })
        
        # 添加常规任务
        plans.extend([
            {
                "title": "查看备忘录",
                "description": "检查今日备忘录和待办事项",
                "priority": 2,
                "start_time": "08:30",
                "duration_minutes": 15
            },
            {
                "title": "午间休息",
                "description": "休息和用餐时间",
                "priority": 1,
                "start_time": "12:00",
                "duration_minutes": 60
            },
            {
                "title": "日程回顾",
                "description": "回顾今日完成情况，规划明日",
                "priority": 2,
                "start_time": "17:30",
                "duration_minutes": 30
            }
        ])
        
        # 保存到数据库
        for plan in plans:
            self.create_plan(user_id, date, plan, auto_generated=True)
        
        return plans
    
    def create_plan(self, user_id: str, date: str, plan_data: Dict[str, Any], auto_generated: bool = False) -> int:
        """创建工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO work_plans (
                user_id, plan_date, plan_title, plan_description,
                priority, start_time, duration_minutes, auto_generated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            date,
            plan_data.get("title"),
            plan_data.get("description", ""),
            plan_data.get("priority", 2),
            plan_data.get("start_time"),
            plan_data.get("duration_minutes", 60),
            1 if auto_generated else 0
        ))
        
        plan_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return plan_id
    
    def get_plans_by_date(self, user_id: str, date: str) -> List[Dict[str, Any]]:
        """获取指定日期的工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, plan_title, plan_description, priority, status,
                   start_time, duration_minutes, auto_generated
            FROM work_plans
            WHERE user_id = ? AND plan_date = ?
            ORDER BY start_time, priority DESC
        """, (user_id, date))
        
        plans = []
        for row in cursor.fetchall():
            plans.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "priority": row[3],
                "status": row[4],
                "start_time": row[5],
                "duration_minutes": row[6],
                "auto_generated": bool(row[7])
            })
        
        conn.close()
        return plans
    
    def update_plan(self, plan_id: int, updates: Dict[str, Any]):
        """更新工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ["plan_title", "plan_description", "priority", "status", "start_time", "duration_minutes"]:
                set_clauses.append(f"{key} = ?")
                values.append(value)
        
        if set_clauses:
            values.append(datetime.now().isoformat())
            values.append(plan_id)
            
            query = f"UPDATE work_plans SET {', '.join(set_clauses)}, updated_at = ? WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()
        
        conn.close()
    
    def delete_plan(self, plan_id: int):
        """删除工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM work_plans WHERE id = ?", (plan_id,))
        cursor.execute("DELETE FROM plan_tasks WHERE plan_id = ?", (plan_id,))
        cursor.execute("DELETE FROM plan_memo_links WHERE plan_id = ?", (plan_id,))
        
        conn.commit()
        conn.close()
    
    def reorder_plans(self, user_id: str, date: str, plan_ids_in_order: List[int]):
        """重新排序工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for order, plan_id in enumerate(plan_ids_in_order):
            cursor.execute("""
                UPDATE work_plans
                SET updated_at = ?
                WHERE id = ? AND user_id = ? AND plan_date = ?
            """, (datetime.now().isoformat(), plan_id, user_id, date))
        
        conn.commit()
        conn.close()
    
    def link_memo_to_plan(self, plan_id: int, memo_id: int, link_type: str = "related"):
        """关联备忘录到工作计划"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO plan_memo_links (plan_id, memo_id, link_type)
            VALUES (?, ?, ?)
        """, (plan_id, memo_id, link_type))
        
        conn.commit()
        conn.close()
    
    def get_linked_memos(self, plan_id: int) -> List[int]:
        """获取计划关联的备忘录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT memo_id FROM plan_memo_links
            WHERE plan_id = ?
        """, (plan_id,))
        
        memo_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return memo_ids

