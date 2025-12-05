#!/usr/bin/env python3
"""
调试边界情况处理问题
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.workflow_enhanced_validator import WorkflowEnhancedValidator

async def debug_edge_cases():
    """调试边界情况处理"""
    print("🔍 调试边界情况处理...")
    
    validator = WorkflowEnhancedValidator()
    
    edge_cases = [
        # (workflow_id, workflow_type, user_input, context, description)
        ("test", "intelligent", "x" * 5000, {}, "超长输入"),
        ("test", "intelligent", "正常输入", {"key": "value" * 1000}, "超大上下文"),
        ("test", "unknown_type", "正常输入", {}, "未知工作流类型"),
    ]
    
    for workflow_id, workflow_type, user_input, context, description in edge_cases:
        print(f"\n🧪 测试: {description}")
        print(f"   workflow_id: {workflow_id}")
        print(f"   workflow_type: {workflow_type}")
        print(f"   user_input 长度: {len(user_input)}")
        print(f"   context 大小: {len(str(context))}")
        
        try:
            # 检查参数验证
            print("   1. 检查参数验证...")
            
            # 手动调用参数验证逻辑
            if not workflow_id or not isinstance(workflow_id, str):
                raise ValueError("workflow_id 必须为非空字符串")
            
            if not workflow_type or not isinstance(workflow_type, str):
                raise ValueError("workflow_type 必须为非空字符串")
            
            if not isinstance(user_input, str):
                raise ValueError("user_input 必须为字符串")
            
            if not isinstance(context, dict):
                raise ValueError("context 必须为字典")
            
            if len(user_input) > 10000:
                raise ValueError("user_input 长度不能超过10000字符")
            
            if context and len(str(context)) > 10000:
                raise ValueError("context 序列化后长度不能超过10000字符")
                
            print("   ✅ 参数验证通过")
            
            # 开始验证
            print("   2. 开始验证...")
            validation_id = await validator.start_workflow_validation(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                user_input=user_input,
                context=context
            )
            print(f"   ✅ 验证ID: {validation_id}")
            
            # 等待验证完成
            print("   3. 等待验证完成...")
            await asyncio.sleep(1)
            
            # 获取报告
            print("   4. 获取验证报告...")
            report = await validator.get_validation_report(validation_id)
            
            if report is None:
                print("   ❌ 报告为None")
                
                # 检查验证任务状态
                print("   5. 检查验证任务状态...")
                if validation_id in validator.active_validations:
                    task = validator.active_validations[validation_id]
                    print(f"   ✅ 验证任务存在，状态: {task.done()}")
                    if task.done():
                        try:
                            result = task.result()
                            print(f"   ✅ 任务结果: {result}")
                        except Exception as e:
                            print(f"   ❌ 任务异常: {e}")
                else:
                    print("   ❌ 验证任务不存在")
                    
                # 检查验证报告存储
                print("   6. 检查验证报告存储...")
                if validation_id in validator.validation_reports:
                    stored_report = validator.validation_reports[validation_id]
                    print(f"   ✅ 存储的报告: {stored_report}")
                else:
                    print("   ❌ 存储中无报告")
                    
            else:
                print(f"   ✅ 报告获取成功")
                print(f"     整体状态: {report.overall_status.value}")
                print(f"     验证结果数量: {len(report.validation_results)}")
                for result in report.validation_results:
                    print(f"     - {result.name}: {result.status.value}")
                    
        except ValueError as e:
            print(f"   ✅ 参数验证正确 - {e}")
        except Exception as e:
            print(f"   ❌ 异常: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    await debug_edge_cases()

if __name__ == "__main__":
    asyncio.run(main())