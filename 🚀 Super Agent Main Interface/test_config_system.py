#!/usr/bin/env python3
"""
测试RAG专家配置系统
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.experts.rag_config import get_rag_config, get_expert_config
from core.rag_expert_system import get_rag_expert_system

def test_config_system():
    """测试配置系统"""
    print("=== 测试RAG专家配置系统 ===")
    
    # 测试获取系统配置
    print("\n1. 测试系统配置获取:")
    try:
        system_config = get_rag_config()
        print(f"✓ 系统配置加载成功")
        print(f"   - 最大并发请求: {system_config.max_concurrent_requests}")
        print(f"   - 请求超时: {system_config.request_timeout}")
        print(f"   - 监控启用: {system_config.monitoring_enabled}")
    except Exception as e:
        print(f"✗ 系统配置加载失败: {e}")
        return False
    
    # 测试获取专家配置
    print("\n2. 测试专家配置获取:")
    expert_ids = ["rag_knowledge_expert", "rag_retrieval_expert", "rag_graph_expert"]
    
    for expert_id in expert_ids:
        try:
            expert_config = get_expert_config(expert_id)
            print(f"✓ {expert_id} 配置加载成功")
            print(f"   - 质量阈值: {expert_config.quality_threshold}")
            print(f"   - 高质阈值: {expert_config.high_quality_threshold}")
            print(f"   - 日志级别: {expert_config.log_level}")
        except Exception as e:
            print(f"✗ {expert_id} 配置加载失败: {e}")
            return False
    
    # 测试RAG专家系统初始化
    print("\n3. 测试RAG专家系统初始化:")
    try:
        rag_system = get_rag_expert_system()
        print("✓ RAG专家系统初始化成功")
        print(f"   - 配置系统: {rag_system.config}")
        print(f"   - 知识专家: {rag_system.experts}")
    except Exception as e:
        print(f"✗ RAG专家系统初始化失败: {e}")
        return False
    
    print("\n=== 所有测试通过 ===")
    return True

if __name__ == "__main__":
    # 设置日志级别
    logging.basicConfig(level=logging.INFO)
    
    success = test_config_system()
    sys.exit(0 if success else 1)