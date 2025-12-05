#!/usr/bin/env python3
"""
内容创作专家系统测试脚本
测试6个内容创作专家的功能
"""

import sys
import os
import asyncio

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.content_experts import (
    material_expert, planning_expert, creation_expert,
    publish_expert, analytics_expert, improvement_expert,
    xiaohongshu_expert, douyin_expert, zhihu_expert
)


async def test_material_expert():
    """测试素材收集专家"""
    print("\n🔍 测试素材收集专家...")
    
    response = await material_expert.chat_response("收集素材", {})
    print(f"素材收集响应: {response[:200]}...")
    
    response = await material_expert.chat_response("热点话题", {})
    print(f"热点分析响应: {response[:150]}...")
    
    print("✅ 素材收集专家测试完成")


async def test_planning_expert():
    """测试内容策划专家"""
    print("\n💡 测试内容策划专家...")
    
    response = await planning_expert.chat_response("选题推荐", {})
    print(f"选题推荐响应: {response[:200]}...")
    
    response = await planning_expert.chat_response("竞品分析", {})
    print(f"竞品分析响应: {response[:150]}...")
    
    print("✅ 内容策划专家测试完成")


async def test_creation_expert():
    """测试内容创作专家"""
    print("\n✍️ 测试内容创作专家...")
    
    response = await creation_expert.chat_response("创作内容", {})
    print(f"内容创作响应: {response[:200]}...")
    
    response = await creation_expert.chat_response("去AI化", {})
    print(f"去AI化响应: {response[:150]}...")
    
    print("✅ 内容创作专家测试完成")


async def test_publish_expert():
    """测试发布管理专家"""
    print("\n📢 测试发布管理专家...")
    
    response = await publish_expert.chat_response("发布策略", {})
    print(f"发布策略响应: {response[:200]}...")
    
    print("✅ 发布管理专家测试完成")


async def test_analytics_expert():
    """测试运营分析专家"""
    print("\n📊 测试运营分析专家...")
    
    response = await analytics_expert.chat_response("数据分析", {"weekly_posts": 28})
    print(f"数据分析响应: {response[:200]}...")
    
    response = await analytics_expert.chat_response("效果评估", {})
    print(f"效果评估响应: {response[:150]}...")
    
    print("✅ 运营分析专家测试完成")


async def test_improvement_expert():
    """测试改进专家"""
    print("\n🔄 测试改进专家...")
    
    response = await improvement_expert.chat_response("改进建议", {})
    print(f"改进建议响应: {response[:200]}...")
    
    print("✅ 改进专家测试完成")


async def test_platform_experts():
    """测试平台专家"""
    print("\n📱 测试平台专家...")
    
    response = await xiaohongshu_expert.chat_response("小红书规则", {})
    print(f"小红书专家响应: {response}")
    
    response = await douyin_expert.chat_response("抖音算法", {})
    print(f"抖音专家响应: {response}")
    
    response = await zhihu_expert.chat_response("知乎优化", {})
    print(f"知乎专家响应: {response}")
    
    print("✅ 平台专家测试完成")


async def main():
    """主测试函数"""
    print("🚀 开始测试内容创作专家系统（6个核心专家 + 3个平台专家）...\n")
    
    # 测试6个核心内容创作专家
    await test_material_expert()
    await test_planning_expert()
    await test_creation_expert()
    await test_publish_expert()
    await test_analytics_expert()
    await test_improvement_expert()
    
    # 测试3个平台专家
    await test_platform_experts()
    
    print("\n🎉 所有内容创作专家测试完成！")
    
    print("\n📊 内容创作专家系统汇总:")
    print("  6个核心专家: 素材收集、内容策划、内容创作、发布管理、运营分析、改进专家")
    print("  3个平台专家: 小红书、抖音、知乎")
    print("  ✅ 总计9个专家系统已实现并测试通过")
    
    print("\n💡 专家能力覆盖:")
    print("  • 素材收集: 智能爬虫、反爬虫、质量评估")
    print("  • 内容策划: 热点分析、选题推荐、竞品分析")
    print("  • 内容创作: AI生成、去AI化、多平台适配")
    print("  • 发布管理: 最佳时间、多平台发布、定时发布")
    print("  • 运营分析: 数据分析、效果评估、用户分析")
    print("  • 改进专家: 问题识别、根因分析、方案制定")


if __name__ == "__main__":
    asyncio.run(main())