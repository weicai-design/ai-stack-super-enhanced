"""
ERP Core Module
ERP核心模块

提供ERP系统的核心功能：
1. 数据库模型
2. 核心服务
3. API路由
"""

from .database_models import (
    Base,
    FinancialData,
    FinancialReport,
    BusinessProcess,
    ProcessInstance,
    ProcessTracking,
    Customer,
    Order,
    OrderItem,
    Project,
    ProductionPlan,
    MaterialRequirement,
    ProcurementPlan,
    MaterialReceipt,
    ProductionExecution,
    QualityInspection,
    Warehouse,
    Inventory,
    Delivery,
    Shipment,
    Payment,
    ProcessException,
    ImprovementPlan,
    AfterSalesTicket,
    CustomerComplaint,
    RepairRecord,
    ReturnRecord,
    PeriodType,
    FinancialCategory,
    CostCategory,
    ProcessStatus,
)

__all__ = [
    "Base",
    "FinancialData",
    "FinancialReport",
    "BusinessProcess",
    "ProcessInstance",
    "ProcessTracking",
    "Customer",
    "Order",
    "OrderItem",
    "Project",
    "ProductionPlan",
    "MaterialRequirement",
    "ProcurementPlan",
    "MaterialReceipt",
    "ProductionExecution",
    "QualityInspection",
    "Warehouse",
    "Inventory",
    "Delivery",
    "Shipment",
    "Payment",
    "ProcessException",
    "ImprovementPlan",
    "AfterSalesTicket",
    "CustomerComplaint",
    "RepairRecord",
    "ReturnRecord",
    "PeriodType",
    "FinancialCategory",
    "CostCategory",
    "ProcessStatus",
]

