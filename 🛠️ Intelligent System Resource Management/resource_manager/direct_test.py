"""
直接用户交互管理器测试脚本
在resource_manager目录中直接测试
"""

import sys
import os
import asyncio
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

print("开始用户交互管理器验证测试...")

# 导入本地模块
from user_interaction_manager import UserInteractionManager, InteractionType, UserInteraction

async def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试1: 基本功能 ===")
    
    try:
        # 创建管理器实例
        manager = UserInteractionManager({
            'max_interactions': 10,
            'default_timeout': 30
        })
        
        print("✓ 用户交互管理器创建成功")
        
        # 测试创建交互
        interaction = UserInteraction(
            interaction_id="test_001",
            interaction_type=InteractionType.CONFIRMATION,
            title="测试确认",
            message="这是一个测试确认对话框",
            options=["确认", "取消"],
            default_option="确认"
        )
        
        print("✓ 用户交互对象创建成功")
        
        # 测试转换为字典
        interaction_dict = interaction.to_dict()
        print(f"✓ 交互对象转换为字典成功: {list(interaction_dict.keys())}")
        
        # 测试过期检查
        is_expired = interaction.is_expired()
        print(f"✓ 过期检查成功: {is_expired}")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_manager_methods():
    """测试管理器方法"""
    print("\n=== 测试2: 管理器方法 ===")
    
    try:
        manager = UserInteractionManager()
        
        # 测试配置加载
        config = manager._load_config({'max_interactions': 50})
        print(f"✓ 配置加载成功: max_interactions = {config.get('max_interactions')}")
        
        # 测试初始化
        await manager.initialize()
        print("✓ 管理器初始化成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 管理器方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_monitoring():
    """测试性能监控"""
    print("\n=== 测试3: 性能监控 ===")
    
    try:
        from user_interaction_manager import monitor_performance, retry_on_failure
        
        # 测试装饰器
        @monitor_performance
        async def test_function():
            await asyncio.sleep(0.1)
            return "success"
        
        result = await test_function()
        print(f"✓ 性能监控装饰器测试成功: {result}")
        
        @retry_on_failure(max_retries=2, delay=0.1)
        async def failing_function():
            raise ValueError("测试错误")
        
        try:
            await failing_function()
        except ValueError:
            print("✓ 错误重试装饰器测试成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 性能监控测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试4: 错误处理 ===")
    
    try:
        # 测试无效交互创建
        try:
            invalid_interaction = UserInteraction(
                interaction_id="",
                interaction_type=InteractionType.CONFIRMATION,
                title="",
                message=""
            )
        except ValueError as e:
            print(f"✓ 数据验证错误处理成功: {e}")
        
        # 测试无效配置
        try:
            invalid_manager = UserInteractionManager({'max_interactions': -1})
        except ValueError as e:
            print(f"✓ 配置验证错误处理成功: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_resource_management():
    """测试资源管理"""
    print("\n=== 测试5: 资源管理 ===")
    
    try:
        manager = UserInteractionManager()
        
        # 测试统计信息
        stats = manager._stats
        print(f"✓ 统计信息获取成功: {list(stats.keys())}")
        
        # 测试健康状态
        health = manager._health_status
        print(f"✓ 健康状态获取成功: {list(health.keys())}")
        
        return True
        
    except Exception as e:
        print(f"✗ 资源管理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("开始用户交互管理器验证测试...")
    
    test_results = []
    
    # 运行所有测试
    test_results.append(await test_basic_functionality())
    test_results.append(await test_manager_methods())
    test_results.append(await test_performance_monitoring())
    test_results.append(await test_error_handling())
    test_results.append(await test_resource_management())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}/{total}")
    print(f"成功率: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 所有测试通过！用户交互管理器功能正常。")
    else:
        print("⚠️ 部分测试失败，需要进一步调试。")
    
    return passed == total

if __name__ == "__main__":
    # 运行测试
    try:
        result = asyncio.run(main())
        exit(0 if result else 1)
    except Exception as e:
        print(f"测试执行失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)