#!/usr/bin/env python3
"""
可视化报表生成器
Visual Report Generator

自动生成各种业务报表和图表
"""

import sqlite3
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import matplotlib
matplotlib.use('Agg')  # 无GUI模式
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class ReportGenerator:
    """报表生成器"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = "/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management/ai_stack.db"
        self.db_path = db_path
        self.output_dir = Path("/Users/ywc/ai-stack-super-enhanced/reports")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置样式
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def generate_financial_report(self) -> str:
        """生成财务报表"""
        print("\n生成财务报表...")
        
        conn = sqlite3.connect(self.db_path)
        
        # 查询财务数据
        query = """
        SELECT date, income, expense, profit
        FROM financial_data
        ORDER BY date DESC
        LIMIT 30
        """
        
        try:
            df = pd.read_sql_query(query, conn)
            
            if len(df) == 0:
                print("⚠️  没有财务数据")
                return None
            
            # 创建图表
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('财务分析报表', fontsize=16, fontweight='bold')
            
            # 1. 收入支出趋势
            ax1 = axes[0, 0]
            ax1.plot(df['date'], df['income'], marker='o', label='收入', linewidth=2)
            ax1.plot(df['date'], df['expense'], marker='s', label='支出', linewidth=2)
            ax1.set_title('收入支出趋势')
            ax1.set_xlabel('日期')
            ax1.set_ylabel('金额（元）')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            ax1.tick_params(axis='x', rotation=45)
            
            # 2. 利润趋势
            ax2 = axes[0, 1]
            ax2.plot(df['date'], df['profit'], marker='d', color='green', linewidth=2)
            ax2.set_title('利润趋势')
            ax2.set_xlabel('日期')
            ax2.set_ylabel('利润（元）')
            ax2.grid(True, alpha=0.3)
            ax2.tick_params(axis='x', rotation=45)
            
            # 3. 收入支出对比柱状图
            ax3 = axes[1, 0]
            x = range(len(df))
            width = 0.35
            ax3.bar([i - width/2 for i in x], df['income'], width, label='收入', alpha=0.8)
            ax3.bar([i + width/2 for i in x], df['expense'], width, label='支出', alpha=0.8)
            ax3.set_title('收入支出对比')
            ax3.set_xlabel('日期索引')
            ax3.set_ylabel('金额（元）')
            ax3.legend()
            ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. 利润率分析
            ax4 = axes[1, 1]
            df['profit_margin'] = (df['profit'] / df['income'] * 100).fillna(0)
            ax4.bar(df['date'], df['profit_margin'], alpha=0.8, color='coral')
            ax4.set_title('利润率分析')
            ax4.set_xlabel('日期')
            ax4.set_ylabel('利润率（%）')
            ax4.axhline(y=0, color='r', linestyle='--', alpha=0.5)
            ax4.grid(True, alpha=0.3, axis='y')
            ax4.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            output_file = self.output_dir / f"financial_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 财务报表已生成: {output_file}")
            
            # 生成摘要
            summary = {
                "period": f"{df['date'].min()} 至 {df['date'].max()}",
                "total_income": float(df['income'].sum()),
                "total_expense": float(df['expense'].sum()),
                "total_profit": float(df['profit'].sum()),
                "avg_profit_margin": float(df['profit_margin'].mean()),
                "days_count": len(df)
            }
            
            # 保存摘要
            summary_file = self.output_dir / f"financial_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            return str(output_file)
            
        except Exception as e:
            print(f"❌ 生成财务报表失败: {e}")
            return None
        finally:
            conn.close()
    
    def generate_customer_report(self) -> str:
        """生成客户分析报表"""
        print("\n生成客户分析报表...")
        
        conn = sqlite3.connect(self.db_path)
        
        try:
            # 查询客户数据
            df_customers = pd.read_sql_query("SELECT * FROM customers", conn)
            df_orders = pd.read_sql_query("SELECT * FROM business_orders", conn)
            
            if len(df_customers) == 0:
                print("⚠️  没有客户数据")
                return None
            
            # 创建图表
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('客户分析报表', fontsize=16, fontweight='bold')
            
            # 1. 客户类别分布
            ax1 = axes[0, 0]
            category_counts = df_customers['category'].value_counts()
            ax1.pie(category_counts.values, labels=category_counts.index, autopct='%1.1f%%', startangle=90)
            ax1.set_title('客户类别分布')
            
            # 2. 客户等级分布
            ax2 = axes[0, 1]
            level_counts = df_customers['level'].value_counts()
            ax2.bar(level_counts.index, level_counts.values, alpha=0.8)
            ax2.set_title('客户等级分布')
            ax2.set_xlabel('等级')
            ax2.set_ylabel('客户数')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. 订单状态分布
            ax3 = axes[1, 0]
            if len(df_orders) > 0:
                status_counts = df_orders['status'].value_counts()
                ax3.bar(status_counts.index, status_counts.values, alpha=0.8)
                ax3.set_title('订单状态分布')
                ax3.set_xlabel('状态')
                ax3.set_ylabel('订单数')
                ax3.tick_params(axis='x', rotation=45)
                ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. 客户数量趋势（如果有时间数据）
            ax4 = axes[1, 1]
            ax4.text(0.5, 0.5, f'总客户数: {len(df_customers)}\n总订单数: {len(df_orders)}',
                    ha='center', va='center', fontsize=20, fontweight='bold')
            ax4.axis('off')
            
            plt.tight_layout()
            
            # 保存
            output_file = self.output_dir / f"customer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ 客户报表已生成: {output_file}")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ 生成客户报表失败: {e}")
            return None
        finally:
            conn.close()
    
    def generate_comprehensive_report(self) -> str:
        """生成综合业务报表"""
        print("\n生成综合业务报表...")
        
        # 生成各类报表
        financial_report = self.generate_financial_report()
        customer_report = self.generate_customer_report()
        
        # 生成HTML综合报告
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Stack 综合业务报表</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .report-section {{
            margin: 30px 0;
        }}
        .report-section h2 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        .report-image {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 8px;
            margin: 15px 0;
        }}
        .footer {{
            margin-top: 50px;
            text-align: center;
            color: #999;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎊 AI Stack 综合业务报表</h1>
        <p><strong>生成时间</strong>: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>系统版本</strong>: v2.0.1</p>
        
        <div class="report-section">
            <h2>💰 财务分析报表</h2>
            {f'<img src="{financial_report}" class="report-image" alt="财务报表">' if financial_report else '<p>暂无数据</p>'}
        </div>
        
        <div class="report-section">
            <h2>👥 客户分析报表</h2>
            {f'<img src="{customer_report}" class="report-image" alt="客户报表">' if customer_report else '<p>暂无数据</p>'}
        </div>
        
        <div class="footer">
            <p>AI Stack Super Enhanced v2.0.1</p>
            <p>© 2025 · 自动生成</p>
        </div>
    </div>
</body>
</html>
        """
        
        html_file = self.output_dir / f"comprehensive_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✅ 综合报表已生成: {html_file}")
        print(f"   请在浏览器中打开查看")
        
        return str(html_file)


def main():
    """主函数"""
    print("="*70)
    print("  AI Stack 可视化报表生成器")
    print("="*70)
    
    generator = ReportGenerator()
    
    print("\n请选择报表类型:")
    print("1. 财务分析报表")
    print("2. 客户分析报表")
    print("3. 综合业务报表")
    print("4. 全部生成")
    
    choice = input("\n请选择 [1-4]: ").strip()
    
    if choice == '1':
        generator.generate_financial_report()
    elif choice == '2':
        generator.generate_customer_report()
    elif choice == '3':
        generator.generate_comprehensive_report()
    elif choice == '4':
        generator.generate_comprehensive_report()
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()

