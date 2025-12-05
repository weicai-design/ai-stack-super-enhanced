"""
测试执行脚本
运行所有类型的测试：单元测试、端到端测试、压力测试、安全测试
"""

import unittest
import sys
import os
import time
import subprocess
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_unit_tests():
    """运行单元测试"""
    print("\n" + "="*60)
    print("🚀 开始运行单元测试")
    print("="*60)
    
    start_time = time.time()
    
    # 导入并运行单元测试
    import test_enhanced_circuit_breaker
    import test_data_persistence_backup
    
    # 获取测试类
    TestEnhancedCircuitBreaker = test_enhanced_circuit_breaker.TestEnhancedCircuitBreaker
    TestEnhancedRateLimiter = test_enhanced_circuit_breaker.TestEnhancedRateLimiter
    TestServiceDegradationRecovery = test_enhanced_circuit_breaker.TestServiceDegradationRecovery
    TestCircuitBreakerIntegration = test_enhanced_circuit_breaker.TestCircuitBreakerIntegration
    TestConfigurationManagement = test_enhanced_circuit_breaker.TestConfigurationManagement
    TestRealWorldScenarios = test_enhanced_circuit_breaker.TestRealWorldScenarios
    TestAsyncFunctionality = test_enhanced_circuit_breaker.TestAsyncFunctionality
    
    TestDataPersistenceManager = test_data_persistence_backup.TestDataPersistenceManager
    TestBackupManager = test_data_persistence_backup.TestBackupManager
    TestDataIntegrityChecker = test_data_persistence_backup.TestDataIntegrityChecker
    TestStorageManagement = test_data_persistence_backup.TestStorageManagement
    TestDecoratorFunctionality = test_data_persistence_backup.TestDecoratorFunctionality
    TestRealWorldScenarios = test_data_persistence_backup.TestRealWorldScenarios
    TestErrorHandling = test_data_persistence_backup.TestErrorHandling
    
    # 创建测试套件
    unit_test_suite = unittest.TestSuite()
    
    # 添加增强熔断器测试
    unit_test_suite.addTest(unittest.makeSuite(TestEnhancedCircuitBreaker))
    unit_test_suite.addTest(unittest.makeSuite(TestEnhancedRateLimiter))
    unit_test_suite.addTest(unittest.makeSuite(TestServiceDegradationRecovery))
    unit_test_suite.addTest(unittest.makeSuite(TestCircuitBreakerIntegration))
    unit_test_suite.addTest(unittest.makeSuite(TestConfigurationManagement))
    unit_test_suite.addTest(unittest.makeSuite(TestRealWorldScenarios))
    unit_test_suite.addTest(unittest.makeSuite(TestAsyncFunctionality))
    
    # 添加数据持久化测试
    unit_test_suite.addTest(unittest.makeSuite(TestDataPersistenceManager))
    unit_test_suite.addTest(unittest.makeSuite(TestBackupManager))
    unit_test_suite.addTest(unittest.makeSuite(TestDataIntegrityChecker))
    unit_test_suite.addTest(unittest.makeSuite(TestStorageManagement))
    unit_test_suite.addTest(unittest.makeSuite(TestDecoratorFunctionality))
    unit_test_suite.addTest(unittest.makeSuite(TestRealWorldScenarios))
    unit_test_suite.addTest(unittest.makeSuite(TestErrorHandling))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(unit_test_suite)
    
    end_time = time.time()
    
    print(f"\n📊 单元测试完成")
    print(f"运行时间: {end_time - start_time:.2f}秒")
    print(f"测试用例: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result


def run_e2e_tests():
    """运行端到端测试"""
    print("\n" + "="*60)
    print("🌐 开始运行端到端测试")
    print("="*60)
    
    start_time = time.time()
    
    # 导入并运行端到端测试
    import test_e2e_integration
    
    # 获取测试类
    TestE2EUserAuthentication = test_e2e_integration.TestE2EUserAuthentication
    TestE2EDataProcessing = test_e2e_integration.TestE2EDataProcessing
    TestE2EAPIIntegration = test_e2e_integration.TestE2EAPIIntegration
    TestE2EConcurrentOperations = test_e2e_integration.TestE2EConcurrentOperations
    TestE2ESystemRecovery = test_e2e_integration.TestE2ESystemRecovery
    TestE2EMonitoringAndObservability = test_e2e_integration.TestE2EMonitoringAndObservability
    TestE2ESecurityScenarios = test_e2e_integration.TestE2ESecurityScenarios
    
    # 创建测试套件
    e2e_test_suite = unittest.TestSuite()
    
    e2e_test_suite.addTest(unittest.makeSuite(TestE2EUserAuthentication))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2EDataProcessing))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2EAPIIntegration))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2EConcurrentOperations))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2ESystemRecovery))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2EMonitoringAndObservability))
    e2e_test_suite.addTest(unittest.makeSuite(TestE2ESecurityScenarios))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(e2e_test_suite)
    
    end_time = time.time()
    
    print(f"\n📊 端到端测试完成")
    print(f"运行时间: {end_time - start_time:.2f}秒")
    print(f"测试用例: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result


def run_stress_tests():
    """运行压力测试"""
    print("\n" + "="*60)
    print("💪 开始运行压力测试")
    print("="*60)
    
    start_time = time.time()
    
    # 导入并运行压力测试
    import test_stress_performance
    
    # 获取测试类
    TestConcurrentLoadStress = test_stress_performance.TestConcurrentLoadStress
    TestDataVolumeStress = test_stress_performance.TestDataVolumeStress
    TestLongRunningStress = test_stress_performance.TestLongRunningStress
    TestCircuitBreakerStress = test_stress_performance.TestCircuitBreakerStress
    TestSystemResourceStress = test_stress_performance.TestSystemResourceStress
    
    # 创建测试套件
    stress_test_suite = unittest.TestSuite()
    
    stress_test_suite.addTest(unittest.makeSuite(TestConcurrentLoadStress))
    stress_test_suite.addTest(unittest.makeSuite(TestDataVolumeStress))
    stress_test_suite.addTest(unittest.makeSuite(TestLongRunningStress))
    stress_test_suite.addTest(unittest.makeSuite(TestCircuitBreakerStress))
    stress_test_suite.addTest(unittest.makeSuite(TestSystemResourceStress))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(stress_test_suite)
    
    end_time = time.time()
    
    print(f"\n📊 压力测试完成")
    print(f"运行时间: {end_time - start_time:.2f}秒")
    print(f"测试用例: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result


def run_security_tests():
    """运行安全测试"""
    print("\n" + "="*60)
    print("🔒 开始运行安全测试")
    print("="*60)
    
    start_time = time.time()
    
    # 导入并运行安全测试
    import test_security_vulnerability
    
    # 获取测试类
    TestInjectionAttacks = test_security_vulnerability.TestInjectionAttacks
    TestAuthenticationSecurity = test_security_vulnerability.TestAuthenticationSecurity
    TestDataSecurity = test_security_vulnerability.TestDataSecurity
    TestAPISecurity = test_security_vulnerability.TestAPISecurity
    TestErrorHandlingSecurity = test_security_vulnerability.TestErrorHandlingSecurity
    
    # 创建测试套件
    security_test_suite = unittest.TestSuite()
    
    security_test_suite.addTest(unittest.makeSuite(TestInjectionAttacks))
    security_test_suite.addTest(unittest.makeSuite(TestAuthenticationSecurity))
    security_test_suite.addTest(unittest.makeSuite(TestDataSecurity))
    security_test_suite.addTest(unittest.makeSuite(TestAPISecurity))
    security_test_suite.addTest(unittest.makeSuite(TestErrorHandlingSecurity))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(security_test_suite)
    
    end_time = time.time()
    
    print(f"\n📊 安全测试完成")
    print(f"运行时间: {end_time - start_time:.2f}秒")
    print(f"测试用例: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    return result


def generate_test_report():
    """生成测试报告"""
    print("\n" + "="*60)
    print("📋 生成测试报告")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_types": ["单元测试", "端到端测试", "压力测试", "安全测试"],
        "results": {}
    }
    
    # 运行所有测试并收集结果
    test_functions = [
        ("单元测试", run_unit_tests),
        ("端到端测试", run_e2e_tests),
        ("压力测试", run_stress_tests),
        ("安全测试", run_security_tests)
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_type, test_function in test_functions:
        try:
            result = test_function()
            report["results"][test_type] = {
                "tests_run": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "successful": result.testsRun - len(result.failures) - len(result.errors)
            }
            
            total_tests += result.testsRun
            total_failures += len(result.failures)
            total_errors += len(result.errors)
            
        except Exception as e:
            print(f"❌ {test_type}执行失败: {e}")
            report["results"][test_type] = {
                "tests_run": 0,
                "failures": 0,
                "errors": 1,
                "successful": 0,
                "error": str(e)
            }
    
    # 计算总体指标
    total_successful = total_tests - total_failures - total_errors
    success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
    
    report["summary"] = {
        "total_tests": total_tests,
        "total_successful": total_successful,
        "total_failures": total_failures,
        "total_errors": total_errors,
        "success_rate": success_rate
    }
    
    # 输出报告
    print("\n" + "="*60)
    print("🎯 测试执行总结报告")
    print("="*60)
    
    for test_type, result in report["results"].items():
        print(f"\n{test_type}:")
        print(f"  测试用例: {result['tests_run']}")
        print(f"  成功: {result['successful']}")
        print(f"  失败: {result['failures']}")
        print(f"  错误: {result['errors']}")
        if 'error' in result:
            print(f"  执行错误: {result['error']}")
    
    print(f"\n📊 总体统计:")
    print(f"  总测试用例: {total_tests}")
    print(f"  总成功: {total_successful}")
    print(f"  总失败: {total_failures}")
    print(f"  总错误: {total_errors}")
    print(f"  成功率: {success_rate:.2f}%")
    
    # 保存报告到文件
    report_filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    import json
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 测试报告已保存到: {report_filename}")
    
    return report


def main():
    """主函数"""
    print("🚀 AI-STACK 增强限流熔断系统 - 完整测试套件")
    print("="*60)
    
    # 检查依赖
    try:
        import psutil
        print("✅ 依赖检查通过")
    except ImportError:
        print("⚠️  警告: psutil未安装，部分压力测试功能可能受限")
        print("   安装命令: pip install psutil")
    
    # 生成测试报告
    report = generate_test_report()
    
    # 根据测试结果给出建议
    success_rate = report["summary"]["success_rate"]
    
    print("\n" + "="*60)
    print("💡 测试结果分析")
    print("="*60)
    
    if success_rate >= 95:
        print("🎉 优秀! 系统稳定性非常高")
        print("   建议: 可以准备生产环境部署")
    elif success_rate >= 85:
        print("✅ 良好! 系统基本稳定")
        print("   建议: 修复少量失败用例后部署")
    elif success_rate >= 70:
        print("⚠️  一般! 系统需要改进")
        print("   建议: 重点修复失败用例")
    else:
        print("❌ 需要改进! 系统稳定性不足")
        print("   建议: 全面检查并修复问题")
    
    print("\n测试执行完成!")


if __name__ == "__main__":
    main()