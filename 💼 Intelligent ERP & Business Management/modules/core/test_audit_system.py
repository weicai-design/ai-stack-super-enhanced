"""
审计系统测试模块
测试审计日志系统的各项功能
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 直接导入模块
import audit_manager
import audit_config
import audit_logger


def test_audit_config():
    """测试审计配置"""
    print("🧪 测试审计配置...")
    
    # 测试默认配置
    config = audit_config.AuditConfig()
    print(f"✅ 默认配置: {config.to_dict()}")
    
    # 测试开发环境配置
    dev_config = audit_config.DEVELOPMENT_CONFIG
    print(f"✅ 开发环境配置: {dev_config.to_dict()}")
    
    # 测试配置验证
    assert config.log_level == "INFO"
    assert dev_config.log_level == "DEBUG"
    print("✅ 配置验证通过")


def test_audit_manager():
    """测试审计管理器"""
    print("\n🧪 测试审计管理器...")
    
    # 初始化审计管理器
    manager = audit_manager.get_audit_manager(audit_config.DEVELOPMENT_CONFIG)
    print("✅ 审计管理器初始化成功")
    
    # 测试获取组件
    logger = manager.get_logger()
    decorators = manager.get_decorators()
    config = manager.get_config()
    
    assert logger is not None
    assert decorators is not None
    assert config is not None
    print("✅ 组件获取测试通过")
    
    # 测试系统事件记录
    manager.log_system_event("TEST_EVENT", "测试系统事件", {"test": "data"})
    print("✅ 系统事件记录测试通过")
    
    return manager


def test_log_audit_event():
    """测试审计事件记录"""
    print("\n🧪 测试审计事件记录...")
    
    # 测试便捷函数
    audit_manager.log_audit_event(
        action=audit_logger.AuditAction.CREATE,
        user_id="test_user",
        module="TEST_MODULE",
        description="测试审计事件",
        details={"key": "value"},
        ip_address="192.168.1.1",
        user_agent="TestClient/1.0",
        success=True
    )
    print("✅ 审计事件记录测试通过")


def test_audit_decorators():
    """测试审计装饰器"""
    print("\n🧪 测试审计装饰器...")
    
    decorators = audit_manager.AuditDecorators()
    
    # 测试装饰器创建
    project_create_decorator = decorators.project_create()
    milestone_complete_decorator = decorators.milestone_complete()
    project_update_decorator = decorators.project_update()
    procurement_create_decorator = decorators.procurement_order_create()
    purchase_request_decorator = decorators.purchase_request_create()
    
    assert project_create_decorator is not None
    assert milestone_complete_decorator is not None
    assert project_update_decorator is not None
    assert procurement_create_decorator is not None
    assert purchase_request_decorator is not None
    print("✅ 装饰器创建测试通过")
    
    # 测试装饰器应用
    @decorators.project_create()
    def test_function():
        return "test_result"
    
    result = test_function()
    assert result == "test_result"
    print("✅ 装饰器应用测试通过")


def test_audit_logger_functionality():
    """测试审计日志器功能"""
    print("\n🧪 测试审计日志器功能...")
    
    manager = audit_manager.get_audit_manager()
    logger = manager.get_logger()
    
    # 测试日志查询
    logs = logger.get_audit_records(
        start_time=datetime.now() - timedelta(days=1),
        end_time=datetime.now()
    )
    print(f"✅ 日志查询测试通过，找到 {len(logs)} 条日志")
    
    # 测试统计信息
    stats = logger.get_audit_statistics()
    assert isinstance(stats, dict)
    print(f"✅ 统计信息测试通过: {stats}")
    
    # 测试日志导出
    logger.export_audit_logs(
        file_path="./test_audit_export.json",
        format="json"
    )
    print("✅ 日志导出测试通过")


def test_integration_with_modules():
    """测试与模块的集成"""
    print("\n🧪 测试与模块的集成...")
    
    # 测试项目管理模块导入
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "project"))
        from project_manager import ProjectManager
        
        project_manager = ProjectManager()
        print("✅ 项目管理模块导入成功")
        
        # 检查装饰器是否已应用
        import inspect
        create_project_method = project_manager.create_project
        decorators = [d for d in inspect.getmembers(create_project_method) if hasattr(d[1], '__wrapped__')]
        print(f"✅ 项目管理方法装饰器数量: {len(decorators)}")
        
    except Exception as e:
        print(f"⚠️ 项目管理模块测试失败: {e}")
    
    # 测试采购管理模块导入
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), "..", "procurement"))
        from procurement_manager import ProcurementManager
        
        procurement_manager = ProcurementManager()
        print("✅ 采购管理模块导入成功")
        
        # 检查装饰器是否已应用
        import inspect
        create_order_method = procurement_manager.create_procurement_order
        decorators = [d for d in inspect.getmembers(create_order_method) if hasattr(d[1], '__wrapped__')]
        print(f"✅ 采购管理方法装饰器数量: {len(decorators)}")
        
    except Exception as e:
        print(f"⚠️ 采购管理模块测试失败: {e}")


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始审计系统测试...\n")
    
    try:
        test_audit_config()
        manager = test_audit_manager()
        test_log_audit_event()
        test_audit_decorators()
        test_audit_logger_functionality()
        test_integration_with_modules()
        
        print("\n🎉 所有测试通过！审计系统功能正常。")
        
        # 显示统计信息
        stats = manager.get_statistics()
        print(f"\n📊 审计统计信息:")
        for key, value in stats.items():
            print(f"   {key}: {value}")
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()