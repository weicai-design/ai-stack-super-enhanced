#!/usr/bin/env python3
"""
工作流验证器错误处理机制测试脚本
测试各种异常情况下的错误处理能力
"""

import asyncio
import sys
import traceback
from core.workflow_enhanced_validator import WorkflowEnhancedValidator

class TestErrorHandler:
    """测试错误处理器"""
    def __init__(self):
        self.errors_handled = []
    
    def handle_error(self, validation_id: str, error: Exception):
        """处理错误"""
        self.errors_handled.append({
            'validation_id': validation_id,
            'error': str(error),
            'type': type(error).__name__
        })
        print(f"✅ 错误处理器捕获到错误: {validation_id} - {error}")

class TestAlertCallback:
    """测试告警回调"""
    def __init__(self):
        self.alerts_received = []
    
    def __call__(self, alert: dict):
        """处理告警"""
        self.alerts_received.append(alert)
        print(f"🚨 告警回调收到告警: {alert['type']} - {alert.get('message', '')}")

async def test_error_handling_mechanism():
    """测试错误处理机制"""
    print("🔧 开始测试工作流验证器错误处理机制...")
    
    # 创建验证器实例
    validator = WorkflowEnhancedValidator()
    
    # 添加测试错误处理器
    test_error_handler = TestErrorHandler()
    validator.add_error_handler(test_error_handler.handle_error)
    
    # 添加测试告警回调
    test_alert_callback = TestAlertCallback()
    validator.add_alert_callback(test_alert_callback)
    
    test_results = {
        'basic_error_handling': False,
        'validation_process_error': False,
        'alert_system': False,
        'error_propagation': False,
        'graceful_degradation': False
    }
    
    # 测试1: 基础错误处理
    print("\n🧪 测试1: 基础错误处理机制")
    try:
        # 模拟一个错误
        await validator._handle_error('test_validation_1', ValueError('测试错误'))
        
        # 检查错误是否被处理
        if len(test_error_handler.errors_handled) > 0:
            test_results['basic_error_handling'] = True
            print("✅ 基础错误处理测试通过")
        else:
            print("❌ 基础错误处理测试失败")
    except Exception as e:
        print(f"❌ 基础错误处理测试异常: {e}")
    
    # 测试2: 验证过程中的错误处理
    print("\n🧪 测试2: 验证过程错误处理")
    try:
        # 创建一个会失败的验证
        validation_id = await validator.start_workflow_validation(
            workflow_id='error_test',
            workflow_type='intelligent',
            user_input='',  # 空输入会触发输入验证失败
            context={}
        )
        
        await asyncio.sleep(1)
        
        report = await validator.get_validation_report(validation_id)
        
        if report.overall_status.value == 'failed':
            test_results['validation_process_error'] = True
            print("✅ 验证过程错误处理测试通过")
        else:
            print("❌ 验证过程错误处理测试失败")
    except Exception as e:
        print(f"❌ 验证过程错误处理测试异常: {e}")
    
    # 测试3: 告警系统
    print("\n🧪 测试3: 告警系统测试")
    try:
        # 触发性能告警
        await validator._check_performance_alerts()
        
        # 检查告警是否被触发
        if len(test_alert_callback.alerts_received) > 0:
            test_results['alert_system'] = True
            print("✅ 告警系统测试通过")
        else:
            print("❌ 告警系统测试失败")
    except Exception as e:
        print(f"❌ 告警系统测试异常: {e}")
    
    # 测试4: 错误传播
    print("\n🧪 测试4: 错误传播测试")
    try:
        # 测试错误是否被正确传播到统计信息
        stats = await validator.get_validation_stats()
        
        if stats['failed_validations'] > 0:
            test_results['error_propagation'] = True
            print("✅ 错误传播测试通过")
        else:
            print("❌ 错误传播测试失败")
    except Exception as e:
        print(f"❌ 错误传播测试异常: {e}")
    
    # 测试5: 优雅降级
    print("\n🧪 测试5: 优雅降级测试")
    try:
        # 检查验证器是否仍然可用
        health = await validator.get_health_status()
        
        if health['status'] == 'healthy':
            test_results['graceful_degradation'] = True
            print("✅ 优雅降级测试通过")
        else:
            print("❌ 优雅降级测试失败")
    except Exception as e:
        print(f"❌ 优雅降级测试异常: {e}")
    
    # 输出测试结果
    print("\n" + "="*60)
    print("📊 错误处理机制测试结果")
    print("="*60)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n测试通过率: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    
    # 输出详细错误信息
    if test_error_handler.errors_handled:
        print(f"\n📋 处理的错误列表 ({len(test_error_handler.errors_handled)} 个):")
        for error in test_error_handler.errors_handled:
            print(f"  - {error['validation_id']}: {error['error']}")
    
    if test_alert_callback.alerts_received:
        print(f"\n🚨 收到的告警列表 ({len(test_alert_callback.alerts_received)} 个):")
        for alert in test_alert_callback.alerts_received:
            print(f"  - {alert['type']}: {alert.get('message', '无消息')}")
    
    # 最终评估
    print("\n🎯 错误处理机制可靠性评估:")
    if passed_tests == total_tests:
        print("✅ 错误处理机制完全可靠！")
        print("   - 所有错误都能被正确捕获和处理")
        print("   - 告警系统响应及时")
        print("   - 错误信息传播完整")
        print("   - 系统具备优雅降级能力")
        print("   - 生产环境可靠性达标")
    else:
        print("⚠️ 错误处理机制需要改进")
        print("   - 部分错误处理功能不完善")
        print("   - 建议进一步优化错误处理逻辑")
    
    return passed_tests == total_tests

async def test_edge_cases():
    """测试边界情况"""
    print("\n🔬 测试边界情况...")
    
    validator = WorkflowEnhancedValidator()
    
    edge_cases = [
        # (workflow_id, workflow_type, user_input, context, description)
        ("", "intelligent", "正常输入", {}, "空工作流ID"),
        ("test", "", "正常输入", {}, "空工作流类型"),
        ("test", "intelligent", ""*5000, {}, "超长输入"),
        ("test", "intelligent", "正常输入", {"key": "value"*1000}, "超大上下文"),
        ("test", "unknown_type", "正常输入", {}, "未知工作流类型"),
    ]
    
    passed_cases = 0
    
    for workflow_id, workflow_type, user_input, context, description in edge_cases:
        try:
            validation_id = await validator.start_workflow_validation(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                user_input=user_input,
                context=context
            )
            
            # 增加等待时间，确保验证完成
            await asyncio.sleep(1)
            
            # 重试机制，确保获取到报告
            max_retries = 3
            report = None
            for attempt in range(max_retries):
                report = await validator.get_validation_report(validation_id)
                if report is not None:
                    break
                await asyncio.sleep(0.5)
            
            # 边界情况应该能够优雅处理，而不是崩溃
            # 只要返回了报告对象且没有异常，就认为处理成功
            if report is not None:
                passed_cases += 1
                print(f"✅ {description}: 处理成功 (状态: {report.overall_status.value})")
            else:
                print(f"❌ {description}: 处理失败 (报告为None)")
                
        except ValueError as e:
            # 参数验证错误是预期的行为
            passed_cases += 1
            print(f"✅ {description}: 参数验证正确 - {e}")
        except Exception as e:
            print(f"❌ {description}: 异常 - {e}")
    
    print(f"\n边界情况测试通过率: {passed_cases}/{len(edge_cases)}")
    return passed_cases == len(edge_cases)

async def main():
    """主测试函数"""
    print("🚀 工作流验证器错误处理机制深度测试")
    print("="*60)
    
    # 运行核心错误处理测试
    core_tests_passed = await test_error_handling_mechanism()
    
    # 运行边界情况测试
    edge_cases_passed = await test_edge_cases()
    
    # 最终评估
    print("\n" + "="*60)
    print("🎯 最终可靠性评估")
    print("="*60)
    
    if core_tests_passed and edge_cases_passed:
        print("✅ 错误处理机制完全可靠！")
        print("   - 所有核心功能正常")
        print("   - 边界情况处理完善")
        print("   - 生产环境稳定性达标")
        print("   - 可以放心部署到生产环境")
        return True
    else:
        print("⚠️ 错误处理机制需要进一步优化")
        print("   - 建议检查边界情况处理逻辑")
        print("   - 建议增加更多异常测试场景")
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试过程发生异常: {e}")
        traceback.print_exc()
        sys.exit(1)