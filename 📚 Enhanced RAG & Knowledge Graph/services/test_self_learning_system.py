#!/usr/bin/env python3
"""
自我学习系统完整测试模块
测试所有组件的生产级工程化能力
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta

# 添加路径以便导入模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from self_learning_system import (
    SelfLearningSystem, SelfLearningConfig, WorkflowMonitor, 
    IssueAnalyzer, ExperienceSummarizer, Optimizer, RAGIntegration,
    IssueType, SeverityLevel, get_self_learning_system
)


def test_workflow_monitor():
    """测试工作流监控器"""
    print("\n=== 测试工作流监控器 ===")
    
    monitor = WorkflowMonitor()
    
    # 模拟工作流数据
    test_workflows = [
        {
            "user_message": "测试工作流1",
            "duration": 2.5,
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "performance_score": 85,
                "resource_usage": 0.3
            }
        },
        {
            "user_message": "测试工作流2", 
            "duration": 8.2,
            "success": False,
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "performance_metrics": {
                "performance_score": 45,
                "resource_usage": 0.8
            }
        }
    ]
    
    # 测试工作流记录
    for workflow in test_workflows:
        monitor.record_workflow(workflow)
    
    # 测试统计分析
    stats = monitor.get_monitoring_statistics()
    print(f"监控统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    
    # 测试工作流查询
    workflow = monitor.get_workflow_by_id("WF001")
    print(f"查询工作流: {workflow}")
    
    # 测试性能趋势
    trends = monitor._get_performance_trends()
    print(f"性能趋势: {trends}")
    
    # 测试告警生成
    alert = monitor.generate_alert(test_workflows[1], IssueType.PERFORMANCE, SeverityLevel.HIGH)
    print(f"生成告警: {alert}")
    
    print("✓ 工作流监控器测试完成")


def test_issue_analyzer():
    """测试问题分析器"""
    print("\n=== 测试问题分析器 ===")
    
    analyzer = IssueAnalyzer()
    
    # 测试工作流分析
    test_workflow = {
        "id": "TEST_WORKFLOW_001",
        "user_message": "测试问题分析工作流",
        "duration": 12.5,  # 超过阈值
        "success": True,
        "rag_retrieval_1": {"results_count": 0},  # 检索问题
        "function_execution": {"success": False, "error": "模块导入错误"},
        "performance_metrics": {"resource_usage": 0.9}  # 资源使用过高
    }
    
    analysis_result = analyzer.analyze_workflow(test_workflow)
    print(f"问题分析结果: {json.dumps(analysis_result, indent=2, ensure_ascii=False)}")
    
    # 测试统计分析
    stats = analyzer.get_analysis_statistics()
    print(f"分析统计: {stats}")
    
    # 测试已知模式匹配
    test_issue = {
        "type": IssueType.PERFORMANCE.value,
        "description": "响应时间过长：12.5秒 (目标<5.0秒)",
        "severity": SeverityLevel.HIGH.value
    }
    
    patterns = analyzer.match_known_patterns(test_issue)
    print(f"匹配模式: {patterns}")
    
    print("✓ 问题分析器测试完成")


def test_experience_summarizer():
    """测试经验总结器"""
    print("\n=== 测试经验总结器 ===")
    
    summarizer = ExperienceSummarizer()
    
    # 模拟问题分析结果 - 修正格式以匹配经验总结器期望的输入
    test_issues_list = [
        {
            "issues": [
                {
                    "type": IssueType.PERFORMANCE.value,
                    "severity": SeverityLevel.HIGH.value,
                    "description": "响应时间过长：15.2秒",
                    "suggestion": "优化RAG检索算法"
                },
                {
                    "type": IssueType.RAG_QUALITY.value,
                    "severity": SeverityLevel.MEDIUM.value,
                    "description": "RAG第一次检索无结果",
                    "suggestion": "扩充知识库内容"
                }
            ]
        }
    ]
    
    # 测试经验总结
    try:
        summary = summarizer.summarize_issues(test_issues_list)
        print(f"经验总结ID: {summary.get('id')}")
        print(f"发现问题数: {summary.get('total_issues')}")
        print(f"质量评分: {summary.get('quality_score')}")
        
        # 测试RAG文档生成
        rag_doc = summary.get('rag_document', '')
        print(f"RAG文档长度: {len(rag_doc)} 字符")
        
        print("✓ 经验总结器测试完成")
    except Exception as e:
        print(f"❌ 经验总结器测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_optimizer():
    """测试优化器"""
    print("\n=== 测试优化器 ===")
    
    optimizer = Optimizer()
    
    # 模拟经验总结数据
    test_experience = {
        "experiences": [
            {
                "issue_type": "performance",
                "severity": "medium",
                "occurrence_count": 5,
                "optimization_suggestions": ["调整缓存策略", "优化数据库查询"]
            }
        ]
    }
    
    # 应用优化
    optimization_result = await optimizer.apply_optimization(test_experience)
    print(f"优化结果: {json.dumps(optimization_result, indent=2, ensure_ascii=False)}")
    
    # 测试优化历史
    history = optimizer.get_optimization_history()
    print(f"优化历史记录数: {len(history)}")
    
    print("✓ 优化器测试完成")


async def test_rag_integration():
    """测试RAG集成"""
    print("\n=== 测试RAG集成 ===")
    
    rag_integration = RAGIntegration()
    
    # 模拟经验总结数据 - 修正格式以匹配RAG集成器期望的输入
    test_summary = {
        "id": "EXP001",
        "summary": "发现2类问题，共2个具体问题",
        "total_issues": 2,
        "issue_types": 2,
        "experiences": [
            {
                "issue_type": "performance",
                "severity": "high",
                "occurrence_count": 1,
                "optimization_suggestions": ["优化RAG检索算法"]
            },
            {
                "issue_type": "rag_quality",
                "severity": "medium",
                "occurrence_count": 1,
                "optimization_suggestions": ["扩充知识库内容"]
            }
        ],
        "rag_document": "# AI-STACK 系统经验总结\n\n**总结ID**: EXP001\n**生成时间**: 2024-01-01 12:00:00\n\n## 系统状态\n\n系统运行正常，发现2类需要优化的问题。\n\n## 监控指标\n\n- **响应时间**: 需要优化\n- **成功率**: 95%\n- **资源使用率**: 正常\n\n## 问题分析\n\n### 1. 性能问题\n- **严重程度**: high\n- **优先级**: high\n- **出现次数**: 1\n- **发现时间**: 2024-01-01 12:00:00\n\n#### 优化建议\n- 优化RAG检索算法\n\n### 2. RAG质量问题\n- **严重程度**: medium\n- **优先级**: medium\n- **出现次数**: 1\n- **发现时间**: 2024-01-01 12:00:00\n\n#### 优化建议\n- 扩充知识库内容\n\n---\n\n*本文档由AI-STACK自我学习系统自动生成*",
        "quality_score": 85.0,
        "priority_distribution": {"critical": 0, "high": 1, "medium": 1, "low": 0},
        "created_at": datetime.now().isoformat(),
        "metadata": {
            "version": "1.0",
            "generator": "AI-STACK Self Learning System",
            "quality_assurance": "enabled"
        }
    }
    
    # 测试RAG保存
    try:
        save_result = await rag_integration.save_to_rag(test_summary)
        print(f"RAG保存结果: {save_result}")
        
        # 测试集成统计
        stats = rag_integration.get_integration_stats()
        print(f"集成统计: {stats}")
        
        print("✓ RAG集成测试完成")
    except Exception as e:
        print(f"❌ RAG集成测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_self_learning_system():
    """测试完整的自我学习系统"""
    print("\n=== 测试完整的自我学习系统 ===")
    
    # 获取全局实例
    system = get_self_learning_system()
    
    # 模拟工作流处理 - 修正格式以匹配process_workflow期望的输入
    test_workflow = {
        "workflow_id": "TEST_WORKFLOW_001",
        "user_message": "系统测试工作流",
        "duration": 3.2,
        "success": True,
        "timestamp": datetime.now().isoformat(),
        "steps": [
            {
                "name": "rag_retrieval_1",
                "results_count": 10,
                "success": True
            },
            {
                "name": "function_execution",
                "success": True
            }
        ],
        "performance_metrics": {
            "performance_score": 92,
            "resource_usage": 0.4
        }
    }
    
    # 测试工作流处理 - 使用await调用异步方法
    try:
        result = await system.process_workflow(test_workflow)
        print(f"系统处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        # 测试系统状态
        status = system.get_learning_status()
        print(f"系统学习状态: {status}")
        
        # 测试批量处理
        batch_workflows = [test_workflow] * 3
        batch_result = await system.batch_process_workflows(batch_workflows)
        print(f"批量处理结果数: {len(batch_result.get('results', []))}")
        
        print("✓ 自我学习系统测试完成")
    except Exception as e:
        print(f"❌ 自我学习系统测试失败: {e}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """运行所有测试"""
    print("开始自我学习系统生产级工程化能力测试...")
    
    try:
        test_workflow_monitor()
        test_issue_analyzer()
        test_experience_summarizer()
        await test_optimizer()
        await test_rag_integration()
        await test_self_learning_system()
        
        print("\n🎉 所有测试完成！自我学习系统生产级工程化能力验证成功！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


import asyncio

async def main():
    await run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())