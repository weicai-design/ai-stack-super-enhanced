#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试RAG专家测试问题
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_rag_experts():
    """测试get_rag_experts函数"""
    try:
        from core.experts import get_rag_experts
        print("✓ 成功导入get_rag_experts函数")
        
        # 调用函数
        experts = get_rag_experts()
        print(f"✓ 函数调用成功，返回专家数量: {len(experts)}")
        print(f"✓ 专家键名: {list(experts.keys())}")
        
        # 检查每个专家
        for key, expert in experts.items():
            print(f"  - {key}: {type(expert).__name__}")
            
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_path():
    """测试导入路径"""
    try:
        # 测试直接导入
        from core.experts.rag_experts import get_rag_experts
        print("✓ 直接导入成功")
        
        experts = get_rag_experts()
        print(f"✓ 直接导入调用成功，专家数量: {len(experts)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 直接导入失败: {e}")
        return False

if __name__ == "__main__":
    print("=== 调试RAG专家测试问题 ===")
    print()
    
    print("1. 测试通过core.experts导入:")
    result1 = test_get_rag_experts()
    print()
    
    print("2. 测试直接导入:")
    result2 = test_import_path()
    print()
    
    if result1 and result2:
        print("✓ 所有测试通过")
    else:
        print("✗ 部分测试失败")