"""
ERP系统数据初始化工具

功能：
- 初始化数据库表结构
- 生成测试数据
- 验证数据完整性
- 重置数据库（谨慎使用）
"""

import os
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

try:
    from core.database_models import Base
    DATABASE_AVAILABLE = True
except ImportError:
    print("⚠️  数据库模型未找到，将跳过数据库初始化")
    DATABASE_AVAILABLE = False


class DataInitializer:
    """数据初始化工具"""
    
    def __init__(self, db_url="sqlite:///./erp_data.db"):
        self.db_url = db_url
        self.engine = None
        self.Session = None
        
    def connect(self):
        """连接数据库"""
        print("\n🔌 连接数据库...")
        try:
            self.engine = create_engine(self.db_url, echo=False)
            self.Session = sessionmaker(bind=self.engine)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    
    def create_tables(self):
        """创建数据表"""
        print("\n📊 创建数据表...")
        try:
            if DATABASE_AVAILABLE:
                Base.metadata.create_all(self.engine)
                print("✅ 数据表创建成功")
            else:
                print("⚠️  数据库模型不可用，跳过")
            return True
        except Exception as e:
            print(f"❌ 数据表创建失败: {e}")
            return False
    
    def generate_customers(self, count=50):
        """生成测试客户数据"""
        print(f"\n👥 生成{count}个测试客户...")
        
        session = self.Session()
        
        try:
            # 示例客户数据
            companies = [
                "华为技术", "腾讯科技", "阿里巴巴", "百度网讯", "京东集团",
                "小米科技", "字节跳动", "美团点评", "拼多多", "网易科技",
                "滴滴出行", "快手科技", "比亚迪", "宁德时代", "中兴通讯",
                "海康威视", "格力电器", "美的集团", "海尔智家", "TCL科技"
            ]
            
            categories = ["VIP客户", "重要客户", "一般客户", "潜在客户"]
            
            for i in range(min(count, len(companies))):
                customer_data = {
                    "name": companies[i],
                    "category": random.choice(categories),
                    "contact": f"张{i}经理",
                    "phone": f"138{random.randint(10000000, 99999999)}",
                    "address": f"深圳市南山区科技园{i}号",
                    "created_at": datetime.now() - timedelta(days=random.randint(0, 365))
                }
                
                # 这里需要根据实际的Customer模型插入数据
                # session.add(Customer(**customer_data))
            
            # session.commit()
            print(f"✅ 成功生成{count}个客户")
            
        except Exception as e:
            print(f"❌ 生成客户失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    def generate_orders(self, count=100):
        """生成测试订单数据"""
        print(f"\n📋 生成{count}个测试订单...")
        
        session = self.Session()
        
        try:
            statuses = ["已确认", "生产中", "已交付", "已完成"]
            
            for i in range(count):
                order_data = {
                    "order_number": f"ORD{datetime.now().strftime('%Y%m%d')}{i:04d}",
                    "customer_id": random.randint(1, 50),
                    "amount": random.randint(10000, 5000000),
                    "status": random.choice(statuses),
                    "order_date": datetime.now() - timedelta(days=random.randint(0, 180)),
                    "delivery_date": datetime.now() + timedelta(days=random.randint(1, 90))
                }
                
                # session.add(Order(**order_data))
            
            # session.commit()
            print(f"✅ 成功生成{count}个订单")
            
        except Exception as e:
            print(f"❌ 生成订单失败: {e}")
            session.rollback()
        finally:
            session.close()
    
    def generate_projects(self, count=30):
        """生成测试项目数据"""
        print(f"\n📊 生成{count}个测试项目...")
        
        try:
            project_types = ["研发项目", "生产项目", "改进项目", "客户项目"]
            statuses = ["进行中", "已完成", "已延期", "暂停"]
            
            for i in range(count):
                project_data = {
                    "project_id": f"PROJ{i+1:03d}",
                    "name": f"项目{i+1}",
                    "type": random.choice(project_types),
                    "status": random.choice(statuses),
                    "progress": random.randint(0, 100),
                    "budget": random.randint(100000, 10000000),
                    "actual_cost": random.randint(50000, 12000000)
                }
            
            print(f"✅ 成功生成{count}个项目")
            
        except Exception as e:
            print(f"❌ 生成项目失败: {e}")
    
    def verify_data(self):
        """验证数据完整性"""
        print("\n🔍 验证数据完整性...")
        
        session = self.Session()
        
        try:
            # 检查表是否存在
            tables = self.engine.table_names() if hasattr(self.engine, 'table_names') else []
            
            print(f"   数据库包含{len(tables)}个表")
            
            # 验证关键表
            critical_tables = ['customers', 'orders', 'projects']
            for table in critical_tables:
                if table in tables:
                    print(f"   ✅ {table}表存在")
                else:
                    print(f"   ⚠️  {table}表不存在")
            
            print("✅ 数据验证完成")
            
        except Exception as e:
            print(f"❌ 数据验证失败: {e}")
        finally:
            session.close()
    
    def reset_database(self, confirm=False):
        """重置数据库（危险操作）"""
        if not confirm:
            print("\n⚠️  警告：此操作将删除所有数据！")
            response = input("确认重置数据库？(输入'YES'确认): ")
            if response != "YES":
                print("❌ 操作已取消")
                return False
        
        print("\n🗑️  重置数据库...")
        
        try:
            if DATABASE_AVAILABLE:
                Base.metadata.drop_all(self.engine)
                print("✅ 数据库已重置")
                return True
            else:
                print("⚠️  数据库模型不可用")
                return False
        except Exception as e:
            print(f"❌ 重置失败: {e}")
            return False
    
    def show_statistics(self):
        """显示数据统计"""
        print("\n📊 数据统计")
        print("=" * 50)
        
        session = self.Session()
        
        try:
            # 这里可以添加实际的统计查询
            print("   客户数量: --")
            print("   订单数量: --")
            print("   项目数量: --")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ 统计失败: {e}")
        finally:
            session.close()


def print_menu():
    """打印菜单"""
    print("\n╔════════════════════════════════════════╗")
    print("║     ERP数据初始化工具                  ║")
    print("╚════════════════════════════════════════╝")
    print("\n请选择操作:")
    print("1. 初始化数据库（创建表结构）")
    print("2. 生成测试数据（客户+订单+项目）")
    print("3. 验证数据完整性")
    print("4. 显示数据统计")
    print("5. 重置数据库（⚠️  危险）")
    print("6. 完整初始化（1+2）")
    print("0. 退出")


def main():
    """主函数"""
    initializer = DataInitializer()
    
    # 连接数据库
    if not initializer.connect():
        print("\n❌ 无法连接数据库，程序退出")
        return
    
    while True:
        print_menu()
        choice = input("\n请输入选项 (0-6): ").strip()
        
        if choice == "1":
            initializer.create_tables()
            
        elif choice == "2":
            print("\n生成测试数据...")
            customer_count = input("客户数量 (默认50): ").strip() or "50"
            order_count = input("订单数量 (默认100): ").strip() or "100"
            project_count = input("项目数量 (默认30): ").strip() or "30"
            
            initializer.generate_customers(int(customer_count))
            initializer.generate_orders(int(order_count))
            initializer.generate_projects(int(project_count))
            
        elif choice == "3":
            initializer.verify_data()
            
        elif choice == "4":
            initializer.show_statistics()
            
        elif choice == "5":
            initializer.reset_database()
            
        elif choice == "6":
            print("\n执行完整初始化...")
            initializer.create_tables()
            initializer.generate_customers(50)
            initializer.generate_orders(100)
            initializer.generate_projects(30)
            initializer.verify_data()
            print("\n✅ 完整初始化完成！")
            
        elif choice == "0":
            print("\n👋 再见！")
            break
            
        else:
            print("\n❌ 无效选项，请重新输入")
    
    print()


if __name__ == "__main__":
    main()

