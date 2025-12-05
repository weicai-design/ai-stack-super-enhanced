#!/usr/bin/env python3
"""
ContentOperationExpert生产级功能增强测试脚本
测试智能运营分析、趋势预测和策略优化功能
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentOperationExpert, ContentStage


async def test_enhanced_operation_analysis():
    """测试生产级运营分析功能"""
    print("\n📋 测试1: 生产级运营分析")
    
    expert = ContentOperationExpert()
    
    # 测试数据
    operation_data = {
        "views": 2500,
        "likes": 150,
        "shares": 80,
        "comments": 45,
        "conversions": 25,
        "avg_time_spent": 45.5,
        "growth_rate": 0.12,
        "avg_conversion_value": 89.99,
        "historical_data": [
            {"views": 2000, "engagement_rate": 0.08, "conversion_rate": 0.008},
            {"views": 2200, "engagement_rate": 0.09, "conversion_rate": 0.009}
        ]
    }
    
    result = await expert.analyze_operation(operation_data)
    
    print(f"✅ 分析完成 - 分数: {result.score}")
    print(f"📊 置信度: {result.confidence}")
    print(f"📝 洞察点: {result.insights[:3]}")
    print(f"💡 建议: {result.recommendations[:2]}")
    
    return result.score > 70


async def test_operation_trend_analysis():
    """测试智能运营趋势分析"""
    print("\n📋 测试2: 智能运营趋势分析")
    
    expert = ContentOperationExpert()
    
    # 历史数据
    historical_data = [
        {"views": 1500, "engagement_rate": 0.06, "conversion_rate": 0.006},
        {"views": 1800, "engagement_rate": 0.07, "conversion_rate": 0.007},
        {"views": 2200, "engagement_rate": 0.08, "conversion_rate": 0.008},
        {"views": 2500, "engagement_rate": 0.09, "conversion_rate": 0.009}
    ]
    
    result = await expert.analyze_operation_trend(historical_data, "14d")
    
    if result["success"]:
        trend_analysis = result["trend_analysis"]
        prediction = result["prediction"]
        
        print(f"✅ 趋势分析完成")
        print(f"📈 整体趋势: {trend_analysis.get('trend', '未知')}")
        print(f"📊 增长率: {trend_analysis.get('overall_growth_rate', 0):.1%}")
        print(f"🔮 未来预测: {prediction.get('prediction', '未知')}")
        print(f"💡 优化建议: {result['optimization_suggestions'][:2]}")
        
        return True
    else:
        print(f"❌ 趋势分析失败: {result.get('error', '未知错误')}")
        return False


async def test_operation_strategy_optimization():
    """测试智能运营策略优化"""
    print("\n📋 测试3: 智能运营策略优化")
    
    expert = ContentOperationExpert()
    
    # 当前表现数据
    current_performance = {
        "views": 2500,
        "engagement_rate": 0.09,
        "conversion_rate": 0.009,
        "growth_rate": 0.12
    }
    
    # 目标指标
    target_metrics = {
        "views": 5000,
        "engagement_rate": 0.12,
        "conversion_rate": 0.015,
        "growth_rate": 0.2
    }
    
    result = await expert.optimize_operation_strategy(current_performance, target_metrics)
    
    if result["success"]:
        gap_analysis = result["gap_analysis"]
        strategies = result["optimization_strategies"]
        
        print(f"✅ 策略优化完成")
        print(f"📊 差距分析: {gap_analysis.get('total_gaps', 0)}个指标需要优化")
        print(f"🎯 高优先级差距: {gap_analysis.get('high_priority_gaps', 0)}个")
        
        if strategies:
            print(f"💡 优化策略示例:")
            for i, strategy in enumerate(strategies[:2], 1):
                print(f"   {i}. {strategy['metric']}: {strategy['strategies'][0]}")
        
        return True
    else:
        print(f"❌ 策略优化失败: {result.get('error', '未知错误')}")
        return False


async def test_monitoring_alerts():
    """测试实时监控预警功能"""
    print("\n📋 测试4: 实时监控预警")
    
    expert = ContentOperationExpert()
    
    # 低性能数据（应触发警报）
    low_performance_data = {
        "views": 50,
        "engagement_rate": 0.01,
        "conversion_rate": 0.002,
        "historical_data": [
            {"engagement_rate": 0.08},
            {"engagement_rate": 0.07}
        ]
    }
    
    result = await expert.analyze_operation(low_performance_data)
    
    # 检查是否包含警报信息
    has_alerts = any("⚠️" in insight for insight in result.insights)
    
    print(f"✅ 监控分析完成 - 分数: {result.score}")
    print(f"🔔 警报数量: {sum(1 for insight in result.insights if '⚠️' in insight)}")
    
    if has_alerts:
        alert_insights = [insight for insight in result.insights if "⚠️" in insight]
        print(f"📢 警报内容: {alert_insights[:2]}")
    
    return has_alerts


async def test_performance_analysis():
    """测试智能性能分析"""
    print("\n📋 测试5: 智能性能分析")
    
    expert = ContentOperationExpert()
    
    # 高性能数据
    high_performance_data = {
        "views": 8000,
        "avg_time_spent": 68.5,
        "growth_rate": 0.25
    }
    
    result = await expert._analyze_performance(high_performance_data)
    
    print(f"✅ 性能分析完成")
    print(f"📊 性能等级: {result['metadata'].get('performance_level', '未知')}")
    print(f"📈 增长率: {result['metadata'].get('growth_rate', 0):.1%}")
    print(f"💡 建议: {result['recommendations'][:1] if result['recommendations'] else '无'}")
    
    return result["metadata"].get("performance_level") == "优秀"


async def test_engagement_analysis():
    """测试智能互动分析"""
    print("\n📋 测试6: 智能互动分析")
    
    expert = ContentOperationExpert()
    
    # 高互动数据
    high_engagement_data = {
        "views": 3000,
        "likes": 300,
        "shares": 150,
        "comments": 120
    }
    
    result = await expert._analyze_engagement(high_engagement_data)
    
    print(f"✅ 互动分析完成")
    print(f"📊 互动等级: {result['metadata'].get('engagement_level', '未知')}")
    print(f"💬 互动率: {result['metadata'].get('engagement_rate', 0):.2%}")
    print(f"💡 建议: {result['recommendations'][:1] if result['recommendations'] else '无'}")
    
    return result["metadata"].get("engagement_level") == "优秀"


async def main():
    """主测试函数"""
    print("🚀 开始测试ContentOperationExpert生产级功能增强")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(await test_enhanced_operation_analysis())
    test_results.append(await test_operation_trend_analysis())
    test_results.append(await test_operation_strategy_optimization())
    test_results.append(await test_monitoring_alerts())
    test_results.append(await test_performance_analysis())
    test_results.append(await test_engagement_analysis())
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    
    print(f"\n📋 测试总结:")
    print(f"✅ 生产级运营分析: {'通过' if test_results[0] else '失败'}")
    print(f"✅ 智能趋势分析: {'通过' if test_results[1] else '失败'}")
    print(f"✅ 策略优化功能: {'通过' if test_results[2] else '失败'}")
    print(f"✅ 实时监控预警: {'通过' if test_results[3] else '失败'}")
    print(f"✅ 智能性能分析: {'通过' if test_results[4] else '失败'}")
    print(f"✅ 智能互动分析: {'通过' if test_results[5] else '失败'}")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"\n📊 测试通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("\n🎊 ContentOperationExpert生产级功能增强成功！")
        return True
    else:
        print("\n⚠️ 部分测试未通过，需要进一步优化")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)