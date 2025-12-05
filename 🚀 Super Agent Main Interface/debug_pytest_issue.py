#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试pytest测试问题
"""

import sys
import os

# 模拟pytest测试环境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def simulate_pytest_test():
    """模拟pytest测试"""
    print("=== 模拟pytest测试环境 ===")
    
    try:
        # 模拟测试文件中的导入
        from core.experts import get_rag_experts
        print("✓ 导入成功")
        
        # 调用函数
        experts = get_rag_experts()
        print(f"专家数量: {len(experts)}")
        print(f"专家键名: {list(experts.keys())}")
        
        # 检查专家实例
        for key, expert in experts.items():
            print(f"  - {key}: {type(expert).__name__}")
            
        return True
        
    except Exception as e:
        print(f"✗ 模拟测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_module_imports():
    """检查模块导入情况"""
    print("\n=== 检查模块导入情况 ===")
    
    try:
        # 检查core.experts模块
        import core.experts
        print("✓ core.experts模块导入成功")
        
        # 检查rag_experts模块
        import core.experts.rag_experts
        print("✓ core.experts.rag_experts模块导入成功")
        
        # 检查get_rag_experts函数
        if hasattr(core.experts, 'get_rag_experts'):
            print("✓ get_rag_experts函数在core.experts模块中")
        else:
            print("✗ get_rag_experts函数不在core.experts模块中")
            
        return True
        
    except Exception as e:
        print(f"✗ 模块检查失败: {e}")
        return False

def test_import_from_tests_dir():
    """从tests目录模拟导入"""
    print("\n=== 从tests目录模拟导入 ===")
    
    # 切换到tests目录的父目录
    original_cwd = os.getcwd()
    tests_dir = os.path.join(os.path.dirname(original_cwd), 'tests')
    
    try:
        # 模拟从tests目录运行
        os.chdir(os.path.dirname(original_cwd))
        
        # 重新配置Python路径
        sys.path.insert(0, os.getcwd())
        
        # 尝试导入
        from core.experts import get_rag_experts
        print("✓ 从tests目录导入成功")
        
        experts = get_rag_experts()
        print(f"专家数量: {len(experts)}")
        
        return True
        
    except Exception as e:
        print(f"✗ 从tests目录导入失败: {e}")
        return False
        
    finally:
        os.chdir(original_cwd)

if __name__ == "__main__":
    print("开始调试pytest测试问题...")
    print()
    
    # 测试1: 模拟pytest测试
    result1 = simulate_pytest_test()
    
    # 测试2: 检查模块导入
    result2 = check_module_imports()
    
    # 测试3: 从tests目录模拟导入
    result3 = test_import_from_tests_dir()
    
    print("\n=== 调试总结 ===")
    if result1 and result2 and result3:
        print("✓ 所有调试测试通过")
        print("问题可能在于pytest的测试运行方式或配置")
    else:
        print("✗ 部分调试测试失败")
        print("需要进一步检查导入路径和模块结构")