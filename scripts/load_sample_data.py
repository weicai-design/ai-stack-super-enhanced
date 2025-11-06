#!/usr/bin/env python3
"""
示例数据加载器
为系统加载示例数据，便于快速体验和测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime, timedelta
import random


class SampleDataLoader:
    """示例数据加载器"""
    
    def __init__(self):
        """初始化加载器"""
        self.loaded_data = {
            "customers": [],
            "orders": [],
            "materials": [],
            "equipments": [],
            "processes": []
        }
    
    def load_all_sample_data(self):
        """加载所有示例数据"""
        print("\n" + "=" * 60)
        print("📦 AI-Stack 示例数据加载器")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 加载各类示例数据
        self.load_sample_customers()
        self.load_sample_orders()
        self.load_sample_materials()
        self.load_sample_equipments()
        self.load_sample_knowledge()
        
        # 生成报告
        self.generate_report()
    
    def load_sample_customers(self):
        """加载示例客户"""
        print("📊 加载示例客户...")
        
        industries = ["制造业", "电子", "化工", "食品", "服装", "机械"]
        cities = ["上海", "北京", "深圳", "广州", "杭州", "成都"]
        
        customers = []
        for i in range(1, 21):  # 20个客户
            customer = {
                "customer_id": f"CUST{i:03d}",
                "name": f"{random.choice(cities)}{random.choice(['科技', '实业', '制造', '发展'])}有限公司",
                "industry": random.choice(industries),
                "contact": {
                    "person": f"联系人{i}",
                    "phone": f"138{random.randint(10000000, 99999999)}",
                    "email": f"contact{i}@example.com"
                },
                "credit_rating": random.choice(["A", "B", "C"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            }
            customers.append(customer)
        
        self.loaded_data["customers"] = customers
        print(f"  ✅ 已加载 {len(customers)} 个客户")
    
    def load_sample_orders(self):
        """加载示例订单"""
        print("📋 加载示例订单...")
        
        orders = []
        for i in range(1, 31):  # 30个订单
            customer_id = f"CUST{random.randint(1, 20):03d}"
            
            order = {
                "order_id": f"ORD{datetime.now().strftime('%Y%m%d')}{i:04d}",
                "customer_id": customer_id,
                "items": [
                    {
                        "product_id": f"PROD{random.randint(1, 10):03d}",
                        "quantity": random.randint(100, 1000),
                        "price": random.uniform(50, 500)
                    }
                    for _ in range(random.randint(1, 3))
                ],
                "status": random.choice(["pending", "confirmed", "in_production", "delivered"]),
                "created_at": (datetime.now() - timedelta(days=random.randint(1, 60))).isoformat()
            }
            orders.append(order)
        
        self.loaded_data["orders"] = orders
        print(f"  ✅ 已加载 {len(orders)} 个订单")
    
    def load_sample_materials(self):
        """加载示例物料"""
        print("📦 加载示例物料...")
        
        material_types = ["原材料", "零部件", "包装材料", "耗材"]
        units = ["个", "kg", "米", "箱"]
        
        materials = []
        for i in range(1, 51):  # 50个物料
            material = {
                "material_id": f"MAT{i:04d}",
                "name": f"物料-{i}",
                "material_type": random.choice(material_types),
                "unit": random.choice(units),
                "safety_stock": random.randint(100, 500),
                "current_stock": random.randint(0, 1000),
                "reorder_point": random.randint(50, 200)
            }
            materials.append(material)
        
        self.loaded_data["materials"] = materials
        print(f"  ✅ 已加载 {len(materials)} 个物料")
    
    def load_sample_equipments(self):
        """加载示例设备"""
        print("🔧 加载示例设备...")
        
        categories = ["加工设备", "检测设备", "包装设备", "运输设备"]
        manufacturers = ["厂商A", "厂商B", "厂商C", "厂商D"]
        
        equipments = []
        for i in range(1, 16):  # 15个设备
            equipment = {
                "equipment_id": f"EQP{i:03d}",
                "name": f"{random.choice(categories)}-{i}",
                "category": random.choice(categories),
                "manufacturer": random.choice(manufacturers),
                "status": random.choice(["available", "in_use", "maintenance"]),
                "usage_hours": random.randint(0, 5000),
                "purchase_date": (datetime.now() - timedelta(days=random.randint(365, 1825))).strftime('%Y-%m-%d')
            }
            equipments.append(equipment)
        
        self.loaded_data["equipments"] = equipments
        print(f"  ✅ 已加载 {len(equipments)} 个设备")
    
    def load_sample_knowledge(self):
        """加载示例知识库"""
        print("📚 加载示例知识...")
        
        knowledge_items = [
            {"title": "产品使用手册", "category": "产品文档"},
            {"title": "质量管理规范", "category": "质量体系"},
            {"title": "采购流程指南", "category": "流程文档"},
            {"title": "设备操作手册", "category": "设备文档"},
            {"title": "安全生产规程", "category": "安全管理"}
        ]
        
        print(f"  ✅ 已准备 {len(knowledge_items)} 个知识条目")
    
    def generate_report(self):
        """生成加载报告"""
        print("\n" + "=" * 60)
        print("📊 示例数据加载报告")
        print("=" * 60)
        
        print(f"\n✅ 客户数据: {len(self.loaded_data['customers'])} 个")
        print(f"✅ 订单数据: {len(self.loaded_data['orders'])} 个")
        print(f"✅ 物料数据: {len(self.loaded_data['materials'])} 个")
        print(f"✅ 设备数据: {len(self.loaded_data['equipments'])} 个")
        
        print("\n" + "=" * 60)
        print("🎉 示例数据加载完成！")
        print("=" * 60)
        print("\n💡 提示:")
        print("  • 访问 http://localhost:8013/docs 查看ERP API")
        print("  • 访问 http://localhost:8020 开始使用AI交互")
        print("  • 打开 unified-dashboard/index.html 查看控制台")
        print("\n" + "=" * 60)


def main():
    """主函数"""
    loader = SampleDataLoader()
    loader.load_all_sample_data()


if __name__ == "__main__":
    main()

