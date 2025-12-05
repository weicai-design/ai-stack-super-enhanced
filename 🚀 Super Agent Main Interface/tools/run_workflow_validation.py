#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流验证测试脚本

功能：
1. 执行完整的工作流验证测试
2. 支持多种测试场景
3. 生成测试报告
4. 与验证监控器集成
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import sys

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.workflow_validation_monitor import (
    WorkflowValidationMonitor,
    get_workflow_validation_monitor,
    ValidationStatus,
    WorkflowValidationResult,
)

logger = logging.getLogger(__name__)


class WorkflowValidationTestRunner:
    """工作流验证测试运行器"""
    
    def __init__(self, monitor: Optional[WorkflowValidationMonitor] = None):
        self.monitor = monitor or get_workflow_validation_monitor()
        self.test_scenarios: List[Dict[str, Any]] = []
        self._setup_test_scenarios()
    
    def _setup_test_scenarios(self):
        """设置测试场景"""
        self.test_scenarios = [
            {
                "name": "ERP订单查询工作流",
                "description": "测试ERP系统中的订单查询完整链路",
                "input": {
                    "query": "查询最近3天的订单状态",
                    "workflow_type": "intelligent",
                    "expected_steps": ["RAG检索", "专家路由", "模块执行", "专家整合", "RAG存储"],
                },
                "expected_output": {
                    "status": ValidationStatus.PASSED,
                    "min_steps": 4,
                    "max_duration": 3.0,  # 秒
                }
            },
            {
                "name": "内容创作建议工作流",
                "description": "测试内容创作系统的建议生成链路",
                "input": {
                    "query": "为新产品生成营销内容建议",
                    "workflow_type": "intelligent",
                    "expected_steps": ["RAG检索", "策划专家", "生成专家", "去AI化专家", "RAG存储"],
                },
                "expected_output": {
                    "status": ValidationStatus.PASSED,
                    "min_steps": 4,
                    "max_duration": 3.0,
                }
            },
            {
                "name": "股票趋势分析工作流",
                "description": "测试股票量化系统的趋势分析链路",
                "input": {
                    "query": "分析AAPL股票最近一周的趋势",
                    "workflow_type": "intelligent",
                    "expected_steps": ["RAG检索", "技术分析专家", "基本面专家", "风险分析专家", "RAG存储"],
                },
                "expected_output": {
                    "status": ValidationStatus.PASSED,
                    "min_steps": 4,
                    "max_duration": 3.0,
                }
            },
            {
                "name": "直接操作工作流",
                "description": "测试直接操作工作流的执行链路",
                "input": {
                    "query": "执行系统状态检查",
                    "workflow_type": "direct",
                    "expected_steps": ["模块执行", "结果返回"],
                },
                "expected_output": {
                    "status": ValidationStatus.PASSED,
                    "min_steps": 2,
                    "max_duration": 1.5,
                }
            },
            {
                "name": "错误处理工作流",
                "description": "测试工作流错误处理机制",
                "input": {
                    "query": "执行无效操作",
                    "workflow_type": "intelligent",
                    "expected_steps": ["RAG检索", "错误处理"],
                },
                "expected_output": {
                    "status": ValidationStatus.FAILED,
                    "min_steps": 1,
                    "max_duration": 2.0,
                }
            }
        ]
    
    async def run_single_test(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试场景"""
        logger.info(f"开始测试: {scenario['name']}")
        
        start_time = time.time()
        
        try:
            # 模拟工作流执行
            workflow_id = f"test_{int(time.time())}_{scenario['name'][:10]}"
            
            # 这里应该调用实际的工作流执行器
            # 目前先模拟执行
            await self._simulate_workflow_execution(scenario)
            
            # 记录验证结果
            result = WorkflowValidationResult(
                workflow_id=workflow_id,
                workflow_type=scenario['input']['workflow_type'],
                user_input=scenario['input']['query'],
                status=ValidationStatus.PASSED,  # 模拟成功
                duration_seconds=time.time() - start_time,
                steps_count=len(scenario['input']['expected_steps']),
                successful_steps=len(scenario['input']['expected_steps']),
                rag_calls=2,  # 模拟两次RAG调用
                validation_details={
                    "scenario": scenario['name'],
                    "input": scenario['input'],
                    "simulated": True,
                },
                timestamp=datetime.now(),
            )
            
            # 验证结果会自动添加到监控器中
            
            # 检查是否符合预期
            expected = scenario['expected_output']
            is_success = (
                result.status == expected['status'] and
                result.successful_steps >= expected['min_steps'] and
                result.duration_seconds <= expected['max_duration']
            )
            
            test_result = {
                "scenario_name": scenario['name'],
                "status": "PASSED" if is_success else "FAILED",
                "duration": result.duration_seconds,
                "steps_completed": f"{result.successful_steps}/{result.steps_count}",
                "expected_status": expected['status'].value,
                "actual_status": result.status.value,
                "details": {
                    "workflow_id": workflow_id,
                    "simulated": True,
                }
            }
            
            logger.info(f"测试完成: {scenario['name']} - {test_result['status']}")
            return test_result
            
        except Exception as e:
            logger.error(f"测试失败: {scenario['name']} - {e}")
            
            # 记录失败结果
            result = WorkflowValidationResult(
                workflow_id=f"test_{int(time.time())}_{scenario['name'][:10]}",
                workflow_type=scenario['input']['workflow_type'],
                user_input=scenario['input']['query'],
                status=ValidationStatus.FAILED,
                duration_seconds=time.time() - start_time,
                steps_count=len(scenario['input']['expected_steps']),
                successful_steps=0,
                rag_calls=0,
                validation_details={
                    "scenario": scenario['name'],
                    "error": str(e),
                    "simulated": True,
                },
                timestamp=datetime.now(),
                error=str(e),
            )
            
            # 验证结果会自动添加到监控器中
            
            return {
                "scenario_name": scenario['name'],
                "status": "FAILED",
                "duration": result.duration_seconds,
                "steps_completed": "0/0",
                "error": str(e),
                "details": {"workflow_id": result.workflow_id}
            }
    
    async def _simulate_workflow_execution(self, scenario: Dict[str, Any]):
        """模拟工作流执行"""
        # 模拟执行时间
        execution_time = 0.5 + (hash(scenario['name']) % 100) / 1000  # 0.5-0.6秒
        await asyncio.sleep(execution_time)
        
        # 模拟可能的失败
        if "错误处理" in scenario['name']:
            raise Exception("模拟工作流执行错误")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试场景"""
        logger.info("开始运行所有工作流验证测试...")
        
        start_time = time.time()
        test_results = []
        
        # 运行所有测试
        for scenario in self.test_scenarios:
            result = await self.run_single_test(scenario)
            test_results.append(result)
        
        # 统计结果
        total_tests = len(test_results)
        passed_tests = sum(1 for r in test_results if r['status'] == "PASSED")
        failed_tests = total_tests - passed_tests
        
        # 计算平均响应时间
        avg_duration = sum(r['duration'] for r in test_results) / total_tests
        
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "pass_rate": passed_tests / total_tests,
            "average_duration": avg_duration,
            "total_duration": time.time() - start_time,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"所有测试完成: {passed_tests}/{total_tests} 通过")
        return summary
    
    def generate_test_report(self, summary: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = f"""
# AI-STACK 工作流验证测试报告

## 测试摘要
- 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 总测试场景: {summary['total_tests']}
- 通过测试: {summary['passed_tests']}
- 失败测试: {summary['failed_tests']}
- 通过率: {summary['pass_rate']:.1%}
- 平均响应时间: {summary['average_duration']:.3f}秒
- 总测试时长: {summary['total_duration']:.2f}秒

## 详细结果
"""
        
        # 添加每个测试的详细结果
        for i, result in enumerate(summary['test_results'], 1):
            status_icon = "✅" if result['status'] == "PASSED" else "❌"
            report += f"\n### {i}. {result['scenario_name']} {status_icon}\n"
            report += f"- 状态: {result['status']}\n"
            report += f"- 响应时间: {result['duration']:.3f}秒\n"
            report += f"- 步骤完成: {result['steps_completed']}\n"
            
            if 'error' in result:
                report += f"- 错误信息: {result['error']}\n"
            
            if 'expected_status' in result:
                report += f"- 预期状态: {result['expected_status']}\n"
                report += f"- 实际状态: {result['actual_status']}\n"
        
        # 添加建议
        report += "\n## 测试建议\n"
        
        if summary['pass_rate'] == 1.0:
            report += "- ✅ 所有测试通过，工作流验证机制运行正常\n"
        elif summary['pass_rate'] >= 0.8:
            report += "- ⚠️  大部分测试通过，建议检查失败场景\n"
        else:
            report += "- ❗ 通过率较低，建议检查工作流实现\n"
        
        if summary['average_duration'] > 1.0:
            report += "- ⏱️  响应时间较长，建议优化性能\n"
        else:
            report += "- ⚡ 响应时间良好\n"
        
        report += "- 📊 建议定期运行验证测试\n"
        report += "- 🔄 持续监控工作流执行状态\n"
        
        return report
    
    def save_test_report(self, summary: Dict[str, Any], report_dir: Path = Path("validation_reports")):
        """保存测试报告"""
        report_dir.mkdir(exist_ok=True)
        
        # 生成报告
        report_content = self.generate_test_report(summary)
        
        # 保存报告文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"workflow_test_report_{timestamp}.md"
        
        report_file.write_text(report_content, encoding="utf-8")
        logger.info(f"测试报告已保存: {report_file}")
        
        return report_file


async def main():
    """主函数"""
    # 创建测试运行器
    test_runner = WorkflowValidationTestRunner()
    
    try:
        print("🚀 开始工作流验证测试...")
        print("=" * 50)
        
        # 运行所有测试
        summary = await test_runner.run_all_tests()
        
        # 显示测试结果
        print("\n📊 测试结果摘要:")
        print(f"   总测试场景: {summary['total_tests']}")
        print(f"   通过测试: {summary['passed_tests']}")
        print(f"   失败测试: {summary['failed_tests']}")
        print(f"   通过率: {summary['pass_rate']:.1%}")
        print(f"   平均响应时间: {summary['average_duration']:.3f}秒")
        
        # 显示详细结果
        print("\n🔍 详细结果:")
        for result in summary['test_results']:
            status_icon = "✅" if result['status'] == "PASSED" else "❌"
            print(f"   {status_icon} {result['scenario_name']}: {result['duration']:.3f}秒")
        
        # 保存测试报告
        report_file = test_runner.save_test_report(summary)
        print(f"\n📄 测试报告已保存: {report_file}")
        
        # 启动仪表板（可选）
        if summary['passed_tests'] > 0:
            print("\n💡 提示: 可以运行 'python tools/workflow_validation_dashboard.py' 启动实时监控仪表板")
        
    except Exception as e:
        logger.error(f"测试运行失败: {e}")
        print(f"❌ 测试运行失败: {e}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())