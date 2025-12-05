#!/usr/bin/env python3
"""
测试pytest环境中的路径问题
"""

import sys
import os

def test_pytest_paths():
    print("=== pytest环境路径调试 ===")
    print("当前工作目录:", os.getcwd())
    print("Python路径:")
    for i, path in enumerate(sys.path):
        print(f"  {i}: {path}")
    
    # 检查关键模块是否可导入
    print("\n=== 检查模块导入 ===")
    try:
        import core.experts
        print("✓ core.experts模块导入成功")
        print("  core.experts路径:", core.experts.__file__)
    except Exception as e:
        print("✗ core.experts模块导入失败:", e)
    
    try:
        from core.experts import get_rag_experts
        print("✓ get_rag_experts函数导入成功")
        
        # 测试函数调用
        experts = get_rag_experts()
        print(f"专家数量: {len(experts)}")
        print(f"专家键名: {list(experts.keys())}")
        
        for key, expert in experts.items():
            print(f"  - {key}: {type(expert).__name__}")
    except Exception as e:
        print("✗ get_rag_experts函数调用失败:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pytest_paths()