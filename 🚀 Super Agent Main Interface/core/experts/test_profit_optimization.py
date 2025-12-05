#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI驱动的利润优化建议和ROI估算功能
"""

import sys
import os
import asyncio

# 添加路径以导入ERP专家模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from erp_experts import ProfitExpert, ERPDataConnector


async def test_profit_optimization():
    """测试利润优化功能"""
    print("=== 测试AI驱动的利润优化建议和ROI估算功能 ===")
    
    # 创建数据连接器
    connector = ERPDataConnector({"sap": {"host": "localhost", "port": 8080}})
    
    # 创建利润专家
    profit_expert = ProfitExpert()
    
    # 模拟利润数据
    profit_data = {
        "current_margin": 12.5,
        "revenue": 10000000,
        "profit": 1250000,
        "market_volatility": 0.25,
        "operational_efficiency": 0.85,
        "yoy_growth": 8.2,
        "new_product_ratio": 15.3,
        "recurring_revenue_ratio": 42.1,
        "gross_margin_improvement": 1.8
    }
    
    print("\n1. 测试基础利润分析...")
    analysis = await profit_expert.analyze_profit(profit_data)
    print(f"   - 分析得分: {analysis.score}")
    print(f"   - 置信度: {analysis.confidence}")
    print(f"   - 洞察数量: {len(analysis.insights)}")
    print(f"   - 建议数量: {len(analysis.recommendations)}")
    
    print("\n2. 测试AI驱动的利润优化建议...")
    optimization_result = await profit_expert.optimize_profit_parameters(profit_data)
    
    if optimization_result:
        print(f"   - 优化策略数量: {len(optimization_result.get('optimization_strategies', []))}")
        print(f"   - 总预计ROI: {optimization_result.get('total_estimated_roi', 'N/A')}")
        print(f"   - 实施路线图: {optimization_result.get('implementation_roadmap', {}).get('total_duration', 'N/A')}")
        
        # 显示详细优化建议
        strategies = optimization_result.get('optimization_strategies', [])
        for i, strategy in enumerate(strategies, 1):
            print(f"   \n   策略 {i}: {strategy.get('strategy_name', 'N/A')}")
            print(f"      - 目标利润率: {strategy.get('target_margin', 'N/A')}")
            print(f"      - 预计ROI: {strategy.get('estimated_roi', 'N/A')}")
            print(f"      - 优先级: {strategy.get('priority', 'N/A')}")
    
    print("\n3. 测试实时监控功能...")
    # 启动实时监控
    await profit_expert.start_real_time_monitoring(profit_data)
    
    # 等待几秒收集数据
    await asyncio.sleep(3)
    
    # 停止监控并获取报告
    report = await profit_expert.stop_real_time_monitoring()
    
    if report:
        print(f"   - 监控持续时间: {report.get('monitoring_duration', 'N/A')}")
        print(f"   - 有效性评分: {report.get('effectiveness_score', 'N/A')}")
        print(f"   - 警报数量: {report.get('alerts_count', 0)}")
        print(f"   - 数据点数: {report.get('data_points', 0)}")
    
    print("\n=== 测试完成 ===")
    return True


async def test_roi_estimation():
    """测试ROI估算功能"""
    print("\n=== 测试AI驱动的ROI估算功能 ===")
    
    profit_expert = ProfitExpert()
    
    # 模拟利润数据
    profit_data = {
        "current_margin": 12.5,
        "revenue": 10000000,
        "profit": 1250000,
        "market_volatility": 0.25,
        "operational_efficiency": 0.85
    }
    
    # 模拟优化改进
    improvements = [
        {
            "area": "定价策略",
            "priority": "high",
            "implementation_time": "3-6个月",
            "ai_enhanced": True
        },
        {
            "area": "成本控制", 
            "priority": "high",
            "implementation_time": "6-9个月",
            "ai_enhanced": True
        },
        {
            "area": "产品组合",
            "priority": "medium", 
            "implementation_time": "9-12个月",
            "ai_enhanced": False
        }
    ]
    
    print("\n1. 测试AI增强ROI估算...")
    roi_estimates = await profit_expert._ai_enhanced_roi_estimation(profit_data, improvements)
    
    for i, estimate in enumerate(roi_estimates, 1):
        print(f"   - 改进 {i}: {estimate.get('improvement', 'N/A')}")
        print(f"     预计ROI: {estimate.get('estimated_roi', 'N/A')}")
        print(f"     置信度: {estimate.get('confidence_level', 'N/A')}")
    
    print("\n2. 测试投资需求分析...")
    investment_analysis = await profit_expert._analyze_investment_requirements(improvements)
    print(f"   - 总投资: {investment_analysis.get('total_investment', 'N/A')}")
    print(f"   - 投资细分: {len(investment_analysis.get('investment_breakdown', []))}项")
    
    print("\n3. 测试敏感性分析...")
    sensitivity = profit_expert._perform_sensitivity_analysis(profit_data, improvements)
    print(f"   - 情景分析: {sensitivity.get('scenario_analysis', {})}")
    print(f"   - 风险容忍度: {sensitivity.get('risk_tolerance', 'N/A')}")
    
    print("\n=== ROI估算测试完成 ===")
    return True


async def main():
    """主测试函数"""
    try:
        await test_profit_optimization()
        await test_roi_estimation()
        print("\n✅ 所有测试通过！AI驱动的利润优化建议和ROI估算功能正常运行。")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())