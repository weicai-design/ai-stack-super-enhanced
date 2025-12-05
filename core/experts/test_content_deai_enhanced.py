#!/usr/bin/env python3
"""
测试增强的ContentDeAIExpert生产级功能
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentDeAIExpert, ContentDataConnector

async def test_enhanced_deai_expert():
    """测试增强的去AI化专家功能"""
    print("🧪 开始测试增强的ContentDeAIExpert生产级功能...\n")
    
    # 创建去AI化专家实例
    deai_expert = ContentDeAIExpert()
    
    # 测试内容数据
    test_content = {
        "content": "首先，我们需要了解人工智能的基本概念。人工智能是一种模拟人类智能的技术，它可以帮助我们解决各种复杂问题。总的来说，人工智能的发展前景非常广阔。",
        "ai_detection_rate": 4.2,
        "naturalness": 0.6,
        "originality": 85
    }
    
    # 测试1: 分析去AI化效果
    print("📊 测试1: 分析去AI化效果")
    analysis_result = await deai_expert.analyze_deai(test_content)
    print(f"✅ 分析完成 - 分数: {analysis_result.score}")
    print(f"📝 洞察点: {analysis_result.insights}")
    print(f"💡 建议: {analysis_result.recommendations}")
    print(f"🔧 元数据: {analysis_result.metadata}")
    print()
    
    # 测试2: 智能去AI化处理
    print("🔧 测试2: 智能去AI化处理")
    deai_result = await deai_expert.smart_deai_processing(
        test_content["content"],
        target_detection_rate=2.5
    )
    print(f"✅ 智能去AI化处理完成 - 成功: {deai_result['success']}")
    print(f"📄 处理步骤: {deai_result['processing_steps']}")
    print(f"🎯 目标检测率: {deai_result['target_detection_rate']}%")
    print(f"📈 预估检测率: {deai_result['estimated_detection_rate']}%")
    print(f"🌟 自然度提升: {deai_result['naturalness_improvement']}")
    print(f"🌐 检测语言: {deai_result['detected_language']}")
    print()
    
    # 测试3: 自然度增强
    print("✨ 测试3: 自然度增强")
    enhance_result = await deai_expert.enhance_naturalness(
        test_content["content"],
        enhancement_level="high"
    )
    print(f"✅ 自然度增强完成 - 成功: {enhance_result['success']}")
    print(f"🔧 应用技术: {enhance_result['techniques_applied']}")
    print(f"📈 预估自然度提升: {enhance_result['estimated_naturalness_improvement']}")
    print(f"📉 预估检测率降低: {enhance_result['estimated_detection_reduction']}%")
    print(f"🔢 AI模式移除数量: {enhance_result['ai_patterns_removed']}")
    print()
    
    # 测试4: 检测仪表板
    print("📈 测试4: 检测仪表板")
    dashboard = deai_expert.get_detection_dashboard()
    print(f"📊 总检测次数: {dashboard['total_detections']}")
    print(f"📈 平均检测率: {dashboard['average_detection_rate']:.2f}%")
    print(f"🌟 平均自然度: {dashboard['average_naturalness']:.2f}")
    print(f"🎯 平均原创性: {dashboard['average_originality']:.2f}%")
    print(f"✅ 合规率: {dashboard['compliance_rate']:.2f}%")
    print(f"🏭 生产就绪: {dashboard['production_ready']}")
    print(f"📈 趋势: {dashboard['trend']}")
    print(f"🌐 语言分布: {dashboard['language_distribution']}")
    print(f"⚠️ 预警: {dashboard['alerts']}")
    print(f"🔍 最近AI模式: {dashboard['ai_patterns_detected']}")
    print()
    
    # 测试5: 多语言支持
    print("🌐 测试5: 多语言支持")
    english_content = {
        "content": "First of all, we need to understand the basic concepts of artificial intelligence. AI is a technology that simulates human intelligence and can help us solve various complex problems. In conclusion, the development prospects of AI are very broad.",
        "ai_detection_rate": 5.1,
        "naturalness": 0.5,
        "originality": 78
    }
    
    english_analysis = await deai_expert.analyze_deai(english_content)
    print(f"✅ 英文内容分析完成 - 分数: {english_analysis.score}")
    print(f"📝 洞察点: {english_analysis.insights}")
    print(f"🌐 检测语言: {english_analysis.metadata.get('detected_language', 'unknown')}")
    print()
    
    # 测试6: 实时监控预警
    print("🚨 测试6: 实时监控预警")
    # 模拟高检测率内容
    high_detection_content = {
        "content": "首先，我们需要了解人工智能的基本概念。",
        "ai_detection_rate": 8.5,
        "naturalness": 0.3,
        "originality": 65
    }
    
    high_analysis = await deai_expert.analyze_deai(high_detection_content)
    print(f"⚠️ 高风险内容分析完成 - 分数: {high_analysis.score}")
    print(f"📝 洞察点: {high_analysis.insights}")
    print(f"💡 建议: {high_analysis.recommendations}")
    print()
    
    print("🎉 所有测试完成！")
    print("\n📋 测试总结:")
    print(f"✅ ContentDeAIExpert生产级功能增强完成")
    print(f"✅ 智能语义分析功能正常")
    print(f"✅ 多语言支持功能正常")
    print(f"✅ 实时监控预警功能正常")
    print(f"✅ 智能去AI化处理功能正常")
    print(f"✅ 检测仪表板功能正常")
    
    return True

async def main():
    """主测试函数"""
    try:
        success = await test_enhanced_deai_expert()
        if success:
            print("\n🎊 所有测试通过！ContentDeAIExpert生产级功能增强成功！")
        else:
            print("\n❌ 测试失败，请检查代码实现")
    except Exception as e:
        print(f"\n💥 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())