#!/usr/bin/env python3
"""
配置管理器测试脚本

测试功能：
- 配置管理器单例模式
- 配置加载和解析
- 配置获取和设置
- 配置验证
- 健康检查
- 重新加载配置
"""

import os
import sys
import json
from datetime import datetime

# 添加项目路径到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.security.config_manager import get_security_config_manager


def test_singleton_pattern():
    """测试单例模式"""
    print("=== 测试单例模式 ===")
    
    # 获取两个实例
    manager1 = get_security_config_manager()
    manager2 = get_security_config_manager()
    
    # 检查是否为同一个实例
    assert manager1 is manager2, "单例模式测试失败：两个实例不相同"
    print("✓ 单例模式测试通过")
    
    return True


def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    manager = get_security_config_manager()
    
    # 测试默认配置
    default_roles = manager.get_config("rbac", "default_roles")
    assert default_roles == "guest,user", f"默认角色配置错误: {default_roles}"
    print(f"✓ 默认角色配置: {default_roles}")
    
    # 测试审计配置
    failure_threshold = manager.get_config("audit", "failure_rate_threshold")
    assert failure_threshold == 5, f"审计失败阈值错误: {failure_threshold}"
    print(f"✓ 审计失败阈值: {failure_threshold}")
    
    # 测试合规检查配置
    cache_ttl = manager.get_config("compliance", "cache_ttl")
    assert cache_ttl == 3600, f"合规检查缓存TTL错误: {cache_ttl}"
    print(f"✓ 合规检查缓存TTL: {cache_ttl}")
    
    return True


def test_config_parsing():
    """测试配置解析"""
    print("\n=== 测试配置解析 ===")
    
    manager = get_security_config_manager()
    
    # 测试JSON配置解析
    extra_permissions = manager.get_config("rbac", "extra_permissions")
    assert isinstance(extra_permissions, dict), "额外权限配置解析失败"
    print(f"✓ 额外权限配置类型: {type(extra_permissions)}")
    
    # 测试列表配置解析
    critical_events = manager.get_config("audit", "critical_security_events")
    assert isinstance(critical_events, str), "关键事件配置解析失败"
    print(f"✓ 关键事件配置: {critical_events}")
    
    return True


def test_config_get_set():
    """测试配置获取和设置"""
    print("\n=== 测试配置获取和设置 ===")
    
    manager = get_security_config_manager()
    
    # 测试获取不存在的配置（使用默认值）
    non_existent = manager.get_config("test", "non_existent", "default_value")
    assert non_existent == "default_value", "默认值配置获取失败"
    print(f"✓ 默认值配置: {non_existent}")
    
    # 测试设置新配置
    manager.set_config("test", "new_config", "test_value")
    retrieved = manager.get_config("test", "new_config")
    assert retrieved == "test_value", "配置设置失败"
    print(f"✓ 新配置设置和获取: {retrieved}")
    
    return True


def test_config_validation():
    """测试配置验证"""
    print("\n=== 测试配置验证 ===")
    
    manager = get_security_config_manager()
    
    # 测试有效配置验证
    is_valid = manager.validate_config()
    assert is_valid, "配置验证失败"
    print("✓ 配置验证通过")
    
    # 测试具体配置验证
    rbac_valid = manager.validate_config_section("rbac")
    assert rbac_valid, "RBAC配置验证失败"
    print("✓ RBAC配置验证通过")
    
    audit_valid = manager.validate_config_section("audit")
    assert audit_valid, "审计配置验证失败"
    print("✓ 审计配置验证通过")
    
    return True


def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    manager = get_security_config_manager()
    
    health_status = manager.health_check()
    assert isinstance(health_status, dict), "健康检查返回类型错误"
    assert health_status["status"] == "healthy", f"健康检查状态错误: {health_status['status']}"
    print(f"✓ 健康检查状态: {health_status['status']}")
    print(f"✓ 配置数量: {health_status['config_count']}")
    print(f"✓ 最后加载时间: {health_status['last_loaded']}")
    
    return True


def test_reload_config():
    """测试重新加载配置"""
    print("\n=== 测试重新加载配置 ===")
    
    manager = get_security_config_manager()
    
    # 记录当前配置数量
    initial_count = len(manager.config)
    
    # 重新加载配置
    reload_result = manager.reload_config()
    assert reload_result["success"], "配置重新加载失败"
    
    # 检查配置数量是否一致
    final_count = len(manager.config)
    assert initial_count == final_count, "配置重新加载后数量不一致"
    
    print(f"✓ 重新加载结果: {reload_result}")
    print(f"✓ 配置数量保持: {initial_count} -> {final_count}")
    
    return True


def test_environment_variables():
    """测试环境变量配置"""
    print("\n=== 测试环境变量配置 ===")
    
    # 设置环境变量
    os.environ["RBAC_DEFAULT_ROLES"] = "admin,security"
    os.environ["AUDIT_FAILURE_RATE_THRESHOLD"] = "10"
    os.environ["COMPLIANCE_CACHE_TTL"] = "1800"
    
    manager = get_security_config_manager()
    
    # 重新加载配置以获取环境变量
    manager.reload_config()
    
    # 测试环境变量配置
    default_roles = manager.get_config("rbac", "default_roles")
    assert default_roles == "admin,security", f"环境变量配置错误: {default_roles}"
    print(f"✓ 环境变量配置 - 默认角色: {default_roles}")
    
    failure_threshold = manager.get_config("audit", "failure_rate_threshold")
    assert failure_threshold == 10, f"环境变量配置错误: {failure_threshold}"
    print(f"✓ 环境变量配置 - 失败阈值: {failure_threshold}")
    
    cache_ttl = manager.get_config("compliance", "cache_ttl")
    assert cache_ttl == 1800, f"环境变量配置错误: {cache_ttl}"
    print(f"✓ 环境变量配置 - 缓存TTL: {cache_ttl}")
    
    # 清理环境变量
    del os.environ["RBAC_DEFAULT_ROLES"]
    del os.environ["AUDIT_FAILURE_RATE_THRESHOLD"]
    del os.environ["COMPLIANCE_CACHE_TTL"]
    
    return True


def main():
    """主测试函数"""
    print("开始配置管理器测试...")
    
    tests = [
        test_singleton_pattern,
        test_config_loading,
        test_config_parsing,
        test_config_get_set,
        test_config_validation,
        test_health_check,
        test_reload_config,
        test_environment_variables,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"❌ {test_func.__name__} 测试失败: {e}")
    
    print(f"\n=== 测试结果 ===")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有测试通过！配置管理器功能正常。")
        return 0
    else:
        print("❌ 部分测试失败，请检查配置管理器实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())