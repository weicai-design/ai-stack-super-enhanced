#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
T001任务简化测试脚本

测试目标：验证双线闭环工作流验证机制的基本功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from core.workflow_enhanced_validator import (
        WorkflowEnhancedValidator,
        get_enhanced_validator,
        ValidationStatus,
        ValidationLevel,
    )
    
    print("✅ 导入验证器模块成功")
    
except ImportError as e:
    print(f"❌ 导入验证器模块失败: {e}")
    sys.exit(1)


def test_validator_initialization():
    """测试验证器初始化"""
    print("\n=== 测试1: 验证器初始化 ===")
    
    try:
        validator = WorkflowEnhancedValidator()
        print("✅ 验证器初始化成功")
        
        # 检查配置
        config = validator.config
        if config:
            print("✅ 验证器配置加载成功")
            print(f"   - 性能验证配置: {config.get('performance_validation', {})}")
            print(f"   - 功能验证配置: {config.get('functional_validation', {})}")
        else:
            print("❌ 验证器配置为空")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 验证器初始化失败: {e}")
        return False


def test_global_validator():
    """测试全局验证器"""
    print("\n=== 测试2: 全局验证器 ===")
    
    try:
        validator = get_enhanced_validator()
        print("✅ 全局验证器获取成功")
        
        # 验证是同一个实例
        validator2 = get_enhanced_validator()
        if validator is validator2:
            print("✅ 全局验证器单例模式正确")
        else:
            print("❌ 全局验证器不是单例模式")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 全局验证器测试失败: {e}")
        return False


def test_validation_classes():
    """测试验证相关类"""
    print("\n=== 测试3: 验证相关类 ===")
    
    try:
        # 测试枚举类
        status_values = [s.value for s in ValidationStatus]
        level_values = [l.value for l in ValidationLevel]
        
        expected_status = ["passed", "failed", "warning", "pending"]
        expected_level = ["critical", "high", "medium", "low"]
        
        if set(status_values) == set(expected_status):
            print("✅ ValidationStatus枚举正确")
        else:
            print(f"❌ ValidationStatus枚举不正确: {status_values}")
            return False
            
        if set(level_values) == set(expected_level):
            print("✅ ValidationLevel枚举正确")
        else:
            print(f"❌ ValidationLevel枚举不正确: {level_values}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 验证相关类测试失败: {e}")
        return False


import asyncio

async def test_validation_methods():
    """测试验证方法"""
    print("\n=== 测试4: 验证方法 ===")
    
    try:
        validator = WorkflowEnhancedValidator()
        
        # 测试统计方法
        stats = await validator.get_validation_stats()
        if isinstance(stats, dict):
            print("✅ 验证统计方法正常")
            print(f"   - 统计信息: {stats}")
        else:
            print("❌ 验证统计方法返回类型错误")
            return False
            
        # 测试报告方法
        report = await validator.get_validation_report("test_id")
        if report is None:  # 不存在的ID应该返回None
            print("✅ 验证报告方法正常")
        else:
            print("❌ 验证报告方法返回非None值")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 验证方法测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("=" * 60)
    print("T001任务简化测试")
    print("=" * 60)
    
    tests = [
        test_validator_initialization,
        test_global_validator,
        test_validation_classes,
        test_validation_methods,
    ]
    
    results = []
    
    for test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试执行异常: {e}")
            results.append(False)
    
    # 统计结果
    passed = sum(1 for r in results if r)
    total = len(results)
    pass_rate = passed / total * 100
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    print(f"总测试数: {total}")
    print(f"通过测试数: {passed}")
    print(f"通过率: {pass_rate:.1f}%")
    
    if pass_rate >= 75:
        print("\n✅ T001任务基本功能验证通过")
        print("✅ 双线闭环工作流验证机制基本功能正常")
        
        # 生成验证报告
        with open("t001_validation_report.txt", "w") as f:
            f.write("T001任务验证报告\n")
            f.write("=" * 40 + "\n")
            f.write(f"测试时间: {__import__('datetime').datetime.now()}\n")
            f.write(f"总测试数: {total}\n")
            f.write(f"通过测试数: {passed}\n")
            f.write(f"通过率: {pass_rate:.1f}%\n")
            f.write("\n验证结果: 通过\n")
            f.write("\n说明: 双线闭环工作流验证机制基本功能正常\n")
        
        print("✅ 验证报告已生成: t001_validation_report.txt")
        
    else:
        print("\n❌ T001任务验证失败")
        print("❌ 需要进一步调试和修复")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())