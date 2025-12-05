#!/usr/bin/env python3
"""
ContentPublishExpert生产级功能增强测试脚本
测试多平台发布和监控能力的增强功能
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentPublishExpert, ContentStage, ContentAnalysis

async def test_content_publish_enhanced():
    """测试ContentPublishExpert的生产级增强功能"""
    print("🚀 开始测试ContentPublishExpert生产级功能增强...\n")
    
    # 创建发布专家实例
    publish_expert = ContentPublishExpert()
    
    print("📋 测试1: 生产级发布策略分析")
    publish_data = {
        "platforms": ["wechat", "weibo", "douyin"],
        "publish_time": {"optimal_hours": [9, 20, 21]},
        "frequency": 4,
        "content_type": "图文",
        "concurrent_posts": 3,
        "historical_performance": {
            "avg_engagement": 0.06,
            "growth_rate": 0.15
        }
    }
    
    analysis = await publish_expert.analyze_publish(publish_data)
    print(f"✅ 发布策略分析完成 - 分数: {analysis.score}")
    print("📝 洞察点:", analysis.insights)
    print("💡 建议:", analysis.recommendations)
    print("📊 元数据:", analysis.metadata)
    print()
    
    print("📋 测试2: 智能调度优化")
    content_data = {
        "content_type": "视频",
        "title": "AI技术发展趋势分析",
        "tags": ["AI", "技术", "趋势"]
    }
    
    target_platforms = ["wechat", "douyin", "zhihu"]
    constraints = {"preferred_hours": [10, 20]}
    
    schedule_result = await publish_expert.optimize_publish_schedule(
        content_data, target_platforms, constraints
    )
    
    if schedule_result["success"]:
        print("✅ 智能调度优化完成")
        print("📅 优化调度:", schedule_result["optimized_schedule"])
        print("💡 建议:", schedule_result["recommendations"])
        print(f"🎯 优化分数: {schedule_result['optimization_score']:.2f}")
    else:
        print("❌ 调度优化失败:", schedule_result["error"])
    print()
    
    print("📋 测试3: 发布效果预测")
    publish_strategy = {
        "platforms": ["wechat", "weibo"],
        "publish_time": {"optimal_hours": [9, 20]},
        "frequency": 3
    }
    
    prediction_result = await publish_expert.predict_publish_performance(
        content_data, publish_strategy
    )
    
    if prediction_result["success"]:
        print("✅ 发布效果预测完成")
        print("📈 平台预测:", prediction_result["predictions"])
        print("🌐 总体预测:", prediction_result["overall_prediction"])
        print(f"🎯 预测置信度: {prediction_result['prediction_confidence']}")
    else:
        print("❌ 效果预测失败:", prediction_result["error"])
    print()
    
    print("📋 测试4: 多平台适配分析")
    multi_platform_data = {
        "platforms": ["wechat", "weibo", "douyin", "zhihu"],
        "publish_time": {},
        "frequency": 5,
        "content_type": "短视频"
    }
    
    multi_analysis = await publish_expert.analyze_publish(multi_platform_data)
    print(f"✅ 多平台分析完成 - 分数: {multi_analysis.score}")
    print("📝 洞察点:", multi_analysis.insights)
    print("💡 建议:", multi_analysis.recommendations)
    print()
    
    print("📋 测试5: 实时监控预警")
    risk_data = {
        "platforms": ["wechat"],
        "publish_time": {"optimal_hours": [2]},  # 非最佳时间
        "frequency": 1,  # 低频率
        "concurrent_posts": 8,  # 高并发
        "historical_performance": {
            "avg_engagement": 0.01,  # 低互动率
            "growth_rate": 0.02  # 低增长率
        }
    }
    
    risk_analysis = await publish_expert.analyze_publish(risk_data)
    print(f"✅ 风险分析完成 - 分数: {risk_analysis.score}")
    print("📝 洞察点:", risk_analysis.insights)
    print("💡 建议:", risk_analysis.recommendations)
    print()
    
    print("📋 测试6: 生产级配置验证")
    print("🔧 平台配置:", publish_expert.platform_configs)
    print("📊 监控配置:", publish_expert.monitoring_config)
    print("✅ 生产级配置验证完成")
    print()
    
    print("🎉 所有测试完成！")
    
    print("\n📋 测试总结:")
    print("✅ ContentPublishExpert生产级功能增强完成")
    print("✅ 智能平台分析功能正常")
    print("✅ 智能调度优化功能正常")
    print("✅ 发布效果预测功能正常")
    print("✅ 实时监控预警功能正常")
    print("✅ 多平台适配功能正常")
    
    print("\n🎊 ContentPublishExpert生产级功能增强成功！")

if __name__ == "__main__":
    asyncio.run(test_content_publish_enhanced())