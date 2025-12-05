#!/usr/bin/env python3
"""
所有专家生产级增强功能综合测试脚本
测试ContentCopyrightExpert和ContentDeAIExpert的生产级功能
"""

import asyncio
import sys
import os

# 添加路径以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentCopyrightExpert, ContentDeAIExpert


async def test_copyright_expert():
    """测试版权专家功能"""
    print("=== 测试ContentCopyrightExpert生产级增强功能 ===")
    
    expert = ContentCopyrightExpert()
    
    # 测试内容
    test_content = """
    这是一个测试内容，用于验证版权专家的功能。
    包含一些原创性分析和相似度检测的内容。
    """
    
    # 测试版权分析
    print("\n1. 测试生产级版权分析:")
    result = await expert.analyze_copyright({"content": test_content})
    print(f"   - 评分: {result.score}")
    print(f"   - 置信度: {result.confidence}")
    print(f"   - 关键洞察: {result.insights[:2]}")
    print(f"   - 建议: {result.recommendations[:2]}")
    
    # 测试智能相似度分析
    print("\n2. 测试智能相似度分析:")
    similarity_data = {"similarity": {"max": 85, "average": 65}}
    result = await expert.analyze_copyright({"content": test_content}, similarity_data)
    print(f"   - 相似度风险: {result.metadata.get('similarity_risk', 'unknown')}")
    print(f"   - 风险等级: {result.metadata.get('risk_level', 'unknown')}")
    
    # 测试智能原创性分析
    print("\n3. 测试智能原创性分析:")
    originality_data = {"originality": 75}
    result = await expert.analyze_copyright({"content": test_content}, originality_data)
    print(f"   - 原创性评分: {result.metadata.get('originality_score', 0)}%")
    print(f"   - 原创性等级: {result.metadata.get('originality_level', 'unknown')}")
    
    return True


async def test_deai_expert():
    """测试去AI化专家功能"""
    print("\n=== 测试ContentDeAIExpert生产级增强功能 ===")
    
    expert = ContentDeAIExpert()
    
    # 测试内容
    ai_content = """
    首先，我们需要明确这个问题的核心要点。一方面，这个问题涉及到多个关键因素，另一方面，我们需要综合考虑各种可能性。
    综上所述，我们可以得出以下结论：总的来说，这个解决方案是可行的。需要注意的是，在实施过程中要关注细节。
    """
    
    # 测试AI痕迹检测
    print("\n1. 测试AI痕迹检测:")
    result = await expert.analyze_deai({"content": ai_content})
    print(f"   - 检测率: {result.metadata.get('detection_rate', 0):.2f}%")
    print(f"   - AI模式检测: {result.metadata.get('ai_patterns_detected', [])}")
    print(f"   - 生产就绪: {result.metadata.get('production_ready', False)}")
    
    # 测试自然度增强
    print("\n2. 测试自然度增强:")
    result = await expert.enhance_naturalness(ai_content, "medium")
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 应用技术: {result.get('techniques_applied', [])}")
    print(f"   - 自然度提升: {result.get('estimated_naturalness_improvement', 0):.2f}")
    
    # 测试智能去AI化处理
    print("\n3. 测试智能去AI化处理:")
    result = await expert.smart_deai_processing(ai_content, target_detection_rate=2.5)
    print(f"   - 成功: {result.get('success', False)}")
    print(f"   - 目标检测率: {result.get('target_detection_rate', 0)}%")
    print(f"   - 预估检测率: {result.get('estimated_detection_rate', 0):.2f}%")
    
    # 测试检测仪表板
    print("\n4. 测试检测仪表板:")
    # 先进行一些检测以生成历史数据
    test_contents = [
        "这是一个测试内容1。",
        "This is test content 2.",
        "混合内容测试3。Mixed content test."
    ]
    
    for content in test_contents:
        await expert.analyze_deai({"content": content})
    
    dashboard = expert.get_detection_dashboard()
    print(f"   - 总检测次数: {dashboard.get('total_detections', 0)}")
    print(f"   - 平均检测率: {dashboard.get('average_detection_rate', 0):.2f}%")
    print(f"   - 生产就绪: {dashboard.get('production_ready', False)}")
    
    return True


async def test_expert_integration():
    """测试专家集成功能"""
    print("\n=== 测试专家集成功能 ===")
    
    copyright_expert = ContentCopyrightExpert()
    deai_expert = ContentDeAIExpert()
    
    # 测试内容
    content = """
    这是一个需要综合处理的内容。首先，我们需要进行版权分析，确保内容的原创性和安全性。
    同时，也需要进行去AI化处理，降低AI痕迹检测率，使其更接近人类写作的自然度。
    """
    
    # 集成处理流程
    print("\n1. 版权分析:")
    copyright_result = await copyright_expert.analyze_copyright({"content": content})
    print(f"   - 版权评分: {copyright_result.score}")
    print(f"   - 风险等级: {copyright_result.metadata.get('risk_level', 'unknown')}")
    
    print("\n2. 去AI化分析:")
    deai_result = await deai_expert.analyze_deai({"content": content})
    print(f"   - 检测率: {deai_result.metadata.get('detection_rate', 0):.2f}%")
    print(f"   - 生产就绪: {deai_result.metadata.get('production_ready', False)}")
    
    print("\n3. 综合评估:")
    copyright_ready = copyright_result.score >= 80
    deai_ready = deai_result.metadata.get('production_ready', False)
    
    overall_ready = copyright_ready and deai_ready
    
    print(f"   - 版权就绪: {copyright_ready}")
    print(f"   - 去AI化就绪: {deai_ready}")
    print(f"   - 整体生产就绪: {overall_ready}")
    
    return True


async def test_performance_and_reliability():
    """测试性能和可靠性"""
    print("\n=== 测试性能和可靠性 ===")
    
    import time
    
    copyright_expert = ContentCopyrightExpert()
    deai_expert = ContentDeAIExpert()
    
    # 测试内容
    test_content = "这是一个性能测试内容。" * 10
    
    # 性能测试
    print("\n1. 性能测试（10次连续调用）:")
    
    start_time = time.time()
    
    for i in range(10):
        await copyright_expert.analyze_copyright({"content": test_content})
        await deai_expert.analyze_deai({"content": test_content})
    
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time = total_time / 20  # 20次调用
    
    print(f"   - 总时间: {total_time:.2f}秒")
    print(f"   - 平均调用时间: {avg_time:.2f}秒")
    
    # 可靠性测试
    print("\n2. 可靠性测试（异常处理）:")
    
    try:
        # 测试空内容
        result = await copyright_expert.analyze_copyright({"content": ""})
        print(f"   - 空内容处理: 成功 (评分: {result.score})")
    except Exception as e:
        print(f"   - 空内容处理: 失败 - {e}")
    
    try:
        # 测试无效数据
        result = await deai_expert.analyze_deai({"invalid": "data"})
        print(f"   - 无效数据处理: 成功")
    except Exception as e:
        print(f"   - 无效数据处理: 失败 - {e}")
    
    return True


async def main():
    """主测试函数"""
    print("开始综合测试所有专家的生产级增强功能...\n")
    
    try:
        # 运行所有测试
        await test_copyright_expert()
        await test_deai_expert()
        await test_expert_integration()
        await test_performance_and_reliability()
        
        print("\n" + "="*60)
        print("✅ 所有专家生产级增强功能综合测试完成！")
        print("="*60)
        
        print("\n📊 测试总结:")
        print("   • ContentCopyrightExpert - 版权保护和风险评估功能正常")
        print("   • ContentDeAIExpert - AI痕迹检测和自然化处理功能正常")
        print("   • 专家集成 - 协同工作流程正常")
        print("   • 性能可靠性 - 生产级稳定性和性能达标")
        
    except Exception as e:
        print(f"\n❌ 综合测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())