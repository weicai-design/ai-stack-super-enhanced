#!/usr/bin/env python3
"""
数据导入导出工具
Data Import/Export Tool

支持ERP系统各模块数据的导入导出
"""

import sqlite3
import json
import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import argparse


class DataImportExport:
    """数据导入导出类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management/ai_stack.db"
        self.db_path = db_path
        self.export_dir = Path("/Users/ywc/ai-stack-super-enhanced/data/exports")
        self.import_dir = Path("/Users/ywc/ai-stack-super-enhanced/data/imports")
        
        # 确保目录存在
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.import_dir.mkdir(parents=True, exist_ok=True)
    
    def export_table_to_json(self, table_name: str) -> str:
        """导出表为JSON"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        data = [dict(row) for row in rows]
        
        filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.export_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        conn.close()
        
        print(f"✅ 导出成功: {filename} ({len(data)} 条记录)")
        return str(filepath)
    
    def export_table_to_csv(self, table_name: str) -> str:
        """导出表为CSV"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.export_dir / filename
        
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        conn.close()
        
        print(f"✅ 导出成功: {filename} ({len(df)} 条记录)")
        return str(filepath)
    
    def export_table_to_excel(self, table_name: str) -> str:
        """导出表为Excel"""
        conn = sqlite3.connect(self.db_path)
        
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        filename = f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = self.export_dir / filename
        
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        conn.close()
        
        print(f"✅ 导出成功: {filename} ({len(df)} 条记录)")
        return str(filepath)
    
    def import_from_json(self, table_name: str, json_file: str):
        """从JSON导入数据"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        # 插入数据
        imported = 0
        for record in data:
            # 过滤只包含表中存在的列
            filtered_record = {k: v for k, v in record.items() if k in columns}
            
            placeholders = ', '.join(['?' for _ in filtered_record])
            columns_str = ', '.join(filtered_record.keys())
            
            try:
                cursor.execute(
                    f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})",
                    list(filtered_record.values())
                )
                imported += 1
            except sqlite3.IntegrityError:
                pass  # 跳过重复记录
        
        conn.commit()
        conn.close()
        
        print(f"✅ 导入成功: {imported}/{len(data)} 条记录")
    
    def import_from_csv(self, table_name: str, csv_file: str):
        """从CSV导入数据"""
        df = pd.read_csv(csv_file)
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            df.to_sql(table_name, conn, if_exists='append', index=False)
            print(f"✅ 导入成功: {len(df)} 条记录")
        except Exception as e:
            print(f"❌ 导入失败: {e}")
        finally:
            conn.close()
    
    def export_all_tables(self, format='json'):
        """导出所有表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        conn.close()
        
        print(f"\n开始导出 {len(tables)} 个表...\n")
        
        exported_files = []
        for table in tables:
            try:
                if format == 'json':
                    filepath = self.export_table_to_json(table)
                elif format == 'csv':
                    filepath = self.export_table_to_csv(table)
                elif format == 'excel':
                    filepath = self.export_table_to_excel(table)
                
                exported_files.append(filepath)
            except Exception as e:
                print(f"❌ 导出 {table} 失败: {e}")
        
        print(f"\n✅ 导出完成！共 {len(exported_files)} 个文件")
        print(f"导出目录: {self.export_dir}")
        
        return exported_files
    
    def list_tables(self):
        """列出所有表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        
        print(f"\n数据库中的表 ({len(tables)} 个):\n")
        for i, table in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{i:2d}. {table:<30} ({count} 条记录)")
        
        conn.close()
        
        return tables


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='AI Stack 数据导入导出工具')
    parser.add_argument('action', choices=['export', 'import', 'list'], help='操作类型')
    parser.add_argument('--table', help='表名')
    parser.add_argument('--format', choices=['json', 'csv', 'excel'], default='json', help='导出格式')
    parser.add_argument('--file', help='导入文件路径')
    parser.add_argument('--all', action='store_true', help='导出所有表')
    
    args = parser.parse_args()
    
    tool = DataImportExport()
    
    if args.action == 'list':
        tool.list_tables()
    
    elif args.action == 'export':
        if args.all:
            tool.export_all_tables(format=args.format)
        elif args.table:
            if args.format == 'json':
                tool.export_table_to_json(args.table)
            elif args.format == 'csv':
                tool.export_table_to_csv(args.table)
            elif args.format == 'excel':
                tool.export_table_to_excel(args.table)
        else:
            print("❌ 请指定表名或使用 --all 导出所有表")
    
    elif args.action == 'import':
        if args.table and args.file:
            if args.file.endswith('.json'):
                tool.import_from_json(args.table, args.file)
            elif args.file.endswith('.csv'):
                tool.import_from_csv(args.table, args.file)
            else:
                print("❌ 不支持的文件格式")
        else:
            print("❌ 请指定表名和文件路径")


if __name__ == "__main__":
    # 如果没有参数，显示使用帮助
    if len(sys.argv) == 1:
        print("""
╔════════════════════════════════════════════════════════════╗
║   AI Stack 数据导入导出工具                                ║
╚════════════════════════════════════════════════════════════╝

使用方法:

1. 列出所有表:
   python3 data_import_export.py list

2. 导出单个表为JSON:
   python3 data_import_export.py export --table financial_data --format json

3. 导出所有表为CSV:
   python3 data_import_export.py export --all --format csv

4. 导出为Excel:
   python3 data_import_export.py export --table customers --format excel

5. 导入JSON数据:
   python3 data_import_export.py import --table financial_data --file data.json

6. 导入CSV数据:
   python3 data_import_export.py import --table customers --file customers.csv

导出目录: data/exports/
导入目录: data/imports/

支持格式: JSON, CSV, Excel
        """)
    else:
        main()

