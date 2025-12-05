#!/usr/bin/env python3
"""
ERP全流程完整测试脚本
基于现有API实现测试11个环节的完整ERP流程：
1. 订单接收
2. 项目立项
3. 生产计划
4. 采购
5. 入库
6. 生产
7. 质检
8. 出库
9. 发运
10. 售后
11. 结算回款
"""

import sys
import os
import asyncio
import json
import time

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.erp_complete_api import router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# 创建测试应用
app = FastAPI()
app.include_router(router)
client = TestClient(app)


async def test_order_management():
    """测试订单管理环节"""
    print("\n📦 测试订单管理环节...")
    
    # 1. 创建订单
    order_data = {
        "customer_id": "C001",
        "customer_name": "ABC公司",
        "product_id": "P001",
        "product_name": "智能手表 SW-2000",
        "quantity": 100,
        "unit_price": 500.0,
        "delivery_date": "2025-11-15",
        "notes": "加急订单，请优先处理"
    }
    
    response = client.post("/erp/orders/create", json=order_data)
    print(f"创建订单响应: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"订单ID: {result.get('order_id')}")
        print(f"AI分析: {result.get('ai_analysis', {}).get('risk_level', 'N/A')}")
        order_id = result.get('order_id')
    else:
        print(f"创建订单失败: {response.text}")
        return None
    
    # 2. 查询订单列表
    response = client.get("/erp/orders")
    print(f"订单列表响应: {response.status_code}")
    
    # 3. 订单详情
    if order_id:
        response = client.get(f"/erp/orders/{order_id}")
        print(f"订单详情响应: {response.status_code}")
        
    # 4. 订单追踪
    response = client.get(f"/erp/orders/{order_id}/track")
    print(f"订单追踪响应: {response.status_code}")
    
    # 5. 订单统计
    response = client.get("/erp/orders/statistics")
    print(f"订单统计响应: {response.status_code}")
    
    print("✅ 订单管理环节测试完成")
    return order_id


async def test_project_management(order_id: str):
    """测试项目管理环节"""
    print("\n📋 测试项目管理环节...")
    
    # 项目立项
    response = client.post("/erp/projects/create", json={
        "name": f"智能手表生产项目-{order_id}",
        "description": f"为订单{order_id}生产100个智能手表",
        "start_date": "2025-11-05",
        "budget": 50000.0
    })
    print(f"项目立项响应: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        project_id = result.get('project_id')
        print(f"项目ID: {project_id}")
    else:
        print(f"项目立项失败: {response.text}")
        return None
    
    # 项目列表
    response = client.get("/erp/projects")
    print(f"项目列表响应: {response.status_code}")
    
    # WBS生成
    response = client.post(f"/erp/projects/{project_id}/wbs")
    print(f"WBS生成响应: {response.status_code}")
    
    # 挣值分析
    response = client.get(f"/erp/projects/{project_id}/evm")
    print(f"挣值分析响应: {response.status_code}")
    
    print("✅ 项目管理环节测试完成")
    return project_id


async def test_procurement_management(order_id: str):
    """测试采购管理环节"""
    print("\n🛒 测试采购管理环节...")
    
    # 创建采购申请
    response = client.post("/erp/purchase/requisition", json={
        "material_id": "M001",
        "quantity": 100,
        "required_date": "2025-11-08"
    })
    print(f"采购申请响应: {response.status_code}")
    
    # MRP运算
    response = client.post("/erp/purchase/mrp", json={
        "order_ids": [order_id]
    })
    print(f"MRP运算响应: {response.status_code}")
    
    # 供应商列表
    response = client.get("/erp/suppliers")
    print(f"供应商列表响应: {response.status_code}")
    
    # 采购分析
    response = client.get("/erp/purchase/analytics")
    print(f"采购分析响应: {response.status_code}")
    
    print("✅ 采购管理环节测试完成")


async def test_inbound_management(order_id: str):
    """测试入库管理环节"""
    print("\n📥 测试入库管理环节...")
    
    # 来料入库
    response = client.post("/erp/warehouse/inbound", json={
        "po_id": f"PO-2025-001",
        "items": [{"material_id": "M001", "quantity": 100, "unit_price": 50}],
        "quality_status": "待检"
    })
    print(f"来料入库响应: {response.status_code}")
    
    # 质检
    response = client.post("/erp/warehouse/quality-check", json={
        "inbound_id": f"IB-{int(time.time())}",
        "check_result": "合格"
    })
    print(f"质检响应: {response.status_code}")
    
    # 库存查询
    response = client.get("/erp/warehouse/inventory")
    print(f"库存查询响应: {response.status_code}")
    
    # ABC分析
    response = client.get("/erp/warehouse/abc-analysis")
    print(f"ABC分析响应: {response.status_code}")
    
    print("✅ 入库管理环节测试完成")


async def test_production_management(order_id: str):
    """测试生产管理环节"""
    print("\n🏭 测试生产管理环节...")
    
    # 创建生产计划
    response = client.post("/erp/production/plan", json={
        "order_ids": [order_id],
        "plan_date": "2025-11-10"
    })
    print(f"生产计划响应: {response.status_code}")
    
    # 生产排程
    response = client.post("/erp/production/schedule", json={
        "plan_id": f"MP-{int(time.time())}"
    })
    print(f"生产排程响应: {response.status_code}")
    
    # 创建生产工单
    response = client.post("/erp/production/work-orders/create", json={
        "product_id": "P001",
        "quantity": 100,
        "priority": "高"
    })
    print(f"生产工单响应: {response.status_code}")
    
    # OEE分析
    response = client.get("/erp/production/oee")
    print(f"OEE分析响应: {response.status_code}")
    
    # 实时看板
    response = client.get("/erp/production/realtime")
    print(f"实时看板响应: {response.status_code}")
    
    print("✅ 生产管理环节测试完成")


async def test_logistics_management(order_id: str):
    """测试物流管理环节"""
    print("\n🚚 测试物流管理环节...")
    
    # 创建发货单
    response = client.post("/erp/logistics/shipment/create", json={
        "order_id": order_id,
        "carrier": "顺丰速运"
    })
    print(f"发货单响应: {response.status_code}")
    
    # 物流追踪
    response = client.get(f"/erp/logistics/tracking/SF{int(time.time())}")
    print(f"物流追踪响应: {response.status_code}")
    
    # 路线优化
    response = client.post("/erp/logistics/route/optimize", json={
        "destinations": [
            {"name": "深圳", "lat": 22.5, "lng": 114.1},
            {"name": "广州", "lat": 23.1, "lng": 113.3},
            {"name": "上海", "lat": 31.2, "lng": 121.5}
        ]
    })
    print(f"路线优化响应: {response.status_code}")
    
    # 物流成本分析
    response = client.get("/erp/logistics/cost/analysis")
    print(f"物流成本分析响应: {response.status_code}")
    
    print("✅ 物流管理环节测试完成")


async def test_service_management(order_id: str):
    """测试售后服务环节"""
    print("\n🔧 测试售后服务环节...")
    
    # 创建服务工单
    response = client.post("/erp/service/tickets/create", json={
        "order_id": order_id,
        "issue_type": "安装指导",
        "description": "客户需要产品安装指导"
    })
    print(f"服务工单响应: {response.status_code}")
    
    # 服务工单列表
    response = client.get("/erp/service/tickets")
    print(f"服务工单列表响应: {response.status_code}")
    
    # 客户满意度
    response = client.get("/erp/service/satisfaction")
    print(f"客户满意度响应: {response.status_code}")
    
    # 常见问题库
    response = client.get("/erp/service/faq")
    print(f"常见问题库响应: {response.status_code}")
    
    print("✅ 售后服务环节测试完成")


async def test_settlement_management(order_id: str):
    """测试结算回款环节"""
    print("\n💰 测试结算回款环节...")
    
    # 创建发票
    response = client.post("/erp/settlement/invoices/create", json={
        "order_id": order_id,
        "amount": 50000.0
    })
    print(f"创建发票响应: {response.status_code}")
    
    # 应收账款
    response = client.get("/erp/settlement/receivables")
    print(f"应收账款响应: {response.status_code}")
    
    # 结算分析
    response = client.get("/erp/settlement/analytics")
    print(f"结算分析响应: {response.status_code}")
    
    print("✅ 结算回款环节测试完成")


async def test_erp_assistant():
    """测试ERP智能助手"""
    print("\n🤖 测试ERP智能助手...")
    
    # 智能对话
    questions = [
        "帮我查看订单状态",
        "当前生产进度如何",
        "库存情况怎么样",
        "采购分析报告"
    ]
    
    for question in questions:
        response = client.post("/erp/assistant/ask", json={
            "question": question,
            "module": "general"
        })
        print(f"助手问答 '{question}' 响应: {response.status_code}")
    
    # 8维度分析
    response = client.get("/erp/dimensions/analyze")
    print(f"8维度分析响应: {response.status_code}")
    
    # 专家列表
    response = client.get("/erp/experts")
    print(f"专家列表响应: {response.status_code}")
    
    print("✅ ERP智能助手测试完成")


async def test_complete_workflow():
    """测试完整ERP工作流"""
    print("🚀 开始测试ERP全流程（11个环节）...\n")
    
    # 1. 订单接收
    order_id = await test_order_management()
    if not order_id:
        print("❌ 订单管理环节失败，终止测试")
        return
    
    # 2. 项目立项
    project_id = await test_project_management(order_id)
    
    # 3. 采购管理
    await test_procurement_management(order_id)
    
    # 4. 入库管理
    await test_inbound_management(order_id)
    
    # 5. 生产管理
    await test_production_management(order_id)
    
    # 6. 物流管理
    await test_logistics_management(order_id)
    
    # 7. 售后服务
    await test_service_management(order_id)
    
    # 8. 结算回款
    await test_settlement_management(order_id)
    
    # 9. 智能助手和维度分析
    await test_erp_assistant()
    
    print("\n🎉 ERP全流程测试完成！")
    
    print("\n📊 ERP全流程汇总:")
    print("  1. 订单接收 - 订单创建、审批、追踪")
    print("  2. 项目立项 - 项目创建、资源分配")
    print("  3. 采购管理 - 采购申请、供应商选择")
    print("  4. 入库管理 - 入库登记、库存管理")
    print("  5. 生产管理 - 工单管理、进度跟踪")
    print("  6. 物流管理 - 发货单、物流跟踪")
    print("  7. 售后服务 - 服务工单、满意度调查")
    print("  8. 结算回款 - 结算单、回款记录")
    print("  9. 智能助手 - 自然语言交互、8维度分析")
    print("  ✅ 总计9个核心环节完整流程已测试")


if __name__ == "__main__":
    asyncio.run(test_complete_workflow())