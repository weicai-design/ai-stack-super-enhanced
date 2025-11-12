"""
ERP管理器（增强版）
ERP Manager

版本: v1.0.0
"""

import logging
from typing import Any, Dict, List, Optional
from collections import defaultdict
from .models import Customer, Order, Project, Purchase, Material, Production, Quality, Warehouse, Delivery
from .modules.customer import customer_manager
from .modules.order import order_manager
from .modules.production import production_manager

logger = logging.getLogger(__name__)


class ERPManager:
    """ERP管理器（增强版）"""
    
    def __init__(self):
        self.customers: Dict[str, List[Customer]] = defaultdict(list)
        self.orders: Dict[str, List[Order]] = defaultdict(list)
        self.projects: Dict[str, List[Project]] = defaultdict(list)
        self.purchases: Dict[str, List[Purchase]] = defaultdict(list)
        self.materials: Dict[str, List[Material]] = defaultdict(list)
        self.productions: Dict[str, List[Production]] = defaultdict(list)
        self.qualities: Dict[str, List[Quality]] = defaultdict(list)
        self.warehouses: Dict[str, List[Warehouse]] = defaultdict(list)
        self.deliveries: Dict[str, List[Delivery]] = defaultdict(list)
        
        # 子模块管理器
        self.customer_mgr = customer_manager
        self.order_mgr = order_manager
        self.production_mgr = production_manager
        
        logger.info("✅ ERP管理器（增强版）已初始化")
    
    # ==================== 客户管理 ====================
    
    def add_customer(self, tenant_id: str, customer: Customer) -> Customer:
        """添加客户"""
        customer.tenant_id = tenant_id
        self.customers[tenant_id].append(customer)
        return self.customer_mgr.add_customer(tenant_id, customer)
    
    def get_customers(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Customer]:
        """获取客户列表"""
        return self.customer_mgr.get_customers(tenant_id, filters)
    
    # ==================== 订单管理 ====================
    
    def create_order(self, tenant_id: str, order: Order) -> Order:
        """创建订单"""
        order.tenant_id = tenant_id
        order.total_amount = order.quantity * order.unit_price
        self.orders[tenant_id].append(order)
        return self.order_mgr.create_order(tenant_id, order)
    
    def get_orders(self, tenant_id: str, filters: Optional[Dict] = None) -> List[Order]:
        """获取订单列表"""
        return self.order_mgr.get_orders(tenant_id, filters)
    
    def update_order_status(self, tenant_id: str, order_id: str, status: str) -> Optional[Order]:
        """更新订单状态"""
        return self.order_mgr.update_order_status(tenant_id, order_id, status)
    
    # ==================== 项目管理 ====================
    
    def create_project(self, tenant_id: str, project: Project) -> Project:
        """创建项目"""
        project.tenant_id = tenant_id
        self.projects[tenant_id].append(project)
        logger.info(f"项目已创建: {project.name}")
        return project
    
    def get_projects(self, tenant_id: str) -> List[Project]:
        """获取项目列表"""
        return self.projects.get(tenant_id, [])
    
    # ==================== 采购管理 ====================
    
    def create_purchase(self, tenant_id: str, purchase: Purchase) -> Purchase:
        """创建采购单"""
        purchase.tenant_id = tenant_id
        purchase.total_amount = purchase.quantity * purchase.unit_price
        self.purchases[tenant_id].append(purchase)
        logger.info(f"采购单已创建: {purchase.material_name}")
        return purchase
    
    def get_purchases(self, tenant_id: str) -> List[Purchase]:
        """获取采购列表"""
        return self.purchases.get(tenant_id, [])
    
    # ==================== 生产管理 ====================
    
    def create_production_plan(self, tenant_id: str, production: Production) -> Production:
        """创建生产计划"""
        return self.production_mgr.create_production_plan(tenant_id, production)
    
    def get_productions(self, tenant_id: str) -> List[Production]:
        """获取生产列表"""
        return self.production_mgr.productions.get(tenant_id, [])
    
    # ==================== 物料管理 ====================
    
    def manage_material(self, tenant_id: str, material: Material) -> Material:
        """管理物料"""
        return self.production_mgr.manage_material(tenant_id, material)
    
    def get_materials(self, tenant_id: str) -> List[Material]:
        """获取物料列表"""
        return self.production_mgr.materials.get(tenant_id, [])
    
    # ==================== 质量管理 ====================
    
    def record_quality_check(self, tenant_id: str, quality: Quality) -> Quality:
        """记录质量检验"""
        quality.tenant_id = tenant_id
        self.qualities[tenant_id].append(quality)
        logger.info(f"质量检验已记录: {quality.production_id}")
        return quality
    
    # ==================== 仓储管理 ====================
    
    def warehouse_in(self, tenant_id: str, warehouse: Warehouse) -> Warehouse:
        """入库"""
        warehouse.tenant_id = tenant_id
        self.warehouses[tenant_id].append(warehouse)
        logger.info(f"入库完成: {warehouse.material_id}")
        return warehouse
    
    def get_inventory(self, tenant_id: str) -> List[Warehouse]:
        """获取库存"""
        return self.warehouses.get(tenant_id, [])
    
    # ==================== 交付管理 ====================
    
    def create_delivery(self, tenant_id: str, delivery: Delivery) -> Delivery:
        """创建交付单"""
        delivery.tenant_id = tenant_id
        self.deliveries[tenant_id].append(delivery)
        logger.info(f"交付单已创建: {delivery.delivery_no}")
        return delivery
    
    def get_deliveries(self, tenant_id: str) -> List[Delivery]:
        """获取交付列表"""
        return self.deliveries.get(tenant_id, [])
    
    # ==================== 统计分析 ====================
    
    def get_statistics(self, tenant_id: str) -> dict:
        """获取ERP统计信息"""
        order_stats = self.order_mgr.get_order_statistics(tenant_id)
        material_shortage = self.production_mgr.check_material_shortage(tenant_id)
        
        return {
            "total_customers": len(self.customers.get(tenant_id, [])),
            "total_orders": order_stats.get("total_orders", 0),
            "total_amount": order_stats.get("total_amount", 0),
            "total_projects": len(self.projects.get(tenant_id, [])),
            "total_materials": len(self.materials.get(tenant_id, [])),
            "material_shortage_count": len(material_shortage),
            "total_productions": len(self.productions.get(tenant_id, [])),
            "total_deliveries": len(self.deliveries.get(tenant_id, []))
        }


erp_manager = ERPManager()

