"""
多租户认证系统测试脚本
Multi-tenant Authentication System Test Script

用于快速验证认证功能是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 切换到正确的目录
os.chdir(project_root)

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 模块导入")
    print("=" * 60)
    
    try:
        from enterprise.tenancy.auth import (
            token_service,
            api_key_service,
            APIKeyScope,
            CommandWhitelist
        )
        print("✅ 认证模块导入成功")
        
        from enterprise.tenancy.manager import tenant_manager
        print("✅ 租户管理器导入成功")
        
        from enterprise.tenancy.models import Tenant, TenantStatus, TenantPlan
        print("✅ 租户模型导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_token_service():
    """测试 Token 服务"""
    print("\n" + "=" * 60)
    print("测试 2: JWT Token 生成和验证")
    print("=" * 60)
    
    try:
        from enterprise.tenancy.auth import token_service
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="测试租户",
            slug="test-tenant",
            owner_email="test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        print(f"✅ 创建测试租户: {tenant.name} ({tenant.id})")
        
        # 生成 Token
        access_token = token_service.create_access_token(
            tenant_id=tenant.id,
            user_id="test-user-123",
            email="test@example.com",
            scopes=["read", "write"]
        )
        print(f"✅ 生成访问令牌: {access_token[:50]}...")
        
        # 验证 Token
        token_payload = token_service.verify_token(access_token)
        print(f"✅ 验证令牌成功:")
        print(f"   - 租户ID: {token_payload.tenant_id}")
        print(f"   - 用户ID: {token_payload.user_id}")
        print(f"   - 邮箱: {token_payload.email}")
        print(f"   - 权限范围: {token_payload.scopes}")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print(f"✅ 清理测试租户")
        
        return True
    except Exception as e:
        print(f"❌ Token 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_service():
    """测试 API Key 服务"""
    print("\n" + "=" * 60)
    print("测试 3: API Key 生成和验证")
    print("=" * 60)
    
    try:
        from enterprise.tenancy.auth import api_key_service, APIKeyScope
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="测试租户",
            slug="test-tenant-api",
            owner_email="test-api@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        print(f"✅ 创建测试租户: {tenant.name} ({tenant.id})")
        
        # 创建 API Key
        api_key_string, api_key_obj = api_key_service.create_api_key(
            tenant_id=tenant.id,
            name="测试 API Key",
            scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
            allowed_commands=["查询订单", "创建订单"],
            rate_limit=100,
            expires_days=30
        )
        print(f"✅ 创建 API Key: {api_key_string[:50]}...")
        print(f"   - Key ID: {api_key_obj.id}")
        print(f"   - 名称: {api_key_obj.name}")
        print(f"   - 权限范围: {[s.value for s in api_key_obj.scopes]}")
        print(f"   - 允许的命令: {api_key_obj.allowed_commands}")
        
        # 验证 API Key
        verified_key = api_key_service.verify_api_key(api_key_string)
        if verified_key:
            print(f"✅ 验证 API Key 成功:")
            print(f"   - 租户ID: {verified_key.tenant_id}")
            print(f"   - 名称: {verified_key.name}")
            print(f"   - 是否激活: {verified_key.is_active}")
        
        # 测试命令权限
        can_execute = verified_key.can_execute_command("查询订单")
        print(f"✅ 命令权限检查: '查询订单' -> {can_execute}")
        
        can_execute_dangerous = verified_key.can_execute_command("删除所有")
        print(f"✅ 命令权限检查: '删除所有' -> {can_execute_dangerous} (应该为 False)")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print(f"✅ 清理测试租户")
        
        return True
    except Exception as e:
        print(f"❌ API Key 服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_command_whitelist():
    """测试命令白名单"""
    print("\n" + "=" * 60)
    print("测试 4: 命令白名单分类")
    print("=" * 60)
    
    try:
        from enterprise.tenancy.auth import CommandWhitelist
        
        test_commands = [
            "查询订单",
            "查看财务",
            "创建订单",
            "删除订单",
            "配置系统",
            "删除所有",
            "未知命令"
        ]
        
        for cmd in test_commands:
            normalized = CommandWhitelist.normalize_command(cmd)
            cmd_type = CommandWhitelist.classify_command(cmd)
            print(f"✅ '{cmd}' -> 标准化: '{normalized}' -> 类型: {cmd_type}")
        
        return True
    except Exception as e:
        print(f"❌ 命令白名单测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("多租户认证系统测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 运行测试
    results.append(("模块导入", test_imports()))
    results.append(("Token 服务", test_token_service()))
    results.append(("API Key 服务", test_api_key_service()))
    results.append(("命令白名单", test_command_whitelist()))
    
    # 输出结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())




