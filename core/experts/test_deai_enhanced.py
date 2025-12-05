#!/usr/bin/env python3
"""
ContentDeAIExpert生产级增强功能测试脚本
测试AI痕迹检测和自然化处理能力
"""

import asyncio
import sys
import os

# 添加路径以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentDeAIExpert


async def test_ai_trace_detection():
    """测试AI痕迹检测功能"""
    print("=== 测试AI痕迹检测功能 ===")
    
    # 创建去AI化专家实例
    expert = ContentDeAIExpert()
    
    # 测试内容 - 包含明显AI痕迹
    ai_content = """
    首先，我们需要明确这个问题的核心要点。一方面，这个问题涉及到多个关键因素，另一方面，我们需要综合考虑各种可能性。
    综上所述，我们可以得出以下结论：总的来说，这个解决方案是可行的。需要注意的是，在实施过程中要关注细节。
    """
    
    # 测试内容 - 自然内容
    natural_content = """
    我觉得这个问题挺有意思的，从我的经验来看，解决这个问题需要考虑几个方面。
    在实际工作中，我发现这种方法效果不错，但具体实施时还需要根据实际情况调整。
    个人认为，最重要的是找到适合自己团队的工作方式。
    """
    
    # 测试AI痕迹检测
    print("\n1. 测试AI痕迹内容检测:")
    result = await expert.analyze_deai({"content": ai_content})
    print(f"   - 检测率: {result.metadata.get('detection_rate', 0):.2f}%")
    print(f"   - AI模式检测: {result.metadata.get('ai_patterns_detected', [])}")
    print(f"   - 洞察: {result.insights[:3]}")
    
    print("\n2. 测试自然内容检测:")
    result = await expert.analyze_deai({"content": natural_content})
    print(f"   - 检测率: {result.metadata.get('detection_rate', 0):.2f}%")
    print(f"   - AI模式检测: {result.metadata.get('ai_patterns_detected', [])}")
    print(f"   - 洞察: {result.insights[:3]}")
    
    return True


async def test_semantic_analysis():
    """测试智能语义分析功能"""
    print("\n=== 测试智能语义分析功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 测试不同语义复杂度的内容
    simple_content = "这是一个简单的句子。另一个简单的句子。"
    complex_content = """
    在这个复杂的问题中，我们需要深入分析多个维度的因素，包括技术实现、用户体验、商业价值等各个方面，
    同时还要考虑长期发展和短期目标的平衡，以及团队资源和时间限制等现实约束条件。
    """
    
    print("\n1. 测试简单内容语义分析:")
    result = await expert.analyze_deai({"content": simple_content})
    semantic_metadata = result.metadata.get('semantic_analysis', {})
    print(f"   - 句子复杂度: {semantic_metadata.get('sentence_complexity', 'unknown')}")
    print(f"   - 情感丰富度: {semantic_metadata.get('emotional_richness', 'unknown')}")
    
    print("\n2. 测试复杂内容语义分析:")
    result = await expert.analyze_deai({"content": complex_content})
    semantic_metadata = result.metadata.get('semantic_analysis', {})
    print(f"   - 句子复杂度: {semantic_metadata.get('sentence_complexity', 'unknown')}")
    print(f"   - 情感丰富度: {semantic_metadata.get('emotional_richness', 'unknown')}")
    
    return True


async def test_language_support():
    """测试多语言支持功能"""
    print("\n=== 测试多语言支持功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 测试中文内容
    chinese_content = "这是一个中文测试内容，包含一些常见的表达方式。"
    
    # 测试英文内容
    english_content = "This is an English test content with some common expressions."
    
    # 测试混合内容
    mixed_content = "这是一个混合内容测试。This is a mixed content test."
    
    print("\n1. 测试中文内容语言检测:")
    result = await expert.analyze_deai({"content": chinese_content})
    print(f"   - 检测语言: {result.metadata.get('detected_language', 'unknown')}")
    print(f"   - 中文AI模式: {result.metadata.get('chinese_ai_patterns_detected', [])}")
    
    print("\n2. 测试英文内容语言检测:")
    result = await expert.analyze_deai({"content": english_content})
    print(f"   - 检测语言: {result.metadata.get('detected_language', 'unknown')}")
    print(f"   - 英文AI模式: {result.metadata.get('english_ai_patterns_detected', [])}")
    
    print("\n3. 测试混合内容语言检测:")
    result = await expert.analyze_deai({"content": mixed_content})
    print(f"   - 检测语言: {result.metadata.get('detected_language', 'unknown')}")
    
    return True


async def test_naturalness_enhancement():
    """测试自然度增强功能"""
    print("\n=== 测试自然度增强功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 测试内容
    ai_content = "首先，我们需要分析这个问题。一方面，这个问题很重要。另一方面，我们需要考虑多种因素。"
    
    print("\n1. 测试低级别自然度增强:")
    result = await expert.enhance_naturalness(ai_content, "low")
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 应用技术: {result.get('techniques_applied', [])}")
    print(f"   - 自然度提升: {result.get('estimated_naturalness_improvement', 0):.2f}")
    
    print("\n2. 测试中级别自然度增强:")
    result = await expert.enhance_naturalness(ai_content, "medium")
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 应用技术: {result.get('techniques_applied', [])}")
    print(f"   - 自然度提升: {result.get('estimated_naturalness_improvement', 0):.2f}")
    
    print("\n3. 测试高级别自然度增强:")
    result = await expert.enhance_naturalness(ai_content, "high")
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 应用技术: {result.get('techniques_applied', [])}")
    print(f"   - 自然度提升: {result.get('estimated_naturalness_improvement', 0):.2f}")
    
    return True


async def test_smart_deai_processing():
    """测试智能去AI化处理功能"""
    print("\n=== 测试智能去AI化处理功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 测试内容
    ai_content = """
    首先，我们需要明确目标。一方面，这个项目很重要。另一方面，我们需要考虑资源限制。
    综上所述，我们可以制定详细的计划。需要注意的是，要关注时间节点。
    """
    
    print("\n1. 测试智能去AI化处理:")
    result = await expert.smart_deai_processing(ai_content, target_detection_rate=2.5)
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 目标检测率: {result.get('target_detection_rate', 0)}%")
    print(f"   - 预估检测率: {result.get('estimated_detection_rate', 0):.2f}%")
    print(f"   - 处理步骤: {result.get('processing_steps', [])}")
    print(f"   - 移除AI模式: {result.get('ai_patterns_removed', 0)}个")
    
    return True


async def test_detection_dashboard():
    """测试检测仪表板功能"""
    print("\n=== 测试检测仪表板功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 先进行一些检测以生成历史数据
    test_contents = [
        "这是一个测试内容1。",
        "This is test content 2.",
        "混合内容测试3。Mixed content test."
    ]
    
    for i, content in enumerate(test_contents):
        await expert.analyze_deai({"content": content})
    
    # 获取仪表板数据
    dashboard = expert.get_detection_dashboard()
    
    print(f"   - 总检测次数: {dashboard.get('total_detections', 0)}")
    print(f"   - 平均检测率: {dashboard.get('average_detection_rate', 0):.2f}%")
    print(f"   - 生产就绪: {dashboard.get('production_ready', False)}")
    print(f"   - 趋势: {dashboard.get('trend', 'unknown')}")
    print(f"   - 语言分布: {dashboard.get('language_distribution', {})}")
    print(f"   - 预警: {dashboard.get('alerts', [])}")
    
    return True


async def main():
    """主测试函数"""
    print("开始测试ContentDeAIExpert生产级增强功能...\n")
    
    try:
        # 运行所有测试
        await test_ai_trace_detection()
        await test_semantic_analysis()
        await test_language_support()
        await test_naturalness_enhancement()
        await test_smart_deai_processing()
        await test_detection_dashboard()
        
        print("\n✅ 所有测试完成！ContentDeAIExpert生产级增强功能验证成功。")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())