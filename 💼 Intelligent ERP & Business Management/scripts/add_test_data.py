"""
添加测试数据到数据库
"""

import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management')

from datetime import date, timedelta
from core.database import SessionLocal
from core.database_models import FinancialData
import random

def add_test_data():
    """添加测试财务数据"""
    db = SessionLocal()
    
    try:
        print("📝 开始添加测试数据...")
        
        # 生成过去30天的测试数据
        today = date.today()
        for i in range(30):
            test_date = today - timedelta(days=29-i)
            
            # 添加收入数据
            revenue = FinancialData(
                date=test_date,
                period_type="daily",
                category="revenue",
                subcategory="销售收入",
                amount=random.uniform(40000, 60000),
                description=f"{test_date}的销售收入"
            )
            db.add(revenue)
            
            # 添加支出数据
            expense = FinancialData(
                date=test_date,
                period_type="daily",
                category="expense",
                subcategory="运营成本",
                amount=random.uniform(25000, 35000),
                description=f"{test_date}的运营成本"
            )
            db.add(expense)
        
        # 添加资产数据
        asset = FinancialData(
            date=today,
            period_type="daily",
            category="asset",
            subcategory="总资产",
            amount=5678901.00,
            description="当前总资产"
        )
        db.add(asset)
        
        # 添加负债数据
        liability = FinancialData(
            date=today,
            period_type="daily",
            category="liability",
            subcategory="总负债",
            amount=1234567.00,
            description="当前总负债"
        )
        db.add(liability)
        
        db.commit()
        print("✅ 测试数据添加完成！")
        print(f"   - 添加了 {30 * 2 + 2} 条财务记录")
        print(f"   - 日期范围: {today - timedelta(days=29)} 到 {today}")
        
    except Exception as e:
        print(f"❌ 添加数据失败: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_data()

