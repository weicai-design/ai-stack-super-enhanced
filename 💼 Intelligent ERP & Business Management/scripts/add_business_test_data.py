"""
添加业务测试数据（客户、订单、项目）
"""

import sys
sys.path.insert(0, '/Users/ywc/ai-stack-super-enhanced/💼 Intelligent ERP & Business Management')

from datetime import date, timedelta
from core.database import SessionLocal
from core.database_models import Customer, Order, OrderItem, Project
import random

def add_business_data():
    """添加测试业务数据"""
    db = SessionLocal()
    
    try:
        print("📝 开始添加业务测试数据...")
        
        # 1. 添加客户数据
        customers = [
            Customer(
                name="ABC科技有限公司",
                code="C-001",
                category="VIP",
                contact_person="张三",
                contact_phone="13800138001",
                contact_email="zhangsan@abc.com",
                address="北京市海淀区中关村大街1号"
            ),
            Customer(
                name="XYZ贸易集团",
                code="C-002",
                category="普通",
                contact_person="李四",
                contact_phone="13800138002",
                contact_email="lisi@xyz.com",
                address="上海市浦东新区陆家嘴环路1000号"
            ),
            Customer(
                name="123制造企业",
                code="C-003",
                category="VIP",
                contact_person="王五",
                contact_phone="13800138003",
                contact_email="wangwu@123.com",
                address="深圳市南山区科技园南区"
            ),
            Customer(
                name="DEF互联网公司",
                code="C-004",
                category="普通",
                contact_person="赵六",
                contact_phone="13800138004",
                contact_email="zhaoliu@def.com",
                address="杭州市西湖区文三路"
            ),
            Customer(
                name="GHI电子商务",
                code="C-005",
                category="新客户",
                contact_person="孙七",
                contact_phone="13800138005",
                contact_email="sunqi@ghi.com",
                address="广州市天河区珠江新城"
            ),
            Customer(
                name="JKL物流公司",
                code="C-006",
                category="VIP",
                contact_person="周八",
                contact_phone="13800138006",
                contact_email="zhouba@jkl.com",
                address="成都市高新区天府大道"
            ),
            Customer(
                name="MNO金融服务",
                code="C-007",
                category="普通",
                contact_person="吴九",
                contact_phone="13800138007",
                contact_email="wujiu@mno.com",
                address="武汉市江汉区建设大道"
            ),
            Customer(
                name="PQR教育集团",
                code="C-008",
                category="新客户",
                contact_person="郑十",
                contact_phone="13800138008",
                contact_email="zhengshi@pqr.com",
                address="南京市玄武区中山路"
            ),
        ]
        
        for customer in customers:
            db.add(customer)
        db.commit()
        
        print(f"✅ 添加了 {len(customers)} 个客户")
        
        # 2. 添加项目数据
        projects = [
            Project(
                project_name="企业数字化转型项目",
                project_code="P-001",
                customer_id=1,
                start_date=date(2025, 1, 1),
                end_date=date(2025, 12, 31),
                status="in_progress",
                budget=500000.00,
                description="企业全面数字化转型方案"
            ),
            Project(
                project_name="供应链管理系统",
                project_code="P-002",
                customer_id=2,
                start_date=date(2025, 3, 1),
                end_date=date(2025, 9, 30),
                status="in_progress",
                budget=300000.00,
                description="供应链管理系统开发与实施"
            ),
            Project(
                project_name="智能制造平台",
                project_code="P-003",
                customer_id=3,
                start_date=date(2025, 2, 1),
                end_date=date(2025, 11, 30),
                status="in_progress",
                budget=800000.00,
                description="智能制造平台建设"
            ),
        ]
        
        for project in projects:
            db.add(project)
        db.commit()
        
        print(f"✅ 添加了 {len(projects)} 个项目")
        
        # 3. 添加订单数据（过去6个月）
        today = date.today()
        order_count = 0
        
        for i in range(180):  # 180天
            order_date = today - timedelta(days=179-i)
            
            # 随机选择客户
            customer_id = random.randint(1, len(customers))
            
            # 每天0-3个订单
            daily_orders = random.randint(0, 3)
            
            for j in range(daily_orders):
                # 订单金额
                total_amount = random.uniform(10000, 100000)
                
                order = Order(
                    order_number=f"SO-{order_date.strftime('%Y%m%d')}-{j+1:03d}",
                    customer_id=customer_id,
                    project_id=random.choice([None, 1, 2, 3]),
                    order_date=order_date,
                    delivery_date=order_date + timedelta(days=random.randint(7, 30)),
                    total_amount=total_amount,
                    status=random.choice(['pending', 'confirmed', 'in_production', 'completed']),
                    notes=f"订单备注 - {order_date}"
                )
                db.add(order)
                db.flush()
                
                # 添加订单明细（1-5个产品）
                item_count = random.randint(1, 5)
                for k in range(item_count):
                    unit_price = random.uniform(1000, 20000)
                    quantity = random.randint(1, 10)
                    
                    order_item = OrderItem(
                        order_id=order.id,
                        product_name=f"产品-{k+1}",
                        product_code=f"P{k+1:03d}",
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=unit_price * quantity,
                        notes=f"产品明细"
                    )
                    db.add(order_item)
                
                order_count += 1
        
        db.commit()
        print(f"✅ 添加了 {order_count} 个订单")
        
        print("=" * 50)
        print("🎉 业务测试数据添加完成！")
        print(f"   - 客户: {len(customers)} 个")
        print(f"   - 项目: {len(projects)} 个")
        print(f"   - 订单: {order_count} 个")
        print(f"   - 日期范围: {today - timedelta(days=179)} 到 {today}")
        
    except Exception as e:
        print(f"❌ 添加数据失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_business_data()

