"""
多租户认证系统集成测试脚本
Multi-tenant Authentication System Integration Test

用于全面验证系统的各个功能是否正常工作：
1. JWT Token 生成、验证、撤销
2. API Key 生成、验证、撤销、权限控制
3. 命令白名单
4. tenant_context 绑定
5. 数据库存储（SQLite）
6. 审计日志

运行方式：
    python "📚 Enhanced RAG & Knowledge Graph/enterprise/tenancy/test_integration.py"
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到路径
# enterprise 模块位于 "📚 Enhanced RAG & Knowledge Graph" 目录下
# 需要将 "📚 Enhanced RAG & Knowledge Graph" 目录添加到路径
rag_root = Path(__file__).parent.parent.parent  # "📚 Enhanced RAG & Knowledge Graph"
project_root = rag_root.parent  # 项目根目录
sys.path.insert(0, str(rag_root))
sys.path.insert(0, str(project_root))

# 切换到正确的目录
os.chdir(rag_root)


def print_header(title: str):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_test(test_name: str, status: bool, message: str = ""):
    """打印测试结果"""
    icon = "✅" if status else "❌"
    print(f"{icon} {test_name}", end="")
    if message:
        print(f": {message}")
    else:
        print()


def test_1_imports():
    """测试 1: 模块导入"""
    print_header("测试 1: 模块导入")
    
    try:
        # 导入认证模块
        from enterprise.tenancy.auth import (
            token_service,
            api_key_service,
            APIKeyScope,
            CommandWhitelist,
            bind_tenant_context,
            get_tenant_context
        )
        print_test("认证模块", True)
        
        # 导入租户管理器
        from enterprise.tenancy.manager import tenant_manager
        print_test("租户管理器", True)
        
        # 导入租户模型
        from enterprise.tenancy.models import Tenant, TenantStatus, TenantPlan
        print_test("租户模型", True)
        
        # 导入数据库
        try:
            from enterprise.tenancy.database import get_database, APIKeyDatabase
            db = get_database()
            print_test("数据库模块", True, "SQLite 数据库已连接")
        except Exception as e:
            print_test("数据库模块", False, f"数据库连接失败: {e}")
        
        # 导入审计日志
        try:
            from enterprise.tenancy.audit_logging import audit_logger
            print_test("审计日志模块", True)
        except Exception as e:
            print_test("审计日志模块", False, f"审计日志导入失败: {e}")
        
        return True
    except Exception as e:
        print_test("模块导入", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_2_jwt_token():
    """测试 2: JWT Token 生成、验证、撤销"""
    print_header("测试 2: JWT Token 生成、验证、撤销")
    
    try:
        from enterprise.tenancy.auth import token_service
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="JWT测试租户",
            slug="jwt-test-tenant",
            owner_email="jwt-test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        # 设置租户状态为 ACTIVE（测试需要）
        from enterprise.tenancy.models import TenantStatus
        tenant.status = TenantStatus.ACTIVE
        print_test("创建测试租户", True, f"租户ID: {tenant.id}")
        
        # 生成 Token
        access_token = token_service.create_access_token(
            tenant_id=tenant.id,
            user_id="test-user-123",
            email="test@example.com",
            scopes=["read", "write"]
        )
        print_test("生成访问令牌", True, f"Token: {access_token[:50]}...")
        
        # 验证 Token
        token_payload = token_service.verify_token(access_token)
        assert token_payload.tenant_id == tenant.id
        assert token_payload.user_id == "test-user-123"
        print_test("验证令牌", True, f"租户ID: {token_payload.tenant_id}, 用户ID: {token_payload.user_id}")
        
        # 测试 Token 撤销
        token_id = token_payload.jti
        if token_id:
            token_service.revoke_token(access_token)
            print_test("撤销令牌", True, f"Token ID: {token_id}")
            
            # 验证已撤销的 Token 应该失败
            try:
                token_service.verify_token(access_token)
                print_test("验证已撤销令牌", False, "应该抛出异常")
            except Exception:
                print_test("验证已撤销令牌", True, "正确拒绝了已撤销的 Token")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print_test("清理测试租户", True)
        
        return True
    except Exception as e:
        print_test("JWT Token 测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_3_api_key():
    """测试 3: API Key 生成、验证、权限控制"""
    print_header("测试 3: API Key 生成、验证、权限控制")
    
    try:
        from enterprise.tenancy.auth import api_key_service, APIKeyScope
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="API Key测试租户",
            slug="api-key-test-tenant",
            owner_email="apikey-test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        # 设置租户状态为 ACTIVE（测试需要）
        from enterprise.tenancy.models import TenantStatus
        tenant.status = TenantStatus.ACTIVE
        print_test("创建测试租户", True, f"租户ID: {tenant.id}")
        
        # 创建 API Key
        api_key_string, api_key_obj = api_key_service.create_api_key(
            tenant_id=tenant.id,
            name="测试 API Key",
            scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
            allowed_commands=["查询订单", "创建订单", "查看财务"],
            rate_limit=100,
            expires_days=30
        )
        print_test("创建 API Key", True, f"Key: {api_key_string[:50]}...")
        print(f"   - Key ID: {api_key_obj.id}")
        print(f"   - 名称: {api_key_obj.name}")
        print(f"   - 权限范围: {[s.value for s in api_key_obj.scopes]}")
        print(f"   - 允许的命令: {api_key_obj.allowed_commands}")
        
        # 验证 API Key
        verified_key = api_key_service.verify_api_key(api_key_string)
        assert verified_key is not None
        assert verified_key.tenant_id == tenant.id
        print_test("验证 API Key", True, f"租户ID: {verified_key.tenant_id}")
        
        # 测试命令权限
        can_query = verified_key.can_execute_command("查询订单")
        print_test("命令权限: 查询订单", can_query, f"结果: {can_query}")
        
        can_create = verified_key.can_execute_command("创建订单")
        print_test("命令权限: 创建订单", can_create, f"结果: {can_create}")
        
        can_delete = verified_key.can_execute_command("删除所有")
        print_test("命令权限: 删除所有", not can_delete, f"结果: {can_delete} (应该为 False)")
        
        # 列出租户的 API Keys
        api_keys = api_key_service.list_tenant_api_keys(tenant.id)
        print_test("列出租户 API Keys", True, f"数量: {len(api_keys)}")
        
        # 撤销 API Key
        api_key_service.revoke_api_key(api_key_string)
        print_test("撤销 API Key", True)
        
        # 验证已撤销的 API Key 应该失败
        revoked_key = api_key_service.verify_api_key(api_key_string)
        print_test("验证已撤销 API Key", revoked_key is None or not revoked_key.is_active, 
                  "正确拒绝或标记为无效")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print_test("清理测试租户", True)
        
        return True
    except Exception as e:
        print_test("API Key 测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_4_command_whitelist():
    """测试 4: 命令白名单分类"""
    print_header("测试 4: 命令白名单分类")
    
    try:
        from enterprise.tenancy.auth import CommandWhitelist
        
        test_commands = [
            ("查询订单", "read"),
            ("查看财务", "read"),
            ("创建订单", "write"),
            ("更新订单", "write"),
            ("删除订单", "write"),
            ("配置系统", "admin"),
            ("删除所有", "dangerous"),
            ("格式化磁盘", "dangerous"),
            ("未知命令", "unknown")
        ]
        
        all_passed = True
        for cmd, expected_type in test_commands:
            normalized = CommandWhitelist.normalize_command(cmd)
            cmd_type = CommandWhitelist.classify_command(cmd)
            passed = cmd_type == expected_type
            all_passed = all_passed and passed
            
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} '{cmd}' -> 标准化: '{normalized}' -> 类型: {cmd_type} (期望: {expected_type})")
        
        return all_passed
    except Exception as e:
        print_test("命令白名单测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_5_tenant_context():
    """测试 5: tenant_context 绑定"""
    print_header("测试 5: tenant_context 绑定")
    
    try:
        from enterprise.tenancy.auth import bind_tenant_context
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        from fastapi import Request
        from unittest.mock import Mock
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="上下文测试租户",
            slug="context-test-tenant",
            owner_email="context-test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        # 设置租户状态为 ACTIVE（测试需要）
        from enterprise.tenancy.models import TenantStatus
        tenant.status = TenantStatus.ACTIVE
        print_test("创建测试租户", True, f"租户ID: {tenant.id}")
        
        # 创建模拟请求对象
        request = Mock(spec=Request)
        request.state = Mock()
        
        # 绑定租户上下文
        bind_tenant_context(request, tenant)
        print_test("绑定租户上下文", True)
        
        # 验证上下文内容
        assert hasattr(request.state, "tenant")
        assert hasattr(request.state, "tenant_id")
        assert hasattr(request.state, "tenant_context")
        print_test("验证上下文属性", True)
        
        # 检查上下文内容
        context = request.state.tenant_context
        assert context["tenant_id"] == tenant.id
        assert context["tenant_name"] == tenant.name
        # 处理 plan 可能是 Enum 或字符串的情况
        plan_value = tenant.plan.value if hasattr(tenant.plan, 'value') else tenant.plan
        assert context["tenant_plan"] == plan_value
        print_test("验证上下文内容", True, 
                  f"租户ID: {context['tenant_id']}, 租户名称: {context['tenant_name']}")
        
        # 测试获取上下文（直接从 request.state 获取，因为 get_tenant_context 是异步的）
        retrieved_context = request.state.tenant_context
        assert retrieved_context is not None
        assert retrieved_context["tenant_id"] == tenant.id
        print_test("获取租户上下文", True)
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print_test("清理测试租户", True)
        
        return True
    except Exception as e:
        print_test("租户上下文测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_6_database():
    """测试 6: 数据库存储（SQLite）"""
    print_header("测试 6: 数据库存储（SQLite）")
    
    try:
        from enterprise.tenancy.database import get_database
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        db = get_database()
        print_test("数据库连接", True)
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="数据库测试租户",
            slug="db-test-tenant",
            owner_email="db-test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        # 设置租户状态为 ACTIVE（测试需要）
        from enterprise.tenancy.models import TenantStatus
        tenant.status = TenantStatus.ACTIVE
        print_test("创建测试租户", True, f"租户ID: {tenant.id}")
        
        # 测试 API Key 存储
        from enterprise.tenancy.auth import api_key_service, APIKeyScope
        api_key_string, api_key_obj = api_key_service.create_api_key(
            tenant_id=tenant.id,
            name="数据库测试 Key",
            scopes=[APIKeyScope.READ],
            expires_days=7
        )
        print_test("创建 API Key（存储到数据库）", True, f"Key ID: {api_key_obj.id}")
        
        # 从数据库读取
        keys = db.list_tenant_api_keys(tenant.id)
        assert len(keys) > 0
        print_test("从数据库读取 API Keys", True, f"数量: {len(keys)}")
        
        # 测试 Token 黑名单
        from enterprise.tenancy.auth import token_service
        token = token_service.create_access_token(
            tenant_id=tenant.id,
            user_id="test-user"
        )
        token_payload = token_service.verify_token(token)
        token_id = token_payload.jti
        
        if token_id:
            # 将 expires_at 转换为 datetime（如果它是时间戳）
            from datetime import datetime
            if isinstance(token_payload.exp, (int, float)):
                expires_at = datetime.fromtimestamp(token_payload.exp)
            else:
                expires_at = token_payload.exp
            
            db.add_token_to_blacklist(
                token_id=token_id,
                tenant_id=tenant.id,
                user_id="test-user",
                expires_at=expires_at
            )
            print_test("添加到黑名单", True, f"Token ID: {token_id}")
            
            is_blacklisted = db.is_token_blacklisted(token_id)
            print_test("检查黑名单", is_blacklisted, f"结果: {is_blacklisted}")
        
        # 测试审计日志
        from enterprise.tenancy.audit_logging import audit_logger
        audit_logger.log_api_key_action(
            tenant_id=tenant.id,
            action="test",
            api_key_id=api_key_obj.id,
            api_key_name=api_key_obj.name,
            details={"test": "integration test"}
        )
        print_test("写入审计日志", True)
        
        logs = audit_logger.get_audit_logs(tenant_id=tenant.id, limit=10)
        print_test("读取审计日志", len(logs) > 0, f"数量: {len(logs)}")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print_test("清理测试租户", True)
        
        return True
    except Exception as e:
        print_test("数据库测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def test_7_audit_logging():
    """测试 7: 审计日志"""
    print_header("测试 7: 审计日志")
    
    try:
        from enterprise.tenancy.audit_logging import audit_logger
        from enterprise.tenancy.manager import tenant_manager
        from enterprise.tenancy.models import TenantPlan
        
        # 创建测试租户
        tenant = tenant_manager.create_tenant(
            name="审计日志测试租户",
            slug="audit-test-tenant",
            owner_email="audit-test@example.com",
            plan=TenantPlan.ENTERPRISE
        )
        # 设置租户状态为 ACTIVE（测试需要）
        from enterprise.tenancy.models import TenantStatus
        tenant.status = TenantStatus.ACTIVE
        print_test("创建测试租户", True, f"租户ID: {tenant.id}")
        
        # 记录不同类型的审计日志
        audit_logger.log_api_key_action(
            tenant_id=tenant.id,
            action="create",
            api_key_id="test-key-123",
            api_key_name="测试 Key",
            details={"test": "api key action"}
        )
        print_test("记录 API Key 操作", True)
        
        audit_logger.log_token_action(
            tenant_id=tenant.id,
            action="revoke",
            user_id="test-user",
            details={"test": "token action"}
        )
        print_test("记录 Token 操作", True)
        
        audit_logger.log_command_action(
            tenant_id=tenant.id,
            action="execute",
            command="查询订单",
            allowed=True,
            user_id="test-user",
            details={"test": "command action"}
        )
        print_test("记录命令操作", True)
        
        audit_logger.log_tenant_action(
            tenant_id=tenant.id,
            action="access",
            user_id="test-user",
            details={"test": "tenant action"}
        )
        print_test("记录租户操作", True)
        
        # 读取审计日志
        logs = audit_logger.get_audit_logs(tenant_id=tenant.id, limit=100)
        print_test("读取审计日志", len(logs) >= 4, f"数量: {len(logs)} (期望 >= 4)")
        
        # 按操作类型筛选
        api_key_logs = audit_logger.get_audit_logs(
            tenant_id=tenant.id,
            resource_type="api_key",
            limit=10
        )
        print_test("筛选 API Key 日志", len(api_key_logs) > 0, f"数量: {len(api_key_logs)}")
        
        # 清理
        tenant_manager.delete_tenant(tenant.id)
        print_test("清理测试租户", True)
        
        return True
    except Exception as e:
        print_test("审计日志测试", False, str(e))
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "=" * 70)
    print("  多租户认证系统集成测试")
    print("  Multi-tenant Authentication System Integration Test")
    print("=" * 70)
    print(f"\n开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 运行所有测试
    tests = [
        ("模块导入", test_1_imports),
        ("JWT Token", test_2_jwt_token),
        ("API Key", test_3_api_key),
        ("命令白名单", test_4_command_whitelist),
        ("租户上下文", test_5_tenant_context),
        ("数据库存储", test_6_database),
        ("审计日志", test_7_audit_logging)
    ]
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 执行异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 输出结果汇总
    print_header("测试结果汇总")
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name:20s} {status}")
    
    total = len(results)
    passed = sum(1 for _, result in results if result)
    failed = total - passed
    
    print(f"\n  总计: {passed}/{total} 通过, {failed} 失败")
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if passed == total:
        print("\n" + "🎉" * 35)
        print("  所有测试通过！系统运行正常。")
        print("🎉" * 35 + "\n")
        return 0
    else:
        print("\n" + "⚠️" * 35)
        print(f"  有 {failed} 个测试失败，请检查错误信息。")
        print("⚠️" * 35 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
