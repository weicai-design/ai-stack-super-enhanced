#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试趋势专家通用analyze方法
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.experts.trend_experts import (
    TrendCollectionExpert, 
    TrendProcessingExpert,
    TrendAnalysisExpert,
    TrendPredictionExpert,
    TrendReportExpert,
    TrendAlertExpert
)

async def test_analyze_methods():
    """测试所有趋势专家的通用analyze方法"""
    
    print("=== 测试趋势专家通用analyze方法 ===\n")
    
    # 创建测试数据
    test_data = {
        "trends": [
            {"id": 1, "name": "AI技术", "strength": 0.85},
            {"id": 2, "name": "区块链", "strength": 0.72}
        ],
        "data_count": 1000,
        "platforms": ["financial", "social_media"]
    }
    
    # 测试每个专家
    experts = [
        ("趋势采集专家", TrendCollectionExpert()),
        ("趋势处理专家", TrendProcessingExpert()),
        ("趋势分析专家", TrendAnalysisExpert()),
        ("趋势预测专家", TrendPredictionExpert()),
        ("趋势报告专家", TrendReportExpert()),
        ("趋势预警专家", TrendAlertExpert())
    ]
    
    for expert_name, expert in experts:
        print(f"\n--- 测试 {expert_name} ---")
        
        try:
            # 调用通用analyze方法
            result = await expert.analyze(test_data)
            
            print(f"✓ analyze方法调用成功")
            print(f"  阶段: {result.stage}")
            print(f"  置信度: {result.confidence}")
            print(f"  准确率: {result.accuracy}")
            print(f"  洞察数量: {len(result.insights)}")
            print(f"  建议数量: {len(result.recommendations)}")
            
        except Exception as e:
            print(f"✗ analyze方法调用失败: {e}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_analyze_methods())