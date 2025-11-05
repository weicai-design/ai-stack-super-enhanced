"""
采购管理数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database_models import Base


class Supplier(Base):
    """供应商表"""
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, comment='供应商编号')
    name = Column(String(200), nullable=False, comment='供应商名称')
    category = Column(String(50), comment='供应商类别')
    level = Column(String(20), comment='供应商等级: A/B/C')
    
    # 联系信息
    contact_person = Column(String(100), comment='联系人')
    phone = Column(String(50), comment='电话')
    email = Column(String(100), comment='邮箱')
    address = Column(Text, comment='地址')
    
    # 合作信息
    cooperation_years = Column(Integer, comment='合作年限')
    credit_rating = Column(String(20), comment='信用等级')
    payment_terms = Column(String(100), comment='付款条件')
    
    # 统计信息
    total_purchase_amount = Column(Float, default=0, comment='累计采购金额')
    on_time_delivery_rate = Column(Float, comment='准时交货率')
    quality_pass_rate = Column(Float, comment='质量合格率')
    
    # 状态
    status = Column(String(20), default='active', comment='状态: active/inactive/blacklist')
    
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    """采购订单表"""
    __tablename__ = 'purchase_orders'
    
    id = Column(Integer, primary_key=True)
    po_no = Column(String(50), unique=True, nullable=False, comment='采购订单号')
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=False)
    
    # 订单信息
    order_date = Column(DateTime, default=datetime.now, comment='订单日期')
    expected_delivery_date = Column(DateTime, comment='预计交货日期')
    actual_delivery_date = Column(DateTime, comment='实际交货日期')
    
    # 金额信息
    total_amount = Column(Float, comment='订单总额')
    paid_amount = Column(Float, default=0, comment='已付金额')
    
    # 状态
    status = Column(String(50), default='pending', comment='状态: pending/confirmed/in_transit/received/completed/cancelled')
    
    # 审批
    approved_by = Column(String(100), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    supplier = relationship("Supplier", back_populates="purchase_orders")
    items = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")


class PurchaseOrderItem(Base):
    """采购订单明细表"""
    __tablename__ = 'purchase_order_items'
    
    id = Column(Integer, primary_key=True)
    po_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=False)
    
    # 物料信息
    material_code = Column(String(50), comment='物料编码')
    material_name = Column(String(200), comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), comment='单位')
    
    # 数量和价格
    quantity = Column(Float, comment='采购数量')
    unit_price = Column(Float, comment='单价')
    amount = Column(Float, comment='金额')
    
    # 交货信息
    received_quantity = Column(Float, default=0, comment='已收货数量')
    qualified_quantity = Column(Float, default=0, comment='合格数量')
    
    # 时间
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联
    purchase_order = relationship("PurchaseOrder", back_populates="items")


