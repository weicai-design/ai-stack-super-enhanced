#!/usr/bin/env python3
"""调试相似度分析逻辑"""

import asyncio
import sys
import os

# 添加路径以导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from content_experts import ContentCopyrightExpert

async def debug_similarity_analysis():
    """调试相似度分析"""
    expert = ContentCopyrightExpert()
    
    # 测试85%相似度
    test_data = {
        "originality": 80,
        "similarity": {"max": 85, "avg": 50},
        "risk_level": "medium"
    }
    
    result = await expert.analyze_copyright(test_data)
    
    print("=== 相似度85%分析结果 ===")
    print(f"分数: {result.score}")
    print(f"置信度: {result.confidence}")
    print("\n洞察:")
    for insight in result.insights:
        print(f"  - {insight}")
    print("\n建议:")
    for rec in result.recommendations:
        print(f"  - {rec}")
    print("\n元数据:")
    for key, value in result.metadata.items():
        print(f"  - {key}: {value}")
    
    # 检查相似度相关洞察
    similarity_insights = [insight for insight in result.insights if "相似度" in insight]
    print(f"\n相似度相关洞察数量: {len(similarity_insights)}")
    for insight in similarity_insights:
        print(f"  - {insight}")

if __name__ == "__main__":
    asyncio.run(debug_similarity_analysis())