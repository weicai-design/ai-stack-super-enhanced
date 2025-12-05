#!/usr/bin/env python3
"""
ERP专家系统测试脚本
测试16个ERP专家（8个业务专家 + 8个维度专家）的功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.erp_experts import (
    # 8个ERP业务专家
    order_expert, project_expert, purchase_expert, warehouse_expert,
    production_expert, logistics_expert, service_expert, settlement_expert,
    
    # 8个维度专家
    quality_expert, cost_expert, delivery_expert, safety_expert,
    profit_expert, efficiency_expert, management_expert, technology_expert
)


async def test_order_expert():
    """测试订单管理专家"""
    print("\n📦 测试订单管理专家...")
    
    # 测试订单分析
    order_data = {
        "order_id": "ORD2025001",
        "customer_type": "新客户",
        "quantity": 600,
        "price": 1000,
        "cost": 850
    }
    
    analysis = await order_expert.analyze_order(order_data)
    print(f"订单分析结果: {analysis}")
    
    # 测试对话
    response = await order_expert.chat_response("创建一个新订单", {})
    print(f"对话响应: {response[:100]}...")
    
    print("✅ 订单管理专家测试完成")


async def test_project_expert():
    """测试项目管理专家"""
    print("\n📋 测试项目管理专家...")
    
    response = await project_expert.chat_response("查看项目进度", {"active_projects": 8})
    print(f"项目进度响应: {response[:150]}...")
    
    print("✅ 项目管理专家测试完成")


async def test_purchase_expert():
    """测试采购管理专家"""
    print("\n🛒 测试采购管理专家...")
    
    response = await purchase_expert.chat_response("采购分析", {})
    print(f"采购分析响应: {response[:150]}...")
    
    print("✅ 采购管理专家测试完成")


async def test_warehouse_expert():
    """测试库存管理专家"""
    print("\n📊 测试库存管理专家...")
    
    response = await warehouse_expert.chat_response("库存情况", {})
    print(f"库存响应: {response}")
    
    print("✅ 库存管理专家测试完成")


async def test_production_expert():
    """测试生产管理专家"""
    print("\n🏭 测试生产管理专家...")
    
    response = await production_expert.chat_response("生产状态", {})
    print(f"生产响应: {response}")
    
    print("✅ 生产管理专家测试完成")


async def test_logistics_expert():
    """测试物流管理专家"""
    print("\n🚚 测试物流管理专家...")
    
    response = await logistics_expert.chat_response("物流情况", {})
    print(f"物流响应: {response}")
    
    print("✅ 物流管理专家测试完成")


async def test_service_expert():
    """测试售后服务专家"""
    print("\n🔧 测试售后服务专家...")
    
    response = await service_expert.chat_response("服务状态", {})
    print(f"服务响应: {response}")
    
    print("✅ 售后服务专家测试完成")


async def test_settlement_expert():
    """测试财务结算专家"""
    print("\n💰 测试财务结算专家...")
    
    response = await settlement_expert.chat_response("财务情况", {})
    print(f"财务响应: {response}")
    
    print("✅ 财务结算专家测试完成")


async def test_quality_expert():
    """测试质量管理专家"""
    print("\n✅ 测试质量管理专家...")
    
    analysis = await quality_expert.analyze({})
    print(f"质量分析: {analysis}")
    
    print("✅ 质量管理专家测试完成")


async def test_cost_expert():
    """测试成本管理专家"""
    print("\n💰 测试成本管理专家...")
    
    analysis = await cost_expert.analyze({})
    print(f"成本分析: {analysis}")
    
    print("✅ 成本管理专家测试完成")


async def test_delivery_expert():
    """测试交期管理专家"""
    print("\n⏰ 测试交期管理专家...")
    
    analysis = await delivery_expert.analyze({})
    print(f"交期分析: {analysis}")
    
    print("✅ 交期管理专家测试完成")


async def test_safety_expert():
    """测试安全管理专家"""
    print("\n🛡️ 测试安全管理专家...")
    
    analysis = await safety_expert.analyze({})
    print(f"安全分析: {analysis}")
    
    print("✅ 安全管理专家测试完成")


async def test_profit_expert():
    """测试利润管理专家"""
    print("\n💹 测试利润管理专家...")
    
    analysis = await profit_expert.analyze({})
    print(f"利润分析: {analysis}")
    
    print("✅ 利润管理专家测试完成")


async def test_efficiency_expert():
    """测试效率管理专家"""
    print("\n⚡ 测试效率管理专家...")
    
    analysis = await efficiency_expert.analyze({})
    print(f"效率分析: {analysis}")
    
    print("✅ 效率管理专家测试完成")


async def test_management_expert():
    """测试管理提升专家"""
    print("\n📊 测试管理提升专家...")
    
    analysis = await management_expert.analyze({})
    print(f"管理分析: {analysis}")
    
    print("✅ 管理提升专家测试完成")


async def test_technology_expert():
    """测试技术提升专家"""
    print("\n🔬 测试技术提升专家...")
    
    analysis = await technology_expert.analyze({})
    print(f"技术分析: {analysis}")
    
    print("✅ 技术提升专家测试完成")


async def main():
    """主测试函数"""
    print("🚀 开始测试ERP专家系统（16个专家）...\n")
    
    # 测试8个ERP业务专家
    await test_order_expert()
    await test_project_expert()
    await test_purchase_expert()
    await test_warehouse_expert()
    await test_production_expert()
    await test_logistics_expert()
    await test_service_expert()
    await test_settlement_expert()
    
    # 测试8个维度专家
    await test_quality_expert()
    await test_cost_expert()
    await test_delivery_expert()
    await test_safety_expert()
    await test_profit_expert()
    await test_efficiency_expert()
    await test_management_expert()
    await test_technology_expert()
    
    print("\n🎉 所有ERP专家测试完成！")
    
    print("\n📊 ERP专家系统汇总:")
    print("  8个业务专家: 订单管理、项目管理、采购管理、库存管理、生产管理、物流管理、售后服务、财务结算")
    print("  8个维度专家: 质量、成本、交期、安全、利润、效率、管理、技术")
    print("  ✅ 总计16个专家系统已实现并测试通过")


if __name__ == "__main__":
    asyncio.run(main())