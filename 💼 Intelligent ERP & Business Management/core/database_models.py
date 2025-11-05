"""
ERP Database Models
ERP数据库模型定义

根据需求2.x：企业经营运营管理

核心表结构：
1. 财务数据表
2. 业务流程表
3. 订单和项目管理表
4. 生产管理表
5. 质量管理表
6. 仓储和交付表
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Numeric,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class PeriodType(str, Enum):
    """时间周期类型"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class FinancialCategory(str, Enum):
    """财务类别"""
    REVENUE = "revenue"  # 收入
    EXPENSE = "expense"  # 支出
    ASSET = "asset"  # 资产
    LIABILITY = "liability"  # 负债
    PROFIT = "profit"  # 利润
    INVESTMENT = "investment"  # 投入


class CostCategory(str, Enum):
    """成本类别"""
    SALES = "sales"  # 销售费用
    FINANCE = "finance"  # 财务费用
    MANAGEMENT = "management"  # 管理费用
    PRODUCTION = "production"  # 生产费用
    MANUFACTURING = "manufacturing"  # 制造费用


class ProcessStatus(str, Enum):
    """流程状态"""
    PENDING = "pending"  # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    COMPLETED = "completed"  # 已完成
    SUSPENDED = "suspended"  # 已暂停
    CANCELLED = "cancelled"  # 已取消


# ============ 财务数据表 ============

class FinancialData(Base):
    """财务数据表"""
    __tablename__ = "financial_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    period_type = Column(String(20), nullable=False, default=PeriodType.DAILY)
    category = Column(String(20), nullable=False)  # FinancialCategory
    subcategory = Column(String(100))  # 子类别
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    source_document = Column(String(200))  # 来源单据
    extra_metadata = Column(JSON)  # 扩展元数据
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_financial_date_category', 'date', 'category'),
        Index('idx_financial_period', 'period_type', 'date'),
    )


class FinancialReport(Base):
    """财务报表表"""
    __tablename__ = "financial_reports"

    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), nullable=False)  # balance_sheet, income_statement, cash_flow
    period_type = Column(String(20), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    report_data = Column(JSON, nullable=False)  # 报表数据（JSON格式）
    generated_at = Column(DateTime, default=datetime.utcnow)
    generated_by = Column(String(100))

    __table_args__ = (
        Index('idx_report_period', 'report_type', 'period_type', 'period_start'),
    )


# ============ 业务流程表 ============

class BusinessProcess(Base):
    """业务流程定义表"""
    __tablename__ = "business_processes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    description = Column(Text)
    process_type = Column(String(50))  # 流程类型
    stages = Column(JSON)  # 流程阶段定义（JSON数组）
    kpi_metrics = Column(JSON)  # KPI指标定义
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    instances = relationship("ProcessInstance", back_populates="process")


class ProcessInstance(Base):
    """流程实例表"""
    __tablename__ = "process_instances"

    id = Column(Integer, primary_key=True, index=True)
    process_id = Column(Integer, ForeignKey("business_processes.id"), nullable=False)
    instance_name = Column(String(200))
    status = Column(String(20), default=ProcessStatus.PENDING, index=True)
    current_stage = Column(String(100))  # 当前阶段
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    process = relationship("BusinessProcess", back_populates="instances")
    tracking_records = relationship("ProcessTracking", back_populates="instance")


class ProcessTracking(Base):
    """流程跟踪记录表"""
    __tablename__ = "process_tracking"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("process_instances.id"), nullable=False)
    stage = Column(String(100), nullable=False)
    status = Column(String(20))
    action = Column(String(200))  # 操作内容
    operator = Column(String(100))  # 操作人
    duration = Column(Integer)  # 耗时（秒）
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    instance = relationship("ProcessInstance", back_populates="tracking_records")

    __table_args__ = (
        Index('idx_tracking_instance_stage', 'instance_id', 'stage', 'created_at'),
    )


# ============ 订单和项目管理表 ============

class Customer(Base):
    """客户表"""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)  # 客户编码
    category = Column(String(50))  # 客户类别
    contact_person = Column(String(100))
    contact_phone = Column(String(50))
    contact_email = Column(String(200))
    address = Column(Text)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="customer")


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"))
    order_date = Column(Date, nullable=False, index=True)
    delivery_date = Column(Date)
    total_amount = Column(Numeric(15, 2), nullable=False)
    status = Column(String(20), default="pending", index=True)
    notes = Column(Text)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="orders")
    project = relationship("Project", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """订单明细表"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_name = Column(String(200), nullable=False)
    product_code = Column(String(50))
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total_price = Column(Numeric(15, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="items")

    __table_args__ = (
        Index('idx_order_items_order', 'order_id'),
    )


class Project(Base):
    """项目表"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(200), nullable=False)
    project_code = Column(String(50), unique=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default="planning", index=True)
    budget = Column(Numeric(15, 2))
    description = Column(Text)
    extra_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    orders = relationship("Order", back_populates="project")


# ============ 生产管理表 ============

class ProductionPlan(Base):
    """生产计划表"""
    __tablename__ = "production_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    plan_date = Column(Date, nullable=False, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(String(20), default="planned")
    quantity = Column(Numeric(10, 2), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaterialRequirement(Base):
    """物料需求表"""
    __tablename__ = "material_requirements"

    id = Column(Integer, primary_key=True, index=True)
    production_plan_id = Column(Integer, ForeignKey("production_plans.id"))
    material_code = Column(String(50), nullable=False)
    material_name = Column(String(200), nullable=False)
    required_quantity = Column(Numeric(10, 2), nullable=False)
    required_date = Column(Date)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class ProcurementPlan(Base):
    """采购计划表"""
    __tablename__ = "procurement_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_number = Column(String(50), unique=True, nullable=False)
    material_requirement_id = Column(Integer, ForeignKey("material_requirements.id"))
    supplier = Column(String(200))
    planned_date = Column(Date, nullable=False, index=True)
    expected_date = Column(Date)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(15, 2))
    total_amount = Column(Numeric(15, 2))
    status = Column(String(20), default="planned")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaterialReceipt(Base):
    """到料记录表"""
    __tablename__ = "material_receipts"

    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(50), unique=True, nullable=False)
    procurement_plan_id = Column(Integer, ForeignKey("procurement_plans.id"))
    receipt_date = Column(Date, nullable=False, index=True)
    quantity = Column(Numeric(10, 2), nullable=False)
    quality_status = Column(String(20))
    inspector = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProductionExecution(Base):
    """生产执行表"""
    __tablename__ = "production_executions"

    id = Column(Integer, primary_key=True, index=True)
    execution_number = Column(String(50), unique=True, nullable=False)
    production_plan_id = Column(Integer, ForeignKey("production_plans.id"))
    start_time = Column(DateTime, index=True)
    end_time = Column(DateTime)
    quantity_produced = Column(Numeric(10, 2))
    quantity_qualified = Column(Numeric(10, 2))
    operator = Column(String(100))
    status = Column(String(20), default="in_progress")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============ 质量管理表 ============

class QualityInspection(Base):
    """质量检验表"""
    __tablename__ = "quality_inspections"

    id = Column(Integer, primary_key=True, index=True)
    inspection_number = Column(String(50), unique=True, nullable=False)
    production_execution_id = Column(Integer, ForeignKey("production_executions.id"))
    inspection_date = Column(DateTime, nullable=False, index=True)
    inspector = Column(String(100))
    inspection_type = Column(String(50))
    result = Column(String(20))  # passed, failed, conditional
    quantity_inspected = Column(Numeric(10, 2))
    quantity_passed = Column(Numeric(10, 2))
    quantity_failed = Column(Numeric(10, 2))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# ============ 仓储和交付表 ============

class Warehouse(Base):
    """仓库表"""
    __tablename__ = "warehouses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True)
    location = Column(String(200))
    capacity = Column(Numeric(15, 2))
    manager = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Inventory(Base):
    """库存记录表"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    material_code = Column(String(50), nullable=False, index=True)
    material_name = Column(String(200), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(20))
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_inventory_warehouse_material', 'warehouse_id', 'material_code'),
    )


class Delivery(Base):
    """交付记录表"""
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    delivery_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    delivery_date = Column(Date, nullable=False, index=True)
    delivery_address = Column(Text)
    contact_person = Column(String(100))
    contact_phone = Column(String(50))
    status = Column(String(20), default="pending")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Shipment(Base):
    """发运记录表"""
    __tablename__ = "shipments"

    id = Column(Integer, primary_key=True, index=True)
    shipment_number = Column(String(50), unique=True, nullable=False)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"))
    shipment_date = Column(Date, nullable=False, index=True)
    carrier = Column(String(200))  # 承运商
    tracking_number = Column(String(100))
    status = Column(String(20), default="in_transit")
    estimated_arrival = Column(Date)
    actual_arrival = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Payment(Base):
    """回款记录表"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(50))  # 付款方式
    status = Column(String(20), default="pending")
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_payments_order_date', 'order_id', 'payment_date'),
    )


# ============ 异常分析表 ============

class ProcessException(Base):
    """流程异常表"""
    __tablename__ = "process_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(Integer, ForeignKey("process_instances.id"))
    exception_type = Column(String(50), nullable=False)
    exception_level = Column(String(20))  # info, warning, error, critical
    description = Column(Text, nullable=False)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_at = Column(DateTime)
    resolution = Column(Text)
    resolver = Column(String(100))
    status = Column(String(20), default="open")  # open, investigating, resolved, closed
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_exceptions_status_level', 'status', 'exception_level', 'detected_at'),
    )


class ImprovementPlan(Base):
    """改进计划表"""
    __tablename__ = "improvement_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    related_exception_id = Column(Integer, ForeignKey("process_exceptions.id"))
    priority = Column(String(20))  # low, medium, high, urgent
    status = Column(String(20), default="planned")  # planned, in_progress, completed
    planned_start = Column(Date)
    planned_end = Column(Date)
    actual_start = Column(Date)
    actual_end = Column(Date)
    responsible = Column(String(100))
    progress = Column(Numeric(5, 2), default=0)  # 进度百分比
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_improvements_status_priority', 'status', 'priority'),
    )

